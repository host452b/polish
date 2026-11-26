#!/usr/bin/env python3
"""
Domain-agnostic longitudinal time-series synthesis, Sinkhorn conservation Sankey
& velocity SVG generator, rollover-safe Markdown slot synchronizer, and Typst
textbook compiler helper.

Python 3.10+ standard library only.
"""

from __future__ import annotations

import argparse
import csv
import html
import io
import json
import re
import statistics
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

DEFAULT_PALETTE = [
    "#1F4E79", "#B84A39", "#2E7D6B", "#6C4F8F", "#C98A2C",
    "#3B7EA1", "#4A5568", "#9E3B52", "#2F6B3C", "#5C6B73",
]

FONT_STACK = "'Hiragino Sans GB', 'PingFang SC', 'Noto Sans CJK SC', 'Helvetica Neue', Arial, sans-serif"


def esc(val: object) -> str:
    return html.escape(str(val), quote=True)


def parse_period(ts: str, grain: str = "quarter") -> tuple[str, str]:
    """Normalize an ISO-like timestamp/date string into (bucket_label, day_key)."""
    s = str(ts).strip()
    if not s:
        return ("unknown", "unknown")
    m = re.match(r"^(\d{4})(?:[-/](\d{1,2})(?:[-/](\d{1,2}))?)?", s)
    if not m:
        return (s, s)
    yr = int(m.group(1))
    mo = int(m.group(2) or 1)
    dy = int(m.group(3) or 1)
    day_key = f"{yr:04d}-{mo:02d}-{dy:02d}"
    if grain == "year":
        return (f"{yr:04d}", day_key)
    if grain == "month":
        return (f"{yr:04d}-{mo:02d}", day_key)
    if grain == "week":
        dt = datetime(yr, mo, dy)
        iso_y, iso_w, _ = dt.isocalendar()
        return (f"{iso_y:04d}-W{iso_w:02d}", day_key)
    q = (mo - 1) // 3 + 1
    return (f"{yr:04d}-Q{q}", day_key)


def sinkhorn_coupling(
    p_src: list[float],
    p_dst: list[float],
    affinity: list[list[float]],
    iters: int = 150,
    tol: float = 1e-10,
) -> list[list[float]]:
    """Solve mass-conserving flow matrix T[i][j] with row sums = p_src and col sums = p_dst."""
    n, m = len(p_src), len(p_dst)
    mat = [[max(1e-7, float(affinity[i][j])) for j in range(m)] for i in range(n)]
    for _ in range(iters):
        for i in range(n):
            rs = sum(mat[i])
            if p_src[i] <= 0:
                for j in range(m):
                    mat[i][j] = 0.0
            elif rs > 0:
                scale = p_src[i] / rs
                for j in range(m):
                    mat[i][j] *= scale
        for j in range(m):
            cs = sum(mat[i][j] for i in range(n))
            if p_dst[j] <= 0:
                for i in range(n):
                    mat[i][j] = 0.0
            elif cs > 0:
                scale = p_dst[j] / cs
                for i in range(n):
                    mat[i][j] *= scale
        max_row_err = max((abs(sum(mat[i]) - p_src[i]) for i in range(n)), default=0.0)
        if max_row_err < tol:
            break
    return mat


def _classify_record(
    rec: dict,
    compiled_cats: list[tuple[dict, re.Pattern | None]],
    compiled_subs: list[tuple[dict, re.Pattern | None]],
) -> tuple[str, list[str], list[str]]:
    title = str(rec.get("title", "") or "")
    text = str(rec.get("text", "") or rec.get("summary", "") or rec.get("abstract", "") or "")
    combined = f"{title} {text}"

    explicit_cat = rec.get("category")
    explicit_tags = list(rec.get("tags") or [])
    explicit_subs = list(rec.get("subsignals") or [])

    scores: dict[str, float] = {}
    for cmeta, rx in compiled_cats:
        cid = cmeta["id"]
        if explicit_cat == cid:
            scores[cid] = scores.get(cid, 0.0) + 10.0
        if cid in explicit_tags:
            scores[cid] = scores.get(cid, 0.0) + 4.0
        if rx is not None:
            scores[cid] = scores.get(cid, 0.0) + len(rx.findall(title)) * 3.0 + len(rx.findall(text)) * 1.0

    positive = [(cid, sc) for cid, sc in scores.items() if sc > 0]
    if not positive:
        fallback_id = compiled_cats[-1][0]["id"] if compiled_cats else (str(explicit_cat) if explicit_cat else "other")
        primary = fallback_id
        multi = [fallback_id]
    else:
        positive.sort(key=lambda kv: -kv[1])
        primary = positive[0][0]
        top_sc = positive[0][1]
        multi = [cid for cid, sc in positive if sc >= max(1.0, top_sc * 0.3)][:4]

    matched_subs = list(explicit_subs)
    for smeta, srx in compiled_subs:
        sid = smeta["id"]
        if sid not in matched_subs and srx is not None and srx.search(combined):
            matched_subs.append(sid)

    return primary, multi, matched_subs


def _classify_subsignal_lifecycle(series_pct: list[float]) -> str:
    if not series_pct or max(series_pct) == 0:
        return "dormant"
    peak = max(series_pct)
    peak_idx = series_pct.index(peak)
    last = series_pct[-1]
    n = len(series_pct)
    if peak_idx >= n - 2 and last >= peak * 0.85 and (series_pct[0] == 0 or last >= series_pct[0] * 1.8):
        return "igniting"
    if peak_idx == n - 1:
        return "peaking"
    if last >= peak * 0.72:
        return "high_plateau"
    if last >= peak * 0.35:
        return "maturing_infra"
    return "declining"


