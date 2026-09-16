---
name: find-a-bug
description: Use when a user asks to find a bug in a project, investigate a failure, diagnose unexpected behavior, or locate the cause of a regression, flaky test, hang, incorrect output, or build/runtime error. Also applies to bounded defect reviews without a supplied symptom.
---

# Find a Bug: Uncertainty-First Defect Investigation

Separate verified facts, user statements, inferences, and unknowns before acting. Prioritize evidence that could disprove the current approach. The goal is to identify an evidence-backed defect and decide what to do next. Finding no confirmed defect is a valid outcome; never invent a bug to satisfy a delivery expectation.

Apply this workflow across languages, frameworks, build systems, data pipelines, and runtime environments. Do not assume a repository layout, tool, platform, version, or failure cause. Respond in the user's language. Style preferences, refactoring suggestions, and general option comparisons must not be presented as defect investigations.

## 1. Define the Actual Decision and Investigation Scope

Frame the task as an action, such as: "Should this input-handling path change, or should we first correct the test contract or runtime environment?" Establish expected behavior, observed behavior, success criteria, impact, reversibility, and constraints on time, cost, permissions, safety, and compatibility.

- **A failure symptom is available:** Start from the specific input, terminal error, failure record, or behavioral difference. Preserve the raw evidence.
- **No failure symptom is available:** Read the project documentation, entry points, tests, and recent changes. Select one important, testable execution path. State the scope of this investigation; do not claim that the entire repository is defect-free.
- **The user requested investigation only:** Deliver findings and evidence. **The user already requested a fix:** Continue with the fix once evidence and execution gates permit it; do not request authorization already granted. A request to find a bug does not itself authorize deployment, deletion, or external communication.

Identify the project from its files and actual state: repository instructions, working-tree changes, revision, dependency locks, build configuration, test entry points, runtime, and deployment records. Verify what available artifacts can answer before asking the user to complete a questionnaire. Preserve existing working-tree changes.

| Project signals | Contracts and boundaries to verify first |
|---|---|
| Frontend, mobile, interactive applications | Event → state → asynchronous result → rendering; input, lifecycle, cancellation, and race conditions |
| Services, libraries, command-line interfaces (CLI) | Caller → arguments/defaults → processing → return/error; null values, zero values, and persisted formats |
| Native code, build tools | Compiler options, application binary interface (ABI), platform, resource lifecycle, and the artifact actually loaded |
| Data, machine learning (ML), graphics processing unit (GPU) projects | Data/model versions, tensor shape, data type (`dtype`), devices, and dependencies; assess each stage's success separately |
| Continuous integration (CI), scripts, configuration, agent skills | Trigger → arguments/environment → subprocess or tool → exit/cleanup; output contracts and actual execution records |

Use only checks relevant to the target project. Discover commands from project files rather than inventing test entry points from ecosystem conventions. A missing tool is a verification limitation, not a product defect.

## 2. Maintain an Evidence Ledger

For each entry, record its source, applicability, and the action it could change. Write "None" for an empty category.

| Category | Meaning and evidence requirements |
|---|---|
| VERIFIED | Directly verified through files, logs, tests, tools, or authoritative records. Cite a path/line or command result, together with the relevant version, environment, run instance, and time. |
| USER-STATED | Explicitly provided by the user or responsible owner, but not independently verified. Preserve attribution. |
| INFERRED | State which facts support the inference, which assumptions must still hold, and what evidence would disprove it. |
| UNKNOWN | Missing, conflicting, stale, inaccessible, or unconfirmed information. State how it could be verified. |

Verifying a file's contents does not prove that the runtime used it. The current configuration is not necessarily the configuration used by the failed job. Old logs, other platforms, and other revisions establish facts only within their own scope. Missing logs do not prove an event never occurred. One unsuccessful reproduction does not prove the absence of a defect. Never promote an inference to a verified fact.

## 3. Scan for Hidden Unknowns and Disconfirming Evidence

