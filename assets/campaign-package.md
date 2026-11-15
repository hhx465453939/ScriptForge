# 运营物料包 · 目录契约与最小规格

> 本文件定义**一次 campaign 的交付物长什么样**。缺件即不合格。
> 闭环阶段见 `references/ops-loop.md`；指标字段见 `references/metrics-taxonomy.md`。
>
> 一句话：**交付物是一个目录，不是一段话。**

---

## 1. 目录结构（冻结）

```
campaigns/<slug>_<YYYYMMDD>/
├── 00-brief.md            运营目标书        ← S0
├── 01-recon.md            侦察报告          ← S1
├── 02-positioning.md      定位与差异化      ← S2
├── 03-backlog.md          选题池与排序      ← S3
├── 04-scripts/            各形态文案        ← S4
│   ├── graphic-01.md
│   ├── video-01.md
│   └── text-01.md
├── 05-assets/             物料规格          ← S5
│   ├── image-prompts.md
│   ├── video-prompts.md
│   ├── copy-blocks.md
│   └── html/
├── 06-schedule.md         发布排期          ← S6
├── 07-ledger.md           数据回填          ← S7
└── 08-review.md           复盘与校准        ← S8
```

**生成方式**：

```bash
python scripts/campaign_init.py --slug demo --obj-type repo --metric stars
# 校验已有物料包缺件
python scripts/campaign_init.py --check campaigns/demo_20261115
```

---

## 2. 缺件判定（10 项）

| # | 判据 | 说明 |
|---|---|---|
| 1 | `00-brief.md` 存在且含 `primary_metric` | 无指标 = 不合格 |
| 2 | `01-recon.md` 存在且含 `source_level` 标注 | 无来源 = 不合格 |
| 3 | `02-positioning.md` 存在且含 ≥1 条可验证差异点 | 无差异 = 不合格 |
| 4 | `03-backlog.md` 存在且候选带四维打分 | 无打分 = 不合格 |
| 5 | `04-scripts/` 含 ≥1 份 `.md` 且每份有评分卡 | 无评分卡 = 不合格 |
| 6 | `05-assets/image-prompts.md` 存在 | — |
| 7 | `05-assets/copy-blocks.md` 存在 | — |
| 8 | `06-schedule.md` 存在 | — |
| 9 | `07-ledger.md` 存在 | — |
| 10 | `08-review.md` 存在 | — |

`05-assets/video-prompts.md` 与 `05-assets/html/` 为**按需**（有视频/网页需求才建），不计入 10 项。

---

## 3. 每份文件的最小规格

### 3.1 `00-brief.md`（目标书）

````
---
campaign: demo_20261115
obj_type: repo
primary_metric: stars
secondary_metrics: [forks, issues, 日增star]
window: {start: 2026-11-15, end: 2026-12-15}
baseline: BASELINE_MISSING        # 或 {p50: , p80: , n: }
judge: "primary >= baseline.p80"
mode: copilot
resources: {人: 1, 预算: 0, 产能: 4}
constraints: [不代发, 不刷量, 不使用绝对化用语]
---

## 一、这个战役要赢什么
<一句话>

## 二、为什么是现在
<外部时机 + 内部准备度>

## 三、基线现状
baseline = BASELINE_MISSING → 本次定位为「基线采集战役」，目标是产出 n≥10 样本

## 四、不做什么
<明确排除>
````

**最小要求**：frontmatter 10 个字段齐全；缺 `primary_metric` 直接不合格。

### 3.2 `01-recon.md`（侦察报告）

必须含三块，每块内每条数据带 `source_level`：

````
## 一、受众
| 结论 | 证据 | source_level |
|---|---|---|
| 目标人群是独立开发者与内容创作者 | <来源> | L2 |

## 二、竞品
| 竞品/标杆 | 内容形态 | 结构特征 | 互动中位数 | source_level |
|---|---|---|---|---|

## 三、热点与概念（近 30 天）
| 概念/事件 | 与我们的相关性 | 可借势角度 | 时效窗口 | source_level |
|---|---|---|---|---|

## 四、侦察结论
<3 条：机会在哪 / 不要碰什么 / 最缺的证据是什么>
````

**最小要求**：三块齐全；`source_level` 不得为空；未知写 `UNKNOWN`。

### 3.3 `02-positioning.md`（定位）

````
## 一、我们是谁（一句话）

## 二、我们不是谁（主动放弃）

## 三、差异点（≤3 条，每条可验证）
| 编号 | 差异点 | 竞品缺失证据 | 我方证据 | 可验证方式 |
|---|---|---|---|---|
| D1 | | | | |

## 四、不做什么
- ...

## 五、差异化量化（可选）
与竞品语言分布的 JS 散度 = <值>（用 viralmath.align / info.js_divergence）
````

**最小要求**：≥1 条差异点，且「可验证方式」非空。

### 3.4 `03-backlog.md`（选题池）

