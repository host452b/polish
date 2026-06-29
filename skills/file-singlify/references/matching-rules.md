# file-singlify matching rules（匹配判定规则）

Layered funnel: cheap structural signals filter candidates first; content hash
is the only thing that confirms "identical". Never collapse files on anything
weaker than a hash match.

## Phase order（判定顺序）

1. **Directory structure pre-scan（目录预扫描）** — 不读文件内容。
   为每个目录建 *directory signature*：递归收集后代文件的 `(relpath, size)`，
   外加文件名、扩展名、文件数、子目录结构。
2. **Directory match rate（目录匹配率）** — 对候选目录对计算四个分量：
   - `path_name` — 相对路径/文件名集合的 Jaccard 相似度
   - `extension` — 扩展名多重集相似度
   - `size` — 文件大小多重集相似度
   - `count` — 文件数比值
   - `overall` — 四者平均
   结构一致（structure key = `(relpath, size)` 集合相同）只是**候选**：必须对组内
   每个文件做内容 hash，全部一致才作为 *duplicate directory group* 输出；结构一致但
   内容不一致（或无法全部 hash）的目录会被降级，不计入确定重复目录组。
   `overall ≥ threshold`（默认 0.90）→ 列为 *suspected duplicate directory*。
   match rate 只是候选，不是结论。
3. **File-level candidate grouping（文件级候选分组）** —
   - 大小不同 → 不可能完全重复，直接排除。
   - 大小相同、名称不同 → 进入内容 hash 确认。
   - 名称相同、大小不同 → 标记「同名不同内容风险」，不当重复。
4. **Hash confirmation（哈希确认）** —
   - 默认 `md5`（快速确认）；严格模式 `sha256`；高可靠 `both`。
   - 相同大小 **且** 相同 hash 才标 `confirmed`（确定重复）。
   - 大文件分块读取（1 MiB），不一次性载入内存。
   - 读失败 / 权限不足 → 记入 errors，不当作重复。

## Confidence levels（置信度）

| level | 含义 |
|---|---|
| confirmed | 相同大小 + 相同 hash（`both` 模式下两种 hash 都相同）；目录组要求组内每个文件都 hash 一致 |
| uncertain | canonical 有歧义，或重复项带风险标记（zero-byte/symlink/已硬链接等） |
| suspected (dir) | 目录 match rate ≥ threshold 但未逐文件 hash 确认 |
| skipped | symlink / 零字节 / 特殊文件 / 被 exclude / 小于 min-size |

## Canonical copy selection（canonical 选择，按优先级）

1. 用户 `--prefer` 指定的优先保留路径（substring 命中）。
2. 路径更短、层级更浅。
3. 非临时/cache/backup/copy/old/archive/trash 目录（命中这些词的位置被降权）。
4. mtime 默认**不**作强判断；早/晚偏好由用户指定。
5. 路径更稳定、权限更完整的位置。
6. 仍无法判定 → 标 `uncertain` 并列候选，交用户确认，脚本不拍板。
