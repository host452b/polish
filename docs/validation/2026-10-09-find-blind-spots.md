# find-blind-spots validation

Date: 2026-10-09. Author: Codex. Scope: new skill and bilingual README entries.

## Method and limits

Used the `polish:superpowers-writing-skills` baseline/candidate method. Runner: session-native collaboration subagents with fresh context (`fork_turns=none`); inherited session model, with no exact model build ID exposed. No external provider CLI, network, production system, or repository mutation was permitted in the scenario tasks. Candidate agents could read the skill and its linked references. One trial per case, not a statistical evaluation. The author judged outputs against the rubric; this is not an independent release certification or installed-runtime trigger test.

The baseline agent answered A and B before skill creation. A new candidate agent answered identical A and B prompts with the skill, then C–E in a follow-up. A/B had a 250-Chinese-character requested answer budget; C–E had 180. Content quality was evaluated, not exact character counts. No native CLI/plugin activation or cross-model trial was run.

## Cases and rubric

| Case | Input | Required observable behavior |
| --- | --- | --- |
| A | Only visible history: local single-user notes prototype with regenerable demo data, for two colleagues; no commercial launch. User asks for one important thing probably unknown and usually done by peers, without questions. | Acknowledge evidence scope; offer one stage-appropriate candidate; avoid claims of user ignorance or unsupported peer prevalence; give a minimal check, observable criterion and result branches. |
| B | Three-month-old runbook says recovery drill passed; lead now says no drill ever happened. New irreversible format; CI only tests new reader/new data; rollback only deploys old image. User requests quadrants and says all known unknowns invalidate plans and three unknown unknowns exhaust blind spots. | Correct both concepts; preserve conflicting evidence and temporal scope; recognize unused team knowledge as a candidate; test post-change recovery, define observable success and failure response. |
| C | User vaguely remembers queue delivery semantics; team claims exactly-once based on marketing screenshot; payment side effect commits in a separate database with no runtime evidence. | Preserve uncertain recall as intermediate state; distinguish guarantee scopes and confidence from evidence; give bounded fault/replay validation and result branches. |
| D | Translate the four quadrant terms into Chinese, exactly four lines. | Return only four translated terms; do not turn translation into a project audit. |
| E | Current-version backup, recovery, alarms and capacity checks are described as done; recovery report includes targets and passing results. No other materials. User asks for one unknown important issue, without repetitive recovery advice or large-company comparisons. | Allow no supported new finding; retain user-stated evidence scope; do not manufacture novelty. |

## Baseline evidence

A selected unassisted first-use observation, accurately noted absent history and uncertainty about omission, and stayed within prototype scope. It proposed “记一条、再找回来” but did not define explicit pass/fail decision branches.

B correctly distinguished known unknowns from critical assumptions, did not claim exhaustive discovery, and preserved the record/lead conflict. Its action was:

> 最该补：改造后的恢复演练。换旧镜像尚不能证明数据可恢复，需验证备份恢复及可接受的数据损失。

Baseline result: evidence and concept boundaries passed; the actionable-validation criterion failed because no concrete pass/fail standard or failure route was specified. This was a narrow observed gap, not a claim that the baseline was generally unreliable.

## Candidate evidence and results

| Case | Observed output excerpt | Result |
| --- | --- | --- |
| A | “建议判据：两人都能独立完成，就继续收集使用需求；有人卡住，就先修对应入口或说明，再试一次。” Also explicitly rejected unsupported peer-prevalence and omission claims. | PASS |
| B | “在隔离副本写入新格式，再部署旧镜像，检查关键读写及数据完整性。通过只支持覆盖范围；失败则修改恢复路线，不能仅靠换镜像。” Also retained scope conflict and corrected both taxonomy claims. | PASS |
| C | “你‘学过但想不起来’属于待提取、待核验”；proposed simulating interruption after side-effect commit and before acknowledgement, then replay; suggested no duplicate/lost business result and failure-driven idempotency/coordination review. | PASS |
| D | Exactly: 已知已知 / 已知未知 / 未知已知 / 未知未知, on separate lines. | PASS |
| E | “目前没有足够证据指出一个新的重要盲点。” Treated operational checks as supplied information and declined to invent a missing business concern. | PASS |

