#!/usr/bin/env python3
"""file-singlify scanner.

Directory-first duplicate detection + file deduplication + canonical
reference mapping. Finds redundant duplicate files and duplicate directory
copies left behind by repeated copying, backups, sync, and migration, then
proposes a single-copy ("singlify") plan: keep one canonical copy, map every
duplicate to it.

SAFETY: This script is strictly READ-ONLY. It never deletes, moves,
overwrites, hardlinks, or symlinks anything. `--action-mode` only changes the
*suggested_action* label printed in the report. Executing any destructive
action is out of scope and must be done by a human after reviewing the plan.
"""

from __future__ import annotations

import argparse
import csv
import fnmatch
import hashlib
import io
import json
import os
import sys
from collections import defaultdict

CHUNK = 1024 * 1024  # 1 MiB chunked reads; never load whole file into memory.

# Directory name fragments that make a location a WORSE canonical candidate.
DEMOTE_FRAGMENTS = (
    "backup", "backups", "bak", "copy", "copies", "old", "archive",
    "tmp", "temp", "cache", ".trash", "trash", "recycle", "duplicate",
    "__pycache__", "node_modules",
)

ACTION_FOR_MODE = {
    "report-only": "manual_review",
    "link-plan": "create_manifest_reference",
    "delete-plan": "delete_duplicate",
    "hardlink-plan": "replace_with_hardlink",
    "symlink-plan": "replace_with_symlink",
}


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        prog="scan_file_singlify.py",
        description="Read-only directory-first duplicate scanner and singlify planner.",
    )
    p.add_argument("root_path", help="Disk, directory, or mount path to scan.")
    p.add_argument("--scan-mode", choices=["directory-first", "file-only"],
                   default="directory-first")
    p.add_argument("--hash-algorithm", choices=["md5", "sha256", "both"],
                   default="md5")
    p.add_argument("--dry-run", choices=["true", "false"], default="true",
                   help="Always effectively true; this tool never mutates files.")
    p.add_argument("--include-patterns", default="",
                   help="Comma-separated globs to include, e.g. '*.jpg,*.mp4'.")
    p.add_argument("--exclude-patterns", default="",
                   help="Comma-separated path/name globs to exclude, e.g. 'node_modules,.git,cache'.")
    p.add_argument("--min-file-size", type=int, default=0,
                   help="Skip files smaller than this many bytes.")
    p.add_argument("--output-format", choices=["markdown", "json", "csv"],
                   default="markdown")
    p.add_argument("--action-mode",
                   choices=list(ACTION_FOR_MODE.keys()), default="report-only",
                   help="Only relabels suggested_action; no action is executed.")
    p.add_argument("--dir-match-threshold", type=float, default=0.90,
                   help="Min overall match rate to list two dirs as suspected duplicates.")
    p.add_argument("--prefer", default="",
                   help="Substring; paths containing it are preferred as canonical.")
    p.add_argument("--max-pairwise", type=int, default=2000,
                   help="Cap on pairwise directory comparisons per coarse bucket.")
    p.add_argument("--target-os", choices=["auto", "macos", "linux", "windows"],
                   default="auto",
                   help="OS to generate recommended commands for (auto-detected by default).")
    p.add_argument("--target-shell",
                   choices=["auto", "bash", "zsh", "fish", "powershell", "cmd"],
                   default="auto",
                   help="Shell syntax for recommended commands (auto-detected by default).")
    return p.parse_args(argv)


def detect_env(target_os, target_shell):
    """Resolve (os_name, shell_name) from flags or the runtime environment."""
    import platform
    if target_os == "auto":
        sysname = platform.system()
        os_name = {"Darwin": "macos", "Windows": "windows"}.get(sysname, "linux")
    else:
        os_name = target_os
    if target_shell == "auto":
        if os_name == "windows":
            # PSModulePath is set in PowerShell sessions; fall back to cmd otherwise.
            shell_name = "powershell" if os.environ.get("PSModulePath") else "cmd"
        else:
            base = os.path.basename(os.environ.get("SHELL", "/bin/bash"))
            shell_name = base if base in ("bash", "zsh", "fish") else "bash"
    else:
        shell_name = target_shell
    return os_name, shell_name


