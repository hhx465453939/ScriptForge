# TASK_ORCHESTRATION：品牌中性化

| # | 动作 | 产物 | 依赖 |
|---|---|---|---|
| 1 | 改 skill 标识与文案 | `SKILL.md`（4 处） | 无 |
| 2 | 改标识符与路径 | `skill.manifest.json`（5 处） | 1（同一批改，避免路径漂移） |
| 3 | 清废弃脚本 docstring | `scripts/*.py`（2 处） | 无 |
| 4 | grep 收口 | — | 1-3 |
| 5 | 全量回归 | 79 项单测 | 1-3 |

## 冻结约束

- 不动任何逻辑代码、不动引擎、不动形态规则、不动模板
- 标识符与路径同批改，不许分两次
- 历史 CHG 文档不改写

## DoD

- [ ] `grep -rli "ebuygo\|易购宝"` 在核心文件上无输出
- [ ] `skill.manifest.json` 合法且 `id=scriptforge`
- [ ] 79 项单测通过，三形态评分结果与改名前逐位一致
