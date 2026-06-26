# polish

> Personal collection of curated, self-made agent skills.

**English** | [中文](#中文版)

`polish` is a Claude Code, Codex CLI, and Cursor CLI skill/plugin collection for selected personal skills. The repo/plugin package is named `polish`; individual skill names stay stable so existing triggers and installs do not break.

Currently included:

- `prompt-polish` - turns a rough question into high-performing, ready-to-paste bilingual LLM prompts.

## Install

### Claude Code - as a plugin

```text
/plugin marketplace add host452b/polish
/plugin install polish@polish
```

- Invoke the current skill with `/polish:prompt-polish`, or hand Claude a raw prompt and let the skill trigger automatically.
- Updates: this repo pins no `version`, so every new commit counts as an update. Run `/plugin update` to get the latest.

### Codex CLI - as a plugin

```bash
codex plugin marketplace add host452b/polish
codex plugin add polish@polish
```

Start a new Codex thread after installing so the skills in this collection are available for automatic triggering.

### Cursor CLI - as a skill

For the current `prompt-polish` skill:

```bash
git clone https://github.com/host452b/polish.git
mkdir -p ~/.cursor/skills
ln -s "$(pwd)/polish/skills/prompt-polish" ~/.cursor/skills/prompt-polish
```

The repo also includes `.cursor-plugin/plugin.json` for Cursor plugin consumers that read Cursor plugin manifests.

### Manual skill install

For the current `prompt-polish` skill:

```bash
git clone https://github.com/host452b/polish.git
mkdir -p ~/.claude/skills ~/.agents/skills ~/.cursor/skills
ln -s "$(pwd)/polish/skills/prompt-polish" ~/.claude/skills/prompt-polish
ln -s "$(pwd)/polish/skills/prompt-polish" ~/.agents/skills/prompt-polish
ln -s "$(pwd)/polish/skills/prompt-polish" ~/.cursor/skills/prompt-polish
```

Use plugin install when you want the whole collection as it grows. Use manual symlinks when you only want a specific skill in a specific tool or project.

## Skills

### `prompt-polish`

Give it a raw question or task. It detects the task type, selects a matching combo of research-backed, text-only prompt-engineering strategies, and returns only bilingual rewritten prompts: one code block with `English Prompt` and `中文提示词`.

It builds a better prompt; it does not answer the question for you.

How it works:

1. **Classify** - reasoning, multiple-choice, professional/compliance, structured output, vague requirements, etc.
2. **Select** - pick a 2-4 strategy combo from a task-type to combo table.
3. **Rewrite** - express each strategy as concrete role lines, steps, answer anchors, and fill in the original question.
4. **Output prompts only** - a single code block containing `English Prompt` and `中文提示词`, nothing outside it.

It ships 15 text-only strategies such as `Chain-of-Thought (CoT)`, `Step-Back Prompting`, `Tree of Thoughts (ToT)`, `Self-Contrast`, `Symbolic Placeholder`, `Role-Rule Double Bind`, `Flipped Interaction`, and `Layered Prompt`. Strategies that need API/decoding control or multiple runs are deliberately excluded so the output stays copy-pasteable.

See [references/strategies.md](references/strategies.md) for full strategy templates, rationale, and sources.

## Structure

```text
polish/
├── references/strategies.md  # prompt-polish strategy library
├── skills/prompt-polish/
│   └── SKILL.md              # canonical prompt-polish skill contract
├── .claude-plugin/
│   ├── plugin.json           # Claude plugin manifest
│   └── marketplace.json      # self-contained marketplace catalog
├── .codex-plugin/
│   └── plugin.json           # Codex CLI plugin manifest
└── .cursor-plugin/
    └── plugin.json           # Cursor plugin manifest
```

When adding new personal skills, keep each skill name stable under `skills/<skill-name>/`. The repo/plugin package can remain `polish` while skills inside it grow independently.

---

<a name="中文版"></a>

# 中文版

> 个人精选自制 agent skills 集合。

[English](#polish) | **中文**

`polish` 是一个面向 Claude Code、Codex CLI 和 Cursor CLI 的个人 skill/plugin 集合。repo/plugin 包名叫 `polish`；里面每个 skill 的名字保持稳定，避免已有触发方式和安装路径失效。

当前包含：

- `prompt-polish` - 把粗糙问题改写成高质量、可直接粘贴使用的中英双语 LLM 提示词。

## 安装

### Claude Code：作为插件安装

```text
/plugin marketplace add host452b/polish
/plugin install polish@polish
```

- 当前 skill 可用 `/polish:prompt-polish` 调用，也可以直接把原始 prompt 交给 Claude，由它按描述自动触发。
- 更新：本仓库未固定 `version`，因此每个新 commit 都算一次更新，运行 `/plugin update` 即可获取最新版。

### Codex CLI：作为插件安装

```bash
codex plugin marketplace add host452b/polish
codex plugin add polish@polish
```

安装后开启新的 Codex 对话，让这个集合里的 skills 进入可触发列表。

### Cursor CLI：作为 skill 安装

安装当前 `prompt-polish` skill：

```bash
git clone https://github.com/host452b/polish.git
mkdir -p ~/.cursor/skills
ln -s "$(pwd)/polish/skills/prompt-polish" ~/.cursor/skills/prompt-polish
```

仓库也包含 `.cursor-plugin/plugin.json`，供能读取 Cursor plugin manifest 的插件消费者使用。

### 手动安装（clone + 软链）

安装当前 `prompt-polish` skill：

```bash
git clone https://github.com/host452b/polish.git
mkdir -p ~/.claude/skills ~/.agents/skills ~/.cursor/skills
ln -s "$(pwd)/polish/skills/prompt-polish" ~/.claude/skills/prompt-polish
ln -s "$(pwd)/polish/skills/prompt-polish" ~/.agents/skills/prompt-polish
ln -s "$(pwd)/polish/skills/prompt-polish" ~/.cursor/skills/prompt-polish
```

如果你想随着仓库扩展使用整个集合，优先用 plugin 安装；如果只想在某个工具或项目里启用单个 skill，再用手动软链。

## Skills

### `prompt-polish`

输入一个原始问题或任务。它会判断任务类型，选择一组匹配的、纯文本提示词工程策略，然后只输出中英双语重构提示词：一个代码块，内含 `English Prompt` 和 `中文提示词`。

它是在帮你造更好的 prompt，不会替你回答原题。

工作流程：

1. **判类型** - 复杂推理、选择题、专业/合规、结构化输出、需求模糊等。
2. **选组合** - 按任务类型选择 2-4 个策略组合。
3. **重构** - 把策略写成具体角色句、步骤、答案锚点，并填入原始问题。
4. **只输出提示词** - 一个代码块，包含 `English Prompt` 和 `中文提示词`，块外零说明。

当前内置 15 项纯文本策略，例如 `Chain-of-Thought (CoT)`、`Step-Back Prompting`、`Tree of Thoughts (ToT)`、`Self-Contrast`、`Symbolic Placeholder`、`Role-Rule Double Bind`、`Flipped Interaction`、`Layered Prompt`。需要 API/解码控制或多次运行的策略被排除，保证输出始终可直接复制使用。

完整策略模板、原理与来源见 [references/strategies.md](references/strategies.md)。

## 结构

```text
polish/
├── references/strategies.md  # prompt-polish 策略库
├── skills/prompt-polish/
│   └── SKILL.md              # prompt-polish 的主行为契约
├── .claude-plugin/
│   ├── plugin.json           # Claude 插件清单
│   └── marketplace.json      # 自带 marketplace 目录
├── .codex-plugin/
│   └── plugin.json           # Codex CLI 插件清单
└── .cursor-plugin/
    └── plugin.json           # Cursor 插件清单
```

以后新增个人 skills 时，把每个 skill 的稳定入口放在 `skills/<skill-name>/` 下。外层 repo/plugin 包名继续叫 `polish`，里面的 skills 可以独立增长。
