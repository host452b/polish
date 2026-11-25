# Cross-Agent Session Storage Locations & Parsing Pitfalls

Observed local session formats across **Cursor, Windsurf, Claude Code, GitHub Copilot, Codex, Kiro, OpenCode, Zed, and Devin CLI** on **macOS, Linux, and Windows** (plus **WSL <-> Windows** cross-mounting).

> **Safety & Privacy Invariants (Mandatory for Every Reader):**
> 1. **Read-only SQLite only:** Always open databases via URI `file:<path>?mode=ro` (`sqlite3 -readonly "file:...?mode=ro"` or Python `sqlite3.connect("file:...?mode=ro", uri=True)`). Check file existence *before* invoking `sqlite3` so a missing path never creates an empty DB. If a running IDE holds an exclusive/WAL lock on Windows or network storage, copy `<db>`, `<db>-wal`, and `<db>-shm` to a temp dir first.
> 2. **Never touch auth/credential tables:** Skip `ItemTable` auth keys (`cursorAuth/*`, `windsurfAuthStatus`, OAuth tokens) and redact API keys/tokens (`sk-*`, `ghp_*`, `Bearer ...`) before injecting snippets into context.
> 3. **Never dump raw `tool_result` bodies:** Tool outputs (`cat`, test logs, full file snapshots) make up ~90% of transcript bytes. Extract file paths and command exit codes/tails; verify current file contents from disk.

---

## 1. Claude Code (`claude`)

### Storage Paths
- **macOS / Linux:** `${CLAUDE_CONFIG_DIR:-~/.claude}/${CLAUDE_CODE_PROJECT_DIR_NAME:-projects}/<project-slug>/<session-id>.jsonl`
- **Windows:** `%USERPROFILE%\.claude\projects\<project-slug>\<session-id>.jsonl` (or `%CLAUDE_CONFIG_DIR%`)
- **Additional roots:** `<claude-root>/transcripts/*.jsonl` (headless/SDK); on macOS Xcode: `~/Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig/projects/<slug>/*.jsonl`
- **Subagents:** `<claude-root>/projects/<slug>/<session-id>/subagents/agent-<agent-id>.jsonl`

### Schema & Pitfalls
- **Lossy project slug:** Non-alphanumeric characters (`/`, `-`, `_`, `.`) all map to `-` (and slugs >200 chars are hash-truncated). Never invert `<project-slug>` to guess `cwd`; read `.cwd` from the JSONL records themselves.
- **`isMeta: true` & command tag soup:** Claude Code writes loaded skills, cron prompts, `/fork` notices, and `<local-command-caveat>` / `<command-name>/model` wrappers as `type: "user"` lines. Drop `isMeta == true`, drop records carrying `toolUseResult`, and strip `<command-name>`, `<local-command-stdout>`, and `<system-reminder>` before picking the session's Goal.
- **Subagent `sessionId` collision:** Inside `subagents/agent-<agentId>.jsonl`, `.sessionId` repeats the **parent** session ID. Key sidechains by `.agentId` (or filename stem), never `.sessionId`.
- **30-day auto-purge:** CLI transcripts default to `cleanupPeriodDays: 30` in `settings.json`; `history.jsonl` persists longer but holds user prompts only.

---

## 2. OpenAI Codex CLI / Desktop (`codex`)

### Storage Paths
- **macOS / Linux:** `${CODEX_HOME:-~/.codex}/sessions/YYYY/MM/DD/rollout-<ts>-<uuid>.jsonl` (and `.jsonl.zst`), plus `archived_sessions/rollout-*.jsonl*`
- **Windows:** `%USERPROFILE%\.codex\sessions\YYYY\MM\DD\rollout-<ts>-<uuid>.jsonl[.zst]` (or `%CODEX_HOME%`)
- **Metadata SQLite cache:** `${CODEX_SQLITE_HOME:-$CODEX_HOME}/state_5.sqlite` (`threads` table)
- **macOS Xcode store:** `~/Library/Developer/Xcode/CodingAssistant/codex/sessions/...`

