---
change_id: CHG-20261115-dim-orthogonality
version: 1.0
status: spec_frozen
parent_spec: CHG-20261115-viralmath-engine/SPEC.md
prev_spec: null
prd_ref: CHANGE.md §0（Owner 原话 + 实测审计）
approved_by: Owner
approved_at: 2026-11-15
---

# SPEC：七维正交性修复

## 0. 收敛原则

1. **一维一方面**：同一维度内的子指标必须测**不同方面**（分布/趋势/位置/周期），禁止「同一统计量的不同标度」（如 Gini 与 CV）。
2. **一源一轴**：同一原始数据源原则上只驱动一个维度；若必须有第二个，必须是**相对量或位置量**，并在文档显式说明。
3. **可验证优先**：去重结论必须能被第三方用 `scripts/dim_audit.py` 复现，不接受「我算过了」。
4. **小样本诚实**：n < 30 时相关系数只作健全性检查，工具必须打印警告，不得据此下结论。
5. **口径单一**：维度定义只写在 `references/math-engine.md` §2；其他文件只引用。
6. **零依赖**：仍纯标准库。
7. **零破坏**：AHP 矩阵结构、TOPSIS 机制、分区阈值方式、7 维输出键名（`hook/density/rhythm/emotion/persuasion/distinction/replicability`）保持不变，避免下游断裂。
8. **分数变化必须交代**：TRACEABILITY 记录改前改后三形态分数与原因，禁止静默变化。

---

## 1. 契约：新子指标定义（冻结）

### 1.1 D1 钩子力 → 移到「位置轴」

| 子指标 | 权重 | 定义 | 数据源 |
|---|---|---|---|
| 钩子加权命中 | 0.40 | 前 3 句钩子词表命中 × 类型权重，饱和上限 2.5 | 词表 |
| 前 3 句标点强度 | 0.30 | 前 3 句 `？！` 计数，上限 2.0 | 位置 |
| **前 3 句字数占比** | **0.30** | `first3_chars / n_chars`，上限 0.35 | **位置** |

**移除**：首句 surprisal（与 D2 的熵同源）。
**理由**：钩子力应回答「开头有没有把力气放对位置」，不是「用词多罕见」。后者归 D2。

### 1.2 D2 信息密度 → 保留「词汇轴」，去掉同源双计

| 子指标 | 权重 | 定义 | 数据源 |
|---|---|---|---|
| 信息单元密度 | 0.55 | 每百字（数字+信任锚+钩子）数，上限 12 | 词表 |
| 归一化词汇熵 | 0.45 | `H/log2|V|`，上限 0.95 | token_counts |

**移除**：Zipf α（与归一化熵同源且强负相关），降级为 `feature_trace` 里的**诊断输出**，不再计分。
**理由**：熵衡量「分布有多散」，Zipf α 衡量「尾部有多重」，两者在单一序列上互为镜像，同时计分＝重复投票。

### 1.3 D3 节奏冲击 → 「长度动态轴」，三个不同方面

| 子指标 | 权重 | 定义 | 方面 | 数据源 |
|---|---|---|---|---|
| Gini(句长) | 0.40 | 离散度 | **分布** | sent_lengths |
| **句长交替率** | **0.35** | 相邻句长差值的符号变化比例 | **时序模式** | sent_lengths |
| 主周期能量占比 | 0.25 | DFT 基频显著峰能量占比 | **周期性** | sent_lengths |

**移除**：CV（与 Gini 同为离散度）。
**新增** `rhythm.alternation_rate(xs)`：相邻差符号变化数 / (n-1)，∈[0,1]；n<5 时 `reliable=False`。
**理由**：同一句长向量上，**离散度**（大小差多少）、**交替率**（是否长短交替）、**周期性**（是否循环）是三个统计上不同的方面。而 Gini 与 CV 只是同一个方面的两种标度。

### 1.4 D4 情绪驱动 → 「情绪动态轴」，三个不同方面

