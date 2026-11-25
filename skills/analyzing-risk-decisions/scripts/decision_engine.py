#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Iterable

VALID_PROVENANCE = {"fact", "estimate", "assumption", "preference"}


def _fmt_key(value: float) -> str:
    if math.isfinite(value) and float(value).is_integer():
        return str(int(value))
    return str(value)


def _validate_probabilities(probs: list[float]) -> None:
    if not probs or any(p < 0.0 for p in probs) or abs(sum(probs) - 1.0) > 1e-9:
        raise ValueError("state probabilities must be non-negative and sum to 1")


def _cara_ce(losses: list[float], probs: list[float], risk_tolerance: float) -> float:
    _validate_probabilities(probs)
    if len(losses) != len(probs):
        raise ValueError("losses and probabilities length mismatch")
    if math.isinf(risk_tolerance) and risk_tolerance > 0:
        return float(sum(x * p for x, p in zip(losses, probs)))
    if risk_tolerance <= 0:
        raise ValueError("risk_tolerance R must be positive (or +inf for risk-neutral)")
    terms = [math.log(p) + (x / risk_tolerance) for x, p in zip(losses, probs) if p > 0.0]
    m = max(terms)
    return float(risk_tolerance * (m + math.log(sum(math.exp(t - m) for t in terms))))


def _var_discrete(losses: list[float], probs: list[float], alpha: float) -> float:
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be in (0, 1)")
    _validate_probabilities(probs)
    cum = 0.0
    for x, p in sorted(zip(losses, probs), key=lambda pair: pair[0]):
        cum += p
        if cum >= alpha - 1e-12:
            return float(x)
    return float(max(x for x, p in zip(losses, probs) if p > 0.0))


def _es_discrete(losses: list[float], probs: list[float], alpha: float) -> float:
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be in (0, 1)")
    _validate_probabilities(probs)
    rem = 1.0 - alpha
    acc = 0.0
    for x, p in sorted(zip(losses, probs), key=lambda pair: pair[0], reverse=True):
        if p <= 0.0:
            continue
        take = min(p, rem)
        acc += x * take
        rem -= take
        if rem <= 1e-15:
            break
    return float(acc / (1.0 - alpha))


def _extract_alt_losses(alt: dict[str, Any], state_ids: list[str]) -> tuple[float, float, list[float], list[float]]:
    upfront = float(alt.get("upfront_cost", 0.0))
    sure_benefit = float(alt.get("sure_benefit", 0.0))
    if "state_net_losses" in alt:
        raw_map = alt["state_net_losses"]
        net = [float(raw_map[sid]) for sid in state_ids]
        residual = [z - upfront + sure_benefit for z in net]
    else:
        res_map = alt["state_residual_losses"]
        residual = [float(res_map[sid]) for sid in state_ids]
        net = [upfront - sure_benefit + y for y in residual]
    return upfront, sure_benefit, residual, net


def reimbursement_payout(
    eligible_loss: float,
    *,
    deductible: float = 0.0,
    rate: float = 1.0,
    cap: float | None = None,
    prior_compensation: float = 0.0,
) -> float:
    if eligible_loss < 0 or deductible < 0 or prior_compensation < 0:
        raise ValueError("monetary inputs must be non-negative")
    if not 0.0 <= rate <= 1.0:
        raise ValueError("coinsurance rate must be in [0, 1]")
    if cap is not None and cap < 0:
        raise ValueError("cap must be non-negative")

    raw = rate * max(0.0, eligible_loss - deductible)
    if cap is not None:
        raw = min(cap, raw)
    residual = max(0.0, eligible_loss - prior_compensation)
    return float(min(raw, residual))


