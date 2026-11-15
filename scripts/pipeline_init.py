#!/usr/bin/env python3
"""pipeline_init.py — 生成 / 校验 pipeline 输出包。

替代 campaign_init.py（后者的 10 文件物料包是团队协作产物，会稀释注意力）。

用法
    python scripts/pipeline_init.py --slug demo --platforms douyin,xiaohongshu
    python scripts/pipeline_init.py --slug demo --platforms douyin --dry-run
    python scripts/pipeline_init.py --check output/demo_20261115

纪律
    1. 只生成骨架 + 待填标记（TBD / 待填），绝不写假数据
    2. mpt.json 键名只能来自 references/downstream-contracts.md 的契约表
    3. 小红书/公众号不生成伪 publish.sh（图文与长文无法用 CLI 分发）
    4. -f 视频路径未生成时用占位符，不填假路径
    5. --check 校验缺件与契约合规
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from viralmath.console import setup_streams  # noqa: E402

# 平台 -> (目录, CLI 码, 画幅, 类型)
PLATFORMS: dict[str, tuple[str, str, str, str]] = {
    "douyin": ("douyin", "dy", "9:16", "video"),
    "kuaishou": ("kuaishou", "ks", "9:16", "video"),
    "shipinhao": ("shipinhao", "sph", "9:16", "video"),
    "bilibili": ("bilibili", "blbl", "16:9", "video"),
    "toutiao": ("toutiao", "tt", "16:9", "video"),
    "baijiahao": ("baijiahao", "bjh", "16:9", "video"),
    "xiaohongshu": ("xiaohongshu", "xhs", "9:16", "graphic"),
    "gongzhonghao": ("gongzhonghao", "", "", "text"),
}

# MPT 允许写入的字段（契约见 downstream-contracts.md §1.1）
MPT_ALLOWED = {
    "video_subject", "video_script", "video_terms", "video_aspect",
    "video_clip_duration", "video_source", "voice_rate", "voice_volume",
    "bgm_type", "bgm_volume", "subtitle_enabled", "subtitle_position",
    "subtitle_display_mode", "subtitle_animation", "font_size",
    "text_fore_color", "stroke_color", "stroke_width",
    "paragraph_number", "video_count",
}
MPT_FORBIDDEN = {"video_materials", "custom_audio_file", "bgm_file",
                 "video_music_prompt", "sonilo_bgm_prompt"}


def tpl_readme(slug: str, platforms: list) -> str:
    lines = [
        f"# {slug} · {date.today().isoformat()}",
        "",
        "目标：<TBD 平台> 的 <TBD 主指标>",
        "定位：<TBD 一句话差异点>",
        "选题：<TBD 条1>（理由）/ <TBD 条2>（理由）",
        f"下游：{', '.join(platforms)}",
        "",
        "> 正文不得超过 5 行——超过就说明写成了过程文档。",
        "",
    ]
    return "\n".join(lines)


def tpl_script(platform: str) -> str:
    return f"""---
platform: {platform}
genre: video
model: TBD
---

## 文案全文

TBD（可直接念的完整口播）

## 量化评分卡

> 必须来自 `python scripts/viral_score.py --file <稿> --json`，不许手写数字。

| 综合分 | 分区 | 95% CI |
|---|---|---|
| TBD | TBD | TBD |

| 维度 | 分数 |
|---|---|
| 钩子力 | TBD |
| 信息密度 | TBD |
| 节奏冲击 | TBD |
| 情绪驱动 | TBD |
| 说服转化 | TBD |
| 差异化 | TBD |
| 可复制性 | TBD |

短板：TBD

## 迭代记录

| 轮次 | 改动 | 综合分 | 变化 |
|---|---|---|---|
| 1 | TBD | TBD | TBD |
"""


def tpl_mpt(platform: str, aspect: str) -> str:
    payload = {
        "video_subject": "TBD（标题，30 字以内）",
        "video_script": "TBD（与 script.md 正文逐字一致）",
        "video_terms": "TBD（3-6 个素材检索词，空格分隔）",
        "video_aspect": aspect,
        "video_clip_duration": 5,
        "video_source": "pexels",
        "voice_rate": 1.1,
        "voice_volume": 1.0,
        "bgm_type": "random",
        "bgm_volume": 0.15,
        "subtitle_enabled": True,
        "subtitle_position": "bottom",
        "font_size": 60,
        "text_fore_color": "#FFFFFF",
        "stroke_color": "#000000",
        "stroke_width": 1.5,
        "paragraph_number": 4,
        "video_count": 1,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def tpl_publish_sh(platform: str, code: str) -> str:
    return f"""#!/usr/bin/env bash
# 平台: {platform}({code})  生成于 {date.today().isoformat()}
# 前置：先用同目录 mpt.json 在 MPT 生成视频，再把 VIDEO 改成真实绝对路径
set -euo pipefail

