# Google Stitch Frontend Skills Port Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add four portable `google-stitch-*` frontend design skills to `polish` without any runtime Stitch MCP or upload dependency.

**Architecture:** Each skill is an independently triggerable unit under `skills/` and composes through optional root-level `DESIGN.md` and frontend brief artifacts. Large taste rules, framework extraction notes, component catalogs, and examples stay behind one-level progressive-disclosure references. A deterministic validator enforces the prefixed naming, runtime closure, links, and forbidden dependency boundary.

**Tech Stack:** Agent Skills Markdown/YAML, Python 3 validator, shell syntax checks, JSON plugin manifests, subagent behavior tests.

---

## File Map

**Create**

- `scripts/validate_google_stitch_port.py`: deterministic file, name, link, and forbidden-dependency validation.
- `skills/google-stitch-frontend-taste-design/SKILL.md`: taste workflow and review gates.
- `skills/google-stitch-frontend-taste-design/references/taste-rules.md`: detailed visual heuristics.
- `skills/google-stitch-frontend-taste-design/assets/DESIGN.md`: reusable design contract template.
- `skills/google-stitch-extract-frontend-design-system/SKILL.md`: source-reading extraction workflow.
- `skills/google-stitch-extract-frontend-design-system/references/{react-tailwind,vue,svelte,angular,plain-css}.md`: framework extraction notes.
- `skills/google-stitch-extract-frontend-design-system/references/design-md-template.md`: portable output example.
- `skills/google-stitch-frontend-brief-enhancer/SKILL.md`: vague-request to implementation-brief workflow.
- `skills/google-stitch-frontend-brief-enhancer/references/ui-ux-keywords.md`: UI vocabulary.
- `skills/google-stitch-frontend-brief-enhancer/references/brief-template.md`: complete brief structure.
- `skills/google-stitch-shadcn-ui/SKILL.md`: shadcn/ui implementation workflow.
- `skills/google-stitch-shadcn-ui/references/{component-catalog,customization-guide,setup-guide,migration-guide}.md`: progressive implementation references.
- `skills/google-stitch-shadcn-ui/examples/form-pattern.tsx`: one complete implementation example.
- `skills/google-stitch-shadcn-ui/scripts/verify-setup.sh`: deterministic project setup check.

**Modify**

- `README.md`: English and Chinese collection lists, workflow, and structure.
- `.codex-plugin/plugin.json`: frontend design discovery description and keywords.
- `.claude-plugin/plugin.json`: frontend design discovery description.
- `.claude-plugin/marketplace.json`: marketplace description.
- `.cursor-plugin/plugin.json`: frontend design discovery description and keywords.
- `THIRD_PARTY_NOTICES.md`: Apache-2.0 source attribution and pinned source commit.

## Task 1: Add the deterministic port gate

- [ ] **Step 1: Create the validator before any destination skill exists**

Implement `scripts/validate_google_stitch_port.py` with:

```python
EXPECTED = {
    "google-stitch-frontend-taste-design": {
        "SKILL.md", "references/taste-rules.md", "assets/DESIGN.md",
    },
    "google-stitch-extract-frontend-design-system": {
        "SKILL.md",
        "references/react-tailwind.md", "references/vue.md",
        "references/svelte.md", "references/angular.md",
        "references/plain-css.md", "references/design-md-template.md",
    },
    "google-stitch-frontend-brief-enhancer": {
        "SKILL.md", "references/ui-ux-keywords.md",
        "references/brief-template.md",
    },
    "google-stitch-shadcn-ui": {
        "SKILL.md", "references/component-catalog.md",
        "references/customization-guide.md", "references/setup-guide.md",
        "references/migration-guide.md", "examples/form-pattern.tsx",
        "scripts/verify-setup.sh",
    },
}
```

Validate exact runtime closure, matching frontmatter `name`, descriptions
beginning with `Use when`, relative Markdown links, and forbidden runtime
strings: `upload-to-stitch`, `upload_to_stitch`, `StitchMCP`,
`stitch*:*`, `list_projects`, `get_screen`, `generate_screen`,
and `.stitch/`.

- [ ] **Step 2: Run the validator and verify RED**

Run:

```bash
python3 scripts/validate_google_stitch_port.py
```

Expected: FAIL with four missing-directory errors.

- [ ] **Step 3: Syntax-check the validator**

Run:

```bash
PYTHONPYCACHEPREFIX=/tmp/polish-pycache python3 -m py_compile scripts/validate_google_stitch_port.py
```

Expected: exit 0.

- [ ] **Step 4: Commit the gate**

```bash
git add scripts/validate_google_stitch_port.py
git commit -m "test: add google-stitch skill port gate"
```