def forward_cashflow_npv(
    future_benefits: Iterable[tuple[float, float]],
    future_costs: Iterable[tuple[float, float]],
    *,
    discount_rate: float = 0.0,
    exit_opportunity_cost: float = 0.0,
    terminal_value: tuple[float, float] | None = None,
) -> dict[str, float | None]:
    if discount_rate <= -1.0:
        raise ValueError("discount_rate must be > -1")
    if exit_opportunity_cost < 0:
        raise ValueError("exit_opportunity_cost must be non-negative")

    def _pv(items: Iterable[tuple[float, float]]) -> float:
        total = 0.0
        for t, amount in items:
            if t < 0:
                raise ValueError("sunk/past cashflows (t < 0) are excluded from forward decisions")
            total += amount / ((1.0 + discount_rate) ** t)
        return float(total)

    pv_benefits = _pv(future_benefits)
    pv_costs = _pv(future_costs)
    pv_terminal = _pv([terminal_value]) if terminal_value is not None else 0.0
    net_pv = pv_benefits + pv_terminal - pv_costs - exit_opportunity_cost
    required_prob = (
        (pv_costs + exit_opportunity_cost - pv_terminal) / pv_benefits
        if pv_benefits > 0
        else None
    )
    return {
        "pv_benefits": pv_benefits,
        "pv_costs": pv_costs,
        "pv_terminal": pv_terminal,
        "exit_opportunity_cost": float(exit_opportunity_cost),
        "net_present_value": float(net_pv),
        "required_benefit_prob_to_break_even": required_prob,
    }