### Schema & Pitfalls
- **`.jsonl.zst` background compression & dual files:** Codex compresses rollouts older than ~7 days to `.jsonl.zst` and materializes plain `.jsonl` again if resumed. Deduplicate by the trailing UUID in the filename, keeping the file with the newest `mtime`, and decompress `.zst` via `zstd -dc`, Python `zstandard`, or Python 3.14+ `compression.zstd`.
- **Forked rollout `session_meta` trap:** A forked rollout emits its own `session_meta` first and then repeats its parent's `session_meta`. **Keep only the first `session_meta`** or `cwd` and `id` will be overwritten by the parent's.
- **Injected `AGENTS.md` boilerplate:** Codex injects `# AGENTS.md instructions...` and `<environment_context>...</environment_context>` as `role: "user"` messages. Strip whole `<tag>...</tag>` envelopes and `# AGENTS.md instructions` blocks so they don't mask the real user prompt.
- **Two turn & edit generations:** Current paginated rollouts emit `response_item` (`role`, `content`, `custom_tool_call` `apply_patch`, `function_call` `exec_command`/`shell_command`) plus `event_msg` (`item_completed` with `FileChange` / `UserMessage` / `AgentMessage`). Prefer `response_item` turns when present; fall back to `event_msg` only on legacy rollouts to avoid double-counting turns.
- **UUIDv7 prefix collisions & stale `history.jsonl`:** Use at least 13 characters (not 8) when matching Codex session ID prefixes (`state_5.sqlite`). Check `history.jsonl` `mtime` before trusting it—`codex exec` never appends to it.

---

## 3. Cursor IDE & Cursor Agent CLI (`cursor`)

### Storage Paths
- **Agent / CLI root:** `${CURSOR_CONFIG_DIR:-~/.cursor}` (`%USERPROFILE%\.cursor` on Windows; Linux also honours `~/.config/cursor` when lowercase `cursor` exists—beware case-insensitive APFS/NTFS aliasing `~/.config/Cursor`!):
  - Plaintext transcripts: `<cli-root>/projects/<slug>/agent-transcripts/<id>/<id>.jsonl` (or flat `<id>.jsonl`), subagents in `subagents/*.jsonl`
  - CLI chat store + real `cwd`: `<cli-root>/chats/<md5-of-cwd>/<chat-uuid>/meta.json` & `store.db`
- **IDE User root:**
  - **macOS:** `~/Library/Application Support/Cursor/User`
  - **Linux:** `${XDG_CONFIG_HOME:-~/.config}/Cursor/User`
  - **Windows:** `%APPDATA%\Cursor\User`
  - **Primary DB (Cursor 3.0+):** `<User>/globalStorage/state.vscdb` (can exceed 1 GB); optional FTS5 index `<User>/globalStorage/conversation-search.db`
  - **Legacy DB (pre-3.0):** `<User>/workspaceStorage/<hash>/state.vscdb` + sibling `workspace.json`

### Schema & Pitfalls
- **Plaintext `agent-transcripts` have NO `cwd` and NO JSON timestamp field:** User text wraps timestamps in `<timestamp>...</timestamp>` and prompts in `<user_query>...</user_query>`. `<slug>` maps `/`, `-`, `_`, `.` identically to `-` and is **irreversible**—resolve true `cwd` via `~/.cursor/chats/<md5>/<id>/meta.json` (`cwd` field) or IDE `composerHeaders`.
- **Orphan bubbles in `state.vscdb`:** `cursorDiskKV` holds `composerData:<cid>` and `bubbleId:<cid>:<bid>`. Regenerated/deleted turns leave orphan `bubbleId:*` rows behind. **Always walk `composerData.fullConversationHeadersOnly[]` in array order** (`type: 1` = user, `2` = assistant) and fetch bubbles via primary-key range `key >= 'bubbleId:<cid>:' AND key < 'bubbleId:<cid>;'`.
- **Workspace attribution in `state.vscdb`:** `composerData.workspaceIdentifier` is almost always empty; read `composerHeaders` (`json_extract(value, '$.workspaceIdentifier.uri.fsPath')`) first, falling back to the first bubble carrying `workspaceProjectDir`.

---

## 4. Windsurf / Devin Desktop Cascade (`windsurf`)

