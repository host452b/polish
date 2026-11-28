#!/usr/bin/env python3
"""Unit tests for skills/model-council/scripts/council_runner.py."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys
import unittest


SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "council_runner.py"
SPEC = importlib.util.spec_from_file_location("council_runner", SCRIPT_PATH)
assert SPEC and SPEC.loader
council_runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(council_runner)


class CouncilRunnerTest(unittest.TestCase):
    def test_family_inference_covers_frontier_open_weight_and_fusion_pairings(self) -> None:
        cases = {
            "claude-fable-5.2": "anthropic",
            "opus-5.5": "anthropic",
            "gpt-6.1-sol": "openai",
            "gpt-6.1-terra-high": "openai",
            "gpt-6-luna": "openai",
            "gemini-4-carbon": "google",
            "gemini-4-neon-high": "google",
            "gemini-4-argon-medium": "google",
            "nemotron-3-5-super-high": "nvidia",
            "swe-2": "cognition",
            "deepseek/deepseek-r1": "deepseek",
            "kimi-k3": "moonshot",
            "glm-5.2": "zhipu",
            "qwen3-235b": "alibaba",
            "fusion-gemini-4-neon-high-sidekick-claude-haiku-5-5-medium": "google",
            "fusion-gemini-4-neon-high-sidekick-gpt-6-luna-high": "google",
            "fusion-gpt-6-2-astra-high-sidekick-claude-sonnet-5-5-medium": "openai",
            "fusion-claude-fable-5-2-high-sidekick-swe-2-1-medium": "anthropic",
        }
        for model_id, expected in cases.items():
            with self.subTest(model_id=model_id):
                self.assertEqual(council_runner.infer_model_family(model_id), expected)

        parsed = council_runner.parse_fusion_pairing("fusion-gemini-4-neon-high-sidekick-gpt-6-luna-high")
        self.assertIsNotNone(parsed)
        assert parsed is not None
        self.assertEqual(parsed["lead_family"], "google")
        self.assertEqual(parsed["sidekick_family"], "openai")

    def test_probe_never_leaks_secret_values(self) -> None:
        fake_secret = "sk-SUPERSECRET9876543210abcdef"
        report = council_runner.probe_environment(
            which_fn=lambda name: "/usr/bin/devin" if name == "devin" else None,
            environ={"OPENAI_API_KEY": fake_secret, "ANTHROPIC_API_KEY": fake_secret},
        )
        serialized = repr(report)
        self.assertNotIn(fake_secret, serialized)
        self.assertEqual(report["recommended_tier"], "tier_1_multi_cli_or_api")
        self.assertEqual(report["distinct_vendor_families_detected"], ["anthropic", "openai"])

    def test_dispatch_dry_run_checks_diversity_and_neutrality_warnings(self) -> None:
        brief = {
            "question": "Should we use CRDTs or OT for offline CAD constraint graphs?",
            "track": "judgment",
            "fact_pack": [
                "Max document size: 50,000 parametric constraints",
                "I think CRDTs are clearly the best choice here",
            ],
            "seats": [
                {"seat_id": "a", "cli": "devin", "model": "opus"},
                {"seat_id": "b", "cli": "codex", "model": "gpt-5"},
                {"seat_id": "c", "cli": "devin", "model": "gemini"},
            ],
        }
        out = council_runner.dispatch_council(
            brief,
            dry_run=True,
            which_fn=lambda name: f"/opt/bin/{name}",
        )
        self.assertEqual(out["mode"], "dry_run")
        self.assertEqual(out["family_diversity_ratio"], 1.0)
        self.assertFalse(out["homogeneous_family_warning"])
        self.assertEqual(len(out["fact_pack_neutrality_warnings"]), 1)

    def test_dispatch_rejects_unallowlisted_cli_and_unsafe_model_strings(self) -> None:
        with self.assertRaises(ValueError):
            council_runner.validate_brief(
                {
                    "question": "test",
                    "seats": [
                        {"seat_id": "a", "cli": "bash", "model": "opus"},
                        {"seat_id": "b", "cli": "codex", "model": "gpt-5"},
                    ],
                }
            )
        with self.assertRaises(ValueError):
            council_runner.validate_brief(
                {
                    "question": "test",
                    "seats": [
                        {"seat_id": "a", "cli": "devin", "model": "opus; rm -rf /"},
                        {"seat_id": "b", "cli": "codex", "model": "gpt-5"},
                    ],
                }
            )

    def test_ledger_protects_1_of_n_niche_anchors_and_flags_same_family_echo(self) -> None:
        report = council_runner.evaluate_ledger(
            {
                "execution_tier": "tier_1_multi_cli_or_api",
                "relay_rounds_used": 1,
                "seats": [
                    {"seat_id": "s_opus", "model": "opus-5.5", "status": "ok"},
                    {"seat_id": "s_sonnet", "model": "sonnet-4.6", "status": "ok"},
                    {"seat_id": "s_gpt", "model": "gpt-6.1-sol", "status": "ok"},
                    {"seat_id": "s_gem", "model": "gemini-4-carbon", "status": "timeout"},
                ],
                "claims": [
                    {
                        "claim_id": "C1",
                        "statement": "Cross-family agreement",
                        "supporters": ["s_opus", "s_gpt"],
                        "challengers": [],
                        "specificity": "mechanism",
                        "evidence_status": "unverified_assertion",
                    },
                    {
                        "claim_id": "C2",
                        "statement": "Same-family echo between Opus and Sonnet",
                        "supporters": ["s_opus", "s_sonnet"],
                        "challengers": [],
                        "specificity": "mechanism",
                        "evidence_status": "unverified_assertion",
                    },
                    {
                        "claim_id": "C3",
                        "statement": "Obscure USB-PD BIST carrier mode 2 timing window (tBISTContMode 30..60ms)",
                        "supporters": ["s_gpt"],
                        "challengers": [],
                        "specificity": "exact_anchor",
                        "evidence_status": "unverified_assertion",
                        "relay_seam": "Verify against USB PD R3.1 v1.8 Table 6-67",
                    },
                    {
                        "claim_id": "C4",
                        "statement": "Disputed retry backoff curve",
                        "supporters": ["s_opus"],
                        "challengers": ["s_gpt"],
                        "specificity": "mechanism",
                        "evidence_status": "unverified_assertion",
                    },
                ],
            }
        )
        self.assertTrue(report["invariants_all_passed"])
        self.assertEqual(report["failed_seats"], ["s_gem"])
        by_id = {c["claim_id"]: c for c in report["claims"]}
        self.assertEqual(by_id["C1"]["bucket"], "CONVERGENT_HIGH_TRUST")
        self.assertEqual(by_id["C2"]["bucket"], "HOMOGENEOUS_ECHO_WARNING")
        self.assertEqual(by_id["C3"]["bucket"], "UNIQUE_1_OF_N_RELAY_CANDIDATE")
        self.assertTrue(by_id["C3"]["protect_from_majority_vote"])
        self.assertTrue(by_id["C3"]["requires_relay_or_probe"])
        self.assertEqual(by_id["C4"]["bucket"], "DISPUTED_FAULT_LINE")

        md = council_runner.format_ledger_markdown(report)
        self.assertIn("PROTECT_1_OF_N", md)
        self.assertIn("UNIQUE_1_OF_N_RELAY_CANDIDATE", md)

    def test_ledger_prevents_fake_consensus_in_tier3_single_model_fallback(self) -> None:
        report = council_runner.evaluate_ledger(
            {
                "execution_tier": "tier_3_single_model_counterfactual",
                "relay_rounds_used": 0,
                "seats": [
                    {"seat_id": "p1", "model": "gemini-4-carbon", "status": "ok"},
                    {"seat_id": "p2", "model": "gemini-4-carbon", "status": "ok"},
                ],
                "claims": [
                    {
                        "claim_id": "C1",
                        "statement": "Both lenses agreed",
                        "supporters": ["p1", "p2"],
                        "challengers": [],
                        "specificity": "mechanism",
                        "evidence_status": "unverified_assertion",
                    }
                ],
            }
        )
        self.assertFalse(report["multi_family_consensus_eligible"])
        self.assertEqual(report["claims"][0]["bucket"], "SINGLE_FAMILY_CONVERGENCE")
        self.assertTrue(report["invariants_all_passed"])

    def test_ledger_flags_excess_relay_rounds_stop_loss(self) -> None:
        report = council_runner.evaluate_ledger(
            {
                "execution_tier": "tier_1_multi_cli_or_api",
                "relay_rounds_used": 2,
                "seats": [
                    {"seat_id": "s1", "model": "opus", "status": "ok"},
                    {"seat_id": "s2", "model": "gpt-5", "status": "ok"},
                ],
                "claims": [],
            }
        )
        self.assertFalse(report["invariants"]["relay_stop_loss_respected"])
        self.assertFalse(report["invariants_all_passed"])

    def test_cli_selftest_and_probe_exit_zero(self) -> None:
        res_self = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "selftest"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(res_self.returncode, 0, res_self.stderr)
        self.assertIn("selftest passed", res_self.stdout)

        res_probe = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), "probe"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(res_probe.returncode, 0, res_probe.stderr)
        self.assertIn("recommended_tier", res_probe.stdout)


if __name__ == "__main__":
    unittest.main()
