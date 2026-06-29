---
name: file-singlify
description: scan disks, folders, mounted paths, or uploaded file manifests to find redundant duplicate files and duplicate directory copies. use when the user wants file deduplication, directory-first duplicate detection, storage cleanup, canonical-copy selection, duplicate-to-canonical reference mapping, hardlink or symlink plans, dry-run reports, or storage space saving analysis.
metadata:
  language: bilingual
---

# file-singlify（文件单副本化）

## 这个 skill 做什么

扫描某个磁盘 / 目录 / 挂载路径，找出因多次复制、备份、同步、迁移产生的**重复文件**和**重复目录**，生成「单副本化」方案：每组保留一份 canonical copy，其余映射为引用 / 待删除 / 链接建议，估算可节省空间。

**核心原则：默认只读、只做 dry-run。绝不直接删除、移动、覆盖、改写、创建硬/软链接。任何破坏性操作都必须先出报告、再等用户明确确认。** 脚本本身永远只读 —— `--action-mode` 只改报告里 `suggested_action` 的标签，不执行任何动作。

## 何时使用

- 用户要扫某个盘/目录/一批文件夹，找「一模一样的文件」「重复目录」「冗余备份」「多重复制」
- 用户想保留一份原始文件、生成引用映射、删除建议、硬/软链接建议、去重报告、节省空间估算
- 关键词：去重 / 单副本化 / 重复目录折叠 / dedup / canonical copy / storage cleanup

**不适用：** 用户要的是文件内容分析、压缩、或与重复检测无关的整理。

## 默认工作流

1. **路径与权限检查** — 确认当前环境能否访问 `root_path`。**能访问就运行脚本；不能访问则要求用户提供目录清单 / 目录树 / 压缩包 / 可访问挂载路径。绝不虚构扫描结果。**
2. **运行脚本（directory-first）** — 先按目录一致性找冗余，再用 hash 确认文件。整个目录被重复复制是最大空间浪费来源，优先展示目录级结果。
3. **读脚本输出，整理给用户** — 优先讲重复目录组，再讲重复文件组、canonical 映射、节省空间、风险项。对脚本标为 `uncertain` / `manual_review` 的项，**向用户提问澄清**，不要替他决定。
4. **给出 top-4 后续命令** — 脚本会按当前 OS/shell 生成 top-4 推荐命令（安全优先：verify → quarantine → hardlink → delete），见报告第 10 节 / JSON 的 `recommended_commands`。把它们呈现给用户，并按用户**真实的** OS 与 shell 调整语法；脚本默认自动探测，必要时用 `--target-os` / `--target-shell` 覆盖。**只给命令，不执行。** 命令里用的是代表性样本路径，需逐行套用到映射表。
5. **destructive 操作前再确认** — 用户要真正删除 / 换链接时，先复述计划并要求明确确认；脚本不会执行，需用户自行执行或另行授权。

## 何时运行脚本

环境可直接读到 `root_path` 就运行；只拿到清单/树时，按同样的判定逻辑（目录结构一致 → 文件大小一致 → 内容 hash 确认）人工分析并明确说明「未做 hash 确认」。

```bash
python3 scripts/scan_file_singlify.py <root_path> \
  --scan-mode directory-first \      # 或 file-only
  --hash-algorithm md5 \             # md5 | sha256 | both（严格用 both）
  --output-format markdown \         # markdown | json | csv
  --action-mode report-only \        # report-only|link-plan|delete-plan|hardlink-plan|symlink-plan
  --exclude-patterns ".git,node_modules,cache,temp" \
  --include-patterns "*.jpg,*.mp4" \
  --min-file-size 1024 \
  --prefer "/Volumes/Primary" \      # 优先保留此路径作 canonical
  --target-os auto \                 # auto|macos|linux|windows（生成 top-4 命令用）
  --target-shell auto                # auto|bash|zsh|fish|powershell|cmd
```

完整参数与判定细节见脚本 `--help`、[references/matching-rules.md](references/matching-rules.md) 与 [references/safety-rules.md](references/safety-rules.md)。

## 输出格式

脚本产出结构化报告，含：扫描范围、参数、总文件/目录/容量、重复目录组、疑似重复目录、重复文件组（hash 确认）、节省空间估算、canonical 映射表、**top-4 推荐命令（按 OS/shell 生成）**、风险与不确定项、下一步建议。`markdown` 给人看，`json` 给程序消费（含 `recommended_commands`），`csv` 是 duplicate→canonical 映射表。

每个映射行带 `confidence`（confirmed / uncertain）和 `suggested_action`（keep / delete_duplicate / replace_with_hardlink / replace_with_symlink / create_manifest_reference / manual_review）。

## 安全边界

- **默认绝不删除文件、绝不自动建硬/软链接。** 脚本只读。
- 只凭文件名 / 大小 / mtime **不能**判定相同 —— 只作候选筛选；最终结论必须 hash 确认（相同大小 + 相同 hash）。
- 对系统目录、隐藏目录、应用目录、Git 仓库、数据库、照片图库、云同步目录格外谨慎。
- 符号链接不跟随、不递归；遇到目录循环停止递归并报告。
- 权限不足 / 零字节 / 特殊文件 / 已硬链接文件 → 标记并跳过，进入「跳过 / 不确定」分类，不当作确定重复。
- canonical 无法判定时，列候选并要求用户确认，不自行拍板。

## 常见错误

| 错误 | 纠正 |
|---|---|
| 没确认能否访问路径就「假装扫描」 | 先确认；不能访问就要清单，绝不虚构结果 |
| 仅凭文件名/大小/时间就判定重复 | 只作候选；必须 hash 确认 |
| 一上来就对所有文件做 hash | 先目录一致性筛选，再对候选 hash |
| 报告还没出就建议删除/换链接 | 先出报告、等明确确认；脚本不执行破坏性动作 |
| 替用户决定 `uncertain` 项 | 把不确定项作为问题抛回给用户 |
