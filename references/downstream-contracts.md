# 下游工具契约（MPT / MatrixMedia）

> **本文件是下游参数的唯一承载点。** 其他文件只引用，禁止复制第二份。
>
> **铁律：参数不许编。** 下表每个字段都实测自下游源码，标注了来源。
> 不确定的字段写 `UNKNOWN` 并注明怎么查，**不许猜一个看起来合理的名字**——
> 猜错会让工具直接报错，比留空更糟。

---

## 1. MoneyPrinterTurbo（MPT）· 视频生成

**来源**：`MoneyPrinterTurbo/app/models/schema.py` → `class VideoParams`（取证：图谱点名 → `get_code_snippet` → 直读 30–175 行）

### 1.1 本项目写入的字段（冻结）

| 字段 | 类型 / 取值 | 本项目填法 | 说明 |
|---|---|---|---|
| `video_subject` | `str`（**必填**） | 标题（≤30 字） | MPT 用它做主题 |
| `video_script` | `str` | 口播全文 | 与 `script.md` 同源，逐字一致 |
| `video_terms` | `str \| list[str]` | 素材检索词 3–6 个，空格分隔 | 影响画面素材命中率，是最容易被忽略但最影响成片质量的参数 |
| `video_aspect` | `"9:16"` \| `"16:9"` \| `"1:1"` | 见 §1.3 平台映射 | **默认 `9:16`**（`VideoAspect.portrait`） |
| `video_clip_duration` | `int` ≥ 1（默认 5） | 30s 口播取 `5` | 单素材停留秒数 |
| `video_source` | `str`（默认 `pexels`） | `pexels` | 保持默认 |
| `voice_rate` | `float`（默认 1.0） | 干货 `1.1` / 故事 `1.0` | 语速 |
| `voice_volume` | `float`（默认 1.0） | `1.0` | — |
| `bgm_type` | `str`（默认 `random`） | `random` | 配乐类型 |
| `bgm_volume` | `float`（默认 0.2） | `0.15` | 口播为主，压低 BGM |
| `subtitle_enabled` | `bool`（默认 true） | `true` | — |
| `subtitle_position` | `top` \| `bottom` \| `center` \| `two_thirds_bottom` \| `custom` | `bottom` | 竖屏底部 |
| `subtitle_display_mode` | `sentence` \| `word_by_word` | `sentence` | 逐词模式对带货更抓眼，但需实测 |
| `subtitle_animation` | `none` \| `pop_spring` | `none` | — |
| `font_size` | `int`（默认 60） | `60` | 竖屏可读性下限 |
| `text_fore_color` | `str` | `"#FFFFFF"` | ⚠️ 注意字段名是 `text_fore_color`（**不是** `text_color`） |
| `stroke_color` | `str` | `"#000000"` | — |
| `stroke_width` | `float`（默认 1.5） | `1.5` | — |
| `paragraph_number` | `int` 1–10 | 按口播段数 | 用于脚本分段 |
| `video_count` | `int`（默认 1） | `1` | 一次产出条数 |

### 1.2 禁止写入的字段

| 字段 | 为什么禁 |
|---|---|
| `video_materials` | 需 `MaterialInfo` 本地/在线素材清单，本项目无法预知 |
| `custom_audio_file` | 需本地音频路径，视频尚未生成 |
| `bgm_file` | 需本地路径，用 `bgm_type` 代替 |
| `video_music_prompt` / `sonilo_bgm_prompt` | 需配乐供应商配置，交给 MPT 侧 |

### 1.3 平台 → MPT 画幅映射

| 平台 | `video_aspect` |
|---|---|
| 抖音 / 快手 / 视频号 | `"9:16"` |
| B站 / 头条 / 百家号 | `"16:9"` |
| 小红书（若发视频） | `"9:16"` |

### 1.4 一个实测坑

`VideoParams` 的 docstring 示例写的是 `"video_aspect": "横屏 16:9（西瓜视频）"` ——
那是 **WebUI 的中文显示串**，不是可投喂的枚举值。
真正能写进 JSON 的只有 `VideoAspect` 枚举的 `"16:9"` / `"9:16"` / `"1:1"`。
只看 docstring 会写错，必须看枚举定义。

---

## 2. MatrixMedia · 多平台分发

**来源**：`MatrixMedia/CLI_SKILLS.md`（直读）

### 2.1 发布命令（冻结）

```bash
matrixmedia cli publish \
  -p <平台码> \
  --phone <账号手机号> \
  -f "<视频绝对路径>" \
  -t "<标题>" \
  --description "<简介>" \
  --tags "#标签1 #标签2" \
  --publish-at "<YYYY-MM-DD HH:mm:ss>"
```

| 参数 | 取值 | 必填 | 说明 |
|---|---|---|---|
| `-p` / `--platform` | `dy` \| `tt` \| `ks` \| `blbl` \| `bjh` \| `sph` \| `xhs` | ✅ | 平台码 |
| `--phone` | 手机号 | ✅（或用 `--partition`） | 发布账号 |
| `-f` / `--file` | 绝对路径 | ✅ | **本地视频文件** |
| `-t` / `--title` | `str` | ✅ | 标题 |
| `--description` | `str` | ⬜ | 简介 |
| `--short-title` | `str` | ⬜ | **仅视频号** |
| `--tags` | `str` | ⬜ | 空格分隔，前带 `#` |
| `--publish-at` | `"YYYY-MM-DD HH:mm:ss"` | ⬜ | 一次性定时，**不支持循环** |

### 2.2 平台码映射

| 平台 | 码 | 可自动分发视频 |
|---|---|---|
| 抖音 | `dy` | ✅ |
| 头条 | `tt` | ✅ |
| 快手 | `ks` | ✅ |
| B站 | `blbl` | ✅ |
| 百家号 | `bjh` | ✅ |
| 视频号 | `sph` | ✅ |
| 小红书 | `xhs` | ⚠️ 仅**视频**；图文笔记不可 |

### 2.3 其他子命令

| 命令 | 用途 | 限制 |
|---|---|---|
| `matrixmedia cli login -p dy\|sph` | 扫码登录 | 仅抖音/视频号有 CLI 登录；其他平台需先在 GUI 登一次，CLI 复用 session |
| `matrixmedia cli accounts` | 列账号 + 检测 cookie 态 | — |
| `matrixmedia cli history` | 读发布记录，支持平台/手机号/状态/时间过滤 | — |

数据目录：`<Documents>/MatrixMedia/data/`（与 GUI 共用）。

### 2.4 能力边界（必须写进产物）

> `cli publish` 只发**本地视频文件**。
> 小红书图文笔记、公众号长文**无法通过它分发**，必须人工发布。

写 `publish.md` 时必须显式写出这条，**不许生成一条看起来能跑、实际必然失败的伪命令**。

---

## 3. 参数字段的自检方式

任何 AI 在写 `mpt.json` 或 `publish.sh` 前，先自检：

| 检查 | 方法 |
|---|---|
| MPT 字段名对不对 | 对照本文 §1.1 表；表里没有的**不要写** |
| 画幅对不对 | 对照 §1.3 平台映射 |
| 平台码对不对 | 对照 §2.2 |
| 能力是否支持 | 对照 §2.4；图文不要生成 `cli publish` |
| `-f` 路径是否真实 | 视频尚未生成时写 `<待填：MPT 输出视频的绝对路径>` 占位，**不填假路径** |

---

*本文件为下游参数唯一承载点。下游工具升级后，重新实测并更新本文件；改动需同步 `scripts/pipeline_init.py` 的模板。*
