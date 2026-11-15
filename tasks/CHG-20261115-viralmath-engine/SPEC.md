---
change_id: CHG-20261115-viralmath-engine
version: 1.0
status: spec_frozen
parent_spec: null
prev_spec: null
prd_ref: null  # 需求 = CHANGE §0.1 Owner 原话 + §0.2 实测审计
approved_by: Owner
approved_at: 2026-11-15
---

# SPEC：爆款量化评估引擎

## 0. 收敛原则

1. **零依赖**：只用 Python 标准库（`math`/`statistics`/`random`/`re`/`json`/`argparse`/`collections`）。禁止 numpy/scipy/sklearn——skill 要能被任何宿主直接跑。
2. **可复现**：所有随机过程必须接受 `--seed`，默认 20260101；同输入同 seed 结果逐位一致。
3. **无误差棒不算结论**：综合分必须输出 95% Bootstrap CI，禁止裸标量。
4. **公式必须可回溯**：每个维度分数能在 `feature_trace` 里找到来源计数。
5. **不预测播放量**：输出只给「形态内相对分区（S/A/B/C/D）」+ 短板，禁止声称预测。
6. **AHP 硬校验**：判断矩阵 CR>0.1 直接抛 `InconsistentMatrixError`，不许静默放行。
7. **体积红线（rev1.2 修订，附实测）**：
   - 原定：`scripts/viralmath/` 总行数 ≤ 1400。
   - **实测超限：2160 行（去注释与空行后 1774 行）**。不静默放过，此处显式记录并重定基线。
   - 根因：红线制定于实现前，未评估**零依赖约束**的真实代价——18 个数学工具要在纯标准库下实现
     （无 numpy/scipy，需自建 DFT、Beta 分位、幂迭代、DTW），且有库版本可一行完成的事在这里要几十行。
     另，‘陷阱注释’本身是交付物（SPEC §0.8 可审计性要求），不能当水肿删。
   - 重定红线：**有效代码行（去注释与空行）≤ 1800，总行数 ≤ 2200**；超标仍需 SPEC 修订。
   - 同时已做的真实精简：`features.median_of` 与 `rhythm.median` 的重复实现已合并为单一事实来源。
   - `references/math-engine.md` ≤ 500 行（实测 308 ✓）。
8. **校准诚实**：词表/阈值常量全部集中在 `calibration.py` 并标 `CALIBRATION_PENDING`。

---

## 1. 契约：模块结构（冻结）

```
scripts/
├── viral_score.py              # CLI 入口
└── viralmath/
    ├── __init__.py
    ├── features.py             # 分句/分词/计数 → FeatureSet
    ├── info.py                 # 熵/Surprisal/JS/Zipf
    ├── rhythm.py               # Gini/CV/MAD/ACF/FFT/Markov 熵率
    ├── affect.py               # 情绪序列/OLS 斜率/CUSUM
    ├── mcdm.py                 # AHP/熵权/组合赋权/TOPSIS
    ├── uncertainty.py          # Bootstrap BCa/Beta 后验
    ├── align.py                # 余弦/DTW
    ├── genres.py               # 三形态 AHP 矩阵 + 指标方向 + 基线
    ├── calibration.py          # 词表与阈值常量（标 CALIBRATION_PENDING）
    └── engine.py               # 编排：特征→指标→维度→权重→TOPSIS→CI
```

**冻结 API**（下游文档与测试依赖，不得改名）：

