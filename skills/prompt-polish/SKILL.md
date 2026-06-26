---
name: prompt-polish
description: Use when a user hands you a raw question or task and wants it rewritten into stronger bilingual LLM prompts. Triggers - "帮我优化提示词 / 把这个问题改写成更好的 prompt / 提示词重构 / 提示词策略优化 / optimize this prompt / prompt polishing", or any ask to make a question more likely to get a correct, well-formatted answer. Covers reasoning, MCQ, extraction, professional/compliance, creative, structured-output and vague-requirement tasks.
---

# Prompt Polish（提示词策略优化）

## 这个 skill 做什么

输入一个**原始问题/任务**，先判断它属于哪种任务类型，再为该类型选定一组**text-only prompt-engineering strategies（纯文本提示词策略）**，把这些策略编织进两条语义一致的提示词里，**输出 English Prompt 和中文提示词两份成品**。

**核心原则：你的整条回复就是那一个代码块，代码块内只有 English Prompt 和中文提示词，别的什么都不写。** 你在为用户造可复用的提示词，不是在替他回答原始问题。

## 何时使用

- 用户给你一个问题/任务，希望"改写成更好的 prompt"「优化提示词」「提示词重构」
- 用户希望某个提问更容易让大模型答对、答得格式正确
- 关键词：prompt polish / optimize prompt / 提示词工程 / 改写提问

**不适用：**
- 用户想要你**直接回答**那个原始问题（那就直接答，别改写）
- 与 LLM 提示无关的写作/编辑任务

## 输出契约（最重要）

> 你的整条回复 = **一个代码块**。块内必须包含两份可直接复制使用的提示词：**English Prompt** 和 **中文提示词**；**块外零字符**。

具体即：

- 代码块**之前**不写任何引言、寒暄、"这是改写后的提示词"之类的话。
- 代码块**之后**不写任何说明、解读、点评，**尤其不要把原始问题的答案算出来或泄露**（你在造模板，不是在答题）。
- 代码块内固定使用这两个小标题：`English Prompt`、`中文提示词`。先英文，后中文。
- 两份提示词必须语义一致，但不是逐字硬翻译；英文版优先使用自然、技术准确的英文表达，中文版优先使用自然、清晰的中文表达。
- 专有技术名词保留英文原文，并可在中文后补括号解释，例如 `Chain-of-Thought (CoT)（链式思考）`、`Tree of Thoughts (ToT)（思维树）`、`ReAct`、`Prompt Chaining（提示链）`。
- 把所选策略**直接落进提示词正文**（角色句、步骤、答案锚点等），而不是在块外描述"我用了哪些策略"。
- 默认用 ``` 包裹；若提示词正文本身含 ``` ，改用 `~~~` 包裹，保证整体仍是单一代码块。
- 分类判断、组合选择都是你的**内部思考**，不写进回复。

例外：仅当用户**明确要求**"讲解你为什么这么改/解释策略"时才补充说明（用户指令优先于本契约）。

## 工作流程（内部执行，不输出过程）

1. **判类型** — 把原始问题归入下表某一类型（取最主要的一类；可由两类合并，但策略总数控制在 2–4 个）。
2. **选组合** — 直接采用下方「任务类型 → 策略组合」表里的那一组（通常 2–4 个）。除非有明确理由，否则不要再额外叠加策略——堆得越多越互相干扰、提示越臃肿。
3. **重构** — 用「策略速查」把每个策略写成提示词里的具体句子/步骤，并把**原始问题的具体内容填进去**（产出是成品，不留 `{占位符}`，除非那是留给终端用户填写的字段）。分别生成 `English Prompt` 和 `中文提示词`，两份都要完整可用。
4. **只输出提示词** — 按输出契约，整条回复只给那个代码块。

**任务过于模糊、信息不足时**：不要自己回头问用户。改用「翻转交互」策略——把"先澄清再执行"**写进重构后的提示词里**（让目标模型先向用户提问），整条回复仍然只是一个代码块。

## 任务类型 → 策略组合（纯文本版）

