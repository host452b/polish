---
name: architecting-agent-context
description: Use when designing an agent context window, structuring system prompts and API message loops, diagnosing TTFT spikes or low KV-cache hit rates, managing reasoning or preserved-thinking blocks across turns, building an agent status bar, or choosing between context compression and subagent isolation (上下文工程、KV Cache 命中率下降、状态栏设计、上下文压缩与子 Agent 隔离).
---

# Architecting Agent Context

Design stateless LLM API requests (`messages` + `tools`) so the agent sees complete decision-making context while maximizing cross-turn KV/Prompt Cache reuse and avoiding Context Rot.

## Architecture Workflow

1. **Partition the context window by mutability.**
   Arrange every model request in strict prefix-stability order:
   ```text
   [1. Static System Prompt]     <- Byte-identical across turns & sessions
   [2. Core Tool Schemas]        <- Deterministic registration/alphabetical order
   [3. Append-Only Trajectory]   <- user / assistant(tool_calls+reasoning) / tool(tool_call_id)
   [4. Tail Dynamic Injection]   <- Status bar, newly discovered tool/skill bodies
   ```
   Move volatile environment combinations (OS, mode, locale: $2^k$ prefix variants) after shared rules, and never interpolate live timestamps, balances, or counters into `system`.
   *Completion criterion:* Two consecutive requests in the same session share an identical byte prefix up to the previous turn's tail.

2. **Enforce native Chat Template roles and Thinking-Block protocols.**
   - Pass tool outputs strictly via `role: "tool"` paired by `tool_call_id` (or `function_call_output` + `call_id` in Responses API; note top-level `instructions` and `tools` must still be passed when chaining `previous_response_id`). Never flatten history into `USER: / ASSISTANT:` strings or inject tool outputs as plain `user` messages (which tricks templates like Qwen3 into wiping active `<think>` scratchpads).
   - Preserve provider-mandated reasoning fields across tool loops (DeepSeek/GLM/Kimi `reasoning_content`; Claude signed `thinking` blocks bound to exact `system` + `tools` + message prefixes).
   *Completion criterion:* Multi-turn tool calls pass provider validation with zero HTTP 400 errors or silent thinking-block drops.

3. **Maintain explicit runtime state via a code-computed Agent Status Bar.**
   - Maintain deterministic counts, quotas, working directory, git branch, and active TODO state in code—never ask the LLM to count history events in-context.
   - Inject `<agent_status>` at the message tail (or inside tool responses when template rules strip pre-user thinking). Sanitize any untrusted external text before status-bar rendering.
   - Choose **Replace-each-turn** vs **Persistent-append** using `python3 scripts/estimate_status_bar_cache_cost.py`: append wins when $\alpha S N / 2 < (1 - \alpha) R$.
   *Completion criterion:* Status fields are 100% code-derived, source-sanitized, and evaluated against the cache cost formula.

4. **Bound trajectory growth with Subagent Isolation first, Stratified Compression second.**
   - **Isolate first:** Delegate bounded, high-noise exploration (broad codebase search, multi-page web scraping) to an isolated subagent returning `{conclusion, citations, open_questions}`.
   - **Compress in batches (not every turn):** Apply the 5-tier ladder:
     1. *Entry budget:* Persist outputs >200 lines / 10K chars to disk; freeze the preview string + artifact ID so session replay hits cache.
     2. *Noise stripping:* Strip navbars/ads/unused boilerplate before context entry.
     3. *API-layer context editing:* Drop stale tool blobs only near budget thresholds.
     4. *Stage archival logs:* Structured per-stage changelog.
     5. *Full handoff summary (at ~80% window or stage boundary):* Use a near-parity model with context-aware prompts (`Given query + Current context`) and a 3-strike circuit breaker; explicitly preserve **decisions, constraints, failed paths, and verifiable citations**. If resetting for **Context Anxiety**, write a structured handoff doc to disk and start a clean window.
   *Completion criterion:* Window utilization stays below overflow threshold with zero orphaned `tool_call_id` pairs and audited entity/citation fidelity.

## System Prompt Design Rules

- **Structure:** Combine Markdown headings (`#` hierarchy) with semantic XML tags (`<file_operation>`, `<network_request>`) to scope rules unambiguously.
- **SOP over flat checklists:** Organize multi-stage tasks as explicit Step 1 -> Step N flows with stage-local exit branches.
- **Executable business boundaries:** Replace vague prose ("pick appropriate fee") with boolean predicates, explicit units, rounding order, and boundary intervals (`>=60%`, `30%–60%`, `<30%`).
- **Fixed few-shot sets:** Place 2–3 boundary-covering examples in a fixed order; dynamic per-turn example retrieval busts prefix cache and hurts reproducibility.

## Disclosed Resources

- Run `scripts/estimate_status_bar_cache_cost.py` to compute Replace vs. Append Prompt-Cache cost and inspect prefix breakpoints.
- Read [references/provider-thinking-and-compression.md](references/provider-thinking-and-compression.md) for provider-specific thinking-block rules (DeepSeek, Claude Preserved Thinking, Qwen3, GLM, Kimi, Responses API) and Exp 2-10 compression trade-offs.
