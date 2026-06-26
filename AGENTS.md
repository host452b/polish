# Repository Instructions

## Project Goal

This repo is `polish`: a personal collection of curated, self-made agent skills.
Treat the repo/plugin package name as `polish`, but keep individual skill names stable.
The current skill is `prompt-polish`.

## Layout

- `.codex-plugin/plugin.json` is the Codex plugin manifest.
- `.claude-plugin/` contains Claude plugin and marketplace metadata.
- `.cursor-plugin/plugin.json` contains Cursor plugin metadata.
- `skills/<skill-name>/SKILL.md` is the canonical location for each skill.
- `skills/prompt-polish/SKILL.md` is the canonical implementation of the current prompt-polishing skill.
- `references/strategies.md` supports `prompt-polish`; keep links from the skill relative to its nested location.

Do not put canonical skill instructions in a root-level `SKILL.md`. Root docs are for repo-level documentation only.

## Editing Rules

- Keep `prompt-polish` as the skill name and `skills/prompt-polish/` as its path unless the user explicitly asks to rename the skill itself.
- Use `polish` for the repo/plugin/package name and install commands.
- Keep README wording collection-oriented: this repo is a growing personal skill collection, not a single-purpose prompt-polish repo.
- When adding a new skill, add it under `skills/<new-skill-name>/SKILL.md` and update README plus plugin metadata only as needed.
- Keep `CLAUDE.md` as a thin import of this file; put shared repo policy here.

## Verification

Run these checks after changing manifests, docs, or skills:

```bash
python3 -m json.tool .codex-plugin/plugin.json >/dev/null
python3 -m json.tool .claude-plugin/plugin.json >/dev/null
python3 -m json.tool .claude-plugin/marketplace.json >/dev/null
python3 -m json.tool .cursor-plugin/plugin.json >/dev/null
python3 /Users/joejiang/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/prompt-polish
python3 /Users/joejiang/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py .
git diff --check
```
