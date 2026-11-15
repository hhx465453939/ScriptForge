# TRACEABILITY：爆款量化评估引擎

## 需求 → 工具 → 契约 → 产物 追溯

| 需求 | 数学工具（种子库锚点） | SPEC 条款 | 产物 | 验收 | 状态 |
|---|---|---|---|---|---|
| 钩子力可量化 | Surprisal −log p（C7 信息论） | §2 D1 | `info.py` `surprisal` | 单测：p↓ → surprisal↑ | 待验 |
| 差异化可量化 | Jensen–Shannon（C7 KL 条目衍生，避不对称陷阱） | §2 D6 | `info.py` `js_divergence` | 单测：JS∈[0,1]；同分布=0 | 待验 |
| 记忆点集中度 | Zipf log–log OLS（C3 回归） | §2 D2 | `info.py` `zipf_fit` | 单测：幂律生成序列 α≈1.0±0.15 | 待验 |
| 节奏冲击 | Gini / CV / MAD（C2 描述统计） | §2 D3 | `rhythm.py` `gini`/`cv_robust` | 单测：均匀序列 Gini=0 | 待验 |
| 节奏周期 | ACF + FFT + Hann（B8 信号） | §2 D3 | `rhythm.py` `dominant_period` | 单测：周期 4 序列检出 ≈4 | 待验 |
| 情绪弧 | OLS + CUSUM（C3/C6） | §2 D4 | `affect.py` | 单测：线性序列 slope 准确；变点检出 | 待验 |
| 主观权重客观化 | AHP 特征向量 + CR（A2 特征值） | §0.6 | `mcdm.py` `ahp_weights` | 单测：一致阵 CR<0.01；矛盾阵抛异常 | 待验 |
| 客观权重 | 熵权法（C7 熵） | §2 | `mcdm.py` `entropy_weights` | 单测：等值列 → 均权且不除零 | 待验 |
| 综合排序 | TOPSIS（库无专条，自建） | §2 | `mcdm.py` `topsis` | 单测：全优→≈1，全劣→≈0 | 待验 |
| 不确定度 | Bootstrap BCa（C2 recipes/06） | §0.3 | `uncertainty.py` | 单测：CI 含点估计；固定 seed 复现 | 待验 |
| 小样本达标率 | Beta 后验（C4 共轭先验） | §2 | `uncertainty.py` `beta_interval` | 单测：0.5 分位 ≈ successes/n | 待验 |
| 模板对齐 | 余弦 + DTW（D3 DP） | §2 D7 | `align.py` | 单测：DTW 归一化∈[0,1] | 待验 |
| 可复制性 | 马尔可夫熵率（C5） | §2 D7 | `rhythm.py` `markov_entropy_rate` | 单测：确定性序列 determinism=1 | 待验 |
| 三形态差异 | 三套 AHP 判断矩阵 | §3 | `genres.py` `GENRES` | 单测：三阵 CR 全 <0.1 | 待验 |
| 端到端可跑 | — | §5 | `viral_score.py` | CLI 退出码 0 + 两次输出一致 | 待验 |

## 诚实声明（不许越界）

以下工具在 math 种子库中**无专条**，属本 CHG 按标准定义自建，陷阱字段由本项目自行补写，不冒充库内工具：
AHP、熵权法、TOPSIS、DTW、Gini、MAD-z。

## 独占清单核对

- [x] `scripts/viralmath/**` — 仅本 CHG 创建
- [x] `scripts/viral_score.py` — 仅本 CHG 创建
- [x] `scripts/genre_probe.py` — 属 CHG-A 验收依赖，由 CHG-A 清单授权（SPEC-A §7）
- [x] `tests/test_viralmath.py` — 仅本 CHG 创建
- [x] `samples/**` — 仅本 CHG 创建（SPEC §4 rev1.1 增补）
- [x] `references/math-engine.md` — 仅本 CHG 创建
- [x] `assets/quant-scorecard-template.md` — 仅本 CHG 创建
- [x] `SKILL.md` — 本 CHG 只改：新增「定量引擎」层
- [x] `skill.manifest.json` — 本 CHG 只改：summary/trigger/required_sections
- [x] `README.md` — 本 CHG 只改：能力表 + 结构树
- [x] `assets/*.svg`、`.gitignore` — **不属本 CHG**，归 `CHG-20261115-visual-assets`

## 字段名对齐（与 CHG-A 接口）

引擎 `features.py` 输出的形态专属项，字段名必须与 SPEC-A §5.2 完全一致：
`title_len` / `emoji_count` / `para_count` / `tag_count` / `median_lines_per_para` /
`claim_count` / `evidence_ratio` / `golden_sentence_per_kchar` / `heading_count` /
`first3_chars` / `avg_sent_len` / `exclaim_count` / `second_person_count`。

---

## 验收记录（2026-11-15，实测）

### A. 全量验收命令结果