| 任务类型 | 推荐组合 | 核心优势 |
|---|---|---|
| 选择题 / 客观判定 | Option-First MCQ（倒装选项） + Symbolic Placeholder（符号占位符） + Self-Contrast（反向验证） | 降低位置偏差 + 精准提取答案 + 自我排错 |
| 专业领域 / 合规生成 | Role-Rule Double Bind（角色+规则双保险） + Knowledge Time-Stamp（知识时间戳） + Mirror Test（镜子测试） | 专业知识检索 + 时效校准 + 二次优化 |
| 复杂推理求解 | Chain-of-Thought (CoT)（链式思考） + Tree of Thoughts (ToT)（思维树） + Self-Contrast（反向验证） | 分步推导 + 多路径验证 + 自我反驳 |
| 原理 / 框架型推理（物理化学、数学定理、需先选对方法） | Step-Back Prompting（退一步提示） + Chain-of-Thought (CoT)（链式思考） + Self-Contrast（反向验证） | 先锁定正确原理 + 分步推导 + 自我排错 |
| 批量标准化任务 | Meta-Prompting（元提示词） + Layered Prompt（分层提示） + Prompt Repetition（提示重复） | 自优化提示词 + 清晰解析 + 稳定遵循 |
| 创意与事实融合 | Prompt Chaining（提示链） + Self-Contrast（反向验证） + Mirror Test（镜子测试） | 分阶段先发散后收敛 + 事实自查 + 润色 |
| 高精度问答 | Role-Rule Double Bind（角色+规则双保险） + Self-Contrast（反向验证） + Mirror Test（镜子测试） | 三重保险降低错误率 |
| 结构化输出 | Layered Prompt（分层提示） + Symbolic Placeholder（符号占位符） + Prompt Repetition（提示重复） | 确保格式一致性 |
| 减少幻觉 | Knowledge Time-Stamp（知识时间戳） + Self-Contrast（反向验证） + Mirror Test（镜子测试） | 多层事实核查 |
| Agent / 工具调用 | ReAct + Prompt Chaining（提示链） | 系统化处理多步骤任务（有工具时最佳） |
| 需求模糊 | Flipped Interaction（翻转交互） → Layered Prompt（分层提示） →（在提示词内）执行 | 先澄清后执行 |

> 这些是默认起点，不是铁律。命中多类型就合并取并集后裁剪到 2–4 个；策略堆太多会互相干扰。

## 策略速查（15 项，纯文本可写入提示词）

| 策略 | 如何写进提示词（一句话） | 适合 |
|---|---|---|
| Prompt Repetition（提示重复） | 在提示首尾各重申一次核心指令/关键约束（共 2–3 次） | 标准化、格式控制、指令遵循 |
| Option-First MCQ（倒装选项） | 把候选选项放到问题**之前**，先锚定答案范围再提问 | 选择题、分类、客观题 |
| Role-Rule Double Bind（角色+规则双保险） | "你是 X 领域专家，严格遵守规则 Y；若违反先答'错误'并自我纠正" | 专业问答、合规、高精度 |
| Self-Contrast（反向验证） | "先给答案 → 列 3 条可推翻它的证据并打分(1–5) → 据此复核修正" | 事实问答、减少幻觉、高风险判断 |
| Symbolic Placeholder（符号占位符） | "把最终答案放在 ▶︎▶︎answer▶︎▶︎ 之间，否则视为无效输出" | 抽取、精准提答、结构化、可解析 |
| Knowledge Time-Stamp（知识时间戳） | "截至 YYYY-MM ……；此后的新信息请标注'可能已过期'" | 时效性问答、行业动态 |
| Layered Prompt（分层提示） | 按 **目标 → 规则 → 示例 → 格式** 四层组织指令 | 多约束复杂指令、长文本 |
| Mirror Test（镜子测试） | 末尾加"再读一遍你的回答，你会改哪一句？只输出修改后的整句" | 校对、润色、最终质检 |
| Flipped Interaction（翻转交互） | "执行前先就以下 3 点向我提问澄清，再按我的回复执行" | 需求模糊、个性化定制 |
| Chain-of-Thought (CoT)（链式思考） | "think step by step，逐步推导并给出每一步理由" | 数学、逻辑、多步推理 |
| Prompt Chaining（提示链） | 拆成【步骤1 → 步骤2 → 步骤3】，前一步输出喂给下一步（写成单条顺序提示） | 长文摘要、多步分析、流水线 |
| Meta-Prompting（元提示词） | "先针对这个会反复执行的任务生成一个更优提示词，再用它执行" | 重复性任务、提示词自优化 |
| Tree of Thoughts (ToT)（思维树） | "列 3 条推理路径 → 各评可行性(1–10) → 选最优分步推导 → 失败则回溯次优" | 高难推理、决策、规划 |
| Step-Back Prompting（退一步提示） | 先别急着解题：先让模型抽象出「这类问题背后的通用原理 / 定律 / 公式」并写出来，再用它分步求解 | 物理化学 / 数学定理应用、需先选对方法或框架、易被表面细节带偏的题 |
| ReAct | "按 思考 → 行动 → 观察 循环：先想做什么、再行动、再判断是否调整"（有工具/检索时最佳） | Agent、工具调用、检索+推理 |