VIDEO="<待填：MPT 输出视频的绝对路径>"
PHONE="<待填：发布账号手机号>"

matrixmedia cli publish \\
  -p {code} \\
  --phone "$PHONE" \\
  -f "$VIDEO" \\
  -t "<TBD 标题>" \\
  --description "<TBD 简介>" \\
  --tags "#标签1 #标签2" \\
  --publish-at "YYYY-MM-DD HH:mm:ss"
"""


def tpl_note() -> str:
    return """---
platform: xiaohongshu
genre: graphic
model: TBD
---

## 标题

TBD（12-18 字，套标题公式）

## 正文

TBD（分段，1-3 行一段，emoji 作分段锚点）

## 标签

#TBD1 #TBD2 #TBD3 #TBD4

## 量化评分卡

> 必须来自 `python scripts/viral_score.py --json`。

| 综合分 | 分区 | 95% CI |
|---|---|---|
| TBD | TBD | TBD |

短板：TBD
"""


def tpl_prompt(platform: str, aspect: str, usage: str) -> str:
    return f"""# 文生图提示词 · {usage}

> 13 字段冻结，见 `assets/prompt-spec.md`。每条一个 yaml 代码块。

```yaml
id: img-01
subject: TBD（画面主体，具体到可拍）
scene: TBD（环境与背景）
composition: TBD（构图，必须含留白说明）
lighting: TBD
style: TBD
palette: TBD
lens: TBD
negative: 无文字水印，无变形，无夸张滤镜
platform: {platform}
model: 通用图像模型 / UNKNOWN
params: {{aspect_ratio: "{aspect}", seed: 0}}
usage: {usage}
```
"""


def tpl_publish_manual(platform: str, why: str) -> str:
    return f"""# {platform} 发布清单（人工）

⚠️ {why}

| 步骤 | 内容 |
|---|---|
| 1 | 按提示词生成图片（见同目录 prompt 文件） |
| 2 | 打开平台创作入口 |
| 3 | 粘贴标题（见同目录文案文件） |
| 4 | 粘贴正文 / 上传长文 |
| 5 | 粘贴标签 |
| 6 | 选择发布时间 |
"""


def tpl_article() -> str:
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TBD 标题</title>
<style>
body{max-width:720px;margin:2rem auto;padding:0 1rem;font:16px/1.8 -apple-system,"PingFang SC",sans-serif;color:#1a1a1a}
h2{margin-top:2rem;font-size:1.25rem}
p{margin:.8rem 0}
</style>
</head>
<body>
<h1>TBD 标题</h1>
<h2>TBD 小标题一</h2>
<p>TBD 正文段落。</p>
<h2>TBD 小标题二</h2>
<p>TBD 正文段落。</p>
</body>
</html>
"""


def files_for(platform: str) -> dict:
    d, code, aspect, kind = PLATFORMS[platform]
    if kind == "video":
        return {
            "script.md": tpl_script(platform),
            "mpt.json": tpl_mpt(platform, aspect),
            "publish.sh": tpl_publish_sh(platform, code),
        }
    if kind == "graphic":
        return {
            "note.md": tpl_note(),
            "cover-prompt.md": tpl_prompt("xiaohongshu", "3:4", "笔记封面"),
            "publish.md": tpl_publish_manual(
                "小红书", "图文笔记**无法**通过 MatrixMedia CLI 分发（cli publish 只发本地视频）。"),
        }
    return {
        "article.html": tpl_article(),
        "header-prompt.md": tpl_prompt("gongzhonghao", "16:9", "文章头图"),
        "publish.md": tpl_publish_manual("公众号", "公众号长文无 CLI 通道，必须人工发布。"),
    }


