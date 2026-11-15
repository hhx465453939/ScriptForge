"""编排引擎：特征 → 指标 → 7 维 → 组合权重 → TOPSIS → 综合分 + 置信区间。

调用链（每一步都可回溯，见返回值的 feature_trace）：
    features.extract → 子指标（全部 ∈[0,1]，饱和函数 _sat 截断）
    → 7 个维度（加权和，∈[0,1]）
    → 权重：AHP（形态先验，CR 硬校验）× 熵权法（参照原型内区分度）→ 组合赋权
    → TOPSIS 贴近度（对参照原型的正/负理想解）
    → score100 = 100·C*，Bootstrap(BCa) 95% CI
"""

from __future__ import annotations

import math

from . import features as F
from . import genres as G
from . import info, rhythm, affect, mcdm, uncertainty, align


def _sat(x: float, cap: float) -> float:
    """饱和归一：x/cap 截断到 [0,1]。cap≤0 时返回 0。"""
    if cap <= 0:
        return 0.0
    return max(0.0, min(1.0, float(x) / float(cap)))


def _per100(n: float, n_chars: int) -> float:
    return (n * 100.0 / n_chars) if n_chars > 0 else 0.0


def _resample(xs: list[float], n_buckets: int) -> list[float]:
    """把变长序列等宽分桶取均值，压成固定长度（供跨文本 DTW 比较）。"""
    if not xs:
        return [0.0] * n_buckets
    m = len(xs)
    if m <= n_buckets:
        reps = n_buckets // max(m, 1) + 1
        return (list(xs) * reps)[:n_buckets]
    out: list[float] = []
    for b in range(n_buckets):
        lo = int(round(b * m / n_buckets))
        hi = int(round((b + 1) * m / n_buckets))
        seg = xs[lo:hi] or [xs[min(lo, m - 1)]]
        out.append(sum(seg) / len(seg))
    return out


