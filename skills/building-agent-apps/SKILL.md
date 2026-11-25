---
name: building-agent-apps
description: Use when architecting or building downstream AI Agent applications — including coding-core general agents, cross-session user memory systems, hybrid or Agentic RAG knowledge bases, webhook or queue-driven async event agents, fast/slow voice or Computer Use GUI agents, or Generative UI and SQL Artifact apps (构建 Agent 下游应用、用户记忆与 RAG 知识库、异步事件驱动接入层、快慢语音与 GUI、生成式 UI 与数据层权限).
---

# Building Production Agent Applications

Turn `LLM + Context + Tools` into reliable vertical or general-purpose applications by combining a **Coding + Filesystem** execution core, structured **Memory & RAG**, a **Unified Event Ingress**, **Fast/Slow multimodal interaction**, and **Data-Layer security**.

## Application Architecture Workflow

1. **Choose the Core Execution & Persistence Pattern.**
   - **Open-ended / general apps (research, data analysis, multimedia, ops):** Build around a **Coding Agent + Workspace Filesystem** core (7 base tools: `code_interpreter`, `bash`, `read_file`, `write_file`, `edit_file`, `glob`, `grep`). Prefer code/API execution over GUI clicking whenever an API, CLI, or library (`pandas`, `OOXML`, `Slidev`, `FFmpeg`, `CadQuery`) exists; compile repeated successful GUI trajectories into parameterized Playwright/RPA scripts with post-condition state assertions.
   - **Human + Agent co-maintained state:** Store long-term workspace rules and readable memory in Git-versioned Markdown (`AGENTS.md`, `MEMORY.md`, `USER.md`) linked via explicit index pages (`OpenViking` L0 256-char abstract -> L1 4,000-char overview -> L2 full text).
   *Completion criterion:* Capability map separates deterministic code/API paths from open-ended GUI/LLM paths, with persistent workspace storage defined.

2. **Architect Cross-Session User Memory & Knowledge Bases (RAG).**
   - **Dual-Layer User Memory (for L1 recall, L2 multi-session disambiguation, L3 proactive service):**
     - Keep compact **Advanced JSON Cards** (`fact + person + relationship + backstory + valid_from/until`) resident in context for key entities/constraints so the agent notices hidden cross-session links (e.g., passport expiry <180 days before booked Tokyo flight).
     - Store full history as **append-only ADD event logs** (Mem0 v3 style: defer conflict resolution from write-time to read-time, lifting LoCoMo `71.4 -> 91.6`), retrieved via **Contextual Retrieval** (prepend document/session context prefix at index time before **BM25 + Dense Embedding + RRF (`k=60`) + Cross-Encoder Reranking**).
     - Upgrade deterministic math/date/allergy rules to **User as Code** (typed Python dataclasses + pure check functions). Redact PII **locally** before cloud logging (`regex fast-path + local small LLM semantic pass`).
   - **Knowledge Base Governance:** Treat knowledge updates as **Git PRs** reviewed by a **heterogeneous-model Reviewer Agent** against raw immutable evidence, with periodic global consolidation returning to raw transcripts (never summarizing summaries of summaries). Push **tenant/ACL filtering down into the retrieval index layer** before chunks ever enter LLM context.
   *Completion criterion:* Resident vs. retrieved memory layers, hybrid index pipeline, index-level ACL filter, and PR update/expiration workflow specified.

3. **Build the Unified Event Ingress & Fast/Slow Real-Time Loop (Async, Voice, GUI).**
   - **Unified Event Ingress:** Normalize app chat, Feishu/Slack, email, webhooks, SQS/Kafka, and `set_timer` / `monitor_shell` into a single **Event Envelope** (`id`, `source.verified`, `dedupe_key`, `thread`, `correlation`, `kind: state|message`, `raw_ref`, `reply`, `occurred_at`, `expires_at`).
   - **ACK-after-append & 3-Progress Separation:** Persist to the append-only ingress log and **ACK upstream immediately** (beating Feishu 3s / WeCom 5s / SQS visibility timeouts). Track `source_offset`, `dispatch_cursor`, and `task_state` (+ outbound `outbox`) **separately**. Drop expired events, coalesce queued `state` events to latest, and batch `message` events with explicit `[Unhandled Event i/N]` tags so the model answers every item.
   - **Main vs. Executor / Fast vs. Slow Split:** Keep a responsive **Foreground / Main Session** (handling turn-taking, interruptions, explicit name/number confirmations to prevent ASR homophone corruption like `"陈嘉怡" -> "陈佳宜"`, and tracking unspoken pending tool results across interruptions) paired with an isolated **Background / Executor Session** for deep reasoning and slow tools.
   - **Computer Use Grounding:** Prefer **DOM / Accessibility Tree indexed IDs** (`browser-use` `[1]..[k]`) on Web/mobile, **Set-of-Mark** on unindexed native canvases, and aspect-ratio-matched coordinate scaling (`subtract letterbox padding -> scale`) on GUI-trained models; capture inter-action keyframes + persistent text descriptions for transient toasts.
   *Completion criterion:* Ingress envelope, deduplication key semantics, cancellation safe-points, and foreground/background state handoff verified.

4. **Deliver Generative UI / Artifacts with Data-Layer Access Control.**
   - **Artifact Direct-to-UI:** For SQL queries, large tables, and charts, have the model emit verified SQL / declarative UI (`A2UI` + `AG-UI`) or customize a stable React/FastAPI HMR shell—stream query rows directly from the execution service to the UI rather than copying rows through LLM output tokens. Clear stale conditional form fields on state toggle (Exp 5-12).
   - **Data-Layer Trust Boundary:** As application UI/logic becomes dynamically generated, enforce permissions and state-machine invariants inside a trusted **Data Access Layer / PostgreSQL Row-Level Security (`AccessContext`)** that generated code cannot bypass.
   - **Dedicated Virtual Identity:** Give personal/ops agents their own email, phone number, and on-demand sandbox VM/container rather than raw access to the user's primary personal accounts; hand off 2FA/CAPTCHA via VNC/trusted auth UI.
   *Completion criterion:* Data rows bypass LLM transcription where appropriate, dynamic UI clears invalidated state, and RLS/`AccessContext` enforces tenant/role boundaries independently of generated app code.

## Disclosed Reference

- Read [references/memory-rag-and-event-ingress.md](references/memory-rag-and-event-ingress.md) for the Unified Event Envelope JSON schema, RAG chunking/ANN/reranking parameter defaults, and StructuredIndex (`RAPTOR` vs `GraphRAG`) selection criteria.
