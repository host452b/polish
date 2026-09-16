# Contract Relationships

Use this reference while building the project map and selecting candidates. These seven groups supply hypotheses, not seven mandatory tool runs. For each selected relationship, identify why the connected parts should agree; similarity alone is not a contract.

## Seven Candidate Sources

| Group | Compare | Exploration question |
| --- | --- | --- |
| Documentation and usage | Documentation ↔ example; example ↔ implementation; documentation ↔ public API | Does the promised way of using the project work? |
| Interfaces and calls | Internal caller ↔ callee; stubs/headers/bindings ↔ implementation; protocol ↔ plugin | Do parameters, results, errors, ownership, and preconditions agree? |
| Configuration and dispatch | Definition ↔ parsing ↔ propagation ↔ consumption; public entry points | Does the user's selection reach the right implementation and take effect? |
| Data and artifacts | Producer ↔ consumer; save ↔ load; export ↔ import | Are meaning and required information preserved? |
| State and lifecycle | Initialize/use/close/recover; cache; failure/retry | Do composed operations preserve promised state and side effects? |
| Versions and delivery | Dependency declarations ↔ usage; compatibility promises ↔ changes; source ↔ release package | Do supported environments and installation methods actually work? |
| Tests and real behavior | Mock ↔ real component; assertions ↔ feature promises | Do tests exercise real usage or accidentally freeze an incorrect result? |

## Representative Checks

### 1. Documentation and Usage

- Bind a documented promise to its version, support conditions, public entry point, and observable result. Check whether an example is runnable as shipped or explicitly requires additional setup.
- Run a minimal documented workflow; compare arguments, output, exception behavior, and artifacts with the promise. Follow an example into its implementation when its advertised backend or feature is unclear.
- Check migration/deprecation notes before treating differences as regressions. An explicitly archived v1 page need not describe v2. If a page advertised for the current release is inaccurate, determine whether the defect is in that page, the example, or the implementation; do not silently nominate code as authoritative.
- When two current authoritative sources conflict and intent cannot be resolved, report the inconsistency and keep implementation attribution unresolved.

### 2. Interfaces and Calls

- Compare actual callers with signatures and implementation: defaults, keyword names, units, ranges, return structure, exception/status translation, and preconditions.
- For C++, examine the selected overload, public header, compile definitions, ownership, and lifetime. For Python, compare stubs and annotations with reachable runtime behavior. For bindings, trace conversion, overload selection, buffers, and exception translation across both languages.
- Compare a plugin with its declared protocol version and supported capabilities. A plugin that is intentionally incompatible is not proof that the host's supported path is broken.
- Verify public reachability. A direct call to a private helper with an input that its real callers cannot produce does not establish the same user-facing defect.

### 3. Configuration and Dispatch

- Follow a selected option through definition, parser, environment/file/CLI precedence, wrapper, factory, selected backend, and final consumption. Check false/zero/empty values only where the contract permits them.
- Compare the default with a supported non-default value whose behavior should differ. A parser accepting a value is not proof of its use; an unchanged output is not proof of neglect if that input is insensitive to the option.
- Compare public entrances only for behavior they promise to share. An explicit fallback policy can explain a different backend; verify its applicability and promised notification behavior.

**Example — dropped configuration:** The current API promises `total(values, scale)` returns the signed sum multiplied by `scale`. A public call with `[2, 3]` and `scale=2` returns `5`; default scale returns `5`; the callee directly invoked with `scale=2` returns `10`. Source shows the wrapper calls the callee without forwarding `scale`. Together, applicability, public reproduction, control, and call-site evidence support a configuration-propagation defect and its cause. A suspicious call site alone is weaker if another layer may supply the option.

### 4. Data and Artifacts

- Identify what must survive: schema, units, ordering, identity, metadata, precision, device/dtype, or version markers. Do not demand byte equality when the format promises only semantic equivalence.
- Exercise producer → consumer and save → load or export → import using non-default values that expose omitted fields. Include empty or boundary cases when supported.
- Test across supported versions only if compatibility is promised. Separate export success, artifact validity, import success, and downstream correctness.
- In ML workflows, quantization, engine build, inference, and accuracy evaluation have distinct outcomes. A successful earlier stage proves neither later execution nor model accuracy.

### 5. State and Lifecycle

- Examine supported sequences: first use, repeated use, close, reinitialize, partial failure, cleanup, retry, and recovery. Only require idempotence or retry safety where promised.
- For caches, identify the validity key and invalidation contract. Compare cold/warm state and a relevant configuration or data change. Account for intentional process-wide reuse.
- Observe externally visible results and side effects, including resource identity and eventual completion. Missing immediate release is not a leak if release is deferred by contract; check after the applicable completion boundary.
- For asynchronous work, use request/task/object identifiers and declared ordering guarantees. Timing alone or a shared worker thread does not identify a logical operation.

### 6. Versions and Delivery

- Compare supported dependency ranges with actual API usage and conditional imports. Use feasible boundary versions with a reason; do not attempt every combination or infer failure from an uninstalled dependency.
- Inspect the release recipe and the actual wheel, sdist, archive, native install tree, or other applicable distributable. Check runtime resources, public headers, shared libraries, generated files, plugin registration, and entry points used by supported workflows.
- Build/install in isolation using the repository's documented path when feasible. Run from outside the source checkout and prevent editable installs, current-directory imports, search-path overrides, or old libraries from hiding omissions. Record module/library paths and artifact identity.
- Compare source/editable use with an ordinary installed artifact. If a required resource is absent from a built wheel and its public consumer fails in an isolated install, this establishes a packaging defect for that artifact. A hypothetical manifest omission needs verification against generation steps and package contents.
- Distinguish a locally built package from the published package. Never claim that a release channel is broken without examining its artifact or equivalent build evidence, and state that equivalence's limits.

### 7. Tests and Real Behavior

- Check whether mocks preserve the real signature, state transitions, return types, exceptions, and relevant side effects. Where feasible, compare one real integration path with the mocked path.
- Read assertions against the current feature promise. A passing test may exercise only defaults, skip a later stage, or assert a known wrong result; this does not make an unexecuted stage pass or make the recorded test fail.
- Treat generated tests and snapshots as proposed oracles. Review them against the contract before using them to confirm a defect.
- Missing coverage is a coverage gap, not itself a confirmed functional defect. Report an incorrect test independently when evidence establishes that its expectation or setup is wrong.

## Select Runtime Scenarios Independently

| Axis | Useful contrasts, when supported |
| --- | --- |
| Version and dependency | Current contract vs archived docs; supported dependency boundaries; matched source, artifact, and runtime versions |
| Configuration and entry point | Default vs explicit value; file/env/CLI precedence; API vs CLI; selected backend vs allowed fallback |
| Platform and build | Relevant OS/architecture/compiler/ABI; debug vs optimized; optional feature enabled/disabled |
| Operation sequence | First/repeated use; failure then retry; close then reopen; concurrent or asynchronous completion |
| Installation and loading | Source/editable vs installed package; clean environment vs existing installation; actual module/shared-library origin |
| State and data | Cold/warm/invalidated cache; round-trip artifacts; meaningful valid boundary values |

Choose scenarios because they can expose a particular mismatch. Record untested axes explicitly. When a scenario cannot execute, continue accessible relationships and distinguish the missing test environment from a defect in a supported deployment.
