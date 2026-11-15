# TRACEABILITY：多形态内容拆解

## 需求 → 契约 → 产物 追溯

| 需求/目标 | SPEC 条款 | 产物路径 | 验收方式 | 立契状态 |
|---|---|---|---|---|
| G1 形态自动判定 | SPEC §4 判定规则 | `references/content-genres.md` §2 | 3 样本判定 3/3 | 待验 |
| G2 三套拆解矩阵 | SPEC §5.2 | `references/content-genres.md` §3 | 每形态 ≥6 可量化项 | 待验 |
| G3 图文完形填空 | SPEC §5.2 graphic 行 | `references/fill-blank-guide.md` | 含标题/首图/分段/标签四位 | 待验 |
| G4 文本长文拆解 | SPEC §5.2 text 行 | `assets/report-template-text.md` | 含论点链/论证结构/金句密度 | 待验 |
| G5 主题驱动生成 | CHANGE §0.3 | `SKILL.md` 快速启动 + `references/content-genres.md` §5 | 给主题+形态即产出完整稿 | 待验 |
| G6 回归零破坏 | SPEC §0.4 | `references/script-models.md` | 旧 3 模型仍在 | 待验 |
| G7 入口同步 | SPEC §6 | `SKILL.md` description / `skill.manifest.json` | 触发词含图文/文本 | 待验 |
| R1 形态误判可覆盖 | CHANGE §2 | `references/content-genres.md` §2.3 | 输出显式声明 + 可覆盖 | 待验 |

## 独占清单核对（防越界）

- [x] `references/content-genres.md` — 仅本 CHG 创建
- [x] `assets/report-template-graphic.md` — 仅本 CHG 创建
- [x] `assets/report-template-text.md` — 仅本 CHG 创建
- [x] `SKILL.md` — 本 CHG 只改：description 触发词、快速启动、输出规范形态分支
- [x] `references/workflow-guide.md` — 本 CHG 只改：Phase 0 新增、Phase 2/4 形态路由
- [x] `references/fill-blank-guide.md` — 本 CHG 只改：追加图文/文本规则节
- [x] `references/script-models.md` — 本 CHG 只改：文末追加 4 个模型
- [x] `skill.manifest.json` — 本 CHG 只改：summary/trigger/required_sections
- [x] `README.md` — 本 CHG 只改：能力表 + 结构树
- [x] `assets/*.svg`、`.gitignore` — **不属本 CHG**，归 `CHG-20261115-visual-assets`

## 与 CHG-B 的接口

本 CHG 定义的形态字段（SPEC §5.2 各 genre 的量化项）是 CHG-B 数学引擎的**输入契约**：
CHG-B 的 `genres.py` 必须按本表字段名读取特征，不得自造字段名。

---

## 验收记录（2026-11-15，实测）

| 目标 | 实测命令 | 结果 | 结论 |
|---|---|---|---|
| G1 形态判定 3/3 | `python scripts/genre_probe.py --file samples/{video,graphic,text}.txt` | video→video(中) / graphic→graphic(高) / text→text(中) | ✅ 3/3 |
| G2 三形态矩阵 ≥6 可量化项 | `wc -l references/content-genres.md` | 257 行 ≤400；video 10 项 / graphic 17 项 / text 9 项 | ✅ 均 ≥6 |
| G3 图文完形填空四位齐 | 查 `fill-blank-guide.md` 图文节 | 标题公式位①/首图钩子位⑨/正文分段位②-⑦/标签位⑧ | ✅ 四类齐 |
| G4 长文论点链/论证/金句 | 查 `assets/report-template-text.md` | C/E/Q 三元组 + 4 种论证结构 + 金句密度 2–6/千字 | ✅ |
| G5 主题驱动生成 | `content-genres.md` §5 | 7 步流程 + 交付格式（含跑分钟） | ✅ |
| G6 回归零破坏 | `grep -n "模型 1: 吐槽安利\|模型 2: 痛点暴击\|模型 3: 清单收割" references/script-models.md` | 三个旧模型均存在，仅追加 4 个新模型 | ✅ |
| G7 入口同步 | 查 `SKILL.md` description / `skill.manifest.json` | 触发词含图文/笔记/长文/量化；required_sections 增「形态声明」 | ✅ |
| R1 形态误判可覆盖 | `content-genres.md` §2.1/2.2 | 高/中/低置信度 + 用户覆盖规则 | ✅ |
| 体积红线 | `wc -l SKILL.md` vs HEAD | SKILL.md +104 行 ≤120 | ✅ |

**补充实测发现并当轮修复的问题**：
1. 形态判定对外接口需与引擎共享同一实现 → 抽为 `viralmath.features.detect_genre`，CLI 仅做封装（避免两套判定逻辑漂移）。
2. 完形填空规则若只写在 SKILL.md 会与 fill-blank-guide 重复 → 按 SPEC §0.2「单点承载」写入 fill-blank-guide，SKILL 只做路由。
