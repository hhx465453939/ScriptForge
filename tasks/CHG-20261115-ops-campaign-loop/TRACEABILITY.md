# TRACEABILITY：运营作战台

## 需求 → 契约 → 产物 追溯

| 需求 / 目标 | SPEC 条款 | 产物 | 验收方式 | 状态 |
|---|---|---|---|---|
| 指标先行（不拍脑袋） | §1 指标族 | `references/metrics-taxonomy.md` | 四档 obj_type × 判据齐全；含 `BASELINE_MISSING` 降级 | 待验 |
| 爆必须有量化判据 | §1 末段 | 同上 | 「≥ 同条件历史 P80 + 带 n 与区间」 | 待验 |
| 完整闭环 | §2 八阶段 | `references/ops-loop.md` | S0–S8 每阶段有 输入/输出/门控 | 待验 |
| 门控不可跳步 | §2 门控列 | 同上 | 5 条 G1–G5 明确可判 | 待验 |
| 三档协作（主驾/副驾/自驾） | §3 | 同上 | copilot/navigate/autopilot + autopilot 3 决策点 | 待验 |
| 物料包齐全可验收 | §5 目录契约 | `assets/campaign-package.md` | 10 项缺件判定 | 待验 |
| 提示词可复用 | §4 字段冻结 | `assets/prompt-spec.md` | 图 13 字段 / 视频 11 字段 / 平台×模型矩阵 | 待验 |
| 反馈闭环可回填 | §2 S7/S8 | `assets/publish-ledger.md` | 回填表 + 假设台账 | 待验 |
| 一键起物料包 | §7 验收 1 | `scripts/campaign_init.py` | 生成 10 项骨架 + 缺件检测 | 待验 |
| 侦察有降级链且强制标源 | CHANGE §0.2 末行 | `references/mcp-reference.md` | L1/L2/L3 分级 + 「无来源不许用」 | 待验 |
| agent 能被这个目标驱动 | CHANGE §0.1 | `SKILL.md` 运营作战台入口 | 双入口：拆解 / 运营 | 待验 |
| 零回归 | §8 | — | 79 项单测不变 + 三形态评分逐位一致 | 待验 |

## 独占清单核对（防越界）

- [x] `references/ops-loop.md` — 仅本 CHG 创建（闭环唯一承载点）
- [x] `references/metrics-taxonomy.md` — 仅本 CHG 创建
- [x] `assets/campaign-package.md` — 仅本 CHG 创建
- [x] `assets/prompt-spec.md` — 仅本 CHG 创建
- [x] `assets/publish-ledger.md` — 仅本 CHG 创建
- [x] `scripts/campaign_init.py` — 仅本 CHG 创建
- [x] `SKILL.md` — 本 CHG 只改：新增运营作战台入口 + 触发词
- [x] `skill.manifest.json` — 本 CHG 只改：trigger/summary/required_artifacts/completion_artifacts
- [x] `references/mcp-reference.md` — 本 CHG 只改：升级为侦察协议
- [x] `README.md` — 本 CHG 只改：新增一节

## 与既有 CHG 的边界

| 既有资产 | 本 CHG 如何使用 | 是否改动 |
|---|---|---|
| 形态矩阵 `content-genres.md` | S4 生产阶段调用判定与专属层 | 不改 |
| 量化引擎 `viralmath/` | S4 评分卡、S3 指标契合 | 不改 |
| 模型库 `script-models.md` | S3/S4 选模型 | 不改（可追加，但本 CHG 不加） |
| 完形填空 `fill-blank-guide.md` | S4 出稿 | 不改 |

**关键边界**：本 CHG 不生产「更好的文案方法」，只生产「让文案能被组织成一个战役」的流程与契约。

## 验收记录（2026-11-15 实测）

| 项 | 命令 | 结果 | 结论 |
|---|---|---|---|
| 脚手架 dry-run | `campaign_init.py --slug demo --obj-type repo --metric stars --dry-run` | 列出 10 个待生成文件，不写盘 | ✅ |
| 脚手架生成 | 同上去掉 --dry-run | 实际落盘 10 文件 | ✅ |
| 缺件判定 | `campaign_init.py --check <pkg>` | 正确报出「04-scripts/ 需 ≥1 份真实文案，_TEMPLATE.md 不算」 | ✅ 伪造检测有效 |
| 禁止编造 | 查模板内容 | 全部为 `TBD`/`UNKNOWN`/`BASELINE_MISSING`，无假数据 | ✅ |
| 幂等性 | 重复运行 | 已存文件跳过，需 `--force` 才覆盖 | ✅ |
| 提示词字段 | `assets/prompt-spec.md` | 图 13 字段 / 视频 11 字段（含 audio） | ✅ 与 SPEC §4 一致 |
| 指标判据 | `references/metrics-taxonomy.md` | 四档 obj_type + P80 判据 + `BASELINE_MISSING` 降级阶梯 | ✅ |
| 八阶段与门控 | `references/ops-loop.md` | S0–S8 + G0–G6 七条门控可判 | ✅ |
| 侦察降级链 | `references/mcp-reference.md` | L1→L2→L3，强制 `source_level` | ✅ |
| 回归零破坏 | `python -m unittest discover -s tests` | 79 passed | ✅ |
| 评分不变 | 三形态 `--boot 0` | 41.78 / 37.43 / 29.13 与改前一致 | ✅ |

### 当轮修正的契约漂移

| # | 问题 | 处理 |
|---|---|---|
| 1 | SPEC §4 写「图 12 字段 / 视频 11 字段」，但列出 13 / 10 项，与 `prompt-spec.md` 不一致 | 重定为 **图 13 / 视频 11**（视频新增 `audio` 声音设计字段），同步 SPEC / TRACEABILITY / TASK_ORCHESTRATION |

### 遗留与边界（不掩盖）

| 项 | 状态 | 说明 |
|---|---|---|
| 真实采集 | 不实现 | 只定协议与降级链，执行交 MCP / 搜索工具 |
| 出图出视频 | 不实现 | 只产出提示词与规格，生成交下游工具或人 |
| 平台后台 API | 未接入 | 回填由人填表；后续再谈自动化 |
| 发布动作 | 永不代做 | 红线，任何模式不放行 |
| 基线 | `BASELINE_MISSING` | 首次 campaign 定位为基线采集战役 |
