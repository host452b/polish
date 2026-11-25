#!/usr/bin/env python3
"""Calculate Status-Bar Replace vs. Append KV-cache cost (Ch.2) and detect prefix mutations."""

from __future__ import annotations

import argparse
import json


def compare_status_strategies(s_tokens: int, r_tokens: int, n_turns: int, alpha: float) -> dict:
    if n_turns <= 1:
        return {
            "replace_extra_equiv_tokens": 0.0,
            "append_extra_equiv_tokens": 0.0,
            "recommended": "either (N <= 1)",
        }
    c_replace = (n_turns - 1) * (1.0 - alpha) * r_tokens
    c_append = alpha * s_tokens * n_turns * (n_turns - 1) / 2.0
    rec = "persistent_append" if c_append < c_replace else "replace_each_turn"
    return {
        "parameters": {
            "status_tokens_S": s_tokens,
            "cached_suffix_after_old_status_R": r_tokens,
            "injections_N": n_turns,
            "cache_read_price_ratio_alpha": alpha,
        },
        "replace_extra_equiv_tokens": round(c_replace, 2),
        "append_extra_equiv_tokens": round(c_append, 2),
        "lhs_alpha_S_N_div_2": round(alpha * s_tokens * n_turns / 2.0, 2),
        "rhs_one_minus_alpha_R": round((1.0 - alpha) * r_tokens, 2),
        "recommended": rec,
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Compare Replace-each-turn vs Persistent-append status bar cache cost.")
    p.add_argument("--status-tokens", "-S", type=int, required=True, help="Tokens per status injection (S)")
    p.add_argument("--cached-suffix", "-R", type=int, required=True, help="Avg already-cached tokens sitting AFTER old status (R)")
    p.add_argument("--turns", "-N", type=int, required=True, help="Number of status injections (N)")
    p.add_argument("--alpha", "-a", type=float, default=0.1, help="Cached input price / normal input price (default: 0.1)")
    args = p.parse_args()

    result = compare_status_strategies(args.status_tokens, args.cached_suffix, args.turns, args.alpha)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