def dimensions(fs: F.FeatureSet, prof: G.GenreProfile) -> tuple[list[float], dict]:
    """计算 7 个维度分（∈[0,1]）与可回溯的 trace。"""
    caps = G.CAPS
    trace: dict = {}

    # ---------------- D1 钩子力（位置轴）
    # rev1.1：移除首句 surprisal（与 D2 的词汇熵同源，同一 token 分布）；
    # 换入「前3句字数占比」——衡量开头是否把力气放在前 3 秒，属位置轴。
    qe_first3 = sum(s.count("？") + s.count("?") + s.count("！") + s.count("!")
                    for s in fs.sentences[:3])
    first3_ratio = (fs.first3_chars / fs.n_chars) if fs.n_chars > 0 else 0.0
    s_hook_hits = _sat(fs.hook_weight_sum, caps["hook_weight_sum"])
    s_qe = _sat(qe_first3, caps["qe_first3"])
    s_first3 = _sat(first3_ratio, caps["first3_ratio"])
    w = G.SUB_WEIGHTS["hook"]
    hook = w[0] * s_hook_hits + w[1] * s_qe + w[2] * s_first3
    trace["hook"] = {
        "hook_weight_sum": round(fs.hook_weight_sum, 4),
        "hook_hits_first3": fs.hook_hits,
        "qe_first3": qe_first3,
        "first3_chars": fs.first3_chars,
        "first3_ratio": round(first3_ratio, 4),
        "first_sent_surprisal_diag": round(fs.first_sent_surprisal, 4),  # 仅诊断，不计分
        "sub": [round(x, 4) for x in (s_hook_hits, s_qe, s_first3)],
        "weights": w,
        "aspects": ["钩子词(分类)", "标点强度(位置)", "开头占比(位置)"],
    }

    # ---------------- D2 信息密度（词汇轴）
    # rev1.1：移除 Zipf α（与归一化熵为镜像，强负相关）；
    # rev1.2：移除 hook_hits_all（跳维重复计权：钩子已由 D1 加权计入）；
    # rev1.3：再移除 trust_hits（与 D5 重叠，实测 density↔persuasion r=0.79）。
    #          语义重新分配：「数字/度量」→ 信息密度；「信任锚/CTA」→ 说服转化。
    info_units = fs.number_hits
    s_info = _sat(_per100(info_units, fs.n_chars), caps["info_units"])
    s_vocab = _sat(info.normalize_entropy(fs.token_counts), caps["vocab_entropy"])
    zf = info.zipf_fit(fs.token_counts)
    w = G.SUB_WEIGHTS["density"]
    density = w[0] * s_info + w[1] * s_vocab
    trace["density"] = {
        "info_units": info_units,
        "info_units_note": "仅数字/度量（不含钩子词与信任锚，避免与 D1/D5 重复计权）",
        "info_units_per100": round(_per100(info_units, fs.n_chars), 4),
        "vocab_entropy_norm": round(info.normalize_entropy(fs.token_counts), 4),
        "zipf_diag": {k: round(v, 4) if isinstance(v, float) else v for k, v in zf.items()},
        "sub": [round(x, 4) for x in (s_info, s_vocab)],
        "weights": w,
        "aspects": ["具体数字密度(计数)", "词汇离散度(分布)"],
    }

    # ---------------- D3 节奏冲击（长度动态轴：分布 / 时序 / 周期）
    # rev1.1：移除 CV（与 Gini 同为离散度）→ 换入句长交替率（时序模式），降为诊断。
    g = rhythm.gini(fs.sent_lengths)
    alt = rhythm.alternation_rate(fs.sent_lengths)
    cvr = rhythm.cv_robust(fs.sent_lengths)
    per = rhythm.dominant_period(fs.sent_lengths)
    s_gini = _sat(g, caps["gini"])
    s_alt = _sat(alt["rate"], caps["alternation"]) if alt["reliable"] else 0.5
    s_per = _sat(per["power_ratio"], caps["period"]) if per["reliable"] else 0.5
    w = G.SUB_WEIGHTS["rhythm"]
    r_dim = w[0] * s_gini + w[1] * s_alt + w[2] * s_per
    trace["rhythm"] = {
        "gini": round(g, 4),
        "alternation": alt,
        "cv_diag": round(cvr["cv"], 4),
        "mad": round(cvr["mad"], 4),
        "period": {k: (round(v, 4) if isinstance(v, float) else v) for k, v in per.items()},
        "sub": [round(x, 4) for x in (s_gini, s_alt, s_per)],
        "weights": w,
        "aspects": ["离散度(分布)", "交替率(时序)", "周期性(周期)"],
    }

    # ---------------- D4 情绪驱动（情绪动态轴：振幅 / 方向 / 位置 / 词汇）
    # rev1.1：移除 CUSUM（与波动率同为振幅读数）→ 换入情绪峰值位置（位置）。
    # rev1.2：再移除 emo_density——波动率本身就由同一情绪词典逐句计算得出，
    #          再计入词频密度属**同词典重复计权**（实测 density↔emotion r=0.87）。
    emo = affect.emotion_series(fs.emotion_valence)
    sl = affect.ols_slope(fs.emotion_valence)
    pk = affect.peak_position(fs.emotion_arousal)
    cp = affect.cusum_changepoints(fs.emotion_valence, h=4.0, drift=0.5)
    s_vol = _sat(emo["volatility"], caps["volatility"])
    s_slope = _sat(abs(sl["slope"]), caps["slope"])
    s_peak = _sat(pk["pos"], caps["peak_pos"]) if pk["reliable"] else 0.5
    w = G.SUB_WEIGHTS["emotion"]
    emo_dim = w[0] * s_vol + w[1] * s_slope + w[2] * s_peak
    trace["emotion"] = {
        "arc_type": emo["arc_type"],
        "volatility": round(emo["volatility"], 4),
        "slope": round(sl["slope"], 5),
        "slope_t": round(sl["t"], 4),
        "slope_r2": round(sl["r2"], 4),
        "peak_position": pk,
        "cusum_diag": {"max_stat": round(cp["max_stat"], 4), "points": cp["points"]},
        "emotion_hits_diag": fs.emotion_hits,
        "sub": [round(x, 4) for x in (s_vol, s_slope, s_peak)],
        "weights": w,
        "aspects": ["振幅(标准差)", "方向(斜率)", "位置(峰值)"],
    }

    # ---------------- D5 说服转化
    # rev1.3：移除「数字」子指标（已归 D2，避免与信息密度重叠）；
    #          本维只管「信任背书」与「行动指令」两个不同方面 + 合规扣分。
    s_trust = _sat(_per100(fs.trust_hits, fs.n_chars), caps["trust_density"])
    s_num_diag = _sat(_per100(fs.number_hits, fs.n_chars), caps["number_density"])
    if fs.cta_hits > 0:
        pos = max(0.0, fs.cta_position_ratio)
        s_cta = _sat(fs.cta_hits, caps["cta_count"]) * (0.85 + 0.15 * pos)
    else:
        s_cta = 0.0
    w = G.SUB_WEIGHTS["persuasion"]
    pers = w[0] * s_trust + w[1] * s_cta
    # 合规扣分：绝对化用语（广告法风险）拉低说服力——违规文案转化再好也不可持续
    compliance_penalty = min(0.30, fs.absolute_hits * 0.05)
    pers = max(0.0, pers - compliance_penalty)
    trace["persuasion"] = {
        "trust_hits": fs.trust_hits,
        "trust_per100": round(_per100(fs.trust_hits, fs.n_chars), 4),
        "number_hits_diag": fs.number_hits,
        "cta_hits": fs.cta_hits,
        "cta_position_ratio": round(fs.cta_position_ratio, 4),
        "hedge_hits": fs.hedge_hits,
        "absolute_hits": fs.absolute_hits,
        "compliance_penalty": round(compliance_penalty, 4),
        "sub": [round(x, 4) for x in (s_trust, s_cta)],
        "weights": w,
        "aspects": ["信任锚(背书)", "CTA(行动指令)"],
        "number_score_diag": round(s_num_diag, 4),
    }

    # ---------------- D6 差异化（JS vs 形态基线，扣除词表规模噪声地板）
    js = info.js_divergence(fs.token_counts, prof.baseline_tokens)
    floor = info.js_null_floor(prof.baseline_tokens, len(fs.tokens))
    excess = max(0.0, js - floor)
    s_js = _sat(excess, caps["js_excess"])
    trace["distinction"] = {
        "js_bits": round(js, 4),
        "js_null_floor": round(floor, 4),
        "js_excess": round(excess, 4),
        "cap_excess": caps["js_excess"],
        "baseline_vocab": len(prof.baseline_tokens),
        "baseline_tokens": int(sum(prof.baseline_tokens.values())),
        "sub": [round(s_js, 4)],
    }

    # ---------------- D7 可复制性（马尔可夫熵率）
    mk = rhythm.markov_entropy_rate(fs.structure_states)
    r_dim2 = mk["determinism"] if mk["reliable"] else mk["determinism"] * 0.6
    trace["replicability"] = {
        "H_rate": round(mk["H_rate"], 4),
        "H_max": round(mk["H_max"], 4),
        "determinism": round(mk["determinism"], 4),
        "reliable": mk["reliable"],
        "n_transitions": mk["n_transitions"],
        "structure_labels": fs.structure_labels,
        "sub": [round(r_dim2, 4)],
        "note": ("" if mk["reliable"]
                 else "转移样本不足（<10），按 0.6 折减，结论低置信"),
    }

    dims = [hook, density, r_dim, emo_dim, pers, s_js, r_dim2]
    return [max(0.0, min(1.0, d)) for d in dims], trace


