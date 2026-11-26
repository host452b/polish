# Multi-Agent Topologies, Loop Control Planes & Atomic Coordination

## 1. Proposer–Reviewer & Manage–Execute–Audit (MEA) Invariants (Ch.5 & Ch.10)

### Three Non-Negotiable Reviewer Invariants
1. **Modality / Evidence Shift:** Reviewer must inspect **executed or rendered artifacts** (test output, PNG slide renders via Vision LLM, keyframe clips, DB records)—never self-critique raw code/text in the same modality without external feedback. (In Exp 5-6, dual-agent Slidev review cut peak context from `92,601` -> `24,186` tokens at identical 95-point quality.)
2. **Locatable Rejection:** Rejections must specify `{location/page/line, issue_type, severity, repair_condition}`, never vague prose.
3. **Immutable Gate:** Neither Proposer nor Reviewer can edit protected test suites, rubric definitions, or release thresholds.

### LongHorizon-Harness MEA Control Loop
- **Manager:** Reads `{original_goal, verified_progress, failure_evidence, remaining_todo}` and emits **one bounded subtask**.
- **Executor:** Runs GUI/CLI actions in a **fresh isolated context** (eliminating Context Rot and Context Anxiety).
- **Auditor (Read-Only):** Verifies environment state; only audited progress commits to persistent control-plane state (`LoopX`). Lifted WeaveBench `51.8% -> 80.7%`, OSWorld 2.0 `2.8% -> 8.3%`, and Terminal-Bench 2.1 `69.7% -> 77.2%` (-24% tokens).

## 2. Atomic Winner Registration + Transactional Outbox Cancellation (Ch.10)

When $N$ parallel workers search for a single verified target, protect settlement and cancellation in **one DB transaction** so simultaneous hits or Manager crashes cannot double-deliver or leak zombie workers:

```python
import sqlite3

def claim_winner_and_enqueue_cancels(conn: sqlite3.Connection, task_id: int, winner_id: str, peer_ids: list[str]) -> bool:
    with conn:
        cur = conn.execute(
            "UPDATE task SET winner = ? WHERE id = ? AND winner IS NULL",
            (winner_id, task_id),
        )
        if cur.rowcount == 0:
            return False
        for peer in peer_ids:
            if peer != winner_id:
                conn.execute(
                    "INSERT OR IGNORE INTO cancel_outbox (msg_id, task_id, target_agent, acked) VALUES (?, ?, ?, 0)",
                    (f"cancel:{task_id}:{peer}", task_id, peer),
                )
        return True
```

## 3. MCP vs. A2A vs. Subagent Tool Call

| Interface | Primary Relationship | When to Choose |
|---|---|---|
| **Local `spawn_subagent` / `load_skill`** | Intra-process / same-team task isolation or role shift | Default inside a single application; lowest latency and simplest trace debugging |
| **MCP (`tools` / `resources` / `prompts`)** | Agent Host <-> Tool / Data Server | Standardizing deterministic tools, DB queries, or SaaS connectors across hosts |
| **A2A (`Agent Card` / `Task` / `Artifact`)** | Autonomous Agent Service <-> Remote Opaque Agent Service | Cross-team or cross-organization delegation where each side hides internal prompts/memory/tools and negotiates task states (`submitted`, `working`, `input-required`, `completed`, `failed`) |

## 4. Machine Resource Protection for Local Parallel Agents (Ch.4 & Ch.10)

- Use **copy-on-write / `git worktree`** instead of full repo copies (prevents parallel agents from filling TB-scale disks in hours).
- Enforce **CPU/memory/GPU cgroup quotas** and lower OS scheduling priority (`nice`) on background workers so interactive SSH/UI sessions never starve.
