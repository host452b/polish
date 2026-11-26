---
name: engineering-async-realtime-agents
description: Use when building webhook, queue, or cron event-driven agents, designing unified event ingress with deduplication and ACK-after-append, architecting full-duplex or fast/slow voice agents, implementing Computer Use GUI grounding and coordinate scaling, or securing Generative UI and SQL Artifact apps with Data-Layer RLS (异步事件驱动 Agent、统一接入层防重放、快慢双脑实时语音、Computer Use 视觉定位、生成式 UI 与数据层权限).
---

# Engineering Async, Real-Time Voice, GUI, and GenUI Agents

Extend an agent beyond synchronous turn-based text across **timing** (webhooks, queues, timers, mid-turn steering, cancellation) and **modality** (full-duplex voice, Computer Use screens, Generative UI) without duplicate side effects or dropped state.

## Engineering Workflow

1. **Build the Unified Event Ingress Layer (`ACK-After-Append` + 3-Progress Split).**
   - Normalize heterogeneous inputs (App chat, Feishu/WeCom/Slack, email, webhooks, SQS/Kafka, `set_timer`, `monitor_shell`) into one **Unified Envelope** (`id`, `source.verified` via HMAC/OAuth only, semantic `dedupe_key`, per-channel ordered `thread`, cross-channel `correlation`, `kind: state|message`, `raw_ref`, `reply`, `occurred_at`, `expires_at`).
   - **ACK immediately after appending to the inbox log** (beating Feishu 3s / WeCom 5s / SQS visibility timeouts to prevent webhook retry storms).
   - **Maintain 3 independent cursors + Outbox:** Track `source_offset`, `dispatch_cursor`, and `task_state` + outbound `outbox` (`intent + idempotency_key` persisted *before* sending) separately so log replay never double-sends customer messages.
   - **Backpressure & batching:** Log-only expired (`expires_at`) events without waking the LLM; coalesce queued `state` events to the latest value; batch `message` events with explicit `[Unhandled Event i/N]` numbering so the model addresses every item rather than only the last line.
   *Completion criterion:* Crash-before-ack and duplicate-delivery simulations produce exactly 1 inbox entry and <=1 outbound side effect.

2. **Separate Foreground/Main vs. Background/Executor Loops (Async & Voice).**
   - **Main vs. Executor session split (`dsh-superagent` / Fast-Slow Voice):** Keep a non-blocking **Foreground / Main Session** for turn-taking, barge-in interruption, and single-mouthpiece user commitments; delegate multi-step research/coding/booking to an isolated **Background / Executor Session** returning `summary + artifact_id`.
   - **Voice cognitive timing & safety:** Let foreground call fast deterministic tools directly ($\approx 2L_f + T$, e.g., `2.81s` median vs `6.96s` delegated in Exp 6-7) and pre-inject resident memory. When delegating to a text-only slow backend:
     1. Pass verified entity spellings/numbers explicitly in the task brief to prevent ASR homophone corruption (`"陈嘉怡" -> "陈佳宜"`).
     2. Persist unspoken background results in runtime state so a mid-wait user tangent (e.g., asking weather while flight search runs) never drops the completed flight answer.
     3. Distinguish acknowledgment (`"Let me check plan coverage"`) from premature business advice that slow reasoning might contradict; monitor server utilization $\rho$ since queueing latency explodes as $W = S / (1 - \rho)$.
   *Completion criterion:* Interruption/barge-in stops stale audio within one micro-turn, cancels or tracks in-flight tools at safe-points (`cancel != undo`), and preserves pending results.

3. **Ground Computer Use & Secure Generative UI at the Data Layer.**
   - **GUI Grounding priority:** Use **DOM / Accessibility Tree indexed IDs (`[1]..[k]`)** whenever available -> **Set-of-Mark** visual region tags on unindexed native/canvas UIs -> **Aspect-ratio-matched coordinate prediction** (subtract letterbox padding *before* multiplying by `real_dim / model_dim`) on GUI-trained VLMs. Execute **one action per step**, re-verify post-action screen state, and add **inter-action keyframes + persistent text descriptions** (`AOI`) so transient `"Sync failed"` toasts survive image eviction.
   - **Generative UI & Data-Layer RLS:** Stream SQL/table query rows **directly from DB service to UI (`Artifact Direct-to-UI`)** instead of copying rows through LLM tokens; clear invalidated conditional form fields on toggle (Exp 5-12); enforce tenant/role permissions and state-machine invariants inside a trusted **Data Access Layer / PostgreSQL Row-Level Security (`AccessContext`)** independent of dynamically generated app code. Provision **dedicated virtual agent identities** (email/phone/ephemeral VM) and hand off 2FA/CAPTCHA to humans via VNC/trusted auth UI.
   *Completion criterion:* Coordinate transform, post-action state check, form state cleanup, and out-of-sandbox RLS enforcement verified.

## Output Contract

When reviewing or designing an async, voice, GUI, or GenUI agent, output:
1. **Timing & Modality Risk Audit:** Table of `Subsystem | Fragile Boundary (file:line or protocol step) | Evidence ([VERIFIED]/[ASSUMED]/[MISSING]) | Concrete Failure Scenario`.
2. **Ingress, Session Split & Cancellation Spec:** Exact `dedupe_key` rule per source, 3-cursor + outbox persistence boundary, and cancellation/compensation behavior for in-flight side effects.
3. **Fault-Injection Verification Checklist:** Minimum 3 concrete fault tests (duplicate webhook delivery, crash-before-receipt, mid-turn user interruption/override) with pass/fail predicates.

## Disclosed Reference

- Read [references/ingress-voice-and-gui-specs.md](references/ingress-voice-and-gui-specs.md) for the Unified Event Envelope JSON schema, source-by-source deduplication/ordering table, M/M/1 queueing & voice latency formulas, and coordinate scaling math.
