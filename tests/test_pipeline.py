#!/usr/bin/env python3
"""pipeline_init 单测：守住「输出物形态」与「MPT 契约合规」。

为什么必须有（不是形式主义）：
    B 入口曾被做成 campaign 模式（10 文件物料包），把注意力从文案稀释到过程文档。
    本测试把三条不可退让的性质锁死，防止后续改动再滑回去：
      1. 每个平台只产出 3 类文件（文案 / 参数 / 发布指令）
      2. mpt.json 键名只能来自下游契约，禁用字段必须被拦
      3. 图文/长文平台不得生成伪 publish.sh（能力边界如实）
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_ROOT, "scripts"))

import pipeline_init as P  # noqa: E402


class TestFiles(unittest.TestCase):
    def test_video_three(self):
        for name in ("douyin", "kuaishou", "shipinhao",
                     "bilibili", "toutiao", "baijiahao"):
            self.assertEqual(set(P.files_for(name)),
                             {"script.md", "mpt.json", "publish.sh"}, name)

    def test_graphic_no_sh(self):
        files = P.files_for("xiaohongshu")
        self.assertEqual(set(files), {"note.md", "cover-prompt.md", "publish.md"})

    def test_text_no_sh(self):
        files = P.files_for("gongzhonghao")
        self.assertEqual(set(files), {"article.html", "header-prompt.md", "publish.md"})

    def test_manual_note(self):
        for name in ("xiaohongshu", "gongzhonghao"):
            self.assertIn("人工", P.files_for(name)["publish.md"], name)


class TestMpt(unittest.TestCase):
    def test_keys_allowed(self):
        data = json.loads(P.tpl_mpt("douyin", "9:16"))
        extra = sorted(set(data) - P.MPT_ALLOWED)
        self.assertEqual(extra, [], f"契约外字段: {extra}")

    def test_no_forbidden(self):
        data = json.loads(P.tpl_mpt("douyin", "9:16"))
        self.assertEqual(sorted(set(data) & P.MPT_FORBIDDEN), [])

    def test_aspect_enum(self):
        # 实测坑：docstring 里是中文显示串，不是可投喂枚举值
        self.assertEqual(json.loads(P.tpl_mpt("douyin", "9:16"))["video_aspect"], "9:16")
        self.assertEqual(json.loads(P.tpl_mpt("bilibili", "16:9"))["video_aspect"], "16:9")

    def test_fore_color(self):
        data = json.loads(P.tpl_mpt("douyin", "9:16"))
        self.assertIn("text_fore_color", data)
        self.assertNotIn("text_color", data)


class TestSh(unittest.TestCase):
    def test_required_args(self):
        sh = P.tpl_publish_sh("douyin", "dy")
        for token in ("matrixmedia cli publish", "-p dy", "--phone", "-f", "-t"):
            self.assertIn(token, sh)

    def test_placeholder(self):
        self.assertIn("待填", P.tpl_publish_sh("douyin", "dy"))


class TestCheck(unittest.TestCase):
    def _build(self, plats):
        root = tempfile.mkdtemp(prefix="pl_t_")
        self.assertEqual(P.main(["--slug", "t", "--platforms",
                                 ",".join(plats), "--root", root]), 0)
        return os.path.join(root, os.listdir(root)[0])

    def test_fresh_ok(self):
        plats = ["douyin", "xiaohongshu"]
        self.assertEqual(P.check_package(self._build(plats), plats), [])

    def test_missing_file(self):
        pkg = self._build(["douyin"])
        os.remove(os.path.join(pkg, "douyin", "mpt.json"))
        probs = P.check_package(pkg, ["douyin"])
        self.assertTrue(any("mpt.json" in x for x in probs), probs)

    def test_missing_dir(self):
        pkg = self._build(["douyin"])
        probs = P.check_package(pkg, ["douyin", "xiaohongshu"])
        self.assertTrue(any("xiaohongshu" in x for x in probs), probs)

    def test_forbidden_key(self):
        pkg = self._build(["douyin"])
        path = os.path.join(pkg, "douyin", "mpt.json")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        data["video_materials"] = []
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(data, f, ensure_ascii=False)
        probs = P.check_package(pkg, ["douyin"])
        self.assertTrue(any("禁用" in x for x in probs), probs)

    def test_invented_key(self):
        # 自造字段名（如 aspect_ratio）必须被拦
        pkg = self._build(["douyin"])
        path = os.path.join(pkg, "douyin", "mpt.json")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        data["aspect_ratio"] = "9:16"
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(data, f, ensure_ascii=False)
        probs = P.check_package(pkg, ["douyin"])
        self.assertTrue(any("契约外字段" in x for x in probs), probs)

    def test_readme_long(self):
        pkg = self._build(["douyin"])
        path = os.path.join(pkg, "README.md")
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write("# t\n")
            for i in range(10):
                f.write(f"line {i}\n")
        probs = P.check_package(pkg, ["douyin"])
        self.assertTrue(any("README" in x for x in probs), probs)

    def test_broken_sh(self):
        pkg = self._build(["douyin"])
        path = os.path.join(pkg, "douyin", "publish.sh")
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write("echo hello\n")
        probs = P.check_package(pkg, ["douyin"])
        self.assertTrue(any("publish.sh" in x for x in probs), probs)


class TestCli(unittest.TestCase):
    def test_bad_platform(self):
        self.assertEqual(P.main(["--slug", "x", "--platforms", "nope"]), 2)

    def test_no_slug(self):
        self.assertEqual(P.main(["--platforms", "douyin"]), 2)

    def test_dry_run(self):
        root = tempfile.mkdtemp(prefix="pl_d_")
        self.assertEqual(P.main(["--slug", "d", "--platforms", "douyin",
                                 "--root", root, "--dry-run"]), 0)
        self.assertEqual(os.listdir(root), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