| 子指标 | 权重 | 定义 | 方面 | 数据源 |
|---|---|---|---|---|
| 情绪波动率 | 0.35 | 序列标准差 | **振幅** | emotion_valence |
| 情绪趋势绝对值 | 0.25 | OLS 斜率绝对值 | **方向** | emotion_valence |
| **情绪峰值位置** | **0.15** | `argmax(arousal)/n` | **位置** | emotion_arousal |
| 情绪词密度 | 0.25 | 每百字情绪词数，上限 6 | 词汇密度 | 词表 |

**移除**：CUSUM 最大统计量（与波动率高度相关）。
**新增** `affect.peak_position(arousal)`：情绪峰值出现的相对位置 ∈[0,1]，n<5 时 `reliable=False`。
**理由**：振幅、方向、峰值位置是三个不同方面；CUSUM 变点强度本质是振幅的另一种读数。

### 1.5 D5 / D6 / D7 → 保持不动

| 维度 | 状态 | 说明 |
|---|---|---|
| D5 说服转化 | 不变 | 子指标已分属不同方面（信任锚/数字/CTA位置/合规） |
| D6 差异化 | 不变，但文档加注 | 与 D2 同用 token_counts，但 D6 是**相对基线的距离**、D2 是**内部离散度**，属不同量；须在文档显式说明 |
| D7 可复制性 | 不变 | 数据源 `structure_states` 唯一 |

---

## 2. 契约：审计工具（冻结输出）

`scripts/dim_audit.py` 必须输出四块：

| 块 | 内容 | 是否依赖数据 |
|---|---|---|
| 1 源依赖矩阵 | 行=原始数据源，列=七维，值=该维从该源取了几项子指标 | **否，精确** |
| 2 违规检测 | 任一行出现「同一维 ≥2 项同源且同方面」→ 报 FAIL | 否，精确 |
| 3 相关矩阵 | 七维两两 Pearson r，附 **n 与警告** | 是 |
| 4 有效维度 | 相关矩阵特征值谱 + 参与率 `(Σλ)²/Σλ²` | 是 |

**强制警告**：`n < 30` 时，第 3/4 块必须打印「样本不足，仅作健全性检查，不作结论」。

CLI：

```
python scripts/dim_audit.py                  # 用 samples/ + 内置参照语料
python scripts/dim_audit.py --dir <语料目录>  # 用自有语料
python scripts/dim_audit.py --json           # 结构化输出
python scripts/dim_audit.py --strict         # 块2 违规即非零退出
```

---

## 3. 契约：口径一致性（五处必须同步）

| 位置 | 必须写明 |
|---|---|
| `scripts/viralmath/engine.py` | 子指标构成（实现） |
| `references/math-engine.md` §2 | 七维定义 + 每维「方面」与数据源 |
| `references/math-engine.md` §2.6 | 共线性审计方法与实测结果 |
| `SKILL.md` 核心能力 6 | 维度表 + 一句「为何是七维而非五轴」 |
| `README.md` 04 七维量化引擎 | 同上 |
| `skill.manifest.json` summary | 不出现与实现矛盾的口径 |

---

## 4. 交付清单（清单外不建文件）

| 路径 | 类型 |
|---|---|
| `tasks/CHG-20261115-dim-orthogonality/{CHANGE,SPEC,TRACEABILITY,TASK_ORCHESTRATION}.md` | 新建 |
| `scripts/viralmath/rhythm.py` | 修改（新增 `alternation_rate`） |
| `scripts/viralmath/affect.py` | 修改（新增 `peak_position`） |
| `scripts/viralmath/genres.py` | 修改（`SUB_WEIGHTS` + `CAPS`） |
| `scripts/viralmath/engine.py` | 修改（D1/D2/D3/D4 子指标重构） |
| `scripts/dim_audit.py` | 新建 |
| `tests/test_viralmath.py` | 修改（新增正交性 / 审计 / 新测度测试） |
| `references/math-engine.md` | 修改（§2 维度定义 + 新增 §2.6 审计） |
| `SKILL.md` | 修改（核心能力 6 维度表与口径） |
| `README.md` | 修改（04 节口径） |
| `skill.manifest.json` | 修改（summary 口径） |

