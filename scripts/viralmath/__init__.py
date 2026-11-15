"""viralmath —— 爆款量化评估引擎（零依赖，纯标准库）。

模块导航：
    calibration  词表 / 阈值 / 参照语料（全部标 CALIBRATION_PENDING）
    features     分句分词 / 计数 / 形态判定 → FeatureSet
    info         香农熵、Surprisal、Jensen-Shannon、Zipf 拟合
    rhythm       Gini、稳健 CV、ACF、主周期、马尔可夫熵率
    affect       OLS 斜率、CUSUM 变点、情绪序列
    mcdm         AHP、熵权法、组合赋权、TOPSIS
    uncertainty  Bootstrap(BCa) 置信区间、Beta 后验
    align        余弦、DTW
    genres       三形态权重档 + AHP 判断矩阵（CR 硬校验）
    engine       编排：特征 → 7 维 → 权重 → TOPSIS → 综合分 + CI

参见 references/math-engine.md（公式 / 陷阱 / 解读协议）。
"""

__all__ = [
    "calibration", "features", "info", "rhythm", "affect",
    "mcdm", "uncertainty", "align", "genres", "engine",
]

__version__ = "1.0.0"