Check the objective metric; target/version/environment/time boundaries; input completeness and representativeness; upstream and downstream dependencies and interfaces; read/modify/execute/rollback permissions; actual system state; platform/hardware/configuration compatibility; empty, large, and unusual inputs; concurrency; owners and recipients; information freshness; reversibility; and observability of success, failure, and partial failure.

Skip inapplicable items and enter unresolved items in the ledger. Run a premortem: "If this investigation or fix fails, what overlooked fact is most likely responsible?" Then ask: "What evidence would show that the current problem definition or preferred explanation is wrong?" Seek that evidence first, especially at interfaces, boundaries, dependencies, and actual runtime state.

## 4. Keep Competing Hypotheses and Identify Decision-Critical Unknowns

Until the evidence converges, retain **2–4 plausible branches that would lead to different actions**. For each, state its necessary conditions, supporting evidence, opposing evidence, missing evidence, and the action to take if it holds. Close disproven branches with the supporting rationale; do not invent causes to meet a quota.

Trace the causal chain: **input/trigger → state or transformation → first contract violation → downstream symptom**. The final stack frame, last test name, timeout, or outer exception often locates a symptom. A root-cause claim must explain which step violates which contract and how it produces the observed result. Also test whether the expected behavior itself has been defined incorrectly.

Select the **top 1–3** decision-critical variables from UNKNOWN. Each must satisfy all three conditions: different outcomes change the action; an incorrect judgment has a material impact; and a question, query, experiment, or observation can reduce uncertainty. Rank them qualitatively using "likelihood of changing the decision × impact × actionability ÷ verification cost." Use High/Medium/Low with reasons; do not fabricate probabilities or scores.

## 5. Design Minimal Discriminating Tests

Define the decision rules first, then run the cheapest effective check: one configuration or call site, one authoritative record, one minimal input, one existing test, or a small reversible experiment. Change only the variable needed to distinguish the branches at each step.

Each test must specify:

- Target, environment, input, expected contract and its source; where the command came from and whether it was actually executed.
- **Result X → action A; result Y → action B; inconclusive → verify Z or stop.** Derive thresholds from the contract or an explicit experimental design. Do not change them after seeing the result.
- Time/resource budget, stopping conditions, possible side effects, and recovery method.

Prefer existing project tests. When a reproduction is needed, remove irrelevant dependencies while preserving the trigger and control inputs. If execution is unavailable, perform bounded source analysis, identify unverified runtime conditions, and state the minimum missing evidence. Report test-environment failures, missing dependencies, and the target defect separately.

## 6. Apply Execution Gates

Choose **one gate per round**, bound to the immediate next action. Describe restrictions on other actions in ordinary prose rather than listing multiple gate states. Use TEST FIRST when evidence is insufficient but verification remains feasible; do not use STOP as a synonym for "not yet confirmed."

| Gate | Conditions and permitted next action |
|---|---|
| GO | Critical evidence, permissions, and success criteria for this action are sufficient. Execute the authorized action and verify the result. |
| TEST FIRST | A critical unknown can be checked at low cost. Perform the safe read or local test directly, then update the gate. |
| ASK USER | A decision-critical fact or permission cannot be verified independently. Ask at most 3 specific questions while continuing investigation that does not depend on the answers. |
| LIMITED EXPERIMENT | The action is low-risk and reversible. State assumptions, scope, verification method, and rollback path before conducting one bounded experiment. |
| STOP | Risk or permissions prohibit proceeding. State the blocking condition and what would allow investigation to resume. |

Do not execute an action when an unknown could reverse the plan, an incorrect judgment would have high impact, and the action is hard to roll back or involves production, safety, health, funds, deletion, overwriting, or external communication. First perform safe verification or request the critical input. Do not indefinitely block reversible investigation over low-value unknowns. Do not reconfirm existing authorization, but remember that authorization does not establish missing facts.

Compare cost, performance, or option scores only after the critical path and hard gates are clear. An aggregate score cannot compensate for failed correctness, safety, permissions, or required rollback conditions.

## 7. Converge, Deliver, and Fix When Authorized

