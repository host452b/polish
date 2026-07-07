# Prefixed Superpowers Skill Port Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Port five selected Superpowers skills into `polish` with `superpowers-` names, complete runtime dependencies, working internal references, and accurate provenance.

**Architecture:** Treat `superpowers/` as a read-only upstream checkout pinned at commit `d884ae04edebef577e82ff7c4e143debd0bbec99`. Copy only each selected skill's runtime closure into `skills/`, then apply small compatibility edits for prefixed names and the standalone planning handoff. A deterministic validator protects the file manifest, frontmatter, cross-references, and local Markdown links.

**Tech Stack:** Markdown/YAML skills, Python 3 validation, JSON plugin manifests, shell helper scripts, Node.js syntax checks, Git.

---

## File Map

**Create:**

- `scripts/validate_superpowers_port.py` — validates expected runtime files, frontmatter names, legacy references, and relative Markdown links.
- `skills/superpowers-brainstorming/` — brainstorming workflow plus visual-companion runtime.
- `skills/superpowers-systematic-debugging/` — debugging workflow plus directly referenced guides and helpers.
- `skills/superpowers-verification-before-completion/SKILL.md` — evidence-before-claims workflow.
- `skills/superpowers-test-driven-development/` — TDD workflow plus testing anti-pattern reference.
- `skills/superpowers-writing-skills/` — skill-authoring workflow plus directly referenced guidance and tools.
- `THIRD_PARTY_NOTICES.md` — upstream source, pinned commit, copyright, and MIT text.

**Modify:**

- `README.md` — list and document the five skills in English and Chinese, update structure and provenance wording.
- `.codex-plugin/plugin.json` — update collection description, keywords, long description, and prompts.
- `.claude-plugin/plugin.json` — update collection description.
- `.claude-plugin/marketplace.json` — update marketplace description.
- `.cursor-plugin/plugin.json` — update collection description and keywords.
- `AGENTS.md` — make project provenance wording accurate and validate every canonical skill.

### Task 1: Add the port validator and establish RED

**Files:**

- Create: `scripts/validate_superpowers_port.py`
- Verify: `skills/superpowers-*/`

- [ ] **Step 1: Create the deterministic validator**

Create `scripts/validate_superpowers_port.py` with this behavior:

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"

EXPECTED = {
    "superpowers-brainstorming": {
        "SKILL.md",
        "spec-document-reviewer-prompt.md",
        "visual-companion.md",
        "scripts/frame-template.html",
        "scripts/helper.js",
        "scripts/server.cjs",
        "scripts/start-server.sh",
        "scripts/stop-server.sh",
    },
    "superpowers-systematic-debugging": {
        "SKILL.md",
        "condition-based-waiting-example.ts",
        "condition-based-waiting.md",
        "defense-in-depth.md",
        "find-polluter.sh",
        "root-cause-tracing.md",
    },
    "superpowers-verification-before-completion": {"SKILL.md"},
    "superpowers-test-driven-development": {
        "SKILL.md",
        "testing-anti-patterns.md",
    },
    "superpowers-writing-skills": {
        "SKILL.md",
        "anthropic-best-practices.md",
        "examples/CLAUDE_MD_TESTING.md",
        "graphviz-conventions.dot",
        "persuasion-principles.md",
        "render-graphs.js",
        "testing-skills-with-subagents.md",
    },
}

LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


def markdown_without_fenced_code(text: str) -> str:
    output: list[str] = []
    in_fence = False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            output.append(line)
    return "\n".join(output)