def analyze_corpus(payload: dict) -> dict:
    """
    Analyze a timestamped record collection into multi-resolution longitudinal
    shares, Sinkhorn conservation flow matrices, subsignal lifecycle heatmaps,
    and deduplicated landmarks.
    """
    records = payload.get("records", [])
    grain = payload.get("grain", "quarter")
    major_grain = payload.get("major_grain", "year")
    tax = payload.get("taxonomy", {})

    raw_cats = tax.get("categories") or []
    if not raw_cats:
        discovered = sorted({str(r.get("category", "general")) for r in records}) or ["general"]
        raw_cats = [
            {"id": cid, "label": cid, "color": DEFAULT_PALETTE[idx % len(DEFAULT_PALETTE)]}
            for idx, cid in enumerate(discovered)
        ]

    categories: dict[str, dict] = {}
    compiled_cats: list[tuple[dict, re.Pattern | None]] = []
    for idx, c in enumerate(raw_cats):
        c_copy = {
            "id": c["id"],
            "label": c.get("label", c["id"]),
            "color": c.get("color") or DEFAULT_PALETTE[idx % len(DEFAULT_PALETTE)],
            "pattern": c.get("pattern"),
        }
        categories[c_copy["id"]] = c_copy
        rx = re.compile(c_copy["pattern"], re.I) if c_copy["pattern"] else None
        compiled_cats.append((c_copy, rx))

    raw_subs = tax.get("subsignals") or []
    subsignals: dict[str, dict] = {}
    compiled_subs: list[tuple[dict, re.Pattern | None]] = []
    for s in raw_subs:
        s_copy = {
            "id": s["id"],
            "category": s.get("category", raw_cats[0]["id"]),
            "label": s.get("label", s["id"]),
            "pattern": s.get("pattern"),
        }
        subsignals[s_copy["id"]] = s_copy
        srx = re.compile(s_copy["pattern"], re.I) if s_copy["pattern"] else None
        compiled_subs.append((s_copy, srx))

    def _bucket_init() -> dict:
        return {
            "total": 0,
            "score_sum": 0.0,
            "artifact_count": 0,
            "days": set(),
            "primary": Counter(),
            "multi": Counter(),
            "subsignals": Counter(),
            "cooccurrence": defaultdict(Counter),
            "entities": Counter(),
            "records": [],
        }

    periods_raw: dict[str, dict] = defaultdict(_bucket_init)
    majors_raw: dict[str, dict] = defaultdict(_bucket_init)
    unique_by_id: dict[str, dict] = {}
    all_days: list[str] = []

    for idx, r in enumerate(records):
        rec_id = str(r.get("id") or f"rec-{idx + 1}")
        ts = str(r.get("timestamp") or r.get("date") or "")
        p_lbl, day_key = parse_period(ts, grain=grain)
        m_lbl, _ = parse_period(ts, grain=major_grain)
        if day_key != "unknown":
            all_days.append(day_key)

        primary, multi, subs = _classify_record(r, compiled_cats, compiled_subs)
        score = float(r.get("score", 0.0) or 0.0)
        has_art = 1 if r.get("has_artifact") else 0
        entity = str(r.get("entity") or "").strip()

        norm_rec = {
            "id": rec_id,
            "timestamp": ts,
            "day": day_key,
            "period": p_lbl,
            "major_period": m_lbl,
            "title": " ".join(str(r.get("title") or rec_id).split()),
            "score": score,
            "has_artifact": bool(has_art),
            "entity": entity,
            "primary_category": primary,
            "categories": multi,
            "subsignals": subs,
            "url": str(r.get("url") or ""),
        }

        for bucket in (periods_raw[p_lbl], majors_raw[m_lbl]):
            bucket["total"] += 1
            bucket["score_sum"] += score
            bucket["artifact_count"] += has_art
            bucket["days"].add(day_key)
            bucket["primary"][primary] += 1
            for c1 in multi:
                bucket["multi"][c1] += 1
                for c2 in multi:
                    bucket["cooccurrence"][c1][c2] += 1
            for sid in subs:
                bucket["subsignals"][sid] += 1
            if entity:
                bucket["entities"][entity] += 1
            bucket["records"].append(norm_rec)

        prev = unique_by_id.get(rec_id)
        if prev is None or score >= prev["score"]:
            unique_by_id[rec_id] = norm_rec

    sorted_periods = sorted(periods_raw.keys())
    sorted_majors = sorted(majors_raw.keys())

    # Detect partial boundary periods (<50% of median period volume/days when >=3 periods exist)
    partial_periods: list[str] = []
    if len(sorted_periods) >= 3:
        interior_counts = [periods_raw[p]["total"] for p in sorted_periods[1:-1]] or [
            periods_raw[p]["total"] for p in sorted_periods
        ]
        med_cnt = statistics.median(interior_counts)
        for boundary_p in (sorted_periods[0], sorted_periods[-1]):
            if periods_raw[boundary_p]["total"] < med_cnt * 0.5:
                partial_periods.append(boundary_p)

    def _serialize_buckets(raw_map: dict[str, dict], keys: list[str]) -> dict[str, dict]:
        out = {}
        for k in keys:
            b = raw_map[k]
            tot = max(1, b["total"])
            top_recs = sorted(b["records"], key=lambda x: x["score"], reverse=True)[:15]
            out[k] = {
                "total": b["total"],
                "active_days": len(b["days"]),
                "avg_score": round(b["score_sum"] / tot, 2),
                "artifact_rate": round(b["artifact_count"] / tot * 100.0, 2),
                "primary_counts": dict(b["primary"]),
                "primary_shares": {cid: round(b["primary"].get(cid, 0) / tot * 100.0, 4) for cid in categories},
                "multi_counts": dict(b["multi"]),
                "multi_rates": {cid: round(b["multi"].get(cid, 0) / tot * 100.0, 2) for cid in categories},
                "subsignal_rates": {sid: round(b["subsignals"].get(sid, 0) / tot * 100.0, 2) for sid in subsignals},
                "cooccurrence": {c1: dict(c2s) for c1, c2s in b["cooccurrence"].items()},
                "top_entities": b["entities"].most_common(12),
                "top_records": top_recs,
            }
        return out

    periods_clean = _serialize_buckets(periods_raw, sorted_periods)
    majors_clean = _serialize_buckets(majors_raw, sorted_majors)

    # Sinkhorn-coupled conservation transitions across major_grain
    cat_ids = list(categories.keys())
    transitions: list[dict] = []
    for idx in range(len(sorted_majors) - 1):
        m_src = sorted_majors[idx]
        m_dst = sorted_majors[idx + 1]
        b_src = majors_raw[m_src]
        b_dst = majors_raw[m_dst]
        raw_s = [b_src["primary"].get(c, 0) + 0.35 * b_src["multi"].get(c, 0) for c in cat_ids]
        raw_d = [b_dst["primary"].get(c, 0) + 0.35 * b_dst["multi"].get(c, 0) for c in cat_ids]
        sum_s = sum(raw_s) or 1.0
        sum_d = sum(raw_d) or 1.0
        p_s = [v / sum_s * 100.0 for v in raw_s]
        p_d = [v / sum_d * 100.0 for v in raw_d]

        cooc = b_dst["cooccurrence"]
        aff: list[list[float]] = []
        for i, ci in enumerate(cat_ids):
            diag = max(1, cooc.get(ci, {}).get(ci, 1))
            row = []
            for j, cj in enumerate(cat_ids):
                if i == j:
                    row.append(3.4)
                else:
                    cross = cooc.get(ci, {}).get(cj, 0) / diag
                    boost = max(0.05, (p_d[j] - p_s[i]) * 0.12 + 0.25)
                    row.append(max(0.02, cross * boost))
            aff.append(row)

        t_mat = sinkhorn_coupling(p_s, p_d, aff)
        transitions.append(
            {
                "from": m_src,
                "to": m_dst,
                "categories": cat_ids,
                "src_shares": {cat_ids[i]: p_s[i] for i in range(len(cat_ids))},
                "dst_shares": {cat_ids[j]: p_d[j] for j in range(len(cat_ids))},
                "matrix": t_mat,
            }
        )

    subsignal_lifecycle = {}
    for sid in subsignals:
        seq = [periods_clean[p]["subsignal_rates"].get(sid, 0.0) for p in sorted_periods]
        subsignal_lifecycle[sid] = {
            "trajectory": _classify_subsignal_lifecycle(seq),
            "peak_period": sorted_periods[seq.index(max(seq))] if seq else "",
            "peak_rate": max(seq, default=0.0),
            "latest_rate": seq[-1] if seq else 0.0,
        }

    unique_all = sorted(unique_by_id.values(), key=lambda x: x["score"], reverse=True)
    sorted_days_unique = sorted(set(all_days))
    recent_day_window = set(sorted_days_unique[-20:])
    recent_frontier = sorted(
        [u for u in unique_by_id.values() if u["day"] in recent_day_window],
        key=lambda x: x["score"],
        reverse=True,
    )[:15]

    return {
        "grain": grain,
        "major_grain": major_grain,
        "earliest_day": sorted_days_unique[0] if sorted_days_unique else "",
        "latest_day": sorted_days_unique[-1] if sorted_days_unique else "",
        "active_days": len(sorted_days_unique),
        "total_events": len(records),
        "unique_records": len(unique_all),
        "partial_periods": partial_periods,
        "categories": categories,
        "subsignals": subsignals,
        "subsignal_lifecycle": subsignal_lifecycle,
        "periods": periods_clean,
        "major_periods": majors_clean,
        "sankey_transitions": transitions,
        "top_landmarks": unique_all[:100],
        "recent_frontier": recent_frontier,
        "scissor_groups": payload.get("scissor_groups"),
    }