````
## 评分口径
score = 0.35·需求强度 + 0.25·(1-竞争密度) + 0.20·可产性 + 0.20·指标契合

## 候选池（≥12 条）
| # | 选题 | 形态 | 需求强度 | 竞争密度 | 可产性 | 指标契合 | 总分 | 排序 |
|---|---|---|---|---|---|---|---|---|
| 1 | | graphic | 0.8 | 0.6 | 0.9 | 0.7 | 0.76 | 1 |

## 本周 Top-N（N = 产能）
1. ...
````

**最小要求**：候选 ≥12 条、四维分数齐全、Top-N 数量 = `resources.产能`。

### 3.5 `04-scripts/<genre>-<NN>.md`（文案）

````
---
script_id: graphic-01
genre: graphic
model: 圈人清单
backlog_ref: "#3"
---

## 一、文案全文
<可直接拍摄/发布的正文>

## 二、量化评分卡
| 综合分 | 分区 | 95% CI |
|---|---|---|
| 58.4 | B | [51.2, 65.0] |

| 维度 | 分数 |
|---|---|
| 钩子力 | |
| ... | |

短板：<前 2 项>

## 三、迭代记录
| 轮次 | 改动 | 综合分 | 变化 |
|---|---|---|---|

## 四、平台适配
| 平台 | 标题 | 标签 | 备注 |
|---|---|---|---|
````

**最小要求**：评分卡必须来自 `python scripts/viral_score.py --json` 的真实输出，**不许手写数字**。

### 3.6 `05-assets/image-prompts.md`（文生图提示词）

字段规范见 `assets/prompt-spec.md`（13 字段冻结）。

**最小要求**：每条 13 字段齐全；`platform` 与 `model` 非空。

### 3.7 `05-assets/video-prompts.md`（文生视频提示词）

字段规范见 `assets/prompt-spec.md`（11 字段冻结）。

### 3.8 `05-assets/copy-blocks.md`（可直接粘贴块）

按平台分组，每平台含五块：

````
## douyin
- 标题：
- 正文/口播：
- 话题标签：
- 字幕要点（3–5 条）：
- 评论区引导：

## xiaohongshu
- 标题（12–18 字）：
- 正文（分段）：
- 标签组（4–8 个）：
- 评论区引导：
````

**最小要求**：≥1 个平台；每平台五块齐全。

### 3.9 `05-assets/html/`

按需。**最小要求**：纯静态、无外部 CDN 依赖、可直接双击打开。

### 3.10 `06-schedule.md`（排期）

````
| 日期 | 渠道 | 物料文件 | 变体（只改一个变量） | 预期 | 实际发布 |
|---|---|---|---|---|---|
````

**最小要求**：每行必须有「变体只改一个变量」的说明，否则回填无法归因。

### 3.11 `07-ledger.md`（回填）

字段见 `assets/publish-ledger.md`。

### 3.12 `08-review.md`（复盘）

必须含四块：判定结果、假设验证、基线重估、下一轮动作。

---

## 4. 完整示例（骨架，非真实数据）

```
campaigns/scriptforge_20261115/
├── 00-brief.md            obj_type=repo, primary_metric=stars, baseline=BASELINE_MISSING
├── 01-recon.md            受众=独立开发者 / 竞品=3 个同类 / 热点=「本地优先」
├── 02-positioning.md      D1: 唯一把「形态判定+量化评分」做进 skill 的
├── 03-backlog.md          14 条候选 → Top-4
├── 04-scripts/
│   ├── graphic-01.md      「我把爆款拆成了公式」B 区 58.4
│   ├── graphic-02.md      「3 个让我少写 80% 文案的工具」
│   ├── video-01.md        「别再靠感觉写文案了」
│   └── text-01.md         「爆款是可测量的吗」
├── 05-assets/
│   ├── image-prompts.md   6 条（首图/长图/信息卡）
│   ├── video-prompts.md   2 条
│   ├── copy-blocks.md     douyin + xiaohongshu + x
│   └── html/landing.html
├── 06-schedule.md         11-18 至 11-24，4 条，变体单变量
├── 07-ledger.md           4 行待回填
└── 08-review.md           待 S7 完成后填
```

---

## 5. 反模式

| 反模式 | 为什么禁止 |
|---|---|
| 只给文案，不给提示词/平台参数 | 用户拿不到可执行资产 |
| 评分卡数字手写 | 等于伪造证据，比没有更糟 |
| `01-recon.md` 里写「据说」「网上说」 | 无来源层级，违反 G1 |
| 排期里同一选题发多个变体但不说改了什么 | S8 无法归因 |
| 把 `video-prompts.md` 当成必需却平台不匹配 | 画幅/时长必须按平台矩阵填 |
| 物料包放在仓库根目录 | 污染项目，必须放 `campaigns/` |

---

*本文件为物料包契约唯一承载点。改目录或最小规格只改这里，并同步 `scripts/campaign_init.py` 的校验清单。*
