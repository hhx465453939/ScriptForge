# TASK_ORCHESTRATION：七维正交性修复

## 执行顺序（依赖串行）

| # | 动作 | 产物 | 依赖 |
|---|---|---|---|
| 1 | 新增句长交替率测度 | `rhythm.alternation_rate` | 无 |
| 2 | 新增情绪峰值位置测度 | `affect.peak_position` | 无 |
| 3 | 更新子指标权重与饱和上限 | `genres.SUB_WEIGHTS` / `CAPS` | 1,2 |
| 4 | 重构 D1/D2/D3/D4 子指标与 trace | `engine.dimensions` | 1-3 |
| 5 | 审计工具（源依赖 + 相关 + 特征值） | `scripts/dim_audit.py` | 4 |
| 6 | 新增测试（新测度 / 正交性 / 审计） | `tests/test_viralmath.py` | 1-5 |
| 7 | 维度定义与审计章节 | `references/math-engine.md` | 4,5 |
| 8 | 口径同步三处 | `SKILL.md` / `README.md` / `skill.manifest.json` | 7 |
| 9 | 实测 + 记录分数变化 | 本 CHG `TRACEABILITY.md` §A/§C | 全部 |
| 10 | 全量验收 | 见 SPEC §5 | 全部 |

## 关键实现约束

- **纯标准库**：审计工具只用 `math` / `statistics` / `argparse` / `json` / `os` / `logging`
- **新测度必须自带可靠性门**：n < 5 → `reliable=False`，引擎取中性 0.5，不许用噪声当真信号
- **不得改 7 维键名**：`hook/density/rhythm/emotion/persuasion/distinction/replicability` 冻结
- **不得改 AHP 矩阵与 CR 门控**：仍 7×7，CR>0.1 抛异常
- **交替率定义**：`sign(x[i+1]-x[i])` 的变化次数 / (n-1)；差值为 0 时不计变化
- **峰值位置定义**：`argmax(arousal) / max(1, n-1)`，用 arousal 而非 valence（避免与振幅/方向同源）
- **审计工具必须打印 n 警告**：n<30 时明确「仅作健全性检查」

## 反模式（明令禁止）

| 反模式 | 为什么禁止 |
|---|---|
| 只删子指标不补新方面 | 维度信息量塌陷，变成"为了不共线而变弱" |
| 用 `1 - |r|` 之类事后加权去抵消共线 | 掩盖问题而非解决，且不可解释 |
| 小样本相关矩阵当结论 | n≈12 的 r 置信区间极宽，会误导 |
| 改了实现不改文档 | 口径不一，等于对外撒谎 |
| 静默改分数 | 用户会以为模型坏了；必须记录改前改后与原因 |

## 完成定义（DoD）

- [ ] D1 的 `token_counts` 依赖数 = 0
- [ ] D2 子指标 = 2（信息单元密度、归一化熵），Zipf 仅诊断
- [ ] D3 子指标 = 3（Gini、交替率、主周期），分属三个方面
- [ ] D4 子指标 = 4（波动率、斜率、峰值位置、情绪词密度），分属四个方面
- [ ] `dim_audit.py --strict` 退出码 0（无违规）
- [ ] 审计输出四块齐全且含 n 警告
- [ ] 七维键名断言通过
- [ ] 全量单测通过
- [ ] 五处口径一致
- [ ] TRACEABILITY §A/§C 有实测与分数对照
