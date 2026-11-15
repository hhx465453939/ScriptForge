#!/usr/bin/env python3
"""viralmath 单元测试（纯标准库 unittest，零依赖）。

运行：python -m unittest discover -s tests -v
覆盖：TRACEABILITY 表中每一行「验收」列的断言。
"""

from __future__ import annotations

import math
import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_ROOT, "scripts"))

from viralmath import align, affect, info, mcdm, rhythm, uncertainty  # noqa: E402
from viralmath import features as F  # noqa: E402
from viralmath import genres as G  # noqa: E402
from viralmath.engine import score  # noqa: E402


# --- 信息论 ---
class TestInfo(unittest.TestCase):
    def test_entropy_uniform(self):
        self.assertAlmostEqual(info.shannon_entropy({"a": 1, "b": 1, "c": 1, "d": 1}), 2.0, places=12)

    def test_entropy_single(self):
        self.assertEqual(info.shannon_entropy({"a": 99}), 0.0)
        self.assertEqual(info.shannon_entropy({}), 0.0)

    def test_entropy_zero_counts(self):
        self.assertAlmostEqual(info.shannon_entropy({"a": 1, "b": 1, "c": 0}), 1.0, places=12)

    def test_norm_entropy(self):
        self.assertAlmostEqual(info.normalize_entropy({"a": 1, "b": 1}), 1.0, places=12)
        self.assertEqual(info.normalize_entropy({"a": 5}), 0.0)

    def test_surprisal_order(self):
        self.assertAlmostEqual(info.surprisal(0.5), 1.0, places=12)
        self.assertGreater(info.surprisal(0.1), info.surprisal(0.5))

    def test_surprisal_zero_finite(self):
        # 陷阱：p=0 时 -log2 p 发散，必须被 eps 截断
        self.assertTrue(math.isfinite(info.surprisal(0.0)))

    def test_js_same_is_zero(self):
        d = {"a": 3, "b": 1}
        self.assertAlmostEqual(info.js_divergence(d, dict(d)), 0.0, places=12)

    def test_js_disjoint_is_one(self):
        # 完全不相交 → 1 bit（JS 上界），而 KL 会发散为无穷
        self.assertAlmostEqual(info.js_divergence({"a": 1}, {"b": 1}), 1.0, places=9)

    def test_js_symmetric(self):
        p, q = {"a": 3, "b": 1}, {"a": 1, "c": 2}
        self.assertAlmostEqual(info.js_divergence(p, q), info.js_divergence(q, p), places=12)

    def test_js_bounded(self):
        for p, q in [({"a": 1}, {"b": 1}), ({"a": 5}, {"a": 5}), ({"a": 1, "b": 2}, {"c": 3})]:
            v = info.js_divergence(p, q)
            self.assertGreaterEqual(v, 0.0)
            self.assertLessEqual(v, 1.0 + 1e-9)

    def test_zipf_alpha(self):
        # 幂律生成：freq 正比 rank^-1 → 拟合 alpha 约 1
        counts = {f"w{i}": round(10000 / (i + 1)) for i in range(60)}
        res = info.zipf_fit(counts)
        self.assertAlmostEqual(res["alpha"], 1.0, delta=0.15)
        self.assertGreater(res["r2"], 0.95)

    def test_zipf_r2_present(self):
        res = info.zipf_fit({"a": 5, "b": 3, "c": 1, "d": 1})
        self.assertTrue(0.0 <= res["r2"] <= 1.0)

    def test_js_floor_cached(self):
        base = {"a": 20, "b": 10, "c": 5, "d": 3, "e": 1}
        f1 = info.js_null_floor(base, 60)
        f2 = info.js_null_floor(base, 60)
        self.assertGreater(f1, 0.0)
        self.assertEqual(f1, f2)  # 缓存命中 → 逐位一致