## Task 2: Port `google-stitch-frontend-taste-design`

- [ ] **Step 1: Run the baseline pressure scenario without the skill**

Ask a fresh subagent to improve a generic SaaS landing-page direction in one
pass under time pressure, with no permission to invent product facts. Record
whether it defaults to generic gradients, equal card rows, arbitrary fonts,
decorative motion, fake metrics, or lacks responsive and state guidance.

- [ ] **Step 2: Initialize the skill**

Run `init_skill.py` with `references,assets`, then replace all generated
placeholders:

```bash
python3 /Users/joejiang/.codex/skills/.system/skill-creator/scripts/init_skill.py \
  google-stitch-frontend-taste-design --path skills \
  --resources references,assets \
  --interface 'display_name=Google Stitch Frontend Taste Design' \
  --interface 'short_description=Create or review coherent frontend visual direction' \
  --interface 'default_prompt=Use $google-stitch-frontend-taste-design to establish or review the visual direction for this interface.'
```

- [ ] **Step 3: Write the minimal skill and resources**

Use trigger-only frontmatter:

```yaml
---
name: google-stitch-frontend-taste-design
description: Use when creating or reviewing frontend visual direction and the interface risks generic AI styling, weak hierarchy, incoherent color, repetitive layouts, poor typography, or decorative motion without purpose.
---
```

Keep the main workflow under 500 words. Adapt the source taste rules into
`references/taste-rules.md`, replacing universal font/layout bans with
context-aware decision rules. Adapt the source design template into
`assets/DESIGN.md` without Stitch-specific wording.

- [ ] **Step 4: Run GREEN behavior test**

Run the same prompt with the new skill path. Expected: explicit product-context
assumptions, coherent hierarchy/palette/type/layout/motion direction, no
fabricated facts, responsive behavior, component states, and a review checklist.

- [ ] **Step 5: Validate and commit**

```bash
python3 scripts/validate_google_stitch_port.py --skill google-stitch-frontend-taste-design
python3 /Users/joejiang/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/google-stitch-frontend-taste-design
git diff --check
git add skills/google-stitch-frontend-taste-design
git commit -m "feat: add google-stitch frontend taste skill"
```

## Task 3: Port `google-stitch-extract-frontend-design-system`

- [ ] **Step 1: Run the baseline scenario without the skill**

Give a fresh subagent a small mixed Tailwind/CSS-variable fixture with duplicate
tokens and a broken build. Expected baseline failure: raw token listing without
semantic roles, no evidence/inference distinction, missed responsive/component
state patterns, or a demand to run the application.

- [ ] **Step 2: Initialize and implement the skill**

Initialize with `references`. Use this trigger:

```yaml
description: Use when an existing frontend repository needs its visual language, design tokens, styling inconsistencies, component patterns, or responsive rules documented directly from source code, including when the application cannot build or run.
```

Adapt the five framework references. Replace the Stitch-only output section
with a portable root `DESIGN.md` containing evidence, inferred intent,
tokens, typography, components and states, layout, responsiveness, motion,
accessibility, inconsistencies, and implementation guidance.

- [ ] **Step 3: Run GREEN behavior test**

Expected: source-only audit succeeds; near-duplicates are consolidated;
observations and inferences are labeled; missing evidence is reported rather
than invented; output is usable by another coding agent.

- [ ] **Step 4: Validate and commit**

```bash
python3 scripts/validate_google_stitch_port.py --skill google-stitch-extract-frontend-design-system
python3 /Users/joejiang/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/google-stitch-extract-frontend-design-system
git diff --check
git add skills/google-stitch-extract-frontend-design-system
git commit -m "feat: add google-stitch design extraction skill"
```

## Task 4: Port `google-stitch-frontend-brief-enhancer`

- [ ] **Step 1: Run the baseline scenario without the skill**

Prompt a fresh subagent with “make the settings page feel premium.” Expected
baseline gaps: no separation of facts/inferences/questions, weak state coverage,
missing responsive/accessibility criteria, or fabricated product content.

- [ ] **Step 2: Initialize and implement the skill**

Initialize with `references`. Use this trigger:

```yaml
description: Use when a frontend request is too vague to implement without inventing visual, structural, interaction, responsive, accessibility, content, or acceptance-criteria decisions.
```

Adapt the source keyword reference and add a complete brief template. The skill
must stop after producing the brief and must distinguish confirmed
requirements, reversible assumptions, and decisions requiring user input.

- [ ] **Step 3: Run GREEN behavior test**

Expected: implementation-ready brief with purpose, platform, hierarchy,
components, all relevant states, responsive behavior, accessibility, motion,
content constraints, and testable acceptance criteria without fabricated facts.

