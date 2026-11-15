---
change_id: CHG-20261115-pipeline-mode
version: 1.0
status: spec_frozen
parent_spec: CHG-20261115-ops-campaign-loop/SPEC.md
prev_spec: CHG-20261115-dim-orthogonality/SPEC.md
prd_ref: CHANGE.md §0（Owner 原话 + 实测审计）
approved_by: Owner
approved_at: 2026-11-15
---

# SPEC：pipeline 模式重构

## 0. 收敛原则

1. **输出物必须可执行**：目录里每一份文件，要么能被念，要么能被工具直接吃。**不许有「给人看的过程文档」**。
2. **参数实测**：所有下游字段必须来自下游源码实测，文档标注来源文件；不确定写 `UNKNOWN`。**编造参数比没有参数更糟**。
3. **注意力优先**：agent 的输出必须首先是文案，其次是参数。禁止用「完备性」稀释核心产出。
4. **能力边界如实**：平台不支持的能力（如小红书图文自动分发）必须显式写「需人工」，不许假装闭环。
5. **引擎零改动**：形态矩阵 / 模型库 / 完形填空 / 七维引擎全部不动，本 CHG 只改输出形态。
6. **旧物降级不删**：campaign 模式文件标注废弃、保留可追溯，不物理删除。
7. **零依赖**：新增脚本仅标准库。
8. **清单外不建文件**。

---

## 1. 契约：pipeline 输出目录（冻结）

```
output/<slug>_<YYYYMMDD>/
├── README.md                      本次战役 3–5 行摘要（目标 / 定位 / 选题理由）
├── douyin/
│   ├── script.md                  口播全文（可直接念）+ 量化评分卡
│   ├── mpt.json                   MPT VideoParams（可直接投喂）
│   └── publish.sh                 MatrixMedia CLI 命令（参数已填）
├── xiaohongshu/
│   ├── note.md                    图文正文 + 标签
│   ├── cover-prompt.md            封面提示词（13 字段，见 assets/prompt-spec.md）
│   └── publish.md                 ⚠️ 注明「图文笔记需人工发布」，并给发布清单
├── gongzhonghao/
│   ├── article.html               长文 HTML（纯静态）
│   ├── header-prompt.md           头图提示词
│   └── publish.md                 公众号发布清单（人工）
└── video-generic/                 可选：其他视频平台（快手/视频号/B站/头条/百家号）
    ├── script.md
    ├── mpt.json
    └── publish.sh
```

**平台 → 目录映射（冻结）**

| 平台 | 目录 | 形态 | 下游工具 | 可自动化 |
|---|---|---|---|---|
| 抖音 | `douyin/` | video | MPT + MatrixMedia `-p dy` | ✅ |
| 快手 | `video-generic/`（`-p ks`） | video | MPT + MatrixMedia `-p ks` | ✅ |
| 视频号 | `video-generic/`（`-p sph`） | video | MPT + MatrixMedia `-p sph` | ✅ |
| B站 | `video-generic/`（`-p blbl`） | video | MPT + MatrixMedia `-p blbl` | ✅ |
| 头条 | `video-generic/`（`-p tt`） | video | MPT + MatrixMedia `-p tt` | ✅ |
| 百家号 | `video-generic/`（`-p bjh`） | video | MPT + MatrixMedia `-p bjh` | ✅ |
| 小红书 | `xiaohongshu/` | graphic | 文案 + 封面提示词 | ❌ **图文需人工** |
| 公众号 | `gongzhonghao/` | text | HTML + 头图提示词 | ❌ 需人工 |

---

## 2. 契约：MPT 参数（实测冻结，来源 `MoneyPrinterTurbo/app/models/schema.py`）

`mpt.json` 为 MPT `VideoParams` 的**子集**，只放本项目能确定的字段。

| 字段 | 类型/取值 | 本项目填法 |
|---|---|---|
| `video_subject` | str（必填） | 标题（≤30 字） |
| `video_script` | str | 口播全文（与 `script.md` 同源） |
| `video_terms` | str \| list[str] | 素材检索关键词，3–6 个，空格或逗号分隔 |
| `video_aspect` | `"9:16"` / `"16:9"` / `"1:1"` | 抖音/快手/视频号 = `"9:16"`；B站/头条/百家号 = `"16:9"` |
| `video_clip_duration` | int ≥1（默认 5） | 按语速与总时长估：30s 口播约 5 |
| `video_source` | str（默认 `pexels`） | 保持默认 |
| `voice_name` | str | `UNKNOWN` → 留空用 MPT 默认 |
| `voice_rate` | float（默认 1.0） | 干货类 `1.1`，故事类 `1.0` |
| `bgm_type` | str（默认 `random`） | `random` |
| `bgm_volume` | float（默认 0.2） | `0.15`（口播为主） |
| `subtitle_enabled` | bool | `true` |
| `subtitle_position` | `top`/`bottom`/`center`/`two_thirds_bottom` | `bottom` |
| `font_size` | int（默认 60） | `60` |
| `text_fore_color` | str | `"#FFFFFF"` |
| `stroke_color` | str | `"#000000"` |
| `stroke_width` | float（默认 1.5） | `1.5` |
| `paragraph_number` | int 1–10 | 按口播段数 |
| `video_count` | int（默认 1） | `1` |

