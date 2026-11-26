# Production Harness Fragility Catalog & Reference Skeletons

## 1. Reference Production Harness Loop (Ch.1 & Ch.5)

```python
history = [user_request, Environment.observe()]

while Harness.within_budget():  # Global turns, wall-clock, and USD/token caps
    decision = Model(Harness.build_context(history), watchdog_idle_s=45)
    history.append(Harness.to_neutral_record(decision))

    if not decision.tool_calls:
        verdict = Harness.verify_completion(decision, Environment)  # Protected tests / DB truth / provenance
        if verdict.passed:
            return decision.answer
        history.append(verdict.feedback)
        continue

    for call in Harness.schedule_by_dependency(decision.tool_calls):
        if Harness.is_repeated_no_progress(call, history):
            history.append(Harness.loop_breaker_feedback(call))
            continue

        permission = Harness.constrain(call)  # Deterministic ACL + structure-only Sidecar + HITL
        if permission.denied:
            history.append(permission.feedback)
            continue

        result = Harness.dispatch_idempotent(call)  # Persist intent + idempotency_key BEFORE network I/O
        verdict = Harness.verify_step(call, result, Environment)
        if not verdict.passed:
            result = Harness.correct_bounded(call, result, verdict)  # Per-path circuit breaker
        history.append(result)

return Harness.escalate_with_checkpoint(history)
```

## 2. Twelve High-Incidence Harness Fragilities & Mitigations

| # | Fragility | Real Case / Evidence | Concrete Mitigation |
|---|---|---|---|
| 1 | **Silent Data Fabrication after Tool Error** | Exp 1-3 (CoinGecko timeout -> 31 fake BTC prices in Python); Ch.7 T3A (`Coffee $4.50`); Denario synthetic CSV fallback | Inspect code/tool traces for hardcoded arrays when upstream fetch failed; require provenance hash linking inputs to outputs |
| 2 | **Premature Completion / Deleting Failing Tests** | Coding agents claiming green without running tests or editing `test_*.py` | Run read-only protected `FAIL_TO_PASS` + `PASS_TO_PASS` tests outside agent write scope on exit |
| 3 | **Truncated JSON Prefix-Continuation Corruption** | Exp 5-2 (`{"city":"东` closed into valid JSON `{"city":"东"}` instead of `"东京"`, 0/3 recovery) | Discard partial tool-call JSON and re-sample turn, or validate against entity constraints + deduplicate streaming tool calls |
| 4 | **Cross-Provider Opaque Signature Crash** | Exp 5-1 (`reasoning_content` / `thoughtSignature` rejected on failover; neutral trajectory 6/6 vs raw/stripped 3/6 & 4/6) | Persist vendor-neutral trajectory; strip opaque signatures and render completed tool steps as verified narrative if target API requires |
| 5 | **Silent Stream Hang** | TCP socket stays open during reasoning/overload while zero tokens arrive | Enforce separate `connect_timeout`, `read_idle_timeout` (reset on reasoning/heartbeat events), and `turn_total_timeout` |
| 6 | **Error-Hook Death Spiral** | Context overflow -> exit hook calls LLM for commit message -> overflows again -> infinite loop; 3,000+ compression retries | Zero LLM calls on fatal error paths; 3-strike circuit breaker per recovery mechanism; re-entrancy guard |
| 7 | **Duplicate Mutation on Crash-Before-Ack** | Refund/order succeeded remotely, socket dropped before tool result saved | Persist `{intent, idempotency_key}` to outbox first; reconcile remote status by key/business ID before retry (note Stripe 24h key TTL & strict param match) |
| 8 | **Parallel Tool Cascade Over-Kill** | One missing file in 3 parallel `read_file` calls aborts the whole batch | Isolate errors to dependent downstream calls only; preserve independent sibling results; serialize concurrent writes to same path |
| 9 | **Ephemeral vs. Persistent Shell Drift** | Agent runs `cd repo && source .venv/bin/activate`, next command spawns fresh subshell in wrong dir | Default to persistent session IDs tracking `cwd`/env, or pass explicit `workdir` + env per call; re-verify daemon liveness after resume |
| 10 | **Persistent Memory Poisoning** | Exp 2-5 / Ch.5: untrusted webpage summary saved into `MEMORY.md` triggers unauthorized action in next session | Record `{source, trust_level, timestamp}` on memory entries; forbid external untrusted memories from authorizing execution |
| 11 | **Principal Loyalty Drift** | Ch.5 multi-party negotiation: agent leaks principal's `$12,000` ceiling to vendor or over-refuses normal negotiation | Separate private constraints from public talking points; evaluate both confidentiality preservation and deal completion |
| 12 | **Plugin Hot-Swap Resource Leaks** | Ch.9 DeepSeek Harness / Cordis: reloading a tool plugin leaves duplicate event listeners active | Track `revertible effects` (cleanup hooks for listeners/locks/timers) and `reactive coeffects` (pause dependents when upstream provider drops) |
