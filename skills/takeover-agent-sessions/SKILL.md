---
name: takeover-agent-sessions
description: "Use when picking up unfinished work, recovering context, or reading local session transcripts from another coding agent (Cursor, Windsurf, Claude Code, GitHub Copilot, Codex, Kiro, OpenCode, Zed, or Devin) across macOS, Windows, or Linux — including quota or rate-limit switches, mid-task IDE/CLI handoffs, post-crash or post-compaction recovery, and cross-agent history lookup (跨工具接力、读取其他 Agent 本地会话继续干活、额度耗尽切工具接盘)."
allowed-tools:
  - read
  - grep
  - glob
---

# takeover-agent-sessions

Read another coding agent's local session store on **macOS, Windows, or Linux (including WSL <-> Windows)**, compress it into a **5-part Takeover Brief**, reconcile it against live repository state (`git status` / `git diff` / files on disk), and finish the remaining work without redoing completed steps.

**Universal Agent-to-Agent Portability:** Any host agent (Devin, Claude Code, Codex, Cursor, Windsurf, Copilot, Kiro, OpenCode, Zed, or others) can run this skill to read sessions recorded by any other agent on the same machine.

**Core Law:** **Transcript = historical intent; live disk = ground truth.** Open foreign stores strictly read-only, redact secrets, and drop raw `tool_result` bodies so megabytes of old logs never pollute your context window.

## Workflow

### 1. Resolve `SKILL_DIR`, Permissions, and Reader Tier

- Set `SKILL_DIR` from the invoked skill's `Base directory` header, `${CLAUDE_PLUGIN_ROOT}/skills/takeover-agent-sessions`, or the directory containing this `SKILL.md` so commands work from any repository `cwd` (on Windows without `python3`, substitute `py -3` or `python`).
- **Host sandbox / scope check:** Local session stores live outside the project tree (`~/.*`, `~/Library/Application Support`, `%APPDATA%`, `%LOCALAPPDATA%`, `~/.local/share`). If the host sandbox blocks reading a store directory, request read-only scope for that path (e.g. `request_scope` with `scope: "read"`, or ask the user to grant read access). Never guess or fabricate transcript contents when a path is unreadable.
- **Pick the fastest read-only tier available:**
  1. **Native / installed indexer:** If `deja` (`vshulcz/deja-vu`) is on `PATH`, `deja handoff` or `deja last --harness <name>` gives instant indexed recall; for OpenCode in the current `cwd`, `opencode export <id> --pure` (`--pure` skips user plugins/hooks) is also safe.
  2. **Bundled cross-platform extractor (default):** Run `"$SKILL_DIR/scripts/takeover_session.py"` (zero pip dependencies; supports `claude`, `codex`, `cursor`, `windsurf`, `copilot`, `kiro`, `opencode`, `zed`, `devin`, and `all`).
  3. **Direct CLI / SQLite fallback:** When Python is unavailable or inspecting an unfamiliar version, consult [`references/storage-and-pitfalls.md`](references/storage-and-pitfalls.md) for per-OS paths, schemas, and `sqlite3 "file:...?mode=ro"` / `jq` / `zstd -dc` recipes.
- *Completion criterion:* Reader tier selected and target store directory readable (or read permission requested).

### 2. Locate the Target Session (Filter First, Exclude Self)

List or search metadata before reading any full session. Pass `--exclude-harness <your-own-harness>` (or `--exclude-session <current-id>`) when scanning `--harness all` so you never "take over" your own active turn:

```bash
# Check which agent stores exist on this machine (macOS / Linux / Windows / WSL)
python3 "$SKILL_DIR/scripts/takeover_session.py" discover

# List recent sessions for the current workspace (newest first)
python3 "$SKILL_DIR/scripts/takeover_session.py" list --cwd "$PWD" --harness all --limit 10

# Or search across harnesses by keyword / touched file / error message
python3 "$SKILL_DIR/scripts/takeover_session.py" search "webhook retry" --harness cursor,claude,codex
```

