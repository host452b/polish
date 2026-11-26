#!/usr/bin/env python3
"""Deterministic auditor for SKILL.md packages and skill collections."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None


def parse_simple_yaml_mapping(raw: str) -> dict:
    """Zero-dependency YAML mapping parser for SKILL.md frontmatter and openai.yaml."""
    if yaml is not None:
        parsed = yaml.safe_load(raw)
        if not isinstance(parsed, dict):
            raise ValueError("YAML root must be a mapping")
        return parsed

    result: dict = {}
    lines = raw.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        if line[0].isspace():
            i += 1
            continue
        if ":" not in line:
            raise ValueError(f"Invalid YAML line: {line}")
        key, val = line.split(":", 1)
        key = key.strip()
        val = val.strip()
        if val in (">-", ">", "|", "|-"):
            folded: list[str] = []
            i += 1
            while i < len(lines) and (not lines[i].strip() or lines[i][0].isspace()):
                if lines[i].strip():
                    folded.append(lines[i].strip())
                i += 1
            result[key] = (" ".join(folded) if val.startswith(">") else "\n".join(folded)).strip()
            continue
        if val == "":
            nested: dict = {}
            items: list = []
            i += 1
            while i < len(lines) and (not lines[i].strip() or lines[i][0].isspace()):
                sub = lines[i].strip()
                if not sub or sub.startswith("#"):
                    i += 1
                    continue
                if sub.startswith("- "):
                    items.append(sub[2:].strip().strip("\"'"))
                elif ":" in sub:
                    sk, sv = sub.split(":", 1)
                    nested[sk.strip()] = sv.strip().strip("\"'")
                i += 1
            result[key] = items if items else nested
            continue
        if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
            val = val[1:-1]
        result[key] = val
        i += 1
    return result

ALLOWED_FRONTMATTER_KEYS = {
    "name",
    "description",
    "license",
    "allowed-tools",
    "metadata",
    "argument-hint",
    "model",
    "subagent",
    "agent",
    "permissions",
    "triggers",
    "disable-model-invocation",
}
CODEX_STRICT_KEYS = {"name", "description", "license", "allowed-tools", "metadata"}
WORKFLOW_LEAK_PATTERNS = [
    (r"—{1,2}\s*(覆盖|涵盖|包括|包含)", "Chinese dash summary ('——覆盖/涵盖') leaks body contents into description"),
    (r"\b(covers|covering|includes step-by-step|walks through|then runs)\b", "Workflow summary phrase in description risks SDO shortcut"),
    (r"含[^。；\n]{4,}(流程|原则|清单|公式|数据|步骤)", "Content inventory ('含...流程/清单') bloats always-loaded pointer"),
]
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
BACKTICK_PATH_RE = re.compile(r"`((?:chapter\d+|book|docs|references|scripts|assets)/[^`\s]+)`")


@dataclass
class Finding:
    severity: str  # ERROR | WARN | INFO
    rule: str
    skill: str
    file: str
    message: str


def audit_single_skill(skill_dir: Path, strict_codex: bool = True) -> list[Finding]:
    findings: list[Finding] = []
    skill_name = skill_dir.name
    skill_md = skill_dir / "SKILL.md"

    if not skill_md.exists():
        findings.append(Finding("ERROR", "S001_MISSING_SKILL_MD", skill_name, str(skill_dir), "SKILL.md not found"))
        return findings

    text = skill_md.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n?", text, re.DOTALL)
    if not m:
        findings.append(Finding("ERROR", "S002_BAD_FRONTMATTER", skill_name, str(skill_md), "Missing or malformed YAML frontmatter"))
        return findings

    try:
        fm = parse_simple_yaml_mapping(m.group(1))
    except Exception as exc:
        findings.append(Finding("ERROR", "S002_BAD_FRONTMATTER", skill_name, str(skill_md), f"YAML parse error: {exc}"))
        return findings

    allowed = CODEX_STRICT_KEYS if strict_codex else ALLOWED_FRONTMATTER_KEYS
    extra = sorted(set(fm.keys()) - allowed)
    if extra:
        sev = "WARN" if set(extra) <= ALLOWED_FRONTMATTER_KEYS else "ERROR"
        findings.append(
            Finding(sev, "S003_FRONTMATTER_KEYS", skill_name, str(skill_md), f"Non-portable frontmatter keys: {', '.join(extra)}")
        )

    name = str(fm.get("name", "")).strip()
    if not name:
        findings.append(Finding("ERROR", "S004_MISSING_NAME", skill_name, str(skill_md), "Missing 'name' field"))
    else:
        if name != skill_name:
            findings.append(Finding("WARN", "S005_NAME_DIR_MISMATCH", skill_name, str(skill_md), f"Frontmatter name '{name}' != directory '{skill_name}'"))
        if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", name) or len(name) > 64:
            findings.append(Finding("ERROR", "S006_INVALID_KEBAB_NAME", skill_name, str(skill_md), f"Invalid kebab-case name '{name}'"))

    desc = str(fm.get("description", "")).strip()
    if not desc:
        findings.append(Finding("ERROR", "S007_MISSING_DESC", skill_name, str(skill_md), "Missing 'description' field"))
    else:
        if "<" in desc or ">" in desc:
            findings.append(Finding("ERROR", "S008_ANGLE_BRACKETS_IN_DESC", skill_name, str(skill_md), "Angle brackets (< or >) in description break strict validators"))
        if len(desc) > 1024:
            findings.append(Finding("ERROR", "S009_DESC_TOO_LONG", skill_name, str(skill_md), f"Description length {len(desc)} > 1024 chars"))
        elif len(desc) > 500:
            findings.append(Finding("WARN", "S010_DESC_HEAVY_LOAD", skill_name, str(skill_md), f"Description length {len(desc)} > 500 chars; prune context load"))
        if not (desc.startswith("Use when") or "时使用" in desc or "Use for" in desc):
            findings.append(Finding("WARN", "S011_WEAK_TRIGGER_PREFIX", skill_name, str(skill_md), "Description should front-load triggering conditions ('Use when...')"))
        for pat, reason in WORKFLOW_LEAK_PATTERNS:
            if re.search(pat, desc, re.IGNORECASE):
                findings.append(Finding("WARN", "D1_SDO_WORKFLOW_LEAK", skill_name, str(skill_md), reason))
                break

    body = text[m.end():]
    lines = body.splitlines()
    if len(lines) > 350:
        findings.append(Finding("WARN", "D3_BODY_SPRAWL", skill_name, str(skill_md), f"SKILL.md body has {len(lines)} lines (>350); disclose heavy reference into references/"))

    # Check markdown relative links
    for target in MARKDOWN_LINK_RE.findall(body):
        clean = target.split("#", 1)[0].strip()
        if not clean or clean.startswith(("http://", "https://", "mailto:")):
            continue
        resolved = (skill_dir / clean).resolve()
        if not resolved.exists():
            findings.append(Finding("ERROR", "D4_BROKEN_LINK", skill_name, str(skill_md), f"Broken relative link '{target}'"))

    # Check unbundled repo-coupled backtick paths outside fenced code blocks
    in_fence = False
    for lineno, line in enumerate(lines, start=1):
        if re.match(r"^\s*(`{3,}|~{3,})", line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for rel_path in BACKTICK_PATH_RE.findall(line):
            if rel_path.startswith(("references/", "scripts/", "assets/")):
                if not (skill_dir / rel_path.rstrip("/")).exists():
                    findings.append(
                        Finding("ERROR", "D4_MISSING_RESOURCE", skill_name, f"{skill_md}:{lineno}", f"Referenced resource '{rel_path}' does not exist in skill dir")
                    )
            elif rel_path.startswith(("chapter", "book/", "docs/")):
                findings.append(
                    Finding("WARN", "D4_REPO_COUPLED_PATH", skill_name, f"{skill_md}:{lineno}", f"Repo-coupled path '{rel_path}' breaks when skill is installed standalone")
                )

    # Check numbered list monotonicity outside code fences
    in_fence = False
    prev_num: int | None = None
    for lineno, line in enumerate(lines, start=1):
        if re.match(r"^\s*(`{3,}|~{3,})", line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if line.startswith("#"):
            prev_num = None
            continue
        num_match = re.match(r"^(\d+)\.\s+", line)
        if num_match:
            cur = int(num_match.group(1))
            if prev_num is not None and cur == prev_num:
                findings.append(Finding("WARN", "S012_DUPLICATE_STEP_NUMBER", skill_name, f"{skill_md}:{lineno}", f"Duplicate ordered step number '{cur}.'"))
            prev_num = cur

    openai_yaml = skill_dir / "agents" / "openai.yaml"
    if openai_yaml.exists():
        try:
            oy = parse_simple_yaml_mapping(openai_yaml.read_text(encoding="utf-8"))
            if isinstance(oy, dict):
                iface = oy.get("interface", {}) or {}
                dp = str(iface.get("default_prompt", ""))
                if dp and f"${skill_name}" not in dp:
                    findings.append(Finding("WARN", "S013_OPENAI_YAML_PROMPT", skill_name, str(openai_yaml), f"default_prompt does not mention '${skill_name}'"))
        except Exception as exc:
            findings.append(Finding("ERROR", "S014_BAD_OPENAI_YAML", skill_name, str(openai_yaml), f"Invalid YAML: {exc}"))

    return findings


def discover_skill_dirs(target: Path) -> list[Path]:
    if (target / "SKILL.md").exists():
        return [target]
    found = sorted({p.parent for p in target.rglob("SKILL.md")})
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit SKILL.md directories for structural, routing, cache, and portability defects.")
    parser.add_argument("target", type=Path, help="Skill folder or parent directory containing skills")
    parser.add_argument("--json", action="store_true", help="Emit JSON report")
    parser.add_argument("--allow-devin-keys", action="store_true", help="Allow Devin-specific frontmatter keys without WARN")
    args = parser.parse_args()

    skill_dirs = discover_skill_dirs(args.target.resolve())
    if not skill_dirs:
        print(f"No SKILL.md files found under {args.target}", file=sys.stderr)
        return 2

    all_findings: list[Finding] = []
    for sd in skill_dirs:
        all_findings.extend(audit_single_skill(sd, strict_codex=not args.allow_devin_keys))

    errors = sum(1 for f in all_findings if f.severity == "ERROR")
    warns = sum(1 for f in all_findings if f.severity == "WARN")

    if args.json:
        print(
            json.dumps(
                {
                    "scanned_skills": len(skill_dirs),
                    "errors": errors,
                    "warnings": warns,
                    "findings": [asdict(f) for f in all_findings],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(f"Scanned {len(skill_dirs)} skill(s): {errors} ERROR(s), {warns} WARN(s)")
        for f in all_findings:
            print(f"[{f.severity}] {f.skill} ({f.rule}) -> {f.message} [{f.file}]")

    return 1 if errors > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
