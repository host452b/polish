---
name: auditing-agent-skills
description: >-
  Use when scanning, linting, diagnosing, or surgically refactoring existing SKILL.md, AGENTS.md, or CLAUDE.md packages for SDO shortcuts, broken links or #anchors, cross-skill DAG cycles, context sprawl, repeated prose rules, unprovable completion, KV-cache busting, prompt injection, or flat skill benefit (扫描与改善 Skill 缺陷、重复文字转检查脚本、真实产物闭环与四层收益漏斗诊断). For drafting prose from scratch use mattpocock-writing-for-agents; for subagent pressure-testing use superpowers-writing-skills.
---

# Auditing and Polishing Agent Skills

Audit and refactor existing `SKILL.md`, `agents/openai.yaml`, `references/`, `scripts/`, and `AGENTS.md` packages so mechanical rules live in deterministic scripts, completion is proved on real artifacts, and prose retains every high-leverage rule that changes Agent decisions.

## 0. Mode, Subagent Offload & Fast Path

- **Audit Mode (read-only):** Scan, diagnose, and emit §5 with zero file edits. *Done when:* `scripts/audit_skills.py` has run in this session and every `P0`/`P1` finding cites a real `file:line` or observable funnel failure.
- **Polish Mode (audit + improve):** Save baseline -> apply surgical edits -> prove improvement on disk via `--verify-against`. *Done when:* `--verify-against` exits `0` (`PASS_POLISH_VERIFICATION`) alongside repository validators, with zero relaxed checks or gutted triggers.
- **Clean Fast Path:** If `scripts/audit_skills.py` reports `0 ERROR / 0 WARN` and §2 finds zero `P0`/`P1` decision gaps, return `▶︎▶︎PASS_SKILL_AUDIT▶︎▶︎` immediately without cosmetic rewrites.
- **Heavy-Output Isolation:** When scanning `>10` skills or inspecting `>200` lines / `>8 KB` of logs or diffs, delegate the read-only pass to a subagent (when host-supported) or filter via `--json` so raw bulk output never enters the main context window.

Load **only** the matching reference slice when its defect class surfaces (never read all references unconditionally):

