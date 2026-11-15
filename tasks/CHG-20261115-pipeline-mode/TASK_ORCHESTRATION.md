# TASK_ORCHESTRATION：pipeline 模式重构

## 执行顺序

| # | 动作 | 产物 | 依赖 |
|---|---|---|---|
| 1 | 实测下游契约并落档 | `references/downstream-contracts.md` | 无（已取证） |
| 2 | 定义 pipeline 流程 | `references/pipeline-loop.md` | 1 |
| 3 | 定义输出目录契约 | `assets/pipeline-package.md` | 2 |
| 4 | 实现脚手架 | `scripts/pipeline_init.py` | 3 |
| 5 | 旧物降级标注 | `ops-loop.md` / `campaign-package.md` / `publish-ledger.md` | 2 |
| 6 | 主入口口径切换 | `SKILL.md` / `README.md` / `skill.manifest.json` | 2,3 |
| 7 | 全量验收 + 回归 | 见 SPEC §6/§7 | 全部 |

## 关键实现约束

- **纯标准库**：`argparse` / `json` / `os` / `logging`
- **参数不编造**：`mpt.json` 只写 SPEC §2 表内字段；未定字段留空或 `UNKNOWN`
- **`publish.sh` 不给假路径**：`-f` 处写 `<待填：MPT 输出视频的绝对路径>` 占位，因为视频尚未生成
- **平台能力如实**：小红书/公众号目录产出的是「人工发布清单」，不是伪命令
- **幂等**：重复运行不覆盖，`--force` 才覆盖
- **`--check` 缺件判定**：每平台目录最小文件集

## 反模式（明令禁止）

| 反模式 | 原因 |
|---|---|
| 保留 `06-schedule.md` / `07-ledger.md` | 个人流水线里它们是纯负担，稀释注意力 |
| 编造 MPT 字段名（如自造 `aspect_ratio`） | 工具会直接报错，比没有更糟 |
| 给小红书生成 `publish.sh` | 图文无法用该 CLI 发布，假装闭环会误导用户 |
| `-f` 填一个不存在的路径 | 用户执行必失败 |
| 在 `README.md` 里写长篇定位分析 | 那就是又变回过程文档；限 3–5 行 |

## 完成定义（DoD）

- [ ] `pipeline_init.py` 一条命令产出每平台 3 类文件
- [ ] `douyin/mpt.json` 键名全部来自 SPEC §2 表
- [ ] `douyin/publish.sh` 含 `matrixmedia cli publish` 与 7 个参数
- [ ] `xiaohongshu/publish.md` 明确写「图文需人工发布」
- [ ] 输出目录内无 brief/recon/positioning/backlog/schedule/ledger/review
- [ ] `--check` 能报缺件
- [ ] 91 项单测通过；三形态评分逐位不变
- [ ] 三份旧文件已加废弃标注并指向新文件
- [ ] SKILL/README/manifest 的 B 入口口径已切换
