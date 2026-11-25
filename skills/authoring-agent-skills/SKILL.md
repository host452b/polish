---
name: authoring-agent-skills
description: Use when packaging domain workflows into 3-layer progressive-disclosure skill bundles (SKILL.md + references + scripts + openai.yaml), distilling human before/after edits into rules, or diagnosing the 4-layer skill benefit funnel (创建与重构渐进式 Skill 包、把业务经验沉淀为 SKILL.md). For general agent-doc pruning use mattpocock-writing-for-agents; for subagent TDD pressure-testing use superpowers-writing-skills.
---

# Authoring and Optimizing Agent Skills

Package reusable engineering workflows, domain judgment, and deterministic helpers into modular `SKILL.md` units that discover reliably, preserve KV cache prefixes, and enforce checkable completion criteria.

## Authoring Workflow

1. **Decide capability form before creating a skill.**
   Apply the 4-way carrier test:
   - Frequently changing workflow, domain judgment with exceptions, or multi-step CLI recipe -> **Skill (`SKILL.md`)**.
   - High-risk mutation needing strict auth, audit log, or complex nested validation -> **Dedicated Tool**.
   - Ephemeral/queryable facts with provenance & permissions -> **RAG / Knowledge Base**.
   - Implicit perceptual patterns or tone hard to state in rules -> **Model Post-Training**.
   *Completion criterion:* Target capability confirmed as process/judgment knowledge suitable for a skill rather than a hard permission gate.

2. **Design the 3-Layer Progressive Disclosure layout.**
   ```text
   <skill-name>/
   ├── SKILL.md               # Layer 2: Core workflow, decision gates, pointers (<350 lines)
   ├── agents/openai.yaml     # UI metadata & implicit invocation policy
   ├── scripts/               # Layer 3a: Deterministic, repeatable CLI helpers (optional)
   └── references/            # Layer 3b: Mode-specific specs, schemas, examples (optional)
   ```
   - **Layer 1 (`name` + `description` frontmatter):** Lowercase kebab-case verb-first `name` matching directory name; `description` under 500 chars, no `<` or `>`, starting with `Use when...`, listing concrete triggers, error symptoms, and near-miss exclusions—**never** summarizing the workflow.
   - **Layer 2 (`SKILL.md` body):** Inline only what *every* invocation needs; push branch-specific detail behind explicit markdown links in `references/`.
   - **Layer 3 (`scripts/` & `references/`):** Extract math, parsers, validators, and file generators into executable scripts so the agent invokes code instead of regenerating it.
   *Completion criterion:* Directory layout created with zero unreferenced files and zero external broken paths.

3. **Match instruction form to the baseline failure mode.**
   - **Wrong output shape / sprawling output:** Write a **positive recipe** (exact required sections/fields in order). Avoid "Don't X" lists, which drag X into attention and trigger negotiation.
   - **Skipped rule under pressure (e.g., skipping tests/verification):** Add **explicit prohibition + no-exception list + rationalization counter-table + Red Flags**.
   - **Conditional branch:** Key every branch to an **observable predicate** (`If pass@k == 0 on 16 rollouts -> ...`), eliminating vague nuance clauses (`unless appropriate`).
   - **Rule tuple:** Express domain rules as **Scope + Action + Exception + Verification**.
   *Completion criterion:* Every step in `SKILL.md` ends on a binary, observable completion criterion.

4. **Verify across the 4-Layer Skill Benefit Funnel.**
   1. **Structural check:** Invoke **REQUIRED SUB-SKILL:** `auditing-agent-skills` (0 errors, 0 warnings).
   2. **Activation check:** Confirm target prompts trigger the skill and near-miss prompts skip it.
   3. **Compliance check:** Confirm the agent executes required verification steps rather than shortcutting from `description`.
   4. **Boundary + Retention check:** Verify target failure cases improve (Boundary Set) while previously passing tasks do not regress or over-correct (Retention Set).
   *Completion criterion:* All four checks verified before deploying or syncing the skill.

## Invocation & Cache Rules

| Choice | Mechanics | Context & Cache Impact |
|---|---|---|
| **Model-invoked (default)** | Keep trigger-rich `description`; `allow_implicit_invocation: true` | `name + description` stays in directory; `SKILL.md` body appends at call site without busting prior KV cache prefix |
| **User-invoked only** | `allow_implicit_invocation: false` (or `triggers: [user]` in Devin) | Zero permanent model-routing load; human invokes via `/skill-name` or `$skill-name` |
| **Complex CLI args in Skill** | Instruct agent to write nested JSON payload to a temp file and pass `--input file.json` | Eliminates multi-shell quoting/escaping corruption across bash/zsh/PowerShell |

## Disclosed Reference

- Read [references/skill-patterns-and-anti-patterns.md](references/skill-patterns-and-anti-patterns.md) when drafting frontmatter descriptions, converting user before/after edits into rules, or hardening discipline skills against rationalizations.