| Detected Defect Class | Trigger Condition | Read Only When Matched |
| --- | --- | --- |
| **Trigger / SDO / Sibling Collision / DAG** | Workflow leaked in `description`, missing exclusions, or cross-skill `../` links | [1-pointer-and-dag-surgery](references/refactor-patterns.md#1-pointer-and-dag-surgery) |
| **Sprawl / Heavy Output / Missing Fast Path** | `>350` lines, missing Step-0 bypass / `Fast`-vs-`Full` track, or raw bulk outputs in main context | [2-progressive-disclosure-and-fast-paths](references/refactor-patterns.md#2-progressive-disclosure-and-fast-paths) |
| **Repeated Prose / Weak Gates / Retry Loops** | Rules stated twice in text, prose-only math/schema checks, fuzzy "done" claims, or missing stop-loss | [3-deterministic-gates-and-stop-loss](references/refactor-patterns.md#3-deterministic-gates-and-stop-loss) |
| **Permission Nags / Leaked Jargon / Sediment** | Asking approval on reversible edits, leaked internal names in replies, or undated `model-scaffolding` | [4-interaction-ux-and-scaffolding-hygiene](references/refactor-patterns.md#4-interaction-ux-and-scaffolding-hygiene) |
| **Empirical Benchmark Drift (`D10`)** | Auditing `ai-agent-book` adaptations or extracting skills from human before/after diffs | [ai-agent-book-skills-audit.md](references/ai-agent-book-skills-audit.md) |

## 1. Environment Self-Resolution & Irreversibility-Only Gate

1. **Inspect workspace facts first:** Read target skill files, sibling skills, plugin manifests, and repo `AGENTS.md` conventions before acting; infer target hosts (Claude Code, Codex, Devin, Cursor) and technical defaults without asking the user.
2. **Confirm only irreversible actions:** Advance all **reversible** work (git-tracked edits, disclosing `references/`, extracting `scripts/`, running tests and linters) autonomously end-to-end. Pause with **one** batched question **only** before **irreversible** operations: renaming or deleting public skill IDs, removing domain rules with ambiguous business intent, publishing/pushing externally, incurring paid API spend, or deleting untracked user files.

## 2. Audit Workflow

<!-- model-scaffolding: reason="prevent skipping deterministic scanner and jumping straight to subjective prose edits on mid-tier hosts" review-on="next-frontier-model" -->
1. **Run the deterministic structural compiler.**
   Execute `python3 scripts/audit_skills.py <target-dir>` (resolved relative to this skill's directory; in Polish Mode, run `--save-baseline <tmp-baseline.json>` first) on the target skill or collection. Record every `ERROR` and `WARN` with its rule ID and `file:line`.
   *Completion criterion:* Full scanner output (and baseline JSON in Polish Mode) captured in a completed step before manual review or editing begins.
<!-- /model-scaffolding -->

2. **Audit the context pointer (`description`), progressive disclosure, and execution tracks.**
   - **SDO Shortcut Trap & Pointer Purity (`D1`):** Flag any `description` summarizing internal steps or frameworks (`——覆盖...`, `涵盖...`, `runs A then B`), which tempts agents to skip reading `SKILL.md`. Require `Use when...` triggers, concrete symptoms, near-miss sibling redirects (`For X use Y`), and repo-maintenance exclusions only.
   - **Hierarchy, Fast Paths & Portability (`D3/D4/D9`):** Keep universal ordered steps in `SKILL.md` (`<350` lines); add a Step-0 bypass for unchanged/ready inputs plus `Fast` vs. `Full` complexity tracks; push branch-specific matrices/examples into `references/`; dispatch slow external jobs concurrently up front (with idempotency keys) while building local logic; flag unbundled repo-coupled paths.
   - **Structure over Repeated Text:** Whenever a requirement is stated a second time—or checks counts, formats, schemas, links, or call order—convert it into a lint rule, type, schema, fixed template, or zero-dependency self-locating `scripts/` check and delete the duplicate prose sentence. Keep every sentence that changes Agent decisions; delete generic filler ("be thorough") outright.
   *Completion criterion:* Every target classified on pointer purity, disclosure/fast-path split, prose-to-script migration candidates, and standalone path portability.

3. **Audit instruction form, Harness/KV-cache safety, UX boundaries, and the 4-layer funnel.**
   - **Form-to-failure match & Provable Completion (`D5/D6/D8`):** Replace negation lists on output-shaping problems (`don't repeat X`) with positive output contracts; reserve explicit prohibitions + rationalization tables for discipline rules; define completion upfront as checkable predicates verified by reproducible scripts on real artifacts—never trust Agent self-reports or allow relaxing thresholds.
   - **KV-cache, Injection & Black-Box UX (`D7/D8`):** Flag instructions mutating `system` per turn or reordering `tools`; audit bundled scripts, shell commands, and `<agent_status>` inputs as untrusted code/injection surfaces; strip internal skill/tool/path names from user-facing replies and split **Verified** vs. **Unverified** claims; tag temporary model-quirk workarounds with `<!-- model-scaffolding: reason="..." review-on="..." -->`.
   - **4-Layer Benefit Funnel (`D10`):** When a skill fails to improve benchmark scores, diagnose *which* layer broke instead of blindly rewriting `SKILL.md`:
     1. *Proposal validity* (does force-injecting the skill fix the failure?)
     2. *Activation rate* (did `description` trigger on target prompts?)
     3. *Compliance rate* (did the agent execute all steps including verification?)
     4. *Holdout gain* (did Boundary Set improve without Retention Set regression?)
   *Completion criterion:* Form-to-failure gaps, KV-cache/injection risks, and root-cause funnel layer identified with evidence tags (`VERIFIED`, `INFERRED`, `UNKNOWN`).

## 3. Minimal-Diff Refactoring & Artifact Proof (Polish Mode)

1. Preserve directory name, frontmatter `name`, and `agents/openai.yaml` `display_name`; migrate repeated/mechanical rules into `scripts/` or schemas and disclose `>80`-line branch tables into `references/<topic>.md` behind conditional pointers.
2. Re-verify real disk artifacts via `python3 scripts/audit_skills.py <target-dir> --verify-against <tmp-baseline.json>` plus repository validators and `git diff --check` until `--verify-against` exits `0`.

## 4. Anti-Reward-Hacking & Stop-Loss

- **Hard Fails:** Never silence broken-link or `#anchor` errors by deleting needed domain guidance without migrating it; never strip concrete triggers just to shorten `description`; never fabricate empirical numbers or weaken assertions/thresholds to claim completion.
- **Stop-Loss:** Cap polish passes at **2 rounds** (in audited target workflows: block on `P0` with a 2-round approach pivot; cap `P1` fixes at `<=3` rounds; log `P2` items to `Known gaps` without looping). Record ambiguous domain trade-offs or missing external runtimes under `P2` rather than guessing.

## 5. Output Contract

Return these exact sections in order:
1. **Scanner & Baseline Summary:** Scanned skill count, `ERROR` and `WARN` counts (`before -> after` + `--verify-against` status in Polish Mode), and exact command(s) run.
2. **Prioritized Defect & Polish Ledger:** Markdown table with columns `Severity (P0-P2) | Rule ID | Location (file:line) | Evidence ([VERIFIED]/[INFERRED]/[UNKNOWN]) | Structural / Minimal-Diff Fix`.
3. **Funnel, Orthogonality & Verification Split:** Trigger collision check against sibling skills, primary bottleneck layer (`Validity / Activation / Compliance / Holdout`), and **Verified** (script-proved on real artifacts) vs. **Unverified** (live activation/compliance) items, plus up to 5 `P2` items.
4. **Verdict:** `▶︎▶︎PASS_SKILL_AUDIT▶︎▶︎` (`0` P0/P1 defects; or `▶︎▶︎PASS_SKILL_POLISH▶︎▶︎` only when `--verify-against` exits `0`) or `▶︎▶︎FIX_BEFORE_INSTALL▶︎▶︎` followed by one line naming the first fix to apply.

## Disclosed Resources

- Run `scripts/audit_skills.py` (`--save-baseline` / `--verify-against`) for deterministic frontmatter, `#anchor`, DAG, script-path, `model-scaffolding`, repeated-rule, and anti-relaxation artifact checks.
- Read [references/refactor-patterns.md](references/refactor-patterns.md) for conditional surgical refactoring patterns across pointers, fast paths, subagent offloading, provable gates, and UX hygiene.
- Read [references/ai-agent-book-skills-audit.md](references/ai-agent-book-skills-audit.md) for the `D1`–`D10` defect taxonomy, iterative human before/after diff extraction rules, and the 22-skill `ai-agent-book` audit.
