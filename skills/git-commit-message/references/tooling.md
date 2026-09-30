# Optional tooling

Read this file only for a request about templates, commitlint, hooks, DCO, or
release automation. Adapt to existing project tooling; generating a message
does not request installation or configuration changes.

## Commit template

For GitLab, a repository-local `.gitmessage` can contain:

```text
# <type>(<scope>)!: <description>
# Team-approved alternative: <issue-ref>: <type>(<scope>)!: <description>
#
# Why: problem, cause, or requirement
# What: changed behavior
# Risk: compatibility, accuracy, performance, resources, concurrency
# Validation: actual tests or benchmarks
#
# Issue: PROJ-1234
# Refs: PROJ-1200
# Test: <executed command or suite>
# Benchmark: <hardware and workload>
# Risk: <level and reason>
# BREAKING CHANGE: <caller migration>
```

For GitHub:

```text
# <type>(<scope>)!: <description>
# Complete header: aim for <=50 characters; maximum 72.
#
# Why? Changed behavior? Tradeoffs or side effects?
# Wrap body prose at 72 characters.
#
# BREAKING CHANGE: <caller migration>
# Closes #<issue> or Refs #<issue>, only when applicable
```

When configuring a local template is requested:

```bash
git config --local commit.template .gitmessage
```

If the user explicitly wants a global template, save it as `~/.gitmessage` and
use `git config --global commit.template ~/.gitmessage`. Templates appear when
editing a message, for example with `git commit` without `-m`. If GitLab titles
start with `#123`, check the configured comment character and cleanup behavior:
the default `#` can strip that title in the editor. Use an appropriate alternate
comment character or message-file cleanup mode when committing is authorized;
keep template comment markers consistent. Message drafting need not change Git.

## DCO

For a project requiring DCO, check the actual author identity and use
`git commit -s` for an authorized commit. Sign-off is distinct from GPG/SSH
commit signing. `git config format.signOff true` affects `git format-patch`,
not automatic sign-off for ordinary commits, as documented in
[Git's configuration reference](https://git-scm.com/docs/git-config#Documentation/git-config.txt-formatsignOff).

## commitlint and hooks

Use the project's package manager, module format, and installed tool versions.
Check current official documentation before implementing setup. Do not overwrite
an existing hook or config to insert a generic example.

The standard starting point is `@commitlint/config-conventional` with explicit
rules for header length, nonempty subject, no final period, allowed types, and
team scope casing. Apply the selected profile:

| Profile | Length/configuration considerations |
| --- | --- |
| GitHub | Header hard cap 72, preferably 50; honor stricter repository cap |
| GitLab standard | Recommended header 72, description 50; team chooses enforcement |
| GitLab issue prefix | Recommended total cap 100; custom parser required |

For a GitLab issue-prefix parser, support exactly the team's accepted forms:
`#123`, `PROJ-1234`, and/or canonical HTTPS URLs. The issue reference precedes
the normal type/scope/optional `!`/description. A Jira-only regex does not validate
`#123` or URLs. An optional issue capture does not enforce mandatory issues.
Test parser capture fields and breaking-change recognition against the actual
commitlint version, including `!` and migration footers.

Keep issue-required rules separate from syntax and account for documented
docs/maintenance exemptions and controlled automation accounts. Enable
`release`, `merge`, or `sync` only for authorized automation exceptions, not
globally for ordinary development commits. The reference templates alone do not
establish CI acceptance.

If requested, connect commitlint to the existing `commit-msg` hook through
Husky or the project's current hook system and enforce the same policy in CI.
Verify both accepted and rejected sample messages. A hook invocation must pass
the actual message file as a quoted argument (for example `--edit "$1"`).

## Release automation

Once message conventions are stable, a requested integration may use
semantic-release or release-please to calculate versions, create changelogs,
and publish tags/releases. Inspect its rules before predicting version changes:
`perf` and `revert`, pre-1.0 behavior, custom types, and breaking-change handling
can vary. This skill's drafting workflow does not publish anything.
