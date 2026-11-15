# CHANGE：视觉资产纳管与 README 视觉体系

- change_id: CHG-20261115-visual-assets
- 提出人: Owner
- 提出时间: 2026-11-15
- 状态: approved
- 上游 CHG: CHG-20261115-multimodal-decompose、CHG-20261115-viralmath-engine
  （本 CHG 接管这两个 CHG 的**呈现层**：README 美术与视觉资产归属）

---

## 0.1 原始需求（Owner 原话）

> 这张图 `assets/banner.png`，你看是不是也能切割一下用起来？
>
> 立一个小 CHG 管视觉资产，然后 commit push 掉吧

## 0.2 现状审计（实测）

| 事实 | 证据 |
|---|---|
| 旧主视觉是位图，且扩展名与格式不符 | `assets/banner.png` magic = `ffd8ffe0`，**实为 JPEG**；1024×1024，483 KB，四周约 30% 为空白渐变，有效内容仅中间约 920×380 横条 |
| 内容与产品现状脱节 | 画面为赛博霓虹「文案 / 爆款」+ 播放键 + 钢笔，属**视频单形态时代**产物；不含三形态、不含 7 维量化任何信息 |
| 中文字烘焙在像素里 | 「文案」「爆款」直接渲染进位图，改文案必须重画整张图 |
| 直接切用不可行（实测三条） | ① 直切贴米白底：切块自带深紫黑底，角落亮度 **25–29/255**，成硬边暗矩形；② 抠图去背：霓虹发光必留紫青晕 + 高光噪点（区块饱和度 135–165），成发光贴纸；③ 2× 放大：软发光画风无硬边，糊 |
| 与已定视觉体系基因冲突 | 赛博霓虹 + 蓝紫渐变 = 通用 AI 味默认审美；README 已改为瑞士平面 × 构成主义（三色、平涂、零渐变、零圆角） |
| 视觉资产无 CHG 归属 | 两份既有 TRACEABILITY「独占清单核对」均只列 `*.md` 资产，**未列 `assets/*.svg`** → 新增 SVG 属清单外建文件 |
| 运行时产物未忽略 | 仓库无 `.gitignore`；`cache/`、`guji-cache/`、`logs/`、`__pycache__/`、`scripts/*.log`、`tests/*.log` 全部裸露在 `git status` |

**结论（根因）**：视觉资产缺少**归属与契约**。没有归属 → 谁也说不清 `assets/*.svg` 该不该存在；没有契约 → 颜色、形状、技术边界全靠临场发挥，下一个人接手就会往 README 里塞第二套画风。

## 0.3 目标形态

1. **主视觉矢量化**：`assets/banner.svg` 顶替 `assets/banner.png` 作为 README 首图，三色纪律、平涂、零渐变。
2. **语义承接而非像素复用**：旧图唯一值得留下的是「播放三角 = 视频 / 钢笔尖 = 文案」这个符号语义 → 用新基因重绘为**单形体**标记 `assets/mark.svg`（三角既是播放键也是笔尖），可作头像 / favicon。
3. **契约化**：把色彩、形状、技术、尺寸四条写成冻结契约，后续任何人加视觉资产都受同一套约束。
4. **合法入库**：补 `.gitignore` 隔离运行时产物，让 `git status` 只反映真实资产变更。

## 1. 范围

### 1.1 In Scope

- `assets/banner.svg` 新建（README 首图）
- `assets/mark.svg` 新建（品牌标记）
- `.gitignore` 新建（运行时产物隔离）
- `README.md` 视觉层修改（首图引用、徽章条、排版节奏、去 emoji、大号数字锚点）
- 两份既有 CHG 的 TRACEABILITY 增进**资产归口**声明

### 1.2 Out of Scope

- **不删除** `assets/banner.png`（保留为历史留档；仅从 README 引用中移除）
- 不做位图导出（`banner@2x.png`）：已验证可生成 2560×680，但当前无一交付方需要位图，不预先入库
- 不改 README 的**事实性内容**（能力表、模型表、输出结构由前两个 CHG 的契约决定）
- 不改任何脚本、测试、references 规则文档
- 不做动图 / 视频 / GIF 封面

## 2. 风险与对策

