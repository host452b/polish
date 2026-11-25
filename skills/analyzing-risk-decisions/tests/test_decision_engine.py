import json
import math
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import decision_engine as de


class TestPayoffAndCashflowPrimitives(unittest.TestCase):
    def test_reimbursement_layer_deductible_cap_and_prior_overlap(self):
        self.assertEqual(
            de.reimbursement_payout(10_000, deductible=12_000, rate=0.7, cap=1_000_000),
            0.0,
        )
        self.assertAlmostEqual(
            de.reimbursement_payout(50_000, deductible=12_000, rate=0.7, cap=1_000_000),
            26_600.0,
        )
        self.assertAlmostEqual(
            de.reimbursement_payout(
                50_000,
                deductible=12_000,
                rate=0.7,
                cap=1_000_000,
                prior_compensation=45_000,
            ),
            5_000.0,
        )
        self.assertEqual(
            de.reimbursement_payout(
                50_000,
                deductible=12_000,
                rate=0.7,
                cap=1_000_000,
                prior_compensation=50_000,
            ),
            0.0,
        )
        self.assertAlmostEqual(
            de.reimbursement_payout(2_000_000, deductible=12_000, rate=0.7, cap=1_000_000),
            1_000_000.0,
        )

    def test_forward_cashflow_npv_charges_exit_opportunity_cost_not_sunk_cost(self):
        nominal = de.forward_cashflow_npv(
            future_benefits=[],
            future_costs=[(float(i), 2_415.0) for i in range(1, 27)],
            discount_rate=0.0,
            exit_opportunity_cost=0.0,
        )
        self.assertAlmostEqual(nominal["pv_costs"], 62_790.0)
        self.assertAlmostEqual(nominal["net_present_value"], -62_790.0)

        two_year = de.forward_cashflow_npv(
            future_benefits=[(2.0, 121.0)],
            future_costs=[(1.0, 110.0)],
            discount_rate=0.10,
            exit_opportunity_cost=15.0,
            terminal_value=(2.0, 24.2),
        )
        self.assertAlmostEqual(two_year["pv_benefits"], 100.0)
        self.assertAlmostEqual(two_year["pv_costs"], 100.0)
        self.assertAlmostEqual(two_year["pv_terminal"], 20.0)
        self.assertAlmostEqual(two_year["net_present_value"], 5.0)
        self.assertAlmostEqual(two_year["required_benefit_prob_to_break_even"], (100.0 + 15.0 - 20.0) / 100.0)


class TestCompareAlternatives(unittest.TestCase):
    def test_compare_negative_ev_tail_protection_and_dominance(self):
        problem = {
            "baseline_id": "none",
            "states": [
                {"id": "ok", "prob": 0.997, "provenance": "assumption"},
                {"id": "catastrophe", "prob": 0.003, "provenance": "assumption"},
            ],
            "alternatives": [
                {
                    "id": "none",
                    "upfront_cost": 0.0,
                    "state_residual_losses": {"ok": 0.0, "catastrophe": 200_000.0},
                    "provenance": "fact",
                },
                {
                    "id": "medical_plan",
                    "upfront_cost": 600.0,
                    "state_residual_losses": {"ok": 0.0, "catastrophe": 10_000.0},
                    "provenance": "assumption",
                },
                {
                    "id": "redundant_bundle",
                    "upfront_cost": 668.0,
                    "state_residual_losses": {"ok": 0.0, "catastrophe": 10_000.0},
                    "provenance": "assumption",
                },
            ],
            "preferences": {
                "risk_tolerances": [50_000.0, 200_000.0, 1_000_000.0],
                "budget": 1_000.0,
                "loss_limit": 20_000.0,
                "max_breach_prob": 0.001,
                "tail_alphas": [0.99, 0.999],
            },
        }
        res = de.compare_alternatives(problem)
        self.assertTrue(res["has_unverified_assumptions"])
        self.assertTrue(all(res["invariants"].values()))

        by_id = {row["id"]: row for row in res["alternatives"]}
        none_row = by_id["none"]
        plan_row = by_id["medical_plan"]
        dup_row = by_id["redundant_bundle"]

        self.assertAlmostEqual(none_row["expected_net_loss"], 600.0)
        self.assertAlmostEqual(plan_row["expected_net_loss"], 630.0)
        self.assertAlmostEqual(plan_row["incremental_ev_vs_baseline"], -30.0)
        self.assertAlmostEqual(plan_row["incremental_rtp"], 0.95)

        self.assertAlmostEqual(round(none_row["cara_ce"]["50000"]), 7_455)
        self.assertAlmostEqual(round(plan_row["cara_ce"]["50000"]), 633)
        self.assertAlmostEqual(round(none_row["cara_ce"]["200000"]), 1_028)
        self.assertAlmostEqual(round(plan_row["cara_ce"]["200000"]), 631)

        self.assertEqual(none_row["var"]["0.99"], 0.0)
        self.assertEqual(plan_row["var"]["0.99"], 600.0)
        self.assertAlmostEqual(none_row["es"]["0.99"], 60_000.0)
        self.assertAlmostEqual(plan_row["es"]["0.99"], 3_600.0)
        self.assertAlmostEqual(none_row["es"]["0.999"], 200_000.0)
        self.assertAlmostEqual(plan_row["es"]["0.999"], 10_600.0)

        self.assertAlmostEqual(none_row["breach_prob"], 0.003)
        self.assertFalse(none_row["feasible"])
        self.assertEqual(plan_row["breach_prob"], 0.0)
        self.assertTrue(plan_row["feasible"])

        self.assertIn("medical_plan", dup_row["strictly_dominated_by"])
        self.assertEqual(res["rankings_by_r"]["50000"]["optimal_id"], "medical_plan")


