"""多准则决策：AHP 权重、熵权法、组合赋权、TOPSIS。

⚠️ 诚实声明：AHP / 熵权法 / TOPSIS 在 math 种子库中**无专条**，本模块按标准定义自建。
   其中 AHP 主特征向量部分复用库内「特征值分解」思想（domains/A-代数与离散/A2-线性代数与矩阵论.md，
   锚点 np.linalg.eig）——本项目用幂迭代（Perron–Frobenius）实现，避开展式求解。

必防陷阱（本项目自行补写）：
  1. AHP 一致性比率 CR > 0.1 时判断矩阵自相矛盾，权重不可用 → 直接抛异常，禁止静默放行。
  2. Saaty 标度对微小改动敏感 → 矩阵必须显式可审计（用上三角 21 个值构造）。
  3. 熵权法在指标等值时 d_j=0，归一化分母为 0 → 加 ε 保护并回退均权。
  4. TOPSIS 必须先做向量归一化（否则量纲吞掉权重），且成本型/效益型方向必须显式声明。
  5. 贴近度分母 d+ + d- 可能为 0（与正负理想解同时重合）→ 回退 0.5。
"""

from __future__ import annotations

import math

# Saaty 随机一致性指标 RI（n=1..15）
RI_TABLE: dict[int, float] = {
    1: 0.0, 2: 0.0, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24, 7: 1.32,
    8: 1.41, 9: 1.45, 10: 1.49, 11: 1.51, 12: 1.48, 13: 1.56, 14: 1.57, 15: 1.59,
}

CR_LIMIT = 0.10
EPS = 1e-12


class InconsistentMatrixError(ValueError):
    """AHP 判断矩阵一致性比率超限。"""


# ---------------------------------------------------------------- 矩阵构造
def saaty_snap(r: float) -> float:
    """把任意比值吸附到 Saaty 1-9 整数标度（含倒数）。

    陷阱：不吸附会得到 CR≈0 的"完美一致"矩阵，AHP 就退化成把先验权重换个写法——失去审计价值。
    """
    if r <= 0:
        return 1.0
    if r >= 1.0:
        return float(min(9, max(1, int(round(r)))))
    return 1.0 / float(min(9, max(1, int(round(1.0 / r)))))


def matrix_from_upper(n: int, upper: list[float]) -> list[list[float]]:
    """由上三角 n(n-1)/2 个判断值构造对称互反矩阵（a_ji = 1/a_ij，对角 1）。"""
    need = n * (n - 1) // 2
    if len(upper) != need:
        raise ValueError(f"上三角需要 {need} 个值，收到 {len(upper)} 个")
    m = [[1.0] * n for _ in range(n)]
    idx = 0
    for i in range(n):
        for j in range(i + 1, n):
            v = float(upper[idx])
            idx += 1
            if v <= 0:
                raise ValueError("判断值必须为正（Saaty 标度 1/9..9）")
            m[i][j] = v
            m[j][i] = 1.0 / v
    return m


def saaty_matrix_from_priority(w: list[float]) -> list[list[float]]:
    """由先验权重向量按 Saaty 整数标度构造判断矩阵。

    说明：本项目用此法生成三形态判断矩阵。CR 因此主要反映**离散化误差**，
    其门槛作用是防止后续人工调整矩阵（或用户自定义矩阵）时引入不可接受的矛盾。
    """
    n = len(w)
    return matrix_from_upper(n, [saaty_snap(w[i] / w[j]) for i in range(n) for j in range(i + 1, n)])


# ---------------------------------------------------------------- AHP
def _principal_eigenvector(matrix: list[list[float]], max_iter: int = 1000, tol: float = 1e-14) -> tuple[list[float], float]:
    """幂迭代求主特征向量与主特征值（Perron 根）。

    正互反矩阵的主特征向量唯一且为正 → 归一化为权重。

    ⚠️ 关键实现点（踩过的坑）：迭代向量必须用 **L2 归一化**，
       Rayleigh 商 λmax = vᵀ(Av) 只在 ‖v‖₂=1 时成立。
       若用 L1（和）归一化，λmax 会被压到 ~1，使 CI/CR 恒为 0，
       一致性门控彻底失效——这是必须防的静默错误。
    """
    n = len(matrix)
    v = [1.0 / math.sqrt(n)] * n
    for _ in range(max_iter):
        av = [sum(matrix[i][j] * v[j] for j in range(n)) for i in range(n)]
        norm = math.sqrt(sum(x * x for x in av))
        if norm <= EPS:
            break
        v_new = [x / norm for x in av]
        diff = max(abs(a - b) for a, b in zip(v_new, v))
        v = v_new
        if diff < tol:
            break
    av = [sum(matrix[i][j] * v[j] for j in range(n)) for i in range(n)]
    lam = sum(v[i] * av[i] for i in range(n))   # Rayleigh 商，‖v‖₂ = 1
    s = sum(v)
    return ([x / s for x in v] if s > EPS else [1.0 / n] * n), lam


