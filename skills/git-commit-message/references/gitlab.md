# GitLab commit message profile

Use this profile for GitLab destinations, including confirmed self-hosted
instances. Stricter repository contribution and CI rules take precedence.

## Purpose and commit boundaries

Keep history searchable, reviewable, and independently revertible. Link commits
to issues and merge requests so changelogs and release notes remain traceable.
Each commit should perform one independently explainable change and, where
practical, build and test on its own. Classifying a commit does not itself change
a version number; the project's release policy controls that.

Apply this profile to new commits and final MR titles. Do not rewrite existing
history simply to retrofit it. Before merge, temporary `WIP`, `fixup`, `try again`,
and `address comments` commits should be cleaned up according to team policy.

## Header and issue placement

Default:

```text
<type>(<scope>)!: <description>
```

Only when the team uses an issue-prefix convention:

```text
<issue-ref>: <type>(<scope>)!: <description>
```

Retain the Conventional Commit type even after an issue prefix. Do not introduce
issue prefixes solely because the host is GitLab. Use one format consistently
within a repository; absent evidence of a prefix convention, use the standard
header and put issue references in the footer or MR description.

Choose the primary issue reference in this order:

1. Same-project issue: `#123`.
2. Recognized tracker key: `PROJ-1234`.
3. Cross-platform/private tracker or ambiguous numbering: full canonical URL.

```text
#123: fix(runtime): reject invalid configuration
PROJ-1250: feat(api): add cancellation callback
https://tracker.example.com/issues/1280: fix(cache): prevent stale reads
```

Use stable canonical URLs, preferably HTTPS, without user information, tokens,
query/tracking parameters, or fragments. Preserve the tracker identity; do not
turn a URL into an invented bare issue number. If a clean canonical URL cannot
be established, request it. Put only the primary issue in the title and other
issues in `Refs:` footers. A prefix ends with a colon and one space.

Features, fixes, and important tasks should have an issue association. Small
documentation/maintenance changes may be exempt under project rules. A missing
required issue is a reported gap, never a fabricated identifier.

## Types, scope, and description

| Type | Purpose |
| --- | --- |
| `feat` | New functionality or externally available capability |
| `fix` | Defect or regression repair |
| `perf` | Performance improvement |
| `refactor` | Restructure without changing external behavior |
| `test` | Add or modify tests |
| `docs` | Documentation only |
| `build` | Build system or dependencies |
| `ci` | CI configuration or scripts |
| `style` | Code formatting without logic changes |
| `chore` | Other maintenance |
| `revert` | Revert an earlier commit |

`style` means code formatting, not visual styling. Repairing a UI style defect
is `fix`.

Use one short, stable, lowercase kebab-case scope from the team's vocabulary:
`api`, `runtime`, `scheduler`, `cache`, `parser`, `builder`, `cli`, `server`,
`docs`, `tests`, `build`, `ci`, or `infra`, for example. Avoid `misc` and `other`.
Split independent module changes; omit scope for an inseparable cross-module
change without a meaningful primary module.

Use an English imperative description, lowercase initial, without a final
period. Prefer a description of at most 50 characters and a complete header of
at most 72 characters; the header recommendation may extend to 100 with an
issue prefix. These are recommendations unless repository rules make them hard
limits. Shorten wording without truncating identifiers or canonical URLs.

Reject vague titles such as `fix: fix bug`, `update code`, and
`address review comments`. An `and` joining independent behaviors signals a
split; tests and docs explaining the same behavior need not be separate commits.

## Body and footers

Important changes require a body covering why the change is needed, the behavior
that changes, material risks, and actual validation. Explain root cause only
when established. Address compatibility, accuracy, performance, resources, or
concurrency where relevant. Avoid narrating the diff line by line. Prefer lines
of at most 72 characters; lists are allowed. Recommend English for both header
and body; follow explicit team language requirements.

Use a blank line between header, body, and footer sections. Start each footer
on its own line; long values such as migration guidance may continue on the
following line without breaking an identifier or command.

| Footer | Meaning |
| --- | --- |
| `Issue: PROJ-1234` | Task directly implemented or fixed |
| `Refs: PROJ-1200` | Related item without requesting automatic closure |
| `Closes: #256` / `Fixes: #256` | Closure only when configured and intended by the team |
| `Test: pytest -k request_state` | Executed validation; repeat for multiple tests |
| `Benchmark: GPU-X, batch=64, input=1024, output=128` | Reproducible performance conditions |
| `Risk: low; no public API change` | Supported risk assessment and reason |
| `BREAKING CHANGE: ...` | Incompatibility and migration instructions |
| `Signed-off-by: Name <name@example.com>` | DCO sign-off when required |
| `Co-authored-by: Name <name@example.com>` | Actual confirmed co-author |

Performance commits should include hardware and workload/benchmark conditions;
missing measurements remain a gap, not a made-up result. Use `git commit -s`
only when the project requires DCO and committing is authorized.

For an incompatible change, add `!` after type/scope and an uppercase
`BREAKING CHANGE:` footer explaining migration. If no replacement exists,
state the known caller action explicitly.

```text
fix(runtime): validate cache configuration

An incompatible configuration was accepted during startup and failed
only after resources had been allocated. Reject it before allocation;
valid configurations retain their existing behavior.

Issue: PROJ-1234
Test: pytest -k cache_configuration
Risk: low; invalid configurations fail earlier
```

```text
refactor(api)!: remove legacy executor options

Remove the deprecated executor configuration path.

BREAKING CHANGE: Replace legacy_executor_config with executor_config.
The compatibility alias is no longer available.
Issue: PROJ-1300
```

Examples assume those facts and validation are supplied or verified.

## Issues, MRs, and automation

An issue owns requirements, status, ownership, priority, and acceptance criteria.
A commit explains an atomic code change. The MR title summarizes the final
change entering the target branch; its description carries full background,
links, risks, tests, and release notes. Footers supplement issue management.
For squash merging, check the final title because the squash commit may inherit
the MR title. MR numbers need not be manually inserted in commit headers.

Controlled release/merge/sync/generated-file/automatic-revert processes may
use stable templates without issue links when project policy allows:

```text
release: publish version 2.4.0
merge: integrate release branch
sync: update generated metadata
revert: revert abc1234 after failed validation
```

Ordinary development commits cannot use these exceptions to bypass validation.
Never use an empty title, bare version, or bare SHA. Review each final commit for
independent build/test/revert behavior. Suggest `git add -p` or `git rebase -i`
only within the relevant workflow; a message-writing request does not run them.

## Public information and team configuration

Exclude credentials from commit/MR/issue text, logs, and documentation. Treat
URLs containing `token=`, `access_token=`, or `private_token=` as credentials.
Public output must also exclude internal domains, customer names, unreleased
products, internal codenames, and private test paths. A sanitized internal URL
can still be confidential: remove it from public text or use an approved public
reference. Keep a private-link gap outside the commit draft without echoing it.

When actually preparing internal work for public publication, inspect the full
outgoing history as well as the final diff. Discover the real base instead of
assuming `origin/main`; useful checks include `git log --format=full <base>..HEAD`
and `git diff --check <base>...HEAD`. If credentials were committed, report the
need to revoke/rotate them and clean affected history/logs; do not initiate
history rewriting from a drafting request. Secret scanning can support local
hooks and CI.

Team policy should specify header format, language, scope vocabulary, issue
requirements/exemptions, squash-title ownership, DCO/signature requirements,
automation exceptions, and commitlint/secret-scanning/CI merge gates. Unknown
requirements stay unknown; this skill does not install those tools by default.