def _weights(prof: G.GenreProfile) -> dict:
    ahp = mcdm.ahp_weights(prof.ahp_matrix, raise_on_inconsistent=True)
    obj = mcdm.entropy_weights(prof.archetypes)
    combined = mcdm.combine_weights(ahp["weights"], obj, alpha=prof.alpha)
    return {"ahp": ahp, "entropy": obj, "combined": combined}


def _archetype_match(dims: list[float]) -> dict:
    """归一化欧氏距离：本文七维向量最接近哪个参照原型（回答「像什么水平」）。

    ⚠️ 为什么**不用余弦**（实测踩到的坑）：
        七维全为非负且同向量级相近，余弦只测**夹角**、不测**水平**。
        实测把 video 样本（约 C 区）算成「最像 差 原型，cos=0.977」——
        余弦对非负向量几乎恒接近 1，原型之间的水平差异被抹平，结论完全错误。
    「像什么水平」是**水平问题**，必须用距离：d = ‖dims-arch‖/√n ∈ [0,1]，sim = 1-d。
    """
    n = max(len(dims), 1)
    sims: list[float] = []
    for arch in G.ARCHETYPES:
        d = math.sqrt(sum((float(a) - float(b)) ** 2 for a, b in zip(dims, arch)) / n)
        sims.append(max(0.0, min(1.0, 1.0 - d)))
    best = max(range(len(sims)), key=lambda i: sims[i])
    return {
        "closest": G.ARCHETYPE_LABELS[best],
        "similarity": round(sims[best], 4),
        "metric": "1 - normalized_euclidean",
        "all": {G.ARCHETYPE_LABELS[i]: round(s, 4) for i, s in enumerate(sims)},
    }


