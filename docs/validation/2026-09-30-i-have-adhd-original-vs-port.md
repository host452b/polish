# i-have-adhd: original versus selective port

## Conclusion

The selected core capabilities show no observed regression in this basic
comparison: complete information, truthful verification boundaries, exact
output contracts, executable instructions, and actual authorized local edits.
The port is not behaviorally identical to the original.

Under the predeclared case rubric, the original passed 9/12 responses and the
port passed 12/12. Two original failures concern unsupported time estimates;
one concerns inconsistent prioritized next actions. All mechanical output,
item/command retention, and fixture checks passed for both conditions.

The timing criterion reflects the agreed adaptation's evidence requirement.
The original explicitly encourages concrete estimates, so those failures
demonstrate a contract difference, not a claim that its executable commands
were wrong. Two repetitions are insufficient to establish statistical
equivalence, a general quality ranking, or improvement across models.

## Compared inputs and method

| Input | Revision / identity |
| --- | --- |
| Original | `ayghri/i-have-adhd` at `839872f9d1cd634fed642b4589ce7226199cc15f`, `skills/i-have-adhd/SKILL.md` |
| Port | `skills/i-have-adhd-actionable-output/SKILL.md` in this working tree |
| Original SHA-256 | `3170b16ace00aecb0dd7feb54c0b5aa642e7502acda06ecd24fd89a11c7127e9` |
| Port SHA-256 | `dcda9b1b0264a520d61afa0965945f811bb290a9f1ed1db3d4720b1d625e9d0e` |

Both complete skill files were snapshotted before execution and checked
against the unchanged source files afterward. Both were explicitly applied;
automatic invocation was not exercised.

The runner was `collaboration.spawn_agent`, without model or effort overrides.
Exact model/build, seed, provider cost, and token usage are not exposed by the
tool results. Four fresh workers (`fork_turns="none"`) ran two repetitions per
condition. Each worker handled the same six case requests; cases share context
inside a worker. This yields 24 response artifacts, not 24 independent contexts.

Workers saw their skill, the common case requests, and an isolated fixture.
They did not see the other variant, prior authoring conversation, rubric, or
other responses. They could only write their own answers and the authorized
fixture configuration. No networking or real user configuration was involved.

Criteria were written before execution. The author inspected raw responses,
parsed exact outputs, and independently reran all four fixture verifiers.
A fifth fresh agent reviewed anonymous A/B pairs against the rubric; label
assignments were reversed between repetitions and fixture paths normalized.
The blind reviewer did not see the skills or label map. The author then
decoded the results and checked the cited evidence.

## Case results

| Case | Shared request and required behavior | Original | Port |
| --- | --- | --- | --- |
| C1 handoff | Preserve all eight statuses, verification limits and unconfirmed root cause; give one consistent pending action | 1/2 | 2/2 |
| C2 JSON | Exactly `{"passed":9,"failed":2,"cause_confirmed":false}`, no wrapper | 2/2 | 2/2 |
| C3 completed answer | `17+25`, number only, no appended next step | 2/2 | 2/2 |
| C4 explanation | Explain C01-C08 input categories, one check each, two complete JSON examples with explicit missing/null semantics | 2/2 | 2/2 |
| C5 manual steps | Six exact commands, numbered actions, test-success startup gate, first failure retained, no unsupported duration claim | 0/2 | 2/2 |
| C6 actual edit | Change only `batch_size` from 4 to 8 and run the existing verifier | 2/2 | 2/2 |

C1 uses supplied notes: login code changed with six passing unit tests but no
browser check; refresh fails at line 42 with expected 200 / actual 401 and no
header log; timeout copy changed but untested; CSV documentation changed but
implementation untouched/unverified; dark mode half-written; keyboard, mobile,
and screen-reader work not started. A lead suspects a missing Authorization
header. Unrelated dependency and README work is outside scope.

C4 covers empty string, whitespace, Unicode, overlong input, zero, negative
numbers, missing fields, and null. Every response preserves all eight items
and gives two valid JSON objects under an explicit partial-update convention.

