# Tight Feedback Loops and Practical Debugging Hygiene

Selective engineering supplement adapted from `mattpocock/skills` (`skills/engineering/diagnosing-bugs`). Consult this reference when reproducing hard, flaky, or performance bugs, or when instrumenting and cleaning up a fix.

## Redact Secrets First

Before printing commands, logs, HTTP captures, or traces:
- Replace every secret, token, cookie, or credential with `<REDACTED>`.
- Build reproduction commands against environment variables so credentials stay out of transcripts and scripts.
- Quote only the signal-carrying lines from captured headers or payloads.

## 10-Level Feedback Loop Ladder

Prioritize building a **tight, red-capable** signal (fast, deterministic, asserts the exact user-reported symptom) before guessing at fixes. Pick the cheapest viable rung from top to bottom:

1. **Failing test** at the seam that reaches the defect (unit, integration, or e2e).
2. **Curl / HTTP script** against a local dev server.
3. **CLI invocation** with a fixture input, diffing stdout/exit code against a known-good output.
4. **Headless browser script** (Playwright / Puppeteer) asserting DOM, console, or network behavior.
5. **Replay a captured trace** (saved request, payload, or event log) through the target code path in isolation.
6. **Throwaway harness** running a minimal slice of the system with stubbed boundaries.
7. **Property / fuzz loop** (e.g. 1000 randomized inputs) to surface intermittent wrong output.
8. **Bisection harness** suitable for `git bisect run` when the defect regressed between two known states.
9. **Differential loop** running the same input through old vs. new version (or two configs) and diffing outputs.
10. **Human-in-the-loop (HITL) bash script** using [`scripts/hitl-loop.template.sh`](../scripts/hitl-loop.template.sh) when a human must click or authenticate interactively.

### Tighten the Loop and Raise Flaky Repro Rates

- **Tighten**: cache setup, narrow scope, assert the exact symptom (not merely "didn't crash"), and pin nondeterminism (clock, RNG seed, isolated filesystem, frozen network).
- **Non-deterministic bugs**: raise the reproduction rate first (repeat 100x, parallelize, add load, narrow timing windows, inject targeted delays). A 50% flake is debuggable; a 1% flake is not.

## Minimise Before Hypothesising Deeply

Once the loop reliably goes red on the exact reported symptom, shrink the repro by removing inputs, callers, config keys, or steps **one at a time**, re-running after each cut. Stop when every remaining element is load-bearing (removing any one turns the loop green). A minimal repro shrinks the hypothesis space and becomes a clean regression test.

## Instrumentation, Performance Branch, and Cleanup

- **Tagged temporary logs**: prefix every temporary debug log with a unique session tag such as `[DEBUG-a4f2]` so cleanup is a single `grep` before finishing.
- **Performance regressions**: do not guess with logs first. Capture a baseline measurement (timing harness, profiler, query plan), then bisect or test one variable at a time against that baseline.
- **Missing test seam is a finding**: write the regression test at a seam that reproduces the real calling pattern. If no such seam exists (e.g. only shallow unit tests are possible and would give false confidence), do not fake coverage — report the missing seam as an architectural finding.
- **Pre-completion cleanup checklist**:
  - Original un-minimised reproduction loop passes.
  - Regression test passes (or missing seam is explicitly documented).
  - Zero `[DEBUG-...]` instrumentation lines remain.
  - Throwaway harnesses/artifacts are removed or clearly isolated.