# -------------------- Orthogonal Vector SVG Suite --------------------

def _svg_card(w: int, h: int, tag: str, title: str, subtitle: str, footer: str, body: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">
  <defs>
    <linearGradient id="hdrGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#13294B"/>
      <stop offset="100%" stop-color="#1F4E79"/>
    </linearGradient>
  </defs>
  <rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="6" fill="#FAF8F4" stroke="#C8C1B4" stroke-width="1.2"/>
  <rect x="1" y="1" width="{w - 2}" height="60" rx="6" fill="url(#hdrGrad)"/>
  <rect x="1" y="52" width="{w - 2}" height="9" fill="url(#hdrGrad)"/>
  <text x="24" y="26" font-family="{FONT_STACK}" font-size="11" font-weight="700" fill="#E8C574" letter-spacing="1.1">{esc(tag)}</text>
  <text x="24" y="47" font-family="{FONT_STACK}" font-size="16" font-weight="700" fill="#FFFFFF">{esc(title)}</text>
  <text x="24" y="82" font-family="{FONT_STACK}" font-size="11.5" fill="#4A5568">{esc(subtitle)}</text>
  <line x1="24" y1="92" x2="{w - 24}" y2="92" stroke="#DED8CC" stroke-width="1"/>
  {body}
  <line x1="24" y1="{h - 32}" x2="{w - 24}" y2="{h - 32}" stroke="#DED8CC" stroke-width="1"/>
  <text x="24" y="{h - 13}" font-family="{FONT_STACK}" font-size="10.2" fill="#6B7280">{esc(footer)}</text>
</svg>
"""


def render_volume_velocity_svg(report: dict, title: str = "Longitudinal Volume, Score & Artifact Velocity") -> str:
    w, h = 1060, 535
    ps = list(report["periods"].keys())
    totals = [report["periods"][p]["total"] for p in ps]
    scores = [report["periods"][p]["avg_score"] for p in ps]
    rates = [report["periods"][p]["artifact_rate"] for p in ps]
    partials = set(report.get("partial_periods", []))

    x0, y0, pw, ph = 78, 142, 880, 312
    max_tot = max(1.0, max(totals, default=1) * 1.24)
    max_sc = max(1.0, max(scores, default=1.0) * 1.25)
    max_rt = 100.0

    parts = []
    for i in range(6):
        gy = y0 + ph - (i / 5) * ph
        gv = int(round((i / 5) * max_tot))
        parts.append(f'<line x1="{x0}" y1="{gy:.1f}" x2="{x0 + pw}" y2="{gy:.1f}" stroke="#E5E0D5" stroke-dasharray="3,3"/>')
        parts.append(f'<text x="{x0 - 10}" y="{gy + 4:.1f}" text-anchor="end" font-family="{FONT_STACK}" font-size="10.2" fill="#475569">{gv:,}</text>')
        rv = int(round((i / 5) * max_rt))
        sv = round((i / 5) * max_sc, 1)
        parts.append(f'<text x="{x0 + pw + 10}" y="{gy + 4:.1f}" text-anchor="start" font-family="{FONT_STACK}" font-size="9.8" fill="#B84A39">{rv}% / {sv}</text>')

    step = pw / max(1, len(ps))
    bar_w = step * 0.56
    sc_pts, rt_pts = [], []
    for idx, p in enumerate(ps):
        cx = x0 + (idx + 0.5) * step
        bh = (totals[idx] / max_tot) * ph
        by = y0 + ph - bh
        is_part = p in partials
        fill_op = "0.45" if is_part else "0.86"
        dash = ' stroke="#13294B" stroke-dasharray="3,2"' if is_part else ""
        parts.append(f'<rect x="{cx - bar_w / 2:.1f}" y="{by:.1f}" width="{bar_w:.1f}" height="{bh:.1f}" rx="3" fill="#1F4E79" fill-opacity="{fill_op}"{dash}/>')
        lbl_val = f"{totals[idx]:,}*" if is_part else f"{totals[idx]:,}"
        parts.append(f'<text x="{cx:.1f}" y="{by - 6:.1f}" text-anchor="middle" font-family="{FONT_STACK}" font-size="9.5" font-weight="700" stroke="#FAF8F4" stroke-width="3" stroke-linejoin="round" fill="#1E293B">{esc(lbl_val)}</text>')
        parts.append(f'<text x="{cx:.1f}" y="{by - 6:.1f}" text-anchor="middle" font-family="{FONT_STACK}" font-size="9.5" font-weight="700" fill="#1E293B">{esc(lbl_val)}</text>')
        parts.append(f'<text x="{cx:.1f}" y="{y0 + ph + 20:.1f}" text-anchor="middle" font-family="{FONT_STACK}" font-size="9.8" fill="#334155">{esc(p)}</text>')

        sc_pts.append((cx, y0 + ph - (scores[idx] / max_sc) * ph))
        rt_pts.append((cx, y0 + ph - (rates[idx] / max_rt) * ph))

    if len(rt_pts) >= 2:
        parts.append(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in rt_pts)}" fill="none" stroke="#2E7D6B" stroke-width="2.3" stroke-dasharray="5,3"/>')
        parts.append(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in sc_pts)}" fill="none" stroke="#B84A39" stroke-width="2.5"/>')
    for x, y in sc_pts:
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.4" fill="#B84A39" stroke="#FFFFFF" stroke-width="1"/>')

    lx, ly = x0 + 8, 114
    parts.append(f'<rect x="{lx}" y="{ly - 9}" width="13" height="10" rx="2" fill="#1F4E79"/><text x="{lx + 18}" y="{ly}" font-family="{FONT_STACK}" font-size="10.5" fill="#1E293B">Period Volume (left)</text>')
    parts.append(f'<line x1="{lx + 165}" y1="{ly - 4}" x2="{lx + 185}" y2="{ly - 4}" stroke="#B84A39" stroke-width="2.5"/><text x="{lx + 192}" y="{ly}" font-family="{FONT_STACK}" font-size="10.5" fill="#1E293B">Mean Intensity/Score (right)</text>')
    parts.append(f'<line x1="{lx + 380}" y1="{ly - 4}" x2="{lx + 400}" y2="{ly - 4}" stroke="#2E7D6B" stroke-width="2.3" stroke-dasharray="4,2"/><text x="{lx + 407}" y="{ly}" font-family="{FONT_STACK}" font-size="10.5" fill="#1E293B">Artifact/Link Rate % (right)</text>')

    note_part = f" (* partial boundary periods: {', '.join(partials)})" if partials else ""
    footer = f"Corpus: {report['total_events']:,} event-slices ({report['unique_records']:,} unique IDs), {report['earliest_day']} to {report['latest_day']}{note_part}."
    return _svg_card(w, h, "LONGITUDINAL VOLUME & INTENSITY", title, "Separates raw volume expansion from mean intensity and artifact completeness", footer, "\n  ".join(parts))


def render_conservation_sankey_svg(report: dict, title: str = "Multi-Period Attention Flow Sankey") -> str:
    """Render Sinkhorn-conserved multi-period Sankey with explicit band budget and outside-right gutter."""
    majors = list(report["major_periods"].keys())
    cats = report["categories"]
    cat_ids = list(cats.keys())
    transitions = report["sankey_transitions"]

    outside_right = len(majors) >= 3
    w = 1220 if outside_right else 1080
    h = 700
    x_left = 30.0
    x_right = (w - 235.0) if outside_right else (w - 34.0)
    y_top = 172.0
    y_bottom = h - 50.0
    node_w = 20.0
    node_gap = 11.0

    # Band 1 (y=106..128): Color legend strip (strictly above column headers at y=144..160!)
    parts: list[str] = []
    cols_per_row = 5
    for idx, cid in enumerate(cat_ids[:10]):
        lx = 30 + (idx % cols_per_row) * 225
        ly = 109 if idx < cols_per_row else 126
        parts.append(
            f'<rect x="{lx}" y="{ly - 8}" width="10" height="10" rx="2" fill="{cats[cid]["color"]}"/>'
            f'<text x="{lx + 14}" y="{ly}" font-family="{FONT_STACK}" font-size="10" fill="#334155">{esc(cats[cid]["label"])}</text>'
        )

    num_cols = max(1, len(majors))
    col_xs = [
        x_left + c * (x_right - x_left - node_w) / max(1, num_cols - 1)
        for c in range(num_cols)
    ]

    # Compute shares per column matching Sinkhorn endpoints
    col_shares: list[dict[str, float]] = []
    for c_idx, m_key in enumerate(majors):
        if transitions and c_idx < len(transitions):
            col_shares.append(transitions[c_idx]["src_shares"])
        elif transitions and c_idx == len(transitions):
            col_shares.append(transitions[-1]["dst_shares"])
        else:
            col_shares.append(report["major_periods"][m_key]["primary_shares"])

    node_geom: list[dict[str, dict]] = []
    avail_h = y_bottom - y_top
    for c_idx, m_key in enumerate(majors):
        shares = col_shares[c_idx]
        active = [(cid, shares.get(cid, 0.0)) for cid in cat_ids if shares.get(cid, 0.0) > 0]
        active.sort(key=lambda kv: -kv[1])
        tot_s = sum(v for _, v in active) or 1.0
        usable_h = avail_h - node_gap * max(0, len(active) - 1)
        cy = y_top
        gmap: dict[str, dict] = {}
        for cid, val in active:
            nh = max(6.0, (val / tot_s) * usable_h)
            gmap[cid] = {"x": col_xs[c_idx], "y": cy, "h": nh, "val": val, "out": 0.0, "in": 0.0}
            cy += nh + node_gap
        overflow = (cy - node_gap) - y_bottom
        if overflow > 0.5 and len(active) > 1:
            sc = avail_h / (avail_h + overflow)
            cy2 = y_top
            for cid, _ in active:
                gmap[cid]["y"] = cy2
                gmap[cid]["h"] *= sc
                cy2 += gmap[cid]["h"] + node_gap * sc
        node_geom.append(gmap)

        # Band 2 (y=146..162): Column headers
        mb = report["major_periods"][m_key]
        if c_idx == 0 or (c_idx == num_cols - 1 and outside_right):
            anch, tx = "start", col_xs[c_idx]
        elif c_idx == num_cols - 1:
            anch, tx = "end", col_xs[c_idx] + node_w
        else:
            anch, tx = "middle", col_xs[c_idx] + node_w / 2
        parts.append(f'<text x="{tx:.1f}" y="{y_top - 26:.1f}" text-anchor="{anch}" font-family="{FONT_STACK}" font-size="12.5" font-weight="700" fill="#13294B">{esc(m_key)}</text>')
        parts.append(f'<text x="{tx:.1f}" y="{y_top - 11:.1f}" text-anchor="{anch}" font-family="{FONT_STACK}" font-size="10" fill="#64748B">N = {mb["total"]:,}</text>')

    # Ribbons
    for c_idx, tr in enumerate(transitions):
        sg_map = node_geom[c_idx]
        dg_map = node_geom[c_idx + 1]
        t_cats = tr["categories"]
        mat = tr["matrix"]
        edges = []
        out_sum: Counter = Counter()
        in_sum: Counter = Counter()
        for i, ci in enumerate(t_cats):
            for j, cj in enumerate(t_cats):
                v = mat[i][j]
                if v > 0 and ci in sg_map and cj in dg_map:
                    edges.append((ci, cj, v))
                    out_sum[ci] += v
                    in_sum[cj] += v
        edges.sort(key=lambda e: (sg_map[e[0]]["y"], dg_map[e[1]]["y"]))
        for ci, cj, v in edges:
            sg, dg = sg_map[ci], dg_map[cj]
            sh = (v / max(1e-9, out_sum[ci])) * sg["h"]
            dh = (v / max(1e-9, in_sum[cj])) * dg["h"]
            y0, y1 = sg["y"] + sg["out"], dg["y"] + dg["in"]
            sg["out"] += sh
            dg["in"] += dh
            if v < 0.35:
                continue
            x0, x1 = sg["x"] + node_w, dg["x"]
            mx = (x0 + x1) * 0.5
            op = "0.44" if ci == cj else "0.24"
            d_path = (
                f"M {x0:.2f},{y0:.2f} C {mx:.2f},{y0:.2f} {mx:.2f},{y1:.2f} {x1:.2f},{y1:.2f} "
                f"L {x1:.2f},{(y1 + dh):.2f} C {mx:.2f},{(y1 + dh):.2f} {mx:.2f},{(y0 + sh):.2f} {x0:.2f},{(y0 + sh):.2f} Z"
            )
            parts.append(f'<path d="{d_path}" fill="{cats[ci]["color"]}" fill-opacity="{op}"/>')

    # Node bars & collision-free labels
    for c_idx, gmap in enumerate(node_geom):
        for cid, g in gmap.items():
            x, y, nh = g["x"], g["y"], g["h"]
            parts.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{node_w:.1f}" height="{nh:.2f}" rx="2.5" fill="{cats[cid]["color"]}" stroke="#FFFFFF" stroke-width="0.8"/>')
            ly = y + nh / 2 + 4.0
            if c_idx < num_cols - 1 or outside_right:
                lx, anch = x + node_w + 7.0, "start"
            else:
                lx, anch = x - 7.0, "end"

            # Middle columns show compact % only when >=4 columns to keep wide gaps crisp
            if num_cols >= 4 and 0 < c_idx < num_cols - 1:
                lbl = f"{g['val']:.1f}%"
            else:
                lbl = f"{cats[cid]['label']} {g['val']:.1f}%"
            parts.append(f'<text data-role="node-label" x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anch}" font-family="{FONT_STACK}" font-size="10.2" font-weight="600" stroke="#FAF8F4" stroke-width="3.2" stroke-linejoin="round" fill="#1E293B">{esc(lbl)}</text>')
            parts.append(f'<text data-role="node-label" x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anch}" font-family="{FONT_STACK}" font-size="10.2" font-weight="600" fill="#1E293B">{esc(lbl)}</text>')

    footer = f"Mass-conserving Sinkhorn coupling over co-occurrence affinity (N = {report['total_events']:,} event-slices; columns rank-sorted)."
    return _svg_card(w, h, "CONSERVATION SANKEY FLOW", title, "Tracks rank inversions, backbone persistence, and cross-category flow redirection across epochs", footer, "\n  ".join(parts))


def render_share_stream_svg(report: dict, title: str = "100% Normalized Category Share Streamgraph") -> str:
    w, h = 1080, 540
    ps = list(report["periods"].keys())
    cats = report["categories"]
    cat_ids = list(cats.keys())
    x0, y0, pw, ph = 66, 134, 760, 336

    n_p = max(1, len(ps))
    xs = [x0 + i * (pw / max(1, n_p - 1)) for i in range(n_p)]
    q_shares = [[report["periods"][p]["primary_shares"].get(c, 0.0) for c in cat_ids] for p in ps]

    parts = []
    if n_p >= 2:
        cum_prev = [0.0] * n_p
        for c_idx, cid in enumerate(cat_ids):
            cum_next = [cum_prev[i] + q_shares[i][c_idx] for i in range(n_p)]
            top_pts = [f"{xs[i]:.1f},{y0 + ph - (cum_next[i] / 100.0) * ph:.1f}" for i in range(n_p)]
            bot_pts = [f"{xs[i]:.1f},{y0 + ph - (cum_prev[i] / 100.0) * ph:.1f}" for i in reversed(range(n_p))]
            parts.append(f'<polygon points="{" ".join(top_pts + bot_pts)}" fill="{cats[cid]["color"]}" fill-opacity="0.85" stroke="#FAF8F4" stroke-width="0.7"/>')
            cum_prev = cum_next

    for pct in (0, 25, 50, 75, 100):
        gy = y0 + ph - (pct / 100.0) * ph
        parts.append(f'<line x1="{x0}" y1="{gy:.1f}" x2="{x0 + pw}" y2="{gy:.1f}" stroke="#FFFFFF" stroke-opacity="0.45" stroke-dasharray="3,3"/>')
        parts.append(f'<text x="{x0 - 8}" y="{gy + 4:.1f}" text-anchor="end" font-family="{FONT_STACK}" font-size="10.2" fill="#475569">{pct}%</text>')

    stride = max(1, n_p // 12)
    for i in range(0, n_p, stride):
        parts.append(f'<text x="{xs[i]:.1f}" y="{y0 + ph + 18:.1f}" text-anchor="middle" font-family="{FONT_STACK}" font-size="9.5" fill="#334155">{esc(ps[i])}</text>')

    lx = x0 + pw + 22
    for idx, cid in enumerate(reversed(cat_ids[:10])):
        orig_i = cat_ids.index(cid)
        ly = y0 + 14 + idx * 33
        s0 = q_shares[0][orig_i] if q_shares else 0.0
        s1 = q_shares[-1][orig_i] if q_shares else 0.0
        delta = s1 - s0
        dcol = "#166534" if delta >= 1.0 else ("#991B1B" if delta <= -1.0 else "#475569")
        parts.append(f'<rect x="{lx}" y="{ly - 9}" width="12" height="12" rx="2" fill="{cats[cid]["color"]}"/>')
        parts.append(f'<text x="{lx + 18}" y="{ly + 1}" font-family="{FONT_STACK}" font-size="10.2" font-weight="600" fill="#1E293B">{esc(cats[cid]["label"])}</text>')
        parts.append(f'<text x="{lx + 18}" y="{ly + 14}" font-family="{FONT_STACK}" font-size="9.3" fill="{dcol}">{s0:.1f}% → {s1:.1f}% ({delta:+.1f}pp)</text>')

    footer = f"100% normalized primary-category composition from {ps[0] if ps else ''} to {ps[-1] if ps else ''}."
    return _svg_card(w, h, "STRUCTURAL SHARE STREAMGRAPH", title, "Pinpoints exact inflection periods and net percentage-point shifts across categories", footer, "\n  ".join(parts))


def render_subsignal_heatmap_svg(report: dict, title: str = "Sub-Signal Velocity & Lifecycle Heatmap") -> str:
    subs = report["subsignals"]
    sub_ids = list(subs.keys())
    ps = list(report["periods"].keys())
    cats = report["categories"]
    ch = 24.0
    w = 1140
    h = max(320, int(195 + len(sub_ids) * ch))
    x0, y0 = 275, 134
    cw = (w - x0 - 110) / max(1, len(ps))

    parts = []
    for qi, p in enumerate(ps):
        cx = x0 + (qi + 0.5) * cw
        parts.append(f'<text x="{cx:.1f}" y="{y0 - 10:.1f}" text-anchor="middle" font-family="{FONT_STACK}" font-size="9.5" font-weight="600" fill="#13294B">{esc(p)}</text>')
    parts.append(f'<text x="{w - 28}" y="{y0 - 10:.1f}" text-anchor="end" font-family="{FONT_STACK}" font-size="9.5" font-weight="700" fill="#475569">State</text>')

    for ri, sid in enumerate(sub_ids):
        smeta = subs[sid]
        ry = y0 + ri * ch
        vals = [report["periods"][p]["subsignal_rates"].get(sid, 0.0) for p in ps]
        rmax = max(vals, default=1.0) or 1.0
        ccol = cats.get(smeta["category"], {}).get("color", "#1F4E79")
        parts.append(f'<rect x="24" y="{ry + 3:.1f}" width="5" height="{ch - 6:.1f}" rx="1.5" fill="{ccol}"/>')
        parts.append(f'<text x="35" y="{ry + 15.5:.1f}" font-family="{FONT_STACK}" font-size="10" fill="#1E293B">{esc(smeta["label"])}</text>')
        for qi, v in enumerate(vals):
            cx = x0 + qi * cw
            norm = min(1.0, v / max(3.0, rmax))
            rc = int(248 - norm * (248 - 24))
            gc = int(246 - norm * (246 - 68))
            bc = int(240 - norm * (240 - 118))
            tcol = "#FFFFFF" if norm > 0.55 else "#334155"
            parts.append(f'<rect x="{cx + 1:.1f}" y="{ry + 1:.1f}" width="{cw - 2:.1f}" height="{ch - 2:.1f}" rx="2" fill="#{rc:02X}{gc:02X}{bc:02X}"/>')
            parts.append(f'<text x="{cx + cw / 2:.1f}" y="{ry + 15.5:.1f}" text-anchor="middle" font-family="{FONT_STACK}" font-size="8.8" fill="{tcol}">{v:.1f}</text>')
        state_lbl = report["subsignal_lifecycle"].get(sid, {}).get("trajectory", "")
        parts.append(f'<text x="{w - 26}" y="{ry + 15.5:.1f}" text-anchor="end" font-family="{FONT_STACK}" font-size="9" fill="#475569">{esc(state_lbl)}</text>')

    footer = "Cell values denote % penetration per period; right column classifies trajectory (igniting / peaking / high_plateau / maturing_infra / declining)."
    return _svg_card(w, h, "SUB-SIGNAL VELOCITY MATRIX", title, "Distinguishes emerging ignition from infrastructure plateau and true obsolescence", footer, "\n  ".join(parts))


def render_scissor_gap_svg(report: dict, title: str = "Scissor-Gap Divergence Analysis") -> str:
    sg = report.get("scissor_groups") or {}
    ga_ids = sg.get("group_a_ids", [])
    gb_ids = sg.get("group_b_ids", [])
    ga_lbl = sg.get("group_a_label", "Expansion / Capability Axis")
    gb_lbl = sg.get("group_b_label", "Governance / Capacity Axis")

    w, h = 1040, 480
    ps = list(report["periods"].keys())
    x0, y0, pw, ph = 72, 148, 910, 272
    n_p = max(1, len(ps))
    xs = [x0 + i * (pw / max(1, n_p - 1)) for i in range(n_p)]

    va = [sum(report["periods"][p]["primary_shares"].get(c, 0.0) for c in ga_ids) for p in ps]
    vb = [sum(report["periods"][p]["primary_shares"].get(c, 0.0) for c in gb_ids) for p in ps]
    max_y = max(20.0, max(va + vb, default=20.0) * 1.22)

    parts = []
    for g in range(5):
        gy = y0 + ph - (g / 4) * ph
        parts.append(f'<line x1="{x0}" y1="{gy:.1f}" x2="{x0 + pw}" y2="{gy:.1f}" stroke="#E5E0D5" stroke-dasharray="3,3"/>')
        parts.append(f'<text x="{x0 - 8}" y="{gy + 4:.1f}" text-anchor="end" font-family="{FONT_STACK}" font-size="9.8" fill="#64748B">{(g / 4) * max_y:.1f}%</text>')

    if n_p >= 2:
        pts_a = [(xs[i], y0 + ph - (va[i] / max_y) * ph) for i in range(n_p)]
        pts_b = [(xs[i], y0 + ph - (vb[i] / max_y) * ph) for i in range(n_p)]
        poly = " ".join([f"{x:.1f},{y:.1f}" for x, y in pts_a] + [f"{x:.1f},{y:.1f}" for x, y in reversed(pts_b)])
        parts.append(f'<polygon points="{poly}" fill="#B84A39" fill-opacity="0.12"/>')
        parts.append(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts_a)}" fill="none" stroke="#1F4E79" stroke-width="2.6"/>')
        parts.append(f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts_b)}" fill="none" stroke="#9E3B52" stroke-width="2.6" stroke-dasharray="5,3"/>')

    for i, p in enumerate(ps):
        parts.append(f'<text x="{xs[i]:.1f}" y="{y0 + ph + 18:.1f}" text-anchor="middle" font-family="{FONT_STACK}" font-size="9.5" fill="#475569">{esc(p)}</text>')

    parts.append(f'<line x1="{x0}" y1="120" x2="{x0 + 20}" y2="120" stroke="#1F4E79" stroke-width="2.6"/><text x="{x0 + 26}" y="124" font-family="{FONT_STACK}" font-size="10.5" fill="#1E293B">{esc(ga_lbl)} ({va[-1] if va else 0:.1f}%)</text>')
    parts.append(f'<line x1="{x0 + 340}" y1="120" x2="{x0 + 360}" y2="120" stroke="#9E3B52" stroke-width="2.6" stroke-dasharray="4,2"/><text x="{x0 + 366}" y="124" font-family="{FONT_STACK}" font-size="10.5" fill="#1E293B">{esc(gb_lbl)} ({vb[-1] if vb else 0:.1f}%)</text>')

    footer = f"Scissor gap in latest period ({ps[-1] if ps else ''}): {(va[-1] - vb[-1]) if va and vb else 0:+.1f} percentage points."
    return _svg_card(w, h, "SCISSOR-GAP DIVERGENCE", title, f"Compares {ga_lbl} against {gb_lbl} over time", footer, "\n  ".join(parts))


def render_visual_suite(report: dict, out_dir: Path, title_prefix: str = "Corpus") -> dict[str, Path]:
    """Generate the orthogonal SVG suite into out_dir."""
    out_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}

    f1 = out_dir / "01_volume_velocity.svg"
    f1.write_text(render_volume_velocity_svg(report, f"{title_prefix}: Volume, Intensity & Artifact Velocity"), encoding="utf-8")
    written["volume_velocity"] = f1

    f2 = out_dir / "02_conservation_sankey.svg"
    f2.write_text(render_conservation_sankey_svg(report, f"{title_prefix}: Multi-Period Flow Sankey"), encoding="utf-8")
    written["conservation_sankey"] = f2

    f3 = out_dir / "03_share_streamgraph.svg"
    f3.write_text(render_share_stream_svg(report, f"{title_prefix}: Category Share Streamgraph"), encoding="utf-8")
    written["share_streamgraph"] = f3

    if report["subsignals"]:
        f4 = out_dir / "04_subsignal_heatmap.svg"
        f4.write_text(render_subsignal_heatmap_svg(report, f"{title_prefix}: Sub-Signal Velocity Heatmap"), encoding="utf-8")
        written["subsignal_heatmap"] = f4

    if report.get("scissor_groups"):
        f5 = out_dir / "05_scissor_gap.svg"
        f5.write_text(render_scissor_gap_svg(report, f"{title_prefix}: Scissor-Gap Divergence"), encoding="utf-8")
        written["scissor_gap"] = f5

    return written


# -------------------- Rollover-Safe Markdown Slot Sync & Typst Helper --------------------

def build_markdown_slots(report: dict) -> dict[str, str]:
    """Generate rollover-safe dynamic Markdown tables for AUTO-SYNC slots."""
    slots: dict[str, str] = {}
    majors = list(report["major_periods"].keys())
    cats = report["categories"]
    partials = set(report.get("partial_periods", []))

    # 1. macro_overview (dynamic columns across all major_periods — zero hardcoded years!)
    m_hdr = " | ".join(f"{m}{' *' if m in partials else ''}" for m in majors)
    m_sep = " | ".join("---:" for _ in majors)
    lines = [
        f"| Category | {m_hdr} | Net Shift |",
        f"| :--- | {m_sep} | :--- |",
    ]
    for cid, cmeta in cats.items():
        cells = []
        shares = []
        for m in majors:
            mb = report["major_periods"][m]
            cnt = mb["primary_counts"].get(cid, 0)
            sh = mb["primary_shares"].get(cid, 0.0)
            shares.append(sh)
            cells.append(f"{cnt:,} ({sh:.1f}%)")
        delta = (shares[-1] - shares[0]) if len(shares) >= 2 else 0.0
        lines.append(f"| **{cmeta['label']}** | {' | '.join(cells)} | `{delta:+.1f}pp` |")
    slots["macro_overview"] = "\n".join(lines)

    # 2. recent_radar
    r_lines = [
        "| Date | ID | Title | Category | Entity | Score |",
        "| :--- | :--- | :--- | :--- | :--- | ---: |",
    ]
    for item in report["recent_frontier"][:12]:
        c_lbl = cats.get(item["primary_category"], {}).get("label", item["primary_category"])
        t_clean = item["title"].replace("|", "\\|")
        r_lines.append(f"| `{item['day']}` | `{item['id']}` | {t_clean} | {c_lbl} | {item['entity'] or '—'} | **{item['score']:g}** |")
    slots["recent_radar"] = "\n".join(r_lines)

    # 3. era_<MAJOR> and pillar_<CAT>
    for m in majors:
        mb = report["major_periods"][m]
        e_lines = [
            "| Rank | Date | ID | Title | Category | Score |",
            "| ---: | :--- | :--- | :--- | :--- | ---: |",
        ]
        for idx, rec in enumerate(mb["top_records"][:10], 1):
            c_lbl = cats.get(rec["primary_category"], {}).get("label", rec["primary_category"])
            e_lines.append(f"| {idx} | `{rec['day']}` | `{rec['id']}` | {rec['title'].replace('|', '\\|')} | {c_lbl} | **{rec['score']:g}** |")
        slots[f"era_{m}"] = "\n".join(e_lines)

    for cid, cmeta in cats.items():
        p_cells = [f"{report['major_periods'][m]['primary_counts'].get(cid, 0):,}" for m in majors]
        m_cells = [f"{report['major_periods'][m]['multi_rates'].get(cid, 0.0):.1f}%" for m in majors]
        slots[f"pillar_{cid}"] = "\n".join(
            [
                f"| Metric | {m_hdr} |",
                f"| :--- | {m_sep} |",
                f"| **Primary Count** | {' | '.join(p_cells)} |",
                f"| **Multi-Tag Rate** | {' | '.join(m_cells)} |",
            ]
        )

    return slots


def sync_markdown_text(md_text: str, report: dict) -> str:
    slots = build_markdown_slots(report)
    pattern = re.compile(r"(<!-- AUTO-SYNC:START:([a-zA-Z0-9_.-]+) -->)(.*?)(<!-- AUTO-SYNC:END:\2 -->)", re.S)

    def _sub(m: re.Match) -> str:
        key = m.group(2)
        if key not in slots:
            return m.group(0)
        return f"{m.group(1)}\n\n{slots[key]}\n\n{m.group(4)}"

    return pattern.sub(_sub, md_text)


def _typ_escape_plain(s: str) -> str:
    return "".join("\\" + ch if ch in ("\\", "#", "*", "_", "`", "@", "<", ">", "$", "~", "[", "]") else ch for ch in s)


_INLINE_TYPST_RE = re.compile(
    r"(`[^`]+`)"
    r"|(\$\$[^$]+\$\$)"
    r"|(\$(?!\d)(?!\s)[^$\n]{1,80}?(?<!\s)\$)"
    r"|(\[[^\]]+\]\([^)]+\))"
    r"|(\*\*[^*\n]+?\*\*)"
    r"|(\*[^*\s][^*\n]*?\*)"
)


def md_inline_to_typst(text: str) -> str:
    """Convert inline Markdown to Typst content while safely escaping currency like '$15 and $20'."""
    out: list[str] = []
    pos = 0
    for m in _INLINE_TYPST_RE.finditer(text):
        if m.start() > pos:
            out.append(_typ_escape_plain(text[pos : m.start()]))
        tok = m.group(0)
        if m.group(1):
            inner = tok[1:-1].replace("\\", "\\\\").replace('"', '\\"')
            out.append(f'#raw("{inner}")')
        elif m.group(2) or m.group(3):
            expr = tok.strip("$").strip()
            out.append(f"${expr}$")
        elif m.group(4):
            lm = re.match(r"\[([^\]]+)\]\(([^)]+)\)", tok)
            if lm and lm.group(2).startswith("http"):
                u = lm.group(2).replace("\\", "\\\\").replace('"', '\\"')
                out.append(f'#link("{u}")[{md_inline_to_typst(lm.group(1))}]')
            elif lm:
                out.append(md_inline_to_typst(lm.group(1)))
        elif m.group(5):
            out.append(f"#strong[{md_inline_to_typst(tok[2:-2])}]")
        elif m.group(6):
            out.append(f"#emph[{md_inline_to_typst(tok[1:-1])}]")
        pos = m.end()
    if pos < len(text):
        out.append(_typ_escape_plain(text[pos:]))
    return "".join(out)


# -------------------- CLI Entrypoints --------------------

def _load_input(path_arg: str, fmt: str = "auto") -> dict:
    raw_text = sys.stdin.read() if path_arg == "-" else Path(path_arg).read_text(encoding="utf-8")
    if fmt == "csv" or (path_arg != "-" and path_arg.endswith(".csv")):
        reader = csv.DictReader(io.StringIO(raw_text))
        recs = []
        for row in reader:
            recs.append(
                {
                    "id": row.get("id") or row.get("record_id") or "",
                    "timestamp": row.get("timestamp") or row.get("date") or "",
                    "title": row.get("title") or "",
                    "text": row.get("text") or row.get("summary") or "",
                    "category": row.get("category") or None,
                    "tags": [t.strip() for t in (row.get("tags") or "").split(",") if t.strip()],
                    "score": float(row.get("score") or 0.0),
                    "has_artifact": str(row.get("has_artifact", "")).lower() in ("1", "true", "yes"),
                    "entity": row.get("entity") or "",
                }
            )
        return {"records": recs}
    if fmt == "jsonl" or (path_arg != "-" and path_arg.endswith(".jsonl")):
        return {"records": [json.loads(ln) for ln in raw_text.splitlines() if ln.strip()]}
    parsed = json.loads(raw_text)
    return {"records": parsed} if isinstance(parsed, list) else parsed


def run_selftest() -> dict:
    sample = {
        "grain": "quarter",
        "major_grain": "year",
        "taxonomy": {
            "categories": [
                {"id": "a", "label": "Track A", "color": "#1F4E79", "pattern": r"\balpha\b"},
                {"id": "b", "label": "Track B", "color": "#2E7D6B", "pattern": r"\bbeta\b"},
            ],
            "subsignals": [{"id": "s1", "category": "b", "label": "Sub Beta", "pattern": r"\bbeta\b"}],
        },
        "records": [
            {"id": "1", "timestamp": "2024-02-01", "title": "alpha init", "text": "alpha", "score": 10},
            {"id": "1", "timestamp": "2024-05-01", "title": "alpha repeat", "text": "alpha beta", "score": 25},
            {"id": "2", "timestamp": "2025-03-01", "title": "beta launch", "text": "beta", "score": 40},
        ],
    }
    rep = analyze_corpus(sample)
    tr = rep["sankey_transitions"][0]
    row_ok = all(
        abs(sum(tr["matrix"][i]) - tr["src_shares"][cid]) < 1e-4
        for i, cid in enumerate(tr["categories"])
    )
    col_ok = all(
        abs(sum(tr["matrix"][i][j] for i in range(len(tr["categories"]))) - tr["dst_shares"][cid]) < 1e-4
        for j, cid in enumerate(tr["categories"])
    )
    svg_ok = ET.fromstring(render_conservation_sankey_svg(rep)).tag.endswith("svg")
    esc_ok = r"\$10" in md_inline_to_typst("Costs $10 and $20 while $x_1 = 1$.")
    invariants = {
        "dedup_separation": rep["total_events"] == 3 and rep["unique_records"] == 2,
        "sinkhorn_row_conservation": row_ok,
        "sinkhorn_col_conservation": col_ok,
        "svg_xml_well_formed": svg_ok,
        "typst_currency_safe": esc_ok,
    }
    return {"status": "ok" if all(invariants.values()) else "failed", "invariants": invariants}


def main() -> None:
    parser = argparse.ArgumentParser(description="Longitudinal time-series chronicle & Sankey engine")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_an = sub.add_parser("analyze", help="Analyze timestamped records into JSON report")
    p_an.add_argument("--input", required=True, help="JSON/JSONL/CSV file path or '-' for stdin")
    p_an.add_argument("--format", choices=["auto", "json", "jsonl", "csv"], default="auto")
    p_an.add_argument("--output", default="-", help="Output JSON path or '-' for stdout")

    p_rs = sub.add_parser("render-suite", help="Render orthogonal vector SVG chart suite")
    p_rs.add_argument("--input", required=True, help="Corpus input or pre-computed analyze JSON")
    p_rs.add_argument("--out-dir", required=True, help="Output directory for SVG files")
    p_rs.add_argument("--title-prefix", default="Longitudinal Atlas")

    p_sm = sub.add_parser("sync-md", help="Sync <!-- AUTO-SYNC:START:id --> slots in Markdown files")
    p_sm.add_argument("--report", required=True, help="Path to analyze JSON report")
    p_sm.add_argument("markdown_files", nargs="+", help="Markdown chapter files to update in-place")

    sub.add_parser("selftest", help="Verify algebraic, XML, and escaping invariants")

    args = parser.parse_args()
    if args.cmd == "selftest":
        res = run_selftest()
        print(json.dumps(res, indent=2))
        sys.exit(0 if res["status"] == "ok" else 1)

    if args.cmd == "analyze":
        payload = _load_input(args.input, fmt=args.format)
        rep = analyze_corpus(payload)
        out_str = json.dumps(rep, indent=2, ensure_ascii=False)
        if args.output == "-":
            print(out_str)
        else:
            Path(args.output).write_text(out_str, encoding="utf-8")
    elif args.cmd == "render-suite":
        data = _load_input(args.input)
        rep = data if "sankey_transitions" in data else analyze_corpus(data)
        written = render_visual_suite(rep, Path(args.out_dir), title_prefix=args.title_prefix)
        print(json.dumps({k: str(v) for k, v in written.items()}, indent=2))
    elif args.cmd == "sync-md":
        rep = json.loads(Path(args.report).read_text(encoding="utf-8"))
        for mf in args.markdown_files:
            p = Path(mf)
            p.write_text(sync_markdown_text(p.read_text(encoding="utf-8"), rep), encoding="utf-8")


if __name__ == "__main__":
    main()