C5 supplies these ordered operations: `cd /tmp/demo`,
`python3 -m venv .venv`, `source .venv/bin/activate`,
`python3 -m pip install -r requirements.txt`, `python3 -m pytest`, then
`python3 app.py` only on test success. Device speed is unknown. Both conditions
retain every operation and the failure gate in both repetitions.

C6 uses separate but equivalent configurations with `batch_size: 4`,
`timeout_seconds: 30`, and `label: "local-fixture"`. All four agents actually
change only `batch_size` to 8. The unchanged verifiers independently pass with
exit code 0; the reported result stays within that local evidence.

## Observed differences and review findings

1. **Time estimates:** original C5 trial 1 adds “输入并执行约 10 秒”; trial 2
   adds “输入命令预计约 1–2 分钟”. Neither request provides a basis for these
   timings. The reviewer marks both as failures of C5's explicit timing
   criterion. Both still supply correct commands. The port supplies no estimate.
2. **Priority consistency:** original C1 trial 2 opens by prioritizing inspection
   of the failing request's header records, which the notes say are absent,
   then ends by prioritizing inspection of request-construction source. The
   response does not reconcile those different evidence-gathering operations.
   The port consistently assigns collection of the missing header evidence.
3. **Grouping and repetition:** the original splits eight-item inventories
   into smaller groups and often repeats the immediate next action at the end.
   The port uses one complete table and usually names the next action once.
   No item is lost in either condition; grouping alone is not a failure.
4. **Confirmed common behavior:** both preserve uncertain causality, distinguish
   passing unit tests from browser validation, honor JSON/numeric-only output,
   give full explanations on request, and perform the authorized local edit.

Original C1 trial 1 also adds “定位检查约 2 分钟”. The reviewer records it as a
caveat, not another failure, because C1's declared completeness/status/action
criteria are met and C5 alone explicitly scores unsupported timing. This
case-specific scoring distinction is retained rather than changing the rubric
after observing results.

The reviewer could verify C6 narrative consistency against supplied fixture
checks, but did not receive full tool transcripts. Actual mutation and verifier
integrity were independently checked by the author; the blind review is not
claimed to audit every unseen interaction.

## Static differences outside the tested equivalence

| Contract | Original | Port |
| --- | --- | --- |
| Default scope | Rest of session, including topic changes | Current task; unrelated tasks require requested scope |
| Invocation | `disable-model-invocation: true`; Codex implicit invocation disabled | Narrow description-based discovery; no implicit-invocation prohibition |
| Lists | Target at most five items per group, with completeness safeguards | Group for readability without a fixed item count |
| Time | Concrete ballpark estimates encouraged | Estimate only when useful and supported by assumptions |
| Debug spiral | Explicit reassessment after three failed turns | General evidence/unknown handling; no fixed three-turn rule |

These are source-level contract observations, not runtime test results. Session
switching, automatic discovery, installed platform hooks, other models, and the
upstream release gate were not tested. A same-harness comparison can also mask
skill differences already constrained by higher-priority harness instructions.

## Reproduction and artifacts

Local evidence is under `/tmp/polish-adhd-equivalence/`:

- `cases.json`, `rubric.md`, and the two immutable skill snapshots;
- `original-1/`, `original-2/`, `ported-1/`, `ported-2/`: exact answers, fixtures,
  and execution records;
- `check.py`, `mechanical-results.json`, `blind-packets.json`,
  `blind-review.json`, `label-map.json`, and `decoded-results.json`.

`python3 /tmp/polish-adhd-equivalence/check.py` parses output contracts,
checks item/command retention and unchanged skill/verifier hashes, and reruns
the four fixture verifiers. All these checks passed. It does not replace the
semantic review recorded above. The directory is temporary evidence, not a
runtime dependency or a portable model-runner package.

Neither skill was changed to fit these cases. No commit, push, installation,
or external publication was performed during validation.
