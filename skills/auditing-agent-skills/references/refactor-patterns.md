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
- Replace fragile `../other-skill/references/foo.md` relative filesystem jumps with canonical skill invocation so single-skill standalone installs remain intact.

## 2. Progressive Disclosure and Fast Paths

### Add Step-0 Fast Paths & Complexity Tracks (`D3`)
- **No-op / Pristine Input Fast Path:** When input is already valid/complete and zero custom changes were requested, skip rebuild/re-test and deliver directly.
- **Fast Track vs. Full Track:** Route simple single-file/zero-external-asset tasks through a single combined check; reserve multi-stage planning and visual review for complex builds.
- **Delta Context Reads:** When task scope shifts mid-session, preserve locked user decisions and load only the difference between newly required references and already-loaded references.

### Isolate Heavy Outputs via Subagents or Script Aggregation
- **Symptom:** Dumping raw test logs, multi-file diffs, API pagination payloads, or 20+ file scans into the main trajectory dilutes attention and burns context.
- **Refactor:** Instruct the skill to delegate high-volume read/scan/log-triage tasks (`>200` lines / `>8 KB` or `>10` targets) to an isolated read-only **subagent** returning a bounded table (`target | status | file:line | minimal action`), or aggregate via a local script writing full raw output to a temp file and printing only summary counts + failing lines.

### Prune to Decision-Changing Sentences Only (`>350` Lines or `>8,000`-Char Routers)
- Apply the **Decision Test** sentence by sentence: *"Would removing this sentence change what a frontier model actually decides or executes?"* Delete generic exhortations ("be thorough", "write clean code", "handle edge cases carefully") outright rather than rewording them.
- Push branch-specific matrices, provider quirks, and `>50`-line schemas into `references/<branch>.md` behind a 3-column conditional routing table (`Defect/Branch | Trigger Condition | Disclosed Slice`).

## 3. Deterministic Gates and Stop-Loss

### Encode Rules into Structure on Second Write (`D6`, `D9`)
- **The Second-Write Law:** Whenever the same constraint is written a second time—or governs counts, character budgets, naming formats, YAML/JSON schemas, `#anchor` links, or step order—**convert it into a linter, static type, JSON Schema, fixed CLI pipeline, or zero-dependency `scripts/` check, and delete the prose sentence**.
- Bundled scripts must locate sibling files relative to themselves (`Path(__file__).resolve().parent` in Python, `new URL('.', import.meta.url)` in ESM) — never hardcode `/Users/...`, `/home/...`, or `~/.claude/skills/...`.

### Make Completion Provable on Real Artifacts (`D8`, `--verify-against`)
- **Symptom:** Completion relies on fuzzy prose ("verify everything looks good") or trusts the Agent's self-reported summary.
- **Refactor:**
  1. Define **completion** upfront as explicit, machine-checkable predicates on real output files, exit codes, or state snapshots.
  2. Pair every workflow with a reproducible verification script inspecting the actual produced artifact on disk (e.g., `--save-baseline` before edits -> `--verify-against` after edits).
  3. **Anti-Reward-Hacking (Hard Fails):** Forbid creating disconnected stub files to fake green runs, relaxing thresholds/assertions, gutting trigger descriptions (`V004_DESCRIPTION_GUTTED`), deleting failing test cases, or fabricating metrics after tool timeouts.
  4. **Stop-Loss (Round Cap):** Block on `P0` (pivot approach if the core mechanism fails `P0` across **2 consecutive rounds**); cap `P1` fixes at **3 rounds**; log `P2` polish items under `Known gaps (P2)` (max 5 items) without looping.

### Overlap Slow Async Jobs with Local Work
- Submit independent slow external jobs concurrently with deterministic `requestId` / idempotency keys immediately after authorization, build local logic while jobs run, and integrate/verify in one consolidated pass.

## 4. Interaction UX and Scaffolding Hygiene

### Gate Humans on Irreversible Actions Only (`D10`)
- **Autonomous Reversible Execution:** Local file edits, git worktree branches, `references/` splits, `scripts/` creation, dry-runs, and test/linter runs are **reversible**—the Agent must advance them end-to-end without asking step-by-step permission or making the user pick technical defaults (`Choose providers/tools yourself; do not ask the user`).
- **Single Batched Gate for Irreversible Actions:** Ask the human **only** before irreversible operations—breaking public skill/API identifiers, external publishing/pushing/messaging, paid credit/API spend, or deleting untracked/unrecoverable data. Combine any genuine business ambiguity with irreversible consent into **one** turn and wait; never bypass an unanswered spend/publish gate with silent mocked substitutes.

### Black-Box User Replies & Honest Evidence Split
- Keep user-facing replies free of internal skill names, MCP tool identifiers, `references/` paths, or internal rule codes unless the user is explicitly auditing the skill itself.
- Separate **Verified** (proved by reproducible script output on real artifacts in this session) from **Unverified** (human feel, subjective visual/audio taste, unexercised production environments).

### Tag Temporary Model Workarounds (`model-scaffolding`, `D7`)
- Separate permanent **Domain Invariants** from temporary guardrails added for current model quirks using balanced, dated HTML comments:
  ```html
  <!-- model-scaffolding: reason="mid-tier models call write before reading target revision" review-on="next-frontier-model" -->
  Read the target file and capture `expectedRevision` in a completed turn step before calling write.
  <!-- /model-scaffolding -->
  ```
