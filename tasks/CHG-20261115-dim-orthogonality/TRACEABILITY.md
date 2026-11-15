# TRACEABILITY：七维正交性修复

## 需求 → 契约 → 产物 追溯

| 需求 / 判定 | SPEC 条款 | 产物 | 验收方式 | 立契状态 |
|---|---|---|---|---|
| D1 不再与 D2 共源（词汇轴） | §1.1 | `engine.py` D1 重构 | 源依赖矩阵 token_counts × D1 = 0 | 待验 |
| D2 去掉同源双计（熵 vs Zipf α） | §1.2 | `engine.py` D2 + `genres.SUB_WEIGHTS` | D2 子指标数 = 2，Zipf 仅诊断 | 待验 |
| D3 去掉同源双计（Gini vs CV） | §1.3 | `rhythm.alternation_rate` + `engine.py` | D3 三子指标分属 分布/时序/周期 | 待验 |
| D4 去掉同源双计（波动率 vs CUSUM） | §1.4 | `affect.peak_position` + `engine.py` | D4 四子指标分属 振幅/方向/位置/词汇 | 待验 |
| 可被第三方复现的审计 | §2 | `scripts/dim_audit.py` | 四块输出齐全，`--strict` 违规即非零退出 | 待验 |
| 小样本诚实 | §2 | 审计工具 | n<30 打印警告 | 待验 |
| 口径五处一致 | §3 | engine / math-engine / SKILL / README / manifest | grep 校验维度定义 | 待验 |
| 七维键名不变（零破坏） | §6 | engine 返回结构 | 键名断言 | 待验 |
| 分数变化有交代 | §0.8 | 本文件 §C | 三形态改前改后对照 | 待验 |

## 独占清单核对（防越界）

- [x] `scripts/viralmath/rhythm.py` — 仅新增 `alternation_rate`
- [x] `scripts/viralmath/affect.py` — 仅新增 `peak_position`
- [x] `scripts/viralmath/genres.py` — 仅改 `SUB_WEIGHTS` 与 `CAPS`
- [x] `scripts/viralmath/engine.py` — 仅重构 D1/D2/D3/D4 子指标与 trace
- [x] `scripts/dim_audit.py` — 仅本 CHG 创建
- [x] `tests/test_viralmath.py` — 仅追加正交性/审计/新测度测试
- [x] `references/math-engine.md` — 仅改 §2 维度定义 + 新增 §2.6
- [x] `SKILL.md` / `README.md` / `skill.manifest.json` — 仅改口径表述

## A. 实测验收记录

| 验收项 | 命令 | 实测结果 | 结论 |
|---|---|---|---|
| 全量单测 | `python -m unittest discover -s tests` | Ran **91 tests — OK** | ✅ |
| 审计结构层 | `python scripts/dim_audit.py --strict` | 块2 **PASS**（无同源同方面违规），exit=0 | ✅ |
| 审计与实现一致 | `assert_contract()` 运行时反查 | 5 个维度声明项数 == 实现 `sub` 项数 | ✅ |
| 审计四块齐备 | `dim_audit.py` | 块1 源依赖矩阵 / 块2 违规 / 块3 双口径相关 / 块4 有效维度 | ✅ |
| 小样本警告 | 同上 | n=12 < 30 → 打印「仅作健全性检查，不作结论」 | ✅ |
| 七维键名不变 | `test_score_contract_keys` | 7 个键名均存在 | ✅ |
| AHP/TOPSIS 未动 | `test_cr_below_limit` | CR = 0.0162 < 0.10 | ✅ |
| 新测度可用 | `alternation_rate` / `peak_position` | 交替序列 rate=1.0、单调序列 0.0；峰值位置 [0,0,1,0,0]→0.5 | ✅ |

## A2. 去重效果（实测，同一审计命令前后对照）

| 项 | rev1.0 | rev1.3 | 变化 |
|---|---|---|---|
| 块2 违规数 | — | 0 | 结构层无同源同标度 |
| `density ↔ hook` r | 0.66 | 0.29 | ✅ 降 |
| `density ↔ emotion` r | 0.87 | -0.02 | ✅ 降 |
| `density ↔ persuasion` r | 0.79 | -0.08 | ✅ 降 |
| 去体裁均值参与率 | 3.28 | 3.476 | 有效维度略升 |
| 最大非对角 \|r\| | 0.865 | 0.906（`rhythm↔distinction`） | ⚠️ 未解决，见 §D |

## B. 新测度的边界

| 测度 | 最小样本 | 不可靠时的处理 |
|---|---|---|
| `alternation_rate` | n ≥ 5 | `reliable=False`，D3 该项取中性 0.5 |
| `peak_position` | n ≥ 5 | `reliable=False`，D4 该项取中性 0.5 |

## C. 分数变化交代

本 CHG 改变了子指标构成，三形态样本分数必然变化。现列改前改后并交代原因（禁止静默变化）。

| 样本 | 改前（含序数词修复后） | 改后 | 变化 | 原因 |
|---|---|---|---|---|
| video | 43.08 | **47.15** | +4.07 | 移除情绪词密度后 D4 不再被低词频拖低；说服维改由信任锚+CTA 主导 |
| graphic | 38.15 | **36.70** | -1.45 | 数字从说服移到信息密度，该样本数字少 → 说服略降 |
| text | 29.82 | **31.17** | +1.35 | 信息密度改由具体数字+词汇熵构成，该样本数字密度不高但熵较高 |

**结论**：变化方向可由「数字/信任锚归属重分配」解释，不是模型抖动。
所有分数仍属 `CALIBRATION_PENDING`，**不可**跨形态比较绝对值。

## D. 已知残留共线性（不掩盖）

| 残留 | 性质 | 为什么保留 |
|---|---|---|
| **`rhythm ↔ distinction` r = 0.906**（去体裁均值，n=12） | **未解决**。假设：两者都在代理「文本有多不寻常」——句长越散、越大偏离基线词表 | n=12（text 组仅 2 样本），去均值后 df≈9，**无法裁决**。需 n≥30 复核；不凭空构造修法。已在 `dim_audit.py` 输出中显式列出 |
| D2 熵 与 D6 JS 同用 `token_counts` | D2 = 内部离散度；D6 = 相对基线的距离 | 量纲与语义不同（绝对 vs 相对），且 D6 是差异化唯一定义方式 |
| D3 三项同用 `sent_lengths` | 分属 分布 / 时序 / 周期 三个统计方面 | 一条序列可提取多个不同方面；已用交替率替换纯离散度重复项 |
| D4 三项同用 `emotion_series` | 分属 振幅 / 方向 / 位置 | 同上；峰值位置用 `emotion_arousal` 而非 valence，进一步降耦 |

## E. 口径诚实声明

本 CHG 后**不再声称「七维相互独立」**。准确表述：

> 七个评分维度，结构层已去重（无同一统计量的两个标度）；
> 统计层在参考语料（n=12）上测得有效维度 ≈ 3.5，
> 该数字不可作结论，仅说明「七维不等于七个独立证据」。

待真实语料 n≥30 时，用 `python scripts/dim_audit.py --dir <语料>` 重跑并更新本节数字。
