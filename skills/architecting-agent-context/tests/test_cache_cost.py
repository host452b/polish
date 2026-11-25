#!/usr/bin/env python3
"""Unit tests for skills/architecting-agent-context/scripts/estimate_status_bar_cache_cost.py."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "estimate_status_bar_cache_cost.py"
SPEC = importlib.util.spec_from_file_location("cache_cost", SCRIPT_PATH)
assert SPEC and SPEC.loader
MOD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MOD
SPEC.loader.exec_module(MOD)


class CacheCostTests(unittest.TestCase):
    def test_chapter2_worked_example(self) -> None:
        res = MOD.compare_status_strategies(s_tokens=100, r_tokens=1000, n_turns=10, alpha=0.1)
        self.assertEqual(res["replace_extra_equiv_tokens"], 8100.0)
        self.assertEqual(res["append_extra_equiv_tokens"], 450.0)
        self.assertEqual(res["recommended"], "persistent_append")

    def test_tail_only_prefers_replace(self) -> None:
        res = MOD.compare_status_strategies(s_tokens=100, r_tokens=0, n_turns=10, alpha=0.1)
        self.assertEqual(res["replace_extra_equiv_tokens"], 0.0)
        self.assertEqual(res["recommended"], "replace_each_turn")


if __name__ == "__main__":
    unittest.main()
