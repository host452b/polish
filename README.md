# polish

> Personal collection of curated, self-made, and adapted agent skills.

**English** | [中文](#中文版)

`polish` is a Claude Code, Codex CLI, and Cursor CLI skill/plugin collection for selected personal and adapted skills. The repo/plugin package is named `polish`; individual skill names stay stable so existing triggers and installs do not break.

Currently included:

- `prompt-polish` - turns a rough question into high-performing, ready-to-paste bilingual LLM prompts.
- `file-singlify` - scans a disk/folder/mount for duplicate files and duplicate directory copies, then proposes a single-copy plan (canonical copy + duplicate-to-canonical mapping) with a read-only dry-run report.
- `before-git-push` - a final pre-push risk gate: reviews the real diff as a release engineer and returns a PUSH or HOLD verdict before code reaches production.
- `superpowers-using-git-worktrees` - creates or reuses an isolated workspace before feature work or plan execution.
- `superpowers-brainstorming` - turns an idea into an approved design and implementation plan before coding begins.
- `superpowers-test-driven-development` - enforces the red-green-refactor cycle for feature and bug-fix work.
- `superpowers-systematic-debugging` - investigates root causes before proposing changes.
- `superpowers-verification-before-completion` - requires fresh evidence before success claims.
- `superpowers-writing-skills` - applies test-driven discipline to creating and maintaining agent skills.

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

### `file-singlify`

Point it at a disk, directory, or mount path. It detects duplicate files and whole duplicate directory copies left by repeated copying, backups, sync, and migration, then proposes a "singlify" plan: keep one canonical copy and map every duplicate to it.

- **Read-only, dry-run by default.** It never deletes, moves, overwrites, hardlinks, or symlinks. Any destructive action is a separate, human-confirmed step.
- **Directory-first.** A whole folder copied many times is the biggest space waste, so directory-level redundancy is detected and reported before per-file hashing.
- **Hash-confirmed.** Name/size/mtime only shortlist candidates; final "identical" verdicts come from content hashes (`md5`, `sha256`, or `both`).

The scan logic lives in `skills/file-singlify/scripts/scan_file_singlify.py` (markdown/json/csv output). See [skills/file-singlify/references/matching-rules.md](skills/file-singlify/references/matching-rules.md) and [skills/file-singlify/references/safety-rules.md](skills/file-singlify/references/safety-rules.md).

### `before-git-push`

Run it right before `git push`, opening a PR, or shipping. Acting as a senior release engineer / SRE, it judges **only from the real diff** and walks a fixed checklist: the most fragile line, unverified assumptions and blind spots, old-user data-compatibility risk (cache, DB schema/migration, persisted format, API contract), the failure path most likely to break prod, and whether rollback + feature toggle are ready.

- **Review, not execution.** It outputs a verdict plus reasoning; a human decides whether to push. It never runs `git push` for you.
- **Diff-grounded.** No real diff, no review — it asks for the diff instead of guessing.
- **Ends in PUSH / HOLD.** After a reverse-verification pass (3 pieces of counter-evidence, each scored), it prints `▶︎▶︎PUSH▶︎▶︎` or `▶︎▶︎HOLD▶︎▶︎`; on HOLD it names the first thing to fix. When unsure, it prefers HOLD.

See [skills/before-git-push/SKILL.md](skills/before-git-push/SKILL.md).

### Prefixed Superpowers workflow

The six `superpowers-*` skills form a complementary workflow:

1. `superpowers-using-git-worktrees` creates or reuses an isolated workspace.
2. `superpowers-brainstorming` shapes the design and hands off to implementation planning.
3. `superpowers-test-driven-development` drives implementation from a failing test.
4. `superpowers-systematic-debugging` investigates when observed behavior diverges from expectations.
5. `superpowers-verification-before-completion` checks fresh evidence before any success claim.
6. `superpowers-writing-skills` applies the same testing discipline to skill authoring and validation.

These skills are adapted from [`obra/superpowers`](https://github.com/obra/superpowers). See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for the pinned upstream revision and MIT license.

## Structure

```text
polish/
├── references/strategies.md  # prompt-polish strategy library
├── skills/prompt-polish/
│   └── SKILL.md              # canonical prompt-polish skill contract
├── skills/file-singlify/
│   ├── SKILL.md              # canonical file-singlify skill contract
│   ├── scripts/              # read-only duplicate scanner
│   ├── references/           # matching + safety rules
│   └── agents/               # Codex/OpenAI agent descriptor
├── skills/before-git-push/
│   └── SKILL.md              # canonical before-git-push skill contract
├── skills/superpowers-using-git-worktrees/
│   └── SKILL.md              # isolated-workspace setup workflow
├── skills/superpowers-brainstorming/
│   ├── SKILL.md              # design-before-implementation workflow
│   └── scripts/              # optional visual companion runtime
├── skills/superpowers-systematic-debugging/
│   └── SKILL.md              # root-cause-first debugging workflow
├── skills/superpowers-verification-before-completion/
│   └── SKILL.md              # evidence-before-claims gate
├── skills/superpowers-test-driven-development/
│   └── SKILL.md              # red-green-refactor workflow
├── skills/superpowers-writing-skills/
│   └── SKILL.md              # test-driven skill authoring workflow
├── .claude-plugin/
│   ├── plugin.json           # Claude plugin manifest
│   └── marketplace.json      # self-contained marketplace catalog
├── .codex-plugin/
│   └── plugin.json           # Codex CLI plugin manifest
└── .cursor-plugin/
    └── plugin.json           # Cursor plugin manifest
```

When adding skills, keep each skill name stable under `skills/<skill-name>/`. The repo/plugin package can remain `polish` while skills inside it grow independently.

---

<a name="中文版"></a>

# 中文版

> 个人精选的自制与适配 agent skills 集合。

[English](#polish) | **中文**

`polish` 是一个面向 Claude Code、Codex CLI 和 Cursor CLI 的个人自制与适配 skill/plugin 集合。repo/plugin 包名叫 `polish`；里面每个 skill 的名字保持稳定，避免已有触发方式和安装路径失效。

当前包含：

- `prompt-polish` - 把粗糙问题改写成高质量、可直接粘贴使用的中英双语 LLM 提示词。
- `file-singlify` - 扫描磁盘/目录/挂载路径，找出重复文件和重复目录副本，生成「单副本化」方案（保留一份 canonical copy + duplicate→canonical 映射），默认只读 dry-run 报告。
- `before-git-push` - push 前最后一道风险闸门：以发布工程师视角只依据真实 diff 审查本次改动，给出 PUSH 或 HOLD 建议。
- `superpowers-using-git-worktrees` - 在功能开发或执行计划前创建或复用隔离工作区。
- `superpowers-brainstorming` - 在写代码前把想法收敛为已批准的设计与实施计划。
- `superpowers-test-driven-development` - 用 red-green-refactor 约束功能与 bugfix 实现。
- `superpowers-systematic-debugging` - 先定位根因，再提出修改方案。
- `superpowers-verification-before-completion` - 在声称成功前要求最新验证证据。
- `superpowers-writing-skills` - 用测试驱动的方法创建、维护并验证 agent skills。

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

### `file-singlify`

把它指向某个磁盘、目录或挂载路径。它会找出因多次复制、备份、同步、迁移产生的重复文件和整目录重复副本，并生成「单副本化」方案：每组保留一份 canonical copy，其余映射到它。

- **默认只读、dry-run。** 绝不删除、移动、覆盖、改写、建硬/软链接。任何破坏性操作都是独立的、需用户明确确认的一步。
- **目录优先。** 整个目录被多次复制是最大空间浪费来源，所以先做目录级冗余检测和展示，再对候选文件做 hash。
- **hash 确认。** 文件名/大小/时间只用于筛候选；最终「相同」结论来自内容 hash（`md5`、`sha256` 或 `both`）。

扫描逻辑在 `skills/file-singlify/scripts/scan_file_singlify.py`（支持 markdown/json/csv 输出）。详见 [skills/file-singlify/references/matching-rules.md](skills/file-singlify/references/matching-rules.md) 与 [skills/file-singlify/references/safety-rules.md](skills/file-singlify/references/safety-rules.md)。

### `before-git-push`

在 `git push`、提 PR、上线之前运行。它以资深发布工程师 / SRE 视角，**只依据真实 diff** 走一遍固定清单：最发虚的一行、未验证假设与盲区、老用户数据兼容风险（缓存、数据库 schema/迁移、持久化格式、API 契约）、最可能击穿的失败路径，以及回滚 + feature toggle 是否就绪。

- **只审查、不执行。** 只产出建议与理由，是否 push 由人决定；绝不代替你执行 `git push`。
- **以 diff 为准。** 看不到真实 diff 就要求补充，绝不凭空评审。
- **结论落到 PUSH / HOLD。** 经反向验证（3 条反证并打分）后输出 `▶︎▶︎PUSH▶︎▶︎` 或 `▶︎▶︎HOLD▶︎▶︎`；HOLD 时写明第一件要修的事。没把握时倾向 HOLD。

详见 [skills/before-git-push/SKILL.md](skills/before-git-push/SKILL.md)。

### Prefixed Superpowers 工作流

六个 `superpowers-*` skills 组成一套互补工作流：

1. `superpowers-using-git-worktrees` 创建或复用隔离工作区。
2. `superpowers-brainstorming` 完成设计，并衔接到实施计划。
3. `superpowers-test-driven-development` 从失败测试开始驱动实现。
4. `superpowers-systematic-debugging` 在实际行为偏离预期时调查根因。
5. `superpowers-verification-before-completion` 在任何成功声明前检查最新证据。
6. `superpowers-writing-skills` 把相同的测试纪律用于 skill 编写与验证。

这些 skills 适配自 [`obra/superpowers`](https://github.com/obra/superpowers)。固定的上游版本和 MIT license 见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

## 结构

```text
polish/
├── references/strategies.md  # prompt-polish 策略库
├── skills/prompt-polish/
│   └── SKILL.md              # prompt-polish 的主行为契约
├── skills/file-singlify/
│   ├── SKILL.md              # file-singlify 的主行为契约
│   ├── scripts/              # 只读重复扫描脚本
│   ├── references/           # 匹配 + 安全规则
│   └── agents/               # Codex/OpenAI agent 描述
├── skills/before-git-push/
│   └── SKILL.md              # before-git-push 的主行为契约
├── skills/superpowers-using-git-worktrees/
│   └── SKILL.md              # 隔离工作区设置流程
├── skills/superpowers-brainstorming/
│   ├── SKILL.md              # 先设计后实施工作流
│   └── scripts/              # 可选 visual companion runtime
├── skills/superpowers-systematic-debugging/
│   └── SKILL.md              # 根因优先的调试工作流
├── skills/superpowers-verification-before-completion/
│   └── SKILL.md              # 声称完成前的证据闸门
├── skills/superpowers-test-driven-development/
│   └── SKILL.md              # red-green-refactor 工作流
├── skills/superpowers-writing-skills/
│   └── SKILL.md              # 测试驱动的 skill 编写流程
├── .claude-plugin/
│   ├── plugin.json           # Claude 插件清单
│   └── marketplace.json      # 自带 marketplace 目录
├── .codex-plugin/
│   └── plugin.json           # Codex CLI 插件清单
└── .cursor-plugin/
    └── plugin.json           # Cursor 插件清单
```

以后新增 skills 时，把每个 skill 的稳定入口放在 `skills/<skill-name>/` 下。外层 repo/plugin 包名继续叫 `polish`，里面的 skills 可以独立增长。
