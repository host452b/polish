#!/usr/bin/env python3
"""Zero-dependency static fragility scanner for Python and TypeScript/JavaScript AI Agent codebases."""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

SKIP_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    "dist",
    "build",
    ".next",
    ".tox",
    ".mypy_cache",
}
CODE_EXTS = {".py", ".ts", ".tsx", ".js", ".jsx", ".mjs"}

DYNAMIC_CALL_RE = re.compile(
    r"\b(datetime\.now|datetime\.utcnow|time\.time|uuid\.uuid4|Date\.now|new\s+Date\s*\(|Math\.random|crypto\.randomUUID)\b"
)
SYSTEM_ROLE_RE = re.compile(r"""['"]role['"]\s*:\s*['"]system['"]""")
USER_ROLE_RE = re.compile(r"""['"]role['"]\s*:\s*['"]user['"]""")
TOOL_RESULT_MARKER_RE = re.compile(r"(tool_call_id|<tool_response>|tool_result|function_call_output)", re.IGNORECASE)
STREAM_CALL_RE = re.compile(r"(\bstream\s*=\s*True\b|\bstream\s*:\s*true\b|\.stream\s*\()")
TIMEOUT_RE = re.compile(r"\b(timeout|idle_timeout|read_timeout|watchdog|AbortSignal|AbortController)\b", re.IGNORECASE)
MUTATION_FN_RE = re.compile(
    r"(?:^|_)(refund|send_email|charge|transfer_funds|create_order|cancel_reservation|pay_invoice)(?:$|_)",
    re.IGNORECASE,
)
IDEMPOTENCY_RE = re.compile(r"\b(idempotency_key|idempotent|dedupe_key|request_id|outbox)\b", re.IGNORECASE)
UNSAFE_EXEC_RE = re.compile(r"\b(os\.system\s*\(|child_process\.exec\s*\()")


@dataclass
class FragilityFinding:
    severity: str  # HIGH | MEDIUM
    rule: str
    file: str
    line: int
    evidence: str
    remediation: str


def iter_source_files(target: Path) -> list[Path]:
    if target.is_file():
        return [target] if target.suffix in CODE_EXTS else []
    files: list[Path] = []
    for p in sorted(target.rglob("*")):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.is_file() and p.suffix in CODE_EXTS:
            files.append(p)
    return files


def scan_python_ast(path: Path, source: str) -> list[FragilityFinding]:
    findings: list[FragilityFinding] = []
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return findings

    lines = source.splitlines()

    for node in ast.walk(tree):
        # H005: subprocess(..., shell=True)
        if isinstance(node, ast.Call):
            func_name = ast.unparse(node.func) if hasattr(ast, "unparse") else ""
            if func_name.endswith(("subprocess.run", "subprocess.Popen", "subprocess.call", "subprocess.check_output")):
                for kw in node.keywords:
                    if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                        ln = getattr(node, "lineno", 1)
                        findings.append(
                            FragilityFinding(
                                "HIGH",
                                "H005_SHELL_TRUE_EXEC",
                                str(path),
                                ln,
                                lines[ln - 1].strip() if ln <= len(lines) else func_name,
                                "Pass argv list with shell=False and enforce workspace/network sandbox boundaries.",
                            )
                        )

        # H003: Unbounded `while True:` containing tool/LLM/retry calls without a step/attempt counter
        if isinstance(node, ast.While) and isinstance(node.test, ast.Constant) and node.test.value is True:
            segment = ast.get_source_segment(source, node) or ""
            if re.search(r"\b(chat\.completions|responses\.create|execute_tool|tool_calls|retry)\b", segment):
                if not re.search(r"\b(max_turns|max_steps|max_retries|budget|attempts|rounds)\b", segment):
                    ln = getattr(node, "lineno", 1)
                    findings.append(
                        FragilityFinding(
                            "HIGH",
                            "H003_UNBOUNDED_AGENT_OR_RETRY_LOOP",
                            str(path),
                            ln,
                            lines[ln - 1].strip() if ln <= len(lines) else "while True:",
                            "Bind every agent/recovery loop to explicit turn, cost, and 3-strike circuit-breaker caps.",
                        )
                    )

        # H006: Side-effecting mutation function missing idempotency key / outbox check
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and MUTATION_FN_RE.search(node.name):
            segment = ast.get_source_segment(source, node) or ""
            if not IDEMPOTENCY_RE.search(segment):
                ln = getattr(node, "lineno", 1)
                findings.append(
                    FragilityFinding(
                        "MEDIUM",
                        "H006_MUTATION_WITHOUT_IDEMPOTENCY",
                        str(path),
                        ln,
                        f"def {node.name}(...)",
                        "Persist intent + idempotency_key before network I/O and reconcile remote state before retry.",
                    )
                )

    return findings


