# Visual Grammar, Domain Schemas & Typst Textbook Patterns

Reference for `scripts/chronicle_engine.py` (Python 3.10+ stdlib only) and multi-chapter PDF compilation.

---

## 1. Cross-Domain Input Mapping

`chronicle_engine.py` accepts JSON (`--input path.json` or `--input -`), JSONL (`--format jsonl`), or CSV (`--format csv`). Any longitudinal dataset maps onto the same 7 canonical record fields:

| Canonical Field | Research / Patents | Git / Changelogs / RFCs | Incidents / Bugs / Tickets | Product / Market / Filings |
| --- | --- | --- | --- | --- |
| `id` | ArXiv / Patent ID | Commit SHA / PR / RFC ID | Incident / Issue key | Event / Filing / Ticket ID |
| `timestamp` | Published / archived date | Merge / release date | Outage / opened date | Announcement / filing date |
| `title` | Title | Commit header / PR title | Incident summary | Headline / feature name |
| `text` | Abstract / claims | Body / diff summary | Root-cause & impact notes | Description / transcript |
| `score` | Upvotes / citations | Lines / review weight | Severity weight / customer mins | Revenue impact / engagement |
| `has_artifact` | Code / dataset link | Linked test / ADR / runbook | Postmortem / regression test | Verified attachment / repro |
| `entity` | Lab / institution | Subsystem / team | Service / owning squad | Vendor / segment / region |

### Full JSON Input Schema

```json
{
  "grain": "quarter",
  "major_grain": "year",
  "taxonomy": {
    "categories": [
      {
        "id": "automation_agent",
        "label": "Autonomous Ops",
        "color": "#2E7D6B",
        "pattern": "\\b(autonomous|self-healing|harness|workflow)\\b"
      }
    ],
    "subsignals": [
      {
        "id": "auto_harness",
        "category": "automation_agent",
        "label": "Remediation Harnesses",
        "pattern": "\\b(harness|self-healing)\\b"
      }
    ]
  },
  "scissor_groups": {
    "group_a_label": "Automation Velocity",
    "group_a_ids": ["automation_agent"],
    "group_b_label": "Security Guardrails",
    "group_b_ids": ["security_guardrail"]
  },
  "records": [
    {
      "id": "INC-201",
      "timestamp": "2025-01-15",
      "title": "Autonomous deploy harness rolled out progressive canary",
      "text": "Automated rollback harness verified SLO guardrails across 12 regions.",
      "score": 130,
      "has_artifact": true,
      "entity": "SRE-Bot"
    }
  ]
}
```

Records may also specify `"category": "..."`, `"tags": [...]`, and `"subsignals": [...]` directly without regex patterns.

---

## 2. The 5+1 Orthogonal Longitudinal Visual Grammar

Never plot redundant restatements of the same table. Each figure in a longitudinal atlas serves one distinct analytical role:

1. **Dual-Axis Volume, Intensity & Completeness (`01_volume_velocity.svg`)**
   - *Question answered*: Is activity growing in raw count, average impact/quality, or artifact maturity — and which edge buckets are partial (`*`)?
2. **Rank-Sorted Sinkhorn Conservation Sankey (`02_conservation_sankey.svg`)**
   - *Question answered*: When an old category shrinks, where did attention migrate, and which upstream tracks converged to fuel the new #1 track?
   - *Math*: Build affinity $A_{ij} = \gamma_{\text{self}}$ on diagonal ($i=j$) and empirical normalized co-occurrence $\frac{C^{(t+1)}_{ij}}{C^{(t+1)}_{ii}} \cdot g(p^{(t+1)}_j - p^{(t)}_i)$ off-diagonal ($i \neq j$); run Sinkhorn proportional scaling until row sums equal $\mathbf{p}^{(t)}$ and column sums equal $\mathbf{p}^{(t+1)}$.
3. **Multi-Generation Mechanism Lineage Sankey (Custom 3–4 Stage)**
   - *Question answered*: How did specific Stage I primitives combine into Stage II mechanisms, Stage III breakthroughs, and Stage IV production stacks?
4. **100% Normalized Period Streamgraph (`03_share_streamgraph.svg`)**
   - *Question answered*: In which exact quarter/month did structural regime shifts occur, and what is each category's net percentage-point gain/loss ($\Delta\text{pp}$)?
5. **Sub-Signal $\times$ Period Velocity Heatmap (`04_subsignal_heatmap.svg`)**
   - *Question answered*: Which micro-techniques are igniting right now versus plateauing into standard infrastructure versus genuinely declining?
6. **Scissor-Gap Divergence (`05_scissor_gap.svg`, conditional)**
   - *Question answered*: Is risk/governance/capacity falling behind capability/demand/complexity expansion?

---

## 3. Collision-Free SVG Band Budget

When authoring custom vector SVGs beyond `chronicle_engine.py`, enforce strict non-overlapping vertical bands:

- `y = 0..62`: Navy title banner (`tag` at `y = 26`, `title` at `y = 47`)
- `y = 82`: One-line takeaway subtitle + divider rule at `y = 92`
- `y = 108..130`: Multi-column legend strip (**never** place plot titles or column headers inside this band)
- `y = 146..162`: Column / panel headers (`y_top - 26` and `y_top - 11`, requiring `y_top >= 170` whenever a 2-row legend is present)
- `y = 172..(H - 50)`: Plot / Sankey canvas (`>= 1.22x` y-axis headroom above max data point; white `stroke-width="3"` halo under data labels)
- `x_right = W - 235` with `text-anchor="start"` on ALL columns when `num_cols >= 3` so Column $k-2$ and Column $k-1$ never point labels into the same inter-column gap
- `y = (H - 32)..H`: Provenance & sample-size footer (`N` event-slices, unique IDs, date span, partial-bucket note)

---

## 4. Western University Textbook Typst Skeleton

Embed vector SVGs natively (`#image("/figures/02_conservation_sankey.svg", width: 100%)` compiled with `typst.compile(..., root=book_dir)`) so 100+ page compendia stay ~2–5 MB with infinite zoom sharpness:

- **Font stack with CJK + Linux CI fallback**:
  - Serif body: `("Georgia", "Libertinus Serif", "Songti SC", "Noto Serif CJK SC")`
  - Sans headings/tables/callouts: `("Helvetica Neue", "Arial", "Hiragino Sans GB", "Noto Sans CJK SC")`
  - Ubuntu CI package: `fonts-noto-cjk` + pinned `typst` wheel.
- **Pedagogical structure per chapter**:
  - Cover page (navy `#13294B`, gold `#E8C574` hairline, centerpiece Sankey, corpus edition stamp)
  - Full-page Part dividers (`PART I`..`PART IV`)
  - Chapter opener (`CHAPTER NN` badge + title + dual navy/gold rule + `LEARNING OBJECTIVES` box)
  - Unbreakable/tinted callouts (`KEY CONCEPT`, `LANDMARK CASE STUDY`, `PARADIGM SHIFT`)
  - Booktabs zebra tables (`auto` width for short ID/numeric columns, `1.1fr`–`2.1fr` for prose columns)
  - `figure(..., supplement: none)` when caption strings already include `Figure X.Y` / `图 X.Y`
  - Currency-safe inline parser (`chronicle_engine.md_inline_to_typst`): require inline `$...$` math not to start with `$<digit>` so prose like `costs between $15 and $20` never triggers Typst math-variable errors.