# --- 节奏 ---
class TestRhythm(unittest.TestCase):
    def test_gini_uniform(self):
        self.assertAlmostEqual(rhythm.gini([1, 1, 1, 1]), 0.0, places=12)

    def test_gini_spread(self):
        self.assertGreater(rhythm.gini([0, 0, 0, 10]), 0.7)

    def test_gini_bounds(self):
        for xs in ([1], [1, 2, 3], [5, 5, 5, 1, 9]):
            self.assertTrue(0.0 <= rhythm.gini(xs) <= 1.0)

    def test_cv_keys(self):
        r = rhythm.cv_robust([10, 10, 10, 10])
        for k in ("mean", "std", "cv", "mad", "cv_robust"):
            self.assertIn(k, r)
        self.assertAlmostEqual(r["cv"], 0.0, places=12)

    def test_cv_robust_vs_classic(self):
        # 稳健性验证：MAD 对少数离群点免疫 → >50% 样本相同时 cv_robust 归零，
        # 而经典 CV 仍很大。二者差值本身就是离群点的诊断信号。
        r = rhythm.cv_robust([10] * 9 + [1000])
        self.assertAlmostEqual(r["cv_robust"], 0.0, places=9)
        self.assertGreater(r["cv"], 1.0)

    def test_cv_robust_positive_when_spread(self):
        # 无重复、真实离散时应 > 0
        self.assertGreater(rhythm.cv_robust([10, 12, 15, 18, 21])["cv_robust"], 0.0)

    def test_acf_len(self):
        self.assertEqual(len(rhythm.acf([1, 2, 3, 4, 5], max_lag=3)), 3)

    def test_period_four(self):
        # 回归保护：脉冲串频谱是等幅谐波，取全局最大峰会锁到 k=12 → 周期误报 2.0
        res = rhythm.dominant_period([1.0, 0.0, 0.0, 0.0] * 6)   # n=24，周期 4
        self.assertTrue(res["reliable"])
        self.assertAlmostEqual(res["period"], 4.0, delta=0.4)
        self.assertEqual(res["peak_bin"], 6)   # 基频 bin = n/period
        self.assertGreater(res["power_ratio"], 0.0)

    def test_period_short_unreliable(self):
        self.assertFalse(rhythm.dominant_period([1, 0, 0, 0, 1, 0, 0, 0])["reliable"])

    def test_markov_deterministic(self):
        res = rhythm.markov_entropy_rate(["a", "b"] * 6)
        self.assertTrue(res["reliable"])
        self.assertAlmostEqual(res["determinism"], 1.0, places=9)

    def test_markov_few_transitions(self):
        self.assertFalse(rhythm.markov_entropy_rate(["a", "b", "c"])["reliable"])

    def test_markov_bounds(self):
        res = rhythm.markov_entropy_rate(["a", "b", "c", "a", "c", "b"] * 3)
        self.assertTrue(0.0 <= res["determinism"] <= 1.0)


# --- 情绪 ---
class TestAffect(unittest.TestCase):
    def test_slope_exact(self):
        r = affect.ols_slope([0, 1, 2, 3, 4])
        self.assertAlmostEqual(r["slope"], 1.0, places=12)
        self.assertAlmostEqual(r["r2"], 1.0, places=9)

    def test_slope_uncertainty(self):
        r = affect.ols_slope([1, 3, 2, 5, 4, 6])
        for k in ("slope", "se", "t", "r2"):
            self.assertIn(k, r)

    def test_slope_flat(self):
        self.assertAlmostEqual(affect.ols_slope([5, 5, 5, 5])["slope"], 0.0, places=12)

    def test_cusum_shift(self):
        res = affect.cusum_changepoints([0.1] * 10 + [1.0] * 10, h=4.0, drift=0.5)
        self.assertGreater(len(res["points"]), 0)
        self.assertGreater(res["max_stat"], 2.0)

    def test_cusum_flat(self):
        self.assertEqual(affect.cusum_changepoints([3.0] * 12)["points"], [])

    def test_arc_rising(self):
        self.assertEqual(affect.emotion_series([-0.8] * 5 + [0.8] * 5)["arc_type"], "上升")