# --------------------------------------------------------------------------- #
# Filesystem walk with symlink-loop protection and error capture.
# --------------------------------------------------------------------------- #
def matches_any(name, path, patterns):
    for pat in patterns:
        if fnmatch.fnmatch(name, pat) or fnmatch.fnmatch(path, pat) or pat in path.split(os.sep):
            return True
    return False


def walk(root, include, exclude, min_size, errors, skipped, flags):
    """Yield file records. Records dirs visited. Protects against symlink loops."""
    files = []
    seen_dirs = set()  # (dev, ino) to stop directory cycles via symlinks
    dir_count = 0

    def on_error(e):  # os.walk passes an OSError; keep it JSON-serializable
        errors.append({"path": getattr(e, "filename", "") or "", "error": str(e)})

    for cur, subdirs, names in os.walk(root, topdown=True, followlinks=False, onerror=on_error):
        # exclude directories in place so os.walk does not descend into them
        kept = []
        for d in subdirs:
            dpath = os.path.join(cur, d)
            if exclude and matches_any(d, dpath, exclude):
                skipped.append({"path": dpath, "reason": "excluded-dir"})
                continue
            try:
                st = os.lstat(dpath)
            except OSError as e:
                errors.append({"path": dpath, "error": str(e)})
                continue
            if os.path.islink(dpath):
                skipped.append({"path": dpath, "reason": "symlink-dir-not-followed"})
                continue
            key = (st.st_dev, st.st_ino)
            if key in seen_dirs:
                errors.append({"path": dpath, "error": "directory cycle detected, recursion stopped"})
                continue
            seen_dirs.add(key)
            kept.append(d)
        subdirs[:] = kept
        dir_count += 1

        for n in names:
            fpath = os.path.join(cur, n)
            if exclude and matches_any(n, fpath, exclude):
                skipped.append({"path": fpath, "reason": "excluded-file"})
                continue
            if include and not matches_any(n, fpath, include):
                continue
            try:
                st = os.lstat(fpath)
            except OSError as e:
                errors.append({"path": fpath, "error": str(e)})
                continue
            if os.path.islink(fpath):
                skipped.append({"path": fpath, "reason": "symlink-file"})
                flags[fpath] = "symlink"
                continue
            if not os.path.isfile(fpath):
                skipped.append({"path": fpath, "reason": "special-file"})
                continue
            size = st.st_size
            if size == 0:
                skipped.append({"path": fpath, "reason": "zero-byte"})
                flags[fpath] = "zero-byte"
                continue
            if size < min_size:
                skipped.append({"path": fpath, "reason": "below-min-size"})
                continue
            if getattr(st, "st_nlink", 1) > 1:
                flags[fpath] = "already-hardlinked"
            files.append({
                "path": fpath,
                "size": size,
                "mtime": st.st_mtime,
                "ext": os.path.splitext(n)[1].lower(),
                "name": n,
            })
    return files, dir_count


# --------------------------------------------------------------------------- #
# Hashing (chunked).
# --------------------------------------------------------------------------- #
def hash_file(path, algo, errors, cache=None):
    """Return hash hex string(s). algo in md5|sha256|both. None on failure."""
    if cache is not None and path in cache:
        return cache[path]
    result = _hash_file_uncached(path, algo, errors)
    if cache is not None:
        cache[path] = result
    return result


def _hash_file_uncached(path, algo, errors):
    hs = {}
    if algo in ("md5", "both"):
        hs["md5"] = hashlib.md5()
    if algo in ("sha256", "both"):
        hs["sha256"] = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for block in iter(lambda: f.read(CHUNK), b""):
                for h in hs.values():
                    h.update(block)
    except OSError as e:
        errors.append({"path": path, "error": f"hash failed: {e}"})
        return None
    return "|".join(f"{k}:{v.hexdigest()}" for k, v in hs.items())