> 每项的完整模板、原理与来源见 [references/strategies.md](../../references/strategies.md)。

## 一个完整示例

**原始输入：** `下面哪个数是质数？51、57、61、91`

**（内部判断，不写出）** 类型 = 选择题/客观判定 → 组合 = Option-First MCQ（倒装选项） + Symbolic Placeholder（符号占位符） + Self-Contrast（反向验证）

**你的整条回复就是下面这个代码块（注意：不解题、不泄露答案、块外无字）：**

```
English Prompt

Choose which of the following candidates is a prime number:
A. 51    B. 57    C. 61    D. 91

Question: Which of the four numbers above is prime?

Answering requirements:
1. Test each candidate independently by trial division: divide by every prime p where p x p <= n (2, 3, 5, 7, ...). If divisible, mark it composite and show the factorization; if none divide it, mark it prime.
2. After giving a clear answer, list 3 pieces of evidence that could overturn that answer and rate each one's credibility from 1 to 5. If the total score is greater than 0, recheck and revise the answer if needed.
3. Put the final answer letter inside ▶︎▶︎answer▶︎▶︎, for example ▶︎▶︎C▶︎▶︎. Otherwise the output is invalid.

中文提示词

请从下列候选中判断哪个数是质数：
A. 51    B. 57    C. 61    D. 91

问题：上面四个数中，哪一个是质数？

作答要求：
1. 先对每个候选独立做试除检验：用所有满足 p×p ≤ n 的质数 p（2、3、5、7……）依次试除；能整除则为合数并写出分解式，都不能整除则为质数。
2. 给出明确答案后，再列出 3 条可能推翻该答案的证据，并为每条可信度打分（1–5）；若总分 > 0，据此复核并在必要时修正答案。
3. 必须把最终答案（对应字母）放在 ▶︎▶︎answer▶︎▶︎ 之间，例如 ▶︎▶︎C▶︎▶︎，否则判为无效输出。
```

## 常见错误

| 错误 | 纠正 |
|---|---|
| 在代码块前后加引言/解读/点评 | 整条回复只给代码块，块外零字符 |
| 把原始问题的答案算出来或泄露进输出 | 你在造可复用模板，不是答题；让目标模型去算 |
| 只输出中文或只输出英文 | 代码块内必须同时包含 `English Prompt` 和 `中文提示词` 两份完整提示词 |
| 把专有名词翻译到看不出原文 | 保留英文技术名词原文，例如 `Chain-of-Thought (CoT)`、`Tree of Thoughts (ToT)`、`Self-Contrast` |
| 套用需要 API/解码控制的策略（Temp-Decay Sampling、多次独立运行、Dynamic Few-Shot） | 只用纯文本策略；这三项已被排除（见下） |
| 一口气堆 5+ 个策略 | 控制在 2–4 个，匹配类型即可，堆太多互相干扰 |
| 任务模糊时自己回头问用户 | 把"先澄清后执行"写进双语提示词里（Flipped Interaction），仍只输出一个代码块 |
| 输出里残留 `{占位符}` | 产出是成品；把原始问题的具体内容填进去（留给终端用户填的字段除外） |

## 被排除的策略

以下 3 项需要**多轮运行 / 多次独立采样 / 逐 token 解码控制**，无法塞进单次模型调用的双语提示词，故本 skill 默认不用：

- **Dynamic Few-Shot（动态少样本）**（需先跑一轮再抽取自身输出做样本）
- **Self-Consistency（自洽性检查）**（需多次独立运行后投票；单提示场景下用 `Self-Contrast（反向验证）` 替代）
- **Temp-Decay Sampling（温度衰减解码）**（需按 token 调温度，属解码参数）

若用户**确实掌握 API/解码控制或可多轮编排**，这三项的原始模板见 [references/strategies.md](../../references/strategies.md) 末尾，可作为提示词之外的"设置与流程"建议提供——但那已超出"只输出一个代码块，内含 English Prompt 和中文提示词"的默认契约，需先与用户确认。
