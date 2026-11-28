# Three-Paradigm Synthesis, Prompt Contracts & Runner Schemas

## 1. Three-Paradigm Synthesis

### Verified Paradigm Matrix (Model Council vs. Multiagent vs. Devin Fusion)

| Axis | Perplexity Model Council | Perplexity Multiagent (Feb Original vs. Nov Mesh) | Cognition Devin Fusion (`Lead` + `Sidekick`) |
| --- | --- | --- | --- |
| **Architectural Nature** | Built-in epistemic deliberation skill (`model-council`) | Effort-level orchestration mode (`Ultra` hub-and-spoke -> `Multiagent` peer mesh, up to 16 agents) | Asymmetric dual-model execution harness + compaction-coupled mid-session router |
| **Task Partitioning** | **Same question** replicated across $2\text{--}8$ distinct models | **Distinct subtasks** decomposed by Lead (`Fable 5.2`) across heterogeneous workers (`Opus`, `GPT`, `Gemini`) | **Phase & abstraction split**: `Lead` owns plan, ambiguity & review; `Sidekick` owns repo exploration, edits & test loops |
| **Lateral Visibility** | **Zero in Round 1** (strictly blind independent runs to prevent herding) | *Feb Computer:* vertical-only to Lead; *Nov Multiagent:* **direct peer-to-peer** evidence sharing & assumption challenges mid-flight | **Bounded brief/result channel** (`Brief + Constraints` <-> `Diff + Test Output + Pushback`); zero raw transcript dumping |
| **KV-Cache & Context Mechanics** | $N$ parallel fresh contexts + 1 Synthesizer pass | Separate worker contexts coordinated via shared artifacts/messages | **Two persistent, separately cached contexts**; mid-session model swaps piggyback on context compaction ("free" cache boundary) |
| **Primary Optimization Target** | **Epistemic calibration & tail recall**: Consensus + Disagreements + `1/N` minority insights | **Breadth & cross-part consistency** across multi-component deliverables (forecasts, filings, full-stack builds) | **Frontier intelligence per dollar** (`31%--60%` lower cost per task at frontier benchmark scores) |
| **Signature Failure Mode** | $N\times$ redundant repo crawling if unfiltered; majority-vote erasure if Chair averages away `1/N` domain truth | Premature convergence / cascading distortion if peers echo unverified assumptions; high coordination token burn | **Collapses when judgment IS the deliverable** (e.g., subtle UX/architecture trade-offs dropped `54 -> 27` when delegated) or serial root-cause chains |

### Mutual Coverage & Subtle Internal Connections

1. **Where Fusion Fails is Exactly Where Model Council Belongs ("When Judgment IS the Deliverable"):**
   - Devin Fusion's empirical 3,000-session study proved that delegation excels when judgment compresses cleanly into invariants (`operator() must be O(1) in pointer length: NO full token scan`, score `94` vs solo `25`), yet **backfires sharply** when subtle cross-cutting judgment calls cannot be reduced to a mechanical spec upfront.
   - **Upstream–Downstream Dual:** Model Council resolves epistemic ambiguity *upstream* (exposing hidden assumptions, contested trade-offs, and long-tail domain traps) to forge a verified **Constraint Brief**; Fusion's `Lead -> Sidekick` pattern then executes and verifies that brief *downstream* at minimal token cost.

2. **Externalized Briefs Act as a Cognitive Ratchet Across Both Paradigms:**
   - In Fusion, `Fable 5` (at $2\times$ per-token price) beat `Opus 4.8` on *both* accuracy (`60.7` vs `54.6`) and total run cost (`$1.86` vs `$2.04`) because writing a clean constraint brief forced explicit invariant locking (`O(1)` hash), whereas solo inline coding let the invariant slip out of working attention mid-edit.
   - In Model Council, forcing the Chair to compress an **opinion-free Fact Pack** (`<= 1,500` tokens) before Round 1 prevents both $N\times$ mechanical file-read waste *and* leading-the-witness prompt bias.

3. **Why Obscure / Long-Tail Domains Require *Knowledge-Distribution Relay* Rather Than Majority Voting:**
   - On common benchmarks, errors are roughly zero-mean noise around shared knowledge, so majority voting helps.
   - In **niche / obscure / long-tail domains** (vendor SoC errata, esoteric RFC extensions, legacy compiler internals, regional compliance rules, cross-disciplinary edge cases), pretraining coverage is **sparse and non-overlapping**:
     - Model Family A may hold exact recall of **Fragment 1** (e.g., register bitmask or protocol framing) while guessing Fragment 2.
     - Model Family B may hold exact recall of **Fragment 2** (e.g., kernel timing race or theorem precondition) while emitting generic prose on Fragment 1.
     - The remaining $N-1$ models on each fragment often produce smooth, confident boilerplate.
   - Naive majority voting treats every `1/N` truth fragment as an outlier and **deletes all of them**, converging to plausible hallucination!
   - **Hybrid Relay Fix:** Combine **Model Council Round 1** (blind extraction with mandatory `exact_anchor` + `LOW_CONFIDENCE` boundary declarations) + **Fusion Sidekick Reality Probe** (test anchors against code/docs/REPL first) + **Multiagent Round-1.5 Seam Cross-Check** (pass verified Fragment 1 + Fragment 2 across 1–2 models to verify end-to-end compatibility).

