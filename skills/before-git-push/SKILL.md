---
name: before-git-push
description: Use before running git push, or when the user asks to push / ship / deploy / 上线 / 推送 changes that could reach production — a final risk gate to catch what is most likely to break prod before code leaves the local machine. Triggers - "push this / ship it / ready to push? / 可以 push 了吗 / 上线前检查 / 这次改动能推吗", pre-push review, pre-release gate, production safety, don't break prod, rollback readiness, feature toggle.
metadata:
  language: bilingual
---

# before-git-push（push 前最后一道人工把关）

## 这个 skill 做什么

在 `git push`（或任何会把代码推向生产的动作）之前，以**资深发布工程师 / SRE** 的视角做最后一道人工风控：只依据**真实 diff** 判断本次改动最脆弱的地方、老用户兼容风险、最可能击穿的失败路径、回滚与功能开关是否就绪，最后给出明确的 **PUSH / HOLD** 建议。

**核心原则：**

- **只基于真实 diff 判断。** 先看 `git diff`；看不到 diff 就要求补充，绝不凭空评审、不臆测、不粉饰。
- **没把握就标注"不确定"，宁可 HOLD，不可盲目 PUSH。**
- **这是审查，不是执行。** 本 skill 只产出 PUSH/HOLD 建议与理由；是否真的 push 由人决定，skill 绝不代替用户执行 `git push`。

## 何时使用

- 即将 `git push` / 提 PR / 上线 / 发布，想在推之前过一遍风险。
- 用户说「可以 push 了吗」「这次改动能推吗」「上线前帮我检查一下」「别把生产搞崩」。
- 关键词：pre-push review / pre-release gate / 上线前检查 / 回滚 rollback / feature toggle / 生产安全。

**不适用：**

- 纯本地实验、不打算推送的改动。
- 只想让人写 commit message，或做与风险无关的代码格式整理。

## 审查步骤（think step by step，逐条推导并给出理由）

**先看真实改动再开始：** 已暂存与未暂存的 diff（`git diff`、`git diff --staged`），以及相对远端尚未推送的提交及其 diff（`git log @{u}..HEAD`、`git diff @{u}..HEAD`）。无法读取 diff 时先说明并要求补充，不要凭空评审。

1. **风险直觉** — 通读本次改动，指出你心里最发虚、最没底的那一行代码或那段逻辑（给出文件与行/函数），说明它为什么让你不安。
2. **假设与盲区** — 列出本次改动依赖但尚未验证的假设、你没看到的盲区，以及未覆盖的边界条件（空值、并发、超时、超大输入、失败重试等）。
3. **用户视角** — 老用户升级后是否可能因数据兼容问题（缓存结构、数据库 schema/迁移、持久化格式、API 契约）或操作习惯改变而报错、行为异常或懵掉？逐项判断。
4. **失败路径** — 如果现在直接上生产、直达用户，最可能被击穿的失败路径是什么？按"最可能且影响最大"排序，写明触发条件与用户可见后果。
5. **熔断准备** — 针对上面最危险的改动，回滚方案是否已就绪？是否有 Feature Toggle / 功能开关可即时关闭？若没有，明确点出这是上线前的缺口。
6. **缺失的关键检查** — 上线前还必须补做哪一项关键检查（测试、监控/告警、灰度、迁移演练、性能验证等）？确无缺口则写"无"；不适用的维度直接跳过，不要凑数。

## 反向验证（防止误判为"安全"）

给出初步结论后，主动列出 **3 条可以推翻"本次改动可安全上线"的证据**，各按可信度打分（1–5）；若任一得分 ≥3，或合计明显偏高，据此下调结论并说明修正。

## 输出契约

- 先按步骤 1–6 给出简明结论（每条 1–3 句，标出对应文件/行）。
- 再给出反向验证的 3 条证据与打分。
- 最后给出总体建议，把 `PUSH` 或 `HOLD` 放在标记之间，例如 `▶︎▶︎HOLD▶︎▶︎` 或 `▶︎▶︎PUSH▶︎▶︎`，否则视为无效输出。
- **HOLD 时**用一句话写明放行前必须先解决的第一件事。

## 常见错误（借口 → 现实）

| 借口 | 现实 |
|---|---|
| "改动很小，不用审" | 小改动照样搞崩生产：一处删掉的空值检查、一个改了默认值的开关就够。仍要跑完 6 步。 |
| "看着没问题，直接 PUSH" | "看着没问题"不是证据。没读真实 diff 的判断一律作废——先 `git diff`。 |
| "催得急，先推了再说" | 时间压力不改变失败路径。越急越要先问熔断准备（步骤 5）到位没。 |
| "本地测过了" | 本地 ≠ 老用户的缓存 / 数据库 / 历史数据。用户视角（步骤 3）必须单独过。 |
| "回滚以后再说" | 没有回滚方案 = 步骤 5 缺口 = 默认 HOLD。 |
| 把不适用的维度硬凑一段 | 不适用直接写"无"并跳过；凑数会淹没真正的风险项。 |

## 危险信号 —— 命中就倾向 HOLD

- 没看真实 diff 就开始下结论。
- 步骤 1「最发虚的一行」答不出来——要么没读懂改动，要么在回避。
- 步骤 5 回滚 / feature toggle 都没有。
- 动到数据库 schema、迁移、缓存格式、持久化格式、对外 API 契约，却只说"应该没事"。
- 用"应该 / 大概 / 一般不会"代替证据。

**命中任一条：先标注"不确定"，把结论压到 HOLD，并写明放行前要先补的那一件事。**

---

## English (summary)

Before `git push` (or anything that ships code to prod), run a final human-style risk gate as a senior release engineer / SRE. **Judge only from the real diff** (`git diff`, `git diff --staged`, `git log @{u}..HEAD`, `git diff @{u}..HEAD`) — if you can't see it, ask; never review from imagination. When unsure, say so and prefer **HOLD** over a blind **PUSH**. This is review, not execution: it outputs a verdict + reasoning; a human decides whether to push, and the skill never runs `git push` for you.

Walk six steps: (1) the one line you're least sure about and why; (2) unverified assumptions, blind spots, uncovered edge cases; (3) can existing users break/confuse after upgrade via data compatibility (cache, DB schema/migration, persisted format, API contract) or changed habits; (4) the most likely + highest-impact failure path if this hits prod now; (5) is rollback ready and is there a feature toggle to kill it instantly; (6) the one pre-release check still owed. Then list 3 pieces of evidence that could overturn "safe to ship" (score 1–5) and downgrade if any is credible. End with `PUSH`/`HOLD` inside markers, e.g. `▶︎▶︎HOLD▶︎▶︎`; on HOLD, name the first thing to fix.