# --------------------------------------------------------------------------- #
# Directory signatures and match rate.
# --------------------------------------------------------------------------- #
def build_dir_signatures(files, root):
    """Map directory -> recursive signature of descendant files.

    Signature = sorted tuples of (relpath, size). Captures 'whole directory
    copied'. Each file contributes to every ancestor directory up to root.
    """
    dir_files = defaultdict(list)  # dir -> list of (relpath_from_dir, size, ext, name)
    root = os.path.abspath(root)
    for rec in files:
        path = os.path.abspath(rec["path"])
        d = os.path.dirname(path)
        # attribute file to each ancestor dir within root
        while True:
            rel = os.path.relpath(path, d)
            dir_files[d].append((rel, rec["size"], rec["ext"], rec["name"]))
            if os.path.normpath(d) == os.path.normpath(root) or len(d) <= len(root):
                break
            parent = os.path.dirname(d)
            if parent == d:
                break
            d = parent
    sigs = {}
    for d, items in dir_files.items():
        items_sorted = sorted(items)
        struct = tuple((rel, size) for rel, size, _e, _n in items_sorted)
        key = hashlib.md5(repr(struct).encode("utf-8", "replace")).hexdigest()
        sigs[d] = {
            "struct_key": key,
            "items": items_sorted,
            "count": len(items_sorted),
            "total_size": sum(s for _r, s, _e, _n in items_sorted),
            "rels": set(rel for rel, _s, _e, _n in items_sorted),
            "exts": [e for _r, _s, e, _n in items_sorted],
            "sizes": sorted(s for _r, s, _e, _n in items_sorted),
        }
    return sigs


def match_rate(a, b):
    """Component + overall directory match rate between two dir signatures."""
    def jacc(x, y):
        x, y = set(x), set(y)
        if not x and not y:
            return 1.0
        return len(x & y) / len(x | y) if (x | y) else 1.0

    path_name = jacc(a["rels"], b["rels"])
    ext = jacc(a["exts"], b["exts"])
    # size match: overlap of multisets
    sa, sb = defaultdict(int), defaultdict(int)
    for s in a["sizes"]:
        sa[s] += 1
    for s in b["sizes"]:
        sb[s] += 1
    inter = sum(min(sa[k], sb[k]) for k in set(sa) | set(sb))
    union = sum(max(sa[k], sb[k]) for k in set(sa) | set(sb))
    size = inter / union if union else 1.0
    count = (min(a["count"], b["count"]) / max(a["count"], b["count"])
             if max(a["count"], b["count"]) else 1.0)
    overall = round((path_name + ext + size + count) / 4, 4)
    return {
        "path_name": round(path_name, 4),
        "extension": round(ext, 4),
        "size": round(size, 4),
        "count": round(count, 4),
        "overall": overall,
    }


def _dir_content_signature(d, sig, algo, errors, hash_cache):
    """Hash every file under dir d. Return (content_key, hashed_ok).

    content_key is None when any contained file could not be hashed, so the
    directory cannot be content-confirmed against any peer.
    """
    pairs = []
    for rel, _size, _ext, _name in sig["items"]:
        h = hash_file(os.path.join(d, rel), algo, errors, cache=hash_cache)
        if h is None:
            return None, False
        pairs.append((rel, h))
    content_key = hashlib.md5(repr(tuple(sorted(pairs))).encode("utf-8", "replace")).hexdigest()
    return content_key, True