def validate_skill(name: str) -> list[str]:
    skill_dir = SKILLS / name
    errors: list[str] = []
    if not skill_dir.is_dir():
        return [f"{name}: missing directory"]

    actual = {
        path.relative_to(skill_dir).as_posix()
        for path in skill_dir.rglob("*")
        if path.is_file()
    }
    missing = EXPECTED[name] - actual
    extra = actual - EXPECTED[name]
    if missing:
        errors.append(f"{name}: missing files: {', '.join(sorted(missing))}")
    if extra:
        errors.append(f"{name}: unexpected files: {', '.join(sorted(extra))}")

    skill_md = skill_dir / "SKILL.md"
    if skill_md.is_file():
        frontmatter = skill_md.read_text(encoding="utf-8").split("---", 2)
        if len(frontmatter) < 3 or f"\nname: {name}\n" not in f"\n{frontmatter[1]}\n":
            errors.append(f"{name}: frontmatter name does not match directory")

    for path in skill_dir.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        if "superpowers:" in text:
            errors.append(f"{path.relative_to(ROOT)}: legacy superpowers: reference")
        visible_text = markdown_without_fenced_code(text)
        for raw_target in LINK_RE.findall(visible_text):
            target = raw_target.strip().strip("<>").split("#", 1)[0]
            if not target or "://" in target or target.startswith("mailto:"):
                continue
            resolved = (path.parent / target).resolve()
            if not resolved.exists():
                errors.append(
                    f"{path.relative_to(ROOT)}: broken relative link {raw_target}"
                )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill", choices=sorted(EXPECTED))
    args = parser.parse_args()
    names = [args.skill] if args.skill else sorted(EXPECTED)
    errors = [error for name in names for error in validate_skill(name)]
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"Validated {len(names)} prefixed Superpowers skill(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run the validator and verify RED**

Run:

```bash
python3 scripts/validate_superpowers_port.py
```

Expected: exit 1 with five `missing directory` errors. This proves the test detects the absent port before implementation.

- [ ] **Step 3: Syntax-check the validator**

Run:

```bash
python3 -m py_compile scripts/validate_superpowers_port.py
```

Expected: exit 0 with no output.

- [ ] **Step 4: Commit the validation harness**

```bash
git add scripts/validate_superpowers_port.py
git commit -m "test: add superpowers port validator"
```

### Task 2: Port `superpowers-test-driven-development`

**Files:**

- Create: `skills/superpowers-test-driven-development/SKILL.md`
- Create: `skills/superpowers-test-driven-development/testing-anti-patterns.md`

- [ ] **Step 1: Copy the upstream runtime files**

```bash
mkdir -p skills/superpowers-test-driven-development
cp superpowers/skills/test-driven-development/SKILL.md skills/superpowers-test-driven-development/SKILL.md
cp superpowers/skills/test-driven-development/testing-anti-patterns.md skills/superpowers-test-driven-development/testing-anti-patterns.md
```

- [ ] **Step 2: Rename the canonical skill**

Use `apply_patch` to change only the frontmatter line:

```yaml
name: superpowers-test-driven-development
```

- [ ] **Step 3: Validate the isolated skill**

Run:

```bash
python3 scripts/validate_superpowers_port.py --skill superpowers-test-driven-development
python3 /Users/joejiang/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/superpowers-test-driven-development
```

Expected: both commands exit 0.

- [ ] **Step 4: Commit the skill**

```bash
git add skills/superpowers-test-driven-development
git commit -m "feat: add prefixed TDD skill"
```

### Task 3: Port `superpowers-verification-before-completion`

**Files:**

- Create: `skills/superpowers-verification-before-completion/SKILL.md`

- [ ] **Step 1: Copy the upstream skill**

```bash
mkdir -p skills/superpowers-verification-before-completion
cp superpowers/skills/verification-before-completion/SKILL.md skills/superpowers-verification-before-completion/SKILL.md
```

- [ ] **Step 2: Rename the canonical skill**

Use `apply_patch` to set:

```yaml
name: superpowers-verification-before-completion
```

- [ ] **Step 3: Validate the isolated skill**

Run:

```bash
python3 scripts/validate_superpowers_port.py --skill superpowers-verification-before-completion
python3 /Users/joejiang/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/superpowers-verification-before-completion
```

Expected: both commands exit 0.

- [ ] **Step 4: Commit the skill**

```bash
git add skills/superpowers-verification-before-completion
git commit -m "feat: add prefixed verification skill"
```

### Task 4: Port `superpowers-systematic-debugging`

**Files:**

- Create: `skills/superpowers-systematic-debugging/SKILL.md`
- Create: `skills/superpowers-systematic-debugging/condition-based-waiting-example.ts`
- Create: `skills/superpowers-systematic-debugging/condition-based-waiting.md`
- Create: `skills/superpowers-systematic-debugging/defense-in-depth.md`
- Create: `skills/superpowers-systematic-debugging/find-polluter.sh`
- Create: `skills/superpowers-systematic-debugging/root-cause-tracing.md`

- [ ] **Step 1: Copy exactly the runtime closure**