## 5. 验收命令

```bash
python -m unittest discover -s tests                 # 全绿
python scripts/dim_audit.py --strict                 # 块2 无违规，退出码 0
python scripts/dim_audit.py --json | head -30        # 四块齐全
for f in video graphic text; do python scripts/viral_score.py --file samples/$f.txt --boot 0 --json; done
grep -c "方面\|数据源" references/math-engine.md      # 维度定义含方面与源
```

## 6. 回归保护

- 七维输出键名不变：`hook / density / rhythm / emotion / persuasion / distinction / replicability`
- AHP 矩阵仍 7×7、CR 门控不变、TOPSIS 机制不变、分区阈值方式不变
- 既有 91 项单测必须全绿（允许因口径修正而更新的断言，但必须在 TRACEABILITY 说明）
- `CALIBRATION_PENDING` 保留：本次只修正交性，不冒充校准

---

## 7. 修订记录（rev1.1 → rev1.3）

实施过程中由 `dim_audit.py` 实测发现三处**跨维重叠**，均属本 SPEC 初始版本遗漏，
按「开发中发现的问题当场修」逐条修正。不静默漂移，逐条入档。

### rev1.1 · 子指标去同源（初始落地）
- D1：移除首句 surprisal（与 D2 熵同源）→ 换入前 3 句字数占比
- D2：移除 Zipf α（与归一化熵为镜像）
- D3：移除 CV（与 Gini 同为离散度）→ 换入句长交替率
- D4：移除 CUSUM（与波动率同为振幅）→ 换入情绪峰值位置

### rev1.2 · 跨维重复计权（审计实测驱动）
| 重叠 | 实测 | 修正 |
|---|---|---|
| `hook_hits_all` 同时进 D1 与 D2 | density↔hook r = 0.66 | D2 的 info_units 剔除钩子词 |
| `emo_density` 与 D4 振幅同一情绪词典 | density↔emotion r = 0.87 | D4 移除情绪词密度（子指标 4→3） |

### rev1.3 · 语义重新分配（审计实测驱动）
| 重叠 | 实测 | 修正 |
|---|---|---|
| 数字与信任锚同时进 D2 与 D5 | density↔persuasion r = 0.79 | **数字→D2（信息密度）**；**信任锚 + CTA→D5（说服）**，D5 移除数字 |

**修正后子指标构成（当前实现）**

| 维度 | 子指标 | 子指标数 |
|---|---|---|
| D1 hook | 钩子词 / 标点强度 / 开头占比 | 3 |
| D2 density | 具体数字密度 / 词汇离散度 | 2 |
| D3 rhythm | 离散度 / 交替率 / 周期性 | 3 |
| D4 emotion | 振幅 / 方向 / 峰值位置 | 3 |
| D5 persuasion | 信任锚 / CTA（+合规扣分） | 2 |
| D6 distinction | JS 相对距离 | 1 |
| D7 replicability | 序列确定性 | 1 |

### rev1.3 遗留（不掩盖）

| 残留 | 实测（去体裁均值，n=12） | 判定 |
|---|---|---|
| `rhythm ↔ distinction` | r = 0.906 | **未解决**。假设：两者都在代理「文本有多不寻常」。n=12（其中 text 组仅 2 样本）无法裁决，需 n≥30 复核。**不凭空构造修法。** |

### 口径修订（重要）

实施后不再使用「七个相互独立维度」的表述。改为：

> **七维评分，实测有效维度约 3.5（n=12，不可作结论）；结构层已去重，统计层需 n≥30 复核。**

此口径必须同步到 `references/math-engine.md`、`SKILL.md`、`README.md`、`skill.manifest.json`。
