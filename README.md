# prompt-polish

> Turn a rough question into a high-performing, ready-to-paste LLM prompt.

**English** | [中文](#中文版)

`prompt-polish` is a [Claude Code](https://code.claude.com) skill / plugin. Give it a raw question or task; it detects the task type, selects a matching combo of research-backed, **text-only** prompt-engineering strategies, and returns **only the rewritten prompt** — a single code block you can copy and paste.

> It builds you a better prompt; it does **not** answer the question for you.

## Install

### Option A — as a plugin (recommended)

```text
/plugin marketplace add host452b/prompt-polish
/plugin install prompt-polish@prompt-polish
```

- After install, invoke `/prompt-polish:prompt-polish`, or just hand Claude your raw question and let it trigger automatically.
- Updates: this repo pins no `version`, so every new commit counts as an update — run `/plugin update` to get the latest.

### Option B — manual (clone + symlink)

```bash
git clone https://github.com/host452b/prompt-polish.git
ln -s "$(pwd)/prompt-polish" ~/.claude/skills/prompt-polish
```

Or drop the folder into a project's `.claude/skills/` to scope it to that project.

> Note: Claude Code has **no `npx`-style installer** for skills/plugins — use one of the two methods above.

## Usage

Send your raw question to a Claude that has the skill loaded, e.g. *"Polish this prompt: …"*. Its **entire reply is one code block** — the rewritten prompt itself, with no commentary, and it won't solve the original problem for you.

## How it works

1. **Classify** — reasoning, multiple-choice, professional / compliance, structured output, vague-requirement, etc.
2. **Select** — pick a 2–4 strategy combo from a task-type → combo table.
3. **Rewrite** — express each strategy as concrete role lines / steps / answer anchors and fill in your question.
4. **Output the prompt only** — a single code block, nothing outside it.

It ships **14 text-only strategies** (chain-of-thought, tree-of-thoughts, self-contrast verification, symbolic answer anchors, role + rules double-bind, flipped interaction, layered prompting, and more). Three strategies that need API / decoding control or multiple runs (dynamic few-shot, self-consistency, temperature-decay) are deliberately excluded, so the output is always one self-contained, copy-paste prompt.

## Structure

```text
prompt-polish/
├── SKILL.md                  # output contract + workflow + type→combo table + cheat sheet + example
├── references/strategies.md  # full strategy library (14) + combo change log + the 3 excluded ones
└── .claude-plugin/
    ├── plugin.json           # plugin manifest (single-skill plugin)
    └── marketplace.json      # self-contained marketplace catalog
```

See [references/strategies.md](references/strategies.md) for full strategy templates, rationale, and sources.

---

<a name="中文版"></a>

# 中文版

> 把一个粗糙的问题，变成一条高质量、可直接粘贴使用的 LLM 提示词。

[English](#prompt-polish) | **中文**

`prompt-polish` 是一个 [Claude Code](https://code.claude.com) skill / plugin：输入一个**原始问题 / 任务**，它会判断任务类型 → 选用一组**纯文本**提示词策略组合 → **只输出重构后的提示词**（一个代码块，复制即用）。

> 它在帮你造一个更好用的提示词，而不是替你回答问题。

## 安装

### 方式 A：作为插件安装（推荐）

```text
/plugin marketplace add host452b/prompt-polish
/plugin install prompt-polish@prompt-polish
```

- 安装后调用 `/prompt-polish:prompt-polish`，或直接把原始问题交给 Claude，由它按描述自动触发。
- 更新：本仓库未固定 `version`，因此每个新 commit 都算一次更新，运行 `/plugin update` 即可获取最新版。

### 方式 B：手动安装（clone + 软链）

```bash
git clone https://github.com/host452b/prompt-polish.git
ln -s "$(pwd)/prompt-polish" ~/.claude/skills/prompt-polish
```

也可以把目录放进某个项目的 `.claude/skills/` 下，仅在该项目内可用。

> 注：Claude Code 没有 `npx` 形式的 skill / plugin 安装方式，请使用上面两种之一。

## 用法

把原始问题发给已加载本 skill 的 Claude，例如「帮我优化这个提示词：……」。它的**整条回复就是一个代码块**——重构后的提示词本身，块外不写任何说明，也不会替你解出原题答案。

## 工作原理

1. **判类型** —— 选择题、复杂推理、专业 / 合规、结构化输出、需求模糊等。
2. **选组合** —— 按「任务类型 → 策略组合」表取一组 2–4 个纯文本策略。
3. **重构** —— 把策略写成提示词里的具体角色句 / 步骤 / 答案锚点，并填入原始问题。
4. **只输出提示词** —— 一个代码块，块外零字符。

共内置 **14 项纯文本策略**（链式思考、思维树、反向验证、符号占位符、角色规则双保险、翻转交互、分层提示等）。需要 API / 解码控制或多次运行的 3 项策略（动态少样本、自洽性、温度衰减解码）已排除，以保证输出始终是一条自包含、可直接复制的提示词。

## 结构

```text
prompt-polish/
├── SKILL.md                  # 主文件：输出契约 + 工作流 + 类型→组合表 + 策略速查 + 示例
├── references/strategies.md  # 完整策略库（14 项）+ 组合改动说明 + 被排除的 3 项
└── .claude-plugin/
    ├── plugin.json           # 插件清单（单技能插件）
    └── marketplace.json      # 自带 marketplace 目录
```

完整的策略模板、原理与来源见 [references/strategies.md](references/strategies.md)。
