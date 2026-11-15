---
change_id: CHG-20261115-visual-assets
version: 1.0
status: spec_frozen
parent_spec: null
prev_spec: null
prd_ref: CHANGE.md §0（实测审计已足够具体）
approved_by: Owner
approved_at: 2026-11-15
---

# SPEC：视觉资产纳管与 README 视觉体系

## 0. 收敛原则

1. **矢量优先**：主视觉一律 SVG，不引入位图。位图仅在有明确交付方（如公众号后台不收 SVG）时才导出，且不入库。
2. **三色纪律**：品牌色只有三个——纸、墨、红。中性灰阶只作辅助，不得当强调色用。
3. **零特效**：禁止渐变、阴影、滤镜、发光、圆角。高级感来自留白与对齐，不来自特效。
4. **语义优先于像素**：旧素材的价值在语义，不在像素。要复用就重绘，不切图。
5. **技术白名单**：只用 `rect` / `polygon` / `text` / `line` / `circle`；不嵌位图、不引外链、不写脚本、不用 CSS 变量。
6. **不破坏历史**：旧 `assets/banner.png` 保留在库，仅取消引用。
7. **契约单一承载**：色彩 / 形状 / 技术 / 尺寸四条契约**只**写在本文件 §2，其他文件只引用。

---

## 1. 上下文

见 CHANGE.md §0.2。一句话：**旧主视觉与产品现状脱节，且视觉资产没有归属与契约。**

---

## 2. 契约：视觉规则（冻结）

### 2.1 色彩

| 角色 | 色值 | 允许用途 |
|---|---|---|
| 纸 `paper` | `#f0e9dc` | 横幅底、反向文字（红底上）、标记负空间 |
| 墨 `ink` | `#141414` | 正文文字、几何体、描边、分区线 |
| 红 `brand` | `#d93025` | 唯一强调色：品牌字、色块、标记焦点。面积建议 ≤25% |
| 灰·次要 `muted` | `#6b6459` | 次级说明文字（规格行、微标签） |
| 灰·辅助线 `rule` | `#d8cfbe` | 栅格辅助线，仅 1–2px |

**红线**：除上表外**不得使用任何色值**；不得出现渐变（`linearGradient` / `radialGradient`）、阴影、`<filter>`。

### 2.2 形状

- 圆角一律 `0`（不使用 `rx`/`ry`，不使用 `stroke-linejoin="round"`）。
- 描边风格统一：硬边、miter 转角；同一产物内不混用描边与填充两套语言。
- 构图遵守栅格：左对齐统治，元素要么压栅格线，要么明确越格。

### 2.3 技术

| 项 | 规定 |
|---|---|
| 图元 | 仅 `rect` `polygon` `text` `line` `circle` `title` |
| 字体 | 通用回退链 `Helvetica Neue, Helvetica, Arial, sans-serif`；**不嵌 webfont** |
| 外链 | 禁止（无 `xlink:href="http..."`、无 `<image>`） |
| 脚本 | 禁止（无 `<script>`、无 `onload` 等事件属性） |
| 位图嵌入 | 禁止（无 base64 image） |
| 无障碍 | 必须带 `role="img"` 与 `<title>` / `aria-label` |

### 2.4 尺寸

| 资产 | viewBox / 尺寸 | 比例 | 用途 |
|---|---|---|---|
| `assets/banner.svg` | `1280 × 340` | 3.76 : 1 | README 首图、仓库社交预览 |
| `assets/mark.svg` | `64 × 64` | 1 : 1 | 仓库头像、favicon、PPT 角标 |

**最小可读性**：`mark.svg` 在 16px 宽下必须仍可辨识为「播放三角」；小于 24px 时允许丢失笔尖细节（红孔与开缝自然消失），但不许糊成噪点。

---

## 3. 契约：README 视觉层

| 项 | 规定 |
|---|---|
| 首图 | `<img src="assets/banner.svg" width="100%">`，居中 |
| 徽章 | shields.io `style=flat-square`；配色只用本 SPEC 色值；红只出现一次 |
| emoji | 正文**零 emoji**；层级符号改用大号数字锚点（`00`–`12`） |
| 章节 | 标题格式 `## NN 中文标题`；导航锚点必须与标题一一对应 |
| 表格 | 统一左对齐；列数一致；正文表格不做居中排版 |
| 分隔 | 只用 `---` 水平线做章节分隔，不加装饰图 |

