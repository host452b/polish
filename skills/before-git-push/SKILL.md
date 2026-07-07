---
name: before-git-push
description: Use before running git push, or when the user asks to push / ship / deploy / 上线 / 推送 changes that could reach production — a final risk gate to catch what is most likely to break prod before code leaves the local machine. Triggers - "push this / ship it / ready to push? / 可以 push 了吗 / 上线前检查 / 这次改动能推吗", pre-push review, pre-release gate, production safety, don't break prod, rollback readiness, feature toggle.
metadata:
  language: bilingual
---

# before-git-push（push 前最后一道人工把关）

## 这个 skill 做什么

在 `git push`（或任何把代码 ship 到 production 的动作）之前，以 **senior Release Engineer / SRE** 视角做最后一道 **risk gate（风控闸门）**：只依据 **real diff（真实 diff）** 判断本次改动的 **fragile line（最脆弱一行）**、**backward-compatibility（老用户兼容）** 风险、最可能被击穿的 **failure path（失败路径）**、以及 **rollback（回滚）** 与 **feature toggle（功能开关）** 是否就绪，最后给出明确的 **PUSH / HOLD** verdict。

**核心原则 core principles：**

- **Diff-grounded — judge only from the real diff.** 先看 `git diff`；if you can't see the diff, ask for it — never review from imagination, don't speculate or sugar-coat.
- **When unsure, prefer HOLD.** Mark anything uncertain as "uncertain"; prefer HOLD over a blind PUSH.
- **Review, not execution.** 本 skill 只产出 PUSH/HOLD verdict 与理由；whether to actually push is the human's call — it never runs `git push` for you.

## When to use（何时使用）

- About to `git push` / open a PR / ship a release — you want a risk pass before code leaves the local machine.
- The user asks "ready to push?", "can I ship this?", "check this before release", "will this break prod?" (或 可以 push 了吗 / 上线前检查).
- Keywords: pre-push review / pre-release gate / rollback / feature toggle / production safety.

## Not for（不适用）

- Local-only experiments you don't intend to push.
- Writing a commit message, or risk-unrelated code formatting.

## 审查步骤（think step by step，逐条推导并给出理由）

**Inspect the real diff first：** staged 与 unstaged 的 diff（`git diff`、`git diff --staged`），以及相对远端尚未推送的 commits 及其 diff（`git log @{u}..HEAD`、`git diff @{u}..HEAD`）。If you can't read the diff, say so and ask for it — do not review from imagination.

1. **Risk intuition（风险直觉）** — the single line or piece of logic you are **least confident about** (file + line / function), and why it worries you.
2. **Assumptions & blind spots（假设与盲区）** — the unverified assumptions this change relies on, the blind spots you can't see, and uncovered edge cases (null / concurrency / timeout / oversized input / retry).
3. **User impact（用户视角）** — after upgrade, can existing users hit errors, wrong behavior, or confusion from data compatibility (cache 缓存、DB schema / migration、persisted format、API contract) or changed habits? Assess each.
4. **Failure path（失败路径）** — if this reaches production right now, the failure path most likely to be broken through; rank by "most likely × largest blast radius", and state the trigger condition and the user-visible impact.
5. **Circuit breaker（熔断准备）** — for the most dangerous part above, is a rollback ready? Is there a feature toggle / kill switch to disable it instantly? If not, flag it as a pre-release gap.
6. **Missing checks（缺失的关键检查）** — the one critical check still owed before shipping (tests / monitoring & alerting / canary / migration rehearsal / performance validation). Write "none" if there is truly no gap; skip inapplicable dimensions — don't pad the list.

## 反向验证 Self-Contrast（防止误判为 "safe"）

After a draft verdict, actively list **3 pieces of evidence that could overturn "this change is safe to ship"**, and score each by confidence (1–5). If any score ≥3, or the total is clearly high, downgrade the verdict and explain the correction.

## 输出契约 Output Contract

- First give the step 1–6 conclusions (每条 1–3 句，标出对应 file / line).
- Then the 3 self-contrast evidence items with confidence scores.
- Finally the overall verdict — put `PUSH` or `HOLD` between markers, e.g. `▶︎▶︎HOLD▶︎▶︎` or `▶︎▶︎PUSH▶︎▶︎`; otherwise the output is invalid.
- **On HOLD**, name in one line the first thing to fix before release.

## 常见错误（Rationalization → Reality）

| Rationalization（借口） | Reality（现实） |
|---|---|
| "It's a tiny change, no need to review" | Tiny changes break prod too — one deleted null check, one flipped default is enough. Still run all 6 steps. |
| "Looks fine, just PUSH" | "Looks fine" is not evidence. A verdict made without reading the real diff is void — run `git diff` first. |
| "We're in a hurry, ship first" | Deadline / time pressure doesn't change the failure path. The more rushed you are, the more you must check the circuit breaker (step 5) first. |
| "It passed locally" | Local ≠ existing users' cache / database / historical data. User impact (step 3) must be checked separately. |
| "We'll deal with rollback later" | No rollback plan = step 5 gap = default HOLD. |
| Padding an inapplicable dimension | Write "none" and skip it; padding buries the real risks. |

## 危险信号 Red Flags —— 命中就倾向 HOLD

- Drawing a verdict before reading the real diff.
- Can't name the least-confident line in step 1 — you either didn't understand the change or are avoiding it.
- No rollback / feature toggle (step 5).
- Touching DB schema, migration, cache format, persisted format, or a public API contract, but only saying "should be fine".
- Substituting "should / probably / usually won't" for evidence.

**Any one of these → mark "uncertain", force the verdict down to HOLD, and name the first thing to fix before release.**

---

## English (summary)

Before `git push` (or anything that ships code to prod), run a final human-style **risk gate** as a senior release engineer / SRE. **Judge only from the real diff** (`git diff`, `git diff --staged`, `git log @{u}..HEAD`, `git diff @{u}..HEAD`) — if you can't see it, ask; never review from imagination. When unsure, say so and prefer **HOLD** over a blind **PUSH**. This is review, not execution: it outputs a verdict + reasoning; a human decides whether to push, and the skill never runs `git push` for you.

Walk six steps: (1) **risk intuition** — the one line you're least sure about and why; (2) unverified **assumptions**, **blind spots**, uncovered **edge cases**; (3) **user impact** — can existing users break/confuse after upgrade via data compatibility (cache, DB schema/migration, persisted format, API contract) or changed habits; (4) the most likely + highest-impact **failure path** if this hits prod now; (5) **circuit breaker** — is rollback ready and is there a feature toggle to kill it instantly; (6) the one **missing pre-release check** still owed. Then run **self-contrast**: list 3 pieces of evidence that could overturn "safe to ship" (score 1–5) and downgrade if any is credible. End with `PUSH`/`HOLD` inside markers, e.g. `▶︎▶︎HOLD▶︎▶︎`; on HOLD, name the first thing to fix.
