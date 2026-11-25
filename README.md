# polish

> Personal collection of curated, self-made, and adapted agent skills.

**English** | [中文](#中文版)

`polish` is a Claude Code, Codex CLI, Cursor CLI, and Devin CLI skill/plugin collection for selected personal and adapted skills. The repo/plugin package is named `polish`; individual skill names stay stable so existing triggers and installs do not break.

Plugin version: **0.3.0**, shared by the Devin, Codex, Claude Code, and Cursor manifests.

Each skill uses one lowercase kebab-case name for its directory, `SKILL.md` frontmatter `name`, invocation identifier, and `agents/openai.yaml` `interface.display_name`. For example, `git-commit-message` is displayed as `git-commit-message` and invoked as `$git-commit-message` (or `/polish:git-commit-message` in Claude Code and Devin CLI).

Currently included:

- `benchmark-checklist` - checks measured throughput, latency, and speedup claims against completed work and run variability.
- `takeover-agent-sessions` - reads local session stores across Cursor, Windsurf, Claude Code, GitHub Copilot, Codex, Kiro, OpenCode, Zed, and Devin on macOS, Windows, and Linux into a bounded 5-part Takeover Brief, reconciles against live `git status` / `git diff`, and resumes unfinished work from any host agent.
- `analyzing-risk-decisions` - models uncertain options via joint state-wise net losses, CARA exponential utility ($CE_R$), and `VaR`/`ES` tail constraints, with deterministic threshold inversion ($p^*$, reservation price $P^*(R)$, indifference $R^*$) and preference calibration.
- `consistent-term-translation-polish-guard` - translates and polishes EN↔ZH content with stable primary terms, acronym bindings, ambiguity checks, and a bilingual terminology table.
- `yc-rejection-simulator` - critiques startup ideas, product loops, market assumptions, and non-code strategic decisions with evidence-grounded objections, a sharp verdict, and one validation test.
- `find-blind-spots` - surfaces unfamiliar domain/codebase idioms, unspoken engineering conventions, architectural assumptions, and post-launch verification gaps, with evidence and a minimal test.
- `prompt-polish` - turns a rough question into high-performing, ready-to-paste bilingual LLM prompts.
- `find-a-bug` - conducts exploratory, repo-reading defect audits using an evidence ledger, competing hypotheses, decision gates, and a 30s non-blocking regression-commit lookup.
- `project-bug-hunting` - explores unknown functional defects across C++, Python, and mixed projects by checking applicable contracts against source, installed artifacts, and runtime evidence.
- `file-singlify` - scans a disk/folder/mount for duplicate files and duplicate directory copies, then proposes a single-copy plan (canonical copy + duplicate-to-canonical mapping) with a read-only dry-run report.
- `before-git-push` - a final pre-push risk gate: reviews the real diff as a release engineer and returns a PUSH or HOLD verdict before code reaches production.
- `git-commit-message` - drafts and reviews commit messages using separate GitLab and GitHub conventions, with repository rules taking precedence.
- `i-have-adhd-actionable-output` - makes answers and handoffs easier to act on while preserving completeness, evidence, and agent autonomy.
- `google-stitch-frontend-taste-design` - establishes or reviews evidence-backed frontend visual direction without generic AI styling or fabricated product content.
- `google-stitch-extract-frontend-design-system` - extracts a portable `DESIGN.md` from frontend source even when the app cannot build or run.
- `google-stitch-frontend-brief-enhancer` - turns vague UI requests into bounded, implementation-ready briefs with explicit assumptions and acceptance criteria.
- `google-stitch-shadcn-ui` - implements or reviews coherent, accessible, responsive shadcn/ui interfaces using the project's real tokens and primitives.
- `superpowers-using-git-worktrees` - creates or reuses an isolated workspace before feature work or plan execution.
- `superpowers-brainstorming` - refines an idea step by step into an approved written design spec and implementation plan before coding begins.
- `superpowers-test-driven-development` - enforces the red-green-refactor cycle (plus pre-agreed seams and vertical slicing) for feature and bug-fix work.
- `superpowers-systematic-debugging` - investigates surfaced bugs from logs, stack traces, or issue symptoms before proposing fixes, with a 30s non-blocking regression-commit lookup.
- `superpowers-verification-before-completion` - requires fresh evidence before success claims.
- `superpowers-writing-skills` - TDD-verifies and pressure-tests `SKILL.md` files against rationalizations using subagent scenarios.
- `mattpocock-domain-modeling` - builds and sharpens a project's domain model, `GLOSSARY.md`, and ADRs.
- `mattpocock-codebase-design` - provides shared deep-module vocabulary (`module`, `interface`, `depth`, `seam`, `adapter`) and deepening / design-it-twice guides.
- `mattpocock-grilling` - stress-tests a plan, decision, or rough idea in frontier-based rounds of design-tree questions, with optional handoff to spec planning.
- `mattpocock-prototype` - builds throwaway logic or UI prototypes to answer concrete design questions fast.
- `mattpocock-research` - delegates primary-source research to a background agent and captures cited Markdown notes in the repo.
- `mattpocock-code-review` - reviews changes since a fixed point in parallel along two separate axes: Standards and Spec.
- `mattpocock-wizard` - generates an interactive bash wizard for manual setup, credential, or migration steps only a human can perform.
- `mattpocock-writing-for-agents` - reference for structuring, sharpening, and pruning agent-consumed documents (`SKILL.md`, `AGENTS.md`, `CLAUDE.md`).

## Portfolio Orthogonality & Routing

| Metric | Value | Notes |
| --- | --- | --- |
| Total skills | **31** | Total `description` footprint: **8,956 chars** (avg **289 chars/skill**), keeping always-loaded context overhead compact |
| Functional orthogonality | **~86%** (~14% overlap) | Adjacent skills differ in method and artifact rather than duplicating workflows |
| Trigger orthogonality | **~88%** (~12% overlap; raised from ~68%) | Formerly overlapping clusters carry explicit mutual-routing pointers in `description` |
| Standalone single-purpose skills | **11 / 31 (35.5%)** | Zero domain or trigger overlap (`prompt-polish`, `file-singlify`, `takeover-agent-sessions`, `benchmark-checklist`, `mattpocock-wizard`, etc.) |
| Pipeline & complementary cluster skills | **20 / 31 (64.5%)** | Stage-separated across UI (5), modeling/design (2), review/release (3), debugging (3), ideation/critique/risk (5), and agent docs (2) |

Key routing boundaries across adjacent skills:

- **Debugging**: surfaced logs/errors/issues → `superpowers-systematic-debugging`; exploratory repo-reading & uncertainty-gated defect audit → `find-a-bug`; full-repo C++/Python 7-contract sweep → `project-bug-hunting`.
- **Ideation**: rapid multi-question frontier stress-test → `mattpocock-grilling`; step-by-step convergence into a committed design spec & plan → `superpowers-brainstorming`.
- **Critique, blind spots & risk math**: product loops, market/business assumptions, and qualitative non-code critique → `yc-rejection-simulator`; unfamiliar codebase idioms, framework conventions, and engineering/ops blind spots → `find-blind-spots`; quantitative payoffs, tail constraints, CARA utility, and break-even / reservation-price / $R^*$ inversion → `analyzing-risk-decisions`.
- **Agent authoring**: document structure, pointers, and `AGENTS.md`/`CLAUDE.md` → `mattpocock-writing-for-agents`; subagent pressure-testing and loophole hardening of `SKILL.md` → `superpowers-writing-skills`.

## Upstream maintenance

In a checkout of this repository, ask your agent to run `update-and-sync` to review all documented upstream adaptations, or specify a skill, e.g. `update-and-sync google-stitch-shadcn-ui`. The [maintenance workflow](docs/update-and-sync.md) traces upstream commits and recommends a full sync, selected changes, or skipping the update.

## Install

### Claude Code - as a plugin

```text
/plugin marketplace add host452b/polish
/plugin install polish@polish
```

- Invoke the current skill with `/polish:prompt-polish`, or hand Claude a raw prompt and let the skill trigger automatically.
- Updates: Claude Code uses the explicit version in `.claude-plugin/plugin.json`. Bump all four plugin manifests together for each release; run `/plugin update` after the new version is published. See [version management](https://code.claude.com/docs/en/plugins-reference#version-management).

### Devin CLI - as a plugin

```bash
devin plugins install host452b/polish
# Or link a local checkout on this machine for live authoring:
devin plugins install --local ./polish
```

- Invoke any skill with `/polish:<skill-name>` (e.g. `/polish:analyzing-risk-decisions`), or let Devin invoke it automatically when relevant. Run `devin plugins update polish` to pull newer releases.

### Codex CLI - as a plugin

```bash
codex plugin marketplace add host452b/polish
codex plugin add polish@polish
```

Start a new Codex thread after installing so the skills in this collection are available for automatic triggering.

### Cursor CLI - as a skill

For the current `prompt-polish` skill:

```bash
git clone https://github.com/host452b/polish.git
mkdir -p ~/.cursor/skills
ln -s "$(pwd)/polish/skills/prompt-polish" ~/.cursor/skills/prompt-polish
```

The repo also includes `.cursor-plugin/plugin.json` for Cursor plugin consumers that read Cursor plugin manifests.

### Manual skill install

For the current `prompt-polish` skill:

```bash
git clone https://github.com/host452b/polish.git
mkdir -p ~/.claude/skills ~/.agents/skills ~/.cursor/skills ~/.config/devin/skills
ln -s "$(pwd)/polish/skills/prompt-polish" ~/.claude/skills/prompt-polish
ln -s "$(pwd)/polish/skills/prompt-polish" ~/.agents/skills/prompt-polish
ln -s "$(pwd)/polish/skills/prompt-polish" ~/.cursor/skills/prompt-polish
ln -s "$(pwd)/polish/skills/prompt-polish" ~/.config/devin/skills/prompt-polish
```

Use plugin install when you want the whole collection as it grows. Use manual symlinks when you only want a specific skill in a specific tool or project.

## Skills

### `takeover-agent-sessions`

Use it from any coding agent when picking up unfinished work, recovering context after a rate limit or crash, or looking up local session transcripts recorded by another coding agent (`claude`, `codex`, `cursor`, `windsurf`, `copilot`, `kiro`, `opencode`, `zed`, or `devin`) across macOS, Windows, Linux, and WSL.

Backed by a zero-dependency, strictly read-only Python extractor (`skills/takeover-agent-sessions/scripts/takeover_session.py` — including `file:...?mode=ro` SQLite snapshots, `zstd` rollout/thread decompression, NIST AES-256-GCM + `CortexTrajectory` protobuf decoding for Windsurf `.pb`, VS Code delta-log reduction, and automatic secret redaction), it produces a bounded 5-part Takeover Brief (Goal, Settled Constraints, Files Touched, Commands & Exit Status, Stopping Point) and reconciles transcript intent against live `git status` / `git diff` before resuming work.

Example: `Use $takeover-agent-sessions to inspect my latest Cursor or Codex session for this repo, check what is already on disk, and finish the remaining tests.` In Claude Code and Devin CLI, invoke `/polish:takeover-agent-sessions`.

See [the skill](skills/takeover-agent-sessions/SKILL.md) and [storage paths & parsing pitfalls](skills/takeover-agent-sessions/references/storage-and-pitfalls.md).

### `analyzing-risk-decisions`

Use it when comparing options under uncertain losses or payoffs (insurance/warranties, cloud SLA/DR, QA/CI gating, AI model/tool tiers, capex lease-vs-buy, staged R&D pilots), inverting switching thresholds, or calibrating risk tolerance. Every input is tagged as `fact`, `estimate`, `assumption`, or `preference` so stress assumptions are never disguised as empirical odds, and portfolio increments respect deductibles, coinsurance, caps, prior compensation, and forward-looking NPV (charging today's exit value while excluding sunk costs).

Backed by a stdlib-only deterministic engine (`skills/analyzing-risk-decisions/scripts/decision_engine.py`), it provides `compare` (EV, incremental RTP, `VaR`/`ES`, buffer-breach probability, CARA certainty-equivalent loss $CE_R$, strict dominance), `invert` (`break_even_probability` $p^*$, closed-form `reservation_price` $P^*(R)$, `indifference_r` $R^*$ regimes, `budget_tail_frontier`), `calibrate` (consistent $[R_{\min}, R_{\max}]$ bounds and conflict detection), and `cashflow`.

Example: `Use $analyzing-risk-decisions to compare single-AZ, multi-AZ, and multi-region failover under correlated outage states, invert the minimum budget for a 0.5% breach limit, and report switching boundaries.` In Claude Code, invoke `/polish:analyzing-risk-decisions`.

See [the skill](skills/analyzing-risk-decisions/SKILL.md) and [JSON schemas & domain patterns](skills/analyzing-risk-decisions/references/schemas-and-patterns.md).

### `consistent-term-translation-polish-guard`

Use it for English–Chinese translation, bilingual summaries, and translation polishing involving professional terms, proper names, jargon, or acronyms. It locks one primary translation per concept and sense, keeps related concepts distinct, binds known acronym expansions, and asks about unresolved core terminology. EN→ZH first mentions may include the source term and aliases; later prose stays consistent. ZH→EN uses natural English with the selected terms.

By default, it appends a five-column terminology table. Explicit output formats and requests for translation only take precedence. Visible series glossaries carry forward; fresh sessions need an available glossary rather than a promise of permanent memory. Source formatting and code are preserved.

Example: `Use $consistent-term-translation-polish-guard to translate this technical report into Chinese, reuse the attached glossary, and keep terminology consistent.` In Claude Code, invoke `/polish:consistent-term-translation-polish-guard`.

See [the skill](skills/consistent-term-translation-polish-guard/SKILL.md).

### `yc-rejection-simulator`

Submit a startup idea, pitch, business plan, or YC application for a sharp independent simulation. The skill distinguishes `explicit`, `inference`, and `missing` evidence bases, selects `reject`, `insufficient_evidence`, or `continue`, and gives at most three grounded objections plus one concrete validation test. New evidence can weaken or withdraw earlier objections. It does not represent YC or predict admission outcomes.

The self-contained skill uses Chinese action instructions and English professional concepts, criteria, and output fields. It runs in one response without external services or agent orchestration.

Example: `Use $yc-rejection-simulator to critique this startup application. Be sharp, ground every objection in the material, and identify one test that would change the verdict.` In Claude Code, invoke `/polish:yc-rejection-simulator`.

Additional trigger: use it as a sharp devil's-advocate sounding board for product ideas, product loops, market/buyer assumptions, business models, and non-code strategic decisions when you want help poking holes in the logic. Unfamiliar codebase idioms and engineering/architecture blind spots belong to `find-blind-spots`.

See [the skill](skills/yc-rejection-simulator/SKILL.md).

### `find-blind-spots`

Use it when entering an unfamiliar technical domain, codebase, or framework ("what idioms or unspoken engineering conventions am I missing?") as well as for architectural, technology-selection, and post-launch verification blind spots. It separates awareness, evidence, confidence, and decision impact; a known unknown is not automatically a critical assumption. It uses visible context, checks whether the concern was already addressed, and defaults to one useful finding with a minimal test, pass/fail criteria, and the resulting decision branches. Pure product/market/business-loop critique routes to `yc-rejection-simulator`.

Architecture, technology selection, post-implementation recovery, and comparable-team practices are conditional lenses, not a mandatory production checklist. It distinguishes knowledge, implementation, and verification gaps, including opportunities to reuse assets or simplify work. At consequential decision checkpoints, an implicit pass stays lightweight and preserves the main task. Missing discussion does not establish user ignorance. An ASCII quadrant table is shown by default, with up to three numbered entries per quadrant ranked by importance and no invented filler. Research background remains available on demand.

Example: `Use $find-blind-spots to identify one overlooked consequence of our architecture change, explain the evidence, and give the smallest test that would change our decision.` In Claude Code, invoke `/polish:find-blind-spots`.

See [the skill](skills/find-blind-spots/SKILL.md), [knowledge model](skills/find-blind-spots/references/knowledge-model.md), [decision lenses](skills/find-blind-spots/references/decision-lenses.md), and [prompt-strategy choices and sources](skills/find-blind-spots/references/prompt-strategies.md).

### `prompt-polish`

Give it a raw question or task. It detects the task type, selects a matching combo of research-backed, text-only prompt-engineering strategies, and returns only bilingual rewritten prompts: one code block with `English Prompt` and `中文提示词`.

It builds a better prompt; it does not answer the question for you.

How it works:

1. **Classify** - reasoning, multiple-choice, professional/compliance, structured output, vague requirements, etc.
2. **Select** - pick a 2-4 strategy combo from a task-type to combo table.
3. **Rewrite** - express each strategy as concrete role lines, steps, answer anchors, and fill in the original question.
4. **Output prompts only** - a single code block containing `English Prompt` and `中文提示词`, nothing outside it.

It ships 15 text-only strategies such as `Chain-of-Thought (CoT)`, `Step-Back Prompting`, `Tree of Thoughts (ToT)`, `Self-Contrast`, `Symbolic Placeholder`, `Role-Rule Double Bind`, `Flipped Interaction`, and `Layered Prompt`. Strategies that need API/decoding control or multiple runs are deliberately excluded so the output stays copy-pasteable.

See [references/strategies.md](references/strategies.md) for full strategy templates, rationale, and sources.

### `find-a-bug`

Use it for exploratory defect testing starting from reading a repository, module contracts, or risk paths (or ambiguous failure investigations where premises remain unverified; when concrete error logs or reproducer symptoms are already supplied, prefer `superpowers-systematic-debugging`). Adapted from the user-supplied **Uncertainty-First Planning Protocol**, it separates `VERIFIED`, `USER-STATED`, `INFERRED`, and `UNKNOWN`, checks competing explanations, and tests the top 1–3 unknowns that could change the next action.

It adapts to the project's actual files, contracts, tools, and runtime. Each investigation reports a gate (`GO`, `TEST FIRST`, `ASK USER`, `LIMITED EXPERIMENT`, or `STOP`), evidence boundaries, and a checkpoint. Once a root cause is confirmed in a Git repository, it runs a **30-second countdown prompt** (`scripts/prompt-regression-commit.sh`) that defaults to tracing the introducing **regression commit** on timeout or in non-interactive/autonomous runs. Repair proceeds when requested and supported by evidence; finding no confirmed bug is a valid result.

Example: `Use $find-a-bug to audit this module's boundary handling for hidden defects, verify the top unknowns before proposing a fix, and trace any confirmed bug's regression commit.` In Claude Code, invoke `/polish:find-a-bug`.

See [skills/find-a-bug/SKILL.md](skills/find-a-bug/SKILL.md) for the workflow and report contract.

### `benchmark-checklist`

Use `$benchmark-checklist` to review a measured speedup or regression before reporting it. For example, ask whether a higher GPU submission rate supports a claim about completed requests per second. In Claude Code, invoke `/polish:benchmark-checklist`.

### `project-bug-hunting`

Use it when there is no supplied error and you want project-wide exploration of unknown functional defects. It separates contract relationships, runtime scenarios, and verification methods, then builds a project map, contract inventory, and candidate pool across seven groups: documentation/usage, interfaces/calls, configuration/dispatch, data/artifacts, state/lifecycle, versions/delivery, and tests/real behavior.

Each candidate retains its contract basis, applicability, verification, alternatives, status, and impact. Confirmed behavior errors and root-cause confidence are recorded separately. Native tracing with bpftrace, Python monitoring, and GPU observation are optional evidence sources; probe validation and coverage limits determine what they can establish. The deliverable is a findings report, reproducible evidence, and checked/uncovered scope; zero confirmed defects is a valid result.

Example: `Use $project-bug-hunting to explore this C++/Python repository for unknown functional defects within a 30-minute budget. Report evidence and coverage limits.` In Claude Code, invoke `/polish:project-bug-hunting`.

See [skills/project-bug-hunting/SKILL.md](skills/project-bug-hunting/SKILL.md), with on-demand references for [contract relationships](skills/project-bug-hunting/references/contracts.md), [runtime evidence](skills/project-bug-hunting/references/runtime-tracing.md), and the [report format](skills/project-bug-hunting/references/report-format.md).

### `file-singlify`

Point it at a disk, directory, or mount path. It detects duplicate files and whole duplicate directory copies left by repeated copying, backups, sync, and migration, then proposes a "singlify" plan: keep one canonical copy and map every duplicate to it.

- **Read-only, dry-run by default.** It never deletes, moves, overwrites, hardlinks, or symlinks. Any destructive action is a separate, human-confirmed step.
- **Directory-first.** A whole folder copied many times is the biggest space waste, so directory-level redundancy is detected and reported before per-file hashing.
- **Hash-confirmed.** Name/size/mtime only shortlist candidates; final "identical" verdicts come from content hashes (`md5`, `sha256`, or `both`).

The scan logic lives in `skills/file-singlify/scripts/scan_file_singlify.py` (markdown/json/csv output). See [skills/file-singlify/references/matching-rules.md](skills/file-singlify/references/matching-rules.md) and [skills/file-singlify/references/safety-rules.md](skills/file-singlify/references/safety-rules.md).

### `before-git-push`

Run it right before `git push`, opening a PR, or shipping. Acting as a senior release engineer / SRE, it judges **only from the real diff** and walks a fixed checklist: the most fragile line, unverified assumptions and blind spots, old-user data-compatibility risk (cache, DB schema/migration, persisted format, API contract), the failure path most likely to break prod, and whether rollback + feature toggle are ready.

- **Review, not execution.** It outputs a verdict plus reasoning; a human decides whether to push. It never runs `git push` for you.
- **Diff-grounded.** No real diff, no review — it asks for the diff instead of guessing.
- **Ends in PUSH / HOLD.** After a reverse-verification pass (3 pieces of counter-evidence, each scored), it prints `▶︎▶︎PUSH▶︎▶︎` or `▶︎▶︎HOLD▶︎▶︎`; on HOLD it names the first thing to fix. When unsure, it prefers HOLD.

See [skills/before-git-push/SKILL.md](skills/before-git-push/SKILL.md).

### Google Stitch frontend quality workflow

The four `google-stitch-*` skills are adapted from
[`google-labs-code/stitch-skills`](https://github.com/google-labs-code/stitch-skills),
but have no runtime Stitch service, MCP, project, screen, or upload dependency.
They work as independent skills and can optionally compose through repository
artifacts:

1. `google-stitch-frontend-taste-design` establishes or reviews visual direction and can produce `DESIGN.md`.
2. `google-stitch-extract-frontend-design-system` recovers an existing repository's visual language into `DESIGN.md`.
3. `google-stitch-frontend-brief-enhancer` combines a UI request with available design evidence to produce an implementation brief.
4. `google-stitch-shadcn-ui` applies the design contract and brief when implementing or reviewing a React interface.

The skills keep confirmed facts, reversible assumptions, and unresolved
decisions separate. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for the
pinned source revision and Apache-2.0 attribution.

### Prefixed Superpowers workflow

The six `superpowers-*` skills form a complementary workflow:

1. `superpowers-using-git-worktrees` creates or reuses an isolated workspace.
2. `superpowers-brainstorming` refines an idea step by step into a committed design spec and implementation plan (looking up codebase facts itself rather than asking the user, and complementing `mattpocock-grilling`).
3. `superpowers-test-driven-development` drives implementation from a failing test.
4. `superpowers-systematic-debugging` investigates surfaced bugs from logs, stack traces, or issue symptoms, then prompts with a 30-second non-blocking default to trace the introducing regression commit.
5. `superpowers-verification-before-completion` checks fresh evidence before any success claim.
6. `superpowers-writing-skills` pressure-tests and TDD-hardens `SKILL.md` files against rationalizations before deployment.

These skills are adapted from [`obra/superpowers`](https://github.com/obra/superpowers). See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for the pinned upstream revision and MIT license.

### Prefixed Matt Pocock engineering & agent-writing skills

The eight `mattpocock-*` skills are adapted from [`mattpocock/skills`](https://github.com/mattpocock/skills) as standalone, prefixed skills:

1. `mattpocock-domain-modeling` sharpens project terminology, maintains `GLOSSARY.md` inline, and records ADRs sparingly.
2. `mattpocock-codebase-design` fixes shared deep-module vocabulary (`module`, `interface`, `depth`, `seam`, `adapter`) with `DEEPENING.md` and `DESIGN-IT-TWICE.md`.
3. `mattpocock-grilling` interviews through a design tree in frontier rounds until no silent assumptions remain.
4. `mattpocock-prototype` builds throwaway logic (`LOGIC.md`) or multi-variant UI (`UI.md`) prototypes to settle design questions quickly.
5. `mattpocock-research` investigates primary sources via a background agent and writes cited Markdown notes to the repository.
6. `mattpocock-code-review` runs parallel Standards (repo rules + Fowler smell baseline) and Spec reviews since any fixed Git ref, detecting trackers without requiring `setup-matt-pocock-skills`.
7. `mattpocock-wizard` builds an interactive bash wizard from `template.sh` for manual human-only setup or cutover steps.
8. `mattpocock-writing-for-agents` documents context pointers, information hierarchy, completion criteria, leading words, and pruning for `SKILL.md`, `AGENTS.md`, and `CLAUDE.md`.

In addition, selective high-signal supplements were cherry-picked into existing skills without duplicating triggers:

- `find-a-bug`: [references/feedback-loops.md](skills/find-a-bug/references/feedback-loops.md) and [scripts/hitl-loop.template.sh](skills/find-a-bug/scripts/hitl-loop.template.sh) (from `mattpocock/skills` `diagnosing-bugs`).
- `superpowers-test-driven-development`: [seam-and-slicing-guide.md](skills/superpowers-test-driven-development/seam-and-slicing-guide.md) (from `mattpocock/skills` `tdd`).
- `google-stitch-frontend-taste-design`: [references/quantitative-checks.md](skills/google-stitch-frontend-taste-design/references/quantitative-checks.md) (from `nextlevelbuilder/ui-ux-pro-max-skill`).

See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for pinned upstream revisions and MIT licenses, and [upstream-sources.json](upstream-sources.json) for the machine-readable provenance manifest used for future `update-sync` runs.

### `git-commit-message`

Draft or review a commit message, final squash title, or MR/PR title. The skill selects the target platform from the request and repository evidence, reads the matching GitLab or GitHub profile, and applies repository contribution/CI rules first.

- **GitLab:** standard or team-approved Issue-prefixed headers; validation, risk, and traceability footers; controlled automation exceptions.
- **GitHub:** standard Conventional Commits headers, a 50-character target and 72-character maximum, with explanatory bodies and issue/migration footers.
- **Evidence-based:** uses the selected diff and known validation; reports missing facts without inventing issues or test results. Drafting does not stage, commit, push, or change Git configuration.

Invoke with `/polish:git-commit-message` in Claude Code or `$git-commit-message` where skill-name invocation is supported. Example: “Draft a GitLab commit message for the staged changes, related to PROJ-1234.”

See [skills/git-commit-message/SKILL.md](skills/git-commit-message/SKILL.md) for the workflow and platform references.

### `i-have-adhd-actionable-output`

Use it when asking for ADHD-friendly or easier-to-follow answers, a concise
actionable handoff, or a clearer response whose conclusion and progress are
hard to find. It selectively adapts the core of `ayghri/i-have-adhd` into one
task-scoped skill: answer first, bounded steps, visible progress, complete
information, and evidence-calibrated error reporting.

It preserves detailed explanations and exact output formats, lets the agent
finish authorized work, and adds a next action only when something remains
open. It does not impose a five-item cap, infer a diagnosis, or install hooks
or global session settings. Automatic discovery follows the specific request
triggers in its description; applying it does not enable a permanent mode.

Example: `Use $i-have-adhd-actionable-output to turn these work notes into a
clear handoff. Keep every item's status and distinguish tested from unverified.`
In Claude Code, invoke `/polish:i-have-adhd-actionable-output`.

See [the skill](skills/i-have-adhd-actionable-output/SKILL.md) and
[upstream attribution](THIRD_PARTY_NOTICES.md#i-have-adhd-actionable-output).

## Structure

```text
polish/
├── docs/update-and-sync.md   # upstream adaptation review and sync workflow
├── references/strategies.md  # prompt-polish strategy library
├── skills/benchmark-checklist/
│   ├── SKILL.md              # throughput/latency/speedup claim checklist
│   └── agents/openai.yaml
├── skills/takeover-agent-sessions/
│   ├── SKILL.md              # cross-agent local session takeover workflow
│   ├── references/           # 9-harness OS paths, schemas & parsing pitfalls
│   ├── scripts/              # read-only cross-OS Takeover Brief extractor
│   ├── tests/                # 9-harness + AES-GCM/zstd/SQLite unit suite
│   └── agents/openai.yaml
├── skills/analyzing-risk-decisions/
│   ├── SKILL.md              # probabilistic decision analysis & threshold inversion
│   ├── references/           # JSON schemas and domain modeling patterns
│   ├── scripts/              # deterministic stdlib decision engine
│   ├── tests/                # vertical-slice unit & CLI regression suite
│   └── agents/openai.yaml
├── skills/consistent-term-translation-polish-guard/
│   ├── SKILL.md              # EN↔ZH translation and terminology consistency
│   └── agents/openai.yaml
├── skills/yc-rejection-simulator/
│   ├── SKILL.md              # startup, product-loop, and non-code decision critique
│   └── agents/openai.yaml    # matching display and invocation name
├── skills/find-blind-spots/
│   ├── SKILL.md              # unfamiliar codebase idioms & engineering blind spots
│   ├── references/           # knowledge model, decision lenses, prompt strategies
│   └── agents/openai.yaml    # discovery and implicit-checkpoint metadata
├── skills/i-have-adhd-actionable-output/
│   ├── SKILL.md              # actionable output with completeness safeguards
│   └── agents/openai.yaml    # matching display and invocation name
├── skills/prompt-polish/
│   └── SKILL.md              # canonical prompt-polish skill contract
├── skills/find-a-bug/
│   ├── SKILL.md              # exploratory repo-reading defect audit
│   ├── references/           # tight feedback loops and debugging hygiene
│   ├── scripts/              # HITL repro template + 30s regression-commit gate
│   └── agents/openai.yaml    # discovery and invocation metadata
├── skills/project-bug-hunting/
│   ├── SKILL.md              # project-wide contract and defect exploration
│   ├── references/           # contracts, runtime evidence, report format
│   └── agents/openai.yaml    # discovery and invocation metadata
├── skills/file-singlify/
│   ├── SKILL.md              # canonical file-singlify skill contract
│   ├── scripts/              # read-only duplicate scanner
│   ├── references/           # matching + safety rules
│   └── agents/               # Codex/OpenAI agent descriptor
├── skills/git-commit-message/
│   ├── SKILL.md              # commit-message workflow and platform selection
│   ├── references/           # GitLab, GitHub, and optional tooling
│   └── agents/openai.yaml    # discovery and invocation metadata
├── skills/before-git-push/
│   └── SKILL.md              # canonical before-git-push skill contract
├── skills/google-stitch-frontend-taste-design/
│   ├── SKILL.md              # contextual visual-direction workflow
│   ├── references/           # detailed taste heuristics
│   └── assets/DESIGN.md      # portable design-contract template
├── skills/google-stitch-extract-frontend-design-system/
│   ├── SKILL.md              # source-only design-system extraction
│   └── references/           # framework guides + output template
├── skills/google-stitch-frontend-brief-enhancer/
│   ├── SKILL.md              # vague request to implementation brief
│   └── references/           # UI vocabulary + brief template
├── skills/google-stitch-shadcn-ui/
│   ├── SKILL.md              # shadcn/ui implementation workflow
│   ├── references/           # setup, catalog, customization, migration
│   ├── examples/             # complete form-composition example
│   └── scripts/              # deterministic setup checker
├── skills/superpowers-using-git-worktrees/
│   └── SKILL.md              # isolated-workspace setup workflow
├── skills/superpowers-brainstorming/
│   ├── SKILL.md              # design-before-implementation workflow
│   └── scripts/              # optional visual companion runtime
├── skills/superpowers-systematic-debugging/
│   └── SKILL.md              # root-cause-first debugging workflow
├── skills/superpowers-verification-before-completion/
│   └── SKILL.md              # evidence-before-claims gate
├── skills/superpowers-test-driven-development/
│   └── SKILL.md              # red-green-refactor workflow
├── skills/superpowers-writing-skills/
│   └── SKILL.md              # test-driven skill authoring workflow
├── skills/mattpocock-domain-modeling/
│   ├── SKILL.md              # domain modeling, GLOSSARY.md, and ADR workflow
│   └── agents/openai.yaml
├── skills/mattpocock-codebase-design/
│   ├── SKILL.md              # deep-module vocabulary, deepening, design-it-twice
│   └── agents/openai.yaml
├── skills/mattpocock-grilling/
│   ├── SKILL.md              # round-based design-tree interrogation
│   └── agents/openai.yaml
├── skills/mattpocock-prototype/
│   ├── SKILL.md              # throwaway logic/UI prototyping
│   └── agents/openai.yaml
├── skills/mattpocock-research/
│   ├── SKILL.md              # primary-source background research
│   └── agents/openai.yaml
├── skills/mattpocock-code-review/
│   ├── SKILL.md              # parallel Standards + Spec diff review
│   └── agents/openai.yaml
├── skills/mattpocock-wizard/
│   ├── SKILL.md              # interactive human-step bash wizard generator
│   ├── template.sh           # reusable wizard shell library
│   └── agents/openai.yaml
├── skills/mattpocock-writing-for-agents/
│   ├── SKILL.md              # writing reference for agent-consumed docs
│   └── agents/openai.yaml
├── upstream-sources.json     # machine-readable upstream provenance for update-sync
├── THIRD_PARTY_NOTICES.md    # pinned upstream revisions and license notices
├── .claude-plugin/
│   ├── plugin.json           # Claude plugin manifest
│   └── marketplace.json      # self-contained marketplace catalog
├── .codex-plugin/
│   └── plugin.json           # Codex CLI plugin manifest
├── .cursor-plugin/
│   └── plugin.json           # Cursor plugin manifest
└── .devin-plugin/
    └── plugin.json           # Devin CLI / Devin Cloud plugin manifest
```

When adding skills, keep each skill name stable under `skills/<skill-name>/`. The repo/plugin package can remain `polish` while skills inside it grow independently.

---

<a name="中文版"></a>

# 中文版

> 个人精选的自制与适配 agent skills 集合。

[English](#polish) | **中文**

`polish` 是一个面向 Claude Code、Codex CLI、Cursor CLI 和 Devin CLI 的个人自制与适配 skill/plugin 集合。repo/plugin 包名叫 `polish`；里面每个 skill 的名字保持稳定，避免已有触发方式和安装路径失效。

插件版本：**0.3.0**，Devin、Codex、Claude Code 和 Cursor 四份清单使用同一版本号。

每个 skill 的目录名、`SKILL.md` frontmatter `name`、调用标识和 `agents/openai.yaml` 中的 `interface.display_name` 使用同一个小写连字符名称。例如，`git-commit-message` 的显示名就是 `git-commit-message`，调用时使用 `$git-commit-message`（Claude Code 与 Devin CLI 中为 `/polish:git-commit-message`）。

当前包含：

- `benchmark-checklist` - 核对延迟、吞吐和加速比的计时范围、实际完成量与波动。
- `takeover-agent-sessions` - 跨 macOS、Windows、Linux（含 WSL）只读解析 Cursor、Windsurf、Claude Code、GitHub Copilot、Codex、Kiro、OpenCode、Zed 与 Devin 的本地会话记录，提炼五要素接盘简报并与当前 `git status` / `git diff` 对账，让任意 Agent 无缝接力其他 Agent 没干完的活。
- `analyzing-risk-decisions` - 基于联合有限状态空间、增量净损失函数、CARA 指数效用（$CE_R$）与 `VaR`/`ES` 尾部约束做概率决策分析、切换阈值反推（$p^*$、最高可接受价格 $P^*(R)$、无差异 $R^*$）及风险偏好校准。
- `consistent-term-translation-polish-guard` - 中英双向翻译与译文润色，统一主译名、绑定缩写、确认核心歧义，并默认附双向术语对照表。
- `yc-rejection-simulator` - 评审 startup 申请，并作为尖锐反方边界人审视产品逻辑闭环、市场/用户假设与非代码决策，给出最多三条有据反驳与一个最小验证测试。
- `find-blind-spots` - 识别不熟悉领域的代码习惯（idioms）、框架潜规则、行业工程惯例及架构/上线验证盲点，给出证据和最小验证动作。
- `prompt-polish` - 把粗糙问题改写成高质量、可直接粘贴使用的中英双语 LLM 提示词。
- `find-a-bug` - 偏向探索性测试：从读取 repo、模块契约与边界入手按工程管理学/不确定性门禁找 bug，确认根因后支持 30 秒倒数无阻塞查找 regression commit。
- `project-bug-hunting` - 面向 C++、Python 及混合项目主动探索未知功能缺陷，核对适用契约与源码、安装产物和运行证据。
- `file-singlify` - 扫描磁盘/目录/挂载路径，找出重复文件和重复目录副本，生成「单副本化」方案（保留一份 canonical copy + duplicate→canonical 映射），默认只读 dry-run 报告。
- `before-git-push` - push 前最后一道风险闸门：以发布工程师视角从真实 diff 追踪受影响的调用方，给出 PUSH 或 HOLD 建议。
- `git-commit-message` - 按 GitLab / GitHub 各自规范生成和检查提交信息，优先遵守目标仓库规则。
- `i-have-adhd-actionable-output` - 让答案和交接更易执行，同时保留完整信息、证据边界和 agent 自主完成工作的能力。
- `google-stitch-frontend-taste-design` - 建立或审查有证据支撑的前端视觉方向，避免泛化的 AI 风格和虚构产品内容。
- `google-stitch-extract-frontend-design-system` - 即使项目无法构建或运行，也能从前端源码提取可移植的 `DESIGN.md`。
- `google-stitch-frontend-brief-enhancer` - 把模糊 UI 需求转换为边界清晰、假设透明且可验收的实施 Brief。
- `google-stitch-shadcn-ui` - 基于项目真实 token 与 primitives 实现或审查一致、无障碍、响应式的 shadcn/ui 界面。
- `superpowers-using-git-worktrees` - 在功能开发或执行计划前创建或复用隔离工作区。
- `superpowers-brainstorming` - 在写代码前一步一问把想法收敛为已批准的设计规格（spec）与实施计划。
- `superpowers-test-driven-development` - 用 red-green-refactor（含预确认 seam 与垂直切片指南）约束功能与 bugfix 实现。
- `superpowers-systematic-debugging` - 面向已出现报错日志、堆栈或 Issue 现象的根因调试，确认根因后支持 30 秒倒数无阻塞查找 regression commit。
- `superpowers-verification-before-completion` - 在声称成功前要求最新验证证据。
- `superpowers-writing-skills` - 用子 agent 压力测试与 TDD 纪律检验并加固 `SKILL.md` 防绕过能力。
- `mattpocock-domain-modeling` - 构建并打磨项目领域模型、`GLOSSARY.md` 词汇表与 ADR。
- `mattpocock-codebase-design` - 提供深模块设计共享词汇（`module`、`interface`、`depth`、`seam`、`adapter`）及深化与多方案对比指南。
- `mattpocock-grilling` - 按设计树分轮批量拷问方案、决策与想法以消除隐含假设，收敛后可按需衔接正式 spec。
- `mattpocock-prototype` - 快速构建抛弃型逻辑或 UI 原型以验证设计问题。
- `mattpocock-research` - 用后台 agent 基于一手资料调研并沉淀带引用的 Markdown 笔记。
- `mattpocock-code-review` - 基于指定 Git 基准并行执行 Standards 与 Spec 双轴评审。
- `mattpocock-wizard` - 为必须人工执行的配置、凭证或迁移步骤生成交互式 bash 向导脚本。
- `mattpocock-writing-for-agents` - 面向 agent 文档（`SKILL.md`、`AGENTS.md`、`CLAUDE.md`）的结构、指针与精简写作参考。

## 技能正交度与路由总览

| 指标 | 当前数值 | 解读 |
| --- | --- | --- |
| Skill 总数 | **31** | 全部 `description` 合计 **8,956 字符**（均值 **289 字符/个**），常驻上下文开销紧凑可控 |
| 功能正交率（方法论/产出不重复） | **~86%**（功能重叠率 ~14%） | 相邻 skill 在方法论、作用对象与交付产物上互补，无冗余废项 |
| 触发正交率（自动命中不打架） | **~88%**（由调优前 ~68% 提升） | 原 3 个冲突簇已在 `description` 中建立显式互排与分流指针 |
| 完全正交单点（0% 重叠） | **11 / 31（35.5%）** | 作用对象与目标完全独立（如 `prompt-polish`、`file-singlify`、`takeover-agent-sessions`、`benchmark-checklist`、`mattpocock-wizard` 等） |
| 同域流水线 / 正交协作 | **20 / 31（64.5%）** | 按阶段与切面分流：前端 UI(5)、领域与模块设计(2)、评审与发布门禁(3)、缺陷排查(3)、方案推敲/挑刺/概率决策(5)、Agent 文档编写(2) |

相邻 skill 的核心分流规则：

- **缺陷排查三层分流**：有报错日志 / Issue 现象 → `superpowers-systematic-debugging`；从读 repo 出发按工程管理学/不确定性门禁做探索性找 bug → `find-a-bug`；C++/Python 全仓 7 类契约盘点 → `project-bug-hunting`。
- **方案推敲双模式**：早期想法设计树分轮高密度拷问 → `mattpocock-grilling`；一步一问收敛并落盘正式设计 spec 与实施计划 → `superpowers-brainstorming`（两者互通长板）。
- **挑刺、盲点与概率决策分工**：产品闭环、市场/商业假设与定性非代码决策挑刺 → `yc-rejection-simulator`；陌生领域代码习惯（idioms）、框架潜规则、行业工程惯例与架构上线盲区 → `find-blind-spots`；明确含成本/损失分布、尾部风险约束、CARA 效用与回本概率/保留价格/$R^*$ 切换边界反推 → `analyzing-risk-decisions`。
- **Agent 文档分工**：文档信息架构、上下文指针与 `AGENTS.md`/`CLAUDE.md` 编写精简 → `mattpocock-writing-for-agents`；子 agent 压力测试与 `SKILL.md` 防借口加固 → `superpowers-writing-skills`。

## 上游维护

在本仓库里对 agent 说 `update-and-sync`，即可检查所有有明确开源上游的 skill；也可以指定一个，例如 `update-and-sync google-stitch-shadcn-ui`。默认汇总相关提交并给出同步建议；需要落地时可以直接说「分析并应用合适的更新」。详见[上游维护流程](docs/update-and-sync.md)。

## 安装

### Claude Code：作为插件安装

```text
/plugin marketplace add host452b/polish
/plugin install polish@polish
```

- 当前 skill 可用 `/polish:prompt-polish` 调用，也可以直接把原始 prompt 交给 Claude，由它按描述自动触发。
- 更新：Claude Code 使用 `.claude-plugin/plugin.json` 中的显式版本。每次发布时同步递增四份插件清单的版本号；新版本发布后运行 `/plugin update` 更新。详见[版本管理](https://code.claude.com/docs/en/plugins-reference#version-management)。

### Devin CLI：作为插件安装

```bash
devin plugins install host452b/polish
# 或在本机直接链接本地仓库以便实时调试：
devin plugins install --local ./polish
```

- 安装后可用 `/polish:<skill-name>`（例如 `/polish:analyzing-risk-decisions`）调用任意 skill，或由 Devin 按描述自动触发；后续执行 `devin plugins update polish` 拉取新版本。

### Codex CLI：作为插件安装

```bash
codex plugin marketplace add host452b/polish
codex plugin add polish@polish
```

安装后开启新的 Codex 对话，让这个集合里的 skills 进入可触发列表。

### Cursor CLI：作为 skill 安装

安装当前 `prompt-polish` skill：

```bash
git clone https://github.com/host452b/polish.git
mkdir -p ~/.cursor/skills
ln -s "$(pwd)/polish/skills/prompt-polish" ~/.cursor/skills/prompt-polish
```

仓库也包含 `.cursor-plugin/plugin.json`，供能读取 Cursor plugin manifest 的插件消费者使用。

### 手动安装（clone + 软链）

安装当前 `prompt-polish` skill：

```bash
git clone https://github.com/host452b/polish.git
mkdir -p ~/.claude/skills ~/.agents/skills ~/.cursor/skills ~/.config/devin/skills
ln -s "$(pwd)/polish/skills/prompt-polish" ~/.claude/skills/prompt-polish
ln -s "$(pwd)/polish/skills/prompt-polish" ~/.agents/skills/prompt-polish
ln -s "$(pwd)/polish/skills/prompt-polish" ~/.cursor/skills/prompt-polish
ln -s "$(pwd)/polish/skills/prompt-polish" ~/.config/devin/skills/prompt-polish
```

如果你想随着仓库扩展使用整个集合，优先用 plugin 安装；如果只想在某个工具或项目里启用单个 skill，再用手动软链。

## Skills

### `takeover-agent-sessions`

适用于在任意 coding agent 中接手其他工具没干完的任务、额度/限流切换工具、崩溃或压缩后恢复上下文，以及跨工具检索本地历史会话（支持 `claude`、`codex`、`cursor`、`windsurf`、`copilot`、`kiro`、`opencode`、`zed` 与 `devin`，覆盖 macOS、Windows、Linux 及 WSL 跨系统挂载）。

内置零第三方依赖的只读解析脚本 `skills/takeover-agent-sessions/scripts/takeover_session.py`（自动处理 SQLite `?mode=ro` 只读快照、`zstd` 压缩会话、Windsurf `.pb` AES-256-GCM 认证解密与 `CortexTrajectory` Protobuf 解析、VS Code Copilot 增量状态归约及密钥脱敏），将海量原始日志提炼为五要素 Takeover Brief（目标、已拍板约束、触碰文件、命令与退出码、中断现场），并强制与当前工作区 `git status` / `git diff` 对账后再继续施工。

示例：`使用 $takeover-agent-sessions 读取我刚才在 Cursor 或 Codex 里做到一半的当前仓库会话，核对磁盘改动后把剩下的活干完。` Claude Code 与 Devin CLI 中使用 `/polish:takeover-agent-sessions`。

见 [skill 正文](skills/takeover-agent-sessions/SKILL.md) 和 [存储路径与解析坑点参考](skills/takeover-agent-sessions/references/storage-and-pitfalls.md)。

### `analyzing-risk-decisions`

适用于存在不确定成本、收益或大额损失的多方案权衡（保险/延保配置、云服务 SLA/容灾备份、QA/CI 回归资源分配、AI 模型与工具档位选择、设备租买更新、分阶段验证投入）。强制区分 `fact`（合同与报价事实）、`estimate`（经验统计）、`assumption`（压力假设）与 `preference`（预算、承受线与风险偏好），按组合增量扣减免赔、比例、封顶及已赔余额，并在多期持有决策中计入当前退出机会成本、剔除沉没成本。

内置零外部依赖的可审计计算脚本 `skills/analyzing-risk-decisions/scripts/decision_engine.py`，支持四种子命令：`compare`（期望净损失、增量 RTP、深尾部 `VaR`/`ES`、缓冲突破概率、CARA 确定等价损失 $CE_R$ 与严格支配检测）、`invert`（反推回本概率 $p^*$、解析保留价格 $P^*(R)$、无差异风险承受参数 $R^*$ 分段与预算—尾部 Pareto 前沿）、`calibrate`（由取舍题反推一致 $[R_{\min}, R_{\max}]$ 区间并定位矛盾回答）与 `cashflow`。

示例：`使用 $analyzing-risk-decisions 在含共同故障状态的单 AZ、多 AZ 与跨区容灾方案间反推满足 0.5% 尾部突破上限的最低成本，并给出选择切换边界。` Claude Code 中使用 `/polish:analyzing-risk-decisions`。

见 [skill 正文](skills/analyzing-risk-decisions/SKILL.md) 和 [JSON Schema 与领域模式](skills/analyzing-risk-decisions/references/schemas-and-patterns.md)。

### `consistent-term-translation-polish-guard`

适用于含专业术语、专有名词、行业黑话或缩写的中英双向翻译、双语摘要与译文润色。按“源词＋义项”锁定唯一主译名，区分近义概念，绑定缩写与已知全称，并确认尚未解决的核心术语歧义。英译中首次可标注原词及别名，后文统一；中译英保持自然表达和术语一致。

默认附五列《双向术语一致性对照表》，用户指定的严格格式或纯译文要求优先。沿用当前可见的系列术语表；新会话需提供可访问的术语约定，不承诺永久记忆。保留源文结构、格式与代码。

示例：`使用 $consistent-term-translation-polish-guard 把这份技术报告译成中文，沿用附件术语表，并检查全文术语一致性。` Claude Code 中使用 `/polish:consistent-term-translation-polish-guard`。

见 [skill 正文](skills/consistent-term-translation-polish-guard/SKILL.md)。

### `yc-rejection-simulator`

提交 startup idea、pitch、business plan 或 YC application，即可获得尖锐的 independent simulation。区分 `explicit`、`inference`、`missing` 三种 evidence basis，选择 `reject`、`insufficient_evidence` 或 `continue`，给出最多三个有依据的 objections 和一个具体 validation test。补充证据后会减弱或撤回原质疑；不代表 YC，也不预测录取结果。

操作指引用中文，professional concepts、review criteria 和 output fields 使用英文。主流程集中在一个 `SKILL.md`，一次 response 完成，无需外部服务或多个 agents。

示例：`使用 $yc-rejection-simulator 评审这份 startup application，反馈要尖锐，每条 objection 都要对应材料，并给出一个能改变 verdict 的 validation test。` Claude Code 中使用 `/polish:yc-rejection-simulator`。

额外触发：当用户想对自己的产品想法、产品逻辑闭环、市场/用户假设、商业方案或非代码决策挑刺、反省（需要尖锐反方边界人协助补齐闭环）时也可使用；陌生技术领域的代码习惯、框架潜规则与工程架构盲区则交由 `find-blind-spots`。

见 [skill 正文](skills/yc-rejection-simulator/SKILL.md)。

### `find-blind-spots`

聚焦技术与工程盲区：特别适用于进入不熟悉的技术领域、语言/框架或陌生代码库时排查“我不熟的代码习惯（idioms）、框架潜规则或行业工程惯例”，也用于架构、技术选型、改造后恢复能力和同行工程实践差距审视。分别处理觉察、证据、信心和决策影响，明确“已知未知”不一定是关键假设；纯产品与非代码商业决策挑刺交由 `yc-rejection-simulator`。

默认只给一个最有价值的发现，附 ASCII 四象限表，每格按重要程度用 1、2、3 编号、最多三项，有几项列几项，无证据不凑数；随后说明依据、最小验证及通过／失败后的选择。区分知识、落实与验证缺口，同时寻找复用与简化的收益机会。隐式触发仅在关键决策处轻量检查，保留主任务。聊天没提到不等于用户不知道；已经处理过的事项不反复提醒。研究来源按需展开，原型试用不会自动套用生产级清单。

示例：`使用 $find-blind-spots，基于当前聊天和项目证据，找出这次架构改造最容易遗漏的一个上线后问题，并给出最小验证和结果分支。`
Claude Code 中使用 `/polish:find-blind-spots`。

见 [skill 正文](skills/find-blind-spots/SKILL.md)、[认知模型与来源](skills/find-blind-spots/references/knowledge-model.md)、[决策视角](skills/find-blind-spots/references/decision-lenses.md) 和 [提示词策略取舍与来源](skills/find-blind-spots/references/prompt-strategies.md)。

### `prompt-polish`

输入一个原始问题或任务。它会判断任务类型，选择一组匹配的、纯文本提示词工程策略，然后只输出中英双语重构提示词：一个代码块，内含 `English Prompt` 和 `中文提示词`。

它是在帮你造更好的 prompt，不会替你回答原题。

工作流程：

1. **判类型** - 复杂推理、选择题、专业/合规、结构化输出、需求模糊等。
2. **选组合** - 按任务类型选择 2-4 个策略组合。
3. **重构** - 把策略写成具体角色句、步骤、答案锚点，并填入原始问题。
4. **只输出提示词** - 一个代码块，包含 `English Prompt` 和 `中文提示词`，块外零说明。

当前内置 15 项纯文本策略，例如 `Chain-of-Thought (CoT)`、`Step-Back Prompting`、`Tree of Thoughts (ToT)`、`Self-Contrast`、`Symbolic Placeholder`、`Role-Rule Double Bind`、`Flipped Interaction`、`Layered Prompt`。需要 API/解码控制或多次运行的策略被排除，保证输出始终可直接复制使用。

完整策略模板、原理与来源见 [references/strategies.md](references/strategies.md)。

### `find-a-bug`

偏向探索性测试：用于从读取 repo、模块边界与契约出发按工程管理学方法主动排查缺陷，或调查前提尚未核实的疑难故障（已有明确报错日志、堆栈或 Issue 现象时优先使用 `superpowers-systematic-debugging`）。改写自用户提供的 **Uncertainty-First Planning Protocol**：区分 `VERIFIED`、`USER-STATED`、`INFERRED` 和 `UNKNOWN`，保留竞争解释，优先验证最可能改变下一步动作的 1–3 个未知数。

根据项目实际文件、契约、工具和运行状态选择调查方法。每轮报告 `GO`、`TEST FIRST`、`ASK USER`、`LIMITED EXPERIMENT` 或 `STOP` 门槛，以及证据边界和下一检查点。在 Git 仓库内确认 bug 根因后，会通过 `scripts/prompt-regression-commit.sh` 提示是否继续定位引入该问题的 **regression commit**（交互终端默认倒数 30 秒，超时或全自动/非交互模式下默认不阻塞自动寻找）。已要求修复且证据充分时继续修复；本轮没有发现已确认 bug 也是有效结论。

示例：`使用 $find-a-bug 从仓库模块边界出发做探索性缺陷排查，先验证关键未知数，确认 bug 后一并定位引入它的 regression commit。` Claude Code 中可用 `/polish:find-a-bug`。

完整流程与输出契约见 [skills/find-a-bug/SKILL.md](skills/find-a-bug/SKILL.md)。

### `benchmark-checklist`

在报告加速或回退前，使用 `$benchmark-checklist` 核对测量证据。例如，“GPU 请求提交速率提高了，现有数据能支持完成吞吐提升的结论吗？” Claude Code 中使用 `/polish:benchmark-checklist`。

### `project-bug-hunting`

用于没有现成报错时的项目级未知功能缺陷探索。将契约关系、运行场景、验证手段分开组织，建立项目地图、契约清单与候选问题池，覆盖文档与使用、接口与调用、配置与分派、数据与产物、状态与生命周期、版本与交付、测试与真实行为七组关系。

每个候选独立记录契约依据、适用条件、验证过程、替代解释、状态与影响；行为错误是否确认和根因是否确定分别记录。bpftrace、Python 监控和 GPU 观测是可选取证手段，必须校验探针有效性并说明覆盖限制。交付发现报告、可复现证据、已检查与未覆盖范围；没有确认缺陷也是有效结果。

示例：`使用 $project-bug-hunting，在 30 分钟预算内探索这个 C++/Python 仓库中的未知功能缺陷，报告证据与覆盖边界。` Claude Code 中可用 `/polish:project-bug-hunting`。

入口见 [skills/project-bug-hunting/SKILL.md](skills/project-bug-hunting/SKILL.md)，按需加载[契约关系](skills/project-bug-hunting/references/contracts.md)、[运行时取证](skills/project-bug-hunting/references/runtime-tracing.md)及[报告格式](skills/project-bug-hunting/references/report-format.md)。

### `file-singlify`

把它指向某个磁盘、目录或挂载路径。它会找出因多次复制、备份、同步、迁移产生的重复文件和整目录重复副本，并生成「单副本化」方案：每组保留一份 canonical copy，其余映射到它。

- **默认只读、dry-run。** 绝不删除、移动、覆盖、改写、建硬/软链接。任何破坏性操作都是独立的、需用户明确确认的一步。
- **目录优先。** 整个目录被多次复制是最大空间浪费来源，所以先做目录级冗余检测和展示，再对候选文件做 hash。
- **hash 确认。** 文件名/大小/时间只用于筛候选；最终「相同」结论来自内容 hash（`md5`、`sha256` 或 `both`）。

扫描逻辑在 `skills/file-singlify/scripts/scan_file_singlify.py`（支持 markdown/json/csv 输出）。详见 [skills/file-singlify/references/matching-rules.md](skills/file-singlify/references/matching-rules.md) 与 [skills/file-singlify/references/safety-rules.md](skills/file-singlify/references/safety-rules.md)。

### `before-git-push`

在 `git push`、提 PR、上线之前运行。它以资深发布工程师 / SRE 视角，**只依据真实 diff** 走一遍固定清单：最发虚的一行、未验证假设与盲区、老用户数据兼容风险（缓存、数据库 schema/迁移、持久化格式、API 契约）、最可能击穿的失败路径，以及回滚 + feature toggle 是否就绪。

- **只审查、不执行。** 只产出建议与理由，是否 push 由人决定；绝不代替你执行 `git push`。
- **以 diff 为准。** 看不到真实 diff 就要求补充，绝不凭空评审。
- **结论落到 PUSH / HOLD。** 经反向验证（3 条反证并打分）后输出 `▶︎▶︎PUSH▶︎▶︎` 或 `▶︎▶︎HOLD▶︎▶︎`；HOLD 时写明第一件要修的事。没把握时倾向 HOLD。

详见 [skills/before-git-push/SKILL.md](skills/before-git-push/SKILL.md)。

### Google Stitch 前端质量工作流

四个 `google-stitch-*` skills 适配自
[`google-labs-code/stitch-skills`](https://github.com/google-labs-code/stitch-skills)，
但运行时不依赖 Stitch 服务、MCP、project、screen 或上传链。它们可以独立使用，
也可以通过仓库中的 artifact 组合：

1. `google-stitch-frontend-taste-design` 建立或审查视觉方向，并可生成 `DESIGN.md`。
2. `google-stitch-extract-frontend-design-system` 从已有仓库恢复视觉语言并写入 `DESIGN.md`。
3. `google-stitch-frontend-brief-enhancer` 结合 UI 需求与设计证据，产出实施 Brief。
4. `google-stitch-shadcn-ui` 在 React 实现或审查中应用设计契约与 Brief。

这些 skills 会区分已确认事实、可逆假设与待决问题。固定的来源版本和 Apache-2.0
归属信息见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

### Prefixed Superpowers 工作流

六个 `superpowers-*` skills 组成一套互补工作流：

1. `superpowers-using-git-worktrees` 创建或复用隔离工作区。
2. `superpowers-brainstorming` 一步一问把想法收敛为正式设计规格（spec）并衔接到实施计划（自行查证代码事实，只把取舍交给用户，与 `mattpocock-grilling` 互补）。
3. `superpowers-test-driven-development` 从失败测试开始驱动实现。
4. `superpowers-systematic-debugging` 面向已给定的报错日志、堆栈或 Issue 现象调查根因，确认根因后支持 30 秒倒数无阻塞继续定位 regression commit。
5. `superpowers-verification-before-completion` 在任何成功声明前检查最新证据。
6. `superpowers-writing-skills` 用子 agent 压力测试与 TDD 纪律验证并加固 `SKILL.md`。

这些 skills 适配自 [`obra/superpowers`](https://github.com/obra/superpowers)。固定的上游版本和 MIT license 见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

### Prefixed Matt Pocock 工程与 Agent 写作 Skills

八个 `mattpocock-*` skills 适配自 [`mattpocock/skills`](https://github.com/mattpocock/skills)，以独立、带前缀的形式运行：

1. `mattpocock-domain-modeling` 澄清项目领域术语、即时维护 `GLOSSARY.md`，并克制地记录 ADR。
2. `mattpocock-codebase-design` 统一深模块设计词汇（`module`、`interface`、`depth`、`seam`、`adapter`），附 `DEEPENING.md` 与 `DESIGN-IT-TWICE.md`。
3. `mattpocock-grilling` 按设计树 frontier 分轮追问，直到没有隐含假设。
4. `mattpocock-prototype` 用抛弃型逻辑原型（`LOGIC.md`）或多变体 UI 原型（`UI.md`）快速验证设计问题。
5. `mattpocock-research` 派发后台 agent 查证一手资料，并在仓库内沉淀带来源引用的 Markdown 笔记。
6. `mattpocock-code-review` 针对任意 Git 基准并行运行 Standards（仓库规范 + Fowler 代码坏味道基线）与 Spec 双轴评审，自动探测仓库/CLI 追踪方式，不依赖 `setup-matt-pocock-skills`。
7. `mattpocock-wizard` 基于 `template.sh` 生成交互式 bash 向导，引导人工完成只能手动执行的配置或切换步骤。
8. `mattpocock-writing-for-agents` 总结给 agent 消费文档（`SKILL.md`、`AGENTS.md`、`CLAUDE.md`）的指针、信息层级、完成条件、引导词与精简原则。

此外，在不引入重复触发的前提下，向现有 skills 隔离式补充了三组精选参考：

- `find-a-bug`：[references/feedback-loops.md](skills/find-a-bug/references/feedback-loops.md) 与 [scripts/hitl-loop.template.sh](skills/find-a-bug/scripts/hitl-loop.template.sh)（精选自 `mattpocock/skills` `diagnosing-bugs`）。
- `superpowers-test-driven-development`：[seam-and-slicing-guide.md](skills/superpowers-test-driven-development/seam-and-slicing-guide.md)（精选自 `mattpocock/skills` `tdd`）。
- `google-stitch-frontend-taste-design`：[references/quantitative-checks.md](skills/google-stitch-frontend-taste-design/references/quantitative-checks.md)（精选自 `nextlevelbuilder/ui-ux-pro-max-skill`）。

固定上游版本与 MIT 归属见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)，面向后续 `update-sync` 的机器可读来源清单见 [upstream-sources.json](upstream-sources.json)。

### `git-commit-message`

生成或检查 commit message、最终 squash 标题及 MR/PR 标题。根据用户指定目标和仓库证据选择平台，读取对应规范，优先遵守仓库 CONTRIBUTING 与 CI 规则。

- **GitLab：** 标准格式或团队约定的 Issue 前缀格式；验证、风险与追溯 footer；受控自动化提交例外。
- **GitHub：** 标准 Conventional Commits 格式；完整标题建议不超过 50 字符、硬上限 72；正文解释原因，footer 关联 Issue 或说明迁移。
- **基于证据：** 使用选定 diff 和已知验证结果，缺失信息明确说明，不虚构 Issue 或测试结果。仅生成信息不会执行暂存、提交、推送或修改 Git 配置。

Claude Code 中使用 `/polish:git-commit-message`；支持 skill 名称调用的环境中使用 `$git-commit-message`。例如：“根据暂存改动生成 GitLab 提交信息，关联 PROJ-1234。”

工作流与两套平台参考规范见 [skills/git-commit-message/SKILL.md](skills/git-commit-message/SKILL.md)。

### `i-have-adhd-actionable-output`

用于用户要求 ADHD 友好、易跟进的回答、简洁可执行的交接，或重新组织结论和进度
难以找到的回复。它精选迁移 `ayghri/i-have-adhd` 的核心内容，整合为一个按当前
任务生效的 skill：答案优先、步骤明确、进度可见、信息完整、错误陈述有据可查。

保留详细解释和精确输出格式，支持 agent 直接完成已授权工作；仅有未完成事项时
才给出下一步。不设五项硬上限，不推断诊断，不安装 hooks 或全局会话设置。
按照描述中的具体请求场景自动发现，使用一次不会开启永久模式。

示例：`使用 $i-have-adhd-actionable-output 把这些工作记录整理成清晰交接，保留每项状态，区分已验证和未验证。`
Claude Code 中使用 `/polish:i-have-adhd-actionable-output`。

见 [skill 正文](skills/i-have-adhd-actionable-output/SKILL.md) 和
[上游归属](THIRD_PARTY_NOTICES.md#i-have-adhd-actionable-output)。

## 结构

```text
polish/
├── docs/update-and-sync.md   # 上游适配审查与同步工作流
├── references/strategies.md  # prompt-polish 策略库
├── skills/benchmark-checklist/
│   ├── SKILL.md              # 吞吐/延迟/加速比测量核查清单
│   └── agents/openai.yaml
├── skills/takeover-agent-sessions/
│   ├── SKILL.md              # 跨工具本地会话读取与未完任务接盘流程
│   ├── references/           # 9 套工具三端存储路径、Schema 与解析坑点
│   ├── scripts/              # 零依赖只读跨平台 Takeover Brief 提取器
│   ├── tests/                # 9 套工具 + AES-GCM/zstd/SQLite 回归测试
│   └── agents/openai.yaml
├── skills/analyzing-risk-decisions/
│   ├── SKILL.md              # 概率决策分析、尾部约束与切换阈值反推
│   ├── references/           # JSON Schema 与领域建模模式
│   ├── scripts/              # Python 标准库零依赖可审计计算引擎
│   ├── tests/                # 垂直切片单元与 CLI 回归测试
│   └── agents/openai.yaml
├── skills/consistent-term-translation-polish-guard/
│   ├── SKILL.md              # EN↔ZH translation and terminology consistency
│   └── agents/openai.yaml
├── skills/yc-rejection-simulator/
│   ├── SKILL.md              # 产品闭环、商业假设与非代码决策挑刺
│   └── agents/openai.yaml    # 一致的显示名与调用名
├── skills/find-blind-spots/
│   ├── SKILL.md              # 陌生领域代码习惯、工程惯例与架构盲点
│   ├── references/           # 认知模型、决策视角与提示词策略
│   └── agents/openai.yaml    # 发现与关键工程节点隐式检查元数据
├── skills/i-have-adhd-actionable-output/
│   ├── SKILL.md              # 可执行回答与完整性保护
│   └── agents/openai.yaml    # 一致的展示名与调用名
├── skills/prompt-polish/
│   └── SKILL.md              # prompt-polish 的主行为契约
├── skills/find-a-bug/
│   ├── SKILL.md              # 从读仓库出发的探索性缺陷排查
│   ├── references/           # 紧反馈复现阶梯与调试卫生补充
│   ├── scripts/              # HITL 复现模板 + 30s regression commit 门禁
│   └── agents/openai.yaml    # 发现与调用元数据
├── skills/project-bug-hunting/
│   ├── SKILL.md              # 项目级契约一致性与未知缺陷探索
│   ├── references/           # 契约关系、运行时取证、报告格式
│   └── agents/openai.yaml    # 发现与调用元数据
├── skills/file-singlify/
│   ├── SKILL.md              # file-singlify 的主行为契约
│   ├── scripts/              # 只读重复扫描脚本
│   ├── references/           # 匹配 + 安全规则
│   └── agents/               # Codex/OpenAI agent 描述
├── skills/git-commit-message/
│   ├── SKILL.md              # commit-message workflow and platform selection
│   ├── references/           # GitLab, GitHub, and optional tooling
│   └── agents/openai.yaml    # discovery and invocation metadata
├── skills/before-git-push/
│   └── SKILL.md              # before-git-push 的主行为契约
├── skills/google-stitch-frontend-taste-design/
│   ├── SKILL.md              # 基于上下文的视觉方向工作流
│   ├── references/           # 详细审美规则
│   └── assets/DESIGN.md      # 可移植设计契约模板
├── skills/google-stitch-extract-frontend-design-system/
│   ├── SKILL.md              # 只读源码的设计系统提取
│   └── references/           # 框架指南 + 输出模板
├── skills/google-stitch-frontend-brief-enhancer/
│   ├── SKILL.md              # 模糊需求转实施 Brief
│   └── references/           # UI 词汇 + Brief 模板
├── skills/google-stitch-shadcn-ui/
│   ├── SKILL.md              # shadcn/ui 实现工作流
│   ├── references/           # 设置、目录、定制、迁移指南
│   ├── examples/             # 完整表单组合示例
│   └── scripts/              # 确定性设置检查器
├── skills/superpowers-using-git-worktrees/
│   └── SKILL.md              # 隔离工作区设置流程
├── skills/superpowers-brainstorming/
│   ├── SKILL.md              # 先设计后实施工作流
│   └── scripts/              # 可选 visual companion runtime
├── skills/superpowers-systematic-debugging/
│   └── SKILL.md              # 根因优先的调试工作流
├── skills/superpowers-verification-before-completion/
│   └── SKILL.md              # 声称完成前的证据闸门
├── skills/superpowers-test-driven-development/
│   └── SKILL.md              # red-green-refactor 工作流
├── skills/superpowers-writing-skills/
│   └── SKILL.md              # 测试驱动的 skill 编写流程
├── skills/mattpocock-domain-modeling/
│   ├── SKILL.md              # 领域建模、GLOSSARY.md 与 ADR 流程
│   └── agents/openai.yaml
├── skills/mattpocock-codebase-design/
│   ├── SKILL.md              # 深模块词汇、深化与多方案对比
│   └── agents/openai.yaml
├── skills/mattpocock-grilling/
│   ├── SKILL.md              # 设计树分轮拷问
│   └── agents/openai.yaml
├── skills/mattpocock-prototype/
│   ├── SKILL.md              # 抛弃型逻辑/UI 原型验证
│   └── agents/openai.yaml
├── skills/mattpocock-research/
│   ├── SKILL.md              # 后台一手资料调研
│   └── agents/openai.yaml
├── skills/mattpocock-code-review/
│   ├── SKILL.md              # Standards + Spec 双轴并行评审
│   └── agents/openai.yaml
├── skills/mattpocock-wizard/
│   ├── SKILL.md              # 人工步骤交互式 bash 向导生成
│   ├── template.sh           # 可复用向导脚本库
│   └── agents/openai.yaml
├── skills/mattpocock-writing-for-agents/
│   ├── SKILL.md              # 面向 agent 文档的写作参考
│   └── agents/openai.yaml
├── upstream-sources.json     # 面向 update-sync 的机器可读来源清单
├── THIRD_PARTY_NOTICES.md    # 固定上游版本与第三方许可说明
├── .claude-plugin/
│   ├── plugin.json           # Claude 插件清单
│   └── marketplace.json      # 自带 marketplace 目录
├── .codex-plugin/
│   └── plugin.json           # Codex CLI 插件清单
├── .cursor-plugin/
│   └── plugin.json           # Cursor 插件清单
└── .devin-plugin/
    └── plugin.json           # Devin CLI / Devin Cloud 插件清单
```

以后新增 skills 时，把每个 skill 的稳定入口放在 `skills/<skill-name>/` 下。外层 repo/plugin 包名继续叫 `polish`，里面的 skills 可以独立增长。
