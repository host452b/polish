# Failure Attribution, Post-Training Routing & Sleep Consolidation Reference

## 1. Nine-Category Coding & General Agent Failure Taxonomy (Ch.7)

1. **Requirement / Ambiguity Miss:** Missed constraint, wrong scope, guessed between duplicate configs without checking.
2. **Workflow / Convention Violation:** Skipped repo-mandated plan/test/linter, added external dependency when internal helper exists.
3. **Tool Call / Byte-Copy Error:** Malformed JSON schema, broken Unicode/backslash/newline in `old_string`, wrong unit scale.
4. **Verification Distortion (Reward Hacking / Seeking):** Edited/deleted failing assertions, added `skip`, invented trivial self-check, or claimed tests passed without running them.
5. **Incomplete Modification:** Changed function signature but missed dynamic callers, bindings, or DB migration.
6. **User Feedback Mismatch:** Environment state is right (or partial) while final reply misstates amount, status, or next human action.
7. **Compatibility / Non-Functional Regression:** Broke public API contract, blew up latency/memory/token budget.
8. **Execution Exception:** Stream truncation, idle hang, rate limit, incomplete cleanup.
9. **Premature Stopping:** Stopped after 1 of 2 goals or gave up after one recoverable channel error.

## 2. Post-Training Stage & Pitfall Matrix (Ch.8)

| Stage | Entry Signal | Key Recipe & Hyperparameter Priors | Critical Pitfalls to Guard |
|---|---|---|---|
| **Mid-training (CPT)** | `pass@k ≈ 0`; domain concepts/syntax or long-context tracking absent | ~80% high-density domain/code/reasoning text + ~20% general replay (`FineWeb-2` / base mix); evaluate on `RULER` / `LongBench v2` / `IFEval` `capability × length` matrix | Domain loss drops while downstream task stagnates -> pair with SFT to unlock knowledge access |
| **SFT / RFT / Prompt Distillation** | Unstable JSON/tool protocol, or compressing a `10K`-token prompt/rubric into fast student weights | **Loss-mask** `system`, `user`, and `tool` return tokens; apply LoRA to **all major weights including MLP** at ~`10×` full-FT LR, rank `64–256` | Memorizes surface mappings (`J/Q/K = 10` in GeneralPoints degraded `-8.1%` on `J=11` OOD); verify tokenizer lossless round-trip (~`80.1%` ceiling in Exp 8-19) |
| **DPO from Bad Cases** | Clear decision boundary at trajectory prefix (e.g., premature completion) | Truncate at pre-error prefix; `rejected` = unverified stop, `chosen` = verified continuation; mix general tasks; evaluate on **fixed candidate scoring** + **Boundary & Retention** sets | Small-data DPO without Retention check causes **over-correction** (Exp 8-17 free generation: premature stop `1/12 -> 0/12`, but normal finish collapsed `6/8 -> 0/8`!) |
| **On-Policy RL (`GRPO` / `PPO`) + `RLVP`** | Non-zero `pass@k` with within-group variance; verifiable environment resets | LoRA rank `8–32`; mask environment tokens; `RLVP` splits outcome `O` and turn-localized path penalty `Φ` (`R = O + βΦ`, cut TerminalBench violations `3.71 -> 0.66`); use `Never Give Up` extra rollouts on all-zero hard groups | **Sampler/Trainer numerical mismatch:** `1e-3` per-token log-prob drift between vLLM/SGLang and FSDP/Megatron compounds to $e^4 \approx 54.6\times$ ratio error over 4K tokens! Compare log-probs at step 0 and apply score centering |
| **On-Policy Distillation (`OPD` / `OPSD`)** | Environment rollouts are slow/expensive; stronger teacher or privileged verified answer exists | Student rolls out trajectory; minimize per-token reverse KL $D_{\mathrm{KL}}(\pi_\theta \Vert \pi_T)$ on student prefixes (~`10×` sample efficiency; `+23–47` pp over SFT in temporal control) | In `OPSD`, ensure privileged answer enters **only** the `stop_gradient` teacher branch, never student or eval inputs |

## 3. Six-Item Offline "Sleep Consolidation" Routine (Ch.9)

1. Merge duplicate lessons while preserving provenance IDs and effective dates.
2. Push domain-local rules out of global `AGENTS.md` / `system` into on-demand `SKILL.md` files.
3. Refactor `SKILL.md` hierarchy so triggers, steps, and completion criteria stay crisp.
4. Re-verify rarely used tools/scripts against live API/CLI versions.
5. Mark superseded policies expired (`valid_until`) so default RAG filters them out while historical audits can still time-travel.
6. Re-train LoRA adapters from clean base checkpoints periodically rather than stacking adapter patches indefinitely.
