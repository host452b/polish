# Provider Thinking Protocols, KV Cache Constraints & Compression Benchmarks

## 1. Provider-Specific Reasoning Continuation Rules (Ch.2)

| Provider / Family | Protocol Requirement During Tool Loops | Failure if Violated |
|---|---|---|
| **DeepSeek (Thinking + `tools`)** | Must echo `reasoning_content` verbatim on **every** prior assistant turn within the active tool loop (even assistant turns without `tool_calls`). Ignored only when `tools` is absent. | Immediate HTTP `400` error |
| **Claude (Preserved Thinking)** | Save `thinking` blocks + cryptographic signatures. On prefix-bound models (e.g., Claude Fable 5.1, Opus 5.5), `system`, `tools`, and all prior messages form the verified prefix. Trim thinking blocks only as contiguous head/tail ranges (no middle gaps). Use mid-conversation system/tool change blocks for runtime updates. | HTTP `400` or silent drop of invalidated thinking blocks (`prefix_mismatch_behavior`) |
| **Qwen3 Chat Template** | Preserves `<think>` only after the **last `user` message**. Passing a tool result with `role: "user"` instead of `role: "tool"` resets the boundary and strips active reasoning. | Silent loss of multi-step reasoning state |
| **GLM (`clear_thinking: false`)** | Explicitly set `thinking.clear_thinking: false` (defaults differ between Coding Plan and standard API) and echo `reasoning_content` in exact order. | Inconsistent reasoning retention across endpoints |
| **Kimi (Interleaved Thinking)** | Preserve interleaved reasoning + `tool_calls` in exact assistant message sequence. | Degraded long-horizon planning |
| **OpenAI Responses API** | Pair `function_call` with `function_call_output` via `call_id`. `previous_response_id` chains state, **but** top-level `instructions` and `tools` are NOT automatically inherited and must be supplied each turn. | Missing instructions or unavailable tools on continuation |

## 2. Empirical Context Management & Compression Benchmarks (Book v3.0)

### Exp 2-3: KV Cache Anti-Patterns (Kimi K2.6)
- **Tool schema shuffling:** `Hit%` looked identical (`100%`), yet actual cached token share (`Cache%`) dropped from `10.1%` (`768 / 7,567` tokens) to `3.4%` (`256 / 7,568` tokens). Always measure `cached_tokens / prompt_tokens`, never request-level `Hit%` alone.
- **Sliding window (last 6 messages):** Achieved highest `Cache%` (`67.9%`), **but failed the task**—repeatedly rediscovered files and omitted the required 3-sentence summary.

### Exp 2-10: Six Compression Strategies (Kimi K3, 128K Budget)

| Strategy | Rounds | Main-Agent Tokens | Char Ratio | Key Finding |
|---|---:|---:|---:|---|
| No compression | 5 (stopped) | 166,043 | — | Hit protection ceiling after 7 tool calls (367K raw chars) |
| Individual summary | 12 | 276,608 | 10.9% | Cross-page duplication inflated total rounds & tokens |
| Combined summary | 10 | 93,449 | 4.3% | Eliminates cross-page duplicates; risks input truncation |
| **Context-aware summary** | **7** | **40,157** | **3.0%** | Compressed ~150K chars -> ~2K chars keeping target entities & role shifts |
| Context-aware + citations | 10 | 222,992 | 4.1% | Preserves provenance; verify links are real URLs, not prose names |
| Adaptive windowed (80% trigger + `[COMPRESSED]`) | 7 | 174,601 | — | Preserves lossless raw text early; trigger on **latest-turn prompt tokens**, not cumulative sum |

**Critical Caveat:** Both `citations` and `windowed` "completed" the table yet reported contradictory employers (`Pebblebed` vs `Stripe`) for Pamela Vagata. Always pair compression with citation/source spot-checks.

### Exp 7-10: Cache + Compression Non-Additivity
Savings from stable prefixes (`28.3%`) and history compression (`17.5%`) are **non-additive** (`30.0%` combined on GPT-4o-mini; on Kimi K2.5, compressing history after enabling prefix cache actually *increased* uncached tokens from `4,729` to `7,180`, raising 8-turn cost from `$0.00825` to `$0.00906`). Always benchmark combined cost end-to-end.
