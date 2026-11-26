---
name: synthesizing-time-series-chronicles
description: "Use when turning timestamped records, event logs, changelogs, incident histories, release notes, telemetry archives, or multi-period corpora into longitudinal trend analyses, Sankey or velocity visualizations, evolutionary chronicles, or living multi-chapter compendia and PDFs (时间序列数据总结、跨期热点与桑基流向可视化、发展演进编年史、活体教材或厚报告自动合编). For point-in-time latency or speedup validation, use benchmark-checklist."
allowed-tools:
  - read
  - grep
  - glob
---

# synthesizing-time-series-chronicles

Synthesize timestamped corpora of any domain into a **Three-Tier Longitudinal Compendium**:

1. **Tier 1 — Atomic Record Digests**: 1:1 structured cards per record (without duplicating raw text blobs) preserving exact source metrics.
2. **Tier 2 — Two-Tier Taxonomy & Sinkhorn Flow Tensor**: 100%-conserved primary categories + multi-label co-occurrence + sub-signal velocity matrices, rendered as an orthogonal vector SVG suite via `scripts/chronicle_engine.py`.
3. **Tier 3 — Living Hybrid Chronicle**: Horizontal era chapters + vertical thematic pillar chapters with rollover-safe `AUTO-SYNC` data slots, a rolling recent-window radar, and optional single-command Typst vector PDF compilation.

## Workflow

1. **Audit temporal grain, deduplication basis, and boundary completeness**:
   - Separate **event-slice basis** (all period occurrences, measuring temporal agenda intensity) from **unique-entity basis** (deduplicated by canonical ID keeping peak score/severity, used for Top-N landmarks and recent radars).
   - Choose two nested grains: a fine `grain` (`month` or `quarter`, 8–20 buckets) for streamgraphs and velocity heatmaps, and a coarse `major_grain` (`year` or `half-year`, 2–6 epochs) for Sankey columns and era chapters.
   - Flag **partial boundary periods** (leading or trailing buckets with `<50%` of median interior active days/volume) so incomplete windows are marked with `*` rather than misread as real drops.
   - *Completion criterion*: Both grains, dedup key, score/intensity field, and partial boundary buckets are explicitly identified from actual data.

2. **Build atomic digests and a two-tier weighted taxonomy**:
   - When per-record summarization is requested, mirror raw partitions into compact 4-slot digests (`Thesis/Trigger` · `Mechanism/Setup` · `Verified Metrics/Outcome` · `Actionable Takeaway`). Extract numbers strictly from source records; omit raw full-text blobs from digest JSON to keep repository packfiles small.
   - Define 6–12 **Primary Categories** (mutually exclusive top rank via `3x` title/headline + `1x` body weight so period shares sum to `100%`), retain secondary **Multi-Label Tags** (`>=30%` of top score) to measure cross-category coupling, and define 15–30 **Sub-Signals** to track micro-level lifecycle states (`igniting`, `peaking`, `high_plateau`, `maturing_infra`, `declining`).
   - *Completion criterion*: Unclassified rate `<5%`; every category and key domain term has one locked canonical name (invoke `consistent-term-translation-polish-guard` when bilingual output is required).

