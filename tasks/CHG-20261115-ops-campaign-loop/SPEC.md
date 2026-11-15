---
change_id: CHG-20261115-ops-campaign-loop
version: 1.0
status: spec_frozen
parent_spec: CHG-20261115-multimodal-decompose/SPEC.md
prev_spec: CHG-20261115-viralmath-engine/SPEC.md
prd_ref: CHANGE.md §0（Owner 原话 + 实测审计）
approved_by: Owner
approved_at: 2026-11-15
---

# SPEC：运营作战台（流量管理完整闭环）

## 0. 收敛原则

1. **指标先行**：campaign 未声明 `obj_type` 与 `primary_metric` 时，禁止进入 S1。无靶不许开枪。
2. **只做协议不做实现**：检索交 MCP/搜索，视觉交 `taste`，出图出视频交下游工具。本项目产出**规格、提示词、契约**。
3. **零新依赖**：新增脚本仅用标准库；不引入任何第三方包。
4. **清单外不建文件**：目录契约冻结在 §5，不得临时加文件类型。
5. **缺件必须显式**：任何未知项写 `UNKNOWN` 或 `BASELINE_MISSING`，**禁止编造数字**。编造比缺失严重。
6. **县官不如现管**：既有 CHG（形态矩阵、量化引擎）的契约不变；本 CHG 只在上层加闭环。
7. **永不代发**：任何模式下 agent 都不得自行发布内容，发布动作必须由人执行。
8. **体积红线**：新增 references ≤ 900 行，assets ≤ 700 行，脚本 ≤ 400 行。

---

## 1. 契约：指标族（冻结字段名）

```yaml
obj_type: repo | content | product | personal
primary_metric: <string>          # 唯一主指标，决定胜负
secondary_metrics: [<string>...]  # 辅助诊断，不参与胜负判定
window: {start: DATE, end: DATE}  # 观测窗口
baseline: {p50: N, p80: N, n: N} | BASELINE_MISSING
judge: "primary >= baseline.p80"
```

四种目标对象的默认指标档（可在 brief 中覆盖，但覆盖必须写入理由）：

| obj_type | primary_metric | secondary_metrics | 判据 |
|---|---|---|---|
| `repo` 开源项目 | `stars` | forks / issues / prs / 日增 star / 榜单出现 | 主指标 ≥ 同条件历史 P80 |
| `content` 内容账号 | `views` | 完播率 / 互动率 / 收藏率 / 涨粉 | 同上 |
| `product` 电商产品 | `sales` | 点击率 / 加购率 / 转化率 / ROI | 同上 |
| `personal` 个人品牌 | `followers` | 主页点击 / 搜索指数 / 提及量 | 同上 |

**爆的量化定义（唯一）**：

> `爆 = 主指标在「同 obj_type + 同形态 + 同渠道」的历史序列中 ≥ P80`，且必须回带样本量 `n` 与置信区间。

- `n < 10` 时判据降级为「观测模式」：只记录，不下结论
- 无历史序列时 `baseline = BASELINE_MISSING`，本 campaign 只能产出**假设**，不能宣称成功

---

## 2. 契约：八阶段闭环（冻结阶段名与顺序）

| 阶段 | 键 | 输入 | 输出（落到物料包哪个文件） | 门控 |
|---|---|---|---|---|
| S0 定标 | `goal` | 目标对象 + 主指标 + 窗口 + 资源 | `00-brief.md` | 无指标 → 阻断 |
| S1 侦察 | `recon` | 目标 + 渠道 | `01-recon.md` | G1：无来源分级 → 不许进 S2 |
| S2 定位 | `position` | 侦察结果 | `02-positioning.md` | 无差异化结论 → 不许进 S3 |
| S3 选题 | `backlog` | 定位 + 热点 | `03-backlog.md` | G2：无四维打分排序 → 不许进 S4 |
| S4 生产 | `produce` | 选题 Top-N | `04-scripts/*.md` | G3：无评分卡 → 不许进 S5 |
| S5 组装 | `assemble` | 定稿文案 | `05-assets/*` | G4：无平台×模型适配 → 不许进 S6 |
| S6 排期 | `schedule` | 物料 + 渠道节奏 | `06-schedule.md` | 无渠道/时段/变体 → 不许进 S7 |
| S7 回填 | `measure` | 已发布内容 | `07-ledger.md` | G5：无回填 → 不许进 S8 |
| S8 校准 | `calibrate` | 回填表 | `08-review.md` + 更新基线 | — |

**选题四维打分（S3 冻结）**：

```
score = w1·需求强度 + w2·(1-竞争密度) + w3·可产性 + w4·指标契合
```
四维各 ∈[0,1]，权重默认 `[0.35, 0.25, 0.20, 0.20]`（可在 brief 覆盖并写明理由）。

---

## 3. 契约：三档协作模式（冻结键名）

| 模式 | 键 | 人的角色 | agent 的角色 | 决策点确认 |
|---|---|---|---|---|
| 副驾（默认） | `copilot` | 每阶段审核关键结论 | 框架驱动，逐阶段产出并等确认 | 每阶段末 1 次 |
| 主驾 | `navigate` | 指定目标、素材、方向 | 只做执行与校验，不自行决策 | 仅在冲突时提问 |
| 自动驾驶 | `autopilot` | 只给目标 | 全链自主，只在 3 点确认 | ①目标指标 ②资源边界 ③发布前终审 |

**autopilot 红线**：可自主检索、拆解、评分、写稿、出提示词、排期建议；**不可**自行发布、不可编造数据、不可跳过门控。

