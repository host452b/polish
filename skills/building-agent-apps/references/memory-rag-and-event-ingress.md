# Memory, RAG Indexing & Unified Event Ingress Reference

## 1. RAG & Knowledge Organization Decision Matrix (Ch.3)

| Layer / Choice | Default Production Recommendation | Upgrade Trigger |
|---|---|---|
| **Chunking** | Structure-aware recursive chunking (`Markdown/HTML headings -> paragraphs -> sentences`), `256–1024` tokens, `10%–20%` overlap + **Contextual Retrieval prefix** (~$1.02 / 1M doc tokens with Prompt Cache; cuts top-20 retrieval failure by `49%–67%`) | Semantic embedding-cliff chunking for unstructured transcripts |
| **Vector ANN Index** | **HNSW (`hnswlib`)** for online incremental inserts/deletes; **ANNOY** for static read-only mmap sharing across worker processes | Rebuild HNSW periodically after heavy churn |
| **Retrieval & Fusion** | **Parallel Dense (`BGE-M3`) + Sparse (`BM25`, $k_1=1.5, b=0.75$, floor IDF at $10^{-6}$, code/ID-aware tokenizer) -> RRF (`k=60`)** | Add **Cross-Encoder Reranker (`bge-reranker-v2-m3`)** on top-50 only when verified on target multilingual/domain eval set (Exp 3-6 showed English-centric MiniLM reranker degraded Chinese MRR from `1.0 -> 0.903`) |
| **Query Control** | Single-shot RAG for direct fact lookup | **Agentic RAG** (ReAct search tool with explicit step budget) for multi-hop/conditional queries (Exp 3-8 lifted complex legal statute coverage `8% -> 92%`) |
| **Beyond Flat Chunks** | Pre-compute **Statistical Summaries** (for global counts like 90/100 black cats) and **Policy Rule Cards** (for eligibility boundaries/exceptions) at index time | **RAPTOR** tree for multi-resolution overview-to-detail navigation; **GraphRAG** + entity disambiguation for multi-hop relational queries |

## 2. Unified Event Ingress Envelope & Progress Separation (Ch.6)

```json
{
  "id": "evt_7f3a",
  "source": {"type": "app_chat", "sender": "user:u_5521", "verified": true},
  "dedupe_key": "app:msg:msg_1029",
  "thread": "app:conv:conv_88",
  "kind": "message",
  "correlation": ["order:12345"],
  "content": {"type": "text", "text": "这个订单我想退款"},
  "raw_ref": "raw/2026-11-23/app/msg_1029.json",
  "reply": {"via": "app_chat", "target": "app:conv:conv_88"},
  "occurred_at": "2026-11-23T14:02:09+08:00",
  "expires_at": null
}
```

### Four Ingress Invariants
1. **Verified Identity Only:** `source.verified` is set strictly by adapter HMAC signature, OAuth token, or channel session—never by self-declared text inside `content`.
2. **Semantic Deduplication Key:** Use client message ID for chat (`user saying "refund" twice = 2 messages`), webhook delivery ID for transport retries, and business key (`refund_id + status`) to deduplicate redundant webhook + Kafka notifications across channels.
3. **Thread vs. Correlation:** Order is guaranteed **within `thread` only**; cross-channel events (App chat + WeCom manager approval + Payment webhook + Kafka topic) keep their native `thread` partition keys and link to the same task via `correlation: ["order:12345"]`.
4. **Three Independent Cursors + Outbox:** Maintain `source_offset` (Kafka/SQS/IMAP), `dispatch_cursor` (log -> task router), and `task_state` + `outbox` (intent + idempotency key before send) independently so log replay never re-sends customer replies.

## 3. Fast/Slow Voice Latency & Queueing Math (Ch.6)

- **Queueing blow-up (M/M/1):** Total wait $W = S / (1 - \rho)$. At $S = 1\text{s}$, utilization $\rho$ rising from `0.5 -> 0.8` jumps latency from `2s -> 5s` (`3s` pure queueing). Monitor concurrency headroom, not just single-user TTFT.
- **Direct vs. Delegated Voice Tool Call:** Direct foreground call costs $\approx 2L_f + T$; delegating to a slow backend costs $\approx 2L_f + 2L_b + T$ (Exp 6-7 weather median `2.81s` direct vs `6.96s` delegated). Pre-inject resident user memory ($L_f$ only), let foreground call simple fast tools, delegate multi-step planning to background with explicit entity spelling/corrections, and persist unspoken background answers in runtime state so mid-wait user tangents never drop the primary result.
