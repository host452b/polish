#!/usr/bin/env python3
"""Deterministic compiler, baseline verifier, and auditor for SKILL.md packages."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
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
VAGUE_COMPLETION_RE = re.compile(
    r"\b(?:until (?:everything |it )?(?:looks good|is clean|is high quality|feels right)(?:\s+and\s+high\s+quality)?|"
    r"verify (?:that )?everything looks good|"
    r"when you feel confident)\b|"
    r"(?:直到|确认)(?:一切|结果)?(?:看起来不错|没有问题|足够好|满意为止)",
    re.IGNORECASE,
)
REVERSIBLE_NAG_RE = re.compile(
    r"\b(?:ask (?:the )?user (?:for (?:confirmation|permission|approval)|to confirm) before (?:each|every) (?:file|step|edit|change)|"
    r"wait for (?:user )?(?:approval|confirmation) after (?:each|every) step)\b|"
    r"(?:每一步|每次修改文件前)都(?:必须|需要)?(?:先)?(?:询问|征求)用户确认",
    re.IGNORECASE,
)
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


def _normalize_prose_rule(line: str) -> str:
    stripped = line.strip()
    if not stripped or stripped.startswith(("#", "|", ">", "<!--", "---", "***")):
        return ""
    unbulleted = re.sub(r"^(?:[-*+]|\d+\.)\s+", "", stripped)
    compact = re.sub(r"\s+", " ", unbulleted).strip().lower()
    return compact if len(compact) >= 45 else ""


def _audit_skill_with_edges(
    skill_dir: Path,
    strict_codex: bool = True,
    collection_root: Path | None = None,
) -> tuple[list[Finding], set[str], dict[str, Any]]:
    findings: list[Finding] = []
    cross_edges: set[str] = set()
    skill_name = skill_dir.name
    skill_md = skill_dir / "SKILL.md"
    meta: dict[str, Any] = {"name": "", "desc_len": 0, "body_lines": 0, "errors": 0, "warnings": 0}

    if not skill_md.exists():
        findings.append(Finding("ERROR", "S001_MISSING_SKILL_MD", skill_name, str(skill_dir), "SKILL.md not found"))
        meta["errors"] = 1
        return findings, cross_edges, meta

    text = skill_md.read_text(encoding="utf-8", errors="replace")
    m = re.match(r"^---\n(.*?)\n---\n?", text, re.DOTALL)
    if not m:
        findings.append(Finding("ERROR", "S002_BAD_FRONTMATTER", skill_name, str(skill_md), "Missing or malformed YAML frontmatter"))
        meta["errors"] = 1
        return findings, cross_edges, meta

    fm_raw = m.group(1)
    hazard_findings = check_plain_yaml_hazards(fm_raw, skill_name, skill_md)
    findings.extend(hazard_findings)
    try:
        fm = parse_simple_yaml_mapping(fm_raw)
    except Exception as exc:
        if not hazard_findings:
            findings.append(Finding("ERROR", "S002_BAD_FRONTMATTER", skill_name, str(skill_md), f"YAML parse error: {exc}"))
        meta["errors"] = sum(1 for f in findings if f.severity == "ERROR")
        return findings, cross_edges, meta

    allowed = CODEX_STRICT_KEYS if strict_codex else ALLOWED_FRONTMATTER_KEYS
    extra = sorted(set(fm.keys()) - allowed)
    if extra:
        sev = "WARN" if set(extra) <= ALLOWED_FRONTMATTER_KEYS else "ERROR"
        findings.append(
            Finding(sev, "S003_FRONTMATTER_KEYS", skill_name, str(skill_md), f"Non-portable frontmatter keys: {', '.join(extra)}")
        )

    name = str(fm.get("name", "")).strip()
    meta["name"] = name
    if not name:
        findings.append(Finding("ERROR", "S004_MISSING_NAME", skill_name, str(skill_md), "Missing 'name' field"))
    else:
        if name != skill_name:
            findings.append(Finding("WARN", "S005_NAME_DIR_MISMATCH", skill_name, str(skill_md), f"Frontmatter name '{name}' != directory '{skill_name}'"))
        if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", name) or len(name) > 64:
            findings.append(Finding("ERROR", "S006_INVALID_KEBAB_NAME", skill_name, str(skill_md), f"Invalid kebab-case name '{name}'"))

    desc = str(fm.get("description", "")).strip()
    meta["desc_len"] = len(desc)
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
    meta["body_lines"] = len(lines)
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
    seen_prose_rules: dict[str, str] = {}
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
                if VAGUE_COMPLETION_RE.search(line_without_code):
                    findings.append(
                        Finding(
                            "WARN",
                            "D8_VAGUE_COMPLETION",
                            skill_name,
                            f"{skill_md}:{lineno}",
                            "Vague self-reported completion phrase; define a checkable condition and verify real output via script",
                        )
                    )
                if REVERSIBLE_NAG_RE.search(line_without_code):
                    findings.append(
                        Finding(
                            "WARN",
                            "D10_REVERSIBLE_CONFIRMATION_NAG",
                            skill_name,
                            f"{skill_md}:{lineno}",
                            "Confirmation nag on reversible work; advance reversible steps autonomously and gate only irreversible actions",
                        )
                    )
                norm_rule = _normalize_prose_rule(line_without_code)
                if norm_rule:
                    loc = f"{skill_md.name}:{lineno}"
                    if norm_rule in seen_prose_rules:
                        findings.append(
                            Finding(
                                "WARN",
                                "D9_REPEATED_PROSE_RULE",
                                skill_name,
                                f"{skill_md}:{lineno}",
                                f"Rule stated twice (first at {seen_prose_rules[norm_rule]}); encode into lint/type/script/schema and delete duplicate prose",
                            )
                        )
                    else:
                        seen_prose_rules[norm_rule] = loc

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
            oy = parse_simple_yaml_mapping(openai_yaml.read_text(encoding="utf-8", errors="replace"))
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

    meta["errors"] = sum(1 for f in findings if f.severity == "ERROR")
    meta["warnings"] = sum(1 for f in findings if f.severity == "WARN")
    return findings, cross_edges, meta


def audit_single_skill(skill_dir: Path, strict_codex: bool = True, collection_root: Path | None = None) -> list[Finding]:
    findings, _, _ = _audit_skill_with_edges(skill_dir, strict_codex=strict_codex, collection_root=collection_root)
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


def _collect_audit(target: Path, strict_codex: bool = True) -> tuple[list[Path], list[Finding], dict[str, dict[str, Any]]]:
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
    skills_meta: dict[str, dict[str, Any]] = {}
    for sd in skill_dirs:
        f_list, edges, meta = _audit_skill_with_edges(sd, strict_codex=strict_codex, collection_root=col_root)
        all_findings.extend(f_list)
        dag[sd.name] = edges
        skills_meta[sd.name] = meta

    for cyc in _detect_cycles(dag):
        chain = " -> ".join(cyc)
        all_findings.append(
            Finding("ERROR", "D5_SKILL_DAG_CYCLE", cyc[0], str(col_root or resolved), f"Circular cross-skill dependency: {chain}")
        )
    return skill_dirs, all_findings, skills_meta


def audit_collection(target: Path, strict_codex: bool = True) -> list[Finding]:
    _, findings, _ = _collect_audit(target, strict_codex=strict_codex)
    return findings


def build_report(target: Path, strict_codex: bool = True) -> dict[str, Any]:
    skill_dirs, all_findings, skills_meta = _collect_audit(target, strict_codex=strict_codex)
    errors = sum(1 for f in all_findings if f.severity == "ERROR")
    warns = sum(1 for f in all_findings if f.severity == "WARN")
    return {
        "scanned_skills": len(skill_dirs),
        "errors": errors,
        "warnings": warns,
        "findings": [asdict(f) for f in all_findings],
        "skills_meta": skills_meta,
    }


def verify_against_baseline(
    baseline: dict[str, Any],
    current: dict[str, Any],
    allow_rename: bool = False,
) -> list[Finding]:
    """Verify real post-polish disk artifacts against pre-polish baseline without trusting self-reports."""
    issues: list[Finding] = []
    cur_errors = int(current.get("errors", 0))
    if cur_errors > 0:
        issues.append(
            Finding("ERROR", "V001_UNRESOLVED_ERRORS", "*", "post-polish", f"Target still has {cur_errors} structural ERROR(s)")
        )

    base_warns = int(baseline.get("warnings", 0))
    cur_warns = int(current.get("warnings", 0))
    if cur_warns > base_warns:
        issues.append(
            Finding("ERROR", "V002_WARNING_REGRESSION", "*", "post-polish", f"Warning count regressed from {base_warns} to {cur_warns}")
        )

    base_meta: dict[str, Any] = baseline.get("skills_meta", {}) or {}
    cur_meta: dict[str, Any] = current.get("skills_meta", {}) or {}
    for s_key, b_info in sorted(base_meta.items()):
        c_info = cur_meta.get(s_key)
        if c_info is None:
            if not allow_rename:
                issues.append(
                    Finding("ERROR", "V003_SKILL_DROPPED_OR_RENAMED", s_key, "post-polish", f"Skill '{s_key}' vanished after polish without --allow-rename")
                )
            continue
        if not allow_rename and b_info.get("name") and c_info.get("name") != b_info.get("name"):
            issues.append(
                Finding(
                    "ERROR",
                    "V003_SKILL_DROPPED_OR_RENAMED",
                    s_key,
                    "post-polish",
                    f"Skill frontmatter name changed '{b_info.get('name')}' -> '{c_info.get('name')}' without --allow-rename",
                )
            )
        b_len = int(b_info.get("desc_len", 0))
        c_len = int(c_info.get("desc_len", 0))
        min_retained = max(60, int(min(b_len, 220) * 0.5))
        if b_len >= 80 and c_len < min_retained:
            issues.append(
                Finding(
                    "ERROR",
                    "V004_DESCRIPTION_GUTTED",
                    s_key,
                    "post-polish",
                    f"Description shrank from {b_len} to {c_len} chars (<{min_retained} floor); do not gut triggers to game length/SDO checks",
                )
            )
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit SKILL.md directories and verify provable post-polish improvements.")
    parser.add_argument("target", type=Path, help="Skill folder or parent directory containing skills")
    parser.add_argument("--json", action="store_true", help="Emit JSON report")
    parser.add_argument("--allow-devin-keys", "--allow-host-keys", dest="allow_host_keys", action="store_true", help="Allow extended host frontmatter keys without WARN")
    parser.add_argument("--save-baseline", type=Path, help="Write pre-polish baseline JSON to path and exit 0")
    parser.add_argument("--verify-against", type=Path, help="Verify real post-polish artifacts against a saved baseline JSON")
    parser.add_argument("--allow-rename", action="store_true", help="Allow intentional skill renames during --verify-against")
    args = parser.parse_args()

    resolved = args.target.resolve()
    if not discover_skill_dirs(resolved):
        print(f"No SKILL.md files found under {args.target}", file=sys.stderr)
        return 2

    report = build_report(resolved, strict_codex=not args.allow_host_keys)

    if args.save_baseline:
        args.save_baseline.parent.mkdir(parents=True, exist_ok=True)
        args.save_baseline.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(
            f"Saved baseline ({report['scanned_skills']} skill(s), {report['errors']} ERROR(s), {report['warnings']} WARN(s)) -> {args.save_baseline}"
        )
        return 0

    if args.verify_against:
        baseline = json.loads(args.verify_against.read_text(encoding="utf-8"))
        v_issues = verify_against_baseline(baseline, report, allow_rename=args.allow_rename)
        if args.json:
            print(
                json.dumps(
                    {**report, "verification_passed": len(v_issues) == 0, "verification_issues": [asdict(i) for i in v_issues]},
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            print(
                f"Scanned {report['scanned_skills']} skill(s): {report['errors']} ERROR(s), {report['warnings']} WARN(s) "
                f"(baseline: {baseline.get('errors', 0)} ERROR(s), {baseline.get('warnings', 0)} WARN(s))"
            )
            for f in report["findings"]:
                print(f"[{f['severity']}] {f['skill']} ({f['rule']}) -> {f['message']} [{f['file']}]")
            for vi in v_issues:
                print(f"[{vi.severity}] {vi.skill} ({vi.rule}) -> {vi.message} [{vi.file}]")
            if not v_issues:
                print("PASS_POLISH_VERIFICATION")
        return 1 if v_issues else 0

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"Scanned {report['scanned_skills']} skill(s): {report['errors']} ERROR(s), {report['warnings']} WARN(s)")
        for f in report["findings"]:
            print(f"[{f['severity']}] {f['skill']} ({f['rule']}) -> {f['message']} [{f['file']}]")

    return 1 if report["errors"] > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