Distinguish **Confirmed Defect / Unverified Candidate / No Confirmed Defect Found in This Investigation**. A confirmed defect must include its location, trigger, expected versus actual behavior, causal explanation, evidence, impact scope, and verification limits. Specify whether the evidence comes from runtime reproduction, existing tests, or proof from source and contract. Do not present source analysis as an executed test.

When a fix is authorized and the gate permits it, make the smallest change that addresses the established causal chain. Verify with the triggering input and relevant control/regression cases. Report the change, checks actually performed, and remaining limitations. If evidence contradicts expectations, stop layering on fixes and return to the ledger and branches. Revert only your own experiments or changes; do not overwrite the user's work.

Stop researching when additional information can no longer change the current action. When the budget is exhausted or verification is inaccessible, deliver the supported conclusions, coverage boundaries, open questions, and next checkpoint. Do not expand into an unlimited audit or translate "not found" into "no bug exists."

## Output Contract

Use the following order for each planning round and final delivery. A simple section may contain just one sentence. Report auditable evidence and decision rationale without exposing internal deliberation.

### Actual Decision

The action to investigate or decide in this round, its scope, success criteria, and constraints.

### Current Assessment

The current default approach and supporting evidence. In the final delivery, include the defect conclusion, location, trigger, expected/actual behavior, impact, and evidence type.

### Evidence Ledger

List VERIFIED, USER-STATED, INFERRED, and UNKNOWN separately, with sources and applicability.

### Competing Hypotheses

For each branch, give its necessary conditions, supporting/opposing/missing evidence, and resulting action. Include the premortem and evidence that could disprove the current approach.

### Top Decision-Critical Unknowns

Give the top 1–3, ranking rationale, how each could change the decision, impact, minimal verification, and predeclared X/Y/inconclusive rules. Explicitly write "None" if no action-relevant unknown remains.

### Current Gate

Choose exactly one of GO / TEST FIRST / ASK USER / LIMITED EXPERIMENT / STOP. Identify the next action and why this gate applies.

### Execution Plan

After passing the gate, list the action, verification, stopping conditions, rollback method, and next checkpoint. Before passing it, list only permitted verification or outstanding questions; do not elaborate a complete repair plan that depends on unknown premises. Distinguish completed actions from pending actions in the final delivery.

### Residual Risks

Unresolved uncertainties that do not block the current action, plus versions, platforms, inputs, or runtime environments not covered.

## Example: Is Zero-Value Handling Actually a Bug?

Request: "Inspect the pagination function and find a bug." The source uses `limit = limit or 100`, while the documentation specifies that `limit=0` returns an empty list.

The source and documentation contents are VERIFIED. Whether a caller can pass 0 remains UNKNOWN until the entry point is checked. Branch one: 0 is reachable, so the default-value logic violates the contract; investigate that assignment. Branch two: the public entry point rejects 0, so establish which layer the contract applies to before claiming user impact.

Inspect the public entry point, then predeclare the test: call the public application programming interface (API) with valid zero-valued input. A nonempty result confirms the boundary defect; an empty result rules out this candidate; an unavailable runtime leaves a source-level candidate with explicit limits. Use an ordinary positive value as a control. A read-only investigation can be GO; a test can be TEST FIRST. Reporting a confirmed defect does not automatically authorize a fix.

## Common Mistakes and Corrections

| Mistake or rationalization | Correction |
|---|---|
| "The owner has investigated for hours; accept their root cause." | It remains USER-STATED. Seek evidence that could disprove it first. |
| "We read the configuration file, so the failed job used it." | Verify the historical version, override sources, and run instance. Otherwise the effective runtime configuration remains UNKNOWN. |
| "Collect enough logs and the cause will emerge." | Select the top decision-critical unknowns and define result-to-action rules before deciding what to collect. |
| "It did not reproduce, so there is no bug." | This only establishes that the defect did not reproduce under the tested conditions. Preserve coverage boundaries. |
| "We must report a bug within ten minutes." | Deliver a bounded conclusion and next checkpoint without lowering the evidence standard. |
| "Fix it first; collect evidence afterward." | Return to the causal chain, authorization, and gate. Stop changes unsupported by evidence. |