def _profile_fit(dims: list[float], prof: G.GenreProfile) -> dict:
    """权重契合度：cos(dims, 形态先验权重向量) ∈ [0,1]。

    回答的是**形状问题**（非水平问题）：「力气是否花在本形态最看重的维度上」。
    例：video 档把钩子/节奏权重抬得很高，若文本在这两维低、却把分数堆在低权重的可复制性上，
    则 cos 低——这是可执行的诊断（“你力气使错了地方”）。因此这里用余弦是对的。
    """
    cos = align.cosine(dims, prof.priority)
    top = G.strong_hook_dimensions(prof.name, 2)
    idx = {k: i for i, k in enumerate(G.DIMS)}
    return {
        "cosine": round(max(0.0, cos), 4),
        "priority_dims": top,
        "priority_scores": {k: round(dims[idx[k]], 4) for k in top},
        "metric": "cosine(dims, priority_weights)",
    }


def _arc_alignment(fs: F.FeatureSet) -> dict:
    """DTW：本文情绪弧与理想情绪弧的形态对齐度 ∈[0,1]（1 = 完全同形）。

    为什么要它：七维只量「情绪有多强」，不量「情绪怎么走」。
    同强度的上升弧与漡落弧在分数上无差别，但传播效果差异很大。
    DTW 已除以路径长归一化（否则长文永远更不像），且值域 [-1,1] 下 |diff|≤2 → 归一化距离≤2，
    故 alignment = 1 - normal 化距离/2 落在 [0,1]。
    """
    arc = _resample(fs.emotion_valence, G.ARC_BUCKETS)
    dtw = align.dtw_distance(arc, G.IDEAL_ARC)
    norm = dtw["normalized"]
    alignment = max(0.0, min(1.0, 1.0 - norm / 2.0))
    return {
        "alignment": round(alignment, 4),
        "dtw_normalized": round(norm, 4),
        "arc_buckets": G.ARC_BUCKETS,
        "source_sentences": len(fs.emotion_valence),
    }


