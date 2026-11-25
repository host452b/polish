# update-and-sync

Use this workflow to review upstream changes to a `polish` adaptation. A request may name one or more local skills. With no names, review every entry below, fetching each repository once. Report an unlisted name as out of scope. The [third-party notices](../THIRD_PARTY_NOTICES.md) identify the original adaptation commits and licenses.

## Source directories

Paths are relative to the indicated GitHub repository at its original adaptation commit.

| Local skill | Original repository | Skill directory |
| --- | --- | --- |
| `superpowers-brainstorming` | `obra/superpowers` | `skills/brainstorming` |
| `superpowers-systematic-debugging` | `obra/superpowers` | `skills/systematic-debugging` |
| `superpowers-test-driven-development` | `obra/superpowers` | `skills/test-driven-development` |
| `superpowers-using-git-worktrees` | `obra/superpowers` | `skills/using-git-worktrees` |
| `superpowers-verification-before-completion` | `obra/superpowers` | `skills/verification-before-completion` |
| `superpowers-writing-skills` | `obra/superpowers` | `skills/writing-skills` |
| `google-stitch-frontend-taste-design` | `google-labs-code/stitch-skills` | `plugins/stitch-utilities/skills/taste-design` |
| `google-stitch-extract-frontend-design-system` | `google-labs-code/stitch-skills` | `plugins/stitch-design/skills/extract-design-md` |
| `google-stitch-frontend-brief-enhancer` | `google-labs-code/stitch-skills` | `plugins/stitch-utilities/skills/enhance-prompt` |
| `google-stitch-shadcn-ui` | `google-labs-code/stitch-skills` | `plugins/stitch-build/skills/shadcn-ui` |
| `i-have-adhd-actionable-output` | `ayghri/i-have-adhd` | `skills/i-have-adhd` |
| `benchmark-checklist` | `cursor/plugins` | `pstack/skills/benchmark-checklist` |
| `before-git-push` | `cursor/plugins` | `pstack/skills/blast-radius` |
| `project-bug-hunting` | `cursor/plugins` | `pstack/skills/create-verification-skill` |
| `mattpocock-domain-modeling` | `mattpocock/skills` | `skills/engineering/domain-modeling` |
| `mattpocock-codebase-design` | `mattpocock/skills` | `skills/engineering/codebase-design` |
| `mattpocock-grilling` | `mattpocock/skills` | `skills/productivity/grilling` |
| `mattpocock-prototype` | `mattpocock/skills` | `skills/engineering/prototype` |
| `mattpocock-research` | `mattpocock/skills` | `skills/engineering/research` |
| `mattpocock-code-review` | `mattpocock/skills` | `skills/engineering/code-review` |
| `mattpocock-wizard` | `mattpocock/skills` | `skills/engineering/wizard` |
| `mattpocock-writing-for-agents` | `mattpocock/skills` | `skills/productivity/writing-for-agents` |
| `find-a-bug` (supplement) | `mattpocock/skills` | `skills/engineering/diagnosing-bugs` |
| `superpowers-test-driven-development` (supplement) | `mattpocock/skills` | `skills/engineering/tdd` |
| `google-stitch-frontend-taste-design` (supplement) | `nextlevelbuilder/ui-ux-pro-max-skill` | `src/ui-ux-pro-max/templates/base/quick-reference.md` |

For the two pstack integrations, compare upstream changes only against the consumer check in pre-push step 6 and the documentation/API replay table respectively. For the three isolated cherry-picked supplements, compare upstream changes only against `skills/find-a-bug/references/feedback-loops.md` + `scripts/hitl-loop.template.sh`, `skills/superpowers-test-driven-development/seam-and-slicing-guide.md`, and `skills/google-stitch-frontend-taste-design/references/quantitative-checks.md` respectively. Machine-readable provenance for all mapped entries is also maintained in [`upstream-sources.json`](../upstream-sources.json).

## Read the original and its history

1. Fetch the named original repository into a separate checkout or temporary clone. Verify its remote URL and resolve its current default branch to a commit (`tip`). For each skill, use its last recorded full-sync commit as `base`, falling back to its original commit in the notices. Read the original skill and its referenced resources at both revisions, then read the local adaptation. Identify intentional local differences before evaluating updates.
2. Verify both Git objects and their ancestry. Inspect the full range since the base, including the files on which the skill depends. In the upstream checkout, start with:

   ```sh
   git merge-base --is-ancestor "$base" "$tip"
   git diff --name-status -M "$base" "$tip"
   git log --full-history --reverse --format='%h %ad %s' --date=short "$base..$tip" -- "$source_dir"
   git diff "$base" "$tip" -- "$source_dir"
   ```

   Use the unfiltered rename listing and file history to follow moves, including intermediate paths. Repeat the path-scoped history for moved paths and relevant shared files. Read candidate commit patches with `git show` for prerequisites, reversions and changes outside the skill. A commit title or repository release note alone is insufficient. If a fetch, base, ancestry or path cannot be verified, explain the gap for that skill and continue with independently verifiable entries.

## Decide per skill

Summarize the base and tip, relevant upstream commit links, what changed for users of the original skill, and which changes already exist locally. State one recommendation with reasons:

| Decision | When it fits |
| --- | --- |
| Full sync | All applicable upstream changes fit the local adaptation. Identify how to retain local behavior during the port. |
| Selective port | Only specific commits or hunks fit. Name each selected change, prerequisites, and the changes to leave upstream. |
| Skip | The history shows no relevant change, equivalent local behavior, a reverted change, or an incompatibility. Give the specific reason. |

Check Superpowers' prefixed names and standalone handoffs, Stitch's independence from hosted services, and the ADHD skill's task-scoped presentation rules. Use the actual local diff to support the recommendation.

## Apply and record

A review request ends with the recommendations. When the user requests application, apply the selected changes in the local `polish` source checkout. Port mixed commits or renamed paths at file/hunk level. Use a literal Git cherry-pick only when the entire commit belongs in this repository, paths match and creating a commit is in scope. Preserve local edits and attribution.

Exercise the changed behavior and run the repository checks in [AGENTS.md](../AGENTS.md), including the applicable port validator in `scripts/`. After verifying an applied update, append an entry below with the local skill, full upstream SHA(s), selected files or behavior, and verification. For a full sync record the new base for that skill only. For a selective port keep its prior full-sync base and use the recorded patches to recognize already-applied changes on the next review. Preserve the original source pins in the notices.

## Applied updates

The initial baselines are the commits in the third-party notices.