---

## 4. 契约：提示词字段（冻结）

### 4.1 文生图（`05-assets/image-prompts.md`）

每条必须含 13 个字段，缺一即不合格：

```
id / subject / scene / composition / lighting / style / palette /
lens / negative / platform / model / params{aspect_ratio, seed} / usage
```

### 4.2 文生视频（`05-assets/video-prompts.md`）

每条必须含 11 个字段：

```
id / shot_motion / duration / first_frame / style / negative /
platform / model / params{aspect_ratio, duration, fps} / audio / usage
```

> 注：`audio` 声明配音风格 / 字幕 / BGM；多数视频生成工具支持声画同步，不写等于放弃声音设计。

### 4.3 平台 × 模型适配矩阵（冻结列）

| platform | 画幅 | 时长上限 | 首帧偏好 | 推荐模型族 |
|---|---|---|---|---|
| douyin | 9:16 | 60s（带货 30–45s） | 强对比 + 大字 | 通用视频生成模型 |
| xiaohongshu | 3:4 / 1:1 | 60s | 真实感 + 生活化 | 通用图像/视频模型 |
| shipinhao | 9:16 | 60s | 稳 + 清晰 | 同抖音 |
| gongzhonghao | 16:9 | 不限 | 信息图/长图 | 图像模型 + HTML 排版 |
| zhihu | 16:9 | 不限 | 信息图 | 图像模型 |
| x / twitter | 16:9 | 140s | 强视觉冲击 | 通用模型 |
| github | 16:9 | — | 仓库截图 + 数据图 | 截图 + HTML 渲染 |

模型字段填写**族名 + 具体型号**（例：`通用图像模型 / <可用型号>`），无可用型号时写 `UNKNOWN`。

---

## 5. 契约：物料包目录（冻结）

```
campaigns/<slug>_<YYYYMMDD>/
├── 00-brief.md          运营目标书（S0）
├── 01-recon.md          侦察报告（S1）
├── 02-positioning.md    定位与差异化（S2）
├── 03-backlog.md        选题池与排序（S3）
├── 04-scripts/          各形态文案（S4）
│   ├── graphic-01.md
│   ├── video-01.md
│   └── text-01.md
├── 05-assets/           物料规格（S5）
│   ├── image-prompts.md
│   ├── video-prompts.md
│   ├── copy-blocks.md
│   └── html/            (HTML 设计文件)
├── 06-schedule.md       发布排期（S6）
├── 07-ledger.md         数据回填（S7）
└── 08-review.md         复盘与校准（S8）
```

**缺件判定**：`00`、`01`、`02`、`03`、`04/`（≥1 份）、`05/image-prompts.md`、`05/copy-blocks.md`、`06`、`07`、`08` = 10 项。缺任一项即「物料包不合格」。

---

## 6. 交付清单（清单外不建文件）

| 路径 | 类型 | 说明 |
|---|---|---|
| `tasks/CHG-20261115-ops-campaign-loop/{CHANGE,SPEC,TRACEABILITY,TASK_ORCHESTRATION}.md` | 新建 | 本 CHG 四件套 |
| `references/ops-loop.md` | 新建 | **S0–S8 闭环唯一承载点**（阶段/门控/三档模式/产出规格） |
| `references/metrics-taxonomy.md` | 新建 | 指标族 + 爆的判据 + 回填字段字典 |
| `assets/campaign-package.md` | 新建 | 物料包目录契约 + 每份文件的最小规格 + 缺件判定 |
| `assets/prompt-spec.md` | 新建 | 文生图/文生视频字段规范 + 平台×模型矩阵 + 示例 |
| `assets/publish-ledger.md` | 新建 | 回填表 + 假设台账 |
| `scripts/campaign_init.py` | 新建 | 一键生成物料包骨架（零依赖、自带日志 sink） |
| `SKILL.md` | 修改 | 新增「运营作战台」入口 + 双入口快速启动 + 触发词 |
| `skill.manifest.json` | 修改 | trigger / summary / required_artifacts / completion_artifacts |
| `references/mcp-reference.md` | 修改 | 升级为**侦察协议**（降级链 + 来源分级强制 + 热点分析方法） |
| `README.md` | 修改 | 新增「运营作战台」一节（不改既有章节） |
| `campaigns/<slug>_<YYYYMMDD>/**` | 运行产物（**不入库**） | 由 `campaign_init.py` 在**使用者本地**生成、由使用者自行填充；已加入 `.gitignore`。属**用户私域运营内容**，不属项目源码——项目只提供台子（`references/` + `assets/` + `scripts/`） |

## 7. 验收命令

```bash
# 1. 脚手架可用
python scripts/campaign_init.py --slug demo --obj-type repo --metric stars --root /tmp/camp
find /tmp/camp -type f | sort        # 期望 10 项齐

# 2. 缺件检测能报错
python scripts/campaign_init.py --slug demo2 --obj-type repo --metric stars --root /tmp/camp2 --dry-run

# 3. 文档契约完整
grep -c "subject\|composition\|negative\|platform\|model" assets/prompt-spec.md
grep -c "obj_type\|primary_metric\|BASELINE_MISSING" references/metrics-taxonomy.md

# 4. 回归零破坏
python -m unittest discover -s tests
```

## 8. 回归保护

- 不改 `viralmath/` 任何逻辑；不改形态矩阵；不改 3+4 个模型
- 新入口与既有「拆解入口」并存，不覆盖
- 既有 79 项单测结果必须不变
