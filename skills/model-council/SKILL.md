---
name: model-council
description: >-
  Use when the user asks for Model Council, wants a synthesized multi-model discussion or second opinion, asks how multiple models answer a contested question, or faces a niche/obscure long-tail domain needing cross-model knowledge-distribution relay (多模型讨论综合结果、询问多个模型看法、冷门领域跨模型知识分布接力). For architecting multi-agent codebases use orchestrating-multi-agent-workflows; for payoff/tail math use analyzing-risk-decisions.
---

# Model Council (Fusion-Enhanced Multi-Model Synthesis & Knowledge Relay)

Run an epistemically independent multi-model council that fuses **Model Council** (blind cross-family deliberation + `Convergence / Divergence / Unique 1-of-N` mapping), **Multiagent** (targeted cross-examination of conflicting assumptions), and **Devin Fusion** (`1x` neutral Sidekick reconnaissance, persistent KV-cache discipline, constraint-first briefs, and ordered fallback verification).

## 0. Fast Path, Track Selection & Conditional References

1. **Single-Fact Fast Path:** When a question has a deterministic local answer verifiable by one workspace file read, compiler/test run, or authoritative spec check—and the user did **not** explicitly ask to query/compare multiple models—verify and answer directly without spawning a council.
2. **Infer the Council Track** from the user's intent without asking:
   - **Track A — Judgment & Trade-off Council (`judgment`):** Ambiguous architecture, strategy, or risk calls where smart specialists disagree and *judgment is the deliverable*.
   - **Track B — Multi-Model Inquiry (`comparison`):** User explicitly asks how different models answer or weigh in on a prompt, wanting both per-model stances and a synthesized verdict.
   - **Track C — Niche Knowledge-Distribution Relay (`niche_relay`):** Obscure hardware/firmware quirks, rare protocols/RFCs, legacy internals, or cross-disciplinary long-tail domains where no single model holds the full pretraining tail—extract `1/N` partial recalls blindly, verify against primary artifacts, and relay verified fragments across seams.

Load **only** the matching reference section when needed:

