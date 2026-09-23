# 开放认知工作台

只读、无构建、单文件的研究所工作台台面。设计规格见
`_meta/specs/2026-09-23-open-cognition-workbench-design.md`，
实施计划见 `_meta/plans/2026-09-23-open-cognition-workbench.md`。

## 运行

    python3 -m http.server 8000      # 仓库根
    → http://localhost:8000/工作台/

`file://` 直开会被 CORS 拦住取不到 `index.json`，首屏会给出这句提示。
Pages 部署后同一份文件在 `/open-cognition-database/工作台/` 可用，功能差异只有一处：
`file://`/Pages 下读不到源 `.md`，跨链与原文预览改由 `graph.json` 投影提供。

## 四个面板

| 面板 | 回答 | 原语 |
|---|---|---|
| 注册台 | 我们有什么 | `stats` / `list_skills` |
| 检索台 | 我们找什么 | `search` / `cross_links` / `read_entry` |
| 实验台 | 我们用它产出什么 | `apply_skill`（模板 A/B/C） |
| 审计台 | 我们知道得可靠吗 | CI 命令读数 + `graph.json` 覆盖率 |

5 个原语与 `mcp/open_cognition_mcp/queries.py` 一一对应、同名同参同谓词；
一致性由 `python3 mcp/test_workbench.py` 机械校验。

## 非目标

不编辑条目、不做语义检索、不引第三方脚本、不替代 MCP/CI/`_meta/quality-criteria.md`、
不适配移动端（台面假设 ≥1280px）。

## 自检

    node --test mcp/tests/*.test.mjs   # 前端纯函数（Node 22 不吃目录参数，需给文件通配）
    python3 mcp/test_workbench.py      # 前端 ↔ queries.py 契约一致

## 现状

当前提交到位的是 P0 骨架：hash 路由、登记册取数、空/错误态与底栏读数。
四个面板的取数逻辑（`graph.json` 投影、`mcp/test_workbench.py` 契约自检）按计划的
P1–P4 逐级补齐；底栏在契约自检未启用前显式标注 `未启用(P4 前)`，不以缺省冒充完成。
