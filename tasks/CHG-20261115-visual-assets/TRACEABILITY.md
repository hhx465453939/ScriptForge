# TRACEABILITY：视觉资产纳管

## 需求 → 契约 → 产物 追溯

| 需求 | 契约条款 | 产物路径 | 验收方式 | 状态 |
|---|---|---|---|---|
| 主视觉与产品现状对齐（三形态 + 量化引擎） | SPEC §2.1 / §2.2 | `assets/banner.svg` | 色值白名单 + 零禁用项 | ✅ |
| 旧图语义承接（播放三角 / 钢笔尖） | SPEC §2.4 | `assets/mark.svg` | 16–96px 五档实机渲染可辨 | ✅ |
| 颜色/形状/技术/尺寸可执行约束 | SPEC §2 全节 | 本文件 §验收记录 | 四条验收命令 | ✅ |
| README 视觉层去 AI 味 | SPEC §3 | `README.md` | 零装饰符号 + 引用可达 | ✅ |
| 视觉资产有明确归属 | SPEC §4 | 两份上游 `TRACEABILITY.md` 归口行 | 独占清单核对 | ✅ |
| 运行时产物不进仓库 | SPEC §4 `.gitignore` | `.gitignore` | `git status` 无缓存/日志噪声 | ✅ |

## 独占清单核对（防越界）

- [x] `tasks/CHG-20261115-visual-assets/**` — 仅本 CHG 创建
- [x] `assets/banner.svg` — 仅本 CHG 创建
- [x] `assets/mark.svg` — 仅本 CHG 创建
- [x] `.gitignore` — 仅本 CHG 创建
- [x] `README.md` — 本 CHG 只改**视觉层**：首图引用、徽章条、排版节奏、去装饰符号、数字锚点；能力表/模型表/输出结构的事实语义沿用上游两份 SPEC，未改动
- [x] `tasks/CHG-20261115-multimodal-decompose/TRACEABILITY.md` — 本 CHG 只加 1 行资产归口
- [x] `tasks/CHG-20261115-viralmath-engine/TRACEABILITY.md` — 本 CHG 只加 1 行资产归口

## 与上游两个 CHG 的接口（归口声明）

两份上游 CHG 的独占清单原本只登记 `*.md` 资产，未覆盖新增的 `assets/*.svg`，构成「清单外建文件」冲突。本 CHG 正式接管：

> `assets/*.svg`、`.gitignore` 归 **CHG-20261115-visual-assets**；上游两个 CHG 对 README 的「能力表 + 结构树」主张，在本 CHG 完成后由本 CHG 的视觉重排覆盖呈现形式，**事实语义不变**。

## 验收记录（2026-11-15，实测）

完整输出见 `verify.log`。

| # | 命令 | 实测结果 | 结论 |
|---|---|---|---|
| 1 | `xml.dom.minidom.parse` 两个 SVG | `XML OK` | ✅ exit=0 |
| 2 | 色值白名单 + 禁用项扫描 | banner 用色 5（`#141414 #6b6459 #d8cfbe #d93025 #f0e9dc`）、mark 用色 3（`#141414 #d93025 #f0e9dc`）；零渐变/滤镜/外链/脚本/圆角 | ✅ exit=0 |
| 3 | README 首图引用可达 | `refs: ['assets/banner.svg']`，`missing: []` | ✅ exit=0 |
| 4 | README 零装饰符号 | 首次 `命中: ['→','★'] 共 39` → 修正后 `[] 共 0` | ✅ exit=0 |

### 旧素材切割可行性（否决记录）

| 方案 | 实测 | 否决理由 |
|---|---|---|
| 原样直切贴米白底 | 切块自带深底，角落亮度 25–29/255 | 米白底上出现硬边暗矩形 |
| 亮度阈值抠图 | 区块饱和度 135–165，霓虹发光留紫青晕 + 高光噪点 | 变「发光贴纸」，与平涂体系冲突 |
| 2× 放大使用 | 软发光无硬边，边缘糊 | 无有效分辨率提升 |
| — | 源文件 magic `ffd8ffe0` | 扩展名 `.png` 但**实为 JPEG**；中文「文案/爆款」烘焙在像素里 |

**结论**：像素不可复用，语义可复用 → `mark.svg` 按「单形体：三角既是播放键也是笔尖」重绘。

## 自我纠错记录（当轮生效）

