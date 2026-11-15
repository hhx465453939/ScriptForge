"""节奏与序列工具：Gini、稳健 CV、ACF、主周期、马尔可夫熵率。

工具来源（math 种子库）：
  - 自相关 / 互相关        → domains/B-分析与微分方程/B8-信号处理数学.md
  - DFT/FFT 与窗函数       → 同上（本项目自建基-2 DFT，纯标准库）
  - 马尔可夫链             → domains/C-概率统计与随机/C5-随机过程.md
  - Gini / MAD / CV        → 库内无专条，按标准定义自建（描述统计）

已读并规避的陷阱：
  - ACF 在短序列上不可靠 → 硬性最小样本门（<20 句判 reliable=False）
  - DFT 频谱泄漏         → 扣除均值 + 加 Hann 窗后再变换
  - 转移矩阵未行归一化   → 每行除以其计数和
  - 状态样本过少         → <10 个转移判 unreliable
"""

from __future__ import annotations

import cmath
import math

from .calibration import THRESHOLDS


# ------------------------------------------------------------------ 描述统计
def gini(xs: list[float]) -> float:
    """Gini 系数 ∈ [0,1]：0 = 完全平均，→1 = 极度集中。

    用于句长分布：值越大，长短句反差越强，节奏越"打人"。
    """
    vals = sorted(float(x) for x in xs if x is not None and x >= 0)
    n = len(vals)
    s = sum(vals)
    if n == 0 or s <= 0:
        return 0.0
    cum = 0.0
    for i, v in enumerate(vals, start=1):
        cum += i * v
    return max(0.0, min(1.0, (2.0 * cum) / (n * s) - (n + 1.0) / n))


def median(xs: list[float]) -> float:
    vals = sorted(float(x) for x in xs)
    n = len(vals)
    if n == 0:
        return 0.0
    mid = n // 2
    return vals[mid] if n % 2 else 0.5 * (vals[mid - 1] + vals[mid])


def mad(xs: list[float]) -> float:
    """中位数绝对偏差 MAD = median(|x - median(x)|)。

    陷阱规避：标准差被极端值主导；MAD 的崩溃点高达 50%，稳健得多。
    """
    if not xs:
        return 0.0
    m = median(xs)
    return median([abs(float(x) - m) for x in xs])


def cv_robust(xs: list[float]) -> dict:
    """同时回带经典 CV 与 MAD 稳健 CV。

    陷阱规避：CV = std/mean 对异常值极敏感 → 双报，二者差距大即提示存在离群点。

    ⚠️ 关于 cv_robust=0 的语义（勿误读为算错）：
        当**超过 50% 的样本取值相同**时 MAD=0，cv_robust 随之归零。
        这正是稳健统计的设计目的：对少数离群点完全免疫。
        例：[10]*9 + [1000] → median=10，|x-median| 的中位数=0 → MAD=0。
        此时经典 CV 仍然很大，差值本身就是「存在极端离群点」的诊断信号。
        引擎 D3 维度采用的是经典 cv（而非 cv_robust），故此处归零不影响评分。
    """
    vals = [float(x) for x in xs]
    n = len(vals)
    if n == 0:
        return {"mean": 0.0, "std": 0.0, "cv": 0.0, "mad": 0.0, "cv_robust": 0.0}
    mean = sum(vals) / n
    var = sum((v - mean) ** 2 for v in vals) / n
    std = math.sqrt(var)
    m = median(vals)
    m_abs = mad(vals)
    # 1.4826 使 MAD 在正态下与 σ 一致
    return {
        "mean": mean,
        "std": std,
        "cv": (std / mean) if mean > 1e-12 else 0.0,
        "mad": m_abs,
        "cv_robust": (1.4826 * m_abs / m) if m > 1e-12 else 0.0,
    }


def robust_z(xs: list[float]) -> list[float]:
    """MAD 稳健 z 分数 z = (x - median) / (1.4826·MAD)。"""
    if not xs:
        return []
    m = median(xs)
    scale = 1.4826 * mad(xs)
    if scale <= 1e-12:
        return [0.0 for _ in xs]
    return [(float(x) - m) / scale for x in xs]


