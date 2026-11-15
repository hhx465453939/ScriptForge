# TASK_ORCHESTRATION：多形态内容拆解

## 执行顺序

| # | 动作 | 产物 | 依赖 |
|---|---|---|---|
| 1 | 写形态矩阵 | `references/content-genres.md` | 无 |
| 2 | 写两块报告模板 | `assets/report-template-graphic.md`、`assets/report-template-text.md` | 1 |
| 3 | 补完形填空图文/文本规则 | `references/fill-blank-guide.md`（追加） | 1 |
| 4 | 补 4 个图文/文本模型 | `references/script-models.md`（追加） | 3 |
| 5 | 工作流加 Phase 0 与形态路由 | `references/workflow-guide.md` | 1 |
| 6 | 主入口同步 | `SKILL.md`、`skill.manifest.json` | 1-5 |
| 7 | README 同步 | `README.md` | 6 |
| 8 | 验收 | 3 样本判定 + 旧模型 grep | 全部 |

## 冻结约束（不许违反）

- 只追加，不重写既有小节（尤其 SKILL.md 九板块顺序、3 个旧模型）
- `content-genres.md` ≤ 400 行
- 不新增第三方 Python 依赖

## 完成定义（DoD）

- [ ] SPEC §2 G1-G7 全部有对应产物
- [ ] 三形态样本判定通过
- [ ] 旧口播流程零破坏
- [ ] `skill.manifest.json` 为合法 JSON（`python -c "import json;json.load(open(...))"`）
