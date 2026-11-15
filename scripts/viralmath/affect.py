"""情绪与走向工具：OLS 斜率、CUSUM 变点检测。

工具来源（math 种子库）：
  - 线性回归 / OLS 诊断   → domains/C-概率统计与随机/C3-回归与多元统计.md
  - 时间序列 / 变点       → domains/C-概率统计与随机/C6-时间序列.md（库内无 CUSUM 专条，按标准定义自建）

已读并规避的陷阱：
  - 伪回归：非平稳序列直接回归会得到虚假显著 → 本项目只对**句级情绪分**做趋势描述，
    不据此做因果或显著性断言；t 值仅作为"趋势是否明显"的辅助读数，并显式回带。
  - 斜率不报不确定度 → 强制回带 se / t / r²。
  - CUSUM 阈值隐含不透明 → 阈值 h 与漂移 k 全部外露为参数并回带。
"""

from __future__ import annotations

import math


def ols_slope(ys: list[float]) -> dict:
    """一元 OLS：y = a + b·x，x = 0..n-1。

    返回 {slope, intercept, se, t, r2, n}。
    t = slope / se。注意：该 t 未做自相关修正，只作趋势强度的辅助读数（见模块 docstring 陷阱说明）。
    """
    vals = [float(y) for y in ys]
    n = len(vals)
    if n < 3:
        return {"slope": 0.0, "intercept": vals[0] if vals else 0.0,
                "se": 0.0, "t": 0.0, "r2": 0.0, "n": n}
    xs = list(range(n))
    mx = (n - 1) / 2.0
    my = sum(vals) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx <= 1e-12:
        return {"slope": 0.0, "intercept": my, "se": 0.0, "t": 0.0, "r2": 0.0, "n": n}
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, vals))
    slope = sxy / sxx
    intercept = my - slope * mx
    ss_res = sum((y - (intercept + slope * x)) ** 2 for x, y in zip(xs, vals))
    ss_tot = sum((y - my) ** 2 for y in vals)
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 1e-12 else 0.0
    dof = n - 2
    if dof > 0:
        sigma2 = ss_res / dof
        se = math.sqrt(sigma2 / sxx) if sigma2 > 0 else 0.0
    else:
        se = 0.0
    t = (slope / se) if se > 1e-12 else 0.0
    return {"slope": slope, "intercept": intercept, "se": se, "t": t,
            "r2": max(0.0, min(1.0, r2)), "n": n}


def cusum_changepoints(ys: list[float], h: float = 4.0, drift: float = 0.5) -> dict:
    """双侧表格 CUSUM 变点检测（标准化后）。

    参数：
        h     —— 报警阈值（单位：标准化 σ）。越小越敏感，误报越多。
        drift —— 允许漂移 k（通常取 0.5σ，即只关心 0.5σ 以上的均值移动）。

    返回 {points, max_stat, threshold_h, drift_k, n}。
    points 为触发报警的句索引，触发后计数器复位（标准 CUSUM 行为）。
    """
    vals = [float(y) for y in ys]
    n = len(vals)
    if n < 4:
        return {"points": [], "max_stat": 0.0, "threshold_h": h, "drift_k": drift, "n": n}
    mean = sum(vals) / n
    sd = math.sqrt(sum((v - mean) ** 2 for v in vals) / n)
    if sd <= 1e-12:
        return {"points": [], "max_stat": 0.0, "threshold_h": h, "drift_k": drift, "n": n}
    z = [(v - mean) / sd for v in vals]
    k = drift / 2.0
    sp = sn = 0.0
    points: list[int] = []
    max_stat = 0.0
    for i, zi in enumerate(z):
        sp = max(0.0, sp + zi - k)
        sn = min(0.0, sn + zi + k)
        max_stat = max(max_stat, sp, abs(sn))
        if sp > h:
            points.append(i)
            sp = 0.0
        elif sn < -h:
            points.append(i)
            sn = 0.0
    return {"points": sorted(set(points)), "max_stat": max_stat,
            "threshold_h": h, "drift_k": drift, "n": n}


def emotion_series(per_sentence_scores: list[float]) -> dict:
    """把句级情绪分聚合成走向摘要。

    返回 {mean, volatility, slope, up_ratio, arc_type}。
    arc_type 用启发式：末段高于前段 → "上升"；先高后低 → "回落"；持平 → "平"。
    """
    vals = [float(v) for v in per_sentence_scores]
    n = len(vals)
    if n == 0:
        return {"mean": 0.0, "volatility": 0.0, "slope": 0.0,
                "up_ratio": 0.0, "arc_type": "无"}
    mean = sum(vals) / n
    vol = math.sqrt(sum((v - mean) ** 2 for v in vals) / n)
    ols = ols_slope(vals)
    third = max(1, n // 3)
    head = sum(vals[:third]) / third
    tail = sum(vals[-third:]) / third
    ups = sum(1 for a, b in zip(vals, vals[1:]) if b > a)
    up_ratio = ups / (n - 1) if n > 1 else 0.0
    if tail - head > 0.1:
        arc = "上升"
    elif head - tail > 0.1:
        arc = "回落"
    else:
        arc = "平"
    return {"mean": mean, "volatility": vol, "slope": ols["slope"],
            "up_ratio": up_ratio, "arc_type": arc}


def peak_position(arousal: list[float]) -> dict:
    """情绪峰值位置：唤醒度最大的那句在全文的相对位置，∈[0,1]。

    **为什么需要它**（D4 去重的关键）：
        波动率（振幅）、斜率（方向）、CUSUM（变点强度）三者本质都在描述
        「这条情绪序列有多剧烈」，属同一方面的不同读数 → 三重计权。
        而「激烈程度」与「峰值放在哪里」是两个统计上无关的方面：
        一条振幅很大的序列，峰值可能在第 2 句（前强后弱）也可能在末尾（逐步推高）。

    实现要点：用 **arousal**（唤醒度）而非 valence，避免与振幅/方向同一序列；
    位置取 argmax / (n-1)，使首句=0、末句=1。

    陷阱：n<5 时 argmax 受噪声主导 → reliable=False，调用方应取中性值。
    已知局限：本项用**单调饱和**归一，隐含「峰值越靠后越好」的假设；
    真实最优可能非单调（过早无回味，过晚无铺垫），但无校准数据前不凭空构造曲率。

    返回 {pos, peak_index, n, reliable}。
    """
    vals = [float(x) for x in arousal]
    n = len(vals)
    if n == 0:
        return {"pos": 0.0, "peak_index": 0, "n": 0, "reliable": False}
    if n == 1:
        return {"pos": 0.5, "peak_index": 0, "n": 1, "reliable": False}
    idx = max(range(n), key=lambda i: vals[i])
    pos = idx / (n - 1)
    return {
        "pos": max(0.0, min(1.0, pos)),
        "peak_index": idx,
        "n": n,
        "reliable": n >= 5,
    }