4. **Correlated Family Priors vs. True Independence (`subagent` Routing Gotcha):**
   - Multiple samples from one model family share pretraining corpus cutoffs and RLHF blind spots (`HOMOGENEOUS_ECHO_WARNING`).
   - In Devin CLI specifically, `subagent_general` inherits the parent's exact model while `subagent_explore` resolves via the subagent router (and custom profiles use `model:`). Treating three `subagent_general` calls as a "3-model council" creates false confidence unless external multi-model CLIs (`devin --model`, `codex`, `claude`, `gemini`) or `model:`-pinned profiles provide genuine cross-family diversity.

5. **Ordered Rework Over Chair Micromanagement:**
   - When council synthesis uncovers 2–3 viable implementation hypotheses whose winner depends on runtime behavior, do **not** debate them in Round 2 prose—emit Cognition's Fusion rework pattern directly: *"Try alternatives in this order and keep the first that passes: (1) ..., (2) ..., (3) ..."*

6. **Two Concrete Composition Modes (`Council -> Fusion` vs. `Council of Fusions`):**
   - **Sequential `Council -> Fusion` (default, lowest cost):** `1x` neutral Fact Pack -> text-only cross-family Council (`claude-opus-5-5` + `gpt-6-2-sol` + `gemini-4-carbon` + optional `deepseek-v4-1-flash` / `kimi-k3-1-pro` long-tail seat) -> `1x` Devin Fusion `Lead + Sidekick` execution.
   - **Nested `Council of Fusions` (for heavy multi-hypothesis repo archaeology):** When each seat must independently trace deep call chains in Devin CLI, assign distinct `fusion-<lead>-sidekick-<sidekick>` IDs (e.g., `fusion-claude-fable-5-2-high-sidekick-swe-2-flash-max`, `fusion-gpt-6-2-astra-high-sidekick-gpt-6-luna-high`, `fusion-gemini-4-neon-high-sidekick-swe-2-flash-max`). `council_runner.py` parses the **Lead** before `-sidekick-` to measure true epistemic family diversity while letting cheap Sidekicks absorb mechanical tool calls.

---

## 2. Prompt Contracts and Niche Relay

### A. Blind Round-1 Seat Prompt Contract

Every Round-1 panelist receives the **identical neutral Fact Pack** with zero hints of the Chair's leaning or other seats' drafts:

```text
[ROLE]
You are Seat {seat_id} in a blind multi-model council (Track: {track}). Work strictly from first principles, the neutral Fact Pack below, and your verified domain priors. Do NOT hedge into generic averages; surface concrete mechanisms and exact technical anchors.

[QUESTION]
{question}

[NEUTRAL FACT PACK & HARD CONSTRAINTS]
{fact_pack_and_constraints}

[OPTIONAL ORTHOGONAL LENS]
Primary inspection angle (without ignoring fatal flaws elsewhere): {lens}

[REQUIRED OUTPUT SLOTS]
1. VERDICT & CAUSAL MECHANISM: Direct position/answer and step-by-step causal chain.
2. EXACT ANCHORS: Specific specs, RFC sections, APIs, registers, theorems, commands, or file:line invariants supporting your claim. Separate exact recall from inference.
3. UNCERTAINTY & LONG-TAIL SEAMS (LOW_CONFIDENCE / UNKNOWN): Explicitly name sub-questions or edge cases where your recall or the Fact Pack is incomplete. Never guess smoothly over obscure details.
4. STEELMAN COUNTER-CASE & FLIP CONDITION: Where would an equally strong specialist disagree with you, and what single observable test or datum would flip your verdict?
```

### B. Round-1.5 Niche Knowledge Relay & Falsification Brief (`<= 1` Pass)

Use **only** when Round 1 surfaces complementary partial fragments across models or an unverified high-specificity `1/N` anchor that local tools alone cannot settle:

```text
[ROUND-1.5 SEAM RELAY / FALSIFICATION CHECK]
Goal: Test compatibility and attempt falsification across complementary domain fragments surfaced in Round 1. Do NOT defer out of politeness; verify mechanics strictly.

- Question: {question}
- Verified / Candidate Fragment A (from Seat {seat_a}): {fragment_a}
- Verified / Candidate Fragment B (from Seat {seat_b}): {fragment_b}
- Open Seam / Disputed Premise: {open_seam}

Return strictly:
1. COMPATIBILITY / FALSIFICATION VERDICT: Does Fragment A + Fragment B hold end-to-end, or what exact invariant/version/precondition breaks it?
2. DECISIVE VERIFICATION CHECK: Minimal command, test, or primary-source lookup that settles the seam.
```

### C. Downstream Devin Fusion Execution Brief Template

Append whenever the council decision leads into code changes, debugging, or empirical validation:

