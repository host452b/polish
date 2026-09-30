---
name: i-have-adhd-actionable-output
description: Use when the user requests ADHD-friendly or easier-to-follow answers, needs a concise actionable handoff, or asks to restructure a response whose conclusion, next steps, or progress are hard to find.
---

# i-have-adhd-actionable-output

Make the answer easy to find and act on while preserving the work and evidence
the task needs. Apply this presentation guidance to the current task. Continue
across unrelated tasks only when the user requests that scope; honor a request
to return to normal style. A diagnosis is neither required nor inferred.

## Match the task before shaping the answer

| Request | Response shape |
| --- | --- |
| A question | Answer or conclusion first, then supporting explanation |
| A command, path, or snippet | Put that artifact first |
| Work the agent can perform | Complete authorized work with available tools, then report the result |
| Steps the reader must perform | Number the necessary actions, one bounded action per step |
| A comparison or full inventory | Preserve requested options/items and distinctions; use groups or a table |
| An exact format, detailed explanation, or quotation | Follow that contract in full |

User requirements and higher-priority runtime instructions control the response.
Keep required tool announcements, safety checks, and meaningful caveats. This
skill changes presentation; it does not grant permission or introduce an
approval gate for work already authorized.

## Shape the response

1. **Lead with useful information.** Start with the answer, supported result, or
   next action. Replace announcements and ceremonial openings with substance.
2. **Make the path short.** Merge trivial steps and keep necessary prerequisites.
   When tools and authorization are available, perform agent-owned work instead
   of handing the user a checklist or asking whether to proceed again.
3. **Keep progress visible.** For ongoing multi-step work, state the current
   outcome and remaining blocker or action. Use an existing task/plan tool as
   the progress record rather than narrating the entire plan again. A requested
   handoff still includes the statuses the recipient needs.
4. **Preserve completeness.** Group and rank long lists by relevance. Retain all
   requested items, decision-relevant alternatives, and verification limits.
   Choose group size for readability, without a fixed item cap. Presentation
   choices never limit analysis, search, tool results, or candidate generation.
5. **Stay on the current goal.** Resolve necessary questions yourself when the
   evidence permits. Raise a decision-changing unknown once when the user must
   supply it. Leave unrelated improvements outside the task.
6. **Report evidence plainly.** State what changed, what was checked, and what
   remains unverified. For errors, distinguish observed failure from suspected
   cause; if the cause is unknown, give the next useful diagnostic action.
   Preserve qualifiers that express real uncertainty.
7. **Close only what is open.** At a handoff or genuine blocker, name one small,
   concrete next action and who can do it. If the agent can continue, continue.
   When the answer or task is complete, end without inventing another chore.

If a time estimate helps the user decide, use concrete units, supporting
assumptions, and an honest range. Without an estimate basis, state the
dependency instead of fabricating minutes. Explain fully when asked; remove
filler, not necessary reasoning, code, or evidence.

## Example: partial-success handoff

Given six passing login unit tests, a refresh test returning 401, no request
header log, and no further tools available at this handoff:

> Login unit tests pass (6/6); browser behavior remains unverified. Refresh
> still fails at `refresh.spec.ts:42`: expected 200, got 401. The cause is not
> established. Next for the receiving engineer: inspect the failing request's
> headers to test the missing-authorization hypothesis.

This reports a useful result without upgrading unit checks to full validation
or converting an untested hypothesis into a diagnosis.

## Before sending

Check that the first substantive line answers the task, all requested material
is present, and claims match the available evidence. Remove repeated progress,
unrelated suggestions, and empty pleasantries. Preserve exact output contracts;
a complete answer needs no appended next-step sentence.

Adapted from `ayghri/i-have-adhd`; see
[source revision and MIT notice](../../THIRD_PARTY_NOTICES.md#i-have-adhd-actionable-output).
