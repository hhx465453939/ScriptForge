"""不确定度：Bootstrap（BCa）置信区间、Beta-Binomial 后验区间。

工具来源（math 种子库）：
  - Bootstrap 自助法           → domains/C-概率统计与随机/C2-统计推断.md（recipes/06）
  - 先验/后验/共轭先验         → domains/C-概率统计与随机/C4-贝叶斯统计.md

必防陷阱：
  1. 小样本百分位 bootstrap 覆盖率偏低 → 默认 method="bca"（偏差校正 + 加速）。
  2. 随机过程不复现 → seed 必须外露且默认固定（SPEC §0.2）。
  3. BCa 的 z0 在 prop=0 或 1 时发散 → 截断到 [1/(2B), 1-1/(2B)]。
  4. 加速项分母为 0（jackknife 全同）→ 加速度取 0，退化为偏差校正百分位。
  5. Beta 分位需正则化不完全 Beta → 标准库无实现，用 Lentz 连分式 + 二分求逆。
"""

from __future__ import annotations

import math
import random
import statistics

_EPS = 1e-12


# ---------------------------------------------------------------- 分位工具
def quantile(sorted_vals: list[float], q: float) -> float:
    """线性插值分位（输入必须已排序）。"""
    n = len(sorted_vals)
    if n == 0:
        return 0.0
    if n == 1:
        return sorted_vals[0]
    q = min(1.0, max(0.0, q))
    pos = q * (n - 1)
    lo = int(math.floor(pos))
    hi = min(lo + 1, n - 1)
    frac = pos - lo
    return sorted_vals[lo] * (1.0 - frac) + sorted_vals[hi] * frac


def _betacf(a: float, b: float, x: float, max_iter: int = 300) -> float:
    """不完全 Beta 的连分式（修改 Lentz 法）。"""
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < _EPS:
        d = _EPS
    d = 1.0 / d
    h = d
    for m in range(1, max_iter + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < _EPS:
            d = _EPS
        c = 1.0 + aa / c
        if abs(c) < _EPS:
            c = _EPS
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < _EPS:
            d = _EPS
        c = 1.0 + aa / c
        if abs(c) < _EPS:
            c = _EPS
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 3e-16:
            break
    return h


def reg_incomplete_beta(a: float, b: float, x: float) -> float:
    """正则化不完全 Beta 函数 I_x(a,b) = Beta 分布的 CDF。"""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    lbeta = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
    front = math.exp(lbeta + a * math.log(x) + b * math.log1p(-x))
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - front * _betacf(b, a, 1.0 - x) / b


def beta_ppf(q: float, a: float, b: float, tol: float = 1e-12) -> float:
    """Beta 分布分位函数（二分法求 CDF 的逆）。"""
    q = min(1.0 - 1e-15, max(1e-15, q))
    lo, hi = 0.0, 1.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if reg_incomplete_beta(a, b, mid) < q:
            lo = mid
        else:
            hi = mid
        if hi - lo < tol:
            break
    return 0.5 * (lo + hi)


# ---------------------------------------------------------------- Bootstrap
def bootstrap_ci(
    xs: list,
    stat_fn,
    n_boot: int = 2000,
    seed: int = 20260101,
    alpha: float = 0.05,
    method: str = "bca",
) -> dict:
    """Bootstrap 置信区间。

    参数：
        xs       —— 样本（可为任意可重抽样对象列表，例如句子列表）
        stat_fn  —— 统计量函数，签名 stat_fn(sample) -> float
        n_boot   —— 重抽样次数
        seed     —— 随机种子（固定则结果逐位可复现）
        alpha    —— 显著性水平，默认 0.05 → 95% CI
        method   —— "bca"（默认，偏差校正+加速）或 "percentile"

    返回 {point, lo, hi, method, n_boot, alpha}。
    """
    n = len(xs)
    if n == 0:
        return {"point": 0.0, "lo": 0.0, "hi": 0.0, "method": method,
                "n_boot": 0, "alpha": alpha}
    point = float(stat_fn(xs))
    if n < 3 or n_boot < 10:
        return {"point": point, "lo": point, "hi": point, "method": "degenerate",
                "n_boot": 0, "alpha": alpha}

    rng = random.Random(seed)
    boots: list[float] = []
    for _ in range(n_boot):
        sample = [xs[rng.randrange(n)] for _ in range(n)]
        boots.append(float(stat_fn(sample)))
    boots.sort()

    lo_q, hi_q = alpha / 2.0, 1.0 - alpha / 2.0
    if method == "bca":
        # 偏差校正 z0
        below = sum(1 for b in boots if b < point)
        prop = below / n_boot
        prop = min(1.0 - 1.0 / (2 * n_boot), max(1.0 / (2 * n_boot), prop))
        nd = statistics.NormalDist()
        z0 = nd.inv_cdf(prop)
        # 加速 a（jackknife）
        jack: list[float] = []
        for i in range(n):
            left = xs[:i] + xs[i + 1:]
            jack.append(float(stat_fn(left)))
        jmean = sum(jack) / n
        num = sum((jmean - j) ** 3 for j in jack)
        den = 6.0 * (sum((jmean - j) ** 2 for j in jack)) ** 1.5
        acc = (num / den) if den > _EPS else 0.0

        def _adjust(z: float) -> float:
            d = 1.0 - acc * (z0 + z)
            if abs(d) < _EPS:
                return 0.5
            return nd.cdf(z0 + (z0 + z) / d)

        lo_q = min(0.999, max(0.001, _adjust(nd.inv_cdf(alpha / 2.0))))
        hi_q = min(0.999, max(0.001, _adjust(nd.inv_cdf(1.0 - alpha / 2.0))))

    return {
        "point": point,
        "lo": quantile(boots, lo_q),
        "hi": quantile(boots, hi_q),
        "method": method,
        "n_boot": n_boot,
        "alpha": alpha,
    }


# ---------------------------------------------------------------- Beta 后验
def beta_interval(successes: float, n: float, prior: tuple[float, float] = (1.0, 1.0),
                  alpha: float = 0.05) -> dict:
    """Beta-Binomial 后验：Beta(a0+s, b0+n-s)，返回 {mean, lo, hi, a, b, n}。

    用途：把「n 次里 k 次达标」这类小样本率估计成带区间的值，避免「3 次里 2 次 → 66.7%」的假精确。
    陷阱规避：先验取均匀 Beta(1,1)（Laplace）；0 次成功/全成功时后验仍有界，不会出现 0 或 1。
    """
    a0, b0 = prior
    s = max(0.0, float(successes))
    total = max(0.0, float(n))
    s = min(s, total)
    a = a0 + s
    b = b0 + (total - s)
    mean = a / (a + b) if (a + b) > _EPS else 0.5
    return {
        "mean": mean,
        "lo": beta_ppf(alpha / 2.0, a, b),
        "hi": beta_ppf(1.0 - alpha / 2.0, a, b),
        "a": a, "b": b, "n": total,
    }
