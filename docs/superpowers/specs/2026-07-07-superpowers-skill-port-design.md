# Superpowers Skill Port Design

## Goal

Port five selected skills from the local `superpowers/skills/` source tree into the `polish` collection as independently installable, prefixed skills:

| Upstream skill | Polish skill |
| --- | --- |
| `brainstorming` | `superpowers-brainstorming` |
| `systematic-debugging` | `superpowers-systematic-debugging` |
| `verification-before-completion` | `superpowers-verification-before-completion` |
| `test-driven-development` | `superpowers-test-driven-development` |
| `writing-skills` | `superpowers-writing-skills` |

The upstream `superpowers/` directory remains an untracked, read-only source and is not included in the port.

## Porting Strategy

Use an adapted runtime-closure port rather than copying complete upstream directories or only copying `SKILL.md` files.

For each selected skill:

1. Copy the canonical `SKILL.md` into `skills/superpowers-<name>/SKILL.md`.
2. Copy every script, reference, example, or template directly required at runtime by that skill.
3. Exclude upstream creation logs, pressure-test fixtures, and other development-only artifacts that the runtime skill does not reference.
4. Change the YAML `name` to match the prefixed directory exactly.
5. Rewrite references among the five selected skills to their new `superpowers-*` names.
6. Rewrite local file links so they resolve from the new nested skill directory.

No root-level `SKILL.md` is introduced.

## Runtime Dependency Closure

### `superpowers-brainstorming`

Include its visual-companion documentation, prompts, HTML template, JavaScript helper/server, and lifecycle shell scripts because the skill explicitly offers and drives that workflow.

The upstream skill terminates by requiring `writing-plans`, which is outside the five selected skills. Replace that hard dependency with a capability-based handoff: use an available planning skill when one exists; otherwise write a concrete implementation plan directly. This keeps the port usable when `polish` is installed without the upstream Superpowers plugin.

### `superpowers-systematic-debugging`

Include the directly referenced debugging guides, condition-based waiting example, and polluter-finding helper. Exclude `CREATION-LOG.md` and pressure/academic test fixtures.

Rewrite its TDD and completion-verification cross-references to `superpowers-test-driven-development` and `superpowers-verification-before-completion`.

### `superpowers-verification-before-completion`

Include its self-contained `SKILL.md`. It has no required supporting files.

### `superpowers-test-driven-development`

Include `testing-anti-patterns.md`, which the skill directs agents to read when mocks or test utilities are involved.

### `superpowers-writing-skills`

Include the authoring references and tools linked by the skill: Anthropic best practices, subagent-testing methodology, persuasion principles, Graphviz conventions, renderer, and its reusable example material.

Rewrite its required TDD/debugging references and its examples to use the selected prefixed names.

## Collection Integration

Update the English and Chinese README sections to list and briefly explain the five new skills and show the expanded `skills/` structure. Keep `prompt-polish`, `file-singlify`, and `before-git-push` unchanged.

Update the Codex, Claude, marketplace, and Cursor plugin descriptions and relevant keywords so package metadata reflects the expanded collection. Preserve the package name `polish`, existing skill names, and current version values unless a validator requires a version change.

Because the new skills are adapted from third-party MIT-licensed material, replace claims that every skill is self-made with accurate "curated and adapted" wording. Add a repository-level third-party notice containing the upstream copyright and MIT license text, and link it from the README.

Update `AGENTS.md` only where repository policy or the verification commands must reflect the expanded collection. Keep `CLAUDE.md` as its existing thin import.

## Validation

Run the following before completion:

1. Parse all four JSON manifests with `python3 -m json.tool`.
2. Run `quick_validate.py` against all eight canonical skill directories, including each of the five new prefixed skills.
3. Run `validate_plugin.py .`.
4. Check that every relative Markdown link and referenced local file in the five new skill directories resolves.
5. Run representative syntax or smoke checks for copied executable helpers where supported by the local toolchain.
6. Run `git diff --check`.
7. Confirm `git status --short` still shows the upstream `superpowers/` tree as untracked and unmodified.

## Completion Criteria

The port is complete when all five prefixed skills are discoverable under `skills/`, their runtime files and cross-references resolve without requiring the upstream Superpowers plugin, collection documentation and metadata accurately describe their provenance, and all repository validation checks pass.