def compare_alternatives(problem: dict[str, Any]) -> dict[str, Any]:
    states = problem["states"]
    alts = problem["alternatives"]
    if not states or not alts:
        raise ValueError("states and alternatives must be non-empty")

    state_ids = [str(s["id"]) for s in states]
    probs = [float(s["prob"]) for s in states]
    _validate_probabilities(probs)

    provenance_tags: set[str] = set()
    for item in [*states, *alts]:
        prov = item.get("provenance", "assumption")
        if prov not in VALID_PROVENANCE:
            raise ValueError(f"invalid provenance {prov!r}; expected one of {sorted(VALID_PROVENANCE)}")
        provenance_tags.add(prov)

    prefs = problem.get("preferences") or {}
    r_values = [float(r) for r in prefs.get("risk_tolerances", [])]
    tail_alphas = [float(a) for a in prefs.get("tail_alphas", [0.99])]
    budget = float(prefs["budget"]) if prefs.get("budget") is not None else None
    loss_limit = float(prefs["loss_limit"]) if prefs.get("loss_limit") is not None else None
    max_breach_prob = (
        float(prefs["max_breach_prob"]) if prefs.get("max_breach_prob") is not None else None
    )

    parsed: dict[str, dict[str, Any]] = {}
    for alt in alts:
        aid = str(alt["id"])
        upfront, sure_benefit, residual, net = _extract_alt_losses(alt, state_ids)
        parsed[aid] = {
            "id": aid,
            "upfront_cost": upfront,
            "sure_benefit": sure_benefit,
            "residual": residual,
            "net": net,
            "provenance": alt.get("provenance", "assumption"),
        }

    baseline_id = str(problem.get("baseline_id", alts[0]["id"]))
    if baseline_id not in parsed:
        raise ValueError(f"baseline_id {baseline_id!r} not found in alternatives")
    base = parsed[baseline_id]
    base_ev = sum(z * p for z, p in zip(base["net"], probs))
    base_ce = {_fmt_key(r): _cara_ce(base["net"], probs, r) for r in r_values}

    out_alts: list[dict[str, Any]] = []
    ce_bounds_ok = True
    es_ge_var_ok = True

    for aid, info in parsed.items():
        net = info["net"]
        pos_losses = [z for z, p in zip(net, probs) if p > 0.0]
        ev = float(sum(z * p for z, p in zip(net, probs)))
        worst = float(max(pos_losses))
        best = float(min(pos_losses))

        inc_protection = [b_res - r_res for b_res, r_res in zip(base["residual"], info["residual"])]
        expected_inc_protection = float(sum(d * p for d, p in zip(inc_protection, probs)))
        delta_sure = info["sure_benefit"] - base["sure_benefit"]
        delta_cost = info["upfront_cost"] - base["upfront_cost"]
        inc_ev = float(base_ev - ev)
        inc_rtp = (
            float((expected_inc_protection + delta_sure) / delta_cost)
            if delta_cost > 1e-12
            else None
        )
        zero_inc = (
            aid != baseline_id
            and delta_cost > 1e-12
            and max((d for d, p in zip(inc_protection, probs) if p > 0.0), default=0.0) <= 1e-12
            and delta_sure <= 1e-12
        )

        dominated_by: list[str] = []
        for other_id, other in parsed.items():
            if other_id == aid:
                continue
            no_worse_all = all(
                other["net"][i] <= net[i] + 1e-12 for i, p in enumerate(probs) if p > 0.0
            )
            strictly_better_some = any(
                other["net"][i] < net[i] - 1e-12 for i, p in enumerate(probs) if p > 0.0
            )
            if no_worse_all and strictly_better_some:
                dominated_by.append(other_id)

        cara_map: dict[str, float] = {}
        cara_gain_map: dict[str, float] = {}
        for r in r_values:
            rk = _fmt_key(r)
            ce_val = _cara_ce(net, probs, r)
            cara_map[rk] = ce_val
            cara_gain_map[rk] = float(base_ce[rk] - ce_val)
            if not (ev - 1e-7 <= ce_val <= worst + 1e-7 and ce_val >= best - 1e-7):
                ce_bounds_ok = False

        var_map: dict[str, float] = {}
        es_map: dict[str, float] = {}
        for alpha in tail_alphas:
            ak = _fmt_key(alpha)
            v_val = _var_discrete(net, probs, alpha)
            e_val = _es_discrete(net, probs, alpha)
            var_map[ak] = v_val
            es_map[ak] = e_val
            if e_val + 1e-7 < v_val:
                es_ge_var_ok = False

        breach_prob = (
            float(sum(p for z, p in zip(net, probs) if z > loss_limit + 1e-12))
            if loss_limit is not None
            else None
        )
        within_budget = True if budget is None else (info["upfront_cost"] <= budget + 1e-12)
        within_tail = (
            True
            if (breach_prob is None or max_breach_prob is None)
            else (breach_prob <= max_breach_prob + 1e-12)
        )

        out_alts.append(
            {
                "id": aid,
                "provenance": info["provenance"],
                "upfront_cost": info["upfront_cost"],
                "expected_net_loss": ev,
                "worst_case_loss": worst,
                "incremental_ev_vs_baseline": inc_ev,
                "incremental_rtp": inc_rtp,
                "zero_incremental_protection": zero_inc,
                "strictly_dominated_by": dominated_by,
                "cara_ce": cara_map,
                "cara_ce_gain_vs_baseline": cara_gain_map,
                "var": var_map,
                "es": es_map,
                "breach_prob": breach_prob,
                "feasible": bool(within_budget and within_tail),
            }
        )

    rankings_by_r: dict[str, dict[str, Any]] = {}
    for r in r_values:
        rk = _fmt_key(r)
        all_sorted = sorted(out_alts, key=lambda row: row["cara_ce"][rk])
        feas_sorted = [row for row in all_sorted if row["feasible"]]
        rankings_by_r[rk] = {
            "optimal_id": feas_sorted[0]["id"] if feas_sorted else None,
            "feasible_order": [row["id"] for row in feas_sorted],
            "unconstrained_optimal_id": all_sorted[0]["id"],
        }

    ev_sorted = sorted(out_alts, key=lambda row: row["expected_net_loss"])
    ev_feas = [row for row in ev_sorted if row["feasible"]]
    ev_ranking = {
        "optimal_id": ev_feas[0]["id"] if ev_feas else None,
        "feasible_order": [row["id"] for row in ev_feas],
        "unconstrained_optimal_id": ev_sorted[0]["id"],
    }

    return {
        "baseline_id": baseline_id,
        "provenance_tags": sorted(provenance_tags),
        "has_unverified_assumptions": "assumption" in provenance_tags,
        "alternatives": out_alts,
        "ev_ranking": ev_ranking,
        "rankings_by_r": rankings_by_r,
        "invariants": {
            "probabilities_sum_to_one": abs(sum(probs) - 1.0) <= 1e-9,
            "ce_bounded_between_ev_and_worst": ce_bounds_ok,
            "es_at_least_var": es_ge_var_ok,
        },
    }


