# MCP Architecture, File-Editing Interfaces & Active Discovery Playbook

## 1. MCP Primitives & Transport Selection (Ch.4)

| Primitive / Layer | Role | Design Rule |
|---|---|---|
| `tools` (`tools/list`, `tools/call`) | Model-invoked actions & queries (`inputSchema` + optional `outputSchema`) | Paginate `tools/list`; keep `server_id` bound to `tool_name` to block tool shadowing |
| `resources` (URI-addressed) | Read-only data entrypoints (files, DB records, schemas) | Separate passive data reading from mutating execution tools |
| `prompts` | Reusable task/message templates | User- or client-selected workflow starters |
| `stdio` transport | Local subprocess JSON-RPC | Default for local CLI/IDE tools; isolate process env & credentials |
| `Streamable HTTP` | Remote HTTP POST returning JSON or streaming SSE | Standard remote transport (replaces legacy `HTTP+SSE`); negotiate protocol version (`server/discover` / `initialize`) |

## 2. Coding Agent Search & File-Editing Tool Trade-Offs (Ch.5)

- **Search stack:** Build deterministic `grep` (ripgrep regex + glob filter) + `glob` + ranged `read_file` (with 1-based line numbers) **before** adding semantic vector code indexing or LSP (`go-to-definition` / `find-references`). `grep` + `glob` require zero index-sync lag.
- **File-editing interface selection:**
  1. **`old_string -> new_string` exact replacement (Recommended default) or constrained `apply_patch`:** Deterministic, zero secondary Apply-LLM cost, auditable diff. Require unique match by default; return match count + line numbers on `0` or `>1` matches; run language syntax/linter check immediately on write and return structured diagnostics alongside write status.
  2. **`start_anchor + end_anchor -> new_string`:** Add only when deleting hundreds of lines bloats `old_string` output tokens; verify start precedes end and interval is unique.
  3. **Snapshot-bound line numbers:** Safe only if bound to a verified file hash/version so earlier edits or concurrent writes cannot shift line offsets.
  4. **Avoid stateful Vim/cursor keystroke tools:** Forces long-horizon models to simulate cursor state across dozens of micro-calls.

## 3. Active Tool Discovery Benchmarks & Ablation (Ch.4 Exp 4-1)

- **Scale numbers:** 58 MCP tools across 5 servers ≈ `55K` tokens; 127 MCP tools ≈ `50,597` `o200k` tokens.
- ** Savings & accuracy:** Cursor dynamic discovery cut MCP-task tokens by `46.9%`; MCP-Zero (2,797 tools / 308 servers) cut prompt overhead ~`98%`; Anthropic Tool Search (`defer_loading: true`) raised Opus 4 MCP accuracy from `49% -> 74%`; Qwen3-4B active discovery injected only `1,853–3,939` tokens per task vs `50,597` full-load.
- **Deconfounding selection errors (`selection_ablation.py`):** When tool selection fails at scale, run a two-arm single-step ablation at equal token length (e.g., `6,144` tokens):
  - *Arm A:* Core candidate tools + neutral text padding.
  - *Arm B:* Core candidate tools + near-duplicate distractor tools.
  If Arm A passes and Arm B fails, the bottleneck is **sibling tool confusion** (merge tools / sharpen boundary descriptions), not context length.
