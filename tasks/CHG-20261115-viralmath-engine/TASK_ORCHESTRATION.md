# TASK_ORCHESTRATION：爆款量化评估引擎

## 执行顺序（依赖严格串行）

| # | 动作 | 产物 | 依赖 |
|---|---|---|---|
| 1 | 常量词表与阈值 | `scripts/viralmath/calibration.py` | 无 |
| 2 | 特征抽取 | `scripts/viralmath/features.py` | 1 |
| 3 | 信息论工具 | `scripts/viralmath/info.py` | 无 |
| 4 | 节奏/序列工具 | `scripts/viralmath/rhythm.py` | 无 |
| 5 | 情绪工具 | `scripts/viralmath/affect.py` | 无 |
| 6 | 多准则决策 | `scripts/viralmath/mcdm.py` | 无 |
| 7 | 不确定度 | `scripts/viralmath/uncertainty.py` | 无 |
| 8 | 对齐 | `scripts/viralmath/align.py` | 无 |
| 9 | 形态档 + 判断矩阵（须 CR 校验） | `scripts/viralmath/genres.py` | 6 |
| 10 | 编排 | `scripts/viralmath/engine.py` | 2-9 |
| 11 | CLI | `scripts/viral_score.py` | 10 |
| 12 | 形态判定 CLI | `scripts/genre_probe.py` | 2 |
| 13 | 样本 | `samples/{video,graphic,text}.txt` | 无 |
| 14 | 单测 | `tests/test_viralmath.py` | 3-10 |
| 15 | 数学规范文档 | `references/math-engine.md` | 全部 |
| 16 | 评分卡模板 | `assets/quant-scorecard-template.md` | 10 |
| 17 | 主入口/清单/README 同步 | `SKILL.md`、`skill.manifest.json`、`README.md` | 15 |
| 18 | 全量验收 | 见 SPEC §5 | 全部 |

## 关键实现约束

- **纯标准库**：`math`/`statistics`/`random`/`re`/`json`/`argparse`/`collections`/`dataclasses`/`unittest`
- **无 Beta 分位函数** → 自建正则化不完全 Beta（Lentz 连分式 + 二分求分位）
- **无 mel spectrogram/FFT 库** → 自建基-2 DFT（长度补零到 2 的幂）
- **无矩阵库** → AHP 主特征向量用幂迭代（Perron–Frobenius），λmax 用 Rayleigh 商
- **中文本分词** → 字符二元组 + ASCII 词，避免引入 jieba 依赖（文档须声明此近似）

## 完成定义（DoD）

- [ ] `python -m unittest discover -s tests -v` 全绿
- [ ] 三形态 CLI 各跑通，输出含 7 维 + 综合分 + CI + 短板 + feature trace
- [ ] 两次运行输出逐字节一致（复现性）
- [ ] 三形态 AHP 矩阵 CR 全 < 0.1（构建时硬校验）
- [ ] `references/math-engine.md` 每条工具四要素齐（何时用/公式/陷阱/解读）
- [ ] `skill.manifest.json` 合法 JSON
- [ ] 旧 3 个口播模型与 9 板块顺序零破坏