# ------------------------------------------------------------------ 自相关
def acf(xs: list[float], max_lag: int = 10) -> list[float]:
    """样本自相关 r(k)，k=1..max_lag。已扣除均值（ACF 定义要求）。"""
    vals = [float(x) for x in xs]
    n = len(vals)
    if n < 2:
        return []
    mean = sum(vals) / n
    d = [v - mean for v in vals]
    denom = sum(x * x for x in d)
    if denom <= 1e-12:
        return [0.0] * min(max_lag, n - 1)
    out = []
    for k in range(1, min(max_lag, n - 1) + 1):
        num = sum(d[i] * d[i + k] for i in range(n - k))
        out.append(num / denom)
    return out


# ------------------------------------------------------------------ 周期检测
def _hann(n: int) -> list[float]:
    """Hann 窗，压 DFT 频谱泄漏（代价：主瓣展宽）。"""
    if n <= 1:
        return [1.0] * n
    return [0.5 - 0.5 * math.cos(2.0 * math.pi * i / (n - 1)) for i in range(n)]


def _dft_magnitude(xs: list[float]) -> list[float]:
    """朴素 DFT 幅度谱（去掉相位）。n 很小（句数），O(n²) 足够。"""
    n = len(xs)
    out = []
    for k in range(n // 2 + 1):
        acc = 0j
        for t, x in enumerate(xs):
            acc += x * cmath.exp(-2j * math.pi * k * t / n)
        out.append(abs(acc))
    return out


def dominant_period(xs: list[float]) -> dict:
    """主周期检测：扣均值 → Hann 窗 → DFT → 取**最低频的显著峰**得到基频周期。

    返回 {period, power_ratio, reliable, peak_bin, n_peaks}。

    陷阱规避一：ACF/DFT 在短序列上不可靠 → 句数 < 20 时 reliable=False。
    陷阱规避二：不扣均值会让 DC 分量吞掉全部能量；不加窗会泄漏到邻近频点。
    陷阱规避三（本项目实测踩到的坑）：**取全局最大峰 ≠ 取基频**。
        脉冲串（如句长 [长,短,短,短] 重复）的频谱是**等幅多阶谐波**，
        k=6,12,18... 次谐波幅度几乎相同，argmax 会被浮点误差随机选到高次谐波，
        导致周期被报成真实周期的 1/2、1/3。
        实测：[1,0,0,0]*6 的全局最大峰落在 k=12 → 周期误报 2.0（真值 4.0）。

    陷阱规避四：**必须要求局部极大值**。
        Hann 窗会把每个谱峰展宽到 ±1 bin，若只做「首个超过 50% 峰值的 bin」，
        会锁到主峰的**裙边**（k=6 的裙边 k=5）→ 周期误报 4.8（真值 4.0）。
        最终做法：先找所有**局部极大值**，再取其中**最低频且幅度 ≥ 峰值 50%** 的那个。
    """
    vals = [float(x) for x in xs]
    n = len(vals)
    min_n = int(THRESHOLDS["min_sent_for_period"])
    reliable = n >= min_n
    if n < 4:
        return {"period": 0.0, "power_ratio": 0.0, "reliable": False,
                "peak_bin": 0, "n_peaks": 0}
    mean = sum(vals) / n
    x = [(v - mean) * w for v, w in zip(vals, _hann(n))]
    mags = _dft_magnitude(x)
    total = sum(m * m for m in mags[1:])
    if total <= 1e-12:
        return {"period": 0.0, "power_ratio": 0.0, "reliable": reliable,
                "peak_bin": 0, "n_peaks": 0}

    max_mag = max(mags[1:])
    if max_mag <= 1e-12:
        return {"period": 0.0, "power_ratio": 0.0, "reliable": reliable,
                "peak_bin": 0, "n_peaks": 0}

    # 先找局部极大值（排除裙边 bin），再取其中最低频且幅度 ≥ 峰值 50% 的
    thresh = 0.5 * max_mag
    local_max = [
        k for k in range(1, len(mags))
        if mags[k] >= thresh
        and (k == 1 or mags[k] >= mags[k - 1])
        and (k == len(mags) - 1 or mags[k] >= mags[k + 1])
    ]
    peak_k = local_max[0] if local_max else 1
    n_peaks = len(local_max)
    peak_power = mags[peak_k] ** 2
    period = n / peak_k if peak_k else 0.0
    return {
        "period": period,
        "power_ratio": peak_power / total,
        "reliable": reliable,
        "peak_bin": peak_k,
        "n_peaks": n_peaks,
    }


def alternation_rate(xs: list[float]) -> dict:
    """句长交替率：相邻差值的**符号变化**比例，∈[0,1]。

    **为什么需要它**（本维度去重的关键）：
        Gini 与 CV 都是「离散度」的两个标度，同时参与 D3 = 同一方面投两票。
        而「离散度大」不等于「长短交替」——一串单调递增的句长离散度很高，
        但读起来毫无节拍。交替率测的是**时序模式**，与离散度是不同的统计方面。

    定义：sign(x[i+1]-x[i]) 发生变化的次数 / (n-1)；差值为 0 不计变化。
    陷阱：n<5 时最多只有 4 个差值，交替率极不稳定 → reliable=False，调用方应取中性值。

    返回 {rate, changes, n_pairs, reliable}。
    """
    vals = [float(x) for x in xs]
    n = len(vals)
    pairs = max(0, n - 1)
    if pairs < 1:
        return {"rate": 0.0, "changes": 0, "n_pairs": 0, "reliable": False}

    signs: list[int] = []
    for a, b in zip(vals, vals[1:]):
        d = b - a
        if d > 1e-12:
            signs.append(1)
        elif d < -1e-12:
            signs.append(-1)
        # d ≈ 0 → 既不升也不降，不计符号（避免把「平」当成变化）

    changes = sum(1 for s1, s2 in zip(signs, signs[1:]) if s1 != s2)
    denom = max(1, len(signs) - 1)
    rate = min(1.0, changes / denom)
    return {
        "rate": rate,
        "changes": changes,
        "n_pairs": len(signs),
        "reliable": len(signs) >= 4,
    }


# ------------------------------------------------------------------ 马尔可夫
def markov_entropy_rate(states: list[str]) -> dict:
    """一阶马尔可夫链熵率 H_rate = Σ_i π_i · H(P_i·)。

    返回 {H_rate, H_max, determinism, reliable, n_states, n_transitions}。
    determinism = 1 - H_rate/H_max ∈ [0,1]：越高说明结构越固定 → 越可复制。

    陷阱规避一：转移概率按**行**归一化（除以其行和），否则不是概率分布。
    陷阱规避二：转移样本 < 10 时转移概率纯属噪声 → reliable=False。
    """
    seq = [s for s in states if s]
    n = len(seq)
    if n < 2:
        return {"H_rate": 0.0, "H_max": 0.0, "determinism": 0.0,
                "reliable": False, "n_states": len(set(seq)), "n_transitions": 0}

    trans: dict[str, dict[str, int]] = {}
    for a, b in zip(seq, seq[1:]):
        trans.setdefault(a, {})
        trans[a][b] = trans[a].get(b, 0) + 1

    total_trans = sum(sum(row.values()) for row in trans.values())
    # 经验边缘分布作为 π 的 plug-in 估计
    marg: dict[str, int] = {}
    for s in seq:
        marg[s] = marg.get(s, 0) + 1
    tot = sum(marg.values())

    h_rate = 0.0
    for state, row in trans.items():
        row_sum = sum(row.values())
        if row_sum <= 0:
            continue
        pi = marg.get(state, 0) / tot if tot else 0.0
        cond = 0.0
        for cnt in row.values():
            p = cnt / row_sum
            if p > 0:
                cond -= p * math.log2(p)
        h_rate += pi * cond

    k = max(len(set(seq)), 1)
    h_max = math.log2(k) if k > 1 else 0.0
    determinism = (1.0 - h_rate / h_max) if h_max > 0 else 0.0
    return {
        "H_rate": h_rate,
        "H_max": h_max,
        "determinism": max(0.0, min(1.0, determinism)),
        "reliable": total_trans >= int(THRESHOLDS["min_state_for_markov"]),
        "n_states": k,
        "n_transitions": total_trans,
    }
