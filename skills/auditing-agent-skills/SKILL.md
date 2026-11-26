---
name: auditing-agent-skills
description: Use when scanning, linting, or diagnosing existing SKILL.md, AGENTS.md, or CLAUDE.md files for SDO workflow-summary shortcuts, broken paths, context sprawl, KV-cache invalidation, prompt-injection surfaces, or flat end-to-end skill benefit (扫描当前 Skill 缺陷、排查 Skill 不触发或触发后跳步、四层收益漏斗诊断). For prose hierarchy use mattpocock-writing-for-agents; for subagent pressure-testing use superpowers-writing-skills.
---

# Auditing and Diagnosing Agent Skills

Audit existing `SKILL.md`, `agents/openai.yaml`, `references/`, `scripts/`, and `AGENTS.md` packages using deterministic static checks and the 4-layer skill benefit funnel before rewriting or installing them.

## Audit Workflow

1. **Run the deterministic structural scanner.**
   Execute `python3 scripts/audit_skills.py <target-dir>` (resolved relative to this skill's directory) on the target skill or collection. Record every `ERROR` and `WARN` with its rule ID and `file:line`.
   *Completion criterion:* Full scanner output captured before manual review begins.

2. **Audit the context pointer (`description`) and 3-layer progressive disclosure.**
   - **SDO Shortcut Trap (`D1`):** Flag any `description` that summarizes internal steps or frameworks (`——覆盖...`, `涵盖...`, `runs A then B`). Agents treat workflow summaries in `description` as a shortcut to skip reading `SKILL.md`. Require `Use when...` triggers, concrete symptoms, and near-miss routing exclusions only.
   - **Hierarchy & Portability (`D3/D4/D9`):** Keep universal ordered steps in `SKILL.md` (<350 lines); push mode-specific matrices/examples into `references/`; extract repeatable math/validation into zero-dependency `scripts/`; flag unbundled repo-coupled paths.
   *Completion criterion:* Every skill classified on pointer purity, disclosure split, and standalone path portability.

3. **Audit instruction form, Harness/KV-cache safety, and empirical drift.**
   - **Form-to-failure match (`D5/D6`):** Replace negation lists on output-shaping problems (`don't repeat X`) with positive output contracts; reserve explicit prohibitions + rationalization tables for discipline rules; end every step on an observable check.
   - **KV-cache & Injection safety (`D7/D8`):** Flag instructions mutating `system` per turn or reordering `tools`; audit bundled scripts, shell commands, and `<agent_status>` inputs as untrusted code/injection surfaces.
   - **4-Layer Benefit Funnel (`D10`):** When a skill fails to improve benchmark scores, diagnose *which* layer broke instead of blindly rewriting `SKILL.md`:
     1. *Proposal validity* (does force-injecting the skill fix the failure?)
     2. *Activation rate* (did `description` trigger on target prompts?)
     3. *Compliance rate* (did the agent execute all steps including verification?)
     4. *Holdout gain* (did Boundary Set improve without Retention Set regression?)
   *Completion criterion:* Root-cause layer identified with evidence tags (`VERIFIED`, `INFERRED`, `UNKNOWN`).

## Output Contract

Return an audit report containing these exact sections in order:
1. **Scanner Summary:** Scanned skill count, `ERROR` count, `WARN` count, and exact command run.
2. **Prioritized Defect Ledger:** Markdown table with columns `Severity (P0-P2) | Rule ID | Location (file:line) | Evidence ([VERIFIED]/[INFERRED]) | Minimal-Diff Fix`.
3. **Funnel & Orthogonality Diagnosis:** Trigger collision check against sibling skills + which funnel layer (`Validity / Activation / Compliance / Holdout`) is the primary bottleneck.
4. **Verdict:** `▶︎▶︎PASS_SKILL_AUDIT▶︎▶︎` (0 P0/P1 defects) or `▶︎▶︎FIX_BEFORE_INSTALL▶︎▶︎` followed by one line naming the first fix to apply.

## Disclosed Resources

- Run `scripts/audit_skills.py` for zero-dependency frontmatter, SDO leak, broken-link, step-numbering, and portability checks.
- Read [references/ai-agent-book-skills-audit.md](references/ai-agent-book-skills-audit.md) for the 10-class defect taxonomy (`D1`–`D10`), iterative human before/after diff extraction rules, and the 22-skill empirical audit of `ai-agent-book`.
