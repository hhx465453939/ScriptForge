# CHANGE：B 入口从 campaign 模式重构为 pipeline 模式

- change_id: CHG-20261115-pipeline-mode
- 提出人: Owner
- 提出时间: 2026-11-15
- 状态: approved
- 上游 CHG: CHG-20261115-ops-campaign-loop（本 CHG 局部取代其 S5–S8 与物料包契约）

---

## 0.1 原始需求（Owner 原话，节选）

> 我试了一下，输出物料包的效果不好，我更希望能够通过这个工具，把 agent 的注意力最大化的用到爆款文案这个核心产品的输出上……需要改的就是最终的输出这块的注意力约束和收敛方面的优化
>
> B 入口（运营作战台）是为「团队协作」设计的，不是为「个人生产流水线」设计的……物料包是过程文档，不是最终交付物。你真正需要的是：「这段文案给抖音 → 这是 MPT 的输入参数 → 这是 MatrixMedia 的分发指令」
>
> 砍掉排期表/台账/校准模板（这些是团队协作工具，个人流水线用不上）
> S4→S5 合并：文案写完直接输出下游工具的调用参数
> S7/S8 简化为「数据回读」

## 0.2 现状审计（实测）

| 事实 | 证据 |
|---|---|
| B 入口输出 10 类文件 | `assets/campaign-package.md` §2 缺件判定 |
| 其中 7 类是**过程文档** | `00-brief` / `01-recon` / `02-positioning` / `03-backlog` / `06-schedule` / `07-ledger` / `08-review` |
| 唯一可执行的是 `04-scripts` | 而它下游还要人工转成 MPT 参数与分发命令 |
| S5「组装」产出提示词与 HTML，但不给下游工具参数 | `ops-loop.md` §6 |
| S6 排期表等人执行 | `ops-loop.md` §7 |
| S7 台账等人填 | `ops-loop.md` §8 |
| `campaign_init.py` 生成 10 文件骨架 | `scripts/campaign_init.py` `_templates()` |

**结论（根因）**：B 入口的骨架是从**广告代理公司的工作流**抄来的——那个场景是多人协作，需要排期表与台账来协调。
但个人流水线里**工具链本身就是协调机制**：文案 → MPT → MatrixMedia → 数据回读。
中间的排期表、台账、校准模板是**为协调人类而存在的**，个人场景里只有两个作用：稀释注意力、制造虚假完备感。

**这不是文案质量问题，是输出物形态错位。**

## 0.3 目标形态

```
输入：一个选题 / 一个目标
  → 产出：每个平台一个目录，里面只有 3 类东西
      ① 可直接念/发的文案
      ② 可直接投喂的下游工具参数（MPT JSON / MatrixMedia 命令）
      ③ 必要的视觉提示词
  → agent 的注意力 100% 落在文案本身 + 参数正确性上
```

**判据**：用户拿到目录后，不需要读任何过程文档，只要执行 `publish.sh` 与把 `mpt.json` 交给 MPT。

---

## 1. 范围

### In Scope
- B 入口输出物：10 类过程文件 → 每平台 3 类可执行文件
- 新增下游契约文档（MPT `VideoParams` / MatrixMedia CLI 真实参数，**实测自源码，不许编**）
- S4 生产 与 S5 组装 合并为一步
- S6 排期 / S7 台账 / S8 校准模板 → 降级为「数据回读」一页
- `scripts/pipeline_init.py` 替代 `campaign_init.py`
- 文档口径同步（SKILL / README / manifest / ops-loop 标注废弃段）

### Out of Scope
- 不改文案方法论（形态矩阵、模型库、完形填空、量化引擎全部不动）
- 不实现真实发布（`publish.sh` 只生成命令，执行由人）
- 不实现真实数据抓取（回读交 SocialDataX MCP，本项目只给字段与格式）
- 不删除旧文件（标注废弃，保留可追溯）

## 2. 风险与对策

| 风险 | 对策 |
|---|---|
| 参数写错比没写更糟（工具直接报错） | 所有字段**实测自下游源码**，文档标注来源文件与行号；不确定的写 `UNKNOWN` 并注明如何查 |
| 小红书图文无法自动分发 | 如实标注：MatrixMedia `cli publish` 只发本地视频，图文笔记需人工。**不假装能自动** |
| 砍掉过程文档后失去可追溯性 | 关键决策压进 `README.md` 的 3–5 行摘要（目标/定位/选题理由），不再单独成文件 |
| 用户仍想用 campaign 模式 | 旧文件标注废弃但保留；`ops-loop.md` 保留 S0–S4（目标/侦察/定位/选题仍有价值），只废弃 S5–S8 的重型产物 |
| 迁移期两套入口混乱 | `pipeline_init.py` 为默认；`campaign_init.py` 标注「团队协作场景可选」 |

## 3. 成功判据

1. `python scripts/pipeline_init.py --slug x --platforms douyin,xiaohongshu,gongzhonghao` 产出每平台目录，各含 3 类文件
2. `douyin/mpt.json` 的键名与 MPT `VideoParams` 实测字段一致
3. `douyin/publish.sh` 的 CLI 参数与 MatrixMedia `cli publish` 实测参数一致
4. 产出目录内**不存在** schedule / ledger / review / brief / recon / positioning / backlog
5. `pipeline_init.py --check` 能判定缺件
6. 既有 91 项单测与三形态评分零变化（引擎未动）