def _solve_indifference_roots(
    net_a: list[float], net_b: list[float], probs: list[float]
) -> tuple[list[float], float]:
    pos_vals = [z for z, p in zip(net_a, probs) if p > 0.0] + [
        z for z, p in zip(net_b, probs) if p > 0.0
    ]
    spread = max(pos_vals) - min(pos_vals)
    if spread <= 1e-12 or all(
        abs(a - b) <= 1e-12 for a, b, p in zip(net_a, net_b, probs) if p > 0.0
    ):
        return [], 0.0

    def gap(r: float) -> float:
        return _cara_ce(net_a, probs, r) - _cara_ce(net_b, probs, r)

    lo_log = math.log(max(spread * 1e-5, 1e-9))
    hi_log = math.log(max(spread * 1e7, 1e6))
    n_steps = 400
    step = (hi_log - lo_log) / n_steps
    grid_logs = [lo_log + i * step for i in range(n_steps + 1)]
    grid_vals = [gap(math.exp(lg)) for lg in grid_logs]

    roots: list[float] = []
    for i in range(n_steps):
        v0, v1 = grid_vals[i], grid_vals[i + 1]
        if abs(v0) <= 1e-13:
            cand = math.exp(grid_logs[i])
        elif v0 * v1 < 0.0:
            a_lg, b_lg = grid_logs[i], grid_logs[i + 1]
            fa = v0
            for _ in range(80):
                m_lg = 0.5 * (a_lg + b_lg)
                fm = gap(math.exp(m_lg))
                if fa * fm <= 0.0:
                    b_lg = m_lg
                else:
                    a_lg, fa = m_lg, fm
            cand = math.exp(0.5 * (a_lg + b_lg))
        else:
            continue
        if not roots or abs(cand - roots[-1]) / max(cand, 1.0) > 1e-6:
            roots.append(float(cand))
    return roots, spread


