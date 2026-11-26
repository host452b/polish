---
name: architecting-agent-memory-rag
description: Use when designing, auditing, or tuning cross-session user memory systems, hybrid dense+BM25 RAG pipelines, Contextual Retrieval chunking, RAPTOR or GraphRAG structured indexes, Agentic RAG search tools, or PR-reviewed knowledge base updates (用户记忆架构、混合 RAG 检索调优、RAPTOR 与 GraphRAG 选型、知识库更新与多租户隔离).
---

# Architecting Agent Memory and RAG Systems

Design persistent cross-session **User Memory** and shared **Knowledge Bases (RAG)** so agents recall user-specific constraints proactively, retrieve exact + semantic domain truth without context rot, and enforce tenant ACLs at the index layer.

## Architecture & Tuning Workflow

1. **Separate Memory vs. Knowledge Base along three orthogonal axes.**
   - **Scope:** Per-user preferences/entities/history -> **User Memory**; multi-user domain policies/docs -> **RAG Knowledge Base**; single-run append-only trace -> **Trajectory**; workflow stage -> **Business State**.
   - **Dual-Layer User Memory (required for L3 proactive service):**
     - *Resident Layer:* Keep compact **Advanced JSON Cards** (`fact + person + relationship + backstory + valid_from/until`) in context for high-leverage entities/constraints (disambiguates same-name entities like two "Dr. Zhangs" and surfaces proactive alerts such as passport expiry <180 days before international travel).
     - *Retrieved Layer:* Append session extractions as **ADD-only timestamped records** (Mem0 v3 pattern: defer conflict resolution from write-time to read-time to prevent irreversible overwrite loss; lifted LoCoMo `71.4 -> 91.6`), retrieved via hybrid search.
     - *Deterministic Rules:* Express date math, totals, and allergy/policy checks as **User as Code** (typed dataclasses + pure functions). Redact PII **locally** (`regex fast-path + local small LLM semantic pass` + precision check on ticket/order IDs) before cloud storage.
   *Completion criterion:* Memory schema explicitly separates resident overview cards, append-only event records, and code-evaluated constraints.

2. **Build and measure each stage of the Hybrid RAG Pipeline.**
   - **Index-time enrichment:** Split via structure-aware recursive chunking (`256–1024` tokens, `10%–20%` overlap) and prepend **Contextual Retrieval** background prefixes (`[From ACME 2025 Q2 Report, KPI section]`) before indexing—recovering lost pronouns/subjects for both BM25 and dense vectors (cutting top-20 retrieval failure by `49%–67%`).
   - **3-Stage Retrieval:** Run **Dense (`BGE-M3` + `HNSW` for online writes / `ANNOY` for static mmap)** and **Sparse (`BM25`, $k_1=1.5, b=0.75$, floor IDF at $10^{-6}$, code/ID-aware tokenizer)** in parallel -> fuse via **RRF ($k=60$)** -> apply **Cross-Encoder Reranking** on top-50 *only after verifying non-regression on target language queries* (English-heavy rerankers can demote Chinese hits, Exp 3-6).
   - **Beyond flat chunks:** Pre-compute **Statistical Summaries** (for global ratios/counts where top-$k$ samples are biased) and **Policy Rule Cards** (for eligibility boundaries/exceptions) at index build time. Add **RAPTOR** trees only for cross-chapter multi-resolution queries, **GraphRAG** only for multi-hop entity chains, and **Agentic RAG** (bounded ReAct search tool) for multi-factor questions (`8% -> 92%` complex statute coverage).
   *Completion criterion:* Stage-by-stage `recall@k`, `MRR`, and `nDCG@k` measured before tuning generation prompts.

3. **Enforce PR-Style Knowledge Governance & Index-Layer Security.**
   - **3-Tier Storage:** Keep raw transcripts/docs immutable (Evidence Layer) -> maintain human+agent readable Markdown/code in Git (Knowledge Layer) -> rebuild vector/BM25 indexes from merged commits (Service Layer) linked via `OpenViking` L0 (`256`-char abstract) -> L1 (`4,000`-char overview) -> L2 (full text) + explicit cross-file links.
   - **Dual-Path Updates:** Run **Proposer -> Cross-Family Reviewer PRs** for incremental updates (verifying assertions against raw evidence) + periodic **Global Consolidation** grounded in raw transcripts (never rewriting summaries of summaries). Attach `version + valid_from + valid_until` metadata.
   - **Pre-Retrieval ACL & Anti-Poisoning:** Push tenant/user permission filters down into the retrieval query *before* chunks enter LLM context; wrap retrieved chunks in `<external_content>` tags so poisoned docs cannot trigger unauthorized tool calls.
   *Completion criterion:* Zero direct unreviewed index writes, periodic raw-source audit scheduled, and ACL filtering enforced inside the index query.

## Output Contract

When reviewing or designing a Memory/RAG system, output these exact sections:
1. **Layer & Failure Diagnosis:** Identify whether the bottleneck sits in `Chunking/Context Loss`, `Lexical vs. Dense Recall`, `Fusion/Rerank`, `Missing Index-Time Aggregation`, `Write-Time Overwrite`, or `ACL/Injection Boundary` (cite `file:line` or metric evidence tagged `[VERIFIED]/[ASSUMED]`).
2. **Concrete Architecture Spec:** Table specifying `Storage Layer | Format & Index | Update/Conflict Rule | Verification Metric`.
3. **Minimal Ablation Plan:** One paired retrieval experiment (`recall@k` + `MRR` + latency) to validate the chosen components before rollout.

## Disclosed Reference

- Read [references/memory-and-rag-matrix.md](references/memory-and-rag-matrix.md) for the 4 memory format trade-offs, ANNOY vs. HNSW & RAPTOR vs. GraphRAG matrices, and v3.0 benchmark numbers.
