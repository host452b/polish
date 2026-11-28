---
name: auditing-agent-skills
description: >-
  Use when scanning, linting, diagnosing, or surgically refactoring existing SKILL.md, AGENTS.md, or CLAUDE.md packages for SDO workflow-summary shortcuts, broken links or #anchors, cross-skill DAG cycles, context sprawl, missing stop-loss gates, KV-cache invalidation, or flat skill benefit (扫描与改善当前 Skill 缺陷、排查触发失灵与跳步、裁剪上下文膨胀、补齐验证门禁与四层收益漏斗诊断). For drafting prose from scratch use mattpocock-writing-for-agents; for subagent pressure-testing use superpowers-writing-skills.
---

# Auditing and Polishing Agent Skills

Audit existing `SKILL.md`, `agents/openai.yaml`, `references/`, `scripts/`, and `AGENTS.md` packages with deterministic compiler checks and the 4-layer benefit funnel, and—when improvements are requested—apply minimal-diff surgical refactors and re-verify before handoff.

## 0. Mode Selection & Fast Path

Infer the operating mode from the user's request:
- **Audit Mode (read-only):** User asks to scan, lint, check, or diagnose skills. Run §2 and return the Output Contract (§5) with zero file edits.
- **Polish Mode (audit + improve):** User asks to improve, polish, refactor, fix, or harden skills. Run §1 -> §2 -> Surgical Refactor (§3) -> Re-verify (§3.3).
- **Clean Fast Path:** If `scripts/audit_skills.py` reports `0 ERROR / 0 WARN` and §2 finds zero `P0`/`P1` operational gaps, return `▶︎▶︎PASS_SKILL_AUDIT▶︎▶︎` immediately without cosmetic rewrites.

Load **only** the matching reference sections when a defect class appears (never read all references unconditionally):

