#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"

EXPECTED = {
    "google-stitch-frontend-taste-design": {
        "SKILL.md",
        "assets/DESIGN.md",
        "references/taste-rules.md",
    },
    "google-stitch-extract-frontend-design-system": {
        "SKILL.md",
        "references/angular.md",
        "references/design-md-template.md",
        "references/plain-css.md",
        "references/react-tailwind.md",
        "references/svelte.md",
        "references/vue.md",
    },
    "google-stitch-frontend-brief-enhancer": {
        "SKILL.md",
        "references/brief-template.md",
        "references/ui-ux-keywords.md",
    },
    "google-stitch-shadcn-ui": {
        "SKILL.md",
        "examples/form-pattern.tsx",
        "references/component-catalog.md",
        "references/customization-guide.md",
        "references/migration-guide.md",
        "references/setup-guide.md",
        "scripts/verify-setup.sh",
    },
}

FORBIDDEN = {
    ".stitch/": "Stitch workspace path",
    "StitchMCP": "Stitch MCP tool",
    "generate_screen": "Stitch screen generation tool",
    "get_screen": "Stitch screen retrieval tool",
    "list_projects": "Stitch project lookup tool",
    "stitch*:*": "Stitch MCP wildcard",
    "upload-to-stitch": "upload skill dependency",
    "upload_to_stitch": "upload script dependency",
}

LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
DESCRIPTION_RE = re.compile(r"^description:\s*(.+)$", re.MULTILINE)


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


def validate_frontmatter(name: str, skill_md: Path) -> list[str]:
    text = skill_md.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) < 3:
        return [f"{name}: missing YAML frontmatter"]

    frontmatter = parts[1]
    errors: list[str] = []
    if f"\nname: {name}\n" not in f"\n{frontmatter}\n":
        errors.append(f"{name}: frontmatter name does not match directory")

    description = DESCRIPTION_RE.search(frontmatter)
    if not description:
        errors.append(f"{name}: missing one-line description")
    elif not description.group(1).startswith("Use when "):
        errors.append(f"{name}: description must start with 'Use when '")

    fields = {
        line.split(":", 1)[0].strip()
        for line in frontmatter.splitlines()
        if ":" in line
    }
    unexpected = fields - {"name", "description"}
    if unexpected:
        errors.append(
            f"{name}: unexpected frontmatter fields: {', '.join(sorted(unexpected))}"
        )
    return errors


def validate_links(path: Path, text: str) -> list[str]:
    errors: list[str] = []
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


def validate_skill(name: str) -> list[str]:
    skill_dir = SKILLS / name
    if not skill_dir.is_dir():
        return [f"{name}: missing directory"]

    errors: list[str] = []
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
        errors.extend(validate_frontmatter(name, skill_md))

    for path in skill_dir.rglob("*"):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for forbidden, label in FORBIDDEN.items():
            if forbidden.lower() in text.lower():
                errors.append(
                    f"{path.relative_to(ROOT)}: forbidden {label}: {forbidden}"
                )
        if path.suffix == ".md":
            errors.extend(validate_links(path, text))
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
    print(f"Validated {len(names)} Google Stitch frontend skill(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