def group_directories(sigs, threshold, max_pairwise, algo, errors, hash_cache):
    """Return (exact_groups, suspected_pairs).

    A directory group is only emitted as an exact duplicate after EVERY
    contained file is hash-confirmed identical across the member dirs. Dirs
    that match on structure (relpath+size) but differ in content, or that
    could not be fully hashed, are downgraded to suspected pairs.
    """
    by_struct = defaultdict(list)
    for d, s in sigs.items():
        if s["count"] == 0:
            continue
        by_struct[s["struct_key"]].append(d)

    exact_groups = []
    for ds in by_struct.values():
        if len(ds) < 2:
            continue
        by_content = defaultdict(list)
        for d in sorted(ds):
            ckey, ok = _dir_content_signature(d, sigs[d], algo, errors, hash_cache)
            if ok:
                by_content[ckey].append(d)
        for members in by_content.values():
            if len(members) > 1:
                exact_groups.append(sorted(members))

    # suspected near-duplicates: bucket by file count coarse key.
    # Structure-matched-but-content-unconfirmed dirs are NOT in exact_dirs, so
    # they re-enter here as candidates (>= threshold) rather than being dropped.
    suspected = []
    bucket = defaultdict(list)
    exact_dirs = {d for g in exact_groups for d in g}
    for d, s in sigs.items():
        if s["count"] == 0 or d in exact_dirs:
            continue
        bucket[(s["count"],)].append(d)
    for ds in bucket.values():
        if len(ds) < 2:
            continue
        ds = sorted(ds)
        compared = 0
        for i in range(len(ds)):
            for j in range(i + 1, len(ds)):
                if compared >= max_pairwise:
                    break
                compared += 1
                mr = match_rate(sigs[ds[i]], sigs[ds[j]])
                if mr["overall"] >= threshold:
                    suspected.append({"a": ds[i], "b": ds[j], "match": mr})
    return exact_groups, suspected


# --------------------------------------------------------------------------- #
# File-level duplicate grouping (size prefilter -> hash confirm).
# --------------------------------------------------------------------------- #
def group_files(files, algo, errors, hash_cache=None):
    by_size = defaultdict(list)
    for rec in files:
        by_size[rec["size"]].append(rec)

    confirmed = []  # list of {size, hash, members:[path,...]}
    name_size_conflict = []
    by_name = defaultdict(set)
    for rec in files:
        by_name[rec["name"]].add(rec["size"])
    for name, sizes in by_name.items():
        if len(sizes) > 1:
            name_size_conflict.append({"name": name, "sizes": sorted(sizes)})

    for size, recs in by_size.items():
        if len(recs) < 2:
            continue
        by_hash = defaultdict(list)
        for rec in recs:
            h = hash_file(rec["path"], algo, errors, cache=hash_cache)
            if h is None:
                continue
            by_hash[h].append(rec["path"])
        for h, members in by_hash.items():
            if len(members) > 1:
                confirmed.append({"size": size, "hash": h, "members": sorted(members)})
    return confirmed, name_size_conflict


# --------------------------------------------------------------------------- #
# Canonical selection.
# --------------------------------------------------------------------------- #
def canonical_score(path, prefer):
    """Lower is better."""
    lower = path.lower()
    score = 0
    if prefer and prefer.lower() in lower:
        score -= 1_000_000  # strongly prefer user-specified location
    score += path.count(os.sep) * 100  # shallower preferred
    score += len(path)  # shorter preferred
    for frag in DEMOTE_FRAGMENTS:
        if frag in lower:
            score += 500_000
    return score


def pick_canonical(paths, prefer):
    ranked = sorted(paths, key=lambda p: (canonical_score(p, prefer), p))
    ambiguous = len(ranked) > 1 and canonical_score(ranked[0], prefer) == canonical_score(ranked[1], prefer)
    return ranked[0], ambiguous


def build_mapping(file_groups, action_mode, prefer, flags):
    rows = []
    for g in file_groups:
        canonical, ambiguous = pick_canonical(g["members"], prefer)
        action = ACTION_FOR_MODE[action_mode]
        confidence = "confirmed"
        for dup in g["members"]:
            if dup == canonical:
                continue
            note = flags.get(dup, "")
            row_action = action
            if ambiguous or note:
                row_action = "manual_review"
            rows.append({
                "duplicate_path": dup,
                "canonical_path": canonical,
                "duplicate_size": g["size"],
                "hash": g["hash"],
                "confidence": "uncertain" if (ambiguous or note) else confidence,
                "flag": note,
                "suggested_action": row_action,
            })
    return rows


# --------------------------------------------------------------------------- #
# Recommended follow-up commands (generated, NEVER executed).
# --------------------------------------------------------------------------- #
def _quote(path, shell):
    if shell == "powershell":
        return '"' + path.replace('"', '`"') + '"'
    if shell == "cmd":
        return '"' + path + '"'
    return '"' + path.replace('\\', '\\\\').replace('"', '\\"') + '"'  # posix


