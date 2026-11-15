# Pipeline 输出包 · 目录契约

> **本文件是 B 入口输出物的唯一契约。** 取代 `assets/campaign-package.md`（后者降级为「团队协作场景可选」）。
>
> 一句话：**目录里每一份文件，要么能被念，要么能被工具直接吃。没有「给人看的过程文档」。**

---

## 1. 目录结构（冻结）

```
output/<slug>_<YYYYMMDD>/
├── README.md                  战役摘要（≤5 行：目标 / 定位 / 选题理由）
│
├── douyin/                    抖音（video）
│   ├── script.md              口播全文 + 量化评分卡
│   ├── mpt.json               MPT VideoParams（可直接投喂）
│   └── publish.sh             MatrixMedia CLI 命令（可执行）
├── kuaishou/                  快手（video，同上三件）
├── shipinhao/                 视频号（video，同上三件）
├── bilibili/                  B站（video，16:9）
├── toutiao/                   头条（video，16:9）
├── baijiahao/                 百家号（video，16:9）
│
├── xiaohongshu/               小红书（graphic）
│   ├── note.md                图文正文 + 标签
│   ├── cover-prompt.md        封面提示词（13 字段）
│   └── publish.md             人工发布清单（⚠️ 图文不可自动分发）
│
└── gongzhonghao/              公众号（text）
    ├── article.html           长文 HTML（纯静态）
    ├── header-prompt.md       头图提示词（13 字段）
    └── publish.md             人工发布清单
```

**生成方式**

```bash
# 生成骨架（一条命令）
python scripts/pipeline_init.py --slug demo --platforms douyin,xiaohongshu,gongzhonghao
# 校验缺件
python scripts/pipeline_init.py --check output/demo_20261115
```

---

## 2. 平台映射（冻结）

| 平台名 | 目录 | CLI 码 | 画幅 | 类型 | 文件数 |
|---|---|---|---|---|---|
| `douyin` | `douyin/` | `dy` | 9:16 | video | 3 |
| `kuaishou` | `kuaishou/` | `ks` | 9:16 | video | 3 |
| `shipinhao` | `shipinhao/` | `sph` | 9:16 | video | 3 |
| `bilibili` | `bilibili/` | `blbl` | 16:9 | video | 3 |
| `toutiao` | `toutiao/` | `tt` | 16:9 | video | 3 |
| `baijiahao` | `baijiahao/` | `bjh` | 16:9 | video | 3 |
| `xiaohongshu` | `xiaohongshu/` | `xhs` | 9:16 | graphic | 3 |
| `gongzhonghao` | `gongzhonghao/` | — | — | text | 3 |

**为什么用平台名做目录**：比 `video-generic/` 更好——一眼知道发哪，`publish.sh` 里的 `-p` 码不会错配。

---

## 3. 每份文件的最小规格

### 3.1 `README.md`（≤5 行正文）

```markdown
# <slug> · <date>
目标：<平台> 的 <主指标>
定位：<一句话差异点>
选题：<条1>（理由）/ <条2>（理由）
下游：douyin → MPT 生成视频 → `bash douyin/publish.sh`
```

**超过 5 行正文即不合格**——那就是又变回过程文档了。

### 3.2 `<video>/script.md`

```markdown
---
platform: douyin
genre: video
model: 吐槽安利
---

## 文案全文
<可直接念的完整口播>

## 量化评分卡
| 综合分 | 分区 | 95% CI |
|---|---|---|
| 47.2 | C | [40.1, 52.8] |

| 维度 | 分数 |
|---|---|
| 钩子力 | ... |

短板：<前 2 项>

## 迭代记录
| 轮次 | 改动 | 综合分 | 变化 |
|---|---|---|---|
```

**最小要求**：评分卡必须来自 `python scripts/viral_score.py --json` 的真实输出，**不许手写数字**。

### 3.3 `<video>/mpt.json`

键名**只能**取自 `references/downstream-contracts.md` §1.1。最小必填：

```json
{
  "video_subject": "<标题，<=30字>",
  "video_script": "<与 script.md 正文逐字一致>",
  "video_terms": "<3-6 个素材检索词，空格分隔>",
  "video_aspect": "9:16",
  "video_clip_duration": 5,
  "video_source": "pexels",
  "voice_rate": 1.1,
  "voice_volume": 1.0,
  "bgm_type": "random",
  "bgm_volume": 0.15,
  "subtitle_enabled": true,
  "subtitle_position": "bottom",
  "font_size": 60,
  "text_fore_color": "#FFFFFF",
  "stroke_color": "#000000",
  "stroke_width": 1.5,
  "paragraph_number": 4,
  "video_count": 1
}
```

