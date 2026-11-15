# TRACEABILITY：品牌中性化

| 需求 | SPEC 条款 | 产物 | 验收 | 状态 |
|---|---|---|---|---|
| 清除全部品牌残留 | §1 命名映射 | 4 个文件 | `grep -rli "ebuygo\|易购宝"` 返回空 | 待验 |
| 标识符中性化 | §1 前 2 行 | `SKILL.md` frontmatter | `name: scriptforge` | 待验 |
| 路径同步 | §1 manifest 4 处 | `skill.manifest.json` | `entrypoint.path` = `skills/scriptforge/SKILL.md` | 待验 |
| 废弃脚本清残留 | §1 末 2 行 | 2 个 docstring | grep 无命中 | 待验 |
| 零功能破坏 | §4 | 全量 | 79 项单测通过 + 三形态评分结果不变 | 待验 |

## 验收记录（2026-11-15）

| 项 | 命令 | 结果 |
|---|---|---|
| 品牌残留 | `grep -rli "ebuygo\|易购宝" SKILL.md skill.manifest.json scripts/` | 无输出 ✅ |
| 标识符/路径 | `python -c "...print(d['id'], d['entrypoint']['path'])"` | `scriptforge skills/scriptforge/SKILL.md` ✅ |
| JSON 合法 | `python -c "import json;json.load(...)"` | OK ✅ |
| 回归 | `python -m unittest discover -s tests` | 79 passed ✅ |
| 评分不变 | 三形态 `--boot 0` | 41.78 / 37.43 / 29.13，与改名前一致 ✅ |

## 独占清单核对

- [x] `SKILL.md` — 仅改 4 处（name / 标题 / description 前缀 / 首段）
- [x] `skill.manifest.json` — 仅改 5 处（id / display_name / entrypoint.path / local_corpora ×2）
- [x] `scripts/generate-content-brief.py`、`scripts/unpack-7z.py` — 仅改 docstring
- [x] 历史 CHG 文档不动（仅在需要处加中性化注记）