```bash
mkdir -p skills/superpowers-systematic-debugging
cp superpowers/skills/systematic-debugging/SKILL.md skills/superpowers-systematic-debugging/SKILL.md
cp superpowers/skills/systematic-debugging/condition-based-waiting-example.ts skills/superpowers-systematic-debugging/condition-based-waiting-example.ts
cp superpowers/skills/systematic-debugging/condition-based-waiting.md skills/superpowers-systematic-debugging/condition-based-waiting.md
cp superpowers/skills/systematic-debugging/defense-in-depth.md skills/superpowers-systematic-debugging/defense-in-depth.md
cp superpowers/skills/systematic-debugging/find-polluter.sh skills/superpowers-systematic-debugging/find-polluter.sh
cp superpowers/skills/systematic-debugging/root-cause-tracing.md skills/superpowers-systematic-debugging/root-cause-tracing.md
```

- [ ] **Step 2: Apply namespace compatibility edits**

Use `apply_patch` to make these exact substitutions in `SKILL.md`:

```text
name: systematic-debugging
→ name: superpowers-systematic-debugging

superpowers:test-driven-development
→ superpowers-test-driven-development

superpowers:verification-before-completion
→ superpowers-verification-before-completion
```

- [ ] **Step 3: Validate the isolated skill and helper syntax**

Run:

```bash
python3 scripts/validate_superpowers_port.py --skill superpowers-systematic-debugging
python3 /Users/joejiang/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/superpowers-systematic-debugging
bash -n skills/superpowers-systematic-debugging/find-polluter.sh
```

Expected: all commands exit 0.

- [ ] **Step 4: Commit the skill**

```bash
git add skills/superpowers-systematic-debugging
git commit -m "feat: add prefixed systematic debugging skill"
```

### Task 5: Port `superpowers-writing-skills`

**Files:**

- Create: `skills/superpowers-writing-skills/SKILL.md`
- Create: `skills/superpowers-writing-skills/anthropic-best-practices.md`
- Create: `skills/superpowers-writing-skills/examples/CLAUDE_MD_TESTING.md`
- Create: `skills/superpowers-writing-skills/graphviz-conventions.dot`
- Create: `skills/superpowers-writing-skills/persuasion-principles.md`
- Create: `skills/superpowers-writing-skills/render-graphs.js`
- Create: `skills/superpowers-writing-skills/testing-skills-with-subagents.md`

- [ ] **Step 1: Copy exactly the runtime closure**

```bash
mkdir -p skills/superpowers-writing-skills/examples
cp superpowers/skills/writing-skills/SKILL.md skills/superpowers-writing-skills/SKILL.md
cp superpowers/skills/writing-skills/anthropic-best-practices.md skills/superpowers-writing-skills/anthropic-best-practices.md
cp superpowers/skills/writing-skills/examples/CLAUDE_MD_TESTING.md skills/superpowers-writing-skills/examples/CLAUDE_MD_TESTING.md
cp superpowers/skills/writing-skills/graphviz-conventions.dot skills/superpowers-writing-skills/graphviz-conventions.dot
cp superpowers/skills/writing-skills/persuasion-principles.md skills/superpowers-writing-skills/persuasion-principles.md
cp superpowers/skills/writing-skills/render-graphs.js skills/superpowers-writing-skills/render-graphs.js
cp superpowers/skills/writing-skills/testing-skills-with-subagents.md skills/superpowers-writing-skills/testing-skills-with-subagents.md
```

- [ ] **Step 2: Apply namespace compatibility edits**

Use `apply_patch` to change the frontmatter name to `superpowers-writing-skills` and replace every selected upstream reference in this directory:

```text
superpowers:test-driven-development
→ superpowers-test-driven-development

superpowers:systematic-debugging
→ superpowers-systematic-debugging
```

- [ ] **Step 3: Validate the isolated skill and renderer syntax**

Run:

```bash
python3 scripts/validate_superpowers_port.py --skill superpowers-writing-skills
python3 /Users/joejiang/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/superpowers-writing-skills
node --check skills/superpowers-writing-skills/render-graphs.js
```

Expected: all commands exit 0.

- [ ] **Step 4: Commit the skill**

```bash
git add skills/superpowers-writing-skills
git commit -m "feat: add prefixed skill authoring workflow"
```

### Task 6: Port `superpowers-brainstorming`

**Files:**

