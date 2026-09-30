---
name: git-commit-message
description: Use when drafting, reviewing, or rewriting Git commit messages or final squash/MR/PR titles for GitLab or GitHub, including requests to write a commit message or 提交信息.
---

# Git Commit Message

Write a message for the actual change and destination. Apply repository rules
first, then the selected platform profile. These profiles are user conventions,
not requirements imposed by GitLab or GitHub.

## Select the profile

1. Use the user's explicit destination. Otherwise inspect the intended push/MR/PR
   target, remote URLs, and branch tracking/push configuration. An `origin`
   remote can be a fork or mirror; its name alone does not select the platform.
2. Recognize `github.com` and `gitlab.com`. For SSH aliases, GitHub Enterprise,
   and self-hosted GitLab, use known host mappings or repository documentation.
   CI filenames alone are clues, not proof. Keep credentials out of output.
3. Read `AGENTS.md`, `CONTRIBUTING.md`, commitlint/CI rules, and relevant templates
   when available. Recent commits can establish scope vocabulary and conventions;
   they do not override explicit repository rules.
4. Read the matching reference before writing:
   - GitLab: [references/gitlab.md](references/gitlab.md).
   - GitHub: [references/github.md](references/github.md).
   - Destination unresolved or another host: ask for the intended platform when
     it changes the result. A useful provisional draft may use the standard
     format below, clearly labeled as not yet checked against a platform profile.

## Establish the change

For a repository-backed request, inspect status and the diff for the requested
scope. For the next commit, inspect `git diff --cached`; keep unstaged work out
of that message. If nothing is staged, inspect the working diff and label it as
a proposed commit scope. For a squash title, use the full intended merge range.
For supplied text or a supplied diff, work from that evidence without requiring
a checkout.

Identify one atomic behavior, its reason, compatibility impact, known issues,
and actual validation. If changes are independently reviewable/revertible,
propose separate messages. Keep implementation and its tests together.

## Compose and check

```text
<type>(<scope>)!: <description>

<body>

<footer>
```

Only the title is mandatory for a small change. Scope and `!` are conditional.
Separate present sections with blank lines. Use the chosen reference for type,
length, language, issue placement, body, and footer rules.

| Check | Required result |
| --- | --- |
| Header | Valid type, concrete imperative description, measured length |
| Scope | One stable module; omit when no meaningful main scope exists |
| Evidence | Claims match the diff or supplied facts |
| Validation | Actual commands/results only; missing evidence stays unknown |
| Issues | Real identifiers; required missing issue reported outside the draft |
| Breaking change | `!` plus a footer explaining the caller's migration |
| Publication | No credentials or private information in public output |

Never invent an issue, passing test, benchmark, risk assessment, reviewer,
co-author, or sign-off. If validation was not run, say so; if unavailable, say
it is unknown. Ask for missing migration details instead of inventing them.

Return one copyable `text` block per proposed commit. Keep explanations outside
the message and limit them to material assumptions, violations, or missing facts.
For review requests, identify concrete violations and provide the corrected text.

## Scope of action

Drafting a message does not authorize staging, committing, amending, rebasing,
pushing, configuring hooks, or changing global Git settings. If the user already
requested an operation, apply this skill within that authorization.

Read [references/tooling.md](references/tooling.md) only when templates,
commitlint, DCO, or release automation are requested. Suggest atomic staging or
history cleanup when relevant; execute only within the user's requested scope.
