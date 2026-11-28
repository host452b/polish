#!/usr/bin/env python3
"""Zero-dependency CLI helper for model-council: backend probe, blind parallel CLI dispatch, and anti-majority-vote epistemic ledger."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parent.parent

ALLOWED_TRACKS = {"judgment", "comparison", "niche_relay"}
ALLOWED_TIERS = {
    "tier_1_multi_cli_or_api",
    "tier_2_host_subagents",
    "tier_3_single_model_counterfactual",
}
ALLOWED_SPECIFICITY = {"exact_anchor", "mechanism", "generic"}
ALLOWED_EVIDENCE_STATUS = {
    "tool_verified",
    "source_cited",
    "unverified_assertion",
    "falsified",
}

ENV_PROVIDER_KEYS: tuple[tuple[str, str], ...] = (
    ("ANTHROPIC_API_KEY", "anthropic"),
    ("OPENAI_API_KEY", "openai"),
    ("GEMINI_API_KEY", "google"),
    ("GOOGLE_API_KEY", "google"),
    ("DEEPSEEK_API_KEY", "deepseek"),
    ("OPENROUTER_API_KEY", "multi_family_router"),
)

CLI_BACKENDS: dict[str, dict[str, Any]] = {
    "devin": {
        "multi_family": True,
        "description": "Devin CLI non-interactive in-process print mode (read-only auto permissions)",
        "build_argv": lambda bin_path, model, prompt: [
            bin_path,
            "-p",
            "--process-model",
            "in-process",
            "--permission-mode",
            "auto",
            "--respect-workspace-trust",
            "false",
            "--model",
            model,
            "--",
            prompt,
        ],
    },
    "codex": {
        "multi_family": False,
        "default_family": "openai",
        "description": "Codex CLI ephemeral non-interactive read-only sandbox exec",
        "build_argv": lambda bin_path, model, prompt: [
            bin_path,
            "exec",
            "--ephemeral",
            "--skip-git-repo-check",
            "--color",
            "never",
            "-s",
            "read-only",
            "-m",
            model,
            prompt,
        ],
    },
    "claude": {
        "multi_family": False,
        "default_family": "anthropic",
        "description": "Claude Code non-interactive plan/read-only print mode",
        "build_argv": lambda bin_path, model, prompt: [
            bin_path,
            "-p",
            "--permission-mode",
            "plan",
            "--model",
            model,
            prompt,
        ],
    },
    "gemini": {
        "multi_family": False,
        "default_family": "google",
        "description": "Gemini CLI non-interactive prompt mode",
        "build_argv": lambda bin_path, model, prompt: [
            bin_path,
            "-m",
            model,
            "-p",
            prompt,
        ],
    },
    "opencode": {
        "multi_family": True,
        "description": "OpenCode CLI non-interactive multi-provider runner",
        "build_argv": lambda bin_path, model, prompt: [
            bin_path,
            "run",
            "-m",
            model,
            prompt,
        ],
    },
    "llm": {
        "multi_family": True,
        "description": "Simon Willison llm CLI multi-provider runner",
        "build_argv": lambda bin_path, model, prompt: [
            bin_path,
            "-m",
            model,
            prompt,
        ],
    },
    "ollama": {
        "multi_family": True,
        "description": "Ollama local open-weight model runner",
        "build_argv": lambda bin_path, model, prompt: [
            bin_path,
            "run",
            model,
            prompt,
        ],
    },
}

FAMILY_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\b(?:claude|opus|sonnet|haiku|fable|anthropic)\d*\b", "anthropic"),
    (r"\b(?:gpt|o1|o3|o4|codex|sol|terra|luna|astra|openai)\d*\b", "openai"),
    (r"\b(?:gemini|gemma|carbon|neon|argon|hydrogen|google)\d*\b", "google"),
    (r"\b(?:swe|cognition)\d*\b", "cognition"),
    (r"\b(?:deepseek)\d*\b", "deepseek"),
    (r"\b(?:kimi|moonshot)\d*\b", "moonshot"),
    (r"\b(?:glm|zhipu|chatglm)\d*\b", "zhipu"),
    (r"\b(?:qwen|tongyi)\d*\b", "alibaba"),
    (r"\b(?:nemotron|nvidia)\d*\b", "nvidia"),
    (r"\b(?:llama|meta)\d*\b", "meta"),
    (r"\b(?:mistral|mixtral|codestral)\d*\b", "mistral"),
    (r"\b(?:grok|xai)\d*\b", "xai"),
)

LEADING_BIAS_PATTERNS: tuple[tuple[str, str], ...] = (
    (
        r"\b(?:i think|we think|my preferred|preferred solution|obviously we should|clearly the best|lean toward|leaning toward)\b",
        "Fact Pack contains opinion/leaning language that risks anchoring blind seats",
    ),
    (
        r"(?:我倾向于|优先推荐方案|显然应该|最佳答案是|我认为应该选)",
        "Fact Pack contains Chinese opinion/anchoring phrasing; strip Chair hypothesis before Round 1",
    ),
)

SECRET_REDACT_RE = re.compile(
    r"(?:sk-[A-Za-z0-9_-]{16,}|AIza[0-9A-Za-z_-]{20,}|Bearer\s+[A-Za-z0-9._~+/=-]{16,}|gh[pousr]_[A-Za-z0-9_]{20,})"
)

SAFE_MODEL_ID_RE = re.compile(r"^[A-Za-z0-9._:/@-]{1,128}$")


FUSION_MODEL_RE = re.compile(r"^fusion-(.+?)-sidekick-(.+)$", re.IGNORECASE)


def redact_secrets(text: str) -> str:
    return SECRET_REDACT_RE.sub("[REDACTED_SECRET]", text)


def _infer_single_model_family(model_id: str, cli_key: str = "") -> str:
    normalized = model_id.strip().lower().replace("_", "-")
    if "/" in normalized:
        prefix = normalized.split("/", 1)[0]
        for pat, fam in FAMILY_PATTERNS:
            if re.search(pat, prefix):
                return fam
    tokens = re.sub(r"[^a-z0-9]+", " ", normalized)
    for pat, fam in FAMILY_PATTERNS:
        if re.search(pat, tokens):
            return fam
    if cli_key in CLI_BACKENDS and CLI_BACKENDS[cli_key].get("default_family"):
        return str(CLI_BACKENDS[cli_key]["default_family"])
    return "unknown"


def parse_fusion_pairing(model_id: str) -> dict[str, str] | None:
    m = FUSION_MODEL_RE.match(model_id.strip())
    if not m:
        return None
    lead_model, sidekick_model = m.group(1), m.group(2)
    return {
        "lead_model": lead_model,
        "sidekick_model": sidekick_model,
        "lead_family": _infer_single_model_family(lead_model),
        "sidekick_family": _infer_single_model_family(sidekick_model),
    }


def infer_model_family(model_id: str, cli_key: str = "") -> str:
    fusion = parse_fusion_pairing(model_id)
    if fusion is not None:
        return fusion["lead_family"]
    return _infer_single_model_family(model_id, cli_key)


def discover_devin_models(devin_bin: str) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            [devin_bin, "models"],
            shell=False,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except Exception as exc:
        return {"ok": False, "error": redact_secrets(str(exc))}

    if proc.returncode != 0:
        return {"ok": False, "error": redact_secrets((proc.stderr or proc.stdout or "").strip()[:300])}

    by_family: dict[str, list[str]] = {}
    fusion_by_lead_family: dict[str, list[str]] = {}
    for line in (proc.stdout or "").splitlines():
        m = re.match(r"^\s{2}([a-z0-9][a-z0-9._-]*)\s{2,}", line)
        if not m:
            continue
        mid = m.group(1)
        if mid == "aliases:":
            continue
        fusion = parse_fusion_pairing(mid)
        if fusion is not None:
            fusion_by_lead_family.setdefault(fusion["lead_family"], []).append(mid)
        else:
            fam = _infer_single_model_family(mid)
            by_family.setdefault(fam, []).append(mid)

    return {
        "ok": True,
        "families_available": {fam: ids[:5] for fam, ids in sorted(by_family.items())},
        "fusion_lead_families_available": {fam: ids[:3] for fam, ids in sorted(fusion_by_lead_family.items())},
    }


def probe_environment(
    which_fn=shutil.which,
    environ: dict[str, str] | None = None,
    discover_models: bool = False,
) -> dict[str, Any]:
    env_map = os.environ if environ is None else environ
    detected_clis: list[dict[str, Any]] = []
    families_reachable: set[str] = set()
    has_multi_family_cli = False
    devin_bin: str | None = None

    for cli_name, spec in CLI_BACKENDS.items():
        resolved = which_fn(cli_name)
        if not resolved:
            continue
        if cli_name == "devin":
            devin_bin = resolved
        multi = bool(spec.get("multi_family", False))
        if multi:
            has_multi_family_cli = True
        elif spec.get("default_family"):
            families_reachable.add(str(spec["default_family"]))
        detected_clis.append(
            {
                "cli": cli_name,
                "binary_found": True,
                "multi_family_capable": multi,
                "default_family": spec.get("default_family", "multi"),
                "description": spec["description"],
            }
        )

    present_env_providers: list[dict[str, Any]] = []
    for var_name, fam in ENV_PROVIDER_KEYS:
        if env_map.get(var_name):
            present_env_providers.append({"env_var": var_name, "present": True, "family": fam})
            if fam == "multi_family_router":
                has_multi_family_cli = True
            else:
                families_reachable.add(fam)

    if has_multi_family_cli or len(families_reachable) >= 2:
        recommended_tier = "tier_1_multi_cli_or_api"
    elif detected_clis or present_env_providers:
        recommended_tier = "tier_2_host_subagents"
    else:
        recommended_tier = "tier_3_single_model_counterfactual"

    out: dict[str, Any] = {
        "skill_root": str(SKILL_ROOT.name),
        "detected_clis": detected_clis,
        "present_env_providers": present_env_providers,
        "multi_family_router_available": has_multi_family_cli,
        "distinct_vendor_families_detected": sorted(families_reachable),
        "recommended_tier": recommended_tier,
    }
    if discover_models and devin_bin:
        out["devin_catalog"] = discover_devin_models(devin_bin)
    return out


def lint_fact_pack_neutrality(items: list[str], question: str = "") -> list[str]:
    warnings: list[str] = []
    corpus = "\n".join(items)
    for pat, msg in LEADING_BIAS_PATTERNS:
        if re.search(pat, corpus, flags=re.IGNORECASE):
            warnings.append(msg)
    if question and re.search(r"\b(?:isn't it true that|don't you agree)\b", question, flags=re.IGNORECASE):
        warnings.append("Question uses leading confirmation phrasing ('isn't it true that / don't you agree')")
    return warnings


def build_blind_seat_prompt(brief: dict[str, Any], seat: dict[str, Any]) -> str:
    question = str(brief["question"]).strip()
    track = str(brief.get("track", "judgment")).strip()
    fact_pack = [str(x).strip() for x in brief.get("fact_pack", []) if str(x).strip()]
    constraints = [str(x).strip() for x in brief.get("constraints", []) if str(x).strip()]
    lens = str(seat.get("lens", "general first-principles analysis")).strip()
    seat_id = str(seat["seat_id"]).strip()

    fact_lines = "\n".join(f"- {item}" for item in fact_pack) if fact_pack else "- (None supplied)"
    constraint_lines = "\n".join(f"- {c}" for c in constraints) if constraints else "- (None supplied)"

    niche_clause = ""
    if track == "niche_relay":
        niche_clause = (
            "\n[NICHE KNOWLEDGE-RELAY RULE]\n"
            "This question touches a long-tail or obscure domain. Report exact anchors you genuinely recall "
            "(register/bitmask, RFC clause, API symbol, kernel/compiler quirk) and explicitly mark uncertain "
            "seams as UNKNOWN rather than interpolating plausible boilerplate.\n"
        )

    return (
        f"[ROLE]\n"
        f"You are Seat {seat_id} in a blind multi-model council (Track: {track}). "
        f"Reason independently from first principles and the neutral Fact Pack below.\n\n"
        f"[QUESTION]\n{question}\n\n"
        f"[NEUTRAL FACT PACK]\n{fact_lines}\n\n"
        f"[HARD CONSTRAINTS]\n{constraint_lines}\n\n"
        f"[INSPECTION LENS]\n{lens}\n"
        f"{niche_clause}\n"
        f"[REQUIRED OUTPUT SLOTS]\n"
        f"1. VERDICT & CAUSAL MECHANISM: Direct answer and concrete causal chain.\n"
        f"2. EXACT ANCHORS: Specific specs, APIs, equations, registers, or file:line invariants.\n"
        f"3. UNCERTAINTY & MISSING SEAMS (LOW_CONFIDENCE / UNKNOWN): Sub-questions you cannot verify with high confidence.\n"
        f"4. STEELMAN COUNTER-CASE & FLIP CONDITION: Strongest peer objection and the single check that would flip your bet.\n"
    )


def validate_brief(brief: dict[str, Any]) -> None:
    if not isinstance(brief, dict):
        raise ValueError("CouncilBrief root must be a JSON object")
    question = str(brief.get("question", "")).strip()
    if not question:
        raise ValueError("CouncilBrief requires a non-empty 'question'")
    track = str(brief.get("track", "judgment")).strip()
    if track not in ALLOWED_TRACKS:
        raise ValueError(f"Invalid 'track' '{track}'; expected one of {sorted(ALLOWED_TRACKS)}")
    seats = brief.get("seats")
    if not isinstance(seats, list) or not (2 <= len(seats) <= 8):
        raise ValueError("CouncilBrief 'seats' must be a list of 2 to 8 seat objects")
    seen_ids: set[str] = set()
    for seat in seats:
        if not isinstance(seat, dict):
            raise ValueError("Each seat must be a JSON object")
        sid = str(seat.get("seat_id", "")).strip()
        cli_key = str(seat.get("cli", "")).strip()
        model = str(seat.get("model", "")).strip()
        if not sid or sid in seen_ids:
            raise ValueError(f"Duplicate or empty seat_id '{sid}'")
        seen_ids.add(sid)
        if cli_key not in CLI_BACKENDS:
            raise ValueError(f"Disallowed cli '{cli_key}'; allowed: {sorted(CLI_BACKENDS)}")
        if not model or not SAFE_MODEL_ID_RE.match(model):
            raise ValueError(f"Invalid or unsafe model identifier '{model}' on seat '{sid}'")


def _run_single_seat(
    seat: dict[str, Any],
    prompt: str,
    timeout_sec: int,
    which_fn=shutil.which,
) -> dict[str, Any]:
    sid = str(seat["seat_id"]).strip()
    cli_key = str(seat["cli"]).strip()
    model = str(seat["model"]).strip()
    family = seat.get("family") or infer_model_family(model, cli_key)
    bin_path = which_fn(cli_key)
    if not bin_path:
        return {
            "seat_id": sid,
            "cli": cli_key,
            "model": model,
            "family": family,
            "status": "missing_cli",
            "elapsed_ms": 0,
            "exit_code": None,
            "answer": "",
            "error": f"CLI '{cli_key}' not found on PATH",
        }

    argv = CLI_BACKENDS[cli_key]["build_argv"](bin_path, model, prompt)
    t0 = time.monotonic()
    with tempfile.TemporaryDirectory(prefix=f"council_{sid}_") as scratch_dir:
        try:
            proc = subprocess.run(
                argv,
                shell=False,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
                cwd=scratch_dir,
            )
            elapsed_ms = int((time.monotonic() - t0) * 1000)
            stdout_clean = redact_secrets(proc.stdout or "").strip()
            stderr_clean = redact_secrets(proc.stderr or "").strip()
            status = "ok" if proc.returncode == 0 and stdout_clean else "error"
            return {
                "seat_id": sid,
                "cli": cli_key,
                "model": model,
                "family": family,
                "status": status,
                "elapsed_ms": elapsed_ms,
                "exit_code": proc.returncode,
                "answer": stdout_clean,
                "error": stderr_clean[:600] if status != "ok" else "",
            }
        except subprocess.TimeoutExpired:
            elapsed_ms = int((time.monotonic() - t0) * 1000)
            return {
                "seat_id": sid,
                "cli": cli_key,
                "model": model,
                "family": family,
                "status": "timeout",
                "elapsed_ms": elapsed_ms,
                "exit_code": None,
                "answer": "",
                "error": f"Timed out after {timeout_sec}s",
            }


def dispatch_council(
    brief: dict[str, Any],
    dry_run: bool = False,
    max_workers: int = 4,
    which_fn=shutil.which,
) -> dict[str, Any]:
    validate_brief(brief)
    track = str(brief.get("track", "judgment")).strip()
    timeout_sec = max(5, min(int(brief.get("timeout_sec", 90)), 600))
    fact_pack = [str(x) for x in brief.get("fact_pack", [])]
    neutrality_warnings = lint_fact_pack_neutrality(fact_pack, str(brief.get("question", "")))

    seats = brief["seats"]
    seat_plans: list[dict[str, Any]] = []
    families: list[str] = []
    prompts_by_seat: dict[str, str] = {}

    for seat in seats:
        sid = str(seat["seat_id"]).strip()
        cli_key = str(seat["cli"]).strip()
        model = str(seat["model"]).strip()
        fam = str(seat.get("family") or infer_model_family(model, cli_key))
        fusion_info = parse_fusion_pairing(model)
        families.append(fam)
        prompt = build_blind_seat_prompt(brief, seat)
        prompts_by_seat[sid] = prompt
        bin_path = which_fn(cli_key) or f"<missing:{cli_key}>"
        preview_argv = CLI_BACKENDS[cli_key]["build_argv"](bin_path, model, "<BLIND_ROUND1_PROMPT>")
        plan_entry: dict[str, Any] = {
            "seat_id": sid,
            "cli": cli_key,
            "binary_available": bool(which_fn(cli_key)),
            "model": model,
            "family": fam,
            "lens": seat.get("lens", "general first-principles analysis"),
            "prompt_chars": len(prompt),
            "prompt_sha256_12": hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:12],
            "argv_preview": preview_argv,
        }
        if fusion_info is not None:
            plan_entry["fusion_pairing"] = fusion_info
        seat_plans.append(plan_entry)

    unique_fams = sorted({f for f in families if f != "unknown"})
    diversity_ratio = round(len(set(families)) / len(seats), 3)

    if dry_run:
        return {
            "mode": "dry_run",
            "track": track,
            "seat_count": len(seats),
            "unique_families": unique_fams,
            "family_diversity_ratio": diversity_ratio,
            "homogeneous_family_warning": len(set(families)) < 2,
            "fact_pack_neutrality_warnings": neutrality_warnings,
            "blind_round1_verified": True,
            "seat_plans": seat_plans,
        }

    results_by_id: dict[str, dict[str, Any]] = {}
    workers = max(1, min(max_workers, len(seats)))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        fut_map = {
            pool.submit(_run_single_seat, seat, prompts_by_seat[str(seat["seat_id"]).strip()], timeout_sec, which_fn): str(
                seat["seat_id"]
            ).strip()
            for seat in seats
        }
        for fut in as_completed(fut_map):
            sid = fut_map[fut]
            results_by_id[sid] = fut.result()

    ordered_results = [results_by_id[str(s["seat_id"]).strip()] for s in seats]
    ok_count = sum(1 for r in ordered_results if r["status"] == "ok")
    return {
        "mode": "live",
        "track": track,
        "seat_count": len(seats),
        "ok_seat_count": ok_count,
        "failed_seat_count": len(seats) - ok_count,
        "unique_families": unique_fams,
        "family_diversity_ratio": diversity_ratio,
        "fact_pack_neutrality_warnings": neutrality_warnings,
        "blind_round1_verified": True,
        "results": ordered_results,
    }


def evaluate_ledger(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("Ledger input must be a JSON object")

    tier = str(payload.get("execution_tier", "tier_1_multi_cli_or_api")).strip()
    if tier not in ALLOWED_TIERS:
        raise ValueError(f"Invalid 'execution_tier' '{tier}'; expected one of {sorted(ALLOWED_TIERS)}")

    seats = payload.get("seats")
    if not isinstance(seats, list) or not (1 <= len(seats) <= 8):
        raise ValueError("Ledger 'seats' must be a list of 1 to 8 seat records")

    relay_rounds_used = int(payload.get("relay_rounds_used", 0))
    seat_family: dict[str, str] = {}
    active_seats: list[str] = []
    failed_seats: list[str] = []

    for s in seats:
        if not isinstance(s, dict) or not str(s.get("seat_id", "")).strip():
            raise ValueError("Every seat in ledger must have a non-empty 'seat_id'")
        sid = str(s["seat_id"]).strip()
        model = str(s.get("model", "unknown")).strip()
        cli_key = str(s.get("cli", "")).strip()
        fam = str(s.get("family") or infer_model_family(model, cli_key))
        seat_family[sid] = fam
        if str(s.get("status", "ok")).strip() == "ok":
            active_seats.append(sid)
        else:
            failed_seats.append(sid)

    active_families = sorted({seat_family[sid] for sid in active_seats})
    is_multi_family_active = len(active_families) >= 2 and tier != "tier_3_single_model_counterfactual"

    raw_claims = payload.get("claims", [])
    if not isinstance(raw_claims, list):
        raise ValueError("Ledger 'claims' must be a list")

    classified_claims: list[dict[str, Any]] = []
    buckets: dict[str, list[str]] = {
        "CONVERGENT_HIGH_TRUST": [],
        "SINGLE_FAMILY_CONVERGENCE": [],
        "HOMOGENEOUS_ECHO_WARNING": [],
        "DISPUTED_FAULT_LINE": [],
        "FAULT_LINE_RESOLVED_BY_EVIDENCE": [],
        "VERIFIED_MINORITY_GOLD": [],
        "UNIQUE_1_OF_N_RELAY_CANDIDATE": [],
        "LOW_SIGNAL_GENERIC_SINGLETON": [],
        "FALSIFIED_DROPPED": [],
    }

    for item in raw_claims:
        if not isinstance(item, dict):
            raise ValueError("Each claim must be a JSON object")
        cid = str(item.get("claim_id", "")).strip()
        statement = str(item.get("statement", "")).strip()
        if not cid or not statement:
            raise ValueError("Every claim requires non-empty 'claim_id' and 'statement'")

        supporters = [str(x).strip() for x in item.get("supporters", []) if str(x).strip()]
        challengers = [str(x).strip() for x in item.get("challengers", []) if str(x).strip()]
        unknown_refs = [x for x in supporters + challengers if x not in seat_family]
        if unknown_refs:
            raise ValueError(f"Claim '{cid}' references unknown seat_id(s): {unknown_refs}")

        specificity = str(item.get("specificity", "mechanism")).strip()
        if specificity not in ALLOWED_SPECIFICITY:
            raise ValueError(f"Claim '{cid}' has invalid specificity '{specificity}'")

        evidence_status = str(item.get("evidence_status", "unverified_assertion")).strip()
        if evidence_status not in ALLOWED_EVIDENCE_STATUS:
            raise ValueError(f"Claim '{cid}' has invalid evidence_status '{evidence_status}'")

        supporter_fams = sorted({seat_family[s] for s in supporters})
        protect_from_majority_vote = False
        requires_relay_or_probe = False

        if evidence_status == "falsified":
            bucket = "FALSIFIED_DROPPED"
        elif supporters and challengers:
            if evidence_status in {"tool_verified", "source_cited"}:
                bucket = "FAULT_LINE_RESOLVED_BY_EVIDENCE"
            else:
                bucket = "DISPUTED_FAULT_LINE"
                requires_relay_or_probe = True
        elif len(supporters) >= 2:
            if not is_multi_family_active:
                bucket = "SINGLE_FAMILY_CONVERGENCE"
            elif len(supporter_fams) >= 2:
                bucket = "CONVERGENT_HIGH_TRUST"
            else:
                bucket = "HOMOGENEOUS_ECHO_WARNING"
        elif len(supporters) == 1:
            if evidence_status in {"tool_verified", "source_cited"}:
                bucket = "VERIFIED_MINORITY_GOLD"
                protect_from_majority_vote = True
            elif specificity in {"exact_anchor", "mechanism"}:
                bucket = "UNIQUE_1_OF_N_RELAY_CANDIDATE"
                protect_from_majority_vote = True
                requires_relay_or_probe = True
            else:
                bucket = "LOW_SIGNAL_GENERIC_SINGLETON"
        else:
            bucket = "LOW_SIGNAL_GENERIC_SINGLETON"

        buckets[bucket].append(cid)
        classified_claims.append(
            {
                "claim_id": cid,
                "statement": statement,
                "bucket": bucket,
                "supporters": supporters,
                "supporter_families": supporter_fams,
                "challengers": challengers,
                "specificity": specificity,
                "evidence_status": evidence_status,
                "protect_from_majority_vote": protect_from_majority_vote,
                "requires_relay_or_probe": requires_relay_or_probe,
                "note": str(item.get("relay_seam") or item.get("fault_line_reason") or "").strip(),
            }
        )

    invariants = {
        "tier_honesty": not (
            (not is_multi_family_active) and len(buckets["CONVERGENT_HIGH_TRUST"]) > 0
        ),
        "minority_anchor_protected": all(
            c["protect_from_majority_vote"] or c["bucket"] == "FALSIFIED_DROPPED"
            for c in classified_claims
            if len(c["supporters"]) == 1 and len(c["challengers"]) == 0 and c["specificity"] in {"exact_anchor", "mechanism"}
        ),
        "relay_stop_loss_respected": 0 <= relay_rounds_used <= 1,
        "seat_cap_respected": 1 <= len(seats) <= 8,
    }

    return {
        "execution_tier": tier,
        "active_seats": active_seats,
        "failed_seats": failed_seats,
        "active_families": active_families,
        "family_diversity_ratio": round(len(active_families) / max(1, len(active_seats)), 3),
        "multi_family_consensus_eligible": is_multi_family_active,
        "relay_rounds_used": relay_rounds_used,
        "bucket_counts": {k: len(v) for k, v in buckets.items() if v},
        "claims": classified_claims,
        "invariants": invariants,
        "invariants_all_passed": all(invariants.values()),
    }


def format_ledger_markdown(report: dict[str, Any]) -> str:
    lines = [
        "## Council Epistemic Ledger",
        "",
        f"- **Execution Tier:** `{report['execution_tier']}` (multi-family consensus eligible: `{report['multi_family_consensus_eligible']}`)",
        f"- **Active Seats ({len(report['active_seats'])}):** `{', '.join(report['active_seats']) or 'none'}` | **Failed Seats:** `{', '.join(report['failed_seats']) or 'none'}`",
        f"- **Active Model Families:** `{', '.join(report['active_families']) or 'none'}` (diversity ratio: `{report['family_diversity_ratio']}`)",
        f"- **Relay Rounds Used:** `{report['relay_rounds_used']}` | **Invariants All Passed:** `{report['invariants_all_passed']}`",
        "",
        "| Claim | Bucket | Supporters (Families) | Challengers | Evidence | Majority-Vote Shield / Action |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for c in report["claims"]:
        sup = f"{','.join(c['supporters'])} ({','.join(c['supporter_families'])})" if c["supporters"] else "-"
        chal = ",".join(c["challengers"]) if c["challengers"] else "-"
        action_parts: list[str] = []
        if c["protect_from_majority_vote"]:
            action_parts.append("PROTECT_1_OF_N")
        if c["requires_relay_or_probe"]:
            action_parts.append("PROBE_OR_RELAY")
        if c["note"]:
            action_parts.append(c["note"].replace("|", "/"))
        action_str = "; ".join(action_parts) if action_parts else "-"
        stmt = c["statement"].replace("|", "/")
        lines.append(
            f"| `{c['claim_id']}` {stmt} | `{c['bucket']}` | {sup} | {chal} | `{c['evidence_status']}` | {action_str} |"
        )
    return "\n".join(lines)


def _read_json_input(source: str) -> dict[str, Any]:
    if source == "-":
        raw = sys.stdin.read()
    else:
        raw = Path(source).read_text(encoding="utf-8")
    return json.loads(raw)


def run_selftest() -> int:
    assert infer_model_family("claude-opus-5.5") == "anthropic"
    assert infer_model_family("gpt-6.1-sol") == "openai"
    assert infer_model_family("gpt-6.1-terra") == "openai"
    assert infer_model_family("gemini-4-carbon") == "google"
    assert infer_model_family("gemini-4-neon-high") == "google"
    assert infer_model_family("nemotron-3.5-super") == "nvidia"
    assert infer_model_family("swe-2") == "cognition"
    assert infer_model_family("deepseek/deepseek-r1") == "deepseek"
    assert infer_model_family("fusion-gemini-4-neon-high-sidekick-claude-haiku-5-5-medium") == "google"
    assert infer_model_family("fusion-gpt-6-2-astra-high-sidekick-claude-sonnet-5-5-medium") == "openai"

    redacted = redact_secrets("token Bearer abcdefghijklmnop123456 and sk-1234567890abcdefghijkl")
    assert "[REDACTED_SECRET]" in redacted and "sk-1234567890" not in redacted

    dry = dispatch_council(
        {
            "question": "Compare WAL vs rollback journal under NFSv4 locking quirks",
            "track": "niche_relay",
            "fact_pack": ["SQLite 3.46 on Linux 6.8", "I think WAL is obviously we should pick"],
            "seats": [
                {"seat_id": "s_opus", "cli": "devin", "model": "opus"},
                {"seat_id": "s_gpt", "cli": "codex", "model": "gpt-5"},
                {"seat_id": "s_gem", "cli": "devin", "model": "gemini"},
            ],
        },
        dry_run=True,
        which_fn=lambda name: f"/usr/local/bin/{name}",
    )
    assert dry["family_diversity_ratio"] == 1.0
    assert len(dry["fact_pack_neutrality_warnings"]) == 1

    ledger_out = evaluate_ledger(
        {
            "execution_tier": "tier_1_multi_cli_or_api",
            "relay_rounds_used": 1,
            "seats": [
                {"seat_id": "s1", "model": "opus-5.5", "status": "ok"},
                {"seat_id": "s2", "model": "sonnet-4.6", "status": "ok"},
                {"seat_id": "s3", "model": "gpt-6.1-sol", "status": "ok"},
            ],
            "claims": [
                {
                    "claim_id": "C_CROSS",
                    "statement": "Cross-family agreement",
                    "supporters": ["s1", "s3"],
                    "challengers": [],
                    "specificity": "mechanism",
                    "evidence_status": "unverified_assertion",
                },
                {
                    "claim_id": "C_ECHO",
                    "statement": "Anthropic-only two-seat agreement",
                    "supporters": ["s1", "s2"],
                    "challengers": [],
                    "specificity": "mechanism",
                    "evidence_status": "unverified_assertion",
                },
                {
                    "claim_id": "C_NICHE",
                    "statement": "Exact RFC 8881 delegation recall quirk",
                    "supporters": ["s3"],
                    "challengers": [],
                    "specificity": "exact_anchor",
                    "evidence_status": "unverified_assertion",
                },
                {
                    "claim_id": "C_GOLD",
                    "statement": "Verified 1/N kernel check",
                    "supporters": ["s3"],
                    "challengers": [],
                    "specificity": "exact_anchor",
                    "evidence_status": "tool_verified",
                },
            ],
        }
    )
    by_id = {c["claim_id"]: c for c in ledger_out["claims"]}
    assert by_id["C_CROSS"]["bucket"] == "CONVERGENT_HIGH_TRUST"
    assert by_id["C_ECHO"]["bucket"] == "HOMOGENEOUS_ECHO_WARNING"
    assert by_id["C_NICHE"]["bucket"] == "UNIQUE_1_OF_N_RELAY_CANDIDATE"
    assert by_id["C_NICHE"]["protect_from_majority_vote"] is True
    assert by_id["C_GOLD"]["bucket"] == "VERIFIED_MINORITY_GOLD"
    assert ledger_out["invariants_all_passed"] is True

    tier3_out = evaluate_ledger(
        {
            "execution_tier": "tier_3_single_model_counterfactual",
            "relay_rounds_used": 0,
            "seats": [
                {"seat_id": "lens_a", "model": "opus", "status": "ok"},
                {"seat_id": "lens_b", "model": "opus", "status": "ok"},
            ],
            "claims": [
                {
                    "claim_id": "C1",
                    "statement": "Single-model agreement across lenses",
                    "supporters": ["lens_a", "lens_b"],
                    "challengers": [],
                    "specificity": "mechanism",
                    "evidence_status": "unverified_assertion",
                }
            ],
        }
    )
    assert tier3_out["claims"][0]["bucket"] == "SINGLE_FAMILY_CONVERGENCE"
    assert tier3_out["invariants_all_passed"] is True
    print("selftest passed: all invariants verified")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Deterministic probe, blind parallel CLI dispatcher, and epistemic ledger for model-council."
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_probe = sub.add_parser("probe", help="Inspect available local multi-model CLIs and provider env flags (secret-safe)")
    p_probe.add_argument(
        "--discover-models",
        action="store_true",
        help="Also query local `devin models` catalog by model family and Fusion Lead family",
    )

    p_disp = sub.add_parser("dispatch", help="Validate and run (or --dry-run) blind Round-1 council seats")
    p_disp.add_argument("--input", required=True, help="Path to CouncilBrief JSON or '-' for stdin")
    p_disp.add_argument("--output", help="Optional path to write output JSON")
    p_disp.add_argument("--dry-run", action="store_true", help="Preview seat diversity, neutrality lint, and argv without running")
    p_disp.add_argument("--max-workers", type=int, default=4, help="Max concurrent seat processes (default: 4)")

    p_led = sub.add_parser("ledger", help="Classify cross-seat claims and verify anti-majority-vote invariants")
    p_led.add_argument("--input", required=True, help="Path to CouncilLedgerInput JSON or '-' for stdin")
    p_led.add_argument("--format", choices=("json", "markdown"), default="json", help="Output format")

    sub.add_parser("selftest", help="Run built-in deterministic invariant suite")

    args = parser.parse_args(argv)

    if args.cmd == "probe":
        print(json.dumps(probe_environment(discover_models=args.discover_models), ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "dispatch":
        brief = _read_json_input(args.input)
        out = dispatch_council(brief, dry_run=args.dry_run, max_workers=args.max_workers)
        rendered = json.dumps(out, ensure_ascii=False, indent=2)
        if args.output:
            Path(args.output).write_text(rendered + "\n", encoding="utf-8")
        else:
            print(rendered)
        return 0
    if args.cmd == "ledger":
        payload = _read_json_input(args.input)
        report = evaluate_ledger(payload)
        if args.format == "markdown":
            print(format_ledger_markdown(report))
        else:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["invariants_all_passed"] else 1
    if args.cmd == "selftest":
        return run_selftest()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