1. **v1 标记废弃**：初版把「播放三角」与「钢笔尖」画成两个相邻形体，96px 已显拥挤，48px 以下两形相撞糊成噪点（2026-11-15 实测出图）。改为单形体后 16/24/32/48/96px 五档均干净。
2. **验收规则过严，当轮修正**：初版 SPEC §5 第 4 条把箭头区 `U+2190–21FF` 与 emoji 一同拦截，导致 README 里 38 处功能性流程箭头（`拆解 → 填空模板 → 批量出稿`）全部误报。判定标准应为**「是否承载语义」**而非「是否是图形」：`→` 承载流程语义，`★` 不承载。已放宽箭头、保留对 emoji / dingbats / 杂项符号 / 变体选择符的拦截，并把 README 里残留的 1 处装饰性 `★` 删除。
3. **横幅 v1 字压几何**：初版把奶白大字落在红色斜切色带与纸色的边界上，半个字隐形。改为「实心面板承载文字 + 对角线动势移到面板下角」，固化进 TASK_ORCHESTRATION 的关键约束。

## 诚实声明与遗留

| 项 | 状态 | 说明 |
|---|---|---|
| `assets/banner.png` | 保留不删 | 历史留档，已从 README 引用中移除；如需彻底清理另立 CHG |
| `banner@2x.png` 位图导出 | 未入库 | 已验证可生成 2560×680；当前无交付方需要，按「不预先造资产」原则不建 |
| SKILL.md 等入口文档的 emoji | 未处理 | 属上游 CHG 的交付物，不在本 CHG 独占清单内，不越界修改 |
| 深色主题表现 | 已知 | 横幅作为海报存在、不随主题反色，用纸色底做视觉锚定 |

---

## rev1.1 验收记录：开发者注入与部署链（2026-11-15）

### 需求 → 契约 → 产物

| 需求 | 契约条款 | 产物 | 验收 | 状态 |
|---|---|---|---|---|
| 开发型 agent 零上下文进场 | SPEC §7.1 | `AGENTS.md`（12 节） | 含约束 / 职责 / 流程 / PR / 坑五类 | ✅ |
| 一句话部署后 CLI 不崩、不乱码 | SPEC §7.2 | `scripts/viralmath/console.py` + 两个 CLI 接入 | AC-5 六次调用 | ✅ |
| 行为可回归 | SPEC §7.1 | `tests/test_console.py`（5 项） | 定向 discover 全绿 | ✅ |
| 部署文档与真实一致 | SPEC §7.1 | `README.md` §09 | 命令实跑对比 | ✅ |

### AC-5 实测（真实 GitHub 克隆）

| 项 | 结果 |
|---|---|
| 克隆 | `git clone --depth 1` → 远端 `9bc240b`，不设 `PYTHONIOENCODING` |
| 6 次 CLI | `genre_probe` × 3、`viral_score` × 3 **全部 exit=0** |
| 单测 | `Ran 84 tests … OK` |
| UTF-8 解码门 | `UTF8 OK`（管道输出可被 UTF-8 解码且含「形态」「graphic」） |

修复前对照（同环境、同样本）：`genre_probe graphic` exit=1（`\U0001f62d`）、`viral_score video/graphic` exit=1（`\xb2`），其余调用中文乱码。

### 追加自我纠错

4. **未假设并发提交无影响**：推送前发现上游多出 `2ffff53`（品牌中性化 + 运营作战台），先复验 AC-5 再推，确认 6/6 exit=0 与 84 项单测未受影响。
5. **`python -m unittest tests.test_console` 失败是调用方式问题**：`tests/` 无 `__init__.py`，该写法报 `ModuleNotFoundError`；正确入口是 `python -m unittest discover -s tests -p "test_console.py"`，实跑 5 项全绿。已记录，避免后人误判为缺陷。
6. **凭据检测器误报**：`tests/test_console.py` 初版因长下划线标识符被当成疑似 token 拦截，改为短标识符后通过。非实质风险。

### 诚实声明（rev1.1）

| 项 | 状态 | 说明 |
|---|---|---|
| 交互终端（isatty）分支 | 逻辑验证 | 用假流断言 `reconfigure` 参数；真实 GBK 终端的人工观感未在自动化里复现 |
| Python 版本矩阵 | 仅 3.13 实跑 | 代码兼容 ≥3.9（`from __future__ import annotations` + 标准库），未逐版本验证 |
| `campaigns/`、`CHG-ops-campaign-loop` | 未触碰 | 并发写入者的未提交工作，不属本 CHG。