### Storage Paths
- **macOS / Linux:** `~/.codeium/windsurf/cascade/<cascade-id>.pb` (also `windsurf-next` / `windsurf-insiders`; override `DEJA_WINDSURF_ROOT`)
- **Windows:** `%USERPROFILE%\.codeium\windsurf\cascade\<cascade-id>.pb`
- **Hook transcripts (optional):** `~/.windsurf/transcripts/<trajectory-id>.jsonl` (`%USERPROFILE%\.windsurf\transcripts\`)

### Schema & Pitfalls
- **`grep` finds nothing; `state.vscdb` holds no Cascade text:** Windsurf (and renamed Devin Desktop 3.5+) seals each Cascade conversation as `nonce(12) || ciphertext || tag(16)` using **AES-256-GCM** (empty AAD, 32-byte language-server constant key `safeCodeiumworldKeYsecretBalloon`). Always authenticate the 16-byte GCM tag before decoding.
- **Inner `CortexTrajectory` Protobuf wire fields:**
  - `CortexTrajectory`: `1` `trajectory_id`, `2` `steps` (repeated), `6` `cascade_id`, `7` `metadata`, `10` `renamed_title`
  - `CortexTrajectoryMetadata` (`7`): `1` `workspaces` -> `1` `workspace_folder_absolute_uri`, `2` `git_root_absolute_uri` (`file://` URIs); `2` `created_at`
  - `CortexTrajectoryStep` (`2`): `5` `metadata` (`1` `created_at`, `8` `completed_at`), `19` `user_input` (`2` `user_response` preferred over `1` `query`), `20` `planner_response` (`1` `response` preferred over `8` `modified_response`)
- Use `scripts/takeover_session.py` (which includes a zero-dependency NIST AES-256-GCM + protobuf wire reader) or `deja --harness windsurf`.

---

## 5. GitHub Copilot CLI & VS Code Copilot Chat (`copilot`)

### Storage Paths
- **Copilot CLI:** `${COPILOT_HOME:-~/.copilot}/session-state/<dir>/events.jsonl` (`%USERPROFILE%\.copilot\session-state\<dir>\events.jsonl` on Windows; honours `XDG_STATE_HOME/.copilot` when set)
- **VS Code Copilot Chat (`Code`, `Code - Insiders`, `VSCodium`):**
  - **macOS:** `~/Library/Application Support/<Editor>/User/workspaceStorage/<hash>/`
  - **Linux:** `${XDG_CONFIG_HOME:-~/.config}/<Editor>/User/workspaceStorage/<hash>/` (plus `~/.vscode-server/data/User/workspaceStorage/<hash>/`)
  - **Windows:** `%APPDATA%\<Editor>\User\workspaceStorage\<hash>\`
  - **Two stores under `<hash>/`:** `chatSessions/*.jsonl` (or older `*.json`) AND `GitHub.copilot-chat/transcripts/*.jsonl` (newer extensions/VS Code Server write *only* the second!). Sibling `workspace.json` maps `<hash>` -> `{"folder": "file:///..."}`.

### Schema & Pitfalls
- **`chatSessions/*.jsonl` is a state mutation log, NOT one turn per line:** Records carry `kind: 0` (initial snapshot `v`), `kind: 1` (set path `k` to `v`), `kind: 2` (push/extend array at `k`), `kind: 3` (delete at `k`). Tail-reading the last 20 lines fails completely—reduce the file from line 1.
- **Copilot CLI `events.jsonl` quirks:** `session.start` carries `sessionId` and `context.cwd` (directory name can differ from `sessionId`). Tool names are lowercase (`edit`, `create`, `bash`, `apply_patch`), and `tool.execution_complete` sets `success: true` even when a shell command exits non-zero.
- **Cloud-only sessions:** GitHub Actions / cloud sandbox sessions exist only on GitHub.com unless synced locally.

---

## 6. Kiro CLI & Kiro IDE (`kiro`)

### Storage Paths
- **Kiro CLI (v2):** `~/.kiro/sessions/cli/<id>.jsonl` + sibling header `<id>.json` (`%USERPROFILE%\.kiro\...` on Windows)
- **Kiro IDE & `kiro-cli --v3`:** `~/.kiro/sessions/<workspace>/sess_<uuid>/messages.jsonl` + `session.json`
- **Kiro IDE `globalStorage`:**
  - **macOS:** `~/Library/Application Support/Kiro/User/globalStorage/kiro.kiroagent/workspace-sessions/<base64url>/<uuid>.json` (+ `sessions.json`)
  - **Linux:** `${XDG_CONFIG_HOME:-~/.config}/Kiro/User/globalStorage/kiro.kiroagent/workspace-sessions/...`
  - **Windows:** `%APPDATA%\Kiro\User\globalStorage\kiro.kiroagent\workspace-sessions\...`
- **Headless `kiro-cli --no-interactive`:** `kiro-cli/data.sqlite3` under `~/Library/Application Support` (macOS), `${XDG_DATA_HOME:-~/.local/share}` (Linux), or `%LOCALAPPDATA%` (Windows), table `conversations_v2`.

### Schema & Pitfalls
- **`state.vscdb` is a decoy:** Kiro IDE's `state.vscdb` chat keys are empty stubs (`{"version":1,"entries":{}}`). Read `~/.kiro/sessions/` and `kiro.kiroagent/workspace-sessions/`.
- **Streaming `AssistantMessage` fragments:** In `sessions/cli/*.jsonl`, Kiro appends one `AssistantMessage` record *per streamed chunk* under the same `data.message_id`. Join consecutive records sharing `message_id` or replies truncate to sentence fragments.
- **`__` base64url padding:** `workspace-sessions/<encoded-dir>` encodes the workspace path in URL-safe base64 with `=` replaced by `_` (`==` -> `__`).
- **Bookkeeping & encrypted reasoning:** In `sess_<uuid>/messages.jsonl`, skip `operationType == "Reasoning"` (content is `"..."` with encrypted `reasoningSignature`) and skip `session_metadata` / `usage_summary` / `turn_end`.

---

## 7. OpenCode (`opencode`)

### Storage Paths
- **macOS / Linux:** `${XDG_DATA_HOME:-~/.local/share}/opencode/opencode.db` (override `OPENCODE_DB`)
- **Windows:** `%LOCALAPPDATA%\opencode\opencode.db` or `%USERPROFILE%\.local\share\opencode\opencode.db`
- **1.x diff sidecars:** `<opencode-dir>/storage/session_diff/ses_<id>.json`

### Schema & Pitfalls
- **Fast CLI path vs cross-project caveat:** When `opencode` is installed, `opencode export <id> --pure` outputs clean JSON (`--pure` prevents firing user plugins/hooks), *but* `opencode session list --format json --pure` only lists sessions for the **current working directory**. Query `opencode.db` directly for cross-project discovery.
- **1.x and 2.0 tables coexist after upgrade:** OpenCode 2.0 uses `session_v2` + `session_message(session_id, type, seq, data)`. Upgraded stores retain 1.x `session` + `message` + `part` for unmigrated sessions. Prefer `session_message` when rows exist for that `session_id`; otherwise read `message` + `part`.
- **Migration timestamp trap:** On migrated 1.x rows, the SQLite `time_created` column holds the *migration run time*, not when the message was sent. Read `data.time.created` / `part.data.time.start` inside the JSON payload.
- **Missing edit records in 1.x DB:** Many 1.x sessions record edited files *only* in `storage/session_diff/ses_<id>.json` (`[{file, status, patch}]`). Fold those paths in.

---

## 8. Zed Editor (`zed`)

### Storage Paths
- **macOS:** `~/Library/Application Support/Zed/threads/threads.db` (legacy Text Threads: `~/Library/Application Support/Zed/conversations/*.zed.json`)
- **Linux:** `${FLATPAK_XDG_DATA_HOME:-${XDG_DATA_HOME:-~/.local/share}}/zed/threads/threads.db` (Flatpak default: `~/.var/app/dev.zed.Zed/data/zed/threads/threads.db`)
- **Windows:** `%LOCALAPPDATA%\Zed\threads\threads.db`

### Schema & Pitfalls
- **Wrong directory trap (`~/.config/zed` has NO threads):** `~/.config/zed` (`%APPDATA%\Zed` on Windows) holds only `settings.json` and keymaps. Threads live in the **data** directory (`%LOCALAPPDATA%\Zed` on Windows, `Application Support/Zed` on macOS, `~/.local/share/zed` on Linux).
- **`zstd`-compressed SQLite BLOBs:** In `threads(id, summary, updated_at, data_type, data, ...)`, modern rows have `data_type = 'zstd'` and `data` is a zstd-compressed JSON `SerializedThread` (legacy rows have `data_type = 'json'`). Plain `sqlite3` without `zstd` decompression yields binary bytes. Also check `PRAGMA table_info(threads)`—older DBs only have the first 5 columns (no `folder_paths`).
- **Two JSON thread generations & result-side edits:** v0.3.0 uses externally tagged `{"User": {"content": [{"Text": "..."}]}}` and `{"Agent": {"content": [...], "tool_results": {...}}}`; v0.2.0 uses `{"role": "user", "segments": [{"type": "text", "text": "..."}]}`. Crucially, `edit_file` / `write_file` store the target file path and unified `diff` inside `Agent.tool_results[*].output.input_path`, often leaving call inputs minimal.
- **ACP external agents:** When Zed hosts an external ACP agent (e.g. `devin acp`, Claude Code ACP), canonical transcripts also live in that external agent's own store.

---

## 9. Devin CLI (`devin`)

### Storage Paths
- **macOS / Linux:** `${XDG_DATA_HOME:-~/.local/share}/devin/cli/sessions.db` (pre-rename fallback `cli_sessions.db`)
- **Windows:** `%APPDATA%\devin\cli\sessions.db` (`%LOCALAPPDATA%\devin\cli` holds only binaries)

### Schema & Pitfalls
- **`message_nodes` is a DAG of rebuilt chains, NOT a flat log:** Whenever the system prefix changes or context compacts, Devin writes a new chain of `message_nodes` reusing earlier `message_id`s. Start at `sessions.main_chain_id`, walk backwards via `parent_node_id`, reverse to chronological order, and **deduplicate by `message_id`**—otherwise user turns appear 2x–5x.
- **Filter hidden & system-prefix rows:** Skip `sessions.hidden = 1` (deleted via `/rm-session`) and skip nodes whose `metadata` JSON sets `"is_system_prefix": true`. Read `exec` exit codes from `chat_message.metadata.extensions."chisel/terminal_output".exit.exit_code`.

---

## Minimal Fallback One-Liners (When Python Is Unavailable)

```bash
# Claude Code — list newest transcripts in a project dir
ls -t "${CLAUDE_CONFIG_DIR:-$HOME/.claude}"/projects/*/*.jsonl | head -n 10

# Codex — inspect first line (session_meta) of plain or .zst rollout
zstd -dc --force rollout.jsonl.zst | head -n 1 | jq '{id: .payload.id, cwd: .payload.cwd}'

# Cursor IDE — list recent non-empty composers (read-only URI!)
sqlite3 -readonly -separator ' | ' "file:$HOME/Library/Application Support/Cursor/User/globalStorage/state.vscdb?mode=ro" \
  "SELECT datetime(json_extract(value,'$.lastUpdatedAt')/1000,'unixepoch','localtime'), substr(key,14,12), json_extract(value,'$.name') FROM cursorDiskKV WHERE key LIKE 'composerData:%' AND json_array_length(value,'$.fullConversationHeadersOnly')>0 ORDER BY json_extract(value,'$.lastUpdatedAt') DESC LIMIT 15;"

# Zed — extract & decompress one thread JSON from threads.db
sqlite3 -readonly "file:$HOME/Library/Application Support/Zed/threads/threads.db?mode=ro" \
  "SELECT writefile('/tmp/zed_thread.zst', data) FROM threads WHERE id='<thread-id>';" && zstd -dc /tmp/zed_thread.zst | jq . && rm -f /tmp/zed_thread.zst
```

## References & Format Provenance

Storage paths, schema invariants, and format-drift notes are synthesized and cross-verified against:
- [`jlreyes/agent-history-skills`](https://github.com/jlreyes/agent-history-skills) (MIT) — Claude Code, Codex CLI, and Cursor read-only exploration patterns.
- [`vshulcz/deja-vu`](https://github.com/vshulcz/deja-vu) & its [Session Format Registry](https://vshulcz.github.io/deja-vu/registry/README.html) (MIT) — observed multi-OS format specifications across Claude Code, Codex, Cursor, Windsurf (`CortexTrajectory`), Copilot CLI/Chat, Kiro, OpenCode, Zed, and Devin CLI.
