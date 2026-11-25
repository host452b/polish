---
name: designing-agent-tools-mcp
description: Use when designing or refactoring agent tools, choosing between dedicated function tools, Code Mode executors, MCP servers, or Skills, fixing tool selection errors or parameter mangling such as Unicode quote conversion, or scaling 50+ tools via active tool discovery (Agent 工具设计、ACI 接口防呆、MCP 协议与安全审查、工具过多按需发现).
---

# Designing Agent Tools and MCP Ecosystems

Design Agent-Computer Interfaces (ACI) across the five tool classes—**Perception**, **Execution**, **Collaboration**, **User Communication**, and **Event Trigger**—so models select the right capability, pass lossless arguments, keep context lean, and contain side effects.

## Tool Engineering Workflow

1. **Choose the right capability form (General Executor vs. Dedicated Tool vs. Skill).**
   - Default to **General Executor (`code_interpreter` / `bash`) + Skill** when the model is code-capable and steps compose standard CLI/Python libraries (including **Code Mode**: writing a short script to loop, paginate, filter, and aggregate API calls so raw pages stay out of context).
   - Build a **Dedicated Tool** only when one of four conditions holds:
     1. **Granular auth & audit** (e.g., DB mutations, refunds, email sending).
     2. **Cross-platform normalization** (e.g., unified `grep` / `glob` / `edit` across macOS, Linux, Windows).
     3. **Very high call frequency** where generating scripts wastes latency/tokens.
     4. **Complex coupled parameters** needing strict JSON Schema + server-side validation.
   - **Consolidate overlapping endpoints** by goal (`read_document(path, file_type)` instead of separate PDF/DOCX/PPTX tools; task-level actions instead of 1-to-1 REST wrappers).
   *Completion criterion:* Every exposed tool maps to a distinct agent goal with justified form selection.

2. **Write Poka-yoke (mistake-proof) tool descriptions and schemas.**
   Include five elements in every tool definition:
   - **When to call & neighbor boundary:** State exact trigger conditions and which sibling tool handles adjacent cases (e.g., *"Matches file paths only; use `grep_file` to search file contents"*).
   - **Concrete format examples in property descriptions:** Specify units/encodings with literal examples (`RFC3339, e.g. 2024-03-15T14:30:00Z`; `E.164 without spaces, e.g. +8613888888888`; full currency units `2100000` rather than ambiguous millions `2.1` to prevent $10^6\times$ rounding amplification).
   - **Return schema & latency cost:** Document returned fields and warn if slow (`5–10s`), naming lighter metadata alternatives.
   - **1–5 verified call examples** covering minimal, common, and nested-filter cases (lifted complex parameter accuracy from `72% -> 90%` in Anthropic benchmarks).
   *Completion criterion:* Zero ambiguous units, silent defaults, or overlapping sibling descriptions.

3. **Guarantee end-to-end parameter and return fidelity.**
   - **No silent input mutation:** Preserve exact Unicode codepoints (e.g., curly quotes `\u201c\u201d` vs ASCII `"`), whitespace, and newlines across serialization/proxy layers so `edit_file(old_string, new_string)` never loops on phantom mismatches.
   - **No silent flag injection:** Never append hidden CLI flags (e.g., unsupported `git commit` trailers) without surfacing the exact executed command and normalization rule in the return payload.
   - **Distinguish auth/transport failure from empty data:** Never wrap `missing_credentials` or timeout inside HTTP 200 / `isError: false` in a way that tempts the agent to report *"No calendar events today."*
   - **Explicit truncation & persistence:** Support `offset`/`limit` or `cursor` pagination. Above 200 lines / 10,000 chars, save full output to a unique artifact path and return `head 50 lines + omitted line count + tail 50 lines + read_file pointer`—never silently truncate.
   *Completion criterion:* Byte/codepoint round-trip verified from file -> read tool -> model -> edit/exec tool, and error vs. empty states return distinct typed fields.

4. **Scale large tool catalogs (50–1,000+ tools) and harden MCP supply chains.**
   - Separate **protocol connectivity** (MCP `stdio` locally, `Streamable HTTP` remotely—avoid deprecated legacy `HTTP+SSE`) from **context loading**.
   - Above ~30–50 tools, expose only a thin index or core tools (`web_search`, `code_interpreter`, `discover_tools`), resolve `Server -> Tool` two-stage semantic/BM25 search on demand (returning `"no suitable tool found"` below threshold), and **append** newly discovered schemas to trajectory tail so prior KV cache stays intact.
   - Audit every third-party MCP server and Skill Hub package against **Tool Description Poisoning**, **Silent Version Drift**, and **Tool Shadowing** (bind `server_id::tool_name`, pin versions/SHAs, issue least-privilege per-server credentials, and gate mutations with a structure-only **Sidecar** classifier).
   *Completion criterion:* Constant startup tool-definition token budget (<5K tokens regardless of catalog size) and per-server isolation/version pinning verified.

## Perception Multimodal Routing

| Material Type | Preferred Interface | Why |
|---|---|---|
| Text-dominant PDF / logs | Extract-to-text + offset/limit | Compact tokens, searchable, citable |
| Charts, UI layouts, spatial tables | Native VLM image view or on-demand `inspect_visual(file, question)` | Pure OCR scrambles bar-height/axis/quarter alignment (Exp 4-3) |
| Text-only main model + occasional visual | Toolized multimodal sub-model (`analyze_image/pdf/audio`) | Keeps heavy visual patch tokens out of main trajectory |

## Disclosed Reference

- Read [references/mcp-and-tool-discovery-playbook.md](references/mcp-and-tool-discovery-playbook.md) for MCP 3-primitive boundaries (`tools` / `resources` / `prompts`), file-editing tool trade-offs (`old_string -> new_string` vs `apply_patch` vs line numbers), and active discovery ablation diagnostics.