| Detected Defect Class | Condition | Read Only When Matched |
| --- | --- | --- |
| **Trigger / SDO / Sibling Collision / DAG** | Workflow leaked in `description`, missing negative boundaries, or cross-skill `../` links | [1-pointer-and-dag-surgery](references/refactor-patterns.md#1-pointer-and-dag-surgery) |
| **Context Sprawl / Missing Fast Path** | `SKILL.md` > 350 lines, thin router > 8,000 chars, or no Step-0 bypass / Fast-vs-Full track | [2-progressive-disclosure-and-fast-paths](references/refactor-patterns.md#2-progressive-disclosure-and-fast-paths) |
| **Weak Checks / Reward-Hacking / Retry Loops** | Prose-only math/schema checks, hardcoded script paths, or missing anti-cheating & stop-loss caps | [3-deterministic-gates-and-stop-loss](references/refactor-patterns.md#3-deterministic-gates-and-stop-loss) |
| **Chatty UX / Leaked Jargon / Stale Sediment** | Piecemeal questions, leaked internal names in replies, or undated `model-scaffolding` rules | [4-interaction-ux-and-scaffolding-hygiene](references/refactor-patterns.md#4-interaction-ux-and-scaffolding-hygiene) |
| **Empirical Benchmark Drift (`D10`)** | Auditing `ai-agent-book` adaptations or extracting skills from human before/after diffs | [ai-agent-book-skills-audit.md](references/ai-agent-book-skills-audit.md) |

## 1. Environment Self-Resolution & Ask-Once Gate

1. Inspect target skill files, sibling skills, plugin manifests, and repo `AGENTS.md` conventions first; infer target hosts (Claude Code, Codex, Devin, Cursor) without asking.
2. In Polish Mode, ask **at most once** in a single batched turn **only** when splitting a skill would change public `name` identifiers or deleting conflicting rules requires an owner policy decision. Stop and wait when public names or destructive deletions depend on the answer.

## 2. Deterministic Scan & Operational Audit

<!-- model-scaffolding: reason="prevent skipping deterministic scanner and jumping straight to subjective prose edits on mid-tier hosts" review-on="next-frontier-model" -->
1. **Run the deterministic compiler first:** Execute `python3 scripts/audit_skills.py <target-dir>` (resolved relative to this skill's directory) in a completed step before manual review or editing. Capture every `ERROR` and `WARN` (`S001`–`S016`, `D1`, `D3`–`D7`: plain-YAML `: `/` #` hazards, `<`/`>` in `description`, SDO leaks, 8,000-char router budgets, >350-line sprawl, broken links/`#anchor` slugs, cross-skill DAG cycles/`../sibling` links, hardcoded `scripts/` paths, and malformed `model-scaffolding` blocks).
<!-- /model-scaffolding -->
2. **Audit the 6 Operational Laws & KV-Cache/Injection Safety:**
   - **Pointer Purity (`D1`):** `Use when...` triggers, concrete symptoms, sibling redirects (`For X use Y`), and repo-maintenance exclusions—zero workflow summaries in `description`.
   - **Hierarchy, Fast Path & Async Overlap (`D3/D4/D9`):** Step-0 bypass for unchanged/ready inputs, `Fast` vs. `Full` track split, conditional reference table, and upfront concurrent dispatch (with idempotency keys) for slow external jobs.
   - **Ask-Once & Consent Pause:** Workspace facts read first, technical defaults owned internally, human questions batched into 1 turn, and hard pauses enforced before paid/external/destructive actions.
   - **Deterministic Scripts, Anti-Hacking & Stop-Loss (`D5/D6`):** Repeatable math/schema/measurement offloaded to self-locating `scripts/`; positive output contracts over negation lists; every check paired with **Hard Fails** (no stubs, no lowered thresholds) and a **Stop-Loss Cap** (`P0` block / 2-round pivot; `P1` <=3 rounds; `P2` -> `Known gaps`).
   - **KV-Cache, Injection & UX Hygiene (`D7/D8`):** Flag per-turn `system` mutations, `tools` reordering, or unescaped external inputs; strip internal skill/tool/path names from user replies; split **Verified** vs. **Unverified** claims; tag temporary model workarounds with `<!-- model-scaffolding: reason="..." review-on="..." -->`.
3. **Diagnose the 4-Layer Benefit Funnel (`D10`):** When benchmark scores stall, isolate which layer broke instead of rewriting prose blindly: *1. Proposal Validity* (force-injected replay) -> *2. Activation Rate* (`description` trigger) -> *3. Compliance Rate* (step/check completion) -> *4. Holdout Gain* (Boundary gain without Retention regression).

## 3. Minimal-Diff Refactoring & Re-Verification (Polish Mode)

1. Preserve directory name, frontmatter `name`, and `agents/openai.yaml` `display_name`; prune model no-ops ("be thorough") outright rather than rewording.
2. Disclose >80-line branch tables/examples into `references/<topic>.md` behind conditional table pointers, and extract deterministic checks into zero-dependency self-locating `scripts/`.
3. Re-run `python3 scripts/audit_skills.py <target-dir>` (plus applicable repo validators and `git diff --check`) until structural `ERROR` count reaches `0`.

## 4. Anti-Reward-Hacking & Stop-Loss

- **Hard Fails:** Never silence broken-link or `#anchor` errors by deleting needed domain guidance without migrating it; never strip concrete triggers just to shorten `description`; never invent empirical numbers.
- **Stop-Loss:** Cap polish passes at **2 rounds**. Log ambiguous domain trade-offs or missing external runtimes as `P2` items instead of guessing.

## 5. Output Contract

Return these exact sections in order:
1. **Scanner Summary:** Scanned skill count, `ERROR` and `WARN` counts (before -> after in Polish Mode), and exact command run.
2. **Prioritized Defect & Polish Ledger:** Markdown table `Severity (P0-P2) | Rule ID | Location (file:line) | Evidence ([VERIFIED]/[INFERRED]) | Minimal-Diff Fix (Applied or Proposed)`.
3. **Funnel, Orthogonality & Verification Split:** Sibling trigger collision check, primary bottleneck layer (`Validity / Activation / Compliance / Holdout`), and **Verified** vs. **Unverified** boundary (plus up to 5 `P2` items).
4. **Verdict:** `▶︎▶︎PASS_SKILL_AUDIT▶︎▶︎` (`0` P0/P1 defects; or `▶︎▶︎PASS_SKILL_POLISH▶︎▶︎` after verified edits) or `▶︎▶︎FIX_BEFORE_INSTALL▶︎▶︎` followed by one line naming the #1 blocker.

## Disclosed Resources

- Run `scripts/audit_skills.py` for zero-dependency YAML hazard, SDO leak, `#anchor`, cross-skill DAG, script self-location, and `model-scaffolding` checks.
- Read [references/refactor-patterns.md](references/refactor-patterns.md) for conditional surgical refactoring patterns across pointers, fast paths, gates, and UX hygiene.
- Read [references/ai-agent-book-skills-audit.md](references/ai-agent-book-skills-audit.md) for the `D1`–`D10` defect taxonomy, human diff extraction rules, and the 22-skill `ai-agent-book` audit.
