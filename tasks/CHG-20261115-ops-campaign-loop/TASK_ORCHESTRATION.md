# TASK_ORCHESTRATION：运营作战台

## 执行顺序（依赖严格串行）

| # | 动作 | 产物 | 依赖 |
|---|---|---|---|
| 1 | 定指标族与判据 | `references/metrics-taxonomy.md` | 无 |
| 2 | 定八阶段闭环 + 门控 + 三档模式 | `references/ops-loop.md` | 1 |
| 3 | 定物料包目录契约与最小规格 | `assets/campaign-package.md` | 2 |
| 4 | 定提示词字段与平台×模型矩阵 | `assets/prompt-spec.md` | 3 |
| 5 | 定回填表与假设台账 | `assets/publish-ledger.md` | 1,2 |
| 6 | 实现脚手架 CLI | `scripts/campaign_init.py` | 3 |
| 7 | 升级侦察协议 | `references/mcp-reference.md` | 1 |
| 8 | 主入口加运营作战台 | `SKILL.md` | 2,3,4 |
| 9 | 清单同步 | `skill.manifest.json` | 8 |
| 10 | README 增一节 | `README.md` | 8 |
| 11 | 全量验收 + 回归 | 见 SPEC §7 | 全部 |

## 关键实现约束

- **纯标准库**：`argparse` / `os` / `json` / `pathlib` / `logging` / `datetime`
- **自带 W4 日志 sink**：`scripts/campaign_init.log`，不依赖宿主重定向
- **幂等**：重复运行不覆盖已有文件，只补缺失（`--force` 才覆盖）
- **缺件检测**：`--dry-run` 只报告缺什么，不写盘；`--check <dir>` 校验已有物料包
- **不编造**：脚手架只生成**空壳 + 待填标记**（`UNKNOWN` / `TBD`），绝不写入假数据

## 完成定义（DoD）

- [ ] S0–S8 八阶段与 5 条门控在 `ops-loop.md` 中可判定（非描述性语言）
- [ ] 三档模式含 autopilot 的 3 个决策点与「永不代发」红线
- [ ] 物料包 10 项缺件判定可在 `campaign_init.py --check` 中执行
- [ ] 提示词字段数：图 13 / 视频 11，缺字段可被判不合格
- [ ] 回填表字段可被 `metrics-taxonomy.md` 的字段字典解释
- [ ] 侦察协议含 L1/L2/L3 降级链与「每条数据必须标来源层级」
- [ ] `SKILL.md` 双入口（拆解 / 运营）清晰，触发词覆盖「运营火」「物料包」「campaign」
- [ ] 79 项单测通过；三形态评分结果与改前逐位一致
- [ ] 新文件行数不破 SPEC §0.8 红线

## 反模式（明令禁止）

| 反模式 | 为什么禁止 |
|---|---|
| 未声明 primary_metric 就开始写文案 | 无靶射击，产出无法评判 |
| 用「感觉会火」代替指标 | 退回改造前的打分表演 |
| 物料包只给文案，不给提示词/平台参数 | 用户拿不到可执行资产 |
| agent 自行发布 | 越权，且不可回滚 |
| 缺数据时编一个数字 | 比缺失严重得多，破坏整条信任链 |
| 跳过门控直接进下一阶段 | 闭环退化成链接，回填无法归因 |