def invert_thresholds(spec: dict[str, Any]) -> dict[str, Any]:
    kind = spec["kind"]

    if kind == "break_even_probability":
        cost = float(spec["cost"])
        sure_benefit = float(spec.get("sure_benefit", 0.0))
        net_cost = cost - sure_benefit
        payout = float(spec["conditional_payout"])
        eligibility = float(spec.get("eligibility", 1.0))
        if not 0.0 <= eligibility <= 1.0:
            raise ValueError("eligibility must be in [0, 1]")

        denom = payout * eligibility
        if net_cost <= 0.0:
            rn_p: float | None = 0.0
        elif denom <= 0.0:
            rn_p = None
        else:
            raw_p = net_cost / denom
            rn_p = float(raw_p) if raw_p <= 1.0 else None

        cara_p: dict[str, float | None] = {}
        r_list = [float(r) for r in spec.get("risk_tolerances", [])]
        if r_list:
            loss = float(spec["loss_when_event"])
            for r in r_list:
                rk = _fmt_key(r)
                if net_cost <= 0.0:
                    cara_p[rk] = 0.0
                    continue
                if denom <= 0.0:
                    cara_p[rk] = None
                    continue

                def diff_at(p: float, r_val: float = r) -> float:
                    ce_without = _cara_ce([0.0, loss], [1.0 - p, p], r_val)
                    ce_with = _cara_ce(
                        [net_cost, net_cost + loss - payout, net_cost + loss],
                        [1.0 - p, p * eligibility, p * (1.0 - eligibility)],
                        r_val,
                    )
                    return ce_without - ce_with

                if diff_at(1.0) < -1e-12:
                    cara_p[rk] = None
                else:
                    lo, hi = 0.0, 1.0
                    for _ in range(80):
                        mid = 0.5 * (lo + hi)
                        if diff_at(mid) >= 0.0:
                            hi = mid
                        else:
                            lo = mid
                    cara_p[rk] = float(0.5 * (lo + hi))

        return {
            "kind": kind,
            "risk_neutral_p_star": rn_p,
            "cara_p_star": cara_p,
        }

    if kind == "reservation_price":
        states = spec["states"]
        state_ids = [str(s["id"]) for s in states]
        probs = [float(s["prob"]) for s in states]
        _validate_probabilities(probs)
        base_res = [float(spec["baseline_residual_losses"][sid]) for sid in state_ids]
        cand_res = [float(spec["candidate_residual_losses"][sid]) for sid in state_ids]
        sure_delta = float(spec.get("sure_benefit_delta", 0.0))

        rn_max = float(
            sum((b - c) * p for b, c, p in zip(base_res, cand_res, probs)) + sure_delta
        )
        cara_max = {
            _fmt_key(float(r)): float(
                _cara_ce(base_res, probs, float(r))
                - _cara_ce(cand_res, probs, float(r))
                + sure_delta
            )
            for r in spec.get("risk_tolerances", [])
        }
        return {
            "kind": kind,
            "risk_neutral_max_cost": rn_max,
            "cara_max_cost": cara_max,
        }

    if kind == "indifference_r":
        states = spec["states"]
        state_ids = [str(s["id"]) for s in states]
        probs = [float(s["prob"]) for s in states]
        _validate_probabilities(probs)
        id_a = str(spec["alt_a"]["id"])
        id_b = str(spec["alt_b"]["id"])
        _, _, _, net_a = _extract_alt_losses(spec["alt_a"], state_ids)
        _, _, _, net_b = _extract_alt_losses(spec["alt_b"], state_ids)

        roots, spread = _solve_indifference_roots(net_a, net_b, probs)
        if spread <= 1e-12 and not roots:
            return {
                "kind": kind,
                "roots_r_star": [],
                "regimes": [{"r_min": 0.0, "r_max": None, "preferred_id": "indifferent"}],
            }

        boundaries: list[float | None] = [0.0, *roots, None]
        regimes: list[dict[str, Any]] = []
        for idx in range(len(boundaries) - 1):
            r_lo = boundaries[idx]
            r_hi = boundaries[idx + 1]
            if r_lo == 0.0 and r_hi is None:
                probe = max(spread, 1.0)
            elif r_lo == 0.0 and r_hi is not None:
                probe = r_hi * 0.5
            elif r_lo is not None and r_hi is None:
                probe = r_lo * 2.0
            else:
                assert r_lo is not None and r_hi is not None
                probe = math.sqrt(r_lo * r_hi)
            diff = _cara_ce(net_a, probs, probe) - _cara_ce(net_b, probs, probe)
            winner = id_a if diff < -1e-12 else (id_b if diff > 1e-12 else "indifferent")
            regimes.append({"r_min": r_lo, "r_max": r_hi, "preferred_id": winner})

        return {
            "kind": kind,
            "roots_r_star": roots,
            "regimes": regimes,
        }

    if kind == "budget_tail_frontier":
        states = spec["states"]
        state_ids = [str(s["id"]) for s in states]
        probs = [float(s["prob"]) for s in states]
        _validate_probabilities(probs)
        loss_limit = float(spec["loss_limit"])
        max_breach = (
            float(spec["max_breach_prob"]) if spec.get("max_breach_prob") is not None else None
        )
        budget = float(spec["budget"]) if spec.get("budget") is not None else None

        points: list[dict[str, Any]] = []
        for alt in spec["alternatives"]:
            aid = str(alt["id"])
            upfront, _, _, net = _extract_alt_losses(alt, state_ids)
            ev = float(sum(z * p for z, p in zip(net, probs)))
            breach = float(sum(p for z, p in zip(net, probs) if z > loss_limit + 1e-12))
            points.append(
                {
                    "id": aid,
                    "upfront_cost": upfront,
                    "breach_prob": breach,
                    "expected_net_loss": ev,
                }
            )

        pareto: list[dict[str, Any]] = []
        for pt in sorted(points, key=lambda row: (row["upfront_cost"], row["breach_prob"], row["expected_net_loss"])):
            dominated = any(
                other["id"] != pt["id"]
                and other["upfront_cost"] <= pt["upfront_cost"] + 1e-12
                and other["breach_prob"] <= pt["breach_prob"] + 1e-12
                and other["expected_net_loss"] <= pt["expected_net_loss"] + 1e-12
                and (
                    other["upfront_cost"] < pt["upfront_cost"] - 1e-12
                    or other["breach_prob"] < pt["breach_prob"] - 1e-12
                    or other["expected_net_loss"] < pt["expected_net_loss"] - 1e-12
                )
                for other in points
            )
            if not dominated:
                pareto.append(pt)

        by_tail = (
            min(
                (pt for pt in points if pt["breach_prob"] <= max_breach + 1e-12),
                key=lambda row: (row["upfront_cost"], row["breach_prob"], row["expected_net_loss"]),
                default=None,
            )
            if max_breach is not None
            else None
        )
        by_budget = (
            min(
                (pt for pt in points if pt["upfront_cost"] <= budget + 1e-12),
                key=lambda row: (row["breach_prob"], row["upfront_cost"], row["expected_net_loss"]),
                default=None,
            )
            if budget is not None
            else None
        )
        return {
            "kind": kind,
            "pareto_frontier": pareto,
            "min_cost_for_tail_limit": by_tail,
            "min_tail_for_budget": by_budget,
        }

    raise ValueError(f"unsupported invert kind: {kind!r}")


Interval = tuple[float, float | None]