| 验收项 | 命令 | 实测结果 | 结论 |
|---|---|---|---|
| 单元测试 | `python -m unittest discover -s tests` | **Ran 75 tests — OK** | ✅ |
| 三形态评分 | `viral_score.py --file samples/{v,g,t}.txt --boot 40 --json` | video 41.78 C CI[34.55,50.07] / graphic 37.43 C CI[30.61,45.70] / text 29.13 D CI[22.56,33.02] | ✅ 均退出码 0 且带区间 |
| 复现性 | 两次 `--json` 输出 `diff` | 逐字节一致 | ✅ |
| 三形态 AHP | `ahp_weights(GENRES[k].ahp_matrix)` | CR = 0.014951 / 0.014998 / 0.016200，λmax 均 ≥ 7 | ✅ 全 <0.10 |
| 矛盾矩阵拦截 | `ahp_weights([[1,9,1/9],[1/9,1,9],[9,1/9,1]])` | 抛 `InconsistentMatrixError`，CR=6.13 | ✅ 门控生效 |
| 熵权除零保护 | `entropy_weights([[1,5],[1,5],[1,5]])` | 回退均权 [0.5, 0.5] | ✅ |
| TOPSIS 贴近度 | 全优/全劣方案 | 1.0 / 0.0 | ✅ |
| 体积红线 | `wc -l` | viralmath 2248 总 / 1847 有效；math-engine.md 331；content-genres.md 257 | ⚠️ 已按 rev1.2 修订并记录理由 |
| 附加定位输出 | 三形态 `--json` | 最像原型：中等0.815 / 偏弱0.775 / 偏弱0.753；权重契合 0.875/0.902/0.766；弧对齐 0.769–0.788 | ✅ 与分区分层自洽 |
| 模板对齐（余弦+DTW） | `align` 被 engine 实际调用 | 已接线并覆盖 4 项单测（原为死代码） | ✅ |

### B. 本会话实测发现并当轮修复的真实缺陷（不只报喜）

| # | 缺陷 | 危害 | 根因 | 修复 |
|---|---|---|---|---|
| 1 | **AHP λmax 算错**：幂迭代用和归一化（L1）却配 Rayleigh 商 | 7×7 矩阵 λmax≈**1.07**（理论必须≥7）→ CI 为负 → **CR 恒为 0，一致性门控彻底失效且不报错** | Rayleigh 商只在 ‖v‖₂=1 时成立 | 改为 L2 归一化；加回归测试 `test_ahp_lam_ge_n` |
| 2 | **主周期误判（谐波）**：脉冲串频谱等幅，argmax 锁到高次谐波 | `[1,0,0,0]×6` 周期误报 **2.0**（真值 4.0）→ 所有脉冲型节奏被判成倍频 | 取全局最大峰 ≠ 取基频 | 改为取最低频显著局部极大值 |
| 3 | **主周期误判（窗裙边）**：Hann 窗展宽 ±1 bin | 周期误报 **4.8**（真值 4.0） | 只做阈值穿越判定，未要求局部极大值 | 强制局部极大值 + 频点记录 |
| 4 | **差异化维度饱和**：JS 受参照语料规模污染 | 所有输入 D6 均 = **1.000**，零信息量的假指标 | 基线仅 3 段/700 字，词表覆盖度差被当成风格差 | 自建 `js_null_floor` 噪声地板扣除；校正后分离度：形态内≈0 / 跨形态 0.53–0.79 |
| 5 | **中位数逻辑重复实现**：`features.median_of` 与 `rhythm.median` | 双份实现易漂移 | 未建单一事实来源 | `median_of` 改为转发 `rhythm.median` |
| 6 | **`align.py` 是死代码**：SPEC 冻结了 `cosine`/`dtw_distance`，有单测但引擎从未调用 | 工具存在但能力不可达；也是「冻结了却不接线」的契约落空 | 只写了工具没接进链路 | 接入：`archetype_match`（原型定位）、`profile_fit`（权重契合）、`arc_alignment`（情绪弧 DTW 对齐）；并补 4 项单测 |
| 7 | **测度选错：用余弦判「水平」** | 首次接线后用余弦算「最像哪个原型」，得出 **video 样本最像「差」原型 cos=0.977**——C 区样本被判成最差，结论完全错误 | 七维全非负且量级相近，**余弦只测夹角不测水平**，原型间水平差被抹平 | 改为归一化欧氏距离（水平用距离）；余弦改用在它真正适用的「形状」问题上（`profile_fit`）；加回归测试 `test_archetype_not_top_when_score_low` |

**已试过但否定的方案（记录以免后人重走）**：
- top-K 截断降 JS 规模效应 → 反而更糟（in-ref 中位数从 0.47 升到 0.78–0.86，跨形态撞 1.0），因截断后两分布近乎不相交。

### C. 遗留与边界（不掩盖）

| 项 | 状态 | 说明 |
|---|---|---|
| 校准 | `CALIBRATION_PENDING` | 词表/caps/参照原型/分区阈值全为人工先验，需真实爆款语料按 `math-engine.md` §7 回灌 |
| 播放量预测 | 明确不做 | 无因果识别，只给形态内相对位置 |
| 中文分词 | 字符二元组近似 | 分布型指标不受影响，句法级特征做不了 |
| 跨形态比较 | 禁止 | 三形态权重档与基线不同，绝对分不可比 |