- Create: `skills/superpowers-brainstorming/SKILL.md`
- Create: `skills/superpowers-brainstorming/spec-document-reviewer-prompt.md`
- Create: `skills/superpowers-brainstorming/visual-companion.md`
- Create: `skills/superpowers-brainstorming/scripts/frame-template.html`
- Create: `skills/superpowers-brainstorming/scripts/helper.js`
- Create: `skills/superpowers-brainstorming/scripts/server.cjs`
- Create: `skills/superpowers-brainstorming/scripts/start-server.sh`
- Create: `skills/superpowers-brainstorming/scripts/stop-server.sh`

- [ ] **Step 1: Copy the visual-companion runtime**

```bash
mkdir -p skills/superpowers-brainstorming/scripts
cp superpowers/skills/brainstorming/SKILL.md skills/superpowers-brainstorming/SKILL.md
cp superpowers/skills/brainstorming/spec-document-reviewer-prompt.md skills/superpowers-brainstorming/spec-document-reviewer-prompt.md
cp superpowers/skills/brainstorming/visual-companion.md skills/superpowers-brainstorming/visual-companion.md
cp superpowers/skills/brainstorming/scripts/frame-template.html skills/superpowers-brainstorming/scripts/frame-template.html
cp superpowers/skills/brainstorming/scripts/helper.js skills/superpowers-brainstorming/scripts/helper.js
cp superpowers/skills/brainstorming/scripts/server.cjs skills/superpowers-brainstorming/scripts/server.cjs
cp superpowers/skills/brainstorming/scripts/start-server.sh skills/superpowers-brainstorming/scripts/start-server.sh
cp superpowers/skills/brainstorming/scripts/stop-server.sh skills/superpowers-brainstorming/scripts/stop-server.sh
```

- [ ] **Step 2: Rename the skill and repair the local companion link**

Use `apply_patch` to set `name: superpowers-brainstorming` and replace the final companion path with:

```markdown
[visual-companion.md](visual-companion.md)
```

- [ ] **Step 3: Make the planning handoff standalone**

Replace the checklist item, graph labels, terminal-state paragraph, and implementation section so they consistently say:

```markdown
Transition to implementation planning: use an available planning skill when one exists; otherwise create a detailed implementation plan directly. Do not begin implementation during brainstorming.
```

Retain the user review gate and the rule that implementation cannot begin before the plan exists.

- [ ] **Step 4: Validate skill and helper syntax**

Run:

```bash
python3 scripts/validate_superpowers_port.py --skill superpowers-brainstorming
python3 /Users/joejiang/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/superpowers-brainstorming
node --check skills/superpowers-brainstorming/scripts/helper.js
node --check skills/superpowers-brainstorming/scripts/server.cjs
bash -n skills/superpowers-brainstorming/scripts/start-server.sh
bash -n skills/superpowers-brainstorming/scripts/stop-server.sh
```

Expected: all commands exit 0.

- [ ] **Step 5: Commit the skill**

```bash
git add skills/superpowers-brainstorming
git commit -m "feat: add standalone prefixed brainstorming skill"
```

### Task 7: Add attribution and update repository policy

**Files:**

- Create: `THIRD_PARTY_NOTICES.md`
- Modify: `AGENTS.md`

- [ ] **Step 1: Add the upstream notice**

Create `THIRD_PARTY_NOTICES.md` with:

