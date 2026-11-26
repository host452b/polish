#!/usr/bin/env python3
"""Deterministic calculator for Pass@k, Pass^k, Wilson CI, and Paired McNemar / Bootstrap comparisons (Ch.7)."""

from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path


def comb_ratio(s: int, n: int, k: int) -> float:
    if k < 1 or k > n:
        raise ValueError(f"Require 1 <= k <= n (got k={k}, n={n})")
    if s < k:
        return 0.0
    return math.comb(s, k) / math.comb(n, k)


def pass_at_k_unbiased(n: int, c: int, k: int) -> float:
    """Unbiased estimator 1 - C(n-c, k) / C(n, k)."""
    if n - c < k:
        return 1.0
    return 1.0 - (math.comb(n - c, k) / math.comb(n, k))


def pass_power_k_unbiased(n: int, c: int, k: int) -> float:
    """tau2-bench unbiased estimator C(c, k) / C(n, k)."""
    return comb_ratio(c, n, k)


def wilson_ci(successes: int, total: int, z: float = 1.959964) -> tuple[float, float]:
    if total == 0:
        return (0.0, 0.0)
    p = successes / total
    denom = 1.0 + (z * z) / total
    center = (p + (z * z) / (2.0 * total)) / denom
    half = (z / denom) * math.sqrt((p * (1.0 - p) / total) + ((z * z) / (4.0 * total * total)))
    return (max(0.0, center - half), min(1.0, center + half))


def exact_mcnemar_pvalue(b_only: int, a_only: int) -> float:
    n = b_only + a_only
    if n == 0:
        return 1.0
    k = min(b_only, a_only)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n)
    return min(1.0, 2.0 * tail)


def paired_compare(scores_a: dict[str, float], scores_b: dict[str, float], seed: int = 42, n_boot: int = 5000) -> dict:
    if set(scores_a.keys()) != set(scores_b.keys()):
        missing_a = sorted(set(scores_b.keys()) - set(scores_a.keys()))
        missing_b = sorted(set(scores_a.keys()) - set(scores_b.keys()))
        raise ValueError(f"Mismatched task keys! missing_in_a={missing_a[:5]}, missing_in_b={missing_b[:5]}")

    keys = sorted(scores_a.keys())
    n = len(keys)
    diffs = [scores_b[k] - scores_a[k] for k in keys]
    mean_a = sum(scores_a[k] for k in keys) / n
    mean_b = sum(scores_b[k] for k in keys) / n
    mean_diff = sum(diffs) / n

    both_pass = [k for k in keys if scores_a[k] == 1 and scores_b[k] == 1]
    only_a = [k for k in keys if scores_a[k] == 1 and scores_b[k] == 0]
    only_b = [k for k in keys if scores_a[k] == 0 and scores_b[k] == 1]
    both_fail = [k for k in keys if scores_a[k] == 0 and scores_b[k] == 0]

    rng = random.Random(seed)
    boot_means = []
    for _ in range(n_boot):
        sample = [diffs[rng.randrange(n)] for _ in range(n)]
        boot_means.append(sum(sample) / n)
    boot_means.sort()
    ci_low = boot_means[int(0.025 * n_boot)]
    ci_high = boot_means[int(0.975 * n_boot)]

    result: dict = {
        "n_tasks": n,
        "mean_a": round(mean_a, 4),
        "mean_b": round(mean_b, 4),
        "mean_diff_b_minus_a": round(mean_diff, 4),
        "paired_bootstrap_95ci": [round(ci_low, 4), round(ci_high, 4)],
    }
    if all(scores_a[k] in (0, 1) and scores_b[k] in (0, 1) for k in keys):
        result["binary_breakdown"] = {
            "both_pass": len(both_pass),
            "gains_only_b": len(only_b),
            "regressions_only_a": len(only_a),
            "both_fail": len(both_fail),
            "gain_tasks": only_b,
            "regression_tasks": only_a,
            "wilson_95ci_a": [round(x, 4) for x in wilson_ci(int(sum(scores_a.values())), n)],
            "wilson_95ci_b": [round(x, 4) for x in wilson_ci(int(sum(scores_b.values())), n)],
            "exact_mcnemar_p_value": round(exact_mcnemar_pvalue(len(only_b), len(only_a)), 6),
        }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute Pass@k / Pass^k or Paired McNemar & Bootstrap statistics.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_pass = sub.add_parser("passk", help="Compute Pass@k and Pass^k from n trials with c successes (or theoretical p)")
    p_pass.add_argument("--trials", "-n", type=int, help="Number of trials for the task")
    p_pass.add_argument("--successes", "-c", type=int, help="Number of passing trials")
    p_pass.add_argument("--prob", "-p", type=float, help="Theoretical single-trial probability p (optional)")
    p_pass.add_argument("-k", type=int, required=True, help="Target k")

    p_pair = sub.add_parser("paired", help="Compare two JSON files mapping task_id -> score (0/1 or float)")
    p_pair.add_argument("file_a", type=Path, help="Baseline JSON {task_id: score}")
    p_pair.add_argument("file_b", type=Path, help="Candidate JSON {task_id: score}")

    args = parser.parse_args()
    if args.cmd == "passk":
        out: dict = {"k": args.k}
        if args.trials is not None and args.successes is not None:
            out["empirical_unbiased"] = {
                "n": args.trials,
                "c": args.successes,
                "pass_at_k": round(pass_at_k_unbiased(args.trials, args.successes, args.k), 4),
                "pass_power_k": round(pass_power_k_unbiased(args.trials, args.successes, args.k), 4),
            }
        if args.prob is not None:
            out["theoretical_iid"] = {
                "p": args.prob,
                "pass_at_k": round(1.0 - ((1.0 - args.prob) ** args.k), 4),
                "pass_power_k": round(args.prob ** args.k, 4),
            }
        print(json.dumps(out, indent=2))
        return 0

    scores_a = json.loads(args.file_a.read_text(encoding="utf-8"))
    scores_b = json.loads(args.file_b.read_text(encoding="utf-8"))
    print(json.dumps(paired_compare(scores_a, scores_b), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