# --- MCDM ---
class TestMCDM(unittest.TestCase):
    def test_ahp_consistent(self):
        m = [[1, 2, 4], [0.5, 1, 2], [0.25, 0.5, 1]]
        r = mcdm.ahp_weights(m)
        self.assertAlmostEqual(r["lambda_max"], 3.0, places=6)
        self.assertLess(r["cr"], 0.01)
        self.assertAlmostEqual(sum(r["weights"]), 1.0, places=9)

    def test_ahp_order(self):
        r = mcdm.ahp_weights([[1, 3], [1 / 3, 1]])
        self.assertGreater(r["weights"][0], r["weights"][1])

    def test_ahp_lam_ge_n(self):
        # 回归保护：修复前幂迭代用和归一化，λmax 被压到约 1，CR 恒为 0（门控失效）
        for prof in G.GENRES.values():
            r = mcdm.ahp_weights(prof.ahp_matrix)
            self.assertGreaterEqual(r["lambda_max"], len(prof.ahp_matrix) - 1e-9)

    def test_ahp_bad_raises(self):
        bad = [[1, 9, 1 / 9], [1 / 9, 1, 9], [9, 1 / 9, 1]]
        with self.assertRaises(mcdm.InconsistentMatrixError):
            mcdm.ahp_weights(bad)

    def test_ahp_bad_inspectable(self):
        bad = [[1, 9, 1 / 9], [1 / 9, 1, 9], [9, 1 / 9, 1]]
        r = mcdm.ahp_weights(bad, raise_on_inconsistent=False)
        self.assertFalse(r["consistent"])
        self.assertGreater(r["cr"], 0.1)

    def test_entropy_equal_cols(self):
        # 每列取值相同 → d_j=0 → 分母为 0 → 必须回退均权，不许除零
        w = mcdm.entropy_weights([[1, 5], [1, 5], [1, 5]])
        self.assertAlmostEqual(w[0], 0.5, places=9)
        self.assertAlmostEqual(w[1], 0.5, places=9)

    def test_entropy_prefers_spread(self):
        w = mcdm.entropy_weights([[1, 0.1], [1, 0.2], [1, 0.9]])
        self.assertGreater(w[1], w[0])

    def test_combine_norm(self):
        w = mcdm.combine_weights([0.7, 0.3], [0.2, 0.8], alpha=0.5)
        self.assertAlmostEqual(sum(w), 1.0, places=9)
        self.assertAlmostEqual(w[0], 0.45, places=9)

    def test_combine_len_mismatch(self):
        with self.assertRaises(ValueError):
            mcdm.combine_weights([0.5, 0.5], [1.0])

    def test_topsis_extremes(self):
        r = mcdm.topsis([[1, 1], [0, 0]], [0.5, 0.5], benefit=[True, True])
        self.assertAlmostEqual(r["scores"][0], 1.0, places=9)
        self.assertAlmostEqual(r["scores"][1], 0.0, places=9)

    def test_topsis_bounded(self):
        r = mcdm.topsis([[3, 1], [1, 3], [2, 2]], [0.5, 0.5], benefit=[True, True])
        for s in r["scores"]:
            self.assertTrue(0.0 <= s <= 1.0)

    def test_topsis_cost_dir(self):
        # 成本型：值越小越好 → 第 2 行应变优
        r = mcdm.topsis([[1, 9], [1, 1]], [0.0, 1.0], benefit=[True, False])
        self.assertGreater(r["scores"][1], r["scores"][0])

    def test_saaty_snap(self):
        self.assertEqual(mcdm.saaty_snap(1.8), 2.0)
        self.assertEqual(mcdm.saaty_snap(0.5), 1 / 2)
        self.assertEqual(mcdm.saaty_snap(100), 9.0)


# --- 不确定度 ---
class TestUncertainty(unittest.TestCase):
    def test_beta_cdf_bounds(self):
        self.assertAlmostEqual(uncertainty.reg_incomplete_beta(2, 3, 0.0), 0.0, places=12)
        self.assertAlmostEqual(uncertainty.reg_incomplete_beta(2, 3, 1.0), 1.0, places=12)
        self.assertAlmostEqual(uncertainty.reg_incomplete_beta(1, 1, 0.5), 0.5, places=9)

    def test_beta_ppf_median(self):
        self.assertAlmostEqual(uncertainty.beta_ppf(0.5, 1, 1), 0.5, places=6)

    def test_beta_interval(self):
        r = uncertainty.beta_interval(5, 10)
        self.assertAlmostEqual(r["mean"], 6 / 12, places=9)
        self.assertLess(r["lo"], r["mean"])
        self.assertGreater(r["hi"], r["mean"])

    def test_beta_never_extreme(self):
        r = uncertainty.beta_interval(0, 5)      # 全失败
        self.assertGreater(r["lo"], 0.0)
        self.assertLess(r["hi"], 1.0)

    def test_boot_brackets_point(self):
        xs = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
        r = uncertainty.bootstrap_ci(xs, lambda s: sum(s) / len(s), n_boot=200, seed=42)
        self.assertLessEqual(r["lo"], r["point"] + 1e-9)
        self.assertGreaterEqual(r["hi"], r["point"] - 1e-9)

    def test_boot_reproducible(self):
        xs = [1.0, 3.0, 2.0, 5.0, 4.0, 6.0, 7.0]
        a = uncertainty.bootstrap_ci(xs, lambda s: sum(s) / len(s), n_boot=150, seed=7)
        b = uncertainty.bootstrap_ci(xs, lambda s: sum(s) / len(s), n_boot=150, seed=7)
        self.assertEqual((a["lo"], a["hi"]), (b["lo"], b["hi"]))

    def test_boot_tiny_sample(self):
        r = uncertainty.bootstrap_ci([1.0, 2.0], lambda s: sum(s) / len(s), n_boot=100)
        self.assertEqual(r["method"], "degenerate")


