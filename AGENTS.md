# AGENTS.md

给**开发型智能体**与后续贡献者的最小必要上下文。
目标：零上下文进场，5 分钟知道「该改哪个文件、怎么验证、哪里不能碰」。

面向使用者与安装的说明在 `README.md`；本文件面向改代码的人。

---

## 0. 一句话定位

ScriptForge 是一套 AI Skill：把短视频口播 / 图文笔记 / 纯文本长文拆成结构，量化其**形态内相对位置**，产出可填空模板。

| 层 | 位置 | 谁读 |
|---|---|---|
| 规则与知识库 | `references/*.md` | AI 运行时读取（人也要读） |
| 可执行引擎 | `scripts/`（纯标准库） | CLI 与单测 |
| 报告与评分卡模板 | `assets/*.md` | 输出对齐 |
| 变更记录 | `tasks/CHG-*/` | 追溯与契约 |

## 1. 五分钟自检（改任何东西之前先跑）

```bash
python -m unittest discover -s tests -v                    # 期望 OK
python scripts/genre_probe.py --file samples/graphic.txt   # 期望 形态: graphic
python scripts/viral_score.py --file samples/video.txt     # 期望 分数 + 分区 + CI
```

三条不全绿 → 先修环境，不要在这个状态下改代码。

## 2. 三条不可协商的约束

1. **零第三方依赖**：只用标准库。出现 `numpy / scipy / pandas / jieba` 视为破坏契约。
2. **可复现**：任何随机过程必须吃 `--seed`；同输入同 seed 输出逐字节一致（`test_determinism` 守着）。
3. **不预测播放量**：只给形态内相对位置。报告禁止出现「预测播放量约 X」。

## 3. 目录职责（改这里 → 必须连带改那里）

| 你要改 | 主文件 | 必须同步 |
|---|---|---|
| 形态判定规则 | `references/content-genres.md` | `features.detect_genre` + `genre_probe` 相关单测 |
| 维度算法 | `scripts/viralmath/*.py` | `references/math-engine.md` 对应小节（公式 / 陷阱 / 解读） |
| 权重与分区阈值 | `scripts/viralmath/genres.py` | `math-engine.md` §3 + TRACEABILITY |
| 词表与饱和上限 | `scripts/viralmath/calibration.py` | 保留 `CALIBRATION_PENDING` 标注 |
| 输出字段 | `scripts/viralmath/engine.py` | `viral_score.py` 报告模板 + `assets/quant-scorecard-template.md` |
| 脚本模型 | `references/script-models.md` | 完形填空骨架 + README 模型表 |
| 视觉资产 | `assets/*.svg` | `tasks/CHG-20261115-visual-assets/SPEC.md` §2 契约 |

**单点承载**：同一规则只写一处，其他文件只做引用与路由。写出第二份 = 破坏契约。

## 4. 改动流程（本项目强制）

1. **立 CHG**：`tasks/CHG-<日期>-<主题>/` 四件套 `CHANGE / SPEC / TRACEABILITY / TASK_ORCHESTRATION`
2. **SPEC 冻结**：写清 In/Out of Scope、交付清单（**清单外不建文件**）、验收命令
3. **实现**：先判根因，不打补丁；过程中发现的问题当轮修完
4. **验收**：SPEC 里的命令全部 exit=0，日志落盘
5. **记录**：TRACEABILITY 写实测结果 + 自我纠错 + 诚实声明（盲区不掩盖）

## 5. 代码约定

- Python ≥ 3.9；文件首行 `from __future__ import annotations`
- 类型标注齐全；纯函数优先；不引入全局可变状态
- **CLI 输出必须过 `viralmath.console.setup_streams()`**：管道统一 UTF-8、交互终端降级，否则 Windows GBK 下遇 emoji 直接崩
- 报分必须带区间与形态；短板必须给可执行改法（不是「情绪驱动低」）
- 新增数学工具：模块 docstring 写清「陷阱」，并同步 `math-engine.md`

## 6. 视觉契约（摘要，全文见 `CHG-20261115-visual-assets/SPEC.md` §2）

- 色值白名单：`#f0e9dc` 纸 / `#141414` 墨 / `#d93025` 红 / `#6b6459`、`#d8cfbe` 辅助
- 零渐变、零滤镜、零圆角、零位图嵌入、零外链、零脚本
- README 正文零 emoji；`→` 这类承载语义的功能箭头允许，`★` `✅` 这类装饰不允许

## 7. 禁区

- 不加第三方依赖；不改 `platform-insights.md` 的定性洞察
- 不删 `assets/banner.png`（历史留档）
- 不跨形态、跨账号比较绝对分（三形态权重档与基线不同）
- `CALIBRATION_PENDING` 状态下不得对外宣称「这条会爆」

## 8. PR 清单

- [ ] 自检三条命令全绿
- [ ] 有对应 CHG，且改动不越出 SPEC 交付清单
- [ ] 改了公式 → 同步 `math-engine.md`；改了规则 → 同步 `content-genres.md`
- [ ] 新增行为有单测（含失败路径）
- [ ] TRACEABILITY 有实测记录（命令 + 结果 + 退出码）
- [ ] commit message 用 `feat: / fix: / docs: / chore: / test:`，正文说清「为什么」

## 9. 如果你是 agent：开工顺序

1. 读本文件 → `README.md` 对应章节
2. 找到任务相关 CHG 的 `SPEC.md`（契约优先，没有就先立）
3. 跑 §1 自检
4. 用代码图谱或搜索定位文件；`scripts/` 可能未被索引覆盖，直读可接受
5. 改 → 跑 SPEC 验收 → 写 TRACEABILITY
6. 不自创规范；与既有契约冲突时，先改 CHG 再改实现

## 10. 已知坑（踩过，别再踩）

| 坑 | 现象 | 正解 |
|---|---|---|
| Windows 控制台 GBK | emoji / `²` 抛 `UnicodeEncodeError`，中文乱码 | 已由 `console.setup_streams()` 兜底；新 CLI 必须调用 |
| DFT 取全局最大峰 | 脉冲串周期报成真值的 1/2 | 取「最低频的局部极大值」 |
| 幂迭代用 L1 归一化 | AHP 的 λmax 被压到 < n，CR 恒为 0，一致性门控静默失效 | 用 L2 归一化 + Rayleigh 商 |
| JS 不扣噪声地板 | 所有输入饱和到 1.0，维度失去信息量 | 先扣 floor 再归一化 |
| 用余弦判「水平」 | 最差原型被判成最像 | 水平用归一化欧氏距离，余弦只用于形状 |
| 完形填空只堆占位符 | 规则重复写在 SKILL.md 与 fill-blank-guide | 单点承载，SKILL 只做路由 |

## 11. 参考

- 使用与安装：`README.md`
- 形态矩阵：`references/content-genres.md`
- 数学规范（公式 / 陷阱 / 解读 / 校准协议）：`references/math-engine.md`
- 变更追溯：`tasks/CHG-*/TRACEABILITY.md`
