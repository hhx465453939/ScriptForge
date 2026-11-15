# CHANGE：品牌中性化（ebuygo → ScriptForge）

- change_id: CHG-20261115-brand-neutralize
- 提出人: Owner
- 提出时间: 2026-11-15
- 状态: approved

## 0.1 原始需求（Owner 原话）

> ebuygo 是原先我参与的一家电商企业的品牌，把这个品牌在项目里面清理干净，现在这个项目就是纯粹的开源工具，属于我个人。

## 0.2 现状审计（实测 grep 全仓）

命中 4 个文件、共 9 处：

| 文件 | 命中内容 |
|---|---|
| `skill.manifest.json` | `"id": "ebuygo-content-ops"`；`"display_name": "Ebuygo 多形态…"`；`entrypoint.path`、`local_corpora`（3 处路径） |
| `SKILL.md` | frontmatter `name: ebuygo-content-ops`；description 前缀 `ebuygo(易购宝)`；标题行；正文首段「为 ebuygo（易购宝）打造」 |
| `scripts/generate-content-brief.py` | 废弃脚本 docstring 提及 `ebuygo-content-ops skill` |
| `scripts/unpack-7z.py` | 同上 |

**结论（根因）**：品牌名同时承担了三个角色——① skill 标识符（`name`/`id`）② 路径前缀（`skills/ebuygo-content-ops/`）③ 文案里的归属声明。清理必须三者同步，只改文案会留下错误路径。

## 1. 范围

### In Scope
- skill 标识符 → `scriptforge`
- 显示名 / 标题 / description 去掉品牌，改为中性表述
- 路径前缀同步（manifest 的 `entrypoint.path` 与 `local_corpora`）
- 两个废弃脚本的 docstring

### Out of Scope
- 不改任何功能逻辑、不改引擎、不改形态规则
- 不改 `tasks/CHG-20261115-{multimodal-decompose,viralmath-engine,visual-assets}/` 下历史文档中的引述（历史记录，改动等于篡改立项依据）；但其中若含品牌，追加一行「本项目已中性化」注记

## 2. 风险与对策

| 风险 | 对策 |
|---|---|
| 只改文案不改路径 → 宿主按 manifest 找不到入口 | 路径与标识符同批改，改完用 grep 验证零残留 |
| 改名破坏已有安装/引用 | 项目尚未发布使用，改名窗口成本最低；在 README 加一行「旧名 ebuygo-content-ops 已废弃」 |
| 历史 CHG 文档被误改，丢失立项证据 | 明确 Out of Scope，只在必要处加注记 |

## 3. 成功判据

1. `grep -rli "ebuygo\|易购宝"` 在 `SKILL.md`、`skill.manifest.json`、`scripts/` 上返回空
2. `skill.manifest.json` 为合法 JSON，`id` = `scriptforge`
3. 引擎与 CLI 全部验收命令仍通过（零功能破坏）
