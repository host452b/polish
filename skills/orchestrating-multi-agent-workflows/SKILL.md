---
name: orchestrating-multi-agent-workflows
description: Use when deciding between a single agent, deterministic workflow, or multi-agent system, designing Agent-to-Agent orchestration topologies, building Proposer-Reviewer or Manage-Execute-Audit loops, configuring multi-agent virtual filesystems or A2A protocols, or debugging multi-agent conflicts, cascading distortion, homogeneous convergence, or runaway spawning (Agent与Agent工作流编排、多Agent拓扑选型、Loop工程与防扯皮冲突). For live multi-model answers or niche knowledge relay, use model-council.
---

# Orchestrating Multi-Agent Workflows and Loops

Design multi-agent workflows and autonomous loops only where collaboration introduces **new information**, bounded context isolation, or wall-clock parallelism that outweighs coordination and token overhead.

## Orchestration Workflow

1. **Apply the New-Information Gate before adding agents.**
   - Start with a well-tooled **Single Agent** or deterministic **Code Workflow** (`Less structure, more intelligence`). Under equal thinking-token budgets, multi-agent text debate without external evidence matches or underperforms a single agent due to the Data Processing Inequality (lossy re-summarization).
   - Add a second agent only when it accesses **new evidence** (running protected tests, inspecting rendered PNGs/frames via Vision, querying raw source truth), **isolates noisy intermediate context** (e.g., book translation cutting peak prompt from `94,355` -> `2,857` tokens, total tokens `1.32M` -> `203K`), **enforces strict privilege separation**, or **parallelizes independent search branches**.
   *Completion criterion:* Explicit justification recorded naming the exact new evidence, isolation boundary, or parallel speedup each role provides.

2. **Choose Context Sharing & Topology along the two orthogonal axes.**
   - **Shared context:** Prefer **loading a Skill (`load_skill`)** over swapping `system` prompts (`transfer_to_agent`) when roles differ only in SOP/domain rules (Exp 10-1: `15/30` passed via Skill vs `2/30` via system-prompt swap, while preserving prefix cache). Use `transfer_to_agent` or isolated contexts only when tool visibility and permissions must differ.
   - **Isolated context topology:**
     - *2–3 roles iterating on one artifact* -> **Peer Collaboration (`Proposer–Reviewer`, `LoopX`, or `Manage–Execute–Audit`)**.
     - *Dynamic task decomposition, parallel fan-out, or cross-chapter coordination* -> **Manager–Worker** (assign the **strongest model + richest planning budget to the Manager**; alternatively let the Manager generate deterministic workflow code `agent()/parallel()/pipeline()` so it stays out of every hop).
     - *Symmetric peers negotiating directly without Manager bottleneck* -> **Decentralized SOP / Handoff** carrying `{task_id, sender, recipient, goal, constraints, accepted_facts, artifact_refs, remaining_budget, visited_agents}`.
     - *Cross-org / heterogeneous service boundaries* -> **A2A Protocol** (`Agent Card` discovery + `Task` lifecycle + `Message/Artifact` parts).
   *Completion criterion:* Context-sharing mode, topology, and handoff schema defined with cycle detection (`visited_agents`) and explicit step/token budgets.

3. **Partition the 4-Zone Virtual Filesystem & Control Plane.**
   Never mix scratch files, shared deliverables, and user mounts in one flat directory:
   - **Zone 1 — Agent Scratchpad:** Private per-instance read/write, auto-reclaimed on exit.
   - **Zone 2 — Shared Workspace:** Persistent deliverables (`glossary.json`, `progress.md`); guard concurrent writes with **optimistic version locks** (`write_if_version == v`) and **isolated Git worktrees + branches** per Coding Agent.
   - **Zone 3 — Mounted External Resources:** Read-only by default, scoped to principal OAuth/ACL.
   - **Zone 4 — Built-in System Resources:** Version-pinned read-only Skills and templates.
   - **Control-plane settlement:** In parallel first-hit search, verify candidate evidence **first**, claim the winner via an **atomic CAS + transactional outbox** (`UPDATE task SET winner = ? WHERE id = ? AND winner IS NULL`), then cascade graceful `SIGTERM`-style `cancel_subagent` down the process tree (`SIGKILL` fallback on timeout) and wait for cleanup acks.
   *Completion criterion:* Zero unguarded concurrent file writes, atomic winner settlement, and zero orphaned worker processes/browsers/disk clones.

4. **Harden against the 6 Multi-Agent Failure Modes.**
   1. **Concurrent file/semantic conflict:** Optimistic lock + per-agent git worktree + merge-point cross-file reference check (e.g., figure renumbering vs prose citations).
   2. **Cascading semantic distortion:** Reviewer checks raw evidence (call transcript / statement / source text) directly rather than trusting intermediate summaries ("promised $80 credit" compressed into "already refunded $80").
   3. **Homogeneous convergence:** Differentiate **model families** (e.g., Claude Proposer + GPT Reviewer), evidence slices, and resource namespaces so 30 parallel agents don't create identical branch names or share blind spots.
   4. **Role turf wars / buck-passing:** Pre-assign resource ownership and require every handoff to attach `{repro_steps, verified_evidence, specific_question}`. Distinguish `@agent` *advisory comment* from *ticket ownership transfer*.
   5. **Runaway spawn loops:** Enforce global tree-wide caps on `max_depth`, `max_spawn_count`, `concurrency`, `tokens/USD`, and aggregate network blast radius using isolated project API keys.
   6. **Understanding debt & cognitive surrender:** Require human-legible architecture/decision summaries and executable verification entrypoints with every multi-agent delivery.
   *Completion criterion:* All 6 failure modes explicitly addressed in runtime checks and review gates.

## Output Contract

When proposing or reviewing a workflow / multi-agent architecture, return these exact sections:
1. **New-Information Verdict:** Explicit pass/fail check on whether each proposed extra agent adds **new external evidence**, **noisy-context isolation**, **privilege separation**, or **wall-clock parallelism** over a single agent (`▶︎▶︎KEEP_SINGLE_AGENT▶︎▶︎` if none apply).
2. **Topology, Context & VFS Spec:** Table of `Role | Model Tier & Step Budget | Context Mode (Skill Load / Isolated) | VFS Zone Read/Write | Settlement / Lock Rule`.
3. **Six-Failure-Mode Guard Table:** One concrete runtime check per mode (`File/Semantic Conflict`, `Cascading Distortion`, `Homogeneous Convergence`, `Turf War`, `Runaway Spawn`, `Understanding Debt`).

## Disclosed Reference

- Read [references/multi-agent-topologies-and-protocols.md](references/multi-agent-topologies-and-protocols.md) for Proposer–Reviewer / LoopX / LongHorizon-Harness MEA code skeletons, atomic SQLite CAS + outbox patterns, and A2A vs. MCP boundaries.
