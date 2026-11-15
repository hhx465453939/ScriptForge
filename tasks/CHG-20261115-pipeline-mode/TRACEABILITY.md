# TRACEABILITY：pipeline 模式重构

## 需求 → 契约 → 产物 追溯

| 需求 / 判据 | SPEC 条款 | 产物 | 验收方式 | 立契状态 |
|---|---|---|---|---|
| 输出物可执行、无过程文档 | §0.1 / §1 | `assets/pipeline-package.md` | 目录内无 brief/recon/positioning/backlog/schedule/ledger/review | 待验 |
| MPT 参数真实可投喂 | §2 | `references/downstream-contracts.md` + `pipeline_init.py` | 键名与 `MoneyPrinterTurbo/app/models/schema.py` 一致 | 待验 |
| MatrixMedia 命令可执行 | §3 | 同上 | 参数与 `MatrixMedia/CLI_SKILLS.md` 一致 | 待验 |
| 小红书图文能力边界如实 | §3 末段 | `xiaohongshu/publish.md` | 显式写「需人工」，不假装闭环 | 待验 |
| S4+S5 合并 | §1 | `references/pipeline-loop.md` | 无独立「组装」阶段 | 待验 |
| S7/S8 → 数据回读一页 | §4 | `publish.md` / `README.md` | 无人工台账字段，改为 MCP 拉取 | 待验 |
| 一条命令起目录 | §6 | `scripts/pipeline_init.py` | 每平台 3 类文件 | 待验 |
| 引擎零改动 | §7 | — | 91 单测不变 + 三形态评分逐位一致 | 待验 |
| 旧物降级不删 | §0.6 | `ops-loop.md` / `campaign-package.md` / `publish-ledger.md` | 顶部标注废弃并指向新文件 | 待验 |

## 独占清单核对（防越界）

- [x] `references/pipeline-loop.md` — 仅本 CHG 创建（pipeline 流程唯一承载点）
- [x] `references/downstream-contracts.md` — 仅本 CHG 创建（下游参数唯一承载点）
- [x] `assets/pipeline-package.md` — 仅本 CHG 创建
- [x] `scripts/pipeline_init.py` — 仅本 CHG 创建
- [x] `references/ops-loop.md` — 仅加废弃标注与指向，不删旧内容
- [x] `assets/campaign-package.md` / `assets/publish-ledger.md` — 仅加废弃标注
- [x] `SKILL.md` / `README.md` / `skill.manifest.json` — 仅改 B 入口口径

## A. 实测验收记录

| 验收项 | 命令 | 实测结果 | 结论 |
|---|---|---|---|
| 全量单测 | `python -m unittest discover -s tests` | **Ran 111 tests — OK**（原 91 + 新增 20） | ✅ |
| 脚手架 dry-run | `pipeline_init.py --dry-run` | 列出 10 文件，不写盘 | ✅ |
| 脚手架生成 | `--platforms douyin,xiaohongshu,gongzhonghao` | 每平台 3 类文件，共 10 文件 | ✅ |
| MPT 字段合规 | `json.load(mpt.json)` | 18 字段全部 ⊆ `MPT_ALLOWED`；无禁用字段 | ✅ |
| `video_aspect` 值 | 同上 | `'9:16'`（枚举值，非中文显示串） | ✅ |
| `text_fore_color` | 同上 | 字段名正确存在（不是 `text_color`） | ✅ |
| 缺件检测 | `--check output/demo_*` | ✓ 合格（三平台） | ✅ |
| 图文能力边界 | 查 `xiaohongshu/publish.md` | 含「人工」声明，未生成伪 `publish.sh` | ✅ |
| AGENTS.md §1 自检 | 三条命令 | 单测 / genre_probe / viral_score 全绿 | ✅ |
| 引擎零改动 | 三形态评分 | 47.15 C / 36.70 C / 31.17 D（与改前逐位一致） | ✅ |
| 仓库边界 | `git check-ignore output/` | 已忽略，私域产出不入库 | ✅ |

### 新增单测清单（`tests/test_pipeline.py`，20 项）

| 组 | 验的事 |
|---|---|
| `TestFiles` | 视频平台 3 件；图文/长文**无** `publish.sh`；人工声明存在 |
| `TestMpt` | 键名 ⊆ 契约表；无禁用字段；`video_aspect` 是枚举；`text_fore_color` 名称正确 |
| `TestSh` | 含 `cli publish` 与 4 个必填参数；`-f` 用占位符不用假路径 |
| `TestCheck` | 缺文件/缺目录/禁用字段/自造字段名/README 过长/伪 shell 均能报错 |
| `TestCli` | 非法平台、缺 slug、dry-run 不写盘 |

## A2. 与旧 campaign 模式的差异（实测）

| 项 | campaign 模式 | pipeline 模式（本次） |
|---|---|---|
| 一次产出文件数 | 10（含 7 份过程文档） | 10（3 平台 × 3 件 + README） |
| 过程文档 | 7 份 | **0 份** |
| 可直接执行 | 仅文案，需人工转参数 | `mpt.json` 与 `publish.sh` 可直接投喂 |
| agent 注意力落点 | 填满 10 个文件 | 集中在 P2 写稿 + 参数正确性 |

## B. 下游契约来源（禁止编造的证明）

| 字段 | 来源 | 取证方式 |
|---|---|---|
| `video_subject` / `video_script` / `video_aspect` / `video_clip_duration` / `voice_rate` / `bgm_type` / `subtitle_*` / `font_size` / `paragraph_number` / `video_count` | `MoneyPrinterTurbo/app/models/schema.py` `class VideoParams` | codebase-memory 图谱点名 → `get_code_snippet` → 直读 30–175 行 |
| `VideoAspect` 枚举值 `16:9` / `9:16` / `1:1` | 同上 `class VideoAspect` | 直读确认（注意：docstring 里写的是中文显示串「横屏 16:9（西瓜视频）」，**不是**可直接用的枚举值） |
| `cli publish` 参数 `-p/--phone/-f/-t/--description/--tags/--publish-at` | `MatrixMedia/CLI_SKILLS.md` | 直读 |
| 平台码 `dy/tt/ks/blbl/bjh/sph/xhs` | 同上 | 直读 |

## C. 能力边界（必须如实）

| 平台 | 能否自动分发 | 依据 |
|---|---|---|
| 抖音/快手/视频号/B站/头条/百家号/小红书（**视频**） | ✅ 可 | `cli publish` 支持 7 平台视频 |
| 小红书**图文笔记** | ❌ 需人工 | `cli publish` 只发本地视频 |
| 公众号长文 | ❌ 需人工 | 无对应 CLI 通道 |

## D. 与旧 CHG 的关系

| 旧产物 | 本 CHG 处置 |
|---|---|
| `ops-loop.md` S0–S4（目标/侦察/定位/选题） | **保留**：仍有决策价值，只是不再落成独立文件 |
| `ops-loop.md` S5–S8（组装/排期/回填/校准） | **废弃**：标注指向 `pipeline-loop.md` |
| `campaign-package.md` 10 文件契约 | **降级**：标注「团队协作场景可选」 |
| `publish-ledger.md` 台账 | **废弃**：改 MCP 自动回读 |