def score(text: str, genre: str = "auto", seed: int = 20260101,
          n_boot: int = 400, with_ci: bool = True) -> dict:
    """主入口：给一段内容打分。

    返回 dict：
        genre / genre_confidence / genre_reason
        dimensions / dimension_labels / weights
        topsis / score100 / band / ci
        weaknesses / strengths / feature_trace / reliability_notes / disclaimer
    """
    fs = F.extract(text, genre)
    prof = G.GENRES[fs.genre]
    dims, trace = dimensions(fs, prof)
    wres = _weights(prof)
    w = wres["combined"]

    alts = [dims] + prof.archetypes
    ts = mcdm.topsis(alts, w, [True] * len(G.DIMS))
    closeness = ts["scores"][0]
    score100 = 100.0 * closeness

    # ---------------- 置信区间
    ci = {"point": round(score100, 2), "lo": round(score100, 2),
          "hi": round(score100, 2), "method": "degenerate", "n_boot": 0, "alpha": 0.05}
    dim_ci: dict[str, dict] = {}
    if with_ci and n_boot > 0 and len(fs.sentences) >= 5:
        def _stat(sub_sents: list) -> float:
            sub = "。".join(s.strip() for s in sub_sents if s and s.strip())
            f2 = F.extract(sub, fs.genre)
            d2, _ = dimensions(f2, prof)
            t2 = mcdm.topsis([d2] + prof.archetypes, w, [True] * len(G.DIMS))
            return 100.0 * t2["scores"][0]

        raw = uncertainty.bootstrap_ci(fs.sentences, _stat, n_boot=n_boot, seed=seed)

        # 逐维区间（同法重采样；seed+1 与总分独立，避免共用同一批样本造成伪相关）
        import random
        rng = random.Random(seed + 1)
        n = len(fs.sentences)
        per_dim: list[list[float]] = [[] for _ in G.DIMS]
        for _ in range(n_boot):
            idx = [rng.randrange(n) for _ in range(n)]
            sub = "。".join(fs.sentences[i].strip() for i in idx)
            f2 = F.extract(sub, fs.genre)
            d2, _ = dimensions(f2, prof)
            for k in range(len(G.DIMS)):
                per_dim[k].append(d2[k])
        for k, key in enumerate(G.DIMS):
            col = sorted(per_dim[k])
            dim_ci[key] = {
                "point": round(dims[k], 4),
                "lo": round(uncertainty.quantile(col, 0.025), 4),
                "hi": round(uncertainty.quantile(col, 0.975), 4),
            }

        ci = {
            "point": round(raw["point"], 2),
            "lo": round(raw["lo"], 2),
            "hi": round(raw["hi"], 2),
            "method": raw["method"],
            "n_boot": raw["n_boot"],
            "alpha": raw["alpha"],
        }

    # ---------------- 短板 / 优势
    order = sorted(range(len(G.DIMS)), key=lambda i: dims[i])
    weaknesses = [
        {"dim": G.DIMS[i], "label": G.DIM_LABELS[G.DIMS[i]], "score": round(dims[i], 4)}
        for i in order[:2]
    ]
    strengths = [
        {"dim": G.DIMS[i], "label": G.DIM_LABELS[G.DIMS[i]], "score": round(dims[i], 4)}
        for i in reversed(order[-2:])
    ]

    reliability = []
    if not trace["replicability"]["reliable"]:
        reliability.append("可复制性：结构转移样本不足，已折减并标注低置信")
    zf_r2 = trace["density"]["zipf_diag"]["r2"]
    if zf_r2 < 0.70:
        reliability.append(
            f"信息密度：Zipf 拟合 R²={zf_r2} < 0.70（该项已降为诊断输出，不计分）")
    if not trace["rhythm"]["period"]["reliable"]:
        reliability.append("节奏：句数 < 20，主周期检测不可信，已取中性值 0.5")
    if not trace["rhythm"]["alternation"]["reliable"]:
        reliability.append("节奏：句长差样本不足，交替率不可信，已取中性值 0.5")
    if not trace["emotion"]["peak_position"]["reliable"]:
        reliability.append("情绪：句数 < 5，峰值位置不可信，已取中性值 0.5")
    if fs.genre_confidence == "低":
        reliability.append("形态判定为低置信（兜底规则命中），建议用户显式指定形态后重算")

    return {
        "genre": fs.genre,
        "genre_label": prof.label,
        "genre_confidence": fs.genre_confidence,
        "genre_reason": fs.genre_reason,
        "n_chars": fs.n_chars,
        "n_sentences": len(fs.sentences),
        "n_paragraphs": fs.para_count,
        "dimensions": {k: round(v, 4) for k, v in zip(G.DIMS, dims)},
        "dimension_labels": G.DIM_LABELS,
        "dimension_ci": dim_ci,
        "weights": {
            "ahp_cr": round(wres["ahp"]["cr"], 6),
            "ahp_lambda_max": round(wres["ahp"]["lambda_max"], 6),
            "ahp": [round(x, 4) for x in wres["ahp"]["weights"]],
            "entropy": [round(x, 4) for x in wres["entropy"]],
            "combined": [round(x, 4) for x in w],
            "alpha": prof.alpha,
        },
        "topsis": {
            "closeness": round(closeness, 6),
            "d_plus": round(ts["d_plus"][0], 6),
            "d_minus": round(ts["d_minus"][0], 6),
            "n_alternatives_including_archetypes": len(alts),
        },
        "score100": round(score100, 2),
        "band": G.band_of(score100),
        "ci": ci,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "archetype_match": _archetype_match(dims),
        "profile_fit": _profile_fit(dims, prof),
        "arc_alignment": _arc_alignment(fs),
        "priority_dimensions_for_genre": G.strong_hook_dimensions(fs.genre),
        "feature_trace": trace,
        "raw_features": {
            "title": fs.title,
            "title_len": fs.title_len,
            "title_formula": fs.title_formula,
            "emoji_count": fs.emoji_count,
            "tag_count": fs.tag_count,
            "heading_count": fs.heading_count,
            "para_count": fs.para_count,
            "median_lines_per_para": round(fs.median_lines_per_para, 2),
            "avg_sent_len": round(fs.avg_sent_len, 2),
            "first3_chars": fs.first3_chars,
            "exclaim_count": fs.exclaim_count,
            "question_count": fs.question_count,
            "second_person_count": fs.second_person_count,
            "claim_count": fs.claim_count,
            "evidence_ratio": round(fs.evidence_ratio, 4),
            "golden_sentence_per_kchar": round(fs.golden_sentence_per_kchar, 4),
            "absolute_hits": fs.absolute_hits,
        },
        "reliability_notes": reliability,
        "calibration_status": "CALIBRATION_PENDING",
        "disclaimer": (
            "本分为**形态内相对位置**（对参照原型的 TOPSIS 贴近度），不是播放量预测；"
            "基线为人工先验，须用真实爆款数据回灌校准后才可用于跨账号比较。"
        ),
    }