```markdown
# Third-Party Notices

## Superpowers skills

The `superpowers-*` skills in this repository are adapted from [obra/superpowers](https://github.com/obra/superpowers) at commit `d884ae04edebef577e82ff7c4e143debd0bbec99`.

MIT License

Copyright (c) 2025 Jesse Vincent

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 2: Update repository policy**

Change the project goal sentence in `AGENTS.md` to:

```markdown
This repo is `polish`: a personal collection of curated agent skills, including self-made skills and explicitly attributed adaptations.
```

Expand its verification block to run `quick_validate.py` for every `skills/*/SKILL.md`, while retaining all four JSON checks, plugin validation, and `git diff --check`.

- [ ] **Step 3: Verify the notice and policy**

Run:

```bash
rg -n "d884ae04|Copyright \(c\) 2025 Jesse Vincent|MIT License" THIRD_PARTY_NOTICES.md
test "$(cat CLAUDE.md)" = '@AGENTS.md'
```

Expected: the notice command finds all three provenance markers and the thin import check exits 0.

- [ ] **Step 4: Commit provenance changes**

```bash
git add THIRD_PARTY_NOTICES.md AGENTS.md
git commit -m "docs: attribute adapted superpowers skills"
```

### Task 8: Integrate the skills into collection documentation and manifests

**Files:**

- Modify: `README.md`
- Modify: `.codex-plugin/plugin.json`
- Modify: `.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`
- Modify: `.cursor-plugin/plugin.json`

- [ ] **Step 1: Update README collection wording and inventory**

Use the tagline `Personal collection of curated, self-made, and adapted agent skills.` and its accurate Chinese equivalent. Add all five `superpowers-*` names to both "Currently included" lists.

Add one English and one Chinese section that explain the family as a coherent workflow:

```text
superpowers-brainstorming → implementation planning
superpowers-test-driven-development → implementation
superpowers-systematic-debugging → investigation when behavior diverges
superpowers-verification-before-completion → evidence gate before success claims
superpowers-writing-skills → skill authoring and validation
```

State that these five skills are adapted from `obra/superpowers` and link `THIRD_PARTY_NOTICES.md`. Extend the structure tree with the five prefixed directories without expanding every supporting filename.

- [ ] **Step 2: Update plugin descriptions**

For all four manifests, preserve `name`, `version`, author, homepage, repository, and `skills`. Replace all-self-made claims with `curated, self-made, and adapted agent skills` and mention the prefixed Superpowers workflows in long descriptions.

Add these Codex/Cursor keywords where a keyword array exists:

```json
"brainstorming",
"systematic-debugging",
"test-driven-development",
"verification",
"skill-authoring"
```

Add these Codex default prompts:

```json
"Use superpowers-brainstorming to design this change before implementation.",
"Use superpowers-systematic-debugging to investigate this failure.",
"Use superpowers-verification-before-completion before claiming this work is done."
```

- [ ] **Step 3: Parse and validate metadata**

Run:

```bash
python3 -m json.tool .codex-plugin/plugin.json >/dev/null
python3 -m json.tool .claude-plugin/plugin.json >/dev/null
python3 -m json.tool .claude-plugin/marketplace.json >/dev/null
python3 -m json.tool .cursor-plugin/plugin.json >/dev/null
python3 /Users/joejiang/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py .
```

Expected: all five commands exit 0.

- [ ] **Step 4: Commit collection integration**

```bash
git add README.md .codex-plugin/plugin.json .claude-plugin/plugin.json .claude-plugin/marketplace.json .cursor-plugin/plugin.json
git commit -m "docs: integrate prefixed superpowers skills"
```

### Task 9: Run the complete verification gate

**Files:**

- Verify: all files changed by Tasks 1–8

- [ ] **Step 1: Validate all port invariants**

Run:

```bash
python3 scripts/validate_superpowers_port.py
```

Expected: `Validated 5 prefixed Superpowers skill(s).`

- [ ] **Step 2: Validate every canonical skill**

Run:

```bash
for skill in skills/*/SKILL.md; do
  python3 /Users/joejiang/.codex/skills/.system/skill-creator/scripts/quick_validate.py "$(dirname "$skill")"
done
```

Expected: eight successful validation results and no failures.

- [ ] **Step 3: Run repository validation**

Run:

```bash
python3 -m json.tool .codex-plugin/plugin.json >/dev/null
python3 -m json.tool .claude-plugin/plugin.json >/dev/null
python3 -m json.tool .claude-plugin/marketplace.json >/dev/null
python3 -m json.tool .cursor-plugin/plugin.json >/dev/null
python3 /Users/joejiang/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py .
git diff --check 80b9d6a..HEAD
```

Expected: all commands exit 0 and plugin validation reports success.

- [ ] **Step 4: Confirm scope and source preservation**

Run:

```bash
git status --short
git diff --name-only 80b9d6a..HEAD
git -C superpowers rev-parse HEAD
```

Expected:

- Root status shows only `?? superpowers/`.
- The diff contains only the plan, validator, five prefixed skill directories, notice, README, AGENTS, and four manifests.
- The upstream source still reports `d884ae04edebef577e82ff7c4e143debd0bbec99`.

- [ ] **Step 5: Review the final diff**

Run:

```bash
git diff --stat 80b9d6a..HEAD
git diff --check 80b9d6a..HEAD
```

Expected: the stat matches the planned scope and the whitespace check exits 0.