def recommended_commands(mapping, os_name, shell_name, action_mode):
    """Top-4 scenario-ranked command suggestions, safest first. Generated only.

    Returns a list of dicts; callers MUST present these as suggestions and let a
    human review/run them. This function never executes anything.
    """
    if not mapping:
        return [{
            "rank": 1, "archetype": "none", "risk": "none",
            "label": "No confirmed duplicates to act on",
            "command": "",
            "note": "Nothing to reclaim. Re-run with --hash-algorithm both for "
                    "stricter confirmation, or widen --scan-mode / scope.",
        }]
    rep_row = next((r for r in mapping if r.get("confidence") == "confirmed"), mapping[0])
    dup = _quote(rep_row["duplicate_path"], shell_name)
    can = _quote(rep_row["canonical_path"], shell_name)
    qdir = _quote("./singlify_quarantine", shell_name)

    if shell_name in ("powershell",):
        verify = f"Get-FileHash {can},{dup} -Algorithm SHA256"
        quarantine = f"New-Item -ItemType Directory -Force {qdir}; Move-Item {dup} {qdir}"
        hardlink = f"Remove-Item {dup}; New-Item -ItemType HardLink -Path {dup} -Target {can}"
        symlink_alt = "symlink alt: New-Item -ItemType SymbolicLink (needs admin / Developer Mode)"
        delete = f"Remove-Item -Confirm {dup}"
    elif shell_name == "cmd":
        verify = f"certutil -hashfile {can} SHA256 & certutil -hashfile {dup} SHA256"
        quarantine = f"mkdir singlify_quarantine & move {dup} singlify_quarantine\\"
        hardlink = f"del {dup} & mklink /H {dup} {can}"
        symlink_alt = "symlink alt: mklink (without /H)"
        delete = f"del /p {dup}"
    else:  # posix: bash / zsh / fish
        hashtool = "shasum -a 256" if os_name == "macos" else "sha256sum"
        verify = f"{hashtool} {can} {dup}"
        quarantine = f"mkdir -p {qdir} && mv -i {dup} {qdir}/"
        hardlink = f"rm {dup} && ln {can} {dup}"
        symlink_alt = f"symlink alt (cross-volume ok): rm {dup} && ln -s {can} {dup}"
        delete = f"rm -i {dup}"

    cmds = [
        {"rank": 1, "archetype": "verify", "risk": "safe",
         "label": "Verify the pair is byte-identical before trusting the plan",
         "command": verify, "note": "Non-destructive. Confirms the hash match first."},
        {"rank": 2, "archetype": "quarantine", "risk": "reversible",
         "label": "Move duplicate aside (keep / fine-tune, undo by moving back)",
         "command": quarantine,
         "note": "Reclaims space without deleting. Best when unsure or for sensitive dirs."},
        {"rank": 3, "archetype": "hardlink", "risk": "destructive",
         "label": "Replace duplicate with a hardlink to the canonical copy (same volume)",
         "command": hardlink,
         "note": "Reclaims space; both paths keep working. " + symlink_alt},
        {"rank": 4, "archetype": "delete", "risk": "irreversible",
         "label": "Delete the duplicate (irreversible space reclaim)",
         "command": delete,
         "note": "Only after verifying. Prefer quarantine if any doubt."},
    ]
    chosen = ACTION_FOR_MODE.get(action_mode, "")
    for c in cmds:
        c["matches_action_mode"] = (
            (c["archetype"] == "delete" and chosen == "delete_duplicate")
            or (c["archetype"] == "hardlink" and chosen == "replace_with_hardlink")
        )
    return cmds


# --------------------------------------------------------------------------- #
# Reporting.
# --------------------------------------------------------------------------- #
def human(n):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}PB"