- If `--cwd "$PWD"` returns nothing (common for Cursor `agent-transcripts` without a CLI `meta.json`, or sessions started from a parent monorepo root / git worktree), re-run `list` without `--cwd` and match by title/prompt/files.
- If **one** session clearly matches the user's request, proceed directly; if **2+ plausible sessions** compete (e.g. IDE chat vs CLI rollout, or two branches), show the top 3–5 candidates (`[harness] id | updated_at | cwd | title`) and ask the user which one to pick up.
- *Completion criterion:* Exact `harness` + `session_id` identified.

### 3. Extract a Bounded 5-Part Takeover Brief

Generate the structured brief instead of dumping the raw JSONL/SQLite file:

```bash
python3 "$SKILL_DIR/scripts/takeover_session.py" brief \
  --harness <harness> \
  --session <session-id-or-prefix> \
  --turns 6
```

Ensure all five signal blocks are accounted for (reading `--turns 12` only if the stopping point was compacted or spanned a long debugging loop):
1. **Goal:** Cleaned initial user prompt (wrappers and `AGENTS.md` injections stripped).
2. **Settled Constraints & Follow-Ups:** User corrections, chosen design options, and rejected approaches.
3. **Files Touched:** Paths edited/created/patched across main turns and subagent sidechains.
4. **Executed Commands & Exit Codes:** Test/build commands run and their failure tails.
5. **Stopping Point:** The final user/assistant turns showing why the previous agent stopped (rate limit, crash, context limit, failing test, or open TODO).

- *Completion criterion:* 5-part Takeover Brief extracted with secrets redacted and zero raw `tool_result` dumps.

### 4. Reconcile Transcript Intent Against Live Workspace Reality

**Never trust a transcript's claim that a file was saved or a test passed without checking disk.** Run read-only repo checks in parallel:

```bash
git status --short --branch
git diff --stat
git log -n 5 --oneline
```

Inspect the actual files listed under **Files Touched** and classify every task item into three buckets:
- **Verified Done on Disk:** Present in commits or working tree and consistent with the goal.
- **Half-Done / Drifted:** Interrupted mid-edit, reverted, modified manually after the session ended, or sitting on a different branch/worktree — **live disk state wins**.
- **Remaining Work:** Unimplemented steps, unverified edits, or failing tests from the stopping point.

- *Completion criterion:* Every touched file and claimed milestone reconciled against live git/filesystem state.

### 5. Present Takeover Check-In & Finish the Job

Report a concise **Takeover Summary** before making edits:
- **Picked Up From:** `[harness] session_id` (`updated_at`, recorded branch/cwd)
- **Done on Disk:** Verified completed changes
- **Drift / Attention Needed:** Any mismatch between transcript claims and current `git status` / branch
- **Next Actions:** Concrete remaining steps

If the user asked only to *inspect/summarize* the session, stop after the summary. If the user asked to *continue/take over* the work and there is no destructive conflict or wrong-branch hazard, proceed immediately to execute the remaining steps. Pause for confirmation only when uncommitted changes conflict, files were partially clobbered, or the checkout is on an unexpected branch.

---

## 9-Harness Storage & Fatal Pitfall Matrix

Full per-OS paths (`macos` / `linux` / `windows` / `WSL`), schemas, and raw CLI recipes live in [`references/storage-and-pitfalls.md`](references/storage-and-pitfalls.md).

