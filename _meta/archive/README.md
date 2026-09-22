# 归档说明 · Archive

本目录存放**已完成历史使命**的一次性脚本与迁移工具。保留仅为可追溯性，不再维护。

| 文件 | 用途 | 状态 |
|---|---|---|
| `expand-thinkers.js` | 2026-06 社会学思想家"指针子目录化"一次性生成器（stub + `<name>/` 结构的来源） | 已执行完毕；硬编码本地路径与旧英文目录结构，不可复用 |
| `RENAME-MAP.md` | 2026-07 中英双语文件名批量重命名对照表 | 已应用完毕，仅作历史参照 |
| `scripts/` | 2026-07 重命名管线的一次性工具（`build-rename-map.js`、`apply-leaf-renames.js`、`apply-path-replacements.js`、`apply-file-level-replacements.js`、`apply-supplement-renames.js`、`apply-sweep-rename.js`、`annotate-english.js`、`generate-rename-map-md.js`、`_rename-map.json` 等） | 均已执行完毕；硬编码根目录路径与旧目录结构，不可复用 |

> 现行的链接修复/去重工具在 [`_meta/scripts/`](../scripts/)（`fix-nav-links.py`、`dedup-legacy-entries.py`、`resolve-id-collisions.py` 等）。
