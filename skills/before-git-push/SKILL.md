---
name: before-git-push
description: Use before running git push, or when the user asks to push / ship / deploy / 上线 / 推送 changes that could reach production — a final risk gate to catch what is most likely to break prod before code leaves the local machine. Triggers - "push this / ship it / ready to push? / 可以 push 了吗 / 上线前检查 / 这次改动能推吗", pre-push review, pre-release gate, production safety, don't break prod, rollback readiness, feature toggle.
metadata:
  language: bilingual
---

# before-git-push（push 前最后一道人工把关）

## 这个 skill 做什么

在 `git push`（或任何 ship 到 production 的动作）之前，以 **senior Release Engineer / SRE** 视角做最后一道 **risk gate（风控闸门）**：只依据 **real diff（真实 diff）** 判断本次改动的 **fragile line（最脆弱一行）**、**backward-compatibility（老用户兼容）** 风险、最可能击穿的 **failure path（失败路径）**、以及 **rollback（回滚）** 与 **feature toggle（功能开关）** 是否就绪，最后给出明确的 **PUSH / HOLD** verdict。

**核心原则 core principles：**

- **Diff-grounded（只基于 real diff 判断）。** 先看 `git diff`；看不到 diff 就要求补充，绝不凭空评审、不臆测、不粉饰。
- **When unsure, prefer HOLD.** 没把握就标注 "uncertain（不确定）"，宁可 HOLD，不可盲目 PUSH。
- **Review, not execution（只审查，不执行）。** 本 skill 只产出 PUSH/HOLD verdict 与理由；是否真的 push 由人决定，skill 绝不代替用户执行 `git push`。

## 何时使用

- 即将 `git push` / 提 PR / 上线 release，想在推之前过一遍 risk。
- 用户说「可以 push 了吗」「这次改动能推吗」「上线前帮我检查一下」「别把 production 搞崩」。
- 关键词：pre-push review / pre-release gate / 上线前检查 / rollback（回滚）/ feature toggle / production safety。

**不适用：**

- 纯本地实验、不打算 push 的改动。
- 只想让人写 commit message，或做与 risk 无关的代码格式整理。

## 审查步骤（think step by step，逐条推导并给出理由）

**先看 real diff 再开始：** staged 与 unstaged 的 diff（`git diff`、`git diff --staged`），以及相对远端尚未推送的 commits 及其 diff（`git log @{u}..HEAD`、`git diff @{u}..HEAD`）。无法读取 diff 时先说明并要求补充，不要凭空评审。

1. **Risk intuition（风险直觉）** — 通读本次改动，指出你心里最发虚、最没底的那一行代码或那段逻辑（给出 file 与 line / function），说明它为什么让你不安。
2. **Assumptions & blind spots（假设与盲区）** — 列出本次改动依赖但尚未验证的 unverified assumptions、你没看到的 blind spots，以及未覆盖的 edge cases（null / 并发 concurrency / 超时 timeout / 超大输入 oversized input / 失败重试 retry 等）。
3. **User impact（用户视角）** — 老用户升级后是否可能因 data compatibility（cache 缓存、DB schema / migration 迁移、persisted format 持久化格式、API contract 契约）或操作习惯改变而报错、行为异常或懵掉？逐项判断。
4. **Failure path（失败路径）** — 如果现在直接上 production、直达用户，最可能被击穿的 failure path 是什么？按 "最可能 × 影响最大（blast radius）" 排序，写明 trigger 条件与用户可见后果。
5. **Circuit breaker（熔断准备）** — 针对上面最危险的改动，rollback（回滚）方案是否就绪？是否有 feature toggle / kill switch 可即时关闭？若没有，明确点出这是上线前的 gap（缺口）。
6. **Missing checks（缺失的关键检查）** — 上线前还必须补做哪一项关键 check（tests / monitoring & alerting 监控告警 / canary 灰度 / migration rehearsal 迁移演练 / performance validation 性能验证）？确无 gap 则写 "无"；不适用的维度直接跳过，不要凑数。

## 反向验证 Self-Contrast（防止误判为 "safe"）

给出初步 verdict 后，主动列出 **3 条可以推翻 "本次改动 safe to ship" 的证据**，各按 confidence（可信度）打分（1–5）；若任一得分 ≥3，或合计明显偏高，据此下调 verdict 并说明修正。

## 输出契约 Output Contract

- 先按步骤 1–6 给出简明结论（每条 1–3 句，标出对应 file / line）。
- 再给出 self-contrast 的 3 条证据与 confidence 打分。
- 最后给出总体 verdict，把 `PUSH` 或 `HOLD` 放在 markers 之间，例如 `▶︎▶︎HOLD▶︎▶︎` 或 `▶︎▶︎PUSH▶︎▶︎`，否则视为无效输出。
- **HOLD 时** 用一句话写明放行前必须先解决的第一件事（first thing to fix）。

## 常见错误（Rationalization → Reality）

| 借口 Rationalization | 现实 Reality |
|---|---|
| "改动很小，不用审" | 小改动照样搞崩 production：一处删掉的 null check、一个改了 default 的 flag 就够。仍要跑完 6 步。 |
| "看着没问题，直接 PUSH" | "看着没问题" 不是 evidence。没读 real diff 的判断一律作废——先 `git diff`。 |
| "催得急，先推了再说" | Deadline / 时间压力不改变 failure path。越急越要先问 circuit breaker（步骤 5）到位没。 |
| "本地测过了" | 本地 ≠ 老用户的 cache / database / 历史数据。User impact（步骤 3）必须单独过。 |
| "回滚以后再说" | 没有 rollback 方案 = 步骤 5 gap = 默认 HOLD。 |
| 把不适用的维度硬凑一段 | 不适用直接写 "无" 并跳过；凑数会淹没真正的 risk。 |

## 危险信号 Red Flags —— 命中就倾向 HOLD

- 没看 real diff 就开始下 verdict。
- 步骤 1「最发虚的一行 / fragile line」答不出来——要么没读懂改动，要么在回避。
- 步骤 5 rollback / feature toggle 都没有。
- 动到 DB schema、migration、cache format、persisted format、对外 API contract，却只说 "应该没事"。
- 用 "应该 / 大概 / 一般不会（should / probably）" 代替 evidence。

**命中任一条：先标注 "uncertain（不确定）"，把 verdict 压到 HOLD，并写明放行前要先补的那一件事。**

---

## English (summary)

Before `git push` (or anything that ships code to prod), run a final human-style **risk gate** as a senior release engineer / SRE. **Judge only from the real diff** (`git diff`, `git diff --staged`, `git log @{u}..HEAD`, `git diff @{u}..HEAD`) — if you can't see it, ask; never review from imagination. When unsure, say so and prefer **HOLD** over a blind **PUSH**. This is review, not execution: it outputs a verdict + reasoning; a human decides whether to push, and the skill never runs `git push` for you.

Walk six steps: (1) **risk intuition** — the one line you're least sure about and why; (2) unverified **assumptions**, **blind spots**, uncovered **edge cases**; (3) **user impact** — can existing users break/confuse after upgrade via data compatibility (cache, DB schema/migration, persisted format, API contract) or changed habits; (4) the most likely + highest-impact **failure path** if this hits prod now; (5) **circuit breaker** — is rollback ready and is there a feature toggle to kill it instantly; (6) the one **missing pre-release check** still owed. Then run **self-contrast**: list 3 pieces of evidence that could overturn "safe to ship" (score 1–5) and downgrade if any is credible. End with `PUSH`/`HOLD` inside markers, e.g. `▶︎▶︎HOLD▶︎▶︎`; on HOLD, name the first thing to fix.
