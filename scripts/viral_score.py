#!/usr/bin/env python3
"""viral_score.py —— 爆款量化评估引擎 CLI。

用法：
    python scripts/viral_score.py --file samples/video.txt
    python scripts/viral_score.py --file samples/graphic.txt --json
    python scripts/viral_score.py --text "你的文案……" --genre graphic
    python scripts/viral_score.py --file x.txt --boot 0        # 关闭置信区间（更快）

输出：7 维分 + 综合分 + 95% CI + 优势/短板 + 权重来源 + feature trace。
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from viralmath.console import setup_streams  # noqa: E402
from viralmath.engine import score  # noqa: E402


# ---------------------------------------------------------------- W4 日志 sink
def _setup_log() -> str:
    """日志自行写入脚本目录（不依赖宿主重定向），便于事后复核现场。"""
    import logging
    log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "viral_score.log")
    logging.basicConfig(
        filename=log_path, level=logging.INFO, filemode="a", force=True,
        encoding="utf-8",
        format="%(asctime)s %(levelname)s %(message)s",
    )
    return log_path


def _log_run(args, result: dict, text: str) -> None:
    import logging
    logging.info(
        "viral_score argv=%s chars=%d genre=%s(conf=%s) score=%.2f band=%s CI=[%.2f,%.2f](%s,B=%d) "
        "ahp_cr=%.6f dims=%s notes=%d calibration=%s",
        sys.argv[1:], result["n_chars"], result["genre"], result["genre_confidence"],
        result["score100"], result["band"], result["ci"]["lo"], result["ci"]["hi"],
        result["ci"]["method"], result["ci"]["n_boot"], result["weights"]["ahp_cr"],
        result["dimensions"], len(result["reliability_notes"]), result["calibration_status"],
    )


def _fmt_table(result: dict) -> str:
    L = []
    ap = L.append
    ap(f"# 爆款量化评估 · {result['genre_label']}（形态判定置信度：{result['genre_confidence']}）")
    ap("")
    ap(f"- 判定依据：{result['genre_reason']}")
    ap(f"- 规模：{result['n_chars']} 字 / {result['n_sentences']} 句 / {result['n_paragraphs']} 段")
    ap("")
    ap("## 一、综合分")
    ap("")
    ci = result["ci"]
    if ci["method"] == "degenerate":
        ap(f"**{result['score100']} / 100　分区 {result['band']}**（未计算置信区间）")
    else:
        ap(f"**{result['score100']} / 100　分区 {result['band']}**"
           f"　95% CI [{ci['lo']}, {ci['hi']}]（{ci['method']}, B={ci['n_boot']}）")
    ap("")
    ap("## 二、七维得分")
    ap("")
    ap("| 维度 | 分数 | 区间 | 说明 |")
    ap("|---|---|---|---|")
    for key, label in result["dimension_labels"].items():
        v = result["dimensions"][key]
        c = result.get("dimension_ci", {}).get(key)
        ci_txt = f"[{c['lo']}, {c['hi']}]" if c else "—"
        ap(f"| {label} `{key}` | {v:.3f} | {ci_txt} | — |")
    ap("")
    ap("## 三、优势 / 短板")
    ap("")
    ap("优势：")
    for s in result["strengths"]:
        ap(f"- {s['label']}（{s['score']:.3f}）")
    ap("")
    ap("短板：")
    for s in result["weaknesses"]:
        ap(f"- {s['label']}（{s['score']:.3f}）")
    ap("")
    ap(f"该形态最该补的维度：{' / '.join(result['priority_dimensions_for_genre'])}")
    ap("")
    ap("## 四、权重来源（可审计）")
    ap("")
    w = result["weights"]
    ap(f"- AHP 一致性比率 CR = {w['ahp_cr']}（< 0.1 才可用）")
    ap(f"- 组合赋权 alpha（主观占比）= {w['alpha']}")
    ap("")
    ap("| 维度 | AHP 主观 | 熵权客观 | 组合 |")
    ap("|---|---|---|---|")
    for i, key in enumerate(result["dimensions"].keys()):
        ap(f"| `{key}` | {w['ahp'][i]} | {w['entropy'][i]} | {w['combined'][i]} |")
    ap("")
    ap("## 五、可回溯特征（feature trace）")
    ap("")
    ap("```json")
    ap(json.dumps(result["feature_trace"], ensure_ascii=False, indent=2, sort_keys=True))
    ap("```")
    ap("")
    if result["reliability_notes"]:
        ap("## 六、可靠性提示")
        ap("")
        for n in result["reliability_notes"]:
            ap(f"- {n}")
        ap("")
    ap("## 免责")
    ap("")
    ap(result["disclaimer"])
    ap("")
    ap(f"校准状态：`{result['calibration_status']}`")
    return "\n".join(L)


def main(argv: list[str] | None = None) -> int:
    setup_streams()
    p = argparse.ArgumentParser(description="爆款量化评估引擎")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--file", help="内容文件路径（UTF-8）")
    src.add_argument("--text", help="直接传入内容文本")
    p.add_argument("--genre", default="auto", choices=["auto", "video", "graphic", "text"],
                   help="形态：auto 自动判定（默认）")
    p.add_argument("--seed", type=int, default=20260101, help="Bootstrap 随机种子（默认 20260101）")
    p.add_argument("--boot", type=int, default=400, help="Bootstrap 次数，0 关闭（默认 400）")
    p.add_argument("--json", action="store_true", help="输出 JSON 而非 Markdown")
    args = p.parse_args(argv)

    log_path = _setup_log()
    import logging
    logging.info("START viral_score", extra=None)

    if args.file:
        if not os.path.exists(args.file):
            print(f"错误：文件不存在 {args.file}", file=sys.stderr)
            return 2
        with open(args.file, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        text = args.text

    if not text or not text.strip():
        print("错误：内容为空", file=sys.stderr)
        return 2

    result = score(text, genre=args.genre, seed=args.seed,
                   n_boot=args.boot, with_ci=args.boot > 0)
    _log_run(args, result, text)
    logging.shutdown()

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(_fmt_table(result))
    print(f"\n[日志] {log_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
