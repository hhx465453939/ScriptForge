"""信息论工具：熵、Surprisal、Jensen-Shannon 散度、Zipf 幂律拟合。

工具来源（math 种子库）：
  - 香农熵 / 联合熵          → domains/C-概率统计与随机/C7-信息论.md
  - KL 散度                  → 同上（本项目改用对称有界的 JS，规避 KL 陷阱）
  - Zipf 幂律 log-log OLS    → domains/C-概率统计与随机/C3-回归与多元统计.md

已读并规避的陷阱：
  - 熵：对数底数混用 → 本项目**统一 base=2（bits）**，全库只用 bits
  - 熵：0·log0 未定义   → 求和前剔除零概率项（约定 0·log0=0）
  - 熵：小样本偏差      → 提供 Miller-Madow 校正函数
  - KL：不对称、零支撑发散 → 一律用 JS（对称、有界 ∈[0,1] bits）
  - Zipf：log-log 仅中段线性、尾部噪声 → 强制回带 R²，低 R² 标注不可信
"""

from __future__ import annotations

import math


def _safe_counts(counts: dict) -> dict:
    """剔除非正值计数（熵的 0·log0 约定）。"""
    return {k: float(v) for k, v in counts.items() if v and v > 0}


def shannon_entropy(counts: dict) -> float:
    """香农熵 H(X) = -Σ p·log2 p，单位 bits。

    陷阱规避：base 固定 2；零计数在求和前剔除。
    """
    c = _safe_counts(counts)
    total = sum(c.values())
    if total <= 0 or len(c) <= 1:
        return 0.0
    h = 0.0
    for v in c.values():
        p = v / total
        h -= p * math.log2(p)
    return h


def miller_madow_correction(counts: dict) -> float:
    """Miller-Madow 熵偏差校正量：(K_obs - 1) / (2N ln2)。

    陷阱规避：小样本下 plug-in 熵系统性偏低，此项把偏差加回。
    """
    c = _safe_counts(counts)
    total = sum(c.values())
    k = len(c)
    if total <= 0 or k <= 1:
        return 0.0
    return (k - 1) / (2.0 * total * math.log(2))


def entropy_lower_bound(n_symbols: int) -> float:
    """给定符号数时的最大熵，用于把熵归一化到 [0,1]。"""
    if n_symbols <= 1:
        return 0.0
    return math.log2(n_symbols)


def normalize_entropy(counts: dict) -> float:
    """归一化熵 ∈ [0,1]：1 表示各符号等概率（最不可预测）。"""
    c = _safe_counts(counts)
    if len(c) <= 1:
        return 0.0
    return shannon_entropy(c) / entropy_lower_bound(len(c))


def surprisal(p: float, eps: float = 1e-6) -> float:
    """惊异度 -log2 p，单位 bits。p 越接近 0 越大。

    陷阱规避：p=0 时 -log2 p → ∞，用 eps 下限截断；调用方应传入**平滑后**概率。
    """
    if p <= 0.0:
        p = eps
    return -math.log2(p)


def smoothed_probability(count: float, total: float, vocab_size: int, alpha: float = 0.5) -> float:
    """加性平滑（Laplace / Lidstone）后的概率估计。

    陷阱规避：原始频率在稀有事件上给出 p=0，导致 surprisal 发散；alpha=0.5 为 Lidstone。
    """
    if total <= 0:
        return 1.0 / max(vocab_size, 1)
    return (count + alpha) / (total + alpha * max(vocab_size, 1))


