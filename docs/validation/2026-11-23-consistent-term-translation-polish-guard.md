# consistent-term-translation-polish-guard validation

Date: 2026-11-23. Scope: user-supplied Universal Term Consistency Guard,
packaged as a new portable skill; no upstream code or external terminology
source was imported. Plugin version remains 0.2.0; no publication was requested.

## Interpretation of the supplied rules

- A term is keyed by source expression and contextual sense. Identical spelling
  alone does not merge a bank and a river bank. Distinct expressions remain
  separate unless reliable definitions support an alias relationship.
- Aliases may appear in the EN→ZH first-mention annotation and the final table;
  subsequent prose uses the primary term. This reconciles the requested
  first-mention format with the rule that aliases do not circulate in prose.
- Normal grammatical inflections are allowed. Explicit output contracts take
  precedence over default annotations/tables. Existing visible glossaries are
  reused; unseen future sessions are not promised persistent memory.

## Method and predeclared criteria

Session-native `collaboration.spawn_agent`, fresh `fork_turns="none"` agents,
with inherited model/effort and no overrides. No external paid runner was used.
Eight synthetic requests were prepared with a manual rubric before the skill
was written. The baseline had only the requests; the guided agent additionally
read the new SKILL.md. Neither received the rubric, the other's answers, or the
authoring conversation. Both had no browsing access in the test instructions.

The first fixture's C description mistakenly assigned the geographical sense
to the balance sentence; the initial baseline correctly questioned that input.
That run is excluded from the comparison. The definition was corrected to
financial senses in sentences 1–2 and geographical sense in sentence 3, and a
fresh baseline used the corrected inputs below. The guided run used those same
corrected inputs. No instruction was added to force a particular glossary
layout in the raw translation requests; that default is supplied by the skill.

Criteria: respect chosen primary terms and distinct senses; annotate EN→ZH
first mentions and supply the default five-column glossary for technical
translation; preserve code; use grammatical English inflections; ask before
locking an unresolved core term; honor exact JSON; never invent an acronym
expansion or persistent memory; avoid a glossary for ordinary greetings.

## Observed results

| Case | Baseline observation | Guided observation and manual result |
| --- | --- | --- |
| A | Kept 尺度定律 and code; omitted source/alias first annotation and glossary. | PASS: annotated the title once, retained 尺度定律 in later prose, kept fine-tuning/alignment distinct, preserved code, added five-column table. |
| B | Respected enable/tactic/strategy and natural inflections; no glossary. | PASS: same term choices, natural enables/tactics forms, no Chinese parentheticals in English prose, added glossary. |
| C | Correctly separated bank senses and preserved API; no glossary or English full-form annotation. | PASS: separate sense rows, application programming interface/API bound to 应用程序编程接口; no conflation. |
| D | Asked the user to choose and withheld final translation. | PASS: asked for the core term choice and waited; no invented audience/authority rationale. |
| E | Exact requested JSON. | PASS: exact title/summary JSON, no extra glossary; parsed independently with json.loads. |
| F | Preserved unknown NEX and both supplied LLM expansions; no glossary. | PASS: did not invent NEX expansion; used distinct Chinese names for the colliding LLM expansions and recorded separate rows, with the synthetic term labeled provisional. |
| G | Reused alignment/fine-tuning and accurately limited new-session continuity; no glossary. | PASS: same semantic behavior plus glossary; no memory write or permanent-memory claim. |
| H | Translated the greeting directly. | PASS: direct translation, no glossary or unnecessary clarification. |

The observed additions are mainly first-mention annotation and glossary
coverage. Several semantic safeguards already passed in the baseline. This is
one run per condition with eight cases sharing each agent's context, manually
scored by the author without blinding. It is a bounded behavior check, not a
statistical quality comparison or proof of universal translation accuracy.

## Repository verification

- Four plugin/marketplace JSON manifests parse.
- All 20 skills pass the prescribed quick_validate.py using the existing
  `/Users/joejiang/miniconda3/bin/python3` (PyYAML 6.0.3). The default Homebrew
  Python lacks PyYAML; no dependency was installed and no environment changed.
- Six Superpowers and four Google Stitch port checks pass.
- All 20 directory/frontmatter/display names, UI summary lengths, and supplied
  default-prompt identifiers agree. Manifest versions remain aligned, and the
  Claude plugin/marketplace descriptions agree.
- Local file links in the changed README, new skill, and this report resolve;
  git diff --check and whitespace checks including new files pass.
- The prescribed plugin-creator/scripts/validate_plugin.py was attempted but
  is absent in this environment (exit 2). Native plugin ingestion remains
  unverified; JSON and skill checks do not substitute for it.

Automatic selection in the three clients, native plugin installation,
translation of rendered PPT/PDF/Word artifacts, online terminology research,
cross-model generalization, and durable cross-session storage were not tested.
No commit, push, global installation, or publication was performed.

Tested SKILL.md SHA-256: `56a9683645a72436b8410314019294b3a94d666e68100a14770903c95d6196d9`.
Raw local answer artifacts: `/private/tmp/polish-translation-guard-eval/`
(`baseline-corrected.md`, `guided.md`, `rubric.md`). These temporary outputs
are not runtime dependencies; reusable requests and criteria are retained here.

## Reusable test requests

The following cases are independent. Perform the actual request in each case.
Source examples are synthetic. Do not claim external verification. For a guided
run, read [the skill](../../skills/consistent-term-translation-polish-guard/SKILL.md)
first; for a baseline, do not load it. Do not browse or load other skills.

````text
## A
翻译成中文，面向机器学习工程师。既有术语约定：Scaling Law 主译名为“尺度定律”，常见别名是“缩放定律”“规模定律”。保留原文 Markdown 和代码。
### Scaling Law
The Scaling Law guides training. The Scaling Law does not replace evaluation. Fine-tuning and alignment are different processes.
`config.scaling_law = "Scaling Law"`

## B
翻译成英文，用于技术管理报告。既有术语约定：在本系列中，“赋能”译为 enable，“策略”译为 tactic，“战略”译为 strategy。
该平台赋能团队，新的工具继续赋能团队。战略决定方向，策略决定具体行动。请润色得自然。

## C
翻译成中文。本文的 source definitions 如下：bank 在前两句指金融机构，在第三句指河岸；API 全称为 application programming interface。
The bank exposes an application programming interface (API). The API returns the bank balance. The sensors on the river bank do not use the API.

## D
翻译这份系列报告。本地编辑说明：本系列中 Scaling Law 存在两个同等获认可的候选主译名“缩放定律”和“尺度定律”；没有约定、受众偏好或其他选择依据。本术语是标题和全文核心。
Scaling Law: Why the Scaling Law matters.

## E
翻译成英文，只返回 JSON 对象，键为 title、summary，不得新增字段或块外内容。已选术语：推理=inference。
标题：推理服务
摘要：推理服务提供推理结果。

## F
把两段独立短文翻成中文：
F1: We use NEX to route requests. NEX is an internal acronym; its expansion is not provided.
F2: The LLM (large language model) and LLM (linear logistics model) are distinct systems in this document. Both LLM systems are evaluated separately.

## G
续译同一系列（可见术语表：“对齐”=alignment，“微调”=fine-tuning）。翻成英文：对齐不是微调，微调也不自动保证对齐。
然后单独回答：如果下次开启一个看不到本次术语表的新对话，你能否保证自动沿用？

## H
翻译成中文：Good morning. See you tomorrow.
````
