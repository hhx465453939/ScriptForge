#!/usr/bin/env python3
"""console.py —— 终端输出流编码规范化（部署健壮性）。

实测背景（全新克隆 + Windows 默认 cp936 控制台）：
    * 直接 print() 含 emoji（😭）或上标（R²）的文本 → UnicodeEncodeError，整条命令失败；
    * 管道消费时 GBK 字节被按 UTF-8 解码 → 中文变乱码，agent 读不懂输出。

策略：按「谁在读」分流，而不是硬编一种编码。
    * 交互终端（isatty=True）  → 保留终端自身编码，不可编码字符降级为 '?'（人眼可读、不崩）
    * 管道 / 重定向（isatty=False）→ 统一 UTF-8（agent / CI / tee 能正确解码）
    * 日志文件由各 CLI 的 sink 固定 encoding="utf-8"，不随控制台编码漂移

红线：本模块只碰流编码，不碰任何算法、字段名或输出结构。
"""

from __future__ import annotations

import sys


def _apply(stream, *, encoding: str | None) -> None:
    """尽力重配置一个流；流不支持（已包装/已关闭）时静默跳过。"""
    if not hasattr(stream, "reconfigure"):
        return
    try:
        if encoding is None:
            stream.reconfigure(errors="replace")
        else:
            stream.reconfigure(encoding=encoding, errors="replace")
    except (ValueError, OSError, AttributeError):
        pass


def setup_streams() -> None:
    """在 CLI 的 main() 最开始调用；幂等，重复调用无副作用。"""
    for stream in (sys.stdout, sys.stderr):
        try:
            interactive = bool(stream.isatty())
        except (AttributeError, ValueError):
            interactive = False
        _apply(stream, encoding=None if interactive else "utf-8")
