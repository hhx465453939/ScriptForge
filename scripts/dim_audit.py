#!/usr/bin/env python3
"""dim_audit.py — 七维正交性审计（源依赖矩阵 + 相关矩阵 + 有效维度）。

为什么需要这个工具
    此前「七维不共线」只是作者的结论。任何人都不该只听结论——
    本工具把判定过程外化，让第三方能自己复现。

四块输出（契约见 CHG-20261115-dim-orthogonality/SPEC.md §2）
    1 源依赖矩阵   行=数据源，列=七维，值=该维从该源取了几项子指标   精确，不依赖数据
    2 违规检测     同维内出现「同源同方面」两项 → FAIL                精确，不依赖数据
    3 相关矩阵     七维两两 Pearson r，附 n 与警告                     依赖数据
    4 有效维度     相关矩阵特征值谱 + 参与率                         依赖数据

局限（如实写在输出里）
    n<30 时相关系数与特征值谱都不可靠，只作健全性检查，不作结论。

用法
    python scripts/dim_audit.py
    python scripts/dim_audit.py --dir <语料目录>
    python scripts/dim_audit.py --json
    python scripts/dim_audit.py --strict
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from viralmath import calibration as C  # noqa: E402
from viralmath import genres as G  # noqa: E402
from viralmath import features as F  # noqa: E402
from viralmath.engine import dimensions  # noqa: E402

MIN_N_FOR_INFERENCE = 30

# 子指标 -> (数据源, 方面)。必须与 engine.dimensions 保持一致。
# 这是审计的「事实基准」：一旦实现改了子指标而这里没改，工具会与实现不符，
# 所以下面 assert_contract() 会在运行时用 engine 的 trace 反查校验。
SOURCE_MAP: dict[str, list[tuple[str, str, str]]] = {
    "hook": [
        ("hook_weight_sum", "lexicon", "分类强度"),
        ("qe_first3", "position", "标点强度"),
        ("first3_ratio", "position", "开头占比"),
    ],
    "density": [
        ("info_units", "number_stats", "具体数字密度"),
        ("vocab_entropy", "token_dist", "分布离散度"),
    ],
    "rhythm": [
        ("gini", "sent_lengths", "分布离散度"),
        ("alternation", "sent_lengths", "时序交替"),
        ("period", "sent_lengths", "周期性"),
    ],
    "emotion": [
        ("volatility", "emotion_series", "振幅"),
        ("slope", "emotion_series", "方向"),
        ("peak_pos", "arousal_series", "峰值位置"),
    ],
    "persuasion": [
        ("trust", "lexicon_trust", "信任锚"),
        ("cta", "lexicon_cta", "行动指令"),
    ],
    "distinction": [
        ("js_excess", "token_dist", "相对距离"),
    ],
    "replicability": [
        ("determinism", "structure_states", "序列确定性"),
    ],
}


def source_matrix() -> dict:
    """块1：源依赖矩阵 + 块2：违规检测。精确，无需数据。"""
    sources = sorted({s for items in SOURCE_MAP.values() for _, s, _ in items})
    grid = {s: {d: 0 for d in G.DIMS} for s in sources}
    for dim, items in SOURCE_MAP.items():
        for _, src, _ in items:
            grid[src][dim] += 1

    violations = []
    for dim, items in SOURCE_MAP.items():
        seen: dict[tuple, str] = {}
        for name, src, aspect in items:
            key = (src, aspect)
            if key in seen:
                violations.append({
                    "dim": dim,
                    "source": src,
                    "aspect": aspect,
                    "items": [seen[key], name],
                    "reason": "同维内同源同方面重复计权",
                })
            else:
                seen[key] = name
    return {"grid": grid, "sources": sources, "violations": violations}


def assert_contract(trace_hook: dict) -> list:
    """运行时校验：实现里声明的 aspects 必须与 SOURCE_MAP 的方面数一致。"""
    problems = []
    for dim in ("hook", "density", "rhythm", "emotion", "persuasion"):
        declared = len(SOURCE_MAP[dim])
        actual = len(trace_hook[dim]["sub"])
        if declared != actual:
            problems.append(f"{dim}: SOURCE_MAP 声明 {declared} 项，实现输出 {actual} 项")
    return problems


def load_corpus(root: str) -> list:
    texts = []
    if root and os.path.isdir(root):
        for name in sorted(os.listdir(root)):
            path = os.path.join(root, name)
            if os.path.isfile(path) and name.lower().endswith((".txt", ".md")):
                with open(path, "r", encoding="utf-8") as f:
                    body = f.read()
                if body.strip():
                    texts.append((name, body))
    else:
        base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "samples")
        if os.path.isdir(base):
            for name in sorted(os.listdir(base)):
                path = os.path.join(base, name)
                if os.path.isfile(path) and name.endswith(".txt"):
                    with open(path, "r", encoding="utf-8") as f:
                        texts.append((f"samples/{name}", f.read()))
    for genre, corpus in C.REFERENCE_CORPUS.items():
        for i, body in enumerate(corpus):
            texts.append((f"ref/{genre}/{i + 1}", body))
    return texts


def dim_vectors(texts: list) -> list:
    rows = []
    for name, body in texts:
        fs = F.extract(body, "auto")
        prof = G.GENRES[fs.genre]
        dims, _ = dimensions(fs, prof)
        rows.append({"name": name, "dims": dims, "genre": fs.genre})
    return rows


def pearson(xs: list, ys: list) -> float:
    n = len(xs)
    if n < 3:
        return 0.0
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    if sxx <= 1e-12 or syy <= 1e-12:
        return 0.0
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    return max(-1.0, min(1.0, sxy / math.sqrt(sxx * syy)))


def correlation_matrix(rows: list, demean_by_genre: bool = False) -> dict:
    """块3：七维相关矩阵。

    demean_by_genre=True 时，先减去**每个体裁自己的均值**再算相关。
    为什么必须提供这个版本：
        混池相关会把**体裁效应**误认为**维度冗余**。
        例：video 句子短、text 句子长，两者 first3_ratio 天然不同；
        混池后 hook 与 rhythm 会出现很高的表面相关，但它们并不在
        同一个体裁内部冗余——那是题材差异，不是重复计权。
        因此本工具同时给出「混池」与「去体裁均值」两个版本，以去体裁版为准。
    """
    k = len(G.DIMS)
    groups: dict[str, list] = {}
    for r in rows:
        groups.setdefault(r["genre"], []).append(r["dims"])

    cols: list[list] = [[] for _ in range(k)]
    if demean_by_genre:
        for _, members in groups.items():
            if not members:
                continue
            means = [sum(m[j] for m in members) / len(members) for j in range(k)]
            for m in members:
                for j in range(k):
                    cols[j].append(m[j] - means[j])
    else:
        for r in rows:
            for j in range(k):
                cols[j].append(r["dims"][j])

    mat = [[1.0] * k for _ in range(k)]
    for i in range(k):
        for j in range(i + 1, k):
            r = pearson(cols[i], cols[j])
            mat[i][j] = r
            mat[j][i] = r
    return {
        "matrix": mat,
        "n": len(rows),
        "n_groups": len(groups),
        "group_sizes": {g: len(v) for g, v in groups.items()},
        "demeaned": demean_by_genre,
    }


def jacobi_eigenvalues(mat: list, max_iter: int = 100) -> list:
    """对称矩阵特征值（Jacobi 旋转），纯标准库实现。"""
    n = len(mat)
    a = [row[:] for row in mat]
    for _ in range(max_iter):
        off = 0.0
        for i in range(n):
            for j in range(i + 1, n):
                off += a[i][j] * a[i][j]
        if off < 1e-20:
            break
        for p in range(n):
            for q in range(p + 1, n):
                if abs(a[p][q]) < 1e-18:
                    continue
                theta = (a[q][q] - a[p][p]) / (2.0 * a[p][q])
                t = (1.0 if theta >= 0 else -1.0) / (abs(theta) + math.sqrt(theta * theta + 1.0))
                c = 1.0 / math.sqrt(t * t + 1.0)
                s = t * c
                for k in range(n):
                    akp, akq = a[k][p], a[k][q]
                    a[k][p] = c * akp - s * akq
                    a[k][q] = s * akp + c * akq
                for k in range(n):
                    apk, aqk = a[p][k], a[q][k]
                    a[p][k] = c * apk - s * aqk
                    a[q][k] = s * apk + c * aqk
    return sorted((a[i][i] for i in range(n)), reverse=True)


def effective_dim(corr: dict) -> dict:
    """块4：特征值谱 + 参与率。参与率 ≈ 有效独立维度数。"""
    lam = jacobi_eigenvalues(corr["matrix"])
    pos = [max(0.0, v) for v in lam]
    total = sum(pos)
    sq = sum(v * v for v in pos)
    participation = (total * total / sq) if sq > 1e-12 else 0.0
    return {"eigenvalues": [round(v, 4) for v in lam], "participation_ratio": round(participation, 3)}


def setup_log() -> str:
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dim_audit.log")
    logging.basicConfig(filename=path, level=logging.INFO, filemode="a", force=True,
                        format="%(asctime)s %(levelname)s %(message)s")
    return path


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="七维正交性审计")
    p.add_argument("--dir", default=None, help="语料目录（默认 samples/ + 内置参照语料）")
    p.add_argument("--json", action="store_true", help="JSON 输出")
    p.add_argument("--strict", action="store_true", help="块2 有任何违规即非零退出")
    args = p.parse_args(argv)

    log_path = setup_log()

    sm = source_matrix()
    rows = dim_vectors(load_corpus(args.dir))
    corr_pooled = correlation_matrix(rows, demean_by_genre=False)
    corr = correlation_matrix(rows, demean_by_genre=True)
    eff_pooled = effective_dim(corr_pooled)
    eff = effective_dim(corr)

    probe_fs = F.extract("测试一句话。", "text")
    probe_dims, probe_trace = dimensions(probe_fs, G.GENRES["text"])
    contract_problems = assert_contract(probe_trace)

    small_n = corr["n"] < MIN_N_FOR_INFERENCE
    warn = ("样本不足（n=%d < %d）：相关矩阵与特征值谱仅作健全性检查，不作结论。"
            % (corr["n"], MIN_N_FOR_INFERENCE)) if small_n else ""
    max_off = 0.0
    for i in range(len(G.DIMS)):
        for j in range(i + 1, len(G.DIMS)):
            max_off = max(max_off, abs(corr["matrix"][i][j]))
    max_pooled = 0.0
    for i in range(len(G.DIMS)):
        for j in range(i + 1, len(G.DIMS)):
            max_pooled = max(max_pooled, abs(corr_pooled["matrix"][i][j]))

    logging.info("dim_audit n=%d violations=%d contract=%d max_off=%.3f eff=%.2f",
                 corr["n"], len(sm["violations"]), len(contract_problems),
                 max_off, eff["participation_ratio"])

    if args.json:
        payload = {
            "source_dependency": {"grid": sm["grid"], "sources": sm["sources"]},
            "violations": sm["violations"],
            "contract_problems": contract_problems,
            "correlation": {
                "dims": G.DIMS,
                "demeaned_by_genre": True,
                "matrix": [[round(v, 4) for v in row] for row in corr["matrix"]],
                "n": corr["n"],
                "group_sizes": corr["group_sizes"],
                "max_abs_offdiag": round(max_off, 4),
                "pooled_matrix": [[round(v, 4) for v in row] for row in corr_pooled["matrix"]],
                "pooled_max_abs_offdiag": round(max_pooled, 4),
                "warning": warn,
            },
            "effective_dim": eff,
            "effective_dim_pooled": eff_pooled,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print("# 七维正交性审计")
        print()
        print(f"语料样本量 n = {corr['n']}")
        if warn:
            print(f"⚠️  {warn}")
        print()
        print("## 块1 · 源依赖矩阵（行=数据源，列=维度，值=该维从该源取了几项子指标）")
        print()
        print("| 数据源 | " + " | ".join(G.DIMS) + " |")
        print("|---" * (len(G.DIMS) + 1) + "|")
        for src in sm["sources"]:
            cells = [str(sm["grid"][src][d]) for d in G.DIMS]
            print(f"| {src} | " + " | ".join(cells) + " |")
        print()
        print("## 块2 · 违规检测（同维内同源同方面重复计权）")
        print()
        if sm["violations"]:
            for v in sm["violations"]:
                print(f"  FAIL [{v['dim']}] {v['source']}/{v['aspect']}：{v['items']}")
        else:
            print("  PASS 无违规：任一维度内不存在「同源同方面」的两项子指标")
        if contract_problems:
            for c in contract_problems:
                print(f"  FAIL 契约不一致：{c}")
        print()
        print("## 块3 · 相关矩阵（Pearson r）")
        print()
        print(f"体裁构成: {corr['group_sizes']}")
        print()
        print("### 3a 去体裁均值（**以此为准**：已排除题材差异干扰）")
        print()
        print("| | " + " | ".join(d[:6] for d in G.DIMS) + " |")
        print("|---" * (len(G.DIMS) + 1) + "|")
        for i, d in enumerate(G.DIMS):
            cells = [f"{corr['matrix'][i][j]:.2f}" for j in range(len(G.DIMS))]
            print(f"| {d} | " + " | ".join(cells) + " |")
        print()
        print(f"最大非对角 |r| = {max_off:.3f}")
        print()
        print("### 3b 混池（仅参考：**混入了体裁差异**，不能当维度冗余证据）")
        print()
        print("| | " + " | ".join(d[:6] for d in G.DIMS) + " |")
        print("|---" * (len(G.DIMS) + 1) + "|")
        for i, d in enumerate(G.DIMS):
            cells = [f"{corr_pooled['matrix'][i][j]:.2f}" for j in range(len(G.DIMS))]
            print(f"| {d} | " + " | ".join(cells) + " |")
        print()
        print(f"最大非对角 |r| = {max_pooled:.3f}（混池值通常偏高，属体裁效应）")
        print()
        print("## 块4 · 有效维度")
        print()
        print(f"  去体裁均值 特征值谱: {eff['eigenvalues']}")
        print(f"  去体裁均值 参与率（≈有效独立维度）: {eff['participation_ratio']}")
        print(f"  混池       参与率（含体裁差异，仅参考）: {eff_pooled['participation_ratio']}")
        print()
        print("## 结论")
        print()
        if sm["violations"] or contract_problems:
            print("  ✗ 结构层面不通过（块2 有违规），必须先修子指标")
        else:
            print("  ✓ 结构层面通过：无「同一统计量的两个标度」")
        print("  注：块3/块4 在 n<30 时不可作结论；结构层（块1/块2）永远精确可用。")
        print()
        print(f"[日志] {log_path}", file=sys.stderr)

    if args.strict and (sm["violations"] or contract_problems):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