def _intersect_intervals(lhs: list[Interval], rhs: list[Interval]) -> list[Interval]:
    out: list[Interval] = []
    for a_lo, a_hi in lhs:
        for b_lo, b_hi in rhs:
            lo = max(a_lo, b_lo)
            if a_hi is None:
                hi = b_hi
            elif b_hi is None:
                hi = a_hi
            else:
                hi = min(a_hi, b_hi)
            if hi is None or lo <= hi + 1e-9:
                out.append((lo, hi))
    return out


def _feasible_r_intervals(
    chosen: list[float], rejected: list[float], probs: list[float], indifferent: bool = False
) -> list[Interval]:
    roots, spread = _solve_indifference_roots(chosen, rejected, probs)
    if indifferent:
        return [(r, r) for r in roots]
    if spread <= 1e-12 and not roots:
        return [(0.0, None)]

    boundaries: list[float | None] = [0.0, *roots, None]
    intervals: list[Interval] = []
    for idx in range(len(boundaries) - 1):
        r_lo = boundaries[idx]
        r_hi = boundaries[idx + 1]
        assert r_lo is not None
        if r_lo == 0.0 and r_hi is None:
            probe = max(spread, 1.0)
        elif r_lo == 0.0 and r_hi is not None:
            probe = r_hi * 0.5
        elif r_hi is None:
            probe = r_lo * 2.0
        else:
            probe = math.sqrt(r_lo * r_hi)
        if _cara_ce(chosen, probs, probe) <= _cara_ce(rejected, probs, probe) + 1e-12:
            if intervals and intervals[-1][1] is not None and abs(intervals[-1][1] - r_lo) <= 1e-9:
                intervals[-1] = (intervals[-1][0], r_hi)
            else:
                intervals.append((r_lo, r_hi))
    return intervals


def calibrate_preferences(spec: dict[str, Any]) -> dict[str, Any]:
    choices = spec.get("choices") or []
    choice_bounds: list[dict[str, Any]] = []
    per_choice_intervals: list[tuple[str, list[Interval]]] = []
    combined: list[Interval] = [(0.0, None)]
    any_impossible = False

    for idx, ch in enumerate(choices, 1):
        cid = str(ch.get("id", f"q{idx}"))
        if "sure_loss" in ch:
            sure_val = float(ch["sure_loss"])
            lot_losses = [float(x) for x in ch["lottery_losses"]]
            probs = [float(p) for p in ch["lottery_probs"]]
            _validate_probabilities(probs)
            sure_vec = [sure_val for _ in probs]
            picked = str(ch["picked"])
            if picked == "sure":
                chosen, rejected, is_indiff = sure_vec, lot_losses, False
            elif picked == "lottery":
                chosen, rejected, is_indiff = lot_losses, sure_vec, False
            elif picked == "indifferent":
                chosen, rejected, is_indiff = sure_vec, lot_losses, True
            else:
                raise ValueError(f"invalid picked={picked!r} for choice {cid}")
        else:
            probs = [float(p) for p in ch["probs"]]
            _validate_probabilities(probs)
            chosen = [float(x) for x in ch["chosen_losses"]]
            rejected = [float(x) for x in ch["rejected_losses"]]
            is_indiff = bool(ch.get("indifferent", False))

        ivs = _feasible_r_intervals(chosen, rejected, probs, indifferent=is_indiff)
        if not ivs:
            any_impossible = True
            choice_bounds.append(
                {
                    "id": cid,
                    "status": "no_cara_solution",
                    "r_min": None,
                    "r_max": None,
                }
            )
        else:
            choice_bounds.append(
                {
                    "id": cid,
                    "status": "ok",
                    "r_min": ivs[0][0],
                    "r_max": ivs[-1][1],
                }
            )
            per_choice_intervals.append((cid, ivs))
        combined = _intersect_intervals(combined, ivs)

    conflicting_pairs: list[list[str]] = []
    for i in range(len(per_choice_intervals)):
        cid_i, ivs_i = per_choice_intervals[i]
        for j in range(i + 1, len(per_choice_intervals)):
            cid_j, ivs_j = per_choice_intervals[j]
            if not _intersect_intervals(ivs_i, ivs_j):
                conflicting_pairs.append([cid_i, cid_j])

    consistent = bool(not any_impossible and combined)
    r_min = combined[0][0] if consistent else None
    r_max = combined[-1][1] if consistent else None

    suggested_questions: list[dict[str, Any]] = []
    if spec.get("target_loss_scale") is not None:
        scale = float(spec["target_loss_scale"])
        p_ev = float(spec.get("event_prob", 0.01))
        if scale <= 0.0 or not 0.0 < p_ev < 1.0:
            raise ValueError("target_loss_scale must be > 0 and event_prob in (0, 1)")
        for mult, profile in [
            (0.25, "high_aversion"),
            (1.0, "moderate_aversion"),
            (4.0, "low_aversion"),
        ]:
            r_anchor = scale * mult
            sure_eq = _cara_ce([0.0, scale], [1.0 - p_ev, p_ev], r_anchor)
            suggested_questions.append(
                {
                    "profile": profile,
                    "anchor_r": r_anchor,
                    "event_prob": p_ev,
                    "event_loss": scale,
                    "indifference_sure_cost": sure_eq,
                }
            )

    return {
        "consistent": consistent,
        "r_min": r_min,
        "r_max": r_max,
        "choice_bounds": choice_bounds,
        "conflicting_pairs": conflicting_pairs,
        "suggested_questions": suggested_questions,
    }


