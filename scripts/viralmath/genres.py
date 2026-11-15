"""三形态权重档：AHP 判断矩阵、维度饱和上限、参照原型、分区阈值。

⚠️ CALIBRATION_PENDING
    - 先验权重向量、饱和上限 caps、参照原型 archetypes、分区阈值均为**人工先验**。
    - 必须用真实爆款语料（每形态 ≥100 条，带完播/互动/转化真实值）回灌重估。
    - 未校准前，本引擎输出只代表**形态内相对位置**，不代表播放量预测。

AHP 矩阵构造方式（显式可审计）：
    由先验权重向量按 Saaty 整数标度离散化生成（mcdm.saaty_matrix_from_priority）。
    因此 CR 主要反映**离散化误差**；CR 门槛的作用是防止后续人工改写矩阵（或用户自定义矩阵）
    时引入不可接受的矛盾。三形态矩阵在 import 时即做 CR 硬校验，不通过直接抛异常。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import features as F
from .calibration import REFERENCE_CORPUS
from .mcdm import ahp_weights, saaty_matrix_from_priority

DIMS = ["hook", "density", "rhythm", "emotion", "persuasion", "distinction", "replicability"]

DIM_LABELS = {
    "hook": "钩子力",
    "density": "信息密度",
    "rhythm": "节奏冲击",
    "emotion": "情绪驱动",
    "persuasion": "说服转化",
    "distinction": "差异化",
    "replicability": "可复制性",
}

# 各子指标的饱和上限：达到该值即视为满分（1.0）。超过不再加分（防止长文刷分）。
CAPS: dict[str, float] = {
    "hook_weight_sum": 2.5,     # 前3句钩子加权命中数
    "surprisal": 9.0,           # 首句平均 surprisal（bits）
    "qe_first3": 2.0,           # 前3句问号+感叹号数
    "info_units": 12.0,         # 每百字信息单元数
    "vocab_entropy": 0.95,      # 归一化词汇熵
    "zipf_alpha": 1.10,         # Zipf 幂指数
    "gini": 0.45,               # 句长 Gini
    "cv": 0.75,                 # 句长变异系数
    "period": 0.35,             # 主周期能量占比
    "volatility": 0.55,         # 情绪波动率
    "slope": 0.06,              # 情绪斜率绝对值
    "cusum": 6.0,               # CUSUM 最大统计量
    "emo_density": 6.0,         # 每百字情绪词数
    "trust_density": 4.0,       # 每百字信任锚点数
    "number_density": 3.0,      # 每百字数字数
    "cta_count": 2.0,           # CTA 命中数
    "js": 0.45,                 # 与形态基线的 JS 散度（原始值，仅记录不进公式）
    "js_excess": 0.65,          # 扣除噪声地板后的超额 JS（实测：形态内≈0，跳形态0.53~0.79）
}

# 维度内部子指标权重（三形态共用）
SUB_WEIGHTS: dict[str, list[float]] = {
    "hook": [0.45, 0.30, 0.25],
    "density": [0.45, 0.35, 0.20],
    "rhythm": [0.40, 0.35, 0.25],
    "emotion": [0.28, 0.24, 0.20, 0.28],
    "persuasion": [0.40, 0.30, 0.30],
}

# 分区阈值（score100）
BANDS: list[tuple[str, float]] = [("S", 80.0), ("A", 65.0), ("B", 50.0), ("C", 35.0), ("D", 0.0)]

# 参照原型（7 维，顺序同 DIMS）：供 TOPSIS 正/负理想解与熵权法使用
ARCHETYPE_LABELS = ["顶配", "优秀", "中等", "偏弱", "差"]
ARCHETYPES: list[list[float]] = [
    [0.92, 0.86, 0.88, 0.84, 0.90, 0.72, 0.82],
    [0.76, 0.72, 0.74, 0.70, 0.74, 0.60, 0.70],
    [0.54, 0.54, 0.54, 0.54, 0.54, 0.48, 0.54],
    [0.34, 0.38, 0.34, 0.36, 0.32, 0.38, 0.38],
    [0.18, 0.22, 0.18, 0.20, 0.16, 0.24, 0.22],
]

# 理想情绪弧（用于 DTW 形态对齐）：先压痛点再逐层抬高，末尾给峰值。
# 值域与情绪有效价 [-1,1] 一致；长度固定 ARC_BUCKETS，便于跨文本比较。
ARC_BUCKETS = 12
IDEAL_ARC: list[float] = [
    -0.30, -0.45, -0.10, 0.20, 0.05, 0.30,
    0.55, 0.45, 0.70, 0.65, 0.85, 0.95,
]


@dataclass
class GenreProfile:
    name: str
    label: str
    priority: list[float]              # 先验权重向量（外露，可审计）
    alpha: float                       # 组合赋权中主观权重占比
    notes: str
    ahp_matrix: list[list[float]] = field(default_factory=list)
    archetypes: list[list[float]] = field(default_factory=lambda: [list(a) for a in ARCHETYPES])
    baseline_tokens: dict[str, int] = field(default_factory=dict)
    cr: float = 0.0

    def __post_init__(self) -> None:
        if len(self.priority) != len(DIMS):
            raise ValueError(f"{self.name}: 先验权重向量必须 {len(DIMS)} 维")
        self.ahp_matrix = saaty_matrix_from_priority(self.priority)
        res = ahp_weights(self.ahp_matrix, raise_on_inconsistent=True)  # CR 硬校验
        self.cr = res["cr"]


def _baseline_tokens(genre: str) -> dict[str, int]:
    """由参照语料构建该形态的词分布基线（JS 散度的比较对象）。"""
    texts = REFERENCE_CORPUS.get(genre, [])
    toks: list[str] = []
    for t in texts:
        toks.extend(F.tokenize(t))
    return F.token_counts(toks)


GENRES: dict[str, GenreProfile] = {
    "video": GenreProfile(
        name="video",
        label="视频口播",
        priority=[9.0, 5.0, 8.0, 7.0, 7.0, 5.0, 4.0],
        alpha=0.55,
        notes="前3秒定生死：钩子与节奏权重最高；可复制性次之（口播难以结构化复制）。",
        baseline_tokens=_baseline_tokens("video"),
    ),
    "graphic": GenreProfile(
        name="graphic",
        label="图文笔记",
        priority=[9.0, 6.0, 5.0, 7.0, 6.0, 8.0, 5.0],
        alpha=0.55,
        notes="推荐池靠首图+标题点击：钩子与差异化权重最高；节奏（句长反差）在图文里弱于视频。",
        baseline_tokens=_baseline_tokens("graphic"),
    ),
    "text": GenreProfile(
        name="text",
        label="纯文本长文",
        priority=[5.0, 7.0, 4.0, 5.0, 9.0, 6.0, 8.0],
        alpha=0.55,
        notes="长文靠论证与检索长尾：说服转化与可复制性权重最高；节奏权重最低。",
        baseline_tokens=_baseline_tokens("text"),
    ),
}


def band_of(score100: float) -> str:
    for name, lo in BANDS:
        if score100 >= lo:
            return name
    return "D"


def strong_hook_dimensions(genre: str, top_n: int = 2) -> list[str]:
    """该形态权重最高的 top_n 个维度（用于报告「该形态最该补哪块」）。"""
    p = GENRES[genre]
    idx = sorted(range(len(DIMS)), key=lambda i: -p.priority[i])[:top_n]
    return [DIMS[i] for i in idx]
