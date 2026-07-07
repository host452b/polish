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
