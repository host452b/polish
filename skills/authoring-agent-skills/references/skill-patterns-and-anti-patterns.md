# Skill Patterns, Iterative Extraction, and Anti-Patterns

## 1. Writing High-Signal `description` Pointers

`description` is an always-loaded context pointer. Its job is routing, not teaching.

```yaml
# BAD: Summarizes workflow -> agent follows description and skips SKILL.md
description: Use when building RAG — chunk docs at 512 tokens, run BM25 + dense retrieval, fuse with RRF, then rerank top 50.

# BAD: Vague catchall -> fires on every backend prompt
description: Helps with backend APIs and testing.

# GOOD: Concrete triggers, symptoms, and near-miss boundary
description: Use when building or tuning RAG retrieval pipelines, diagnosing low recall@k or MRR, or choosing between dense, BM25, hybrid RRF, and cross-encoder reranking. Skip for pure single-file in-context QA.
```

## 2. Iterative "Before/After Diff" Authoring Loop (Ch.2 Exp 2-7 & Ch.9)

When distilling tacit human expertise (writing style, code review taste, spec clarification) into a skill:
1. Collect 3–5 gold examples and draft a minimal 20-line v0 `SKILL.md` (Role & Audience + 3–5 Core Principles with Before/After pairs).
2. Run the skill on a fresh task; have the domain owner edit the output line-by-line.
3. Diff `agent_draft` vs `human_final`. Group recurring edits into **Scope + Action + Exception + Verification** rules.
4. Calibrate trigger thresholds from feedback:
   - User says *"Not what I meant"* -> widen clarification/verification gate for high-ambiguity tasks.
   - User says *"Too many questions"* -> narrow clarification gate so low-risk reversible edits execute directly with stated assumptions.

## 3. Matching Guidance Form to Failure Type

| Observed Agent Failure | Effective Form | Counterproductive Form |
|---|---|---|
| Violates a known discipline rule under time/sunk-cost pressure | Explicit ban + "No exceptions" list + Rationalization table | Polite advice (`Prefer testing first`) |
| Produces bloated or mis-structured output | Positive template/contract specifying exact sections | Negation list (`Don't repeat the prompt`, `Never add fluff`) |
| Drops a required field (e.g., evidence citation, rollback step) | Explicit slot in output schema/template | Prose reminder in a paragraph |
| Over-applies a rule where an exception exists | Separate conditional keyed to observable state | Nuance suffix (`...unless unnecessary`) |

## 4. Disentangling Skill Update vs. Skill Benefit (Ch.9 Table 9-3)

Never rewrite a valid `SKILL.md` solely because end-to-end benchmark scores stayed flat. Diagnose which stage dropped:
1. **Proposal validity:** Does the rule actually fix the target failure when force-injected?
2. **Activation rate:** Did the agent discover and load the skill on target tasks? (If low -> fix `description` pointer.)
3. **Compliance rate:** After loading `SKILL.md`, did the agent execute every step? (If low -> sharpen completion criteria, disclose sprawl to `references/`, or extract a `scripts/` helper.)
4. **Holdout gain:** Did Boundary Set pass rate rise without Retention Set regression or token explosion?
