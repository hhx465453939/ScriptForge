---
change_id: CHG-20261115-multimodal-decompose
version: 1.0
status: spec_frozen
parent_spec: null
prev_spec: null
prd_ref: CHANGE.md §0（Owner 原话 + 实测审计已足够具体）
approved_by: Owner
approved_at: 2026-11-15
---

# SPEC：多形态内容拆解（video / graphic / text）

## 0. 收敛原则

1. **形态是正交维度，不是分支补丁**：新增 `genre` 概念贯穿「判定 → 拆解 → 模型 → 完形填空 → 评估」全链，禁止只在 SKILL.md 加一句「也支持图文」。
2. **单点承载规则**：形态差异规则**只**写在 `references/content-genres.md`；其他文件只允许引用 + 路由，禁止复制第二份。
3. **零依赖**：不新增 Python 第三方包；新增脚本只用标准库。
4. **零破坏**：既有 3 个口播模型、既有 9 板块输出顺序、既有触发词全部保留；新增内容一律追加。
5. **可量化优先**：每个形态的专属特征项必须是能数出来的（字数、段数、emoji 数、标签数、破折号数），不许只写形容词。
6. **文档体积红线**：`references/content-genres.md` ≤ 400 行，`SKILL.md` 增量 ≤ 120 行。

---

## 1. 上下文

见 CHANGE.md §0.2。一句话：**项目把「视频口播」这个形态写死成了唯一形态。**

---

## 2. 目标与可测判据

| 序 | 目标 | 可测判据 |
|---|---|---|
| G1 | 形态自动判定 | 给定 3 条不同形态样本，判定正确率 3/3，且输出显式声明 `形态=xxx 置信度=高/中/低` |
| G2 | 三套拆解矩阵 | `references/content-genres.md` 覆盖 video/graphic/text，每形态 ≥6 个专属可量化特征项 |
| G3 | 图文完形填空 | 模板含标题公式位、首图钩子位、正文分段位、标签位；每条占位符有填写说明 |
| G4 | 文本长文拆解 | 输出含论点链（claim→evidence→qualifier）、论证结构、金句密度 |
| G5 | 主题驱动生成 | 用户给「主题 + 形态」→ 依模型库产出 ≥1 条完整新爆款，并回带所用模型名与预估量化分区 |
| G6 | 回归零破坏 | 原视频口播样本走原 9 板块，板块名称与顺序不变 |
| G7 | SKILL.md 同步 | description 触发词增加图文/文本；快速启动增加形态判定步骤 |

## 3. 非目标

- 图片 OCR / 视频抽帧 / 自动采集（见 CHANGE §1.2）
- 改写既有 3 个模型骨架
- 平台后台数据接入

## 4. 契约：形态判定规则（冻结）

判定只看文本本身，按优先级短路：

| 优先级 | 强信号 | 判定 |
|---|---|---|
| 1 | 出现 `口播`/`镜头`/`前3秒`/`第X秒`/`旁白`/`字幕` 等元标记 | video |
| 2 | 用户显式声明形态（「这是小红书图文」） | 用户指定，覆盖一切 |
| 3 | 含 `#话题#` 或 `@用户` 或 首行 ≤20 字独立成行且后有 emoji 密集正文 | graphic |
| 4 | 含 `一、/二、`、`##`、`图1`、`表1`、`参考文献`、段落 >8 段且无口语称呼词 | text |
| 5 | 含大量口语称呼（`姐妹们`/`老铁`/`你们`/`咱`）+ 短句密集（平均句长 ≤15 字） | video |
| 6 | 兜底 | 按句长与分段数判：平均句长 ≤20 且 ≤5 段 → video；否则 text |

**置信度**：命中强信号 1 或 2 → 高；命中 3/4/5 → 中；走 6 → 低（低置信度必须在输出中提示用户可覆盖）。

## 5. 契约：三形态拆解矩阵（冻结字段名）

每形态必须给出下列字段，字段名冻结（供下游引擎与报告模板引用）：

### 5.1 通用层（三形态共用，字段名不变）
`基础判断` / `钩子拆解` / `结构解码` / `说服逻辑链` / `亮点标注` / `爆款潜力评估` / `完形填空模板` / `仿写脚本`

### 5.2 形态专属层

| genre | 专属板块（冻结名） | 每板块必含量化项 |
|---|---|---|
| video | `钩子时间轴`、`口播节奏` | 前3秒字数、平均句长、感叹号数、第二人称出现次数 |
| graphic | `标题公式`、`首图钩子`、`分段节奏`、`标签策略` | 标题字数、标题公式类型、emoji 数、段落数、标签数、单段行数中位数 |
| text | `论点链`、`论证结构`、`金句密度`、`长文钩子` | 论点句数、证据/论点比、金句数每千字、小标题数、段数 |

## 6. 交付清单（清单外不建文件）

| 路径 | 类型 | 说明 |
|---|---|---|
| `tasks/CHG-20261115-multimodal-decompose/{CHANGE,SPEC,TRACEABILITY,TASK_ORCHESTRATION}.md` | 新建 | 本 CHG 四件套 |
| `references/content-genres.md` | 新建 | **形态矩阵唯一承载点** |
| `assets/report-template-graphic.md` | 新建 | 图文拆解报告模板 |
| `assets/report-template-text.md` | 新建 | 纯文本长文拆解报告模板 |
| `SKILL.md` | 修改 | description 触发词 + 快速启动加形态判定 + 输出规范加形态分支 |
| `references/workflow-guide.md` | 修改 | 加 Phase 0 形态判定；Phase 2/4 加形态路由 |
| `references/fill-blank-guide.md` | 修改 | 加图文 / 文本完形填空规则与示例 |
| `references/script-models.md` | 修改 | 追加 4 个图文/文本模型（不改旧模型） |
| `skill.manifest.json` | 修改 | summary/trigger/required_sections 同步 |
| `README.md` | 修改 | 能力表与结构树同步 |

## 7. 验收命令

```bash
# 1. 形态判定（三形态各一条样本）
python scripts/genre_probe.py --file samples/graphic.txt   # 期望 graphic
python scripts/genre_probe.py --file samples/text.txt      # 期望 text
python scripts/genre_probe.py --file samples/video.txt     # 期望 video
# 2. 文档完整性
grep -c "video\|graphic\|text" references/content-genres.md
# 3. 回归：旧模型三段仍在
grep -n "模型 1: 吐槽安利\|模型 2: 痛点暴击\|模型 3: 清单收割" references/script-models.md
```
