---
name: analyzing-risk-decisions
description: "Use when comparing options under uncertain losses or payoffs (insurance, cloud SLA/DR, QA/CI gating, AI model/tool selection, lease-vs-buy, staged R&D), inverting break-even probability, reservation price, or indifference risk tolerance R*, or calibrating tail-loss constraints (概率决策、赔率与回本门槛反推、风险偏好与尾部损失评估). For qualitative startup/market devil's-advocate critique without payoff math, use yc-rejection-simulator."
allowed-tools:
  - read
  - grep
  - glob
  - exec
---

# analyzing-risk-decisions

Frame uncertain choices as a **joint finite state-space + incremental net-loss function** $Z_a(s)$, solved via:

$$
a^* = \arg\min_a CE_R(Z_a), \qquad CE_R(Z_a) = R \ln \mathbb{E}[e^{Z_a / R}], \qquad \text{s.t. } \text{cost}_a \le B,\; \Pr(Z_a > A) \le \varepsilon
$$

Deliver **switching boundaries** (exact conditions where Choice A flips to Choice B) and **value of missing evidence**, backed by deterministic execution of `scripts/decision_engine.py`.

## Workflow

1. **Tag every input's provenance** (`fact` | `estimate` | `assumption` | `preference`):
   - `fact`: verified contract clauses, quotes, deductibles, caps, current surrender/resale value $K$.
   - `estimate`: empirical base rates with cited scope (distinguish portfolio loss ratios or claim-acceptance rates from individual annual event probability).
   - `assumption`: stress-test probabilities, eligibility factors, or future fee growth rates when empirical distributions are unavailable.
   - `preference`: user-supplied budget $B$, cash-buffer limit $A$, acceptable tail probability $\varepsilon$, and CARA risk tolerance $R$ ($R$ measures curvature against large losses, distinct from total net worth). Keep model-computed risk separate from user-accepted risk.

2. **Map contracts and architecture into incremental state-wise net losses**:
   - Build one shared state table across all alternatives so correlated shocks, common-mode outages, and overlapping coverage sit on identical states.
   - Measure every candidate by **portfolio increment** ($\Delta C_j(s) = C_{\text{with } j}(s) - C_{\text{current}}(s)$), capping expense reimbursement at uncompensated eligible loss (`reimbursement_payout`).
   - Evaluate multi-period hold-vs-exit choices forward from today (`forward_cashflow_npv`): include future cashflows, terminal value, and today's exit opportunity cost $K$; exclude past sunk payments.

3. **Resolve `SKILL_DIR`, pick the mode, and run `decision_engine.py`**:
   - Set `SKILL_DIR` from the invoked skill's `Base directory` header (in Devin CLI) or the directory containing this `SKILL.md` (e.g. `~/.config/devin/skills/analyzing-risk-decisions` or `<plugin_root>/skills/analyzing-risk-decisions`) so execution works from any project working directory. Read [`references/schemas-and-patterns.md`](references/schemas-and-patterns.md) (`"$SKILL_DIR/references/schemas-and-patterns.md"`) for JSON input schemas and domain patterns.
   - Prefer passing JSON over stdin (`--input -` with `<<'EOF'`) or a `/tmp` file rather than writing scratch files into the user's repository:
   - **`compare`** — probabilities or stress scenarios are given:
     ```bash
     python3 "$SKILL_DIR/scripts/decision_engine.py" compare --input - <<'EOF'
     { ... }
     EOF
     ```
     Computes EV, incremental RTP, `VaR`/`ES` (use deep-tail `ES` alongside `VaR` when rare catastrophes fall beyond `1 - alpha`), breach probability $\Pr(Z_a > A)$, `cara_ce`, and strict dominance / zero-increment overlap flags.
   - **`invert`** — probabilities, prices, or $R$ are unknown; solve for switching thresholds:
     ```bash
     python3 "$SKILL_DIR/scripts/decision_engine.py" invert --input - <<'EOF'
     { ... }
     EOF
     ```
     Supports `break_even_probability` ($p^*$ risk-neutral and CARA-adjusted), `reservation_price` ($P^*(R)$ closed-form max acceptable cost), `indifference_r` ($R^*$ crossing roots and winner regimes), and `budget_tail_frontier` (min cost for $\varepsilon$ / min breach prob for $B$).
   - **`calibrate`** — $R$ is unknown or needs consistency verification:
     ```bash
     python3 "$SKILL_DIR/scripts/decision_engine.py" calibrate --input - <<'EOF'
     { ... }
     EOF
     ```
     Infers the consistent $[R_{\min}, R_{\max}]$ interval from pairwise sure-cost vs lottery answers, pinpoints conflicting pairs when preferences violate CARA, and generates 3 scale-matched calibration questions when `target_loss_scale` is supplied.
   - **`cashflow`** — multi-year discounted hold-vs-exit cashflows:
     ```bash
     python3 "$SKILL_DIR/scripts/decision_engine.py" cashflow --input - <<'EOF'
     { ... }
     EOF
     ```

4. **Verify invariants and report conditional conclusions**:
   - Confirm all `invariants` in engine output are `true` (run `python3 "$SKILL_DIR/scripts/decision_engine.py" selftest` after any script edit).
   - State the **switching boundary** explicitly (e.g., required annual event probability $p^*$, max justifiable fee $P^*(R)$, or indifference $R^*$), label `assumption`-tagged outputs as conditional stress tests rather than personal forecasts, and list the top missing datum whose resolution can flip `optimal_id`.