- [ ] **Step 4: Validate and commit**

```bash
python3 scripts/validate_google_stitch_port.py --skill google-stitch-frontend-brief-enhancer
python3 /Users/joejiang/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/google-stitch-frontend-brief-enhancer
git diff --check
git add skills/google-stitch-frontend-brief-enhancer
git commit -m "feat: add google-stitch frontend brief skill"
```

## Task 5: Port `google-stitch-shadcn-ui`

- [ ] **Step 1: Run the baseline scenario without the skill**

Ask a fresh subagent to plan a dense responsive shadcn/ui settings surface.
Expected baseline gaps: editing registry primitives for product logic, one-off
classes, incomplete loading/error/empty/disabled states, or missing keyboard,
focus, mobile, and dark-mode checks.

- [ ] **Step 2: Initialize and implement the runtime closure**

Initialize with `references,scripts`. Use this trigger:

```yaml
description: Use when implementing or reviewing a React interface with shadcn/ui and it needs coherent theming, component composition, variants, accessibility, interaction states, responsive behavior, or visual consistency.
```

Adapt the four source references, one form example, and setup script. Remove MCP
tool assumptions; document CLI and local-code discovery. Keep the main skill
under 500 words and route detailed requests to the correct reference.

- [ ] **Step 3: Verify the helper and GREEN behavior**

```bash
bash -n skills/google-stitch-shadcn-ui/scripts/verify-setup.sh
```

Run the same behavior prompt with the skill. Expected: project token reuse,
composition boundaries, complete UI states, accessibility, responsive and
dark-mode checks, and explicit validation commands.

- [ ] **Step 4: Validate and commit**

```bash
python3 scripts/validate_google_stitch_port.py --skill google-stitch-shadcn-ui
python3 /Users/joejiang/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/google-stitch-shadcn-ui
git diff --check
git add skills/google-stitch-shadcn-ui
git commit -m "feat: add google-stitch shadcn ui skill"
```

## Task 6: Integrate collection documentation and provenance

- [ ] **Step 1: Update README in English and Chinese**

List all four skills, explain the optional artifact flow, add paths to both
structure trees, and preserve existing collection content.

- [ ] **Step 2: Update plugin discovery metadata**

Add concise frontend-design wording and keywords such as
`frontend-design`, `design-system`, `ui-ux`, `shadcn-ui`, and
`visual-review`. Preserve package name and versions.

- [ ] **Step 3: Add Apache-2.0 provenance**

Record source URL
`https://github.com/google-labs-code/stitch-skills`, source commit
`3f64079d75d025bc5890c73669f27c26a2d80b31`, adapted directories, Google LLC
copyright, and Apache-2.0 terms in `THIRD_PARTY_NOTICES.md`.

- [ ] **Step 4: Validate and commit integration**

```bash
python3 -m json.tool .codex-plugin/plugin.json
python3 -m json.tool .claude-plugin/plugin.json
python3 -m json.tool .claude-plugin/marketplace.json
python3 -m json.tool .cursor-plugin/plugin.json
python3 /Users/joejiang/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py .
git diff --check
git add README.md .codex-plugin/plugin.json .claude-plugin/plugin.json \
  .claude-plugin/marketplace.json .cursor-plugin/plugin.json \
  THIRD_PARTY_NOTICES.md
git commit -m "docs: integrate google-stitch frontend skills"
```

## Task 7: Final merged-state verification

- [ ] **Step 1: Run the full port and skill gates**

```bash
python3 scripts/validate_google_stitch_port.py
for skill in skills/*/SKILL.md; do
  python3 /Users/joejiang/.codex/skills/.system/skill-creator/scripts/quick_validate.py "$(dirname "$skill")"
done
```

- [ ] **Step 2: Run manifest, helper, and whitespace gates**

```bash
python3 -m json.tool .codex-plugin/plugin.json
python3 -m json.tool .claude-plugin/plugin.json
python3 -m json.tool .claude-plugin/marketplace.json
python3 -m json.tool .cursor-plugin/plugin.json
python3 /Users/joejiang/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py .
bash -n skills/google-stitch-shadcn-ui/scripts/verify-setup.sh
PYTHONPYCACHEPREFIX=/tmp/polish-pycache python3 -m py_compile scripts/validate_google_stitch_port.py
git diff --check
```

- [ ] **Step 3: Confirm scope preservation**

Verify that only the planned `google-stitch-*`, documentation, manifests,
notice, and validator paths changed; `superpowers/` remains untracked and
unmodified; no push or PR is performed without a separate user request.