| 模块 | 符号 | 签名 |
|---|---|---|
| features | `extract` | `extract(text, genre="auto") -> FeatureSet` |
| info | `shannon_entropy` | `(counts: dict[str,int]) -> float` (bits) |
| info | `surprisal` | `(p: float) -> float` (bits, 已平滑) |
| info | `js_divergence` | `(p: dict, q: dict) -> float` (bits, ∈[0,1]) |
| info | `zipf_fit` | `(counts: dict) -> dict` → `{alpha, r2, n}` |
| rhythm | `gini` | `(xs: list[float]) -> float` |
| rhythm | `cv_robust` | `(xs: list[float]) -> dict{mean,std,cv,mad,cv_robust}` |
| rhythm | `acf` | `(xs: list[float], max_lag=10) -> list[float]` |
| rhythm | `dominant_period` | `(xs: list[float]) -> dict{period, power_ratio, reliable}` |
| rhythm | `markov_entropy_rate` | `(states: list[str]) -> dict{H_rate, H_max, determinism, reliable}` |
| affect | `ols_slope` | `(ys: list[float]) -> dict{slope, se, t, r2}` |
| affect | `cusum_changepoints` | `(ys: list[float], h=4.0) -> dict{points, max_stat}` |
| mcdm | `ahp_weights` | `(matrix: list[list[float]]) -> dict{weights, cr, lambda_max}` |
| mcdm | `entropy_weights` | `(matrix: list[list[float]]) -> list[float]` |
| mcdm | `combine_weights` | `(w_subj, w_obj, alpha=0.5) -> list[float]` |
| mcdm | `topsis` | `(matrix, weights, benefit: list[bool]) -> dict{scores, d_plus, d_minus}` |
| uncertainty | `bootstrap_ci` | `(xs, stat_fn, n_boot=2000, seed=...) -> dict{point, lo, hi}` |
| uncertainty | `beta_interval` | `(successes, n, prior=(1,1)) -> dict{mean, lo, hi}` |
| align | `cosine` | `(a: list[float], b: list[float]) -> float` |
| align | `dtw_distance` | `(a: list[float], b: list[float]) -> dict{dist, normalized}` |
| genres | `GENRES` | `dict[str, GenreProfile]`，键 = `video`/`graphic`/`text` |
| engine | `score` | `(text, genre="auto", seed=20260101) -> dict` |

---

## 2. 契约：维度定义（冻结）

7 个维度，每维 ∈ [0,1]（已归一化，1 最好），全部为**效益型**（TOPSIS 里方向一致）：

| # | 维度键 | 中文名 | 计算链 |
|---|---|---|---|
| D1 | `hook` | 钩子力 | 首句 surprisal（平滑后）+ 首 3 句问号/感叹/冲突词加权 → sigmoid 归一 |
| D2 | `density` | 信息密度 | 每百字信息单元数 + 词汇熵相对基线 → 线性截断归一 |
| D3 | `rhythm` | 节奏冲击 | Gini(句长) + cv_robust + ACF 周期显著性 → 加权 |
| D4 | `emotion` | 情绪驱动 | 情绪序列波动率 + |OLS 斜率| + CUSUM 变点强度 → 加权 |
| D5 | `persuasion` | 说服转化 | 信任锚密度 + 数字密度 + CTA 位置收益衰减 → 加权 |
| D6 | `distinction` | 差异化 | `js = JS(文本词分布 ‖ 形态基线)`；`floor = js_null_floor(基线, |tokens|)`；`excess = max(0, js − floor)`；`distinction = min(1, excess / cap_excess)`，cap_excess=0.65<br>**rev1.1**：原写 `1 − JS`，方向反了（JS 小=同质=没有差异化）。<br>**rev1.2**：必须扣除**词表规模噪声地板**——小基线（3 段/700 字）下，任何真实文本的 JS 都会被词表覆盖度差异抬高；实测未校正时该维对所有输入饱和到 1.000（零信息量），校正后分离度：形态内≈0、跨形态 0.53–0.79。 |
| D7 | `replicability` | 可复制性 | 1 − 马尔可夫熵率归一（越确定越可复制） |

**综合分**：TOPSIS 贴近度 C* ∈ [0,1] → `score100 = 100·C*`；分区 S≥80 / A≥65 / B≥50 / C≥35 / D<35（阈值在 `genres.py` 可覆盖）。

**不确定度**：对 FeatureSet 的句级重采样（sentence bootstrap）重算全链 2000 次 → 综合分 2.5%/97.5% 分位；同时给出每维 CI。