# --- 对齐 ---
class TestAlign(unittest.TestCase):
    def test_cos_same(self):
        self.assertAlmostEqual(align.cosine([1, 2, 3], [1, 2, 3]), 1.0, places=12)

    def test_cos_ortho(self):
        self.assertAlmostEqual(align.cosine([1, 0], [0, 1]), 0.0, places=12)

    def test_cos_zero(self):
        self.assertEqual(align.cosine([0, 0], [1, 1]), 0.0)

    def test_dtw_same(self):
        self.assertAlmostEqual(align.dtw_distance([0, 1, 2], [0, 1, 2])["normalized"], 0.0, places=12)

    def test_dtw_bounded(self):
        r = align.dtw_distance([0.0, 1.0, 0.0, 1.0], [1.0, 0.0])
        self.assertGreater(r["dist"], 0.0)
        self.assertLessEqual(r["normalized"], 1.0 + 1e-9)

    def test_dtw_len_invariant(self):
        # 陷阱：DTW 距离随路径长度增长 → 归一化后同形状应可比
        a = align.dtw_distance([0, 1, 0, 1, 0, 1], [0, 1])
        b = align.dtw_distance([0, 1] * 12, [0, 1])
        self.assertLess(abs(a["normalized"] - b["normalized"]), 0.35)


# --- 形态档 ---
class TestGenres(unittest.TestCase):
    def test_three_genres(self):
        self.assertEqual(set(G.GENRES), {"video", "graphic", "text"})

    def test_all_cr_ok(self):
        for name, prof in G.GENRES.items():
            r = mcdm.ahp_weights(prof.ahp_matrix)
            self.assertLess(r["cr"], 0.10, f"{name} CR 超限")

    def test_seven_dims(self):
        self.assertEqual(len(G.DIMS), 7)
        for prof in G.GENRES.values():
            self.assertEqual(len(prof.priority), 7)

    def test_band_map(self):
        self.assertEqual(G.band_of(95), "S")
        self.assertEqual(G.band_of(70), "A")
        self.assertEqual(G.band_of(10), "D")

    def test_priority_differs(self):
        self.assertNotEqual(G.GENRES["video"].priority, G.GENRES["text"].priority)


# --- 特征与形态判定 ---
class TestFeatures(unittest.TestCase):
    def _read(self, name: str) -> str:
        with open(os.path.join(_ROOT, "samples", f"{name}.txt"), encoding="utf-8") as f:
            return f.read()

    def test_detect_on_samples(self):
        for name in ("video", "graphic", "text"):
            det = F.detect_genre(self._read(name))
            self.assertEqual(det["genre"], name, f"{name} 判定错: {det}")
            self.assertIn(det["confidence"], ("高", "中", "低"))

    def test_graphic_high_conf(self):
        self.assertEqual(F.detect_genre(self._read("graphic"))["confidence"], "高")

    def test_frozen_fields(self):
        fs = F.extract(self._read("graphic"))
        for f in ("title_len", "emoji_count", "para_count", "tag_count",
                  "median_lines_per_para", "heading_count", "claim_count",
                  "evidence_ratio", "golden_sentence_per_kchar", "first3_chars",
                  "avg_sent_len", "exclaim_count", "second_person_count"):
            self.assertTrue(hasattr(fs, f), f"缺字段 {f}")

    def test_tokenize_bigrams(self):
        toks = F.tokenize("内容创作")
        self.assertIn("内容", toks)
        self.assertIn("创作", toks)

    def test_empty_safe(self):
        fs = F.extract("")
        self.assertEqual(fs.n_chars, 0)
        self.assertEqual(fs.sentences, [])


