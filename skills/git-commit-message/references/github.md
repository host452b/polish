# GitHub commit message profile

Use this profile for GitHub destinations, including confirmed GitHub Enterprise
instances. Follow explicit repository conventions and stricter CI rules first.

## Structure and header

```text
<type>(<scope>)!: <description>

<body>

<footer>
```

Only the header is required for a small change. Separate present sections with
one blank line. Use the standard type-first header; GitLab's optional issue
prefix does not carry over unless the repository explicitly requires it.

| Type | Meaning | Typical configured release effect |
| --- | --- | --- |
| `feat` | New feature | Minor |
| `fix` | Bug fix | Patch |
| `perf` | Performance improvement | Often patch |
| `refactor` | Restructure without external behavior change | None by default |
| `docs` | Documentation only | None by default |
| `style` | Code formatting, no logic change | None by default |
| `test` | Add or modify tests | None by default |
| `build` | Build system or external dependencies | None by default |
| `ci` | CI configuration or scripts | None by default |
| `chore` | Other work not modifying source or tests | None by default |
| `revert` | Revert an earlier change | Tool/policy dependent |

`style` is formatting, not CSS/UI behavior; correcting a visual defect is `fix`.
Version effects depend on configured release tooling. Under the conventional
SemVer mapping, a breaking change on any type signals a major release; GitHub
does not itself bump versions because a message contains `feat`, `fix`, or `!`.
Pre-1.0 and custom release policies may differ.

Scope is optional. Choose one module noun such as `auth`, `cart`, or `api`, using
the team's stable vocabulary rather than alternating synonyms like `user`,
`users`, and `account`.

Use an imperative description: `add`, `fix`, `remove`, not `added` or `fixes`.
It should complete “If applied, this commit will ...”. Omit the final period.
Follow team casing; default to a lowercase initial when unspecified.

Target at most **50 characters for the entire header**, with a **hard maximum
of 72**, or the repository's stricter limit. Count type, scope, punctuation,
and description together. Shorten wording rather than dropping the type.
Avoid vague titles like `fix: fix bug`, `update`, or `Fixed the header.`.

## Body and footers

Important changes need a body explaining why: background, symptoms, or the
requirement. Summarize behavior rather than individual changed lines. Explain
non-obvious choices, tradeoffs, side effects, and unresolved problems.

Manually wrap prose at 72 characters; use `-` lists when helpful. Preserve
unbreakable URLs/identifiers and report a conflict if a hard linter rule requires
another representation. Follow the team's body language; otherwise match the
user's language. Headers use English imperative verbs.

Use trailer-style footers, each beginning on its own line. GitHub issue keyword
forms without colons are also accepted:

```text
BREAKING CHANGE: describe incompatibility and caller migration
Closes #128
Refs #95
Reviewed-by: Zhang San <zhangsan@example.com>
Co-authored-by: Li Si <lisi@example.com>
```

Use `Closes` or `Fixes` only for intended closure; otherwise use `Refs`.
Closing keywords can close an issue when the commit reaches the default branch;
a reference alone is not a closure request. Use qualified references such as
`owner/repo#128` for cross-repository issues. Never invent an issue solely to
complete a footer.

For breaking changes, add `!` before the header colon and provide uppercase
`BREAKING CHANGE:` with migration instructions. `BREAKING-CHANGE:` is an
equivalent footer spelling. Confirm reviewer/co-author identities before adding
trailers; GitHub recognizes `Co-authored-by` for co-authorship attribution.

## Atomic changes and examples

One commit should do one independently reviewable/revertible thing. An `and`
joining independent behaviors or unrelated `feat` and `fix` changes suggests
separate commits. Tests supporting the implementation normally stay with it.
Atomic commits improve revert, bisect, and review. Suggest `git add -p` if the
user is organizing changes; drafting alone does not stage files.

Small fix:

```text
fix(login): prevent button overflow
```

Feature, assuming the supplied requirement and intended issue closure:

```text
feat(cart): support batch item deletion

Removing items one at a time makes clearing the cart cumbersome on
mobile. Allow multi-selection with confirmation before deletion.
Limit each operation to 100 items to avoid request timeouts.

Closes #256
```

Breaking change with known migration:

```text
refactor(api)!: flatten user response

The three-level structure makes field access cumbersome. Move fields
from data.profile directly into data.

BREAKING CHANGE: Read data.name instead of data.profile.name from
/user/info. Apply the same change to other profile fields.
Refs #312
```

Non-obvious implementation, assuming this behavior is supported by evidence:

```text
fix(upload): retry chunks after 408 timeout

Storage can return 408 after successfully writing a chunk. Check for
its existence with HEAD before retrying to avoid duplicate writes.

Fixes #401
```

## Tooling and semantics

When asked to automate enforcement, see [tooling.md](tooling.md) for templates,
commitlint/Husky considerations, and release automation. Message generation
alone does not install tools or edit Git configuration.

The type/release mapping and accepted footer separators follow the
[Conventional Commits specification](https://www.conventionalcommits.org/en/v1.0.0/).
Default-branch closure behavior follows
[GitHub's issue-linking documentation](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue).
