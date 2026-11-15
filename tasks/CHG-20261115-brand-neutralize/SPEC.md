---
change_id: CHG-20261115-brand-neutralize
version: 1.0
status: spec_frozen
parent_spec: null
prev_spec: null
prd_ref: CHANGE.md §0
approved_by: Owner
approved_at: 2026-11-15
---

# SPEC：品牌中性化

## 0. 收敛原则

1. **标识符与路径必须同批改**：`id`/`name` 改了而 `entrypoint.path` 没改 = 宿主找不到入口，是静默故障。
2. **零功能变更**：不动任何 `.py` 逻辑（两个废弃脚本只改 docstring 文字）。
3. **历史不改写**：历史 CHG 文档中的品牌引述保留，仅加一行中性化注记。
4. **单一命名源**：新标识 = 仓库名 `scriptforge`，全小写、无分隔符。
5. **改完必须以 grep 收口**，不接受"应该改干净了"。

---

## 1. 契约：命名映射（冻结）

| 位置 | 旧值 | 新值 |
|---|---|---|
| `SKILL.md` frontmatter `name` | `ebuygo-content-ops` | `scriptforge` |
| `SKILL.md` 标题 | `# ebuygo 多形态内容拆解与仿写引擎` | `# ScriptForge · 多形态内容拆解与运营作战台` |
| `SKILL.md` description 前缀 | `ebuygo(易购宝) 多形态…` | `ScriptForge 多形态…` |
| `SKILL.md` 首段 | `为 ebuygo（易购宝）打造的内容拆解…` | `面向个人与团队的开源内容拆解与运营作战台…` |
| `manifest.id` | `ebuygo-content-ops` | `scriptforge` |
| `manifest.display_name` | `Ebuygo 多形态内容拆解与仿写引擎（…）` | `ScriptForge 多形态内容拆解与运营作战台（…）` |
| `manifest.entrypoint.path` | `skills/ebuygo-content-ops/SKILL.md` | `skills/scriptforge/SKILL.md` |
| `manifest.information_profile.local_corpora`（2 处） | `skills/ebuygo-content-ops/...` | `skills/scriptforge/...` |
| `scripts/generate-content-brief.py` docstring | `ebuygo-content-ops skill` | `scriptforge skill` |
| `scripts/unpack-7z.py` docstring | 同上 | 同上 |

## 2. 交付清单（清单外不建文件）

| 路径 | 类型 |
|---|---|
| `tasks/CHG-20261115-brand-neutralize/{CHANGE,SPEC,TRACEABILITY,TASK_ORCHESTRATION}.md` | 新建 |
| `SKILL.md` | 修改（仅上述 4 处） |
| `skill.manifest.json` | 修改（仅上述 5 处） |
| `scripts/generate-content-brief.py` | 修改（仅 docstring） |
| `scripts/unpack-7z.py` | 修改（仅 docstring） |

## 3. 验收命令

```bash
grep -rli "ebuygo\|易购宝" SKILL.md skill.manifest.json scripts/ ; echo "期望无输出"
python -c "import json;d=json.load(open('skill.manifest.json',encoding='utf-8'));print(d['id'], d['entrypoint']['path'])"
python -m unittest discover -s tests        # 零功能破坏
```

## 4. 回归保护

- 引擎、测试、形态规则、模板一律不动
- 三形态验收命令结果必须与改名前完全一致
