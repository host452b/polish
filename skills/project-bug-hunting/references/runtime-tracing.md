# Runtime Evidence

Load this reference when source analysis and minimal behavior checks leave a specific runtime boundary unresolved. **Contract first, observation points second, probes last.** A trace helps establish actual paths, boundary values, event counts, resources, or error propagation; it does not supply the correctness contract.

## Mechanism, Probe, and Tool

- **eBPF** is the underlying execution mechanism used by this Linux tracing stack.
- **uprobes / uretprobes** observe user-space native function entry and return.
- **bpftrace** provides a language and tooling to attach probes and aggregate observations; it also supports USDT and kernel tracepoints. These facilities support the existing contract groups, rather than defining another group. See the [bpftrace project](https://bpftrace.org/) and its [probe documentation](https://bpftrace.org/docs/release_025/language#probes).

Choose bpftrace for a small native-boundary question on a compatible environment; an existing BCC tool may fit a project-specific observer. Prefer source inspection, existing logs, or a behavior control when these already discriminate the alternatives. Do not make Linux tracing a prerequisite for a C++ or Python investigation on another platform.

## Bind Observation to a Candidate

| Existing relationship | Useful events or values | Candidate mismatch |
| --- | --- | --- |
| Example ↔ implementation | Native entry, selected dispatch path, call count | Example advertises a backend but executes another |
| Caller ↔ callee | Boundary parameters, return status, linked calls | A wrapper changes or drops a valid setting |
| Configuration ↔ effective behavior | Scalar value at consumption, selected implementation | Parsed option leaves the default in effect |
| Python API ↔ C/C++ binding | Python operation correlated with native extension entry | Wrong branch, overload, or extension is selected |
| Lifecycle ↔ resources | Create/use/close/release plus object identity | An operation leaves state or resources beyond promised lifetime |
| Error handling ↔ result | Lower-layer status, recovery, upper-layer completion, exit state | Unhandled lower-layer failure is reported as success |
| Cache promise ↔ access | Cache key, read/write/invalidate, recomputation | Stale entry remains in use or promised reuse still recomputes |
| Package ↔ loaded component | Mapped library path, build identity, observed entry | New installation executes a stale or different extension |

An allowed fallback or recovery can explain a lower-layer failure followed by success. Check that policy before declaring error suppression.

## Observation Protocol

1. **Define the discriminating observation.** Name the candidate, supported workload, expected event/value, control, and what each outcome could establish. Limit the process scope, duration, and fields collected to this question.
2. **Identify the actual runtime.** Record executable/module/shared-library paths, process/run identity, revision and build ID or hash, compiler/build mode when relevant, architecture, tool version, and kernel/device/runtime versions as applicable. Check process mappings or equivalent loader evidence; the checkout path and installed package version alone do not identify loaded code. Account for container paths and child processes when relevant.
3. **Resolve the observation point.** Verify symbol or offset, overload, binary, and parameter signature. Enumerate available probes and inspect argument metadata using the installed tool's documented listing mode. Inlining, stripped symbols, specialization, or JIT-generated code may leave no probe at the expected source function; choose another observable boundary rather than assuming an entry exists.
4. **Validate a known-hit control.** Establish that attachment succeeded before the relevant workload, then exercise an event known to occur through the same observation path. A tool-start message or successful attachment alone is insufficient. Record control input and hit result; a control on another library does not validate this candidate's symbol or filter.
5. **Capture and correlate.** Preserve probe source, exact command, attachment output, workload, timestamps, raw events/aggregates, exit status, and loss/coverage diagnostics. Correlate asynchronous events using a task/request ID or object identity with its lifetime; GPU work may require stream and launch correlation. Thread ID alone cannot associate work across callbacks or workers. Account for recursion, overlapping calls, ID reuse, and incomplete return events when pairing entry/exit.
6. **Interpret within coverage.** Check event loss, capture start/end, subprocess coverage, filters, and perturbation by tracing. Missing hits, dropped events, or incomplete coverage leave absence claims **UNVERIFIED** or **BLOCKED**. Positive hits prove only the observed path/value, not final correctness. Use output assertions, completion/error status, or resource-state checks to establish the promised result.

If a control fails or the observer is unavailable, record the exact missing evidence and continue other verification. Do not relabel an observation failure as an implementation failure, or broaden privileges/system scope merely to complete a tool checklist.

## Native Argument Limits

`argN` is not automatically the nth source-level parameter. ABI, architecture, hidden C++ arguments, return conventions, and argument type matter. bpftrace offers DWARF-based `args` access for supported uprobes with suitable debug information; inspect what is actually available. Do not assume arbitrary C++ objects, Python objects, floating-point values, or optimized-away arguments can be printed correctly. Entry arguments and return values require the appropriate probe. See [arguments](https://bpftrace.org/docs/release_025/language#arguments) and [uprobes / uretprobes](https://bpftrace.org/docs/release_025/language#uprobe-uretprobe).

Validate a decoded value with a known input before attributing a changed value to the program. A pointer printed as an integer is not evidence of a corrupted scalar. Prefer stable scalar boundaries or documented USDT fields when complex layouts remain uncertain. Probe design must match the installed version; the linked bpftrace 0.25 documentation is a reference, not a minimum-version requirement.

## Python and GPU Observation

**Python:** `sys.monitoring` is available from Python 3.12 for interpreter execution events. Check interpreter support and event semantics, reserve an available tool ID, and restore monitoring state after the experiment. It does not expose arbitrary C++ internals or prove device execution. On other interpreters or versions, select an available observer and state its limits. See [Python's monitoring API](https://docs.python.org/3.12/library/sys.monitoring.html).

**GPU:** Use Nsight Systems when the unresolved question concerns host/device scheduling, CUDA activity, or NVTX correlation. Verify supported collection features for the installed driver/tool/platform. A host API return, enqueue, or launch event does not prove device completion or numerical correctness. Correlate the logical task with completion and output evidence, and record synchronization choices or instrumentation overhead that could change behavior. See the [Nsight Systems user guide](https://docs.nvidia.com/nsight-systems/UserGuide/index.html).

For mixed-language paths, connect Python operation → binding → native dispatch → asynchronous completion only as far as the actual evidence reaches. Report a known wrong result independently from an unproven hypothesis about which layer caused it.
