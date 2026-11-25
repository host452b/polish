#!/usr/bin/env python3
"""Read-only preflight checker comparing upstream-sources.json pins against live upstream HEADs."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "upstream-sources.json"


def _resolve_remote_tip(repo: str, url: str) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            ["gh", "api", f"repos/{repo}/commits/HEAD"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            payload = json.loads(proc.stdout)
            commit = payload.get("commit", {})
            return {
                "tip": payload["sha"],
                "date": commit.get("committer", {}).get("date", "")[:10],
                "subject": commit.get("message", "").splitlines()[0][:80],
                "method": "gh-api",
            }
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError, KeyError):
        pass

    proc = subprocess.run(
        ["git", "ls-remote", f"{url.rstrip('/')}.git", "HEAD"],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    if proc.returncode == 0 and proc.stdout.strip():
        sha = proc.stdout.split()[0]
        return {"tip": sha, "date": "", "subject": "", "method": "git-ls-remote"}

    err = (proc.stderr or "unable to query remote HEAD").strip().splitlines()[0]
    return {"tip": None, "error": err}


def check_sources(manifest_path: Path, skill_filter: set[str]) -> list[dict[str, Any]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    selected: list[dict[str, Any]] = []
    for source in manifest.get("sources", []):
        entries = source.get("entries", [])
        if skill_filter:
            entries = [e for e in entries if e.get("skill") in skill_filter]
            if not entries:
                continue
        selected.append({**source, "entries": entries})

    results: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(8, max(1, len(selected)))) as pool:
        future_map = {
            pool.submit(_resolve_remote_tip, src["repo"], src["url"]): src for src in selected
        }
        for fut, src in [(f, future_map[f]) for f in future_map]:
            info = fut.result()
            base = src["commit"]
            tip = info.get("tip")
            skills = sorted({e["skill"] for e in src["entries"]})
            if tip is None:
                status = "ERROR"
            elif tip == base:
                status = "UP_TO_DATE"
            else:
                status = "DRIFTED"
            results.append(
                {
                    "id": src["id"],
                    "repo": src["repo"],
                    "base": base,
                    "tip": tip,
                    "status": status,
                    "tip_date": info.get("date", ""),
                    "tip_subject": info.get("subject", ""),
                    "compare_url": (
                        f"{src['url'].rstrip('/')}/compare/{base}...{tip}"
                        if status == "DRIFTED"
                        else None
                    ),
                    "skills": skills,
                    "error": info.get("error"),
                }
            )
    results.sort(key=lambda r: ({"DRIFTED": 0, "ERROR": 1, "UP_TO_DATE": 2}[r["status"]], r["repo"]))
    return results


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check upstream repositories in upstream-sources.json for new commits without cloning."
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--skill", action="append", default=[], help="Filter to one or more local skill names")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    results = check_sources(args.manifest, set(args.skill))
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return 0

    if not results:
        print("No matching upstream sources found.", file=sys.stderr)
        return 1

    for row in results:
        skills_str = ", ".join(row["skills"])
        if row["status"] == "UP_TO_DATE":
            print(f"[UP_TO_DATE] {row['repo']} @ {row['base'][:7]} ({skills_str})")
        elif row["status"] == "DRIFTED":
            meta = f" ({row['tip_date']}: {row['tip_subject']})" if row["tip_subject"] else ""
            print(f"[DRIFTED]    {row['repo']}: {row['base'][:7]} -> {row['tip'][:7]}{meta}")
            print(f"             skills:  {skills_str}")
            print(f"             compare: {row['compare_url']}")
        else:
            print(f"[ERROR]      {row['repo']}: {row['error']} ({skills_str})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