---

## 4. 交付清单（清单外不建文件）

| 路径 | 类型 | 说明 |
|---|---|---|
| `tasks/CHG-20261115-visual-assets/{CHANGE,SPEC,TRACEABILITY,TASK_ORCHESTRATION}.md` | 新建 | 本 CHG 四件套 |
| `assets/banner.svg` | 新建 | README 首图（1280×340） |
| `assets/mark.svg` | 新建 | 品牌标记（64×64，单形体：播放三角即笔尖） |
| `.gitignore` | 新建 | 运行时产物隔离（cache / logs / `__pycache__` / 脚本日志） |
| `README.md` | 修改 | **仅视觉层**：首图引用、徽章条、排版节奏、去 emoji、数字锚点 |
| `tasks/CHG-20261115-multimodal-decompose/TRACEABILITY.md` | 修改 | 独占清单增一行资产归口 |
| `tasks/CHG-20261115-viralmath-engine/TRACEABILITY.md` | 修改 | 独占清单增一行资产归口 |

**明确不建**：`assets/banner@2x.png` 及任何位图导出、`.github/` 下的社交预览图、任何额外的装饰 SVG。

---

## 5. 验收命令（全部必须退出码 0）

```bash
# 1 · 两个 SVG 均为合法 XML
python -c "import xml.dom.minidom as m; [m.parse(p) for p in ['assets/banner.svg','assets/mark.svg']]; print('XML OK')"

# 2 · 色值白名单 + 零渐变零滤镜零外链零脚本
python - <<'PY'
import re, sys
allow = {"#f0e9dc", "#141414", "#d93025", "#6b6459", "#d8cfbe"}
bad = []
for p in ["assets/banner.svg", "assets/mark.svg"]:
    s = open(p, encoding="utf-8").read()
    used = {c.lower() for c in re.findall(r"#[0-9a-fA-F]{6}", s)}
    bad += [f"{p}: 越界色 {c}" for c in used - allow]
    for pat in ["linearGradient", "radialGradient", "<filter", "<script", "<image",
                'href="http', "rx=", "ry=", "stroke-linejoin=\"round\""]:
        if pat in s:
            bad.append(f"{p}: 命中禁用项 {pat}")
print("\n".join(bad) if bad else "COLOR/SHAPE OK")
sys.exit(1 if bad else 0)
PY

# 3 · README 首图引用可达
python -c "import re,os; src=open('README.md',encoding='utf-8').read(); refs={p for p in re.findall(r'src=\"(assets/[^\"]+)\"', src)}; miss=[p for p in refs if not os.path.exists(p)]; print('refs:',sorted(refs)); print('missing:',miss); raise SystemExit(1 if miss else 0)"

# 4 · README 正文零装饰符号
python -c "import re,sys; s=open('README.md',encoding='utf-8').read(); hit=re.findall(r'[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\uFE0F]', s); print('装饰符号命中:', sorted(set(hit)), '共', len(hit)); sys.exit(1 if hit else 0)"
```

> 禁 emoji、dingbats、杂项符号与变体选择符（`U+1F000–1FAFF` / `U+2600–27BF` / `U+2B00–2BFF` / `U+FE0F`）。
> **放行** `U+2190–21FF` 的功能性箭头：表格与流程里的 `A → B → C` 承载信息结构，不是装饰；瑞士平面体系本身就大量使用箭头。
> 判定标准是「这个符号是否承载语义」，不是「它是不是图形」——`→` 有语义，`★` `✨` `✅` 没有。

---

## 6. 回归保护

- `README.md` 的事实性内容（能力表 / 模型表 / 输出结构 / 命令行示例）**沿用前两个 CHG 已冻结的契约**，本 CHG 不得改动其语义，只改呈现。
- 不触碰 `scripts/**`、`tests/**`、`references/**`、`samples/**`。
- 旧 `assets/banner.png` 不删、不改名。
