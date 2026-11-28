# Surgical Skill Refactoring Patterns

Consult only the section matching the diagnosed defect class. Keep every edit minimal-diff while preserving domain accuracy and public skill identities.

## 1. Pointer and DAG Surgery

### Fix SDO Workflow Leaks & Trigger Collisions (`D1`, `S010`, `S011`)
- **Symptom:** `description` summarizes internal steps (`covers step A, B, and C` / `——涵盖...流程`), tempting models to skip reading `SKILL.md`, or collides with adjacent skills.
- **Before (Defective):**
  ```yaml
  description: Video production skill — covers reading reference videos, measuring optical flow, writing HTML scenes, and rendering MP4s.
  ```
- **After (Polished):**
  ```yaml
  description: >-
    Use when creating, recreating, template-adapting, or exporting editable motion videos.
    For standalone image or audio generation use openmotion-media; repository code maintenance does not trigger video production.
  ```
- **Checklist:**
  1. Front-load `Use when...` naming concrete user intents, error symptoms, or target artifacts.
  2. Delete every summary of *how* the skill executes internally.
  3. Append 1 sentence routing near-miss sibling intents (`For X use Y`) and 1 clause excluding false-positive contexts (e.g., editing the repository itself).
  4. Use a folded `>-` YAML block whenever the text contains `: ` or `#`, and remove literal `<` or `>`.

### Break Cross-Skill Cycles & `../sibling` Coupling (`D5`)
- Extract shared contracts needed by two peer domain skills into a leaf foundation document with zero upward links.
- Replace fragile `../other-skill/references/foo.md` relative filesystem jumps with canonical skill invocation so single-skill standalone installs (`npx skills add` or symlinks) remain intact.

## 2. Progressive Disclosure and Fast Paths

### Add Step-0 Fast Paths & Complexity Tracks (`D3`)
- **Symptom:** The skill forces full multi-step reconstruction and heavy verification even when the user asks to run an unchanged template or adjust one copy string.
- **Pattern:** Insert `## 0. Fast Path & Track Selection` at the top of `SKILL.md`:
  - **No-op / Pristine Input Fast Path:** When input is already valid/complete and zero custom changes were requested, skip rebuild/re-test and deliver directly.
  - **Fast Track vs. Full Track:** Route simple single-file/zero-external-asset tasks through a single combined check; reserve multi-stage planning and visual review for complex or multi-asset builds.
  - **Delta Context Reads:** When task scope shifts mid-session, preserve locked user decisions and load only the set difference between newly required references and already-loaded references.

### Cure Body Sprawl (>350 Lines or >8,000-Char Routers)
- Apply the **Branching Test**: keep ordered steps executed on *every* run inside `SKILL.md`; push branch-specific matrices, provider quirks, and >50-line schemas into `references/<branch>.md` behind a 3-column conditional routing table (`Dimension | Condition | Read Only When Matched`).

## 3. Deterministic Gates and Stop-Loss

### Offload Prose Rules into Self-Locating `scripts/` (`D6`)
- Replace prose instructions asking the LLM to count characters, check math/discounts, validate YAML/JSON schemas, or verify links/anchors with a zero-dependency script under `scripts/`.
- Bundled scripts must locate sibling files relative to themselves (`Path(__file__).resolve().parent` in Python, `new URL('.', import.meta.url)` in ESM) — never hardcode `/Users/...`, `/home/...`, or `~/.claude/skills/...`.

### Pair Every Gate with Anti-Reward-Hacking & Stop-Loss
- **Anti-Reward-Hacking (Hard Fails):** Explicitly forbid creating disconnected stub files just to satisfy a test runner, lowering assertion thresholds, deleting failing checks, or fabricating metrics after a tool timeout.
- **Stop-Loss (Round Cap):**
  - `P0` (crashes, corrupted state, violated invariants): block delivery; if the core mechanism fails `P0` across **2 consecutive rounds**, pivot the approach rather than tweaking parameters.
  - `P1` (usability, layout, balance): cap at **3 fix rounds**, then hand off remaining items transparently.
  - `P2` (minor polish): do not loop; log up to 5 highest-impact items under `Known gaps (P2)` for the user to choose.

### Overlap Slow Async Jobs with Local Work
- When a workflow dispatches slow external jobs (multimodal generation, remote builds, batch runs), submit independent jobs concurrently with deterministic `requestId` / idempotency keys immediately after authorization, build local logic while jobs run, and integrate/inspect in one consolidated pass.

## 4. Interaction UX and Scaffolding Hygiene

### Enforce Ask-Once Batching & Hard Spend/Publish Pauses
1. **Scan workspace first:** Never ask questions already answered by `README.md`, `package.json`, git history, or config files.
2. **Own technical defaults:** Specify a deterministic fallback chain for tool/provider/model choices (`Choose X yourself; do not ask the user to choose`).
3. **One batched question + hard consent gate:** Combine genuine business ambiguities and paid/external/destructive approvals into **one single turn** (offering a `"you decide"` option on creative choices). Never bypass an unanswered spend/publish confirmation with silent local/mocked substitutes.

### Black-Box User Replies & Honest Evidence Split
- Keep user-facing replies free of internal skill names, MCP tool identifiers, `references/` paths, or internal rule codes unless the user is explicitly auditing the skill itself.
- Separate **Verified** (backed by observed command/tool output in the current session) from **Unverified** (human feel, subjective visual/audio quality, unexercised production environments).

### Tag Temporary Model Workarounds (`model-scaffolding`, `D7`)
- Separate permanent **Domain Invariants** from temporary guardrails added for current model quirks using balanced, dated HTML comments:
  ```html
  <!-- model-scaffolding: reason="mid-tier models call write before reading target revision" review-on="next-frontier-model" -->
  Read the target file and capture `expectedRevision` in a completed turn step before calling write.
  <!-- /model-scaffolding -->
  ```
