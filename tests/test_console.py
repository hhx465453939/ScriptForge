#!/usr/bin/env python3
"""tests/test_console.py —— 锁住流编码分流行为（AC-5 的回归保护）。

背景：Windows 默认 cp936 控制台下，CLI 直接 print 含 emoji / 上标（R²）的文本会抛
UnicodeEncodeError；管道场景中文还会变成乱码。console.setup_streams() 按「谁在读」分流：
  * 管道 / 重定向（isatty=False）→ 强制 UTF-8
  * 交互终端（isatty=True）      → 保留本地编码，仅把不可编码字符降级为 '?'

本测试不依赖真实终端：用假流记录 reconfigure 的调用参数。
"""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))

from viralmath import console  # noqa: E402

PIPE_ARGS = {"encoding": "utf-8", "errors": "replace"}
TTY_ARGS = {"errors": "replace"}


class FakeStream:
    """记录 reconfigure 参数的假流。"""

    def __init__(self, is_tty: bool) -> None:
        self._is_tty = is_tty
        self.calls: list[dict] = []

    def isatty(self) -> bool:
        return self._is_tty

    def reconfigure(self, **kwargs) -> None:
        self.calls.append(kwargs)


class PlainStream:
    """没有 reconfigure 的流（已包装 / 已关闭），必须静默跳过而非崩。"""

    def isatty(self) -> bool:
        return False


class TestStreams(unittest.TestCase):
    def _apply(self, out, err) -> None:
        old_out, old_err = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = out, err
        try:
            console.setup_streams()
        finally:
            sys.stdout, sys.stderr = old_out, old_err

    def test_pipe_gets_utf8(self):
        out, err = FakeStream(False), FakeStream(False)
        self._apply(out, err)
        self.assertEqual(out.calls, [PIPE_ARGS])
        self.assertEqual(err.calls, [PIPE_ARGS])

    def test_tty_keeps_local(self):
        out, err = FakeStream(True), FakeStream(True)
        self._apply(out, err)
        self.assertEqual(out.calls, [TTY_ARGS])
        self.assertEqual(err.calls, [TTY_ARGS])

    def test_plain_stream_skipped(self):
        self._apply(PlainStream(), PlainStream())  # 不应抛异常

    def test_probe_raises_as_pipe(self):
        class Boom(FakeStream):
            def isatty(self):
                raise ValueError("closed")

        out = Boom(False)
        self._apply(out, FakeStream(False))
        self.assertEqual(out.calls, [PIPE_ARGS])

    def test_real_streams_safe(self):
        console.setup_streams()  # 幂等，且不得破坏真实 stdout / stderr
        console.setup_streams()
        sys.stdout.write("")
        sys.stderr.write("")


if __name__ == "__main__":
    unittest.main(verbosity=2)