**禁止写入的字段**：`video_materials`、`custom_audio_file`、`bgm_file`（需本地路径，本项目无法预知）。

---

## 3. 契约：MatrixMedia 发布命令（实测冻结，来源 `MatrixMedia/CLI_SKILLS.md`）

`publish.sh` 为**一条可执行命令**，参数已填好：

```bash
matrixmedia cli publish \
  -p <平台码> \
  --phone <账号手机号> \
  -f "<视频绝对路径>" \
  -t "<标题>" \
  --description "<简介>" \
  --tags "#标签1 #标签2" \
  --publish-at "<YYYY-MM-DD HH:mm:ss>"
```

| 参数 | 取值 | 说明 |
|---|---|---|
| `-p` / `--platform` | `dy` \| `tt` \| `ks` \| `blbl` \| `bjh` \| `sph` \| `xhs` | 平台码 |
| `--phone` | 手机号 | 账号；若用 `--partition` 则替代 |
| `-f` / `--file` | 绝对路径 | **视频文件**，需人先跑 MPT 生成 |
| `-t` / `--title` | str | 标题 |
| `--description` | str | 简介 |
| `--tags` | str | 空格分隔，前带 `#` |
| `--publish-at` | `"YYYY-MM-DD HH:mm:ss"` | 可选；仅支持一次性，不支持循环 |

**能力边界（必须写在 `publish.md` 里）**：`cli publish` 只发**本地视频**。
小红书**图文笔记无法通过它分发**，必须人工发布。

---

## 4. 契约：数据回读（替代旧 S7/S8）

不再有台账与校准模板。改为**一页回读**：

```markdown
# 数据回读 <date>
| 平台 | 物料 | 主指标 | 数值 | 判据(P80) | 结论 |
|---|---|---|---|---|---|
```

数据来源：agent 调 SocialDataX MCP（`socialdatax-douyin` / `socialdatax-xhs` 等）拉取，**不落人工台账**。
若 MCP 不可用 → 该行写 `UNKNOWN` 并注明「本轮无 L1 数据」。禁止估算。

---

## 5. 交付清单（清单外不建文件）

| 路径 | 类型 |
|---|---|
| `tasks/CHG-20261115-pipeline-mode/{CHANGE,SPEC,TRACEABILITY,TASK_ORCHESTRATION}.md` | 新建 |
| `references/pipeline-loop.md` | 新建（pipeline 流程唯一承载点） |
| `references/downstream-contracts.md` | 新建（MPT / MatrixMedia 实测参数契约） |
| `assets/pipeline-package.md` | 新建（输出目录契约 + 每份文件最小规格） |
| `scripts/pipeline_init.py` | 新建（替代 campaign_init.py） |
| `tests/test_pipeline.py` | 新建（脚手架与缺件检测的单元测试，含失败路径） |
| `.gitignore` | 修改（加入 `output/`：用户私域产出不入库，与 `campaigns/` 同理） |
| `references/ops-loop.md` | 修改（S5–S8 标注废弃，指向 pipeline-loop） |
| `assets/campaign-package.md` | 修改（顶部标注「团队协作场景，个人流水线请用 pipeline-package」） |
| `assets/publish-ledger.md` | 修改（顶部标注废弃原因） |
| `SKILL.md` | 修改（B 入口默认改 pipeline） |
| `README.md` | 修改（B 入口口径） |
| `skill.manifest.json` | 修改（artifacts / summary） |

## 6. 验收命令

```bash
python scripts/pipeline_init.py --slug demo --platforms douyin,xiaohongshu,gongzhonghao --root /tmp/pl
find /tmp/pl -type f | sort                     # 每平台 3 类文件
python -c "import json;d=json.load(open('/tmp/pl/demo_'$(date +%Y%m%d)'/douyin/mpt.json'));print(sorted(d))"
grep -c "cli publish" /tmp/pl/*/douyin/publish.sh
python scripts/pipeline_init.py --check /tmp/pl/demo_$(date +%Y%m%d)
python -m unittest discover -s tests            # 91 项不变
```

## 7. 回归保护

- `references/content-genres.md`、`script-models.md`、`fill-blank-guide.md`、`math-engine.md`、`scripts/viralmath/**` 全部不动
- 三形态评分结果必须与改前逐位一致（0 变化）
- campaign 模式文件保留，仅标注废弃
