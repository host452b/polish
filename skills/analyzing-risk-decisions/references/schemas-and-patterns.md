# JSON Schemas & Domain Modeling Patterns

Input reference for `scripts/decision_engine.py` (stdlib-only Python 3.10+; accepts `--input path.json` or `--input -` on stdin).

## 1. `compare` Schema

All monetary values use net-loss sign convention (`+` = cost/outflow, `-` = net profit/inflow). Each alternative specifies either `state_residual_losses` (added to `upfront_cost - sure_benefit`) or `state_net_losses` directly.

```json
{
  "baseline_id": "status_quo",
  "states": [
    {"id": "normal", "prob": 0.997, "provenance": "assumption"},
    {"id": "major_loss", "prob": 0.003, "provenance": "assumption"}
  ],
  "alternatives": [
    {
      "id": "status_quo",
      "upfront_cost": 0.0,
      "sure_benefit": 0.0,
      "state_residual_losses": {"normal": 0.0, "major_loss": 200000.0},
      "provenance": "fact"
    },
    {
      "id": "hedged",
      "upfront_cost": 600.0,
      "sure_benefit": 0.0,
      "state_residual_losses": {"normal": 0.0, "major_loss": 10000.0},
      "provenance": "fact"
    }
  ],
  "preferences": {
    "risk_tolerances": [50000, 200000, 1000000],
    "budget": 1000.0,
    "loss_limit": 20000.0,
    "max_breach_prob": 0.001,
    "tail_alphas": [0.99, 0.999]
  }
}
```

## 2. `invert` Schemas (`kind` dispatch)

### `break_even_probability`
Solves $p^* = \frac{P - v}{a \cdot C}$ (risk-neutral) and exact CARA indifference $p^*(R)$ when `loss_when_event` and `risk_tolerances` are provided.

```json
{
  "kind": "break_even_probability",
  "cost": 600.0,
  "sure_benefit": 0.0,
  "conditional_payout": 190000.0,
  "eligibility": 0.95,
  "loss_when_event": 200000.0,
  "risk_tolerances": [50000, 200000]
}
```

### `reservation_price`
Closed-form maximum upfront cost $P^*(R) = CE_R(Y_{\text{base}}) - CE_R(Y_{\text{cand}}) + \Delta v$.

```json
{
  "kind": "reservation_price",
  "states": [{"id": "ok", "prob": 0.997}, {"id": "hit", "prob": 0.003}],
  "baseline_residual_losses": {"ok": 0.0, "hit": 200000.0},
  "candidate_residual_losses": {"ok": 0.0, "hit": 10000.0},
  "sure_benefit_delta": 0.0,
  "risk_tolerances": [50000, 200000]
}
```

### `indifference_r`
Finds all crossing roots $R^*$ where $CE_{R^*}(Z_A) = CE_{R^*}(Z_B)$ and partitions $(0, \infty)$ into winner regimes.

```json
{
  "kind": "indifference_r",
  "states": [{"id": "ok", "prob": 0.997}, {"id": "hit", "prob": 0.003}],
  "alt_a": {"id": "none", "upfront_cost": 0.0, "state_residual_losses": {"ok": 0.0, "hit": 200000.0}},
  "alt_b": {"id": "plan", "upfront_cost": 600.0, "state_residual_losses": {"ok": 0.0, "hit": 10000.0}}
}
```

### `budget_tail_frontier`
Finds Pareto-efficient `(upfront_cost, breach_prob, expected_net_loss)` alternatives, minimum cost meeting `max_breach_prob`, and minimum breach probability within `budget`.

```json
{
  "kind": "budget_tail_frontier",
  "states": [
    {"id": "ok", "prob": 0.98},
    {"id": "az_down", "prob": 0.018},
    {"id": "region_down", "prob": 0.002}
  ],
  "alternatives": [
    {"id": "single_az", "upfront_cost": 0.0, "state_residual_losses": {"ok": 0.0, "az_down": 80000.0, "region_down": 250000.0}},
    {"id": "multi_az", "upfront_cost": 1200.0, "state_residual_losses": {"ok": 0.0, "az_down": 2000.0, "region_down": 250000.0}},
    {"id": "multi_region", "upfront_cost": 6000.0, "state_residual_losses": {"ok": 0.0, "az_down": 1000.0, "region_down": 5000.0}}
  ],
  "loss_limit": 20000.0,
  "max_breach_prob": 0.005,
  "budget": 2000.0
}
```

## 3. `calibrate` Schema

Infers feasible CARA $R \in [r_{\min}, r_{\max}]$ from stated/revealed trade-offs and optionally generates 3 scale-matched calibration prompts.

```json
{
  "choices": [
    {
      "id": "q1",
      "sure_loss": 1200.0,
      "lottery_losses": [0.0, 200000.0],
      "lottery_probs": [0.997, 0.003],
      "picked": "sure"
    }
  ],
  "target_loss_scale": 200000.0,
  "event_prob": 0.003
}
```

## 4. `cashflow` Schema & Python Primitives

```json
{
  "future_benefits": [[20.0, 500000.0]],
  "future_costs": [[1.0, 2415.0], [2.0, 2415.0]],
  "discount_rate": 0.02,
  "exit_opportunity_cost": 875.0,
  "terminal_value": [20.0, 0.0]
}
```

For multi-policy expense reimbursement in custom scripts, import `reimbursement_payout` from `scripts/decision_engine.py`:

```python
from decision_engine import reimbursement_payout

# Caps payout at min(cap, rate * max(0, eligible_loss - deductible), max(0, eligible_loss - prior_compensation))
incremental = reimbursement_payout(50_000, deductible=12_000, rate=0.7, cap=1_000_000, prior_compensation=45_000)
```

## 5. Domain Patterns

- **Overlapping insurance / warranties**: Compute existing portfolio compensation $O(s)$ first, pass `prior_compensation=O(s)` into `reimbursement_payout`, and feed residual losses into `compare`. Any policy with `zero_incremental_protection=true` and no separate lump-sum/insurability option is strictly dominated.
- **Cloud DR / CI gating**: Split states into component-local vs common-mode failures (`az_down` vs `region_down`, or `unit_catchable_bug` vs `spec_bug`) so correlated failure limits are explicit rather than multiplied as independent events.
- **Staged R&D / pilot gate**: Model `(viable, non_viable)` states with negative residual loss for net profit (`-60000.0`); use `reservation_price` against `do_nothing` to compute maximum justifiable pilot spend before committing full capex.