def ahp_weights(matrix: list[list[float]], raise_on_inconsistent: bool = True) -> dict:
    """AHP：返回 {weights, lambda_max, ci, ri, cr, consistent, n}。

    陷阱规避：CR = CI/RI，CI = (λmax - n)/(n - 1)。CR > 0.1 说明判断自相矛盾，
             默认抛 InconsistentMatrixError（SPEC §0.6 硬门控）。
    """
    n = len(matrix)
    if n == 0:
        raise ValueError("判断矩阵为空")
    for row in matrix:
        if len(row) != n:
            raise ValueError("判断矩阵必须为方阵")
    if n <= 2:
        w, lam = _principal_eigenvector(matrix)
        return {"weights": w, "lambda_max": lam, "ci": 0.0, "ri": 0.0,
                "cr": 0.0, "consistent": True, "n": n}
    w, lam = _principal_eigenvector(matrix)
    ci = (lam - n) / (n - 1)
    ri = RI_TABLE.get(n, 1.59)
    cr = (ci / ri) if ri > EPS else 0.0
    cr = max(0.0, cr)
    consistent = cr <= CR_LIMIT
    if not consistent and raise_on_inconsistent:
        raise InconsistentMatrixError(
            f"AHP 一致性比率 CR={cr:.4f} > {CR_LIMIT}（λmax={lam:.4f}, n={n}）。"
            f"判断矩阵自相矛盾，请重调后重试。"
        )
    return {"weights": w, "lambda_max": lam, "ci": ci, "ri": ri,
            "cr": cr, "consistent": consistent, "n": n}


# ---------------------------------------------------------------- 熵权法
def entropy_weights(matrix: list[list[float]], benefit: list[bool] | None = None) -> list[float]:
    """熵权法：按各指标在样本间的**区分度**赋权（区分度大 → 信息量大 → 权重大）。

    参数 matrix：m 个方案 × n 个指标的原始值。
    陷阱规避：某指标在所有方案上取值相同 → p 全等 → e_j=1 → d_j=0；
              若全部 d_j 都为 0 则分母为 0，回退为均权。
    """
    m = len(matrix)
    if m == 0:
        return []
    n = len(matrix[0])
    if n == 0:
        return []
    dirs = benefit or [True] * n
    # 成本型指标先取倒数翻转（避免负值：加一个正的平移量前先确保非负，此处只做方向统一的最小处理）
    norm: list[list[float]] = []
    for row in matrix:
        r = []
        for j in range(n):
            v = float(row[j])
            r.append(v if dirs[j] else (1.0 / (v + EPS) if v >= 0 else 1.0 / (EPS - v)))
        norm.append(r)

    d: list[float] = []
    for j in range(n):
        col = [norm[i][j] for i in range(m)]
        s = sum(col)
        if s <= EPS:
            d.append(0.0)
            continue
        p = [c / s for c in col]
        e = -sum((pi * math.log(pi) for pi in p if pi > EPS)) / math.log(m) if m > 1 else 1.0
        e = min(1.0, max(0.0, e))
        d.append(1.0 - e)
    total = sum(d)
    if total <= EPS:
        return [1.0 / n] * n
    return [x / total for x in d]


# ---------------------------------------------------------------- 组合赋权
def combine_weights(w_subj: list[float], w_obj: list[float], alpha: float = 0.5) -> list[float]:
    """组合赋权：w = α·w_subj + (1-α)·w_obj，再归一化。

    alpha 越大越信任主观先验（AHP）；越小越信任样本内的客观区分度（熵权）。
    陷阱：两权重长度不一致时直接报错，不许静默截断。
    """
    if len(w_subj) != len(w_obj):
        raise ValueError("主观权重与客观权重长度必须一致")
    if not (0.0 <= alpha <= 1.0):
        raise ValueError("alpha 必须 ∈ [0,1]")
    a = max(0.0, min(1.0, alpha))
    mixed = [a * s + (1.0 - a) * o for s, o in zip(w_subj, w_obj)]
    total = sum(mixed)
    if total <= EPS:
        return [1.0 / len(mixed)] * len(mixed)
    return [x / total for x in mixed]


# ---------------------------------------------------------------- TOPSIS
def topsis(matrix: list[list[float]], weights: list[float], benefit: list[bool] | None = None) -> dict:
    """TOPSIS：向量归一化 → 加权 → 正/负理想解 → 相对贴近度 C* ∈ [0,1]。

    返回 {scores, d_plus, d_minus, ideal_best, ideal_worst}。
    陷阱规避一：不做向量归一化则量纲大的指标霸占全部权重。
    陷阱规避二：成本型指标必须显式声明（benefit=False），否则方向反了结论全错。
    陷阱规避三：d+ + d- = 0 时贴近度无定义 → 回退 0.5。
    """
    m = len(matrix)
    if m == 0:
        return {"scores": [], "d_plus": [], "d_minus": [], "ideal_best": [], "ideal_worst": []}
    n = len(matrix[0])
    dirs = benefit or [True] * n
    if len(weights) != n:
        raise ValueError("权重长度与指标数不一致")

    # 1) 向量归一化 r_ij = x_ij / sqrt(Σ_i x_ij²)
    r: list[list[float]] = [[0.0] * n for _ in range(m)]
    for j in range(n):
        norm = math.sqrt(sum(float(matrix[i][j]) ** 2 for i in range(m)))
        for i in range(m):
            r[i][j] = (float(matrix[i][j]) / norm) if norm > EPS else 0.0

    # 2) 加权
    v = [[r[i][j] * weights[j] for j in range(n)] for i in range(m)]

    # 3) 正/负理想解
    best = [0.0] * n
    worst = [0.0] * n
    for j in range(n):
        col = [v[i][j] for i in range(m)]
        if dirs[j]:
            best[j], worst[j] = max(col), min(col)
        else:
            best[j], worst[j] = min(col), max(col)

    # 4) 距离与贴近度
    d_plus: list[float] = []
    d_minus: list[float] = []
    scores: list[float] = []
    for i in range(m):
        dp = math.sqrt(sum((v[i][j] - best[j]) ** 2 for j in range(n)))
        dm = math.sqrt(sum((v[i][j] - worst[j]) ** 2 for j in range(n)))
        d_plus.append(dp)
        d_minus.append(dm)
        denom = dp + dm
        scores.append(dm / denom if denom > EPS else 0.5)
    return {"scores": scores, "d_plus": d_plus, "d_minus": d_minus,
            "ideal_best": best, "ideal_worst": worst}