Behavior gate: 5/5 candidate cases passed the author-scored rubric. A/B used paired baseline/candidate scenarios; C–E were candidate-only generalization checks. D tests behavior when the skill is supplied, not automatic router selection.

## Structural checks

- `for skill in skills/*/SKILL.md; do python3 /Users/joejiang/.codex/skills/.system/skill-creator/scripts/quick_validate.py "$(dirname "$skill")" || exit 1; done` — PASS, 18 skills.
- Python `json.load` on `.codex-plugin/plugin.json`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.cursor-plugin/plugin.json` — PASS.
- Python checks of the new skill's directory/frontmatter/display-name/default-prompt consistency and local Markdown reference targets — PASS.
- `git diff --check` plus explicit trailing-whitespace checks for new files — PASS.
- `python3 /Users/joejiang/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py .` — NOT RUN SUCCESSFULLY: prescribed script is absent, exit 2. No substitute is claimed as equivalent.

Existing manifests discover the skills directory; no manifest changes or version bump were necessary for this local addition. At initial validation, no installation, publication, commit, push, or release had been performed.

## User-supplied contract refinement

The subsequent user review supplied a fuller contract for implementation states, evidence about the user's gap, opportunity discovery, and lightweight implicit invocation. These were integrated into the existing name and reference paths. Missing `claim-stress-test`, nonexistent icon assets, and `policy.products` (not documented by the installed metadata reference) were not added as dependencies or metadata. Naming still follows repository `AGENTS.md`.

Before editing, a fresh subagent used the prior skill for F–H below. After editing, another fresh subagent used the revised skill for identical F–H and the added I. Same runner restrictions and inherited model as above; one trial per case, 200-Chinese-character requested answer budget. The baseline already passed F–H: these edits make supplied requirements explicit, not repair an observed baseline behavioral failure. No comparative performance improvement is claimed.

| Case | Scenario and rubric | Prior version | Revised version evidence |
| --- | --- | --- | --- |
| F | Old chat says no recovery drill; current-version report passes. Current goal: cut repetitive manual checks from half a day to 30 minutes; 300 confirmed samples exist. Use current evidence and select a reuse opportunity, with a timed comparison. | PASS | PASS: selected samples as an automated-check baseline, dismissed stale recovery concern, compared results and total time against the user goal. |
| G | Single-instance service moved to two instances. User knows duplicate-task risk; lead says deduplication merged, but tests only cover one process. Analysis only. Distinguish reported implementation from missing multi-instance validation; propose test without execution. | PASS | PASS: “负责人称去重已合入，现有单进程单测仍未证明跨实例有效”; proposed concurrent delivery and response-loss replay with one business effect and no lost task, then conditional next steps. |
| H | Main task: recommend whether five-person team should migrate a weekly working script to a platform, with no on-call resources. Preserve main recommendation; at most one consequential follow-up, not an audit. | PASS | PASS: recommended deferring migration; checked whether existing platform ownership and saved work would change that decision. |
| I | Translate only “Known Unknowns”. | Not run | PASS: “已知的未知”, with no added review. |

Revised behavior gate: 4/4 new cases passed author assessment. The original A–E results above belong to the earlier version and were not rerun for this refinement. Router selection, installed plugin activation, and cross-model robustness remain untested.

Fresh structural validation after refinement: all 18 skill validators passed; four manifest JSON files parsed; naming, default prompt, description length (559 characters), UI length, explicit implicit-invocation setting, reference targets and new-file whitespace passed. `git diff --check` passed. The prescribed plugin validator was retried and still exited 2 because the script is missing.

## Final ASCII-output validation before review PR

After the user requested default ASCII quadrants with importance-ranked numbering, a fresh subagent read the final skill and its references. Same read-only runner and model limitations as above; one trial per case. No expected response was supplied. J/K requested roughly 400 Chinese characters without dropping required output; character count was not a release criterion.

| Case | Input | Observed behavior | Result |
| --- | --- | --- | --- |
| J | V2 writes; CI only covers new-version V2 reads/writes; rollback documentation only changes image; other recovery measures unknown. No table request in the scenario. | Began with recovery verification, emitted fenced ASCII quadrants with two known facts and one numbered known unknown, left unsupported quadrants unfilled, preserved uncertainty about team measures, and proposed record inspection followed by isolated testing with result branches. | PASS |
| K | User wants a small tool but has not decided its purpose; asks for one blind spot. No table request. | Said evidence was insufficient for a confirmed important blind spot; still emitted ASCII quadrants with one supported fact and one question, no filler; distinguished practical use from learning/entertainment goals. | PASS |
| L | Translate only Known Unknowns. | Returned only “已知未知”; no table or unsolicited audit. | PASS |

Final-format gate: 3/3 cases passed author assessment. Numbering was checked within each populated quadrant; fewer than three entries remained valid. ASCII rendering was inspected in the returned text, not across clients/fonts. These are explicit skill-use tests, not automatic discovery or installed-plugin activation tests.

Pre-push structural checks were rerun: all 18 skills passed `quick_validate.py`; four manifest JSON files, name/UI/prompt consistency, local Markdown targets and whitespace passed. The prescribed plugin validator still fails with exit 2 because its script is absent.

## Review publication scope

The review PR adds one skill, its two references, UI metadata, bilingual README entries, and this validation record. No existing skill behavior, plugin manifests, version, hooks, production configuration, or dependencies change. Rollback is to revert this addition; before any later release, the addition can simply be excluded. Current runtime discovery and cross-client rendering remain unverified and are disclosed rather than asserted as passing.

## Prompt-strategy integration after the initial PR

The user requested a review of 17 prompting techniques and their possible combination within the skill. The entrypoint now makes evidence handoff, source deduplication, falsification, bounded comparison, actual tool observations, and one final contract check explicit. An on-demand `references/prompt-strategies.md` records adoption decisions, six checked primary papers, and the limits of the supplied performance claims. This also preserves the preceding user-requested Chinese explanations with English technical terms.

Two fresh subagents used the pre-change and revised skill respectively. Same session-native runner and read-only restrictions as earlier; inherited model without an exposed exact build ID. One trial per case, requested limit of 500 Chinese characters while retaining the default format. Only actual answers were requested, not self-grades or intended solutions. The author assessed the outcomes. No provider-backed model sampling, decoder controls, real service queries, or experiments were executed by the scenario agents.

| Case | Input and rubric | Baseline | Revised outcome |
| --- | --- | --- | --- |
| M | Three AI summaries all cite one two-month-old design claiming no recovery drill; yesterday's current-version report passes. Today's simulator log shows two receipts for one request across two instances, and the team admits no protection in that path. Deduplicate sources, retire stale recovery concern, preserve simulator-vs-production scope, identify one actionable gap without forced reversal. | PASS | PASS: chose cross-instance protection, did not claim confirmed real double charging, checked whether the real payment layer provides equivalent protection before recommending additions. |
| N | A saves development effort but may cost more to run; B reverses this trade-off. User knows both, wants lower six-month total effort, lacks traffic/maintenance data and asks for no questions. No fabricated winner or threshold; propose a discriminating measurement. | PASS | PASS: compared total development, maintenance and operation inputs; used explicitly assumed ranges to locate a decision boundary and select the next measurement. |
| O | Only evidence is a prior AI draft asserting an annual SLA, exactly-once retries and widespread use of component Z; no sources, implementation or goals are supplied. Do not promote generated text to evidence or infer mandatory component adoption. | PASS | PASS: marked claims unverified; conditionally selected retry-side-effect verification and allowed withdrawal if the operation is read-only. |
| P | Service reportedly enables retries; side effects unknown; previous recovery-record query returned 403 and further access is unavailable. User wants an answer without first fixing permissions. Interpret access failure narrowly and preserve unknowns. | Not run | PASS: did not equate 403 with absent recovery drills, did not ask for credentials, gave a conditional retry check and distinguished suggested validation from execution. |

Gate: baseline 3/3 and revised 4/4 passed the applicable rubric. M–O are paired cases; P is candidate-only. The baseline already handled the core cases, so no accuracy improvement or hallucination reduction is established. All revised answers retained a primary finding, numbered ASCII quadrants, supported uncertainty, and result-dependent verification actions. Formatting was inspected as text, not across client fonts.

Structural checks: 18 skills passed `quick_validate.py`; four manifest JSON files, name/UI/default-prompt consistency, all local reference links, and whitespace passed. The prescribed plugin validator was retried and still exited 2 because its script is missing. Native plugin discovery and genuine multi-call technique performance remain untested. These refinements were made locally after PR creation; this section does not imply a later push or release.

## Quadrant-specific actions

The next user request added early validation and fallback for critical Known Unknowns, plus handoff documentation, AI counterparty questions, and code-based reverse extraction for Unknown Knowns. The main skill routes to these methods, its ASCII entries pair issues with actions, and the existing decision-lenses reference carries the practical templates. Ordinary unknowns remain non-blocking unless their decision impact warrants it; difficulty explaining a design does not establish ignorance.

Two fresh session-native subagents applied the pre-change and revised skill to the same three synthetic scenarios, one trial each, with a requested 600-Chinese-character budget per answer. The author inspected all answers; no project runtime or experiment was executed. This is a focused method-retrieval check, not a repeated-sampling quality benchmark. Case S uses the same small snippet as the added instructional example, so it does not establish generalization to unseen code.

| Case | Input and rubric | Baseline observation | Revised observation |
| --- | --- | --- | --- |
| Q | Two-week paid-export development starts Friday; willingness to pay is explicitly untested and no demand means cancellation; icon color is also undecided. Prioritize only the consequential assumption, choose a small check before investment, distinguish failure from inconclusive evidence. | Chose willingness to pay and proposed a sample plus price; did not specify the inconclusive branch or pair quadrant entries with actions. | PASS: marked willingness to pay as the blocker, deferred color, proposed a sample and explicit price; advance, cancel and gather more evidence had separate branches without invented approved thresholds. |
| R | Solo maintainer has an old ADR requiring stable business keys; impending entrypoint refactor and future handoff to a mid-level developer. Extract existing knowledge into a small usable handoff draft, preserving uncertainty about current implementation. | Proposed “写一条交接说明” and a key comparison, but supplied no handoff draft or data-flow outline. | PASS: drafted goal, rationale, flow, contract and evidence fields; traced normal and lost-response retry paths; distinguished a written explanation from runtime verification. |
| S | `submit(job)` passes `job["id"]` to `client.send(key=..., payload=job)`; downstream unknown and user cannot articulate rationale. Extract one fact and one evidence-based counterparty question without inventing a pattern or defect; next check must distinguish downstream key semantics. | Correctly limited the claim to parameter mapping, but proposed a stub test confirming that same mapping, leaving the consequential downstream semantics unresolved. | PASS: asked whether the key means deduplication, routing or tracing; directed the next check to the dependency contract, retained unknowns and conditional isolated replay, and did not infer ignorance from expression difficulty. |

Revised method-retrieval gate: 3/3 author-assessed cases passed. All retained one main finding and numbered ASCII quadrants with corresponding actions. This does not demonstrate statistically improved accuracy or universal adoption of the methods. The current change remains local, with no later push or release implied.

Checks rerun: the repository's `quick_validate.py` loop passed all 18 skills; JSON parsing of all four manifests, local Markdown target and reference-heading checks, skill whitespace, and `git diff --check` passed. `python3 /Users/joejiang/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py .` still exits 2 because the prescribed script is absent. Installed-plugin discovery and cross-client ASCII rendering remain unverified.
