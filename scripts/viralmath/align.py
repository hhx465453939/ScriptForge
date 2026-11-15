"""序列对齐：余弦相似度、DTW 动态时间规整。

工具来源（math 种子库）：
  - 动态规划（DTW 的算法内核）→ domains/A-代数与离散/A5-离散数学.md / recipes/02-图论与离散算法.md
  - 向量相似度（余弦）→ 库内无专条，按线性代数标准定义自建（domains/A-代数与离散/A2-线性代数与矩阵论.md）

必防陷阱：
  1. DTW 距离随序列长度单调增长 → 必须除以路径长度归一化，否则长序列永远"更不像"。
  2. 余弦对零向量无定义 → 分母为 0 时回退 0。
  3. DTW 贪心最近邻邻域限制过严会漏掉正确对齐 → 默认不设窗口（全搜索），仅在超长序列时启用 Sakoe-Chiba 窗。
"""

from __future__ import annotations

import math

_EPS = 1e-12


def cosine(a: list[float], b: list[float]) -> float:
    """余弦相似度 ∈ [-1,1]；任一向量为零向量时回退 0。"""
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(float(x) * float(y) for x, y in zip(a, b))
    na = math.sqrt(sum(float(x) ** 2 for x in a))
    nb = math.sqrt(sum(float(y) ** 2 for y in b))
    if na <= _EPS or nb <= _EPS:
        return 0.0
    return max(-1.0, min(1.0, dot / (na * nb)))


def dtw_distance(a: list[float], b: list[float], window: int | None = None) -> dict:
    """DTW 距离（成本 = |a_i - b_j|）。

    返回 {dist, normalized, path_len, n, m}。
    normalized = dist / path_len：消除路径长度对距离的放大（陷阱 1 的规避）。

    复杂度 O(n·m)。句级序列长度在几十量级，无需加速结构。
    """
    n, m = len(a), len(b)
    if n == 0 or m == 0:
        return {"dist": 0.0, "normalized": 0.0, "path_len": 0, "n": n, "m": m}

    INF = float("inf")
    prev = [INF] * m
    # 记录路径长度以便归一化
    prev_len = [0] * m
    for j in range(m):
        cost = abs(float(a[0]) - float(b[j]))
        prev[j] = cost if j == 0 else prev[j - 1] + cost
        prev_len[j] = j + 1

    for i in range(1, n):
        cur = [INF] * m
        cur_len = [0] * m
        for j in range(m):
            if window is not None and abs(i - j) > window:
                continue
            cost = abs(float(a[i]) - float(b[j]))
            if j == 0:
                cur[j] = prev[0] + cost
                cur_len[j] = prev_len[0] + 1
            else:
                cand = (
                    (prev[j], prev_len[j]),        # 竖直：a 前进
                    (cur[j - 1], cur_len[j - 1]),  # 水平：b 前进
                    (prev[j - 1], prev_len[j - 1]) # 对角：同时前进
                )
                best = min(cand, key=lambda t: (t[0], -t[1]))
                cur[j] = best[0] + cost
                cur_len[j] = best[1] + 1
        prev, prev_len = cur, cur_len

    dist = prev[m - 1]
    path_len = max(prev_len[m - 1], 1)
    if dist == INF:
        return {"dist": 0.0, "normalized": 0.0, "path_len": 0, "n": n, "m": m}
    return {
        "dist": dist,
        "normalized": dist / path_len,
        "path_len": path_len,
        "n": n,
        "m": m,
    }