**附加定位输出（rev1.2 新增，非七维的一部分）**：

| 字段 | 工具 | 回答的问题 | 为何用这个测度 |
|---|---|---|---|
| `archetype_match` | 归一化欧氏距离 `1-‖dims-arch‖/√n` | 「本文处于哪个水平」 | **水平问题用距离**。余弦对七维全非负向量几乎恒≈1，实测把 C 区样本误判为「最像差原型 cos=0.977」 |
| `profile_fit` | `cos(dims, 形态先验权重)` | 「力气是否花在本形态最看重的维度上」 | **形状问题用夹角**。二者同量纲不同尺度，余弦才是对工具 |
| `arc_alignment` | DTW（已除路径长归一化） | 「情绪弧怎么走」 | 七维只量强度不量走向；上升弧与坠落弧同强度但传播差异大 |

---

## 3. 契约：形态权重档（冻结）

三形态各一份 AHP 判断矩阵（7×7，Saaty 1–9 标度），必须 CR<0.1：

- `video`：节奏与钩子优先（前3秒定生死）
- `graphic`：标题/钩子 + 差异化优先（推荐池靠首图点击）
- `text`：说服与可复制性优先（长文靠论证与检索长尾）

判定矩阵、指标基线均值、分区阈值统一放 `genres.py`；词表放 `calibration.py`。

---

## 4. 交付清单（清单外不建文件）

| 路径 | 类型 |
|---|---|
| `tasks/CHG-20261115-viralmath-engine/{CHANGE,SPEC,TRACEABILITY,TASK_ORCHESTRATION}.md` | 新建 |
| `scripts/viralmath/__init__.py` | 新建 |
| `scripts/viralmath/calibration.py` | 新建 |
| `scripts/viralmath/features.py` | 新建 |
| `scripts/viralmath/info.py` | 新建 |
| `scripts/viralmath/rhythm.py` | 新建 |
| `scripts/viralmath/affect.py` | 新建 |
| `scripts/viralmath/mcdm.py` | 新建 |
| `scripts/viralmath/uncertainty.py` | 新建 |
| `scripts/viralmath/align.py` | 新建 |
| `scripts/viralmath/genres.py` | 新建 |
| `scripts/viralmath/engine.py` | 新建 |
| `scripts/viral_score.py` | 新建 |
| `scripts/genre_probe.py` | 新建（CHG-A 依赖的形态判定 CLI） |
| `tests/test_viralmath.py` | 新建（标准库 unittest，零依赖） |
| `samples/video.txt` | 新建（形态判定与 CLI 验收样本） |
| `samples/graphic.txt` | 新建（同上） |
| `samples/text.txt` | 新建（同上） |
| `references/math-engine.md` | 新建 |
| `assets/quant-scorecard-template.md` | 新建 |
| `SKILL.md` | 修改（加「定量引擎」层） |
| `skill.manifest.json` | 修改 |
| `README.md` | 修改 |

## 5. 验收命令（全部必须退出码 0）

```bash
python -m unittest discover -s tests -v
python scripts/viral_score.py --file samples/video.txt --json
python scripts/viral_score.py --file samples/graphic.txt --json
python scripts/viral_score.py --file samples/text.txt --json
# 复现性：两次输出完全一致
python scripts/viral_score.py --file samples/video.txt --json > /tmp/a.json
python scripts/viral_score.py --file samples/video.txt --json > /tmp/b.json
diff /tmp/a.json /tmp/b.json
# AHP 一致性门
python -c "from viralmath.mcdm import ahp_weights; print(ahp_weights([[1,2],[0.5,1]]))"
```

## 6. 回归保护

- 不改动既有 3 个口播模型、既有 9 板块顺序
- 引擎为**增量能力**：不调 CLI 时 SKILL.md 原流程照常可用
- `platform-insights.md` 不改（它是定性洞察，引擎不依赖它）