3. **Compute Sinkhorn flows and pass the Render-and-Read Visual Gate**:
   - Resolve `SKILL_DIR` from this skill's `Base directory` header or folder path. Read [`references/visual-grammar-and-typst.md`](references/visual-grammar-and-typst.md) for input schemas, domain mappings, SVG band budgets, and Typst templates.
   - Run `chronicle_engine.py` over JSON, JSONL, or CSV (prefer stdin `--input -` or `/tmp` scratch paths):
     ```bash
     python3 "$SKILL_DIR/scripts/chronicle_engine.py" analyze --input - --output /tmp/report.json <<'EOF'
     { "grain": "quarter", "major_grain": "year", "taxonomy": { ... }, "records": [ ... ] }
     EOF
     python3 "$SKILL_DIR/scripts/chronicle_engine.py" render-suite --input /tmp/report.json --out-dir ./figures --title-prefix "Domain Atlas"
     ```
   - Select charts by the **Orthogonal Visual Grammar** (each answers a distinct longitudinal question):
     - `01_volume_velocity.svg` — separates volume inflation from mean intensity/severity and artifact/adoption rate.
     - `02_conservation_sankey.svg` — Sinkhorn-balanced ($\sum_j T_{ij} = p^{(t)}_i$, $\sum_i T_{ij} = p^{(t+1)}_j$) rank-sorted columns revealing rank flips, split-offs, and convergent births; uses an **outside-right unidirectional label gutter** whenever columns $\ge 3$.
     - `03_share_streamgraph.svg` — `100%` normalized stacked shares pinpointing exact inflection periods and net $\Delta\text{pp}$.
     - `04_subsignal_heatmap.svg` — sub-signal $\times$ period matrix separating *maturing into infrastructure* from *dying fad*.
     - `05_scissor_gap.svg` (when opposing axes exist, e.g. capability vs safety, traffic vs capacity, incident rate vs guardrail coverage).
   - **Render-and-Read Visual Gate**: Rasterize every generated SVG (and sample PDF pages) to PNG in `/tmp` and inspect them with `read` to verify zero label collision, zero legend-to-header overlap, and $\ge 1.2\times$ axis headroom; delete `/tmp` previews afterward.
   - *Completion criterion*: All XML parses cleanly, Sinkhorn row/column sums match shares within `1e-4`, and visual inspection confirms zero overlapping text or clipped curves.

4. **Author hybrid chapters with rollover-safe `AUTO-SYNC` slots**:
   - Combine **Part I (Macro Panorama & Sankey Atlas)** + **Part II (Horizontal Era Chapters — concurrent dynamics per major period + Rolling Recent-Window Radar)** + **Part III (Vertical Pillar Chapters — one core domain's end-to-end trajectory across all periods)** + **Part IV (Methodology, Top-N Landmark Compendium & Glossary)**.
   - Wrap live quantitative tables in `<!-- AUTO-SYNC:START:<slot_id> --> ... <!-- AUTO-SYNC:END:<slot_id> -->` and sync via `chronicle_engine.py sync-md` so future incremental updates refresh numbers and rolling radars while preserving analytical prose.
   - Generate period table headers dynamically from observed `major_periods` (**Period-Rollover Invariant** — zero hardcoded year/quarter column counts that break when the next calendar year arrives).
   - *Completion criterion*: Every chapter pairs durable causal prose with live-synced empirical tables, landmark case studies, and review/decision questions.

5. **Compile vector PDF and isolate incremental CI rebuilds**:
   - Embed vector SVGs directly into Typst (`supplement: none` when captions already carry figure numbers; currency-safe inline parser `md_inline_to_typst` so `$15 and $20` stays literal text while `$p_1 + p_2 = 1$` renders as math).
   - When wiring into scheduled ingestion pipelines (cron / CI), gate compilation on actual upstream data diffs, provide an environment/variable kill switch, and isolate optional font/PDF steps so transient package mirror blips never block raw data archiving.
   - *Completion criterion*: Compiled PDF verified for page count, clickable TOC bookmarks, cover/callout/table rendering, and clean `selftest` / unit test exit `0`.

## Guardrails Against Common Shortcuts

| Shortcut Rationalization | Required Practice |
| --- | --- |
| "Isolated per-year bar charts show the trend." | Bar charts hide flow redirection. Pair rank-sorted Sinkhorn Sankey flows with a `100%` streamgraph and sub-signal velocity heatmap. |
| "The SVG XML is valid, no need to render PNGs." | Valid XML still hides text collisions and clipped lines. Render to PNG and inspect via `read` before completion. |
| "Latest period volume dropped 40%, trend is cooling." | Check active-day coverage first; mark incomplete boundary buckets as partial (`*`) rather than reporting false declines. |
| "Hardcoding `2023 \| 2024 \| 2025 \| 2026` columns is fine." | Derive Markdown/Typst table headers dynamically from `major_periods` so calendar rollovers never corrupt column counts. |
| "Regenerate whole chapters from templates on every update." | Keep analytical prose human-grade; mutate only bounded `AUTO-SYNC` tables, SVG figures, and rolling recent-window radars. |