class TestInvertThresholds(unittest.TestCase):
    def test_break_even_probability_and_reservation_price(self):
        # Known-good literal from insurance benchmark: 68 yuan fee, 1000 incremental payout -> 6.8%
        be_acc = de.invert_thresholds(
            {
                "kind": "break_even_probability",
                "cost": 68.0,
                "conditional_payout": 1_000.0,
                "eligibility": 1.0,
            }
        )
        self.assertAlmostEqual(be_acc["risk_neutral_p_star"], 0.068)

        # HHB 50k self-pay after prior 45k paid -> 5000 payout, 129 fee -> 2.58%
        be_hhb_overlap = de.invert_thresholds(
            {
                "kind": "break_even_probability",
                "cost": 129.0,
                "conditional_payout": 5_000.0,
                "eligibility": 1.0,
            }
        )
        self.assertAlmostEqual(be_hhb_overlap["risk_neutral_p_star"], 0.0258)

        # Zero incremental payout -> impossible to break even
        be_zero = de.invert_thresholds(
            {
                "kind": "break_even_probability",
                "cost": 129.0,
                "conditional_payout": 0.0,
            }
        )
        self.assertIsNone(be_zero["risk_neutral_p_star"])

        # CARA break-even probability for P=600, L=200k, C=190k at R=50k:
        # Analytical formula: (exp(600/50000)-1) / ((exp(4)-1) - exp(600/50000)*(exp(0.2)-1))
        expected_p_cara = (math.exp(0.012) - 1.0) / (
            (math.exp(4.0) - 1.0) - math.exp(0.012) * (math.exp(0.2) - 1.0)
        )
        be_cara = de.invert_thresholds(
            {
                "kind": "break_even_probability",
                "cost": 600.0,
                "conditional_payout": 190_000.0,
                "loss_when_event": 200_000.0,
                "eligibility": 1.0,
                "risk_tolerances": [50_000.0],
            }
        )
        self.assertAlmostEqual(be_cara["cara_p_star"]["50000"], expected_p_cara, places=9)

        # Reservation price P*(R) for p=0.003, L=200k -> residual 10k:
        # Risk-neutral P* = 0.003 * 190_000 = 570; at R=50_000, P* = 7454.901... - 33.340... = 7421.56...
        rp = de.invert_thresholds(
            {
                "kind": "reservation_price",
                "states": [
                    {"id": "ok", "prob": 0.997},
                    {"id": "hit", "prob": 0.003},
                ],
                "baseline_residual_losses": {"ok": 0.0, "hit": 200_000.0},
                "candidate_residual_losses": {"ok": 0.0, "hit": 10_000.0},
                "risk_tolerances": [50_000.0],
            }
        )
        self.assertAlmostEqual(rp["risk_neutral_max_cost"], 570.0)
        self.assertAlmostEqual(round(rp["cara_max_cost"]["50000"] - 600.0), 6_822)

    def test_indifference_risk_tolerance_and_budget_tail_frontier(self):
        # Exact analytical root: sure loss c = 100 * ln((1 + e)/2) ties [0, 100] 50/50 at R* = 100.0
        exact_sure = 100.0 * math.log((1.0 + math.e) / 2.0)
        ind = de.invert_thresholds(
            {
                "kind": "indifference_r",
                "states": [
                    {"id": "s0", "prob": 0.5},
                    {"id": "s1", "prob": 0.5},
                ],
                "alt_a": {"id": "sure", "upfront_cost": exact_sure, "state_residual_losses": {"s0": 0.0, "s1": 0.0}},
                "alt_b": {"id": "gamble", "upfront_cost": 0.0, "state_residual_losses": {"s0": 0.0, "s1": 100.0}},
            }
        )
        self.assertEqual(len(ind["roots_r_star"]), 1)
        self.assertAlmostEqual(ind["roots_r_star"][0], 100.0, places=5)
        self.assertEqual(ind["regimes"][0]["preferred_id"], "sure")
        self.assertEqual(ind["regimes"][-1]["preferred_id"], "gamble")

        # Cloud DR / engineering budget-vs-tail frontier
        frontier = de.invert_thresholds(
            {
                "kind": "budget_tail_frontier",
                "states": [
                    {"id": "ok", "prob": 0.98},
                    {"id": "az_down", "prob": 0.018},
                    {"id": "region_down", "prob": 0.002},
                ],
                "alternatives": [
                    {"id": "single_az", "upfront_cost": 0.0, "state_residual_losses": {"ok": 0.0, "az_down": 80_000.0, "region_down": 250_000.0}},
                    {"id": "multi_az", "upfront_cost": 1_200.0, "state_residual_losses": {"ok": 0.0, "az_down": 2_000.0, "region_down": 250_000.0}},
                    {"id": "multi_region", "upfront_cost": 6_000.0, "state_residual_losses": {"ok": 0.0, "az_down": 1_000.0, "region_down": 5_000.0}},
                ],
                "loss_limit": 20_000.0,
                "max_breach_prob": 0.005,
                "budget": 2_000.0,
            }
        )
        # To achieve breach_prob <= 0.005, multi_az (breach_prob = 0.002, cost = 1200) is minimum cost
        self.assertEqual(frontier["min_cost_for_tail_limit"]["id"], "multi_az")
        # Under budget <= 2000, multi_az achieves minimum breach_prob = 0.002
        self.assertEqual(frontier["min_tail_for_budget"]["id"], "multi_az")
        self.assertAlmostEqual(frontier["min_tail_for_budget"]["breach_prob"], 0.002)


