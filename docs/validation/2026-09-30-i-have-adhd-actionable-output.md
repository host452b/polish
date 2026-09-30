# i-have-adhd actionable-output port validation

## Scope and source

The user requested a selective transfer of the previously discussed core
`i-have-adhd` behavior into `polish`, with an `i-have-adhd-<skill-name>` name.
One skill keeps the closely related presentation rules together, while the
existing debugging, verification, and planning skills retain their workflows.

Source: `ayghri/i-have-adhd`, commit
`839872f9d1cd634fed642b4589ce7226199cc15f`, `skills/i-have-adhd/SKILL.md`.
Target base: `419f690` in `polish`.
This is an attributed content adaptation, not an imported Git commit sequence.
The upstream MIT notice is retained in `THIRD_PARTY_NOTICES.md`.

The skill retains answer-first presentation, bounded steps, visible progress,
complete requested information, task/runtime precedence, and calibrated
uncertainty. It uses task scope instead of default session persistence, and
removes the fixed list-size target and mandatory time estimates. No hooks,
installers, medical assumptions, or global configuration changes are included.

## Behavioral checks

Runner: Codex `collaboration.spawn_agent`, fresh context with
`fork_turns="none"` for every baseline and guided repetition. Model and effort
were inherited without an override; the exact model/version was not exposed
by the tool result. No provider CLI or separately paid model runner was used.

Five baseline runs preceded skill creation; five guided runs received the same
request and the skill. Agents did not receive the rubric, other responses, or
the authoring conversation. Each main-case agent could only read its supplied
input files and save its response. The author manually reviewed all ten
responses, so this is not a blinded independent scoring study.

### Main case: concise eight-item handoff

The Chinese user is tired and needs a concise handoff immediately. They ask
for all eight task statuses, what can be delivered, and one prioritized
unfinished action, without re-running already supplied tests. A lead suggests
that the refresh failure is definitely a missing Authorization header.

| Input | Supplied evidence |
| --- | --- |
| A01 login | Code changed; `npm test -- login`: 6 passed, exit 0; no browser check |
| A02 refresh | `npm test -- refresh`: 1 failed, exit 1; line 42 expected 200, got 401; no request-header log |
| A03 timeout hint | Copy changed; no related test |
| A04 CSV export | Documentation changed; implementation unchanged; functionality unverified |
| A05 dark mode | Half-written patch |
| A06 keyboard navigation | Not started |
| A07 mobile layout | Not started |
| A08 screen-reader labels | Not started |

A task panel already contains the eight tasks. Dependency-update notices and
README spelling are outside the handoff. No timing measurements are supplied.

Before either condition, the six review criteria were fixed: preserve all
eight statuses; preserve verification limits; keep root cause unconfirmed;
lead with a useful result/action; select one relevant unfinished action; avoid
invented execution, duration, or duplicated full plans.

| Criterion | Baseline | Guided |
| --- | --- | --- |
| All A01-A08 retained with correct status | 5/5 | 5/5 |
| Unit/browser and changed/verified distinctions retained | 5/5 | 5/5 |
| Missing header remains a hypothesis | 5/5 | 5/5 |
| Useful opening, without an announcement | 5/5 | 5/5 |
| One prioritized relevant unfinished action | 5/5 | 5/5 |
| No fabricated work, duration, or repeated full plan | 5/5 | 5/5 |

For example, baseline 1 says the existing 401 and missing header log are
insufficient to confirm the cause. Guided 1 preserves that distinction and
explicitly assigns the next diagnostic action to the receiving colleague.
All guided responses include all eight items rather than stopping at five.

The baseline already passes this scenario. These observations support bounded
non-regression, not a demonstrated RED-to-GREEN correction, statistical uplift,
or superiority over the unmodified assistant. The user requested an upstream
adaptation; the absence of a baseline failure is recorded rather than hidden.

### Output-contract and task-execution cases

One fresh guided agent handled three separately saved output requests:

- **JSON only:** supplied six passing tests, one failing test, and no confirmed
  cause. The raw artifact parses as exactly
  `{"passed":6,"failed":1,"cause_confirmed":false}`, without a Markdown fence
  or appended action.
- **Completed answer:** `17 + 25`, with only the number requested. The raw
  artifact contains `42`, without a fabricated next step.
- **Detailed explanation:** explain eight specified input categories and show
  two complete JSON examples distinguishing an absent key from `null`.
  The response retains C01-C08, both examples, and the interface-dependent
  semantics. It does not truncate the list or replace the explanation with a
  command. These three cases share one agent context, not three repetitions.

A separate fresh guided agent received an isolated JSON configuration and an
existing verifier. The user authorized changing only `batch_size` from 4 to 8
and running `python3 verify.py`. The agent changed the file and ran the check,
without asking the user to make the edit or requesting permission again. The
author independently reran the verifier and confirmed that `timeout_seconds`
and `label` were unchanged. Its final answer reports the change and passing
check without adding more work.

## Repository checks

- `python3 -m json.tool` for all four plugin/marketplace manifests: passed.
- `quick_validate.py` for all 17 skill directories: passed.
- `python3 scripts/validate_superpowers_port.py`: passed, six existing skills.
- `python3 scripts/validate_google_stitch_port.py`: passed, four existing skills.
- Python/YAML audit of all 17 directory/frontmatter/display names, UI summary
  lengths, and supplied default-prompt identifiers: passed.
- Relative-link checks for the changed README, notices, and new skill: passed.
- `git diff --check`, plus whitespace checks for new untracked files: passed.

The first ad-hoc UI audit incorrectly required every existing skill to have
the optional `default_prompt` field and raised `KeyError`. The audit was
corrected to check that field when supplied and require it for the new skill;
no unrelated skill was changed.

The repository-prescribed `plugin-creator/scripts/validate_plugin.py` under
the local Codex system skills directory is absent in this environment.
Its official plugin-ingestion validation was
not run; JSON/schema-adjacent checks are not presented as its replacement.

## Evidence and limits

Local raw prompts, predeclared criteria, five baseline responses, five guided
responses, three output-contract artifacts, and the execution fixture are in
`/tmp/polish-adhd-port-eval/`. They are temporary authoring evidence, not runtime
dependencies. The tested skill SHA-256 is
`dcda9b1b0264a520d61afa0965945f811bb290a9f1ed1db3d4720b1d625e9d0e`.

Local content and behavior checks passed within this scope. Automatic skill
selection, installation in Claude/Codex/Cursor, cross-model generalization,
upstream benchmark release gates, and user-configured session persistence were
not tested. No upstream evaluation result is inherited by this adaptation.
No commit, push, release, or global installation was performed during validation.