| 风险 | 对策 |
|---|---|
| SVG 在部分渲染器（旧版 GitHub、某些 Markdown 预览）显示异常 | 只用最基础图元：`rect` / `polygon` / `text` / `line` / `circle`；不依赖 CSS 变量、不依赖外部字体文件 |
| 字体缺失导致字重塌陷 | 字族只写通用回退链（Helvetica / Arial / sans-serif）；不嵌 webfont |
| 矢量在深色主题下变成亮色块 | 接受：横幅作为「海报」存在，不随主题反色；已用纸色底做视觉锚定 |
| 新增资产再次越出清单 | 本 CHG 的 SPEC §4 冻结交付清单，并在两份旧 TRACEABILITY 增加归口行 |
| `.gitignore` 误伤验收日志 | 只忽略具体目录与 `scripts/*.log`、`tests/*.log`，**不**用全局 `*.log` |

## 3. 成功判据

1. `assets/banner.svg`、`assets/mark.svg` 均为合法 XML，且仅含白名单色值。
2. 两个 SVG 内**零渐变、零滤镜、零位图嵌入、零外链、零脚本**。
3. README 首图引用可达，正文**零 emoji**。
4. `.gitignore` 生效后，`git status` 不再出现 `cache/ logs/ __pycache__ *.log` 类噪声。
5. 两份旧 CHG 的独占清单含资产归口行，无「清单外建文件」残留。

---

## 4. rev1.1 范围扩展（Owner 授权，2026-11-15）

### 4.1 触发

> 你看能不能给项目写一个 AGENTS.md，做一个 agent 开发与后续开发者 PR 的指导文档，言简意赅的完成开发者智能体注入？
> 另外，对于这个一句话部署：「请帮我部署这个 skill：https://github.com/hhx465453939/ScriptForge」，完整的执行链条，再进行一次验证，确保任何时候，任何 agent，都可以丝滑快速的利用这句话部署这个项目。

### 4.2 实测：一句话部署链当前是断的

从 GitHub 全新 `git clone --depth 1` 到干净目录，**不设** `PYTHONIOENCODING`（即 Windows 默认 GBK 控制台）后实跑 6 次 CLI：

| 命令 | 退出码 | 现象 |
|---|---|---|
| `genre_probe --file samples/video.txt` | 0 | 中文乱码（GBK 字节被按 UTF-8 解码） |
| `genre_probe --file samples/graphic.txt` | **1** | `UnicodeEncodeError: 'gbk' codec can't encode character '\U0001f62d'`（标题含 emoji） |
| `genre_probe --file samples/text.txt` | 0 | 中文乱码 |
| `viral_score --file samples/video.txt` | **1** | `UnicodeEncodeError: 'gbk' codec can't encode character '\xb2'`（报告内 `R²` 上标） |
| `viral_score --file samples/graphic.txt` | **1** | 同上 |
| `viral_score --file samples/text.txt` | 0 | 中文乱码 |
| `python -m unittest discover -s tests` | 0 | 正常（79 项全绿） |

**根因**：两个 CLI 直接 `print()` 到 `sys.stdout`，未规范化流编码。Windows 控制台默认 `cp936`，遇到 emoji 或上标 `²` 直接抛异常；管道场景下 GBK 字节被 agent 按 UTF-8 解码 → 乱码。这不是个别字符问题，是**流编码层缺失**。

### 4.3 rev1.1 新增范围

| 项 | 内容 |
|---|---|
| 开发者注入文档 | `AGENTS.md`（开发型 agent 的最小必要上下文 + PR 指导） |
| 部署链健壮性 | 新增 `scripts/viralmath/console.py`（流编码规范化）；`scripts/genre_probe.py`、`scripts/viral_score.py` 接入；两处日志 sink 固定 `encoding="utf-8"` |
| 部署章节重写 | `README.md` §09 增加「一分钟验证」「终端编码说明」「开发者入口」 |
| 契约归口 | `CHG-20261115-viralmath-engine/TRACEABILITY.md` 增加脚本接管行 |

### 4.4 rev1.1 成功判据

1. 全新克隆后，6 次 CLI 调用 **全部 exit=0**，输出可被 UTF-8 正确解码（无乱码）。
2. `python -m unittest discover -s tests` 仍全绿（79 项）。
3. 任意 agent 仅凭一句「部署这个 skill + 仓库地址」即可完成：克隆 → 跑通三条验证 → 开始使用。
4. `AGENTS.md` 能让一个零上下文 agent 在 5 分钟内定位「该改哪个文件、怎么验证、哪里不能碰」。
