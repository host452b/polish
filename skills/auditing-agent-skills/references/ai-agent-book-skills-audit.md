# Empirical Audit: `ai-agent-book/skills` (22 Skills vs. Book v3.0)

This reference documents concrete defects uncovered when auditing the 22 skills bundled in `ai-agent-book/skills/` against the v3.0 manuscript (`book/chapter1.md`–`book/chapter10.md`) and modern skill-engineering standards.

## 1. Systemic Structural & Routing Defects (22 / 22 Skills)

1. **SDO Workflow-Summary Shortcut (`D1`, 22/22 skills):**
   Every `description` appends `——覆盖... / 涵盖... / 含...` listing the internal frameworks and steps of the skill. When an always-loaded description summarizes how to perform the task, agents frequently follow the summary and skip loading `SKILL.md`, while burning permanent context tokens on every turn.
2. **Repo-Coupled Dead Paths (`D4`, 22/22 skills):**
   All 22 skills reference `book/chapterX.md` and `chapterX/...` directly as relative paths, yet their own `README.md` instructs users to copy them into `~/.claude/skills/`, immediately breaking every pointer outside the book repo.
3. **Zero Progressive Disclosure (`D3` / `D9`, 22/22 skills):**
   None of the 22 skills separate always-needed execution steps from heavy reference tables (`references/`) or ship deterministic verification helpers (`scripts/`), forcing agents to parse dense 100-line Chinese essays and re-implement formulas by hand.

## 2. Factual & Empirical Drift vs. Book v3.0 (`D10`)

| Upstream Skill | Stale / Defective Claim in `SKILL.md` | Verified Evidence in `book/` v3.0 | Engineering Lesson |
|---|---|---|---|
| `context-engineering` | Claims Exp 2-4 scrambling prompt structure drops task pass rate ">30%" and removing tool descriptions increases error "+45%" | `book/chapter2.md` Exp 2-4 (Kimi K3 on τ-bench, 10 tasks): Baseline `7/10`, Scrambled `8/10`, Removed description `9/10`, Casual tone `9/10`, Trump tone `6/10` | Stronger models recover intent from tool names + JSON Schemas alone; re-run ablations after model upgrades to prune "feature debt" |
| `agent-state-bar` | Claims Exp 2-9 TODO list cuts iterations `21 -> 15` and detailed errors lift recovery `60% -> 95%` | `book/chapter2.md` Exp 2-9 (Kimi K3, 5 cases/group): Timestamps `5/5` vs `3/5`; Combined `5/5` vs `3/5`; TODO-only `0/5` vs `1/5` control; Detailed-error-only `4/5` vs `5/5` control | Individual status-bar widgets are not universally positive across models; validate combined vs single-feature marginal gain |
| `memory-system` | Cites Mem0 v3 LoCoMo `92.5` / LongMemEval `94.4`; claims Qwen3-0.6B PII redaction recall ">95%" | `book/chapter3.md`: Mem0 v3 LoCoMo `71.4 -> 91.6`, LongMemEval `67.8 -> 93.4`; Exp 3-3 average recall is Regex `50%`, Local LLM `69%`, Hybrid `78%` (and regex masked a ticket ID, hurting precision `2/3`) | Local 0.6B redaction still misses ~22% on hard samples; combine regex fast-path + model semantic pass + precision audit on business IDs |
| `context-compression` | Omits `citations` token count (`—`) and `windowed` iteration count (`—`) | `book/chapter2.md` Exp 2-10: `citations` used `10` rounds / `222,992` tokens (`4.1%` ratio); `windowed` used `7` rounds / `174,601` tokens; AND `citations` vs `windowed` contradicted each other on Pamela Vagata (`Pebblebed` vs `Stripe`) | Compression completion != factual fidelity; verify entity-attribute consistency and live URLs |
| `tool-discovery` | Cites `35 tools = 3,857 tokens` | `book/chapter4.md` Exp 4-1: `127` MCP tools = `50,597` `o200k` tokens; active discovery appended `3,939 / 1,853 / 2,632` tokens; adds `selection_ablation.py` isolating token-padding length vs distractor-tool confusion | Distinguish context-length degradation from near-duplicate tool-confusion degradation |
| `async-event-agent` | Duplicate step `6.` numbering; omits the entire v3.0 Unified Ingress Layer | `book/chapter6.md` "接入层：多种来源，一种事件": Unified Envelope (`dedupe_key`, `thread`, `correlation`, `kind`, `raw_ref`, `expires_at`), ACK-after-append (<3s Feishu / <5s WeCom), 3-progress separation (`source` / `dispatch` / `task` + `outbox`), state coalescing vs message batching, and `dsh-superagent` Main vs Executor session split | Without ACK-after-append and 3-progress separation, webhook retries and log replays trigger duplicate external side effects |

## 3. Iterative Before/After Diff Extraction & 4-Layer Funnel (Ch.2 & Ch.9)

- **Iterative Extraction from Human Edits (Exp 2-7):** Draft a 20-line v0 `SKILL.md` from 3–5 gold artifacts -> run on a fresh task -> diff `agent_draft` vs `human_edited_final` -> codify recurring deltas as `Scope + Action + Exception + Verification` tuples. Widen clarification gates when users say *"not what I meant"*; narrow them when users say *"too many questions"* on reversible edits.
- **4-Layer Benefit Funnel (Table 9-3):** Separate *Proposal Validity* (force-injected replay) from *Activation Rate* (`description` routing), *Compliance Rate* (step completion), and *Boundary + Retention Holdout Gain* so a routing miss never causes you to delete valid domain rules.

## 4. High-Fragility Gaps Consolidated from v3.0

- **Silent Data Fabrication under Tool Failure** (`book/chapter1.md` Exp 1-3 CoinGecko timeout -> hardcoded 31 fake prices; `book/chapter7.md` T3A fabricated `Coffee $4.50` when image pixels were missing; Denario fabricated synthetic scientific data when file read failed).
- **Unit-Scaling Rounding Amplification** (`book/chapter1.md` Exp 1-1: passing `2.1` instead of `2100000` to `convert_currency` magnified 2-decimal rounding by $10^6$, losing `$2,895.73`).
- **Preserved Thinking Prefix Binding** (`book/chapter2.md`: Claude Fable 5.1 / Opus 5.5 invalidates signed thinking blocks or returns HTTP 400 if `system`, `tools`, or prior messages mutate).
- **Lethal Trifecta + Persistent Memory (4th Dimension)** (`book/chapter5.md`: private data + untrusted input + outbound comms + persistent `MEMORY.md` turns a one-shot injection into a cross-session sleeper payload).
- **Voice Fast/Slow Delegation Pitfalls** (`book/chapter6.md` Exp 6-7: ASR homophone corruption `"陈嘉怡" -> "陈佳宜"` when text-only slow backend books tickets; dropped flight answer when user asks weather mid-wait).