| Harness | Primary Local Store (macOS / Linux / Windows) | #1 Parsing Pitfall Handled by `takeover_session.py` |
| --- | --- | --- |
| **`claude`** | `~/.claude/projects/<slug>/<id>.jsonl` (`%USERPROFILE%\.claude\...`) | Skip `isMeta: true` & `toolUseResult`; strip `<command-name>` / `<system-reminder>`; key `subagents/` by `agentId` (not parent `sessionId`). |
| **`codex`** | `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl[.zst]` | Decompress `.jsonl.zst`; keep **only first** `session_meta` on forked rollouts; strip `# AGENTS.md instructions` user boilerplate. |
| **`cursor`** | `~/.cursor/projects/<slug>/agent-transcripts/` + `<AppSupport\|AppData\|.config>/Cursor/User/globalStorage/state.vscdb` | Walk `composerData.fullConversationHeadersOnly[]` (skip orphan `bubbleId:*` rows); `<slug>` is lossy — read `chats/<md5>/<id>/meta.json` or `composerHeaders` for `cwd`. |
| **`windsurf`** | `~/.codeium/windsurf/cascade/<id>.pb` (`%USERPROFILE%\.codeium\...`) | `state.vscdb` has no chat bodies; `.pb` is AES-256-GCM sealed `CortexTrajectory` protobuf (`grep` finds nothing). |
| **`copilot`** | `~/.copilot/session-state/*/events.jsonl` + `<VSCode>/User/workspaceStorage/<hash>/{chatSessions,GitHub.copilot-chat/transcripts}` | `chatSessions/*.jsonl` is a `kind: 0/1/2/3` delta mutation log (must reduce from line 1, never `tail`); newer extensions write `GitHub.copilot-chat/transcripts/`. |
| **`kiro`** | `~/.kiro/sessions/{cli,*/sess_*}` + `<Kiro>/User/globalStorage/kiro.kiroagent/workspace-sessions/<base64>/*.json` + `kiro-cli/data.sqlite3` | Join streaming `AssistantMessage` chunks sharing `message_id`; `state.vscdb` chat keys are empty stubs; decode `__` -> `==` in base64 workspace dirs. |
| **`opencode`** | `~/.local/share/opencode/opencode.db` (`%LOCALAPPDATA%\opencode\opencode.db`) + `storage/session_diff/` | Upgraded DBs hold both 2.0 (`session_v2`+`session_message`) and 1.x (`session`+`message`+`part`); migration overwrites `time_created` column (use `data.time.created`). |
| **`zed`** | `~/Library/Application Support/Zed/threads/threads.db` (`~/.local/share/zed` / `%LOCALAPPDATA%\Zed`) | Threads live in **data** dir (never `~/.config/zed`); `data` BLOB is `zstd`-compressed JSON; edits sit on `Agent.tool_results[*].output.input_path`. |
| **`devin`** | `~/.local/share/devin/cli/sessions.db` (`%APPDATA%\devin\cli\sessions.db`) | Walk `message_nodes` backwards from `sessions.main_chain_id` via `parent_node_id` and **dedupe by `message_id`** across rebuilt context chains; skip `hidden = 1`. |

## Common Mistakes to Avoid

| Mistake | Required Behavior |
| --- | --- |
| Opening a running IDE's SQLite DB in read-write mode | Always use `file:...?mode=ro` (or snapshot `.db` + `-wal` + `-shm` to temp dir) so WAL locks never corrupt or block the live editor. |
| Feeding raw `.jsonl` files directly into LLM context | Always extract the bounded 5-part Takeover Brief (`takeover_session.py brief`); raw `tool_result` and `thinking` blocks blow out context. |
| Inverting Claude or Cursor `<project-slug>` (`-Users-foo-my-app`) into `/Users/foo/my/app` | Slugs map `/` and `-` identically; read `.cwd`, `chats/<md5>/<id>/meta.json`, `workspace.json`, or `composerHeaders` instead. |
| Looking in `~/.config/zed` (`%APPDATA%\Zed`) or Windsurf/Kiro `state.vscdb` | Zed stores `threads.db` in its data dir; Windsurf stores encrypted `.pb` under `~/.codeium/windsurf/cascade/`; Kiro stores JSON under `~/.kiro` & `kiro.kiroagent`. |
| Using `--resume` on another CLI without `--pure` / read-only flags just to inspect history | Never spawn an interactive foreign agent session or trigger its lifecycle hooks merely to read its transcript. |
| Assuming transcript edits match disk | Always cross-check `git status` and `git diff` before writing a single line of code. |
