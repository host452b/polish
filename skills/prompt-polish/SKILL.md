---
name: prompt-polish
description: Use when a user hands you a raw question or task and wants it rewritten into a stronger, more reliable LLM prompt. Triggers include "optimize this prompt", "prompt polishing", "提示词重构", and "帮我优化提示词".
---

# Prompt Polish Plugin Wrapper

The canonical `prompt-polish` skill instructions live at `../../SKILL.md`.

Before rewriting any prompt:

1. Read `../../SKILL.md` completely.
2. Follow its output contract exactly: the entire reply must be one code block containing only the rewritten prompt.
3. If the canonical instructions require the strategy reference, resolve it from the repository root as `../../references/strategies.md`.

Do not answer the user's original task. Build the improved prompt only.