# --- 端到端 ---
class TestEngine(unittest.TestCase):
    def _read(self, name: str) -> str:
        with open(os.path.join(_ROOT, "samples", f"{name}.txt"), encoding="utf-8") as f:
            return f.read()

    def test_score_contract_keys(self):
        r = score(self._read("video"), n_boot=0)
        for k in ("genre", "dimensions", "weights", "topsis", "score100", "band",
                  "ci", "strengths", "weaknesses", "feature_trace",
                  "reliability_notes", "calibration_status", "disclaimer"):
            self.assertIn(k, r)

    def test_dims_in_range(self):
        for name in ("video", "graphic", "text"):
            r = score(self._read(name), n_boot=0)
            self.assertEqual(len(r["dimensions"]), 7)
            for k, v in r["dimensions"].items():
                self.assertTrue(0.0 <= v <= 1.0, f"{name}.{k} 越界")

    def test_determinism(self):
        import json
        t = self._read("video")
        a = score(t, n_boot=30, seed=123)
        b = score(t, n_boot=30, seed=123)
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))

    def test_ci_brackets(self):
        r = score(self._read("video"), n_boot=60, seed=11)
        self.assertLessEqual(r["ci"]["lo"], r["ci"]["point"] + 1e-9)
        self.assertGreaterEqual(r["ci"]["hi"], r["ci"]["point"] - 1e-9)
        self.assertEqual(r["ci"]["method"], "bca")

    def test_d6_discriminates(self):
        # 回归保护：修复前 D6 对所有输入饱和到 1.0（零信息量）
        vals = [score(self._read(n), n_boot=0)["dimensions"]["distinction"]
                for n in ("video", "graphic", "text")]
        self.assertGreater(max(vals) - min(vals), 0.2, f"差异化无区分度: {vals}")

    def test_cr_below_limit(self):
        self.assertLess(score(self._read("text"), n_boot=0)["weights"]["ahp_cr"], 0.10)

    def test_genre_override(self):
        self.assertEqual(score(self._read("video"), genre="text", n_boot=0)["genre"], "text")

    def test_calibration_flagged(self):
        self.assertEqual(score(self._read("video"), n_boot=0)["calibration_status"],
                         "CALIBRATION_PENDING")

    def test_archetype_match_contract(self):
        r = score(self._read("video"), n_boot=0)["archetype_match"]
        self.assertIn(r["closest"], G.ARCHETYPE_LABELS)
        self.assertGreaterEqual(r["similarity"], 0.0)
        self.assertLessEqual(r["similarity"], 1.0)
        self.assertEqual(len(r["all"]), len(G.ARCHETYPES))
        self.assertIn("euclidean", r["metric"])

    def test_archetype_not_top_when_score_low(self):
        # 回归保护：用余弦时会把 C 区样本判成「最像差」；改距离后不应再出现错位等级
        for name in ("video", "graphic", "text"):
            r = score(self._read(name), n_boot=0)
            if r["score100"] < 50:
                self.assertNotEqual(r["archetype_match"]["closest"], "顶配",
                                    f"{name} 低分却匹配顶配原型")

    def test_profile_fit_contract(self):
        r = score(self._read("graphic"), n_boot=0)["profile_fit"]
        self.assertGreaterEqual(r["cosine"], 0.0)
        self.assertLessEqual(r["cosine"], 1.0)
        self.assertEqual(len(r["priority_dims"]), 2)
        for d in r["priority_dims"]:
            self.assertIn(d, G.DIMS)

    def test_arc_alignment_contract(self):
        r = score(self._read("text"), n_boot=0)["arc_alignment"]
        self.assertGreaterEqual(r["alignment"], 0.0)
        self.assertLessEqual(r["alignment"], 1.0)
        self.assertGreaterEqual(r["dtw_normalized"], 0.0)
        self.assertEqual(r["arc_buckets"], G.ARC_BUCKETS)


if __name__ == "__main__":
    unittest.main(verbosity=2)
