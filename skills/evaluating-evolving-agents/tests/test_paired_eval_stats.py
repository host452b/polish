#!/usr/bin/env python3
"""Unit tests for skills/evaluating-evolving-agents/scripts/paired_eval_stats.py."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "paired_eval_stats.py"
SPEC = importlib.util.spec_from_file_location("paired_eval_stats", SCRIPT_PATH)
assert SPEC and SPEC.loader
MOD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MOD
SPEC.loader.exec_module(MOD)


class PairedEvalStatsTests(unittest.TestCase):
    def test_pass_at_and_power_k(self) -> None:
        self.assertAlmostEqual(MOD.pass_at_k_unbiased(5, 3, 2), 0.9, places=4)
        self.assertAlmostEqual(MOD.pass_power_k_unbiased(5, 3, 2), 0.3, places=4)
        self.assertEqual(MOD.pass_power_k_unbiased(5, 3, 5), 0.0)

    def test_paired_compare_detects_hidden_regression(self) -> None:
        a = {"查订单": 1, "换地址": 1, "查配送": 0, "改时段": 0}
        b = {"查订单": 1, "换地址": 0, "查配送": 1, "改时段": 1}
        res = MOD.paired_compare(a, b)
        self.assertAlmostEqual(res["mean_diff_b_minus_a"], 0.25, places=4)
        self.assertEqual(res["binary_breakdown"]["gain_tasks"], ["改时段", "查配送"])
        self.assertEqual(res["binary_breakdown"]["regression_tasks"], ["换地址"])


if __name__ == "__main__":
    unittest.main()