def js_divergence(p_counts: dict, q_counts: dict) -> float:
    """Jensen-Shannon 散度，base=2，返回值 ∈ [0,1] bits。

    JS(P‖Q) = H((P+Q)/2) - (H(P)+H(Q))/2

    为什么不用 KL：KL 不对称（D(P‖Q)≠D(Q‖P)），且当 Q 在 P 支撑外为零时发散为 ∞。
    JS 对称、有界（≤1 bit），可直接当"距离"用于差异化维度。
    """
    p = _safe_counts(p_counts)
    q = _safe_counts(q_counts)
    if not p and not q:
        return 0.0
    vocab = set(p) | set(q)
    if len(vocab) <= 1:
        return 0.0
    tp = sum(p.values())
    tq = sum(q.values())
    if tp <= 0 or tq <= 0:
        return 1.0

    def _dist(normalize_to: dict) -> dict:
        return {k: v for k, v in normalize_to.items() if v > 0}

    P = _dist({k: p.get(k, 0.0) / tp for k in vocab})
    Q = _dist({k: q.get(k, 0.0) / tq for k in vocab})
    M = {}
    for k in vocab:
        m = 0.5 * (P.get(k, 0.0) + Q.get(k, 0.0))
        if m > 0:
            M[k] = m
    # 熵函数直接吃概率（分母为 1）
    def _h(d: dict) -> float:
        s = sum(d.values())
        if s <= 0:
            return 0.0
        return -sum((v / s) * math.log2(v / s) for v in d.values() if v > 0)

    return max(0.0, _h(M) - 0.5 * (_h(P) + _h(Q)))


_FLOOR_CACHE: dict[tuple, float] = {}


def js_null_floor(baseline_counts: dict, n_tokens: int, reps: int = 40, seed: int = 7) -> float:
    """JS 的**词表规模噪声地板**：从基线自身重采样出与文本等长的样本，测其与基线的 JS 中位数。

    为什么需要它（实测发现的坑）：
        参照语料很小（每形态 3 段、~700 字）时，任何真实文本（几百字）与它相比都会因
        **词表覆盖度不同**而产生很大的 JS，这个量与风格差异无关。实测：形态内参照文本
        自比得 JS≈0.47，而 300 字真实样本得 JS≈0.87——若不校正，差异化维度会对所有输入
        饱和到 1.0，沦为零信息量的假指标。

    做法：把「同样的词分布、同样的长度」能自然产生的 JS 作为地板扣掉，只留超额部分。
    实测校正后分离度：形态内 ≈ 0，跟形态 ≈ 0.53~0.79（见 references/math-engine.md §5.3）。

    性能：结果按（基线规模, token 数分桶）缓存——bootstrap 会反复调用，不缓存会慢一个量级。
    """
    toks: list[str] = []
    for t, c in baseline_counts.items():
        if c and c > 0:
            toks.extend([t] * int(c))
    if not toks or n_tokens <= 0:
        return 0.0
    key = (len(baseline_counts), int(sum(baseline_counts.values())), int(round(n_tokens / 50.0)))
    if key in _FLOOR_CACHE:
        return _FLOOR_CACHE[key]

    import random as _random
    rng = _random.Random(seed)
    n = max(20, int(n_tokens))
    vals: list[float] = []
    for _ in range(reps):
        sample = [toks[rng.randrange(len(toks))] for _ in range(n)]
        cts: dict[str, int] = {}
        for s in sample:
            cts[s] = cts.get(s, 0) + 1
        vals.append(js_divergence(cts, baseline_counts))
    vals.sort()
    floor = vals[len(vals) // 2]
    _FLOOR_CACHE[key] = floor
    return floor


def zipf_fit(counts: dict, max_rank: int = 200) -> dict:
    """Zipf 幂律拟合：freq ∝ rank^(-alpha)，对 log(freq) ~ log(rank) 做 OLS。

    返回 {alpha, r2, n, intercept}。
    陷阱规避：log-log 只在中间区段近似线性，尾部噪声大 → 必须回带 R²；
              R² < 0.7 时调用方须标注「拟合不可信」。alpha 越大说明流量越集中在少数词（记忆点越强）。
    """
    c = _safe_counts(counts)
    freqs = sorted((v for v in c.values() if v > 0), reverse=True)[:max_rank]
    n = len(freqs)
    if n < 3:
        return {"alpha": 0.0, "r2": 0.0, "n": n, "intercept": 0.0}
    xs = [math.log(i + 1.0) for i in range(n)]
    ys = [math.log(f) for f in freqs]
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    if sxx <= 0:
        return {"alpha": 0.0, "r2": 0.0, "n": n, "intercept": my}
    slope = sxy / sxx
    intercept = my - slope * mx
    syy = sum((y - my) ** 2 for y in ys)
    ss_res = sum((y - (intercept + slope * x)) ** 2 for x, y in zip(xs, ys))
    r2 = 1.0 - ss_res / syy if syy > 0 else 0.0
    return {"alpha": -slope, "r2": max(0.0, min(1.0, r2)), "n": n, "intercept": intercept}
