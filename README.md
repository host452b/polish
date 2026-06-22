# prompt-polish

一个提示词策略优化 skill：输入一个**原始问题/任务**，自动判断任务类型 → 选用一组**纯文本提示词策略**组合 → **只输出重构后的提示词**（一个代码块，复制即用）。

> 它在帮你造一个更好用的提示词，而不是替你回答问题。

## 安装

### 方式 A：作为插件安装（推荐）

```text
/plugin marketplace add host452b/prompt-polish
/plugin install prompt-polish@prompt-polish
```

- 安装后调用：`/prompt-polish:prompt-polish`，或直接把原始问题交给 Claude，由它按描述自动触发。
- 更新：本仓库未固定 `version`，因此每个新 commit 都算一次更新，运行 `/plugin update` 即可获取最新版。

### 方式 B：手动安装（clone + 软链，单技能/自用）

```bash
git clone https://github.com/host452b/prompt-polish.git
ln -s "$(pwd)/prompt-polish" ~/.claude/skills/prompt-polish
```

也可以把目录放进某个项目的 `.claude/skills/` 下，仅在该项目内可用。

> 注：Claude Code 没有 `npx` 形式的 skill/plugin 安装方式，请使用上面两种之一。

## 用法

把原始问题发给已加载本 skill 的 Claude，例如「帮我优化这个提示词：……」。它的**整条回复就是一个代码块**——重构后的提示词本身，块外不写任何说明，也不会替你解出原题答案。

## 工作原理

1. **判类型** —— 归入选择题、复杂推理、专业/合规、结构化输出、需求模糊等任务类型之一。
2. **选组合** —— 按「任务类型 → 策略组合」表取一组 2–4 个纯文本策略。
3. **重构** —— 把策略写成提示词里的具体角色句/步骤/答案锚点，并填入原始问题。
4. **只输出提示词** —— 一个代码块，块外零字符。

共内置 **14 项纯文本策略**（链式思考、思维树、反向验证、符号占位符、角色规则双保险、翻转交互等）。需要 API/解码控制或多次运行的 3 项策略（动态少样本、自洽性、温度衰减解码）已排除，以保证输出始终是一条自包含、可直接复制的提示词。

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
