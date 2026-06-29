# file-singlify safety rules（安全规则）

**The scanner is strictly read-only.** It never deletes, moves, overwrites,
hardlinks, or symlinks. `--action-mode` only relabels `suggested_action` in the
report. Executing any destructive action is a separate, human-confirmed step.

## Hard rules（硬性规则）

- **默认绝不删除文件，绝不自动创建硬/软链接。** dry-run 是默认且唯一的脚本行为。
- 删除 / 换硬链接 / 换软链接 / 生成引用映射等破坏性操作，**必须先生成报告并等待用户明确确认**才能由用户执行。
- 最终「相同」判定必须基于文件内容 hash，不可仅凭目录相似度合并或删除。

## Sensitive locations（高风险目录，格外谨慎）

系统目录、隐藏目录、应用目录（`.app`）、Git 仓库（`.git`）、数据库目录、
照片图库（Photos Library、`.photoslibrary`）、云同步目录（Dropbox/iCloud/
OneDrive/Google Drive）。默认建议加入 `--exclude-patterns`，并在报告中提醒
用户：对这些位置去重可能破坏应用内部结构或触发重新同步。

## File-level cautions（文件级标记）

权限不足、正在同步 / 占用、零字节、特殊文件（设备/管道/socket）、
符号链接、已硬链接（`st_nlink > 1`）的文件 → 一律标记并归入「跳过 / 不确定」，
不计入「确定重复」。

## Recursion safety（递归安全）

- 符号链接默认**不跟随**（`followlinks=False`），目录符号链接记为跳过。
- 用 `(st_dev, st_ino)` 记录已访问目录；检测到目录循环立即停止递归并在 errors 报告。

## Interaction contract（交互契约）

- 无法访问 `root_path` → 要求用户提供目录清单 / 目录树 / 压缩包 / 可访问挂载路径，**绝不虚构扫描结果**。
- canonical 不确定、或映射置信度为 `uncertain` → 把它当作问题抛回给用户，不替用户决定。
- 用户要真正执行删除/链接替换 → 先复述完整计划、点明风险，取得明确确认后再由用户执行。