**红线**：
- 字段名不在契约表内 → 不合格
- 出现 `video_materials` / `custom_audio_file` / `bgm_file` → 不合格（本地路径项目无法预知）
- `video_aspect` 写成 `"横屏 16:9（西瓜视频）"` → 不合格（那是显示串，不是枚举值）

### 3.4 `<video>/publish.sh`

```bash
#!/usr/bin/env bash
# 平台: 抖音(dy)  生成于 <date>
# 前置：先用 mpt.json 在 MPT 生成视频，把下面的 VIDEO 改成真实绝对路径
set -euo pipefail

VIDEO="<待填：MPT 输出视频的绝对路径>"
PHONE="<待填：发布账号手机号>"

matrixmedia cli publish \
  -p dy \
  --phone "$PHONE" \
  -f "$VIDEO" \
  -t "<标题>" \
  --description "<简介>" \
  --tags "#标签1 #标签2" \
  --publish-at "YYYY-MM-DD HH:mm:ss"
```

**最小要求**：含 `matrixmedia cli publish` 与 `-p/--phone/-f/-t` 四个必填参数；
`-f` 未生成时必须写 `<待填：...>` 占位，**不许填假路径**。

### 3.5 `xiaohongshu/note.md`

```markdown
---
platform: xiaohongshu
genre: graphic
model: 圈人清单
---

## 标题
<12-18 字，套公式>

## 正文
<分段，1-3 行一段，emoji 作分段锚点>

## 标签
#标签1 #标签2 #标签3 #标签4（4-8 个，覆盖品类/人群/场景/长尾）

## 量化评分卡
<同上>
```

### 3.6 `xiaohongshu/cover-prompt.md`

沿用 `assets/prompt-spec.md` 的 **13 字段**（id / subject / scene / composition / lighting / style / palette / lens / negative / platform / model / params / usage）。

### 3.7 `xiaohongshu/publish.md`

```markdown
# 小红书发布清单（人工）

⚠️ **图文笔记无法通过 MatrixMedia CLI 分发**（`cli publish` 只发本地视频）。需人工操作。

| 步骤 | 内容 |
|---|---|
| 1 打开小红书 App / 创作中心 | — |
| 2 上传图片 | 按 `cover-prompt.md` 生成 6–9 张 |
| 3 粘贴标题 | 见 `note.md` §标题 |
| 4 粘贴正文 | 见 `note.md` §正文 |
| 5 粘贴标签 | 见 `note.md` §标签 |
| 6 发布时间建议 | <时段> |
```

### 3.8 `gongzhonghao/article.html`

纯静态 HTML：无外部 CDN、无脚本、单文件可直接双击打开。

### 3.9 `gongzhonghao/header-prompt.md`

13 字段，`platform` 填 `gongzhonghao`，`params.aspect_ratio` 填 `"16:9"`。

### 3.10 `gongzhonghao/publish.md`

人工发布清单（标题 / 摘要 / 正文来源 `article.html` / 头图 / 发布时间）。

---

## 4. 缺件判定（`--check`）

每个已选平台目录必须含其 3 个文件，且：

| 检查项 | 判据 |
|---|---|
| 平台目录存在 | 是 |
| 3 个文件齐全 | 是 |
| `<video>/mpt.json` 合法 JSON | 是 |
| `<video>/mpt.json` 键名全在契约表内 | 是 |
| `<video>/publish.sh` 含 `cli publish` | 是 |
| `<video>/script.md` 含「量化评分卡」 | 是 |
| `xiaohongshu/publish.md` 含「无法通过」或「需人工」 | 是 |
| `README.md` 正文 ≤5 行 | 是 |

任一项不满足 → `--check` 退出码 1 并列出缺项。

---

## 5. 反模式

| 反模式 | 后果 |
|---|---|
| 目录里出现 `06-schedule.md` / `07-ledger.md` | 违反本 CHG 核心目标 |
| `README.md` 写成战略分析 | 又变回过程文档 |
| `mpt.json` 自造字段名 | MPT 直接报错 |
| 给小红书生成 `publish.sh` | 图文发不了，伪命令误导 |
| `-f` 填不存在的路径 | 用户执行必失败 |
| 手工填评分卡数字 | 伪造证据 |

---

*本文件为输出包契约唯一承载点。改目录或最小规格只改这里，并同步 `scripts/pipeline_init.py` 的校验清单。*