```markdown
### Fusion Execution Brief (`Lead -> Sidekick`)
- **Objective:** <one-sentence outcome>
- **Hard Invariants (Must Hold):**
  - <invariant 1 — e.g., complexity, compatibility, security, or API contract>
- **Ordered Alternatives Ladder:** Try in this exact order and keep the first that passes all acceptance checks:
  1. <Primary approach backed by council convergence / verified 1/N anchor>
  2. <Fallback approach if Fault Line X manifests>
- **Pushback Trigger:** Pause and escalate back to Lead if <specific assumption fails during execution>.
- **Acceptance Check:** `<exact test / build / repro command and pass criterion>`
```

---

## 3. Runner Schemas and CLI Backends

### Non-Interactive Read-Only CLI Backend Matrix (`council_runner.py`)

`scripts/council_runner.py` allowlists the following non-interactive CLI runners (`shell=False`, `stdin=DEVNULL`, timeout-guarded, secret-redacted):

| `cli` Key | Non-Interactive Command Template | Typical Cross-Family `model` Examples |
| --- | --- | --- |
| `devin` | `devin -p --process-model in-process --permission-mode auto --respect-workspace-trust false --model <model> -- <prompt>` | `opus`, `gpt-6-2-sol-medium`, `gemini-4-carbon-high`, `kimi-k3-1-pro-high`, `deepseek-v4-1-flash-1017-high`, `fusion-...` |
| `codex` | `codex exec --ephemeral --skip-git-repo-check --color never -s read-only -m <model> <prompt>` | `gpt-5`, `o3`, `o4-mini` |
| `claude` | `claude -p --permission-mode plan --model <model> <prompt>` | `opus`, `sonnet` |
| `gemini` | `gemini -m <model> -p <prompt>` | `gemini-2.5-pro`, `gemini-3.1-pro` |
| `opencode` | `opencode run -m <model> <prompt>` | `anthropic/...`, `openai/...`, `google/...`, `deepseek/...` |
| `llm` | `llm -m <model> <prompt>` | Any configured Simon Willison `llm` provider model |
| `ollama` | `ollama run <model> <prompt>` | `deepseek-r1`, `qwen3`, `llama3.3`, `glm4` |

### `dispatch` Input Schema (`CouncilBrief`)

```json
{
  "question": "Why does CEC standby wake fail intermittently on Amlogic S905X4 Android 11 OTT firmware when HDMI hotplug races with deep suspend, and how should we fix it?",
  "track": "niche_relay",
  "fact_pack": [
    "SoC: Amlogic S905X4, kernel 5.4 vendor tree, Android 11 TV",
    "Symptom: ~8% of S3 suspend entries ignore CEC 0x04 <Image View On> wake until AC power cycle",
    "Observed log: hdmitx_cec_suspend completes 40ms after ao_cec irq mask when TV toggles HPD low"
  ],
  "constraints": [
    "Cannot replace signed BL30 SCP firmware blob on deployed boxes",
    "Fix must live in kernel driver, HAL, or init power sequence"
  ],
  "timeout_sec": 90,
  "seats": [
    {"seat_id": "seat_opus", "cli": "devin", "model": "opus", "lens": "Linux PM & wakeup_source race invariants"},
    {"seat_id": "seat_gpt", "cli": "codex", "model": "gpt-5", "lens": "HDMI-CEC / HPD spec & Amlogic ao_cec register sequence"},
    {"seat_id": "seat_gemini", "cli": "devin", "model": "gemini", "lens": "Android TV HAL & vendor S905X4 errata"}
  ]
}
```

### `ledger` Input Schema (`CouncilLedgerInput`)

```json
{
  "execution_tier": "tier_1_multi_cli_or_api",
  "relay_rounds_used": 1,
  "seats": [
    {"seat_id": "seat_opus", "model": "opus", "status": "ok"},
    {"seat_id": "seat_gpt", "model": "gpt-5", "status": "ok"},
    {"seat_id": "seat_gemini", "model": "gemini", "status": "ok"}
  ],
  "claims": [
    {
      "claim_id": "C1",
      "statement": "Hold a kernel wakeup_source across HPD debounce so late HPD-low cannot clear CEC wake armed state before BL30 handoff",
      "supporters": ["seat_opus", "seat_gpt"],
      "challengers": [],
      "specificity": "mechanism",
      "evidence_status": "tool_verified"
    },
    {
      "claim_id": "C2",
      "statement": "Amlogic meson_ao_cec_g12a clears CEC_INTR_MASKN when HPD drops if hdmi_cec_ctl bit 4 is unlatched prior to suspend_noirq",
      "supporters": ["seat_gpt"],
      "challengers": [],
      "specificity": "exact_anchor",
      "evidence_status": "unverified_assertion",
      "relay_seam": "Verify bitmask behavior in drivers/media/cec/platform/meson/ao-cec-g12a.c"
    },
    {
      "claim_id": "C3",
      "statement": "Disable deep S3 suspend globally and keep CPU in idle freeze",
      "supporters": ["seat_gemini"],
      "challengers": ["seat_opus"],
      "specificity": "mechanism",
      "evidence_status": "unverified_assertion",
      "fault_line_reason": "Trades 0.5W standby compliance against eliminating BL30 mailbox handoff entirely"
    }
  ]
}
```