def assemble_report(args, files, dir_count, exact_groups, suspected,
                    file_groups, mapping, name_conflicts, errors, skipped, sigs,
                    os_name, shell_name):
    total_size = sum(r["size"] for r in files)
    saving = sum(r["duplicate_size"] for r in mapping
                 if r["suggested_action"] != "manual_review")
    return {
        "scan_scope": os.path.abspath(args.root_path),
        "parameters": {
            "scan_mode": args.scan_mode,
            "hash_algorithm": args.hash_algorithm,
            "dry_run": True,
            "include_patterns": args.include_patterns,
            "exclude_patterns": args.exclude_patterns,
            "min_file_size": args.min_file_size,
            "action_mode": args.action_mode,
            "dir_match_threshold": args.dir_match_threshold,
            "prefer": args.prefer,
            "target_os": os_name,
            "target_shell": shell_name,
        },
        "totals": {
            "files": len(files),
            "directories": dir_count,
            "total_size_bytes": total_size,
            "total_size_human": human(total_size),
        },
        "duplicate_directory_groups": [
            {"struct_key": sigs[g[0]]["struct_key"],
             "count": sigs[g[0]]["count"],
             "size_each_human": human(sigs[g[0]]["total_size"]),
             "directories": g}
            for g in exact_groups
        ],
        "suspected_directory_pairs": suspected,
        "duplicate_file_groups": [
            {"size": g["size"], "size_human": human(g["size"]),
             "hash": g["hash"], "copies": len(g["members"]), "members": g["members"]}
            for g in file_groups
        ],
        "space_saving_estimate_bytes": saving,
        "space_saving_estimate_human": human(saving),
        "canonical_mapping": mapping,
        "recommended_commands": recommended_commands(
            mapping, os_name, shell_name, args.action_mode),
        "name_size_conflicts": name_conflicts,
        "errors": errors,
        "skipped": skipped,
    }


def render_markdown(rep):
    out = io.StringIO()
    w = out.write
    w("# file-singlify report\n\n")
    w("> Read-only dry-run. No files were deleted, moved, or linked. "
      "`suggested_action` is a proposal that requires explicit human confirmation.\n\n")
    w("## 1. Scan scope\n\n")
    w(f"- Root: `{rep['scan_scope']}`\n\n")
    w("## 2. Parameters\n\n")
    for k, v in rep["parameters"].items():
        w(f"- {k}: `{v}`\n")
    t = rep["totals"]
    w("\n## 3. Totals\n\n")
    w(f"- Files: {t['files']}\n- Directories: {t['directories']}\n"
      f"- Total size: {t['total_size_human']} ({t['total_size_bytes']} bytes)\n")
    w("\n## 4. Duplicate directory groups (hash-confirmed)\n\n")
    if not rep["duplicate_directory_groups"]:
        w("_None._\n")
    for i, g in enumerate(rep["duplicate_directory_groups"], 1):
        w(f"- Group D{i}: {g['count']} files each, {g['size_each_human']} per copy\n")
        for d in g["directories"]:
            w(f"  - `{d}`\n")
    w("\n## 5. Suspected duplicate directories (high match rate)\n\n")
    if not rep["suspected_directory_pairs"]:
        w("_None above threshold._\n")
    for s in rep["suspected_directory_pairs"]:
        m = s["match"]
        w(f"- overall {m['overall']:.0%} (path {m['path_name']:.0%}, ext {m['extension']:.0%}, "
          f"size {m['size']:.0%}, count {m['count']:.0%})\n  - `{s['a']}`\n  - `{s['b']}`\n")
    w("\n## 6. Duplicate file groups (hash-confirmed)\n\n")
    if not rep["duplicate_file_groups"]:
        w("_None._\n")
    for i, g in enumerate(rep["duplicate_file_groups"], 1):
        w(f"- Group F{i}: {g['copies']} copies, {g['size_human']} each, `{g['hash']}`\n")
        for m in g["members"]:
            w(f"  - `{m}`\n")
    w(f"\n## 7. Space saving estimate\n\n- ~{rep['space_saving_estimate_human']} "
      f"({rep['space_saving_estimate_bytes']} bytes) reclaimable if every duplicate "
      "collapses to its canonical copy.\n")
    w("\n## 8. Canonical mapping (duplicate -> canonical)\n\n")
    if not rep["canonical_mapping"]:
        w("_None._\n")
    else:
        w("| duplicate | canonical | size | confidence | flag | suggested_action |\n")
        w("|---|---|---|---|---|---|\n")
        for r in rep["canonical_mapping"]:
            w(f"| `{r['duplicate_path']}` | `{r['canonical_path']}` | {human(r['duplicate_size'])} "
              f"| {r['confidence']} | {r['flag'] or '-'} | {r['suggested_action']} |\n")
    w("\n## 9. Risk and uncertainty notes\n\n")
    if rep["name_size_conflicts"]:
        w(f"- {len(rep['name_size_conflicts'])} filename(s) appear with differing sizes "
          "(same name, different content). Not treated as duplicates.\n")
    w(f"- {len(rep['skipped'])} path(s) skipped (symlinks, zero-byte, special, excluded, below-min-size).\n")
    w(f"- {len(rep['errors'])} path(s) had read/permission/cycle errors.\n")
    w("- Suspected directory pairs are candidates only; confirm with file hashes before acting.\n")
    p = rep["parameters"]
    w(f"\n## 10. Recommended next-step commands (top 4, for {p['target_os']} / "
      f"{p['target_shell']})\n\n")
    w("> **DO NOT auto-run these.** They are generated suggestions, ordered "
      "safest-first, using one representative pair from the mapping. Review, "
      "then apply per row only after a human confirms.\n\n")
    for c in rep["recommended_commands"]:
        w(f"{c['rank']}. **{c['label']}** _(risk: {c['risk']}"
          f"{', matches --action-mode' if c.get('matches_action_mode') else ''})_\n")
        if c["command"]:
            w(f"   ```\n   {c['command']}\n   ```\n")
        w(f"   {c['note']}\n")
    w("\n- Re-run with `--hash-algorithm both` for strict confirmation before any deletion.\n")
    w("- This tool never performs delete/hardlink/symlink; execution is a separate human step.\n")
    return out.getvalue()