| Dimension | Condition | Read Only When Matched |
| --- | --- | --- |
| **Paradigm Architecture & Trade-offs** | Explaining or applying mutual coverage across Model Council, Multiagent, and Devin Fusion | [1-three-paradigm-synthesis](references/paradigm-synthesis-and-schemas.md#1-three-paradigm-synthesis) |
| **Seat, Relay & Chair Prompts** | Constructing blind Round-1 prompts, Round-1.5 niche knowledge relays, or Fusion handoff briefs | [2-prompt-contracts-and-niche-relay](references/paradigm-synthesis-and-schemas.md#2-prompt-contracts-and-niche-relay) |
| **CLI Dispatch & Ledger JSON Schemas** | Running `scripts/council_runner.py` `dispatch` or `ledger` with custom JSON payloads | [3-runner-schemas-and-cli-backends](references/paradigm-synthesis-and-schemas.md#3-runner-schemas-and-cli-backends) |

*Completion criterion:* Fast-path eligibility and active track (`judgment` | `comparison` | `niche_relay`) locked before probing seats.

## 1. Environment Probe, Seat Selection & Consent Gate

1. Resolve `SKILL_DIR` from this skill's `Base directory` header or folder containing `SKILL.md`. Run the read-only, secret-safe capability probe (pass `--discover-models` when `devin` is available to inspect live cross-family and `fusion-*` Lead catalogs):
   ```bash
   python3 "$SKILL_DIR/scripts/council_runner.py" probe --discover-models
   ```
2. Select the highest-diversity execution tier automatically (own technical defaults; do not ask the user to pick CLI flags):
   - **Tier 1 — Cross-Family Multi-Model (`preferred`):** Dispatch **3 seats** (scale to **4–5** for wide comparisons or multi-seam `niche_relay`; hard cap **8**) across **distinct model families** (e.g., Anthropic + OpenAI + Google + Open-Weight `deepseek`/`kimi`/`glm`/`qwen`/`swe`) via callable non-interactive CLIs (`devin -p --process-model in-process --model ...`, `codex exec --ephemeral -s read-only -m ...`, `claude -p`, `gemini`, `opencode`, `llm`, `ollama`), `model:`-pinned subagent profiles, or configured MCP hubs. For deep multi-hypothesis codebase probes in Devin CLI, seats may also use `fusion-<lead>-sidekick-<sidekick>` pairings with distinct Lead families (**Council of Fusions**).
   - **Tier 2 — Host Isolated Subagents (`partial diversity`):** When external CLIs are unavailable or restricted, spawn parallel read-only subagents with fresh contexts (`subagent_explore` + distinct profiles). Record exact model families—note that Devin `subagent_general` inherits the parent model while `subagent_explore` uses the subagent router.
   - **Tier 3 — Single-Model Counterfactual Fallback (`degraded`):** When host policy or sandboxing forbids both external CLIs and subagents, run 3 explicit orthogonal passes (e.g., *Mechanism/Spec Anchor*, *Adversarial Falsifier*, *Operational/Edge-Case Prior*) inline and label the run `tier_3_single_model_counterfactual`.
3. **Ask-Once & Spend Gate:** Inspect workspace files first. Pause in **at most one batched turn** only when (a) invoking paid external CLIs/APIs requires user approval under host rules (preview via `council_runner.py dispatch --dry-run`), or (b) an unstated business constraint flips the target problem.

*Completion criterion:* Execution tier (`tier_1` | `tier_2` | `tier_3`) and seat lineup (`2–8` seats with explicit model-family tags) determined.

## 2. Fusion Fact-Pack Compression (1x Neutral Reconnaissance)

Apply Devin Fusion's KV-cache and reconnaissance discipline before fan-out:

1. Gather objective workspace facts **once** (`<= 1,500` tokens): exact user question, relevant `file:line` snippets, versions, logs, and hard constraints. Avoid making $N$ models redundantly crawl the same repository files or ingest the raw conversation transcript.
2. **Zero Opinion Contamination:** State constraints, evidence, and open questions—strip the Chair's provisional hypothesis or preferred solution (`Fable`-style constraint brief, never `Opus`-style answer dictation). Verify zero neutrality warnings via `council_runner.py dispatch --dry-run` when dispatching via JSON.

*Completion criterion:* One self-contained, opinion-free Fact Pack prepared for identical Round-1 distribution.

## 3. Blind Round-1 Panel Execution

Dispatch all seats **in parallel with zero lateral visibility** so Round-1 priors remain uncontaminated (no anchoring or herd cascades):

- For Tier 1 CLI seats, pass a `CouncilBrief` JSON over stdin (`--input -`) to `python3 "$SKILL_DIR/scripts/council_runner.py" dispatch --input -` (read [3-runner-schemas-and-cli-backends](references/paradigm-synthesis-and-schemas.md#3-runner-schemas-and-cli-backends) for schema).
- Require every seat to return four structured slots (templates in [2-prompt-contracts-and-niche-relay](references/paradigm-synthesis-and-schemas.md#2-prompt-contracts-and-niche-relay)):
  1. **Verdict & Causal Mechanism:** Direct answer and concrete mechanism.
  2. **Specific Anchors (`exact_anchor`):** Exact spec clauses, APIs, registers, equations, `file:line` invariants, or historical edge cases recalled from pretraining/evidence.
  3. **Explicit Gaps (`LOW_CONFIDENCE / UNKNOWN`):** Which piece of the domain this seat is uncertain about instead of smoothing over long-tail holes.
  4. **Steelman Flip Condition:** Strongest counter-argument from a peer specialist and the single check that would reverse this seat's bet.

*Completion criterion:* Raw Round-1 outputs (plus any seat timeouts/errors) captured without cross-seat leakage.

## 4. Epistemic Ledger, Anti-Majority-Vote Law & Niche Knowledge Relay

1. Extract atomic claims across seats and run the deterministic epistemic classifier:
   ```bash
   python3 "$SKILL_DIR/scripts/council_runner.py" ledger --input - --format markdown <<'EOF'
   { ... }
   EOF
   ```
2. **Enforce the Anti-Majority-Vote Law on `1/N` Surfaces:**
   - Same-family agreement (`HOMOGENEOUS_ECHO_WARNING`) counts as **one correlated family prior**, never independent cross-model proof.
   - **Never discard a concrete `1/N` claim (`exact_anchor` or `mechanism`) by majority vote.** In obscure/long-tail domains (`niche_relay`), 1 model recalling a rare register/RFC/compiler rule while $N-1$ models emit generic boilerplate looks like a `1 vs N-1` minority—erasing it destroys the council's primary tail signal.
3. **Bounded Round-1.5 Verification & Knowledge Relay (`<= 1` pass):**
   Trigger Round 1.5 **only** when the ledger flags `UNIQUE_1_OF_N_RELAY_CANDIDATE`, complementary partial domain pieces across models, or a falsifiable `DISPUTED_FAULT_LINE`:
   - **Reality Probe First (Fusion Sidekick Rule):** Check testable anchors directly against repo code, docs, compiler/REPL, or search (`tool_verified` -> `VERIFIED_MINORITY_GOLD`; disproved -> `FALSIFIED_DROPPED`).
   - **1-Hop Seam Relay (Multiagent Cross-Check Rule):** When Model A supplies verified Piece 1 (e.g., protocol framing) and Model B supplies Piece 2 (e.g., state-machine timing quirk), send **only** `{verified anchors + exact open seam}` (`<= 600` tokens) to 1–2 complementary seats to verify interface compatibility or attempt falsification. Re-run `council_runner.py ledger` to confirm all invariants pass.

*Completion criterion:* `council_runner.py ledger` reports `invariants_all_passed: true`, with every `1/N` anchor classified as verified, falsified, or explicitly bounded.

## 5. Anti-Reward-Hacking & Stop-Loss Guardrails

- **Hard Fails:**
  - Never fabricate or paraphrase outputs for a model/CLI seat that timed out, lacked credentials, or was not invoked; list failed seats transparently.
  - Never present `tier_3_single_model_counterfactual` or single-family echoes as "multi-model consensus."
  - Never drop a specific `1/N` long-tail anchor solely because $N-1$ models omitted it, and never label an unverified `1/N` recall as `[VERIFIED]` without primary-source or tool confirmation.
  - Never pass API keys, bearer tokens, or private credentials in council prompts or command arguments.
- **Stop-Loss:** Cap deliberation strictly at **Round 1 (blind) + at most 1 Round-1.5 relay/probe**. Do not run open-ended multi-round free-text debates (Data Processing Inequality degrades signal and inflates sycophancy). If a CLI seat fails or times out once, proceed with remaining seats and note coverage limits.

## 6. Output Contract

Respond in the user's language with these exact sections in order (keep internal skill/script paths out of user-facing prose unless asked):

1. **Council Verdict & Switching Boundary (综合裁决与切换边界):** Direct recommendation upfront, actual seats/models & execution tier run (`Cross-Family Council` / `Isolated Subagents` / `Single-Model Counterfactual Fallback`), and the exact condition or datum that would flip the verdict.
2. **Epistemic Synthesis Map (三域认知图谱):**
   - **Convergence (跨模型独立共识):** Conclusions independently reached across distinct model families (flagging any single-family echo limits).
   - **Fault Lines & Disagreements (核心分歧与冲突拆解):** Where seats diverged, the underlying assumption or evidence split, and how reality checks resolved or bounded it.
   - **Unique `1/N` Surfaces & Knowledge Relay (独有盲区点亮与知识分布接力):** Minority anchors rescued from majority-vote erasure and cross-model long-tail pieces stitched together, each tagged `[VERIFIED]`, `[PLAUSIBLE — NEEDS CHECK]`, or `[FALSIFIED — EXCLUDED]`.
3. **Per-Seat Snapshot (各席位独立摘要, concise):** Compact table or bullets of `Seat / Model Family | Core Stance | Unique Anchor Contributed | Key Blind Spot / Caveat` (expand full per-model answers when Track B `comparison` is requested).
4. **Fusion Execution Brief (落地执行契约, include whenever code/action/verification follows):** Spec-grade `Lead -> Sidekick` brief with **Hard Constraints**, **Ordered Alternatives Ladder** (*"Try alternatives in this order and keep the first that passes"*), and **Observable Acceptance Check**.