def check_package(pkg: str, platforms: list) -> list:
    problems = []
    readme = os.path.join(pkg, "README.md")
    if not os.path.isfile(readme):
        problems.append("README.md 缺失")
    else:
        with open(readme, encoding="utf-8") as f:
            body = [ln for ln in f.read().splitlines() if ln.strip() and not ln.startswith("#")]
        if len(body) > 6:
            problems.append(f"README.md 正文 {len(body)} 行，超过 5 行上限")

    for p in platforms:
        d, code, aspect, kind = PLATFORMS[p]
        pdir = os.path.join(pkg, d)
        if not os.path.isdir(pdir):
            problems.append(f"{d}/ 目录缺失")
            continue
        for name in files_for(p):
            if not os.path.isfile(os.path.join(pdir, name)):
                problems.append(f"{d}/{name} 缺失")
        if kind == "video":
            mp = os.path.join(pdir, "mpt.json")
            if os.path.isfile(mp):
                try:
                    with open(mp, encoding="utf-8") as f:
                        data = json.load(f)
                except Exception as e:
                    problems.append(f"{d}/mpt.json 不是合法 JSON：{e}")
                    data = None
                if isinstance(data, dict):
                    bad = [k for k in data if k not in MPT_ALLOWED]
                    if bad:
                        problems.append(f"{d}/mpt.json 含契约外字段：{bad}")
                    forb = [k for k in data if k in MPT_FORBIDDEN]
                    if forb:
                        problems.append(f"{d}/mpt.json 含禁用字段：{forb}")
            sh = os.path.join(pdir, "publish.sh")
            if os.path.isfile(sh):
                with open(sh, encoding="utf-8") as f:
                    txt = f.read()
                if "matrixmedia cli publish" not in txt:
                    problems.append(f"{d}/publish.sh 缺 matrixmedia cli publish")
        if kind in ("graphic", "text"):
            pm = os.path.join(pdir, "publish.md")
            if os.path.isfile(pm):
                with open(pm, encoding="utf-8") as f:
                    txt = f.read()
                if "人工" not in txt:
                    problems.append(f"{d}/publish.md 未声明需人工发布")
    return problems


def setup_log() -> str:
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pipeline_init.log")
    logging.basicConfig(filename=path, level=logging.INFO, filemode="a", force=True,
                        format="%(asctime)s %(levelname)s %(message)s")
    return path


def main(argv=None) -> int:
    setup_streams()   # AGENTS.md §5：管道统一 UTF-8，Windows GBK 下防 emoji 崩
    ap = argparse.ArgumentParser(description="pipeline 输出包脚手架 / 校验器")
    ap.add_argument("--slug")
    ap.add_argument("--platforms", default="douyin",
                    help="逗号分隔：" + ",".join(PLATFORMS))
    ap.add_argument("--root", default="output")
    ap.add_argument("--date", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--check", metavar="DIR")
    args = ap.parse_args(argv)

    log_path = setup_log()

    if args.check:
        if not os.path.isdir(args.check):
            print(f"错误：目录不存在 {args.check}", file=sys.stderr)
            return 2
        found = [p for p in PLATFORMS if os.path.isdir(os.path.join(args.check, PLATFORMS[p][0]))]
        if not found:
            print("错误：目录下没有任何已知平台子目录", file=sys.stderr)
            return 2
        problems = check_package(args.check, found)
        logging.info("check dir=%s platforms=%s problems=%d", args.check, found, len(problems))
        if problems:
            print(f"✗ 不合格，{len(problems)} 项：")
            for x in problems:
                print(f"  - {x}")
            print(f"[日志] {log_path}", file=sys.stderr)
            return 1
        print(f"✓ 合格（平台：{', '.join(found)}）")
        print(f"[日志] {log_path}", file=sys.stderr)
        return 0

    if not args.slug:
        print("错误：生成模式需要 --slug", file=sys.stderr)
        return 2
    plats = [p.strip() for p in args.platforms.split(",") if p.strip()]
    bad = [p for p in plats if p not in PLATFORMS]
    if bad:
        print(f"错误：未知平台 {bad}；可选 {list(PLATFORMS)}", file=sys.stderr)
        return 2
    if not plats:
        print("错误：至少选一个平台", file=sys.stderr)
        return 2

    stamp = args.date or date.today().strftime("%Y%m%d")
    pkg = os.path.join(args.root, f"{args.slug}_{stamp}")

    planned: list[tuple[str, str]] = []
    planned.append((os.path.join(pkg, "README.md"), tpl_readme(args.slug, plats)))
    for p in plats:
        d = PLATFORMS[p][0]
        for name, body in files_for(p).items():
            planned.append((os.path.join(pkg, d, name), body))

    if args.dry_run:
        print(f"[dry-run] 将生成 {pkg}/")
        for path, _ in planned:
            print(f"  + {os.path.relpath(path, pkg)}")
        print(f"\n共 {len(planned)} 个文件")
        return 0

    written, skipped = [], []
    for path, body in planned:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if os.path.exists(path) and not args.force:
            skipped.append(path)
            continue
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(body)
        written.append(path)

    logging.info("init slug=%s platforms=%s pkg=%s written=%d skipped=%d",
                 args.slug, plats, pkg, len(written), len(skipped))

    print(f"✓ 已生成：{pkg}")
    for p in written:
        print(f"  + {os.path.relpath(p, pkg)}")
    if skipped:
        print(f"  跳过（已存在，--force 覆盖）：{len(skipped)} 个")
    print()
    print("下一步：")
    print("  1) 写各平台文案（P2），跑 viral_score.py 出评分卡")
    print("  2) 填 mpt.json 的 video_subject / video_script / video_terms")
    print("  3) MPT 生成视频后，把 publish.sh 里 VIDEO 改成真实路径")
    print(f"[日志] {log_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