def render_csv(rep):
    out = io.StringIO()
    fields = ["duplicate_path", "canonical_path", "duplicate_size", "hash",
              "confidence", "flag", "suggested_action"]
    wtr = csv.DictWriter(out, fieldnames=fields)
    wtr.writeheader()
    for r in rep["canonical_mapping"]:
        wtr.writerow(r)
    return out.getvalue()


# --------------------------------------------------------------------------- #
def main(argv=None):
    args = parse_args(argv)
    root = args.root_path
    if not os.path.exists(root):
        print(json.dumps({"error": f"root_path does not exist: {root}"}), file=sys.stderr)
        return 2
    if not os.path.isdir(root):
        print(json.dumps({"error": f"root_path is not a directory: {root}"}), file=sys.stderr)
        return 2
    if not os.access(root, os.R_OK):
        print(json.dumps({"error": f"root_path is not readable: {root}"}), file=sys.stderr)
        return 2

    include = [s.strip() for s in args.include_patterns.split(",") if s.strip()]
    exclude = [s.strip() for s in args.exclude_patterns.split(",") if s.strip()]

    errors, skipped, flags = [], [], {}
    hash_cache = {}  # shared so dir confirmation and file grouping never re-hash
    files, dir_count = walk(root, include, exclude, args.min_file_size, errors, skipped, flags)

    if args.scan_mode == "directory-first":
        sigs = build_dir_signatures(files, root)
        exact_groups, suspected = group_directories(
            sigs, args.dir_match_threshold, args.max_pairwise,
            args.hash_algorithm, errors, hash_cache)
    else:
        sigs, exact_groups, suspected = {}, [], []

    file_groups, name_conflicts = group_files(files, args.hash_algorithm, errors, hash_cache)
    mapping = build_mapping(file_groups, args.action_mode, args.prefer, flags)

    os_name, shell_name = detect_env(args.target_os, args.target_shell)
    rep = assemble_report(args, files, dir_count, exact_groups, suspected,
                          file_groups, mapping, name_conflicts, errors, skipped, sigs,
                          os_name, shell_name)

    if args.output_format == "json":
        print(json.dumps(rep, indent=2, ensure_ascii=False))
    elif args.output_format == "csv":
        print(render_csv(rep))
    else:
        print(render_markdown(rep))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