def run_selftest() -> dict[str, Any]:
    c_100 = 100.0 * math.log((1.0 + math.e) / 2.0)
    cal = calibrate_preferences(
        {
            "choices": [
                {
                    "id": "t1",
                    "sure_loss": c_100,
                    "lottery_losses": [0.0, 100.0],
                    "lottery_probs": [0.5, 0.5],
                    "picked": "indifferent",
                }
            ]
        }
    )
    checks = {
        "deductible_below_zero_payout": reimbursement_payout(10_000, deductible=12_000, rate=0.7) == 0.0,
        "prior_compensation_caps_residual": abs(
            reimbursement_payout(50_000, deductible=12_000, rate=0.7, prior_compensation=45_000) - 5_000.0
        )
        < 1e-9,
        "ce_constant_identity": abs(_cara_ce([123.0, 123.0], [0.3, 0.7], 50_000.0) - 123.0) < 1e-9,
        "ce_risk_neutral_limit": abs(_cara_ce([0.0, 1_000.0], [0.99, 0.01], 1e11) - 10.0) < 1e-4,
        "es_tail_mean_exact": abs(_es_discrete([0.0, 200_000.0], [0.997, 0.003], 0.999) - 200_000.0) < 1e-7,
        "calibration_exact_indifference": cal["consistent"] and abs((cal["r_min"] or 0.0) - 100.0) < 1e-5,
    }
    return {
        "status": "ok" if all(checks.values()) else "failed",
        "checks": checks,
    }


def _read_json_input(path_arg: str) -> dict[str, Any]:
    if path_arg == "-":
        return json.loads(sys.stdin.read())
    return json.loads(Path(path_arg).read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="decision_engine.py",
        description="Deterministic probabilistic decision analysis, threshold inversion, and CARA preference calibration.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    for name in ("compare", "invert", "calibrate", "cashflow"):
        sp = sub.add_parser(name)
        sp.add_argument("--input", required=True, help="Path to JSON input file, or '-' for stdin")

    sub.add_parser("selftest")
    args = parser.parse_args(argv)

    if args.cmd == "selftest":
        res = run_selftest()
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0 if res["status"] == "ok" else 1

    data = _read_json_input(args.input)
    if args.cmd == "compare":
        out = compare_alternatives(data)
    elif args.cmd == "invert":
        out = invert_thresholds(data)
    elif args.cmd == "calibrate":
        out = calibrate_preferences(data)
    elif args.cmd == "cashflow":
        benefits = [(float(t), float(a)) for t, a in data.get("future_benefits", [])]
        costs = [(float(t), float(a)) for t, a in data.get("future_costs", [])]
        tv_raw = data.get("terminal_value")
        tv = (float(tv_raw[0]), float(tv_raw[1])) if tv_raw is not None else None
        out = forward_cashflow_npv(
            benefits,
            costs,
            discount_rate=float(data.get("discount_rate", 0.0)),
            exit_opportunity_cost=float(data.get("exit_opportunity_cost", 0.0)),
            terminal_value=tv,
        )
    else:
        raise ValueError(f"unknown subcommand {args.cmd!r}")

    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
