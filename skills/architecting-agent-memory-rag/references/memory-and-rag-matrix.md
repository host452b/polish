# User Memory Formats, Hybrid RAG Defaults & Structured Index Matrix

## 1. User Memory Storage Formats (Ch.3 Exp 3-2, 60 Cases)

| Format | Pass Rate (60 cases) | Token Footprint | Strengths | Failure Mode to Guard |
|---|---:|---:|---|---|
| `Simple Notes` | 48 / 60 | Lowest | $O(1)$ key lookup, cheap extraction | Drops multi-attribute context across fragments |
| `Enhanced Notes` | 52 / 60 | ~990K | Preserves narrative links | Redundant across paragraphs; hard to update cleanly |
| `JSON Cards` | 51 / 60 | Moderate | Clean partial field updates | Rigid single-category tree drops cross-cutting activities |
| `Advanced JSON Cards` | 49 / 60 (19/20 on L3) | ~1.55M | `person + relationship + backstory + timestamp` solves homonym disambiguation | **Whole-card LLM rewrites drop older items** (lost Netflix & Disney+ by session 3 in Exp 3-2 -> pair with ADD-only log!) |
| **Dual-Layer (Cards + Contextual RAG)** | **57 / 60** (20/20 on L2) | Balanced | Global proactive awareness + lossless detail recall | Audit boundary regressions (3 regressions alongside 8 gains in Exp 3-11) |

## 2. RAG Pipeline Component Matrix (Ch.3)

| Decision | Option A | Option B | Selection Rule |
|---|---|---|---|
| **Vector Index** | **ANNOY** (random projection trees, ~13ms build, mmap shared read-only) | **HNSW** (hierarchical graph, supports incremental insert/delete) | Static batch releases -> `ANNOY`; live streaming inserts -> `HNSW` (periodic rebuild) |
| **Lexical vs. Dense** | **BM25** ($k_1=1.5, b=0.75$, floor IDF at $10^{-6}$) wins exact SKUs (`XR-7003`), error codes, names | **Dense (`BGE-M3`, 8K ctx)** wins synonyms (`cat` vs `kitten/feline`) & cross-lingual | Always run **Parallel Hybrid + RRF ($k=60$)** in production |
| **Structured Index** | **RAPTOR** (recursive cluster summaries) | **GraphRAG** (entity-relation triples + community summaries) | Overview-to-detail hierarchy -> `RAPTOR`; multi-hop entity paths (`CPUID -> XCR0 -> YMM`) -> `GraphRAG`; keep natural-language originals because triples lose conditionals (`"if it rains next week..."`) |
