---
name: auditing-agent-skills
description: >-
  Use when scanning, linting, diagnosing, or surgically refactoring existing SKILL.md, AGENTS.md, or CLAUDE.md packages for SDO shortcuts, broken links or #anchors, cross-skill DAG cycles, repeated prose rules, unprovable completion criteria, or flat skill benefit (扫描与改善 Skill 缺陷、把重复文字规则转化为检查脚本、验证真实产物闭环与四层收益漏斗诊断). For drafting prose from scratch use mattpocock-writing-for-agents; for subagent pressure-testing use superpowers-writing-skills.
---

# Auditing and Polishing Agent Skills

Audit and refactor `SKILL.md`, `agents/openai.yaml`, `references/`, `scripts/`, and `AGENTS.md` packages so structural rules live in deterministic scripts, completion is proved against real artifacts, and prose retains only sentences that change Agent decisions.

## 0. Mode, Subagent Offload & Fast Path

- **Audit Mode (read-only):** Scan, diagnose, and emit §4 with zero file edits. *Done when:* `scripts/audit_skills.py` has run in this session and every `P0`/`P1` finding cites a real `file:line` or observable funnel failure.
- **Polish Mode (inspect + improve):** Save baseline -> apply surgical edits -> prove improvement on disk via `--verify-against`. *Done when:* `--verify-against` exits `0` (`PASS_POLISH_VERIFICATION`) alongside repository validators, with zero relaxed checks or gutted triggers.
- **Clean Fast Path:** When `scripts/audit_skills.py` reports `0 ERROR / 0 WARN` and §2 finds zero `P0`/`P1` decision gaps, return `▶︎▶︎PASS_SKILL_AUDIT▶︎▶︎` immediately without cosmetic edits.
- **Heavy-Output Isolation:** When scanning `>10` skills or inspecting `>200` lines / `>8 KB` of logs or diffs, delegate the read-only pass to a subagent (when host-supported) or filter via `--json` so raw bulk output never enters the main context window.

Load **only** the matching reference slice when its defect class appears:

| Defect Class | Trigger Condition | Disclosed Slice |
| --- | --- | --- |
| **Pointer / SDO / DAG** | Workflow leaked in `description`, missing exclusions, or cross-skill `../` links | [1-pointer-and-dag-surgery](references/refactor-patterns.md#1-pointer-and-dag-surgery) |
| **Sprawl / Heavy Output / Fast Path** | `>350` lines, missing Step-0 bypass, or raw bulk outputs dumped into main context | [2-progressive-disclosure-and-fast-paths](references/refactor-patterns.md#2-progressive-disclosure-and-fast-paths) |
| **Repeated Prose / Unprovable Completion** | Rules stated twice in text, prose-only checks, fuzzy "done" claims, or missing stop-loss | [3-deterministic-gates-and-stop-loss](references/refactor-patterns.md#3-deterministic-gates-and-stop-loss) |
| **Permission Nags / Jargon / Sediment** | Asking approval on reversible edits, leaked internal names, or undated `model-scaffolding` | [4-interaction-ux-and-scaffolding-hygiene](references/refactor-patterns.md#4-interaction-ux-and-scaffolding-hygiene) |
| **Empirical Drift (`D10`)** | Auditing `ai-agent-book` adaptations or extracting rules from human before/after diffs | [ai-agent-book-skills-audit.md](references/ai-agent-book-skills-audit.md) |

## 1. Irreversibility-Only Human Gate

Advance all **reversible** work (git-tracked edits, disclosing `references/`, extracting `scripts/`, running tests and linters) autonomously without asking permission. Pause with **one** batched question **only** before **irreversible** actions: renaming or deleting public skill IDs, removing domain rules with ambiguous business intent, publishing/pushing externally, incurring paid API spend, or deleting untracked user files.

## 2. Structural Scan & Decision-Only Audit

<!-- model-scaffolding: reason="prevent skipping deterministic scanner and jumping straight to subjective prose edits on mid-tier hosts" review-on="next-frontier-model" -->
1. **Run the compiler first:** Execute `python3 scripts/audit_skills.py <target-dir>` (in Polish Mode, add `--save-baseline <tmp-baseline.json>` first) in a completed step before manual review or editing.
<!-- /model-scaffolding -->
2. **Audit what the script cannot prove semantically:**
   - **Provable Completion over Self-Report:** Every workflow must state checkable completion conditions up front and verify real output artifacts with a runnable command/script—never trust Agent self-reporting or allow relaxing assertions/thresholds to declare success.
   - **Structure over Text (Encode on Second Write):** Whenever a requirement appears a second time—or checks counts, formats, schemas, links, or call order—convert it into a lint rule, type, schema, fixed template, or `scripts/` check and **delete the prose sentence**. Prune every sentence in `SKILL.md` that does not alter a model decision vs. default behavior.
   - **Subagent & Irreversibility Discipline:** Offload high-volume command/file outputs to subagents or scripts; gate human confirmation strictly on irreversible side effects while driving reversible steps end-to-end; cap `P1` repair loops at `<=3` rounds (`P2` -> `Known gaps`).
   - **KV-Cache, Injection & Funnel Diagnosis:** Flag per-turn `system`/`tools` mutations and untrusted script/input surfaces; isolate benchmark stalls across the **4-Layer Funnel** (*1. Proposal Validity -> 2. Activation Rate -> 3. Compliance Rate -> 4. Holdout Gain*).

## 3. Surgical Refactor & Artifact Proof (Polish Mode)

1. Convert repeated or mechanical prose rules into self-locating `scripts/` or schemas and delete the superseded text; disclose `>80`-line branch tables into `references/<topic>.md`; tag temporary model-quirk workarounds with `<!-- model-scaffolding: reason="..." review-on="..." -->`.
2. **Prove completion on real artifacts** (cap at **2** polish passes): run `python3 scripts/audit_skills.py <target-dir> --verify-against <tmp-baseline.json>` plus repository validators and `git diff --check`. Never gut `description` triggers or delete needed domain rules to silence warnings.

## 4. Output Contract

Return these exact sections in order:
1. **Scanner & Baseline Proof:** Scanned count, `ERROR`/`WARN` counts (`before -> after` + `--verify-against` exit status in Polish Mode), and exact command(s) run.
2. **Prioritized Defect & Structuralization Ledger:** Markdown table `Severity (P0-P2) | Rule ID | Location (file:line) | Evidence ([VERIFIED]/[INFERRED]) | Structural / Minimal-Diff Fix`.
3. **Funnel, Orthogonality & Verification Split:** Sibling trigger collision check, bottleneck layer (`Validity / Activation / Compliance / Holdout`), and **Verified** (script-proved on real artifacts) vs. **Unverified** (live activation/compliance) items, plus at most 5 `P2` items.
4. **Verdict:** `▶︎▶︎PASS_SKILL_AUDIT▶︎▶︎` (`0` P0/P1 defects; or `▶︎▶︎PASS_SKILL_POLISH▶︎▶︎` only when `--verify-against` exits `0`) or `▶︎▶︎FIX_BEFORE_INSTALL▶︎▶︎` followed by one line naming the #1 blocker.
