#!/usr/bin/env python3
"""Deterministic compiler and auditor for SKILL.md packages and skill collections."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import unquote

try:
    import yaml  # type: ignore
except ImportError:
    yaml = None


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
    (r"\b(covers|covering|includes step-by-step|walks through|then runs|first .* then)\b", "Workflow summary phrase in description risks SDO shortcut"),
    (r"含[^。；\n]{4,}(流程|原则|清单|公式|数据|步骤)", "Content inventory ('含...流程/清单') bloats always-loaded pointer"),
]
UNCONDITIONAL_REF_PATTERNS = [
    r"read all (?:files|documents|references) in `?references",
    r"阅读\s*`?references/?`?\s*(?:下|目录)?的?所有",
]
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
BACKTICK_PATH_RE = re.compile(r"`((?:chapter\d+|book|docs|references|scripts|assets)/[^`\s]+)`")
HARDCODED_SCRIPT_PATH_RE = re.compile(
    r"(?:(?:/Users|/home)/[A-Za-z0-9._-]+/[^\s\"')]*skills/|C:\\\\Users\\\\[A-Za-z0-9._-]+\\\\[^\s\"')]*skills\\\\|~/(?:\.claude|\.codex|\.cursor|\.agents|\.config/devin)/skills(?:/|[\"']))"
)
PLACEHOLDER_RE = re.compile(r"\b(?:remains a placeholder|is still a placeholder|TODO:\s*fill)\b", re.IGNORECASE)
SCAFFOLD_OPEN_RE = re.compile(r"<!--\s*model-scaffolding\b([^>]*)-->")
SCAFFOLD_CLOSE_RE = re.compile(r"<!--\s*/model-scaffolding\s*-->")


@dataclass
class Finding:
    severity: str  # ERROR | WARN | INFO
    rule: str
    skill: str
    file: str
    message: str


def check_plain_yaml_hazards(frontmatter: str, skill: str, skill_md: Path) -> list[Finding]:
    """Detect unquoted ': ', ' #', or leading YAML indicator chars on plain top-level scalars."""
    findings: list[Finding] = []
    for idx, line in enumerate(frontmatter.splitlines(), start=2):
        if not line.strip() or line[0].isspace() or line.lstrip().startswith("#"):
            continue
        field = re.match(r"^([A-Za-z_][\w-]*):(?: (.*))?$", line)
        if not field:
            findings.append(
                Finding("ERROR", "S002_BAD_FRONTMATTER", skill, f"{skill_md}:{idx}", f"Malformed YAML key line: {line}")
            )
            continue
        key, value = field.group(1), (field.group(2) or "").strip()
        if not value or re.match(r"^[>|][+-]?$", value):
            continue
        if (value.startswith("'") and value.endswith("'")) or (value.startswith('"') and value.endswith('"')):
            continue
        if re.match(r"^[-?:,\[\]{}#&*!|>'\"%@`]", value) or re.search(r": | #|:$", value):
            findings.append(
                Finding(
                    "ERROR",
                    "S002_PLAIN_YAML_HAZARD",
                    skill,
                    f"{skill_md}:{idx}",
                    f"Plain YAML scalar '{key}' contains unquoted ': ', ' #', or indicator char; use a folded block (>-) or quotes",
                )
            )
    return findings


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
        if not stripped or stripped.startswith("#") or line[0].isspace():
            i += 1
            continue
        if ":" not in line:
            raise ValueError(f"Invalid YAML line: {line}")
        key, val = line.split(":", 1)
        key = key.strip()
        val = val.strip()
        if re.match(r"^[>|][+-]?$", val):
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


def github_heading_slugs(md_text: str) -> set[str]:
    """Extract GitHub-flavored Markdown heading slugs and explicit <a id/name='...'> anchors."""
    slugs: set[str] = set()
    gfm_counts: dict[str, int] = {}
    collapsed_counts: dict[str, int] = {}
    in_fence = False
    for line in md_text.splitlines():
        if re.match(r"^\s*(`{3,}|~{3,})", line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for anchor_id in re.findall(r"<a\s+[^>]*?(?:id|name)=[\"']([^\"']+)[\"']", line, flags=re.IGNORECASE):
            slugs.add(anchor_id.lower())
        hm = re.match(r"^#{1,6}\s+(.+?)\s*#*$", line)
        if not hm:
            continue
        raw = re.sub(r"`([^`]*)`", r"\1", hm.group(1))
        raw = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", raw)
        raw = re.sub(r"<[^>]+>", "", raw)
        cleaned = re.sub(r"[^\w\s-]", "", raw.lower(), flags=re.UNICODE).strip()
        if not cleaned:
            continue
        gfm_base = cleaned.replace(" ", "-")
        idx = gfm_counts.get(gfm_base, 0)
        gfm_counts[gfm_base] = idx + 1
        slugs.add(gfm_base if idx == 0 else f"{gfm_base}-{idx}")

        col_base = re.sub(r"\s+", "-", cleaned)
        c_idx = collapsed_counts.get(col_base, 0)
        collapsed_counts[col_base] = c_idx + 1
        slugs.add(col_base if c_idx == 0 else f"{col_base}-{c_idx}")
    return slugs


def _audit_skill_with_edges(
    skill_dir: Path,
    strict_codex: bool = True,
    collection_root: Path | None = None,
) -> tuple[list[Finding], set[str]]:
    findings: list[Finding] = []
    cross_edges: set[str] = set()
    skill_name = skill_dir.name
    skill_md = skill_dir / "SKILL.md"

    if not skill_md.exists():
        findings.append(Finding("ERROR", "S001_MISSING_SKILL_MD", skill_name, str(skill_dir), "SKILL.md not found"))
        return findings, cross_edges

    text = skill_md.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n?", text, re.DOTALL)
    if not m:
        findings.append(Finding("ERROR", "S002_BAD_FRONTMATTER", skill_name, str(skill_md), "Missing or malformed YAML frontmatter"))
        return findings, cross_edges

    fm_raw = m.group(1)
    hazard_findings = check_plain_yaml_hazards(fm_raw, skill_name, skill_md)
    findings.extend(hazard_findings)
    try:
        fm = parse_simple_yaml_mapping(fm_raw)
    except Exception as exc:
        if not hazard_findings:
            findings.append(Finding("ERROR", "S002_BAD_FRONTMATTER", skill_name, str(skill_md), f"YAML parse error: {exc}"))
        return findings, cross_edges

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
        if not (desc.startswith(("Use when", "Use for")) or "时使用" in desc or "适用于" in desc):
            findings.append(Finding("WARN", "S011_WEAK_TRIGGER_PREFIX", skill_name, str(skill_md), "Description should front-load triggering conditions ('Use when...')"))
        for pat, reason in WORKFLOW_LEAK_PATTERNS:
            if re.search(pat, desc, re.IGNORECASE):
                findings.append(Finding("WARN", "D1_SDO_WORKFLOW_LEAK", skill_name, str(skill_md), reason))
                break

    body = text[m.end():]
    lines = body.splitlines()
    fm_line_offset = text[: m.end()].count("\n")

    is_thin_router = bool(
        re.search(r"\b(?:this (?:entry|skill|file) is a thin router|unified [^\n]{0,40} router)\b|本入口为薄路由|作为薄路由", body, re.IGNORECASE)
    )
    if is_thin_router and len(text) > 8000:
        findings.append(
            Finding("ERROR", "S015_ROUTER_BUDGET", skill_name, str(skill_md), f"Thin-router skill exceeds 8000-char budget ({len(text)} chars)")
        )
    if len(lines) > 350:
        findings.append(Finding("WARN", "D3_BODY_SPRAWL", skill_name, str(skill_md), f"SKILL.md body has {len(lines)} lines (>350); disclose heavy reference into references/"))
    for pat in UNCONDITIONAL_REF_PATTERNS:
        if re.search(pat, body, re.IGNORECASE):
            findings.append(
                Finding("WARN", "D3_UNCONDITIONAL_REF_LOAD", skill_name, str(skill_md), "Avoid reading all references unconditionally; route conditionally by branch")
            )
            break

    slug_cache: dict[Path, set[str]] = {}
    resolved_skill_dir = skill_dir.resolve()
    resolved_collection = collection_root.resolve() if collection_root else None

    for md_file in sorted(skill_dir.rglob("*.md")):
        md_text = md_file.read_text(encoding="utf-8", errors="replace")
        md_no_fences = re.sub(r"(?ms)^\s*(`{3,}|~{3,}).*?^\s*\1", "", md_text)
        md_no_code = re.sub(r"`[^`\n]*`", "", md_no_fences)
        opens = SCAFFOLD_OPEN_RE.findall(md_no_code)
        closes = SCAFFOLD_CLOSE_RE.findall(md_no_code)
        if len(opens) != len(closes):
            findings.append(Finding("ERROR", "D7_UNCLOSED_SCAFFOLDING", skill_name, str(md_file), "Unbalanced <!-- model-scaffolding --> block"))
        for attrs in opens:
            if "reason=" not in attrs or "review-on=" not in attrs:
                findings.append(
                    Finding("WARN", "D7_UNDATED_SCAFFOLDING", skill_name, str(md_file), 'model-scaffolding comment missing reason="..." or review-on="..."')
                )

        in_fence = False
        prev_num: int | None = None
        scan_lines = lines if md_file == skill_md else md_text.splitlines()
        line_offset = fm_line_offset if md_file == skill_md else 0

        for idx, line in enumerate(scan_lines, start=1):
            lineno = line_offset + idx
            if re.match(r"^\s*(`{3,}|~{3,})", line):
                in_fence = not in_fence
                continue
            if in_fence:
                continue

            line_without_code = re.sub(r"`[^`]*`", "", line)
            if PLACEHOLDER_RE.search(line_without_code):
                findings.append(Finding("WARN", "D7_STALE_PLACEHOLDER", skill_name, f"{md_file}:{lineno}", "Stale placeholder or TODO marker in live instructions"))

            if md_file == skill_md:
                if line.startswith("#"):
                    prev_num = None
                else:
                    num_match = re.match(r"^(\d+)\.\s+", line)
                    if num_match:
                        cur = int(num_match.group(1))
                        if prev_num is not None and cur == prev_num:
                            findings.append(Finding("WARN", "S012_DUPLICATE_STEP_NUMBER", skill_name, f"{skill_md}:{lineno}", f"Duplicate ordered step number '{cur}.'"))
                        prev_num = cur

                for rel_path in BACKTICK_PATH_RE.findall(line):
                    if "*" in rel_path or "<" in rel_path or ">" in rel_path:
                        if rel_path.startswith(("chapter", "book/", "docs/")):
                            findings.append(
                                Finding("WARN", "D4_REPO_COUPLED_PATH", skill_name, f"{skill_md}:{lineno}", f"Repo-coupled path '{rel_path}' breaks when skill is installed standalone")
                            )
                        continue
                    if rel_path.startswith(("references/", "scripts/", "assets/")):
                        if not (skill_dir / rel_path.rstrip("/")).exists():
                            findings.append(
                                Finding("ERROR", "D4_MISSING_RESOURCE", skill_name, f"{skill_md}:{lineno}", f"Referenced resource '{rel_path}' does not exist in skill dir")
                            )
                    elif rel_path.startswith(("chapter", "book/", "docs/")):
                        findings.append(
                            Finding("WARN", "D4_REPO_COUPLED_PATH", skill_name, f"{skill_md}:{lineno}", f"Repo-coupled path '{rel_path}' breaks when skill is installed standalone")
                        )

            for raw_target in MARKDOWN_LINK_RE.findall(line_without_code):
                if raw_target.startswith(("http://", "https://", "mailto:")):
                    continue
                path_part, _, frag = raw_target.partition("#")
                target_file = md_file.resolve() if not path_part else (md_file.parent / path_part).resolve()
                if not target_file.exists():
                    findings.append(Finding("ERROR", "D4_BROKEN_LINK", skill_name, f"{md_file}:{lineno}", f"Broken relative link '{raw_target}'"))
                    continue
                if not target_file.is_relative_to(resolved_skill_dir):
                    if resolved_collection and target_file.is_relative_to(resolved_collection):
                        rel_parts = target_file.relative_to(resolved_collection).parts
                        other_skill = rel_parts[0] if rel_parts else ""
                        if other_skill and other_skill != skill_name and (resolved_collection / other_skill / "SKILL.md").exists():
                            cross_edges.add(other_skill)
                            findings.append(
                                Finding(
                                    "WARN",
                                    "D5_CROSS_SKILL_LINK",
                                    skill_name,
                                    f"{md_file}:{lineno}",
                                    f"Cross-skill relative link to '{other_skill}' breaks standalone single-skill installation",
                                )
                            )
                        else:
                            findings.append(
                                Finding("WARN", "D4_REPO_COUPLED_PATH", skill_name, f"{md_file}:{lineno}", f"Repo-coupled relative link '{raw_target}' outside skill package")
                            )
                    else:
                        findings.append(
                            Finding("WARN", "D4_REPO_COUPLED_PATH", skill_name, f"{md_file}:{lineno}", f"Repo-coupled relative link '{raw_target}' outside skill package")
                        )
                if frag and target_file.is_file() and target_file.suffix.lower() == ".md":
                    if target_file not in slug_cache:
                        slug_cache[target_file] = github_heading_slugs(target_file.read_text(encoding="utf-8", errors="replace"))
                    decoded_frag = unquote(frag).lower()
                    if frag.lower() not in slug_cache[target_file] and decoded_frag not in slug_cache[target_file]:
                        findings.append(
                            Finding("ERROR", "D4_BROKEN_ANCHOR", skill_name, f"{md_file}:{lineno}", f"Broken Markdown anchor '#{frag}' in '{target_file.name}'")
                        )

    scripts_dir = skill_dir / "scripts"
    this_script = Path(__file__).resolve()
    if scripts_dir.is_dir():
        for script_file in sorted(scripts_dir.rglob("*")):
            if not script_file.is_file() or script_file.suffix.lower() not in {".py", ".sh", ".js", ".mjs", ".cjs", ".ts"}:
                continue
            if script_file.resolve() == this_script:
                continue
            script_text = script_file.read_text(encoding="utf-8", errors="ignore")
            for idx, sline in enumerate(script_text.splitlines(), start=1):
                if HARDCODED_SCRIPT_PATH_RE.search(sline):
                    findings.append(
                        Finding(
                            "WARN",
                            "D6_SCRIPT_HARDCODED_PATH",
                            skill_name,
                            f"{script_file}:{idx}",
                            "Bundled script hardcodes workstation or host skill path instead of self-locating relative to itself",
                        )
                    )

    openai_yaml = skill_dir / "agents" / "openai.yaml"
    if openai_yaml.exists():
        try:
            oy = parse_simple_yaml_mapping(openai_yaml.read_text(encoding="utf-8"))
            if isinstance(oy, dict):
                iface = oy.get("interface", {}) or {}
                if isinstance(iface, dict):
                    dn = str(iface.get("display_name", "")).strip()
                    dp = str(iface.get("default_prompt", "")).strip()
                    if dn and dn != skill_name:
                        findings.append(
                            Finding("WARN", "S016_OPENAI_DISPLAY_NAME", skill_name, str(openai_yaml), f"display_name '{dn}' != '{skill_name}'")
                        )
                    if dp and f"${skill_name}" not in dp:
                        findings.append(Finding("WARN", "S013_OPENAI_YAML_PROMPT", skill_name, str(openai_yaml), f"default_prompt does not mention '${skill_name}'"))
        except Exception as exc:
            findings.append(Finding("ERROR", "S014_BAD_OPENAI_YAML", skill_name, str(openai_yaml), f"Invalid YAML: {exc}"))

    return findings, cross_edges


def audit_single_skill(skill_dir: Path, strict_codex: bool = True, collection_root: Path | None = None) -> list[Finding]:
    findings, _ = _audit_skill_with_edges(skill_dir, strict_codex=strict_codex, collection_root=collection_root)
    return findings


def _detect_cycles(graph: dict[str, set[str]]) -> list[list[str]]:
    visited: set[str] = set()
    stack: list[str] = []
    on_stack: set[str] = set()
    cycles: list[list[str]] = []

    def dfs(node: str) -> None:
        visited.add(node)
        stack.append(node)
        on_stack.add(node)
        for nxt in sorted(graph.get(node, ())):
            if nxt not in graph:
                continue
            if nxt not in visited:
                dfs(nxt)
            elif nxt in on_stack:
                idx = stack.index(nxt)
                cycles.append(stack[idx:] + [nxt])
        stack.pop()
        on_stack.remove(node)

    for n in sorted(graph):
        if n not in visited:
            dfs(n)
    return cycles


def discover_skill_dirs(target: Path) -> list[Path]:
    if (target / "SKILL.md").exists():
        return [target]
    return sorted({p.parent for p in target.rglob("SKILL.md")})


def audit_collection(target: Path, strict_codex: bool = True) -> list[Finding]:
    resolved = target.resolve()
    skill_dirs = discover_skill_dirs(resolved)
    col_root: Path | None = None
    if len(skill_dirs) > 1:
        col_root = resolved
    elif len(skill_dirs) == 1:
        parent = skill_dirs[0].parent
        if any((p / "SKILL.md").exists() for p in parent.iterdir() if p.is_dir() and p != skill_dirs[0]):
            col_root = parent

    all_findings: list[Finding] = []
    dag: dict[str, set[str]] = {}
    for sd in skill_dirs:
        f_list, edges = _audit_skill_with_edges(sd, strict_codex=strict_codex, collection_root=col_root)
        all_findings.extend(f_list)
        dag[sd.name] = edges

    for cyc in _detect_cycles(dag):
        chain = " -> ".join(cyc)
        all_findings.append(
            Finding("ERROR", "D5_SKILL_DAG_CYCLE", cyc[0], str(col_root or resolved), f"Circular cross-skill dependency: {chain}")
        )
    return all_findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit SKILL.md directories for structural, routing, DAG, cache, and portability defects.")
    parser.add_argument("target", type=Path, help="Skill folder or parent directory containing skills")
    parser.add_argument("--json", action="store_true", help="Emit JSON report")
    parser.add_argument("--allow-devin-keys", "--allow-host-keys", dest="allow_host_keys", action="store_true", help="Allow extended host frontmatter keys without WARN")
    args = parser.parse_args()

    resolved = args.target.resolve()
    skill_dirs = discover_skill_dirs(resolved)
    if not skill_dirs:
        print(f"No SKILL.md files found under {args.target}", file=sys.stderr)
        return 2

    all_findings = audit_collection(resolved, strict_codex=not args.allow_host_keys)
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