class TestCalibrateAndCLI(unittest.TestCase):
    def test_calibrate_bounds_and_inconsistency_detection(self):
        ce_at_100 = 100.0 * math.log((1.0 + math.e) / 2.0)
        ce_at_200 = 200.0 * math.log((1.0 + math.exp(0.5)) / 2.0)

        consistent = de.calibrate_preferences(
            {
                "choices": [
                    {
                        "id": "q1",
                        "sure_loss": ce_at_100,
                        "lottery_losses": [0.0, 100.0],
                        "lottery_probs": [0.5, 0.5],
                        "picked": "lottery",
                    },
                    {
                        "id": "q2",
                        "sure_loss": ce_at_200,
                        "lottery_losses": [0.0, 100.0],
                        "lottery_probs": [0.5, 0.5],
                        "picked": "sure",
                    },
                ],
                "target_loss_scale": 200_000.0,
            }
        )
        self.assertTrue(consistent["consistent"])
        self.assertAlmostEqual(consistent["r_min"], 100.0, places=4)
        self.assertAlmostEqual(consistent["r_max"], 200.0, places=4)
        self.assertEqual(len(consistent["suggested_questions"]), 3)

        contradictory = de.calibrate_preferences(
            {
                "choices": [
                    {
                        "id": "q_high_r",
                        "sure_loss": ce_at_100,
                        "lottery_losses": [0.0, 100.0],
                        "lottery_probs": [0.5, 0.5],
                        "picked": "lottery",
                    },
                    {
                        "id": "q_low_r",
                        "sure_loss": 70.0,
                        "lottery_losses": [0.0, 100.0],
                        "lottery_probs": [0.5, 0.5],
                        "picked": "sure",
                    },
                ]
            }
        )
        self.assertFalse(contradictory["consistent"])
        self.assertIn(["q_high_r", "q_low_r"], contradictory["conflicting_pairs"])

        risk_seeking = de.calibrate_preferences(
            {
                "choices": [
                    {
                        "id": "q_seek",
                        "sure_loss": 45.0,
                        "lottery_losses": [0.0, 100.0],
                        "lottery_probs": [0.5, 0.5],
                        "picked": "lottery",
                    }
                ]
            }
        )
        self.assertFalse(risk_seeking["consistent"])
        self.assertEqual(risk_seeking["choice_bounds"][0]["status"], "no_cara_solution")

    def test_cli_stdin_and_selftest(self):
        script = SCRIPTS_DIR / "decision_engine.py"
        st = subprocess.run(
            [sys.executable, str(script), "selftest"],
            capture_output=True,
            text=True,
            check=True,
        )
        st_json = json.loads(st.stdout)
        self.assertEqual(st_json["status"], "ok")
        self.assertTrue(all(st_json["checks"].values()))

        payload = json.dumps(
            {
                "kind": "break_even_probability",
                "cost": 68.0,
                "conditional_payout": 1_000.0,
            }
        )
        inv = subprocess.run(
            [sys.executable, str(script), "invert", "--input", "-"],
            input=payload,
            capture_output=True,
            text=True,
            check=True,
        )
        inv_json = json.loads(inv.stdout)
        self.assertAlmostEqual(inv_json["risk_neutral_p_star"], 0.068)

    def test_staged_pilot_option_value_and_ev_ranking_without_r(self):
        # Full build: 30% net -60k loss (+60k profit), 70% +40k loss -> EV loss = +10k (worse than do_nothing=0)
        # Staged pilot (before pilot fee): 30% -60k loss, 70% 0 loss -> reservation price vs do_nothing = 18,000
        rp = de.invert_thresholds(
            {
                "kind": "reservation_price",
                "states": [
                    {"id": "viable", "prob": 0.30},
                    {"id": "non_viable", "prob": 0.70},
                ],
                "baseline_residual_losses": {"viable": 0.0, "non_viable": 0.0},
                "candidate_residual_losses": {"viable": -60_000.0, "non_viable": 0.0},
            }
        )
        self.assertAlmostEqual(rp["risk_neutral_max_cost"], 18_000.0)

        cmp_res = de.compare_alternatives(
            {
                "baseline_id": "do_nothing",
                "states": [
                    {"id": "viable", "prob": 0.30, "provenance": "estimate"},
                    {"id": "non_viable", "prob": 0.70, "provenance": "estimate"},
                ],
                "alternatives": [
                    {"id": "do_nothing", "upfront_cost": 0.0, "state_residual_losses": {"viable": 0.0, "non_viable": 0.0}, "provenance": "fact"},
                    {"id": "full_commit", "upfront_cost": 40_000.0, "state_residual_losses": {"viable": -100_000.0, "non_viable": 0.0}, "provenance": "fact"},
                    {"id": "pilot_then_commit", "upfront_cost": 5_000.0, "state_residual_losses": {"viable": -60_000.0, "non_viable": 0.0}, "provenance": "fact"},
                ],
                "preferences": {
                    "loss_limit": 10_000.0,
                    "max_breach_prob": 0.05,
                },
            }
        )
        self.assertFalse(cmp_res["has_unverified_assumptions"])
        self.assertEqual(cmp_res["ev_ranking"]["optimal_id"], "pilot_then_commit")


if __name__ == "__main__":
    unittest.main()
