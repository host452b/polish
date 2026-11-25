---
name: evaluating-evolving-agents
description: Use when building agent benchmarks or evaluation pipelines, choosing Pass@k vs Pass^k metrics, designing deterministic verifiers or LLM-as-a-Judge rubrics, attributing trajectory failures, testing statistical significance of model or Harness changes, or routing bad cases into Knowledge, Skill, Harness code, SFT, DPO, RLVR, RLVP, or On-Policy Distillation updates (Agent 评估体系、失败归因与前缀回归、模型后训练选型与持续进化闭环).
---

# Evaluating, Post-Training, and Evolving Agents

Turn agent iteration from anecdotal trajectory-reading into a scientific closed loop: measure `Model + Harness` with calibrated verifiers and paired statistics, isolate first-divergence errors into prefix regressions, and route updates to the cheapest valid carrier guarded by **Boundary + Retention** sets.

## Evaluation & Evolution Workflow

1. **Define the Task Metric, Dual-Control Environment, and Verifier.**
   - **Metric alignment:** Use `Pass@k` / `Best@k` ($1 - (1-p)^k$) for exploration/discovery where one verified hit suffices; require **`Pass^k`** ($p^k$; at $p=0.6, k=5$, `Pass@5 = 99.0%` vs `Pass^5 = 7.8%`) for production workflows where every customer run must succeed. Track **cost per successful task** (including failed retries) and p95/p99 tail latency.
   - **4-part reproducible task spec:** `ticket` + `user_scenario` (`known_info` separated from `task_instructions`, grounded in user-side tool outputs with patience caps) + resettable `initial_state` + `evaluation_criteria`.
   - **Verifier hierarchy:** Assert **environment state + scope non-collateral** (`FAIL_TO_PASS` + `PASS_TO_PASS` + verifying untouched records like roommate-only payment approvals) and **final user communication** separately ("did it right, explained it wrong"). Use **Rubric + Multi-Family LLM-as-a-Judge** only for open-ended quality: self-contained criteria, weighted tiers, position-swap + length-bias checks, and a **hard 0-score Veto on hallucination**.
   *Completion criterion:* Resettable eval harness verifies both environment end-state and user-facing statement without trusting agent self-reports.

2. **Run Controlled Ablations & Paired Statistical Significance.**
   - **Check the eval harness first** whenever scores drop (resource OOM, stale mock state, overly narrow rubric labels like rejecting valid `ask_user`).
   - Run **Model Swap** (fixed Harness, vary model) vs **Component Ablation** (fixed model, toggle one Harness feature) across 3–5 seeds.
   - Compare configurations on the **exact same `(task_id, seed)` pairs** using `python3 scripts/paired_eval_stats.py` to inspect gains, regressions, Wilson CIs, exact McNemar $p$-values, and paired bootstrap CIs—never eyeball raw aggregate deltas (`70% -> 73%` can hide `+23` gains and `-20` regressions!).
   *Completion criterion:* Paired gain/loss matrix and confidence interval computed before promoting any prompt, Harness, or model change.

3. **Attribute First-Divergence Failures into Prefix Regressions.**
   - Filter suspect traces with cheap deterministic rules first (unexecuted test claims, edited assertions, missing schema migrations), then align agent claims against tool outputs step-by-step to locate the **earliest diverging step** (distinguishing observation-channel absence, tool/serializer corruption, Harness bug, and model decision error).
   - Freeze the context + state immediately *before* the first error into a **Trajectory-Prefix Regression Task** scored against an **acceptable action set** + **forbidden action set**.
   *Completion criterion:* Every recurring production bad case converted into a fast, deterministic prefix regression test.

4. **Route Updates Across the 4 Evolution Carriers & Post-Training Stages.**
   Choose the lightest carrier that matches how the capability is represented, and gate release behind **Boundary Set (fixes target failure) + Retention Set (zero regression / zero over-correction)**:
   1. **Experience Knowledge Base:** Missing/updated domain facts or cross-trajectory lessons (`applicable_when + recommended_action + counterexamples + evidence_ids`).
   2. **Prompt / Skill (`minimal diff`):** Articulable judgment rules/SOPs; track the 4-layer funnel (**Proposal Validity -> Activation Rate -> Compliance Rate -> Holdout Gain**).
   3. **Program / Harness (`git worktree` + PR):** Deterministic retries, auth gates, parsers, or parameterized RPA workflows; protect verifiers, release thresholds, and audit logs in an **immutable control plane** the business agent cannot edit. Run periodic offline **"Sleep Consolidation"** to deduplicate, prune superseded rules, and archive stale skills.
   4. **Model Parameters (only after ruling out upstream byte/tool/Harness bugs):**
      - `pass@k ≈ 0` on domain language/concepts -> **Mid-training** (domain + ~20% general replay, checked on `capability × context-length` matrix).
      - Format/schema unstable -> **SFT / RFT** (loss-mask system/user/tool-return tokens; LoRA on all linear + MLP layers at ~10× full-FT LR, rank `64–256`).
      - `pass@1` low, `pass@k` rising, verifiable reward has within-group variance -> **RLVR (`GRPO` / `PPO`) + `RLVP`** (`R = O + βΦ`: reward outcome, penalize verifiable path violations; mask environment tokens; unit-test **sampler vs. trainer token log-prob parity** *before* step 1!).
      - Expensive rollouts + available teacher (or privileged answer context) -> **On-Policy Distillation / OPSD** (~10× sample efficiency via dense per-token reverse KL on student prefixes).
   *Completion criterion:* Carrier selected via replay test ("can find rule" vs "can apply rule when given"), sampler/trainer parity verified for RL, and Boundary + Retention sets pass in staging.

## Disclosed Resources

- Run `scripts/paired_eval_stats.py` to compute `Pass@k`, `Pass^k` (unbiased combinatorial estimator), Wilson CIs, paired gain/loss breakdowns, exact McNemar test, and paired bootstrap CIs.
- Read [references/post-training-and-evolution-matrix.md](references/post-training-and-evolution-matrix.md) for the 9-category failure taxonomy, SFT/DPO/RLVR/RLVP/OPD recipes, and Sleep Consolidation checklist.
