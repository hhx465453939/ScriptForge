#!/usr/bin/env python3
"""genre_probe.py —— 形态判定 CLI（CHG-A G1 验收工具）。

用法：
    python scripts/genre_probe.py --file samples/graphic.txt
    python scripts/genre_probe.py --text "……"
    python scripts/genre_probe.py --file x.txt --json

输出：形态 + 置信度 + 判定依据 + 关键量化读数。
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from viralmath.features import extract, detect_genre  # noqa: E402


# ---------------------------------------------------------------- W4 日志 sink
def _setup_log() -> str:
    """日志自行写入脚本目录（不依赖宿主重定向），便于事后复核现场。"""
    import logging
    log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "genre_probe.log")
    logging.basicConfig(
        filename=log_path, level=logging.INFO, filemode="a", force=True,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    return log_path


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="内容形态判定（video / graphic / text）")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--file", help="内容文件路径（UTF-8）")
    src.add_argument("--text", help="直接传入内容文本")
    p.add_argument("--json", action="store_true", help="输出 JSON")
    args = p.parse_args(argv)

    log_path = _setup_log()
    import logging

    if args.file:
        if not os.path.exists(args.file):
            print(f"错误：文件不存在 {args.file}", file=sys.stderr)
            return 2
        with open(args.file, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        text = args.text

    det = detect_genre(text)
    fs = extract(text)
    payload = {
        **det,
        "n_chars": fs.n_chars,
        "n_sentences": len(fs.sentences),
        "n_paragraphs": fs.para_count,
        "avg_sent_len": round(fs.avg_sent_len, 2),
        "title": fs.title,
        "title_len": fs.title_len,
        "title_formula": fs.title_formula,
        "emoji_count": fs.emoji_count,
        "tag_count": fs.tag_count,
        "heading_count": fs.heading_count,
        "median_lines_per_para": round(fs.median_lines_per_para, 2),
        "claim_count": fs.claim_count,
        "evidence_ratio": round(fs.evidence_ratio, 4),
        "golden_sentence_per_kchar": round(fs.golden_sentence_per_kchar, 4),
        "exclaim_count": fs.exclaim_count,
        "second_person_count": fs.second_person_count,
        "first3_chars": fs.first3_chars,
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"形态: {payload['genre']}    置信度: {payload['confidence']}")
        print(f"依据: {payload['reason']}")
        print(f"规模: {payload['n_chars']} 字 / {payload['n_sentences']} 句 / {payload['n_paragraphs']} 段"
              f" / 平均句长 {payload['avg_sent_len']} 字")
        if payload["title"]:
            print(f"标题: {payload['title']}（{payload['title_len']} 字，公式={payload['title_formula']}）")
        print(f"量化: emoji {payload['emoji_count']} / 标签 {payload['tag_count']}"
              f" / 小标题 {payload['heading_count']} / 论点句 {payload['claim_count']}"
              f" / 证据比 {payload['evidence_ratio']}"
              f" / 金句密度 {payload['golden_sentence_per_kchar']}/千字")
        print(f"口播读数: 前3句字数 {payload['first3_chars']} / 感叹号 {payload['exclaim_count']}"
              f" / 第二人称 {payload['second_person_count']}")

    logging.info(
        "genre_probe argv=%s => genre=%s conf=%s reason=%s chars=%d sents=%d paras=%d "
        "title_len=%d emoji=%d tags=%d headings=%d claims=%d evidence_ratio=%.4f golden=%.4f",
        sys.argv[1:], payload["genre"], payload["confidence"], payload["reason"],
        payload["n_chars"], payload["n_sentences"], payload["n_paragraphs"],
        payload["title_len"], payload["emoji_count"], payload["tag_count"],
        payload["heading_count"], payload["claim_count"], payload["evidence_ratio"],
        payload["golden_sentence_per_kchar"],
    )
    logging.shutdown()
    print(f"[日志] {log_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
