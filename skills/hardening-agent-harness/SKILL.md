---
name: hardening-agent-harness
description: Use when building, auditing, or debugging an agent runtime or Harness for reliability and fragility — including premature completion, silent data fabrication on tool failure, infinite retry loops, hung streaming connections, cross-provider trajectory failover, duplicate non-idempotent side effects, sandbox escapes, or prompt-injection exfiltration (Agent 与 Harness 脆弱性加固、防编造数据、防死循环与死亡螺旋、幂等与跨模型接管).
---

# Hardening Agent Harnesses Against Fragility

Engineer the production **Harness** (`Agent = Model + Harness`, where `Harness = Context + Tools + Constrain + Verify + Correct`) so fragile model behaviors, network drops, and untrusted inputs cannot corrupt state or fake completion.

## Harness Hardening Workflow

1. **Enforce the 3-Layer Guardrail & Lethal-Quadruple Defense (`Constrain`).**
   When an agent combines **Private Data + Untrusted Input + Outbound Communication + Persistent Memory**, prompt instructions alone cannot hold the boundary:
   - **Context layer:** Wrap external data in Harness-generated provenance tags (`<external_content source="webpage">`) and strip forged role/status tags. Tag every persistent memory write with `{source, scope, verified_status}` so untrusted web/email text cannot plant sleeper instructions into `MEMORY.md`.
   - **Execution layer:** Default-deny network egress and out-of-workspace writes inside real OS/container/microVM sandboxes (`venv` is **not** a sandbox). Parse shell ASTs/flags rather than relying on regex blacklists. Gate high-impact calls with a **Sidecar** classifier that reads **only** `{user_intent, tool_name, structured_args}`—never the main model's persuasive rationale or raw untrusted tool outputs.
   - **Data layer:** Enforce server-side truth & Row-Level Security (`AccessContext` bound by trusted auth, server clock, DB state)—never trust model-supplied flags like `cancellation_reason="airline_cancelled"` to bypass policy.
   *Completion criterion:* Every external mutation passes an out-of-context deterministic check + Sidecar/HITL gate, with network egress allowlisted.

2. **Eliminate Silent Fabrication & Premature Completion (`Verify`).**
   - **Completion gate invariant:** A model can *propose* completion (`tool_calls == []`), never *approve* it. Run `Harness.verify_completion(decision, Environment)` against independent evidence (protected test suite, DB transaction status, rendered screenshot, source receipt) before returning to the user.
   - **Anti-fabrication provenance check:** Models under tool timeouts or missing observation channels (e.g., CoinGecko timeout in Exp 1-3; missing receipt image pixels in T3A; unreadable CSV in Denario) frequently fabricate plausible hardcoded numbers in Python scripts or prose. Verify that reported numbers trace to actual tool-return records or input hashes—treat ungrounded literals after a tool failure as a hard verification veto.
   - **Commitment vs. Settlement:** Require final responses to distinguish *oral/API request accepted* ("carrier promised $80 credit") from *settled environment state* ("$80 credit posted on statement").
   *Completion criterion:* Zero unverified completion exits; synthetic/hardcoded data after tool failure triggers immediate rejection feedback.

3. **Build the 4-Layer Error Recovery Matrix & Stream Watchdogs (`Correct`).**
   Map every failure to its layer instead of blind `"retry on exception"`:
   - **API layer (429 / 5xx / network drop / `max_tokens`):** Exponential backoff + jitter on foreground calls only (**drop auxiliary background retries** like title generation to prevent retry amplification). Attach an **idle-stream watchdog** (chunk-to-chunk timeout aware of reasoning heartbeats) in addition to connection timeout to kill silently hung streams.
   - **Tool layer (bad schema / missing file / permission denied):** Never retry identical `(tool_name, canonical_args)` fingerprints. Return structured error + parameter JSON + actionable hint into `role: "tool"` so the model self-corrects.
   - **Context layer (overflow / broken `tool_call_id` pair):** Reconcile missing tool outputs from execution logs first (or explicit `"status_unknown"` marker in prod; **never** inject fake placeholders into training trajectories), then run batch compression with a **3-failure circuit breaker**.
   - **Control-flow layer (loop / death spiral):** Forbid error-handling hooks (e.g., on-exit auto-commit message generators) from invoking LLMs on the primary budget; guard all recovery hooks with re-entrancy locks, recursion-depth caps, and global turn/cost budgets.
   *Completion criterion:* Every recovery path has an empirically calibrated circuit-breaker cap, fingerprint loop detector, and zero LLM calls inside fatal error handlers.

4. **Make mutations idempotent and store Neutral Trajectories for failover.**
   - **Idempotency & reconciliation:** Generate and persist a deterministic `idempotency_key` *before* dispatching external writes; separate `"request_sent"`, `"remote_acked"`, and `"result_persisted"` states. On timeout/crash, query remote state by `idempotency_key` / business ID before retrying; use **Precheck -> Confirm -> Commit** for non-idempotent actions (email, phone call, transfer).
   - **Stream-cut & Cross-Provider Failover:** Never prefix-continue a mid-JSON tool-call cut without re-validating semantics (e.g., `"东京"` cut at `{"city":"东` gets validly closed as wrong city `"东"`—re-issue the turn or deduplicate already-dispatched streaming tool calls by fingerprint). Persist sessions in a **vendor-neutral trajectory** separating portable facts/summaries from opaque provider tokens (`thinking` signatures, `thoughtSignature`), remapping `tool_call_id`s on failover.
   *Completion criterion:* Crash-before-ack replay produces zero duplicate mutations, and mid-task provider switch completes without HTTP 400 or repeated side effects.

## Red Flags — Fragile Harness Smells

- Catch-all `for attempt in range(5): call_tool()` around non-idempotent writes or deterministic parameter errors.
- Only setting `connect_timeout` on streaming LLM calls with no inter-token idle watchdog.
- Letting the Coding Agent modify test files, evaluation scripts, or approval thresholds to make CI green.
- Using Python `venv` or prompt wording as the sole barrier for untrusted code execution.

## Disclosed Reference

- Read [references/harness-fragility-catalog.md](references/harness-fragility-catalog.md) for the complete 12-item production fragility checklist, codebase referenceskeletons, and real postmortem cases from `ai-agent-book` v3.0.
