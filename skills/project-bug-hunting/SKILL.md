---
name: project-bug-hunting
description: Use when proactively exploring a C++, Python, or mixed-language repository for unknown functional defects or project-wide contract inconsistencies without a supplied failure or localized bug.
---

# Project Bug Hunting

Build an auditable chain: **what the project promises → what happens under applicable conditions → why the difference is a defect**. Explore the whole project, including its documentation, examples, interfaces, implementation, configuration, tests, and delivery artifacts. Machine learning frameworks are one application, not the scope boundary. Report in the user's language.

Use this for open-ended discovery. A supplied crash, failing test, or localized regression usually calls for focused debugging instead. Discovery delivers evidence and coverage; fixes, commits, and issue publication follow the user's requested scope.

## Keep Three Dimensions Separate

| Dimension | Decision |
| --- | --- |
| Contract relationship | What should agree, and which promise makes that agreement necessary? |
| Runtime scenario | Which version, dependencies, configuration, platform, operation sequence, installation mode, or cache state makes it applicable? |
| Verification method | What source analysis, static check, behavior test, or trace can distinguish the candidate from its alternatives? |

Start with a relationship, select a meaningful scenario, then choose sufficient evidence. Tools do not define additional contract groups. Do not expand these dimensions into an exhaustive Cartesian product.

## Exploration Loop

1. **Fix the baseline and budget.** Inspect repository instructions, revision and local changes, support claims, dependencies, build/test entry points, and available environments. Record the scope and time/resource limits supplied by the user. If unspecified, state a bounded initial pass and proceed; ask only when an unresolved choice changes what can be checked. Preserve existing changes and isolate experiments and generated artifacts.
2. **Map the project and its contracts.** Identify public entry points, major workflows, module/language boundaries, configuration sources, produced/consumed artifacts, and test entry points. Survey the seven groups in [Contract relationships](references/contracts.md); mark relevant, inapplicable, and unexamined areas. Record each promise's source, version, conditions, and connected components. Map broadly before concentrating on promising candidates.
3. **Maintain a candidate pool.** Read [Report format](references/report-format.md) when creating the ledger. Give each candidate a stable ID, specific conflict hypothesis, supporting evidence, alternative explanations, and next discriminating check. Prioritize user impact, clarity of the contract, reachable paths, and verification cost; avoid invented numeric scores. A scanner warning or suspicious pattern is a lead, not a finding.
4. **Check applicability and reachability.** Verify that the promise applies to the investigated revision and supported input/environment, and that a real public workflow reaches the suspected mismatch. Check migration notes, optional features, intentional differences between entry points, and which component is actually installed or loaded. An archived example is not automatically a current implementation contract.
5. **Verify one candidate at a time.** Trace the relevant source boundary, then run the smallest discriminating behavior check with a control. State expected outcomes before running it. Prefer the project's existing test framework; isolate new reproducers. Record commands, inputs, exit status, output, and artifact paths. If execution is unavailable, a complete source proof may suffice, but unresolved dispatch, support, or reachability leaves a candidate unconfirmed. Never describe source inspection as a run.
6. **Trace only an unresolved runtime question.** Read [Runtime evidence](references/runtime-tracing.md) before using native, Python, or GPU tracing. Define the contract, observation points, and expected events before attaching probes. Verify the loaded artifact and a known-hit control. Missing hits, lost events, or incomplete coverage are insufficient evidence for absence; observing an entry point does not prove correct completion. Unavailable tools leave an observation gap; continue other useful checks.
7. **Seek counter-evidence, attribute, and deduplicate.** Test permitted behavior, stale documentation, incorrect examples/assertions, environment differences, fallback policies, and packaging errors. Attribute the established defect to implementation, documentation, example, test, or delivery as evidence permits. Deduplicate a shared demonstrated violation; retain linked candidates when a common root cause is only suspected. Feed new leads back into the pool within budget.
8. **Deliver and stop at the boundary.** Report when the budget is reached, required conditions are missing, remaining candidates have no executable check, or further work cannot change the supported conclusions. Finish independent checks before treating a missing capability as a project-wide blocker. Never stop because a bug quota was met, invent findings to meet one, or equate an empty result with a defect-free project.

## Choose Evidence for the Question

| Method | When it helps | Limits |
| --- | --- | --- |
| Source/interface analysis | Definitions, call paths, types, configuration propagation; search, AST, headers/stubs, build information | Source presence alone does not establish runtime selection. |
| Static scanning | Candidate patterns; Ruff, Pyright, Cppcheck, clang-tidy, Infer as appropriate | Use actual project configuration; review diagnostics and public reachability. |
| Behavior tests | Public workflows, controls, combinations, round trips, state changes; existing tests, pytest, Hypothesis | Derive the oracle from the contract, including allowed tolerance or nondeterminism. |
| Test generation | Additional inputs and operation sequences; Pynguin where suitable | Audit generated assertions; recording today's output can preserve a bug. |
| Runtime tracing | Hidden paths, boundary values, call counts, resource events; bpftrace, uprobes/uretprobes, USDT, BCC | Validate observation and correlation before drawing conclusions. |
| Language/device observation | Python execution or GPU work; `sys.monitoring`, Nsight Systems | Language events, native calls, device completion, and output correctness are distinct evidence. |

Choose tools already useful for the target project; no tool is a prerequisite for the whole exploration. For an accepted-but-ineffective option, inspect propagation and compare public behavior first; add tracing only if an intermediate boundary remains unobservable.

## Evidence Standard and Delivery

Keep an independent record per candidate using the report format. It must contain the contract basis, applicable conditions, compared objects, conflict hypothesis, verification, alternative explanations, conclusion, user impact, severity and its rationale, evidence strength, and unresolved questions. Distinguish independently executed evidence from supplied records and proposed checks.

Include a **Severity** column in the findings overview and a severity field in each detailed finding: **Blocker / Major / Medium / Minor / Trivial**. Apply the impact definitions in the report format; severity is independent of finding status, root-cause confidence, and investigation priority. Leave it unassigned when impact evidence is insufficient.

| Status | Meaning |
| --- | --- |
| CONFIRMED / 已确认 | Evidence establishes a violation of an applicable contract. State whether proof is behavioral, source-based, or from supplied artifacts. |
| UNVERIFIED / 待验证 | A concrete lead exists, but evidence does not yet establish a violation. |
| EXCLUDED / 已排除 | Evidence refutes this candidate, for example intentional behavior or an incorrect test expectation. |
| BLOCKED / 受阻 | A named missing environment, dependency, device, or observation capability prevents the required check. |

Record **root cause: established / hypothesis / unknown** separately. A confirmed wrong result can have an unknown cause. Excluding an implementation candidate can create a separate confirmed documentation or test defect; do not silently discard the inconsistency.

Deliver the findings report, saved reproducible evidence, and checked/uncovered scope with reasons and useful next checks. A zero-finding report is valid. Passing tests cover only the exercised scenarios; unavailable tools provide neither findings nor a clean bill of health.