def scan_text_patterns(path: Path, source: str) -> list[FragilityFinding]:
    findings: list[FragilityFinding] = []
    lines = source.splitlines()
    file_has_timeout = bool(TIMEOUT_RE.search(source))

    for idx, line in enumerate(lines, start=1):
        window = "\n".join(lines[max(0, idx - 2) : min(len(lines), idx + 3)])

        # H001: Dynamic timestamp/UUID interpolated directly inside system role message
        if SYSTEM_ROLE_RE.search(line) and DYNAMIC_CALL_RE.search(window):
            findings.append(
                FragilityFinding(
                    "HIGH",
                    "H001_DYNAMIC_SYSTEM_PREFIX_CACHE_BUST",
                    str(path),
                    idx,
                    line.strip(),
                    "Keep system prompt byte-identical; append timestamps/counters in a tail <agent_status> message.",
                )
            )

        # H004: Tool result injected with role='user'
        if USER_ROLE_RE.search(line) and TOOL_RESULT_MARKER_RE.search(window):
            findings.append(
                FragilityFinding(
                    "HIGH",
                    "H004_TOOL_RESULT_IN_USER_ROLE",
                    str(path),
                    idx,
                    line.strip(),
                    "Send tool outputs via role='tool' paired with tool_call_id to preserve <think> state and provenance.",
                )
            )

        # H002: Streaming LLM call in a file with zero timeout / idle watchdog handling
        if STREAM_CALL_RE.search(line) and not file_has_timeout:
            findings.append(
                FragilityFinding(
                    "MEDIUM",
                    "H002_STREAM_WITHOUT_IDLE_WATCHDOG",
                    str(path),
                    idx,
                    line.strip(),
                    "Configure both connect timeout and inter-chunk read/idle watchdog to prevent silent stream hangs.",
                )
            )

        # H005b: os.system / child_process.exec
        if UNSAFE_EXEC_RE.search(line):
            findings.append(
                FragilityFinding(
                    "HIGH",
                    "H005_SHELL_STRING_EXEC",
                    str(path),
                    idx,
                    line.strip(),
                    "Avoid shell string execution; parse structured args and run inside an isolated sandbox.",
                )
            )

        # H007: Reconstructing assistant tool_calls dict manually without preserving reasoning_content/thinking
        if re.search(r"""['"]tool_calls['"]\s*:""", line) and re.search(r"""['"]role['"]\s*:\s*['"]assistant['"]""", window):
            wide = "\n".join(lines[max(0, idx - 5) : min(len(lines), idx + 6)])
            if not re.search(r"(reasoning_content|thinking|model_dump)", wide):
                findings.append(
                    FragilityFinding(
                        "MEDIUM",
                        "H007_DROPPED_REASONING_IN_TOOL_LOOP",
                        str(path),
                        idx,
                        line.strip(),
                        "Preserve provider reasoning_content / signed thinking blocks (or neutral trajectory slots) across tool turns.",
                    )
                )

    return findings


def scan_target(target: Path) -> list[FragilityFinding]:
    all_findings: list[FragilityFinding] = []
    seen: set[tuple[str, str, int]] = set()
    for fpath in iter_source_files(target):
        try:
            src = fpath.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        items = scan_text_patterns(fpath, src)
        if fpath.suffix == ".py":
            items.extend(scan_python_ast(fpath, src))
        for item in items:
            key = (item.rule, item.file, item.line)
            if key not in seen:
                seen.add(key)
                all_findings.append(item)
    return all_findings


def main() -> int:
    p = argparse.ArgumentParser(description="Scan Python/TS/JS agent codebases for Harness fragility anti-patterns.")
    p.add_argument("target", type=Path, help="Repository directory or source file to scan")
    p.add_argument("--json", action="store_true", help="Output JSON report")
    args = p.parse_args()

    target = args.target.resolve()
    files = iter_source_files(target)
    findings = scan_target(target)
    high = sum(1 for f in findings if f.severity == "HIGH")
    med = sum(1 for f in findings if f.severity == "MEDIUM")

    if args.json:
        print(
            json.dumps(
                {
                    "scanned_files": len(files),
                    "high_count": high,
                    "medium_count": med,
                    "findings": [asdict(f) for f in findings],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(f"Scanned {len(files)} source file(s): {high} HIGH, {med} MEDIUM finding(s)")
        for f in findings:
            print(f"[{f.severity}] {f.rule} at {f.file}:{f.line} -> {f.evidence}")
            print(f"  Fix: {f.remediation}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
