# Investigation Report Format

Use stable IDs to connect contracts, candidates, commands, and evidence artifacts. Keep one record per candidate even after exclusion or deduplication. Scale narrative detail to the finding; retain the fields needed to audit its conclusion. These are reusable field definitions, not completed findings.

## Run and Coverage

Record:

- Target repository/revision and relevant uncommitted changes; investigated package/build identity if different.
- Requested scope, execution budget, actual stopping reason, and completed versus proposed checks.
- Platform, dependencies, build/install method, effective configuration, and relevant operation/cache state. For supplied evidence, identify its originating run separately from the current environment.
- Paths to the report, reproducers, raw output, traces, and generated artifacts. Exclude credentials and unrelated data from evidence bundles.

### Project Map

| Area / workflow | Public entry points | Module / language boundaries | Configuration sources | Produced / consumed artifacts | Test entry points |
| --- | --- | --- | --- | --- | --- |

### Contract Inventory

| Contract ID / group | Promise and exact source | Applicable version / conditions | Connected files, symbols, artifacts, or events | Unresolved interpretation |
| --- | --- | --- | --- | --- |

### Coverage Boundary

| Contract group / workflow | Scenarios actually checked | Methods and evidence IDs | Result | Unchecked scope and reason / next check |
| --- | --- | --- | --- | --- |

Differentiate inspected, executed, blocked, and inapplicable areas. List relevant unexamined groups even when the investigation focused elsewhere. Passing tests and no findings describe only the checked scope.

## Findings Overview and Severity

For one confirmed finding, the detailed record can follow the result count directly. For multiple confirmed findings, start with this overview, followed by an independent record for each finding. Keep unconfirmed candidates outside the confirmed total.

| ID | Issue | Severity | Defect type | User impact | Status | Root cause |
| --- | --- | --- | --- | --- | --- | --- |

Use these five severity labels, ordered from greatest to least impact. Base the assignment on demonstrated consequences, affected workflows, scope, and practical workarounds; give a short rationale in the detailed record. If the target project defines these labels, cite and apply its definitions; otherwise use the defaults below.

| Severity | Default impact criterion |
| --- | --- |
| Blocker | A core supported workflow cannot complete with no practical workaround, or the defect causes unrecoverable data loss/corruption. State the affected scope; do not imply all users are affected. |
| Major | An important capability is unusable or materially incorrect, with substantial user impact. The evidence does not meet Blocker criteria; any workaround is costly or significantly limits the capability. |
| Medium | A functional defect has bounded impact on a secondary path, or a practical workaround preserves the important workflow. Core results and operations outside the stated scope remain usable. |
| Minor | A low-impact edge case or usability defect causes limited inconvenience, with core results intact and easy recovery or avoidance. |
| Trivial | A cosmetic, wording, or presentation inconsistency has no functional impact. It must still violate an applicable contract; a style preference alone is not a defect. |

Severity describes the defect's impact, not confidence, root-cause certainty, repair effort, or investigation priority. A confirmed severe failure can have an unknown root cause. **BLOCKED** means verification cannot proceed; it does not imply **Blocker** severity. Conversely, missing an optional tool does not reduce a confirmed defect's severity.

If impact cannot be established, use `— (impact unverified)` instead of guessing a level. An unconfirmed candidate may carry an explicitly provisional severity only when supported impact evidence permits it; exclusion makes severity inapplicable. Do not turn hypothetical worst-case effects into established impact or lower severity merely because the defect is difficult to reproduce.

## Candidate Pool

| ID | Contract / compared objects | Specific conflict hypothesis | Supporting evidence | Alternative explanation | Priority rationale | Next check | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |

Use impact, contract clarity, reachability, and cost in the priority rationale; no artificial score is required. Empty areas need no invented candidates. A coverage gap can remain a gap without becoming a defect record.

## Independent Finding Record

Copy this field structure for each candidate worth investigating:

```text
ID and title:
Status: CONFIRMED | UNVERIFIED | EXCLUDED | BLOCKED
Severity: Blocker | Major | Medium | Minor | Trivial; unassigned if impact is unknown
Severity rationale:
  Demonstrated consequence, affected scope, practical workaround or its absence;
  cite project definitions if used and label any candidate rating provisional.
Contract group and basis:
  Promise, source path/line or versioned URL, applicable version/conditions.
Applicability and reachability:
  Revision/build/package, dependencies, platform/device, configuration,
  installation/loading, input, operation order, cache state, public entry point.
Compared objects:
  Files, symbols, caller/callee, artifacts, or runtime events.
Conflict hypothesis:
  Expected behavior, observed or suspected divergence, and user impact.
Verification:
  Evidence IDs, minimal reproducer, exact command and working directory,
  environment/setup, control, expected result, actual output and exit status.
  Label executed checks, supplied records, source proof, and proposed checks.
Alternative explanations / counter-evidence:
  What was checked, rejected, or remains unresolved, and why.
Conclusion and attribution:
  Established violation or reason for exclusion/blocking; implementation,
  documentation, example, test, delivery, or unresolved component.
Evidence strength and limits:
  What the records directly prove; assumptions and unverified applicability.
Root cause: established | hypothesis | unknown
  Mechanism and evidence if established; otherwise the missing causal link.
Impact and remaining questions:
  Affected workflows supported by evidence; no unsupported prevalence claims.
Related / duplicate IDs:
  Shared demonstrated violation or provisional relationship; preserve evidence.
Next useful action:
  Smallest missing check or follow-up requested by the user.
```

For trace evidence, also record the loaded artifact identity, observation point, probe source/command, positive control, correlation scheme, loss/coverage diagnostics, and interpretation limits. Unknown values stay unknown; do not fill them from a different build or run.

## Status and Causal Confidence

| Status | Required justification |
| --- | --- |
| CONFIRMED / 已确认 | Applicable promise, reachable conditions, and sufficient evidence of violation. Source proof must close the relevant path and exclude dynamic alternatives; supplied records must retain their provenance. |
| UNVERIFIED / 待验证 | Concrete conflict hypothesis with an identifiable missing proof. |
| EXCLUDED / 已排除 | Evidence for permitted behavior, inapplicable contract, wrong expectation, or another explanation that refutes this candidate. |
| BLOCKED / 受阻 | Exact missing environment/dependency/device/observation and the check it prevents. |

Root-cause confidence is independent of status: a public result may be demonstrably wrong while its faulty layer remains unknown. If an alleged implementation defect is instead an incorrect current example or test, exclude that allegation and create or link the correctly attributed finding.

## Final Delivery Order

1. State confirmed findings and user impact, including an explicit zero when none are established. For multiple findings, include the overview with its Severity column; retain severity and its rationale in every detailed finding.
2. Provide each independent record and its reproducible evidence. Link raw artifacts; distinguish executed commands from suggested reproductions.
3. List unresolved, excluded, blocked, and duplicate candidates with their dispositions, keeping confirmed totals separate.
4. Report checked and uncovered scope, observation limits, stopping reason, and the next useful checks.

Do not turn a number of candidates into a bug count. Do not claim fixes, commits, issue publication, or release validation that were neither requested nor performed.
