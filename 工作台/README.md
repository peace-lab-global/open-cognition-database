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

    python3 mcp/test_workbench.py           # queries.py 生成契约夹具 → 前端 ocw-core 在 node --test 中重放
    python3 mcp/test_workbench.py --check   # CI workbench-contract job 跑的形态：夹具过期或前端漂移即 exit 1

夹具 `mcp/fixtures/workbench-parity.json` 是提交进仓库的产物：Python 侧是唯一真值，
前端重放同一份字节，两边逐字相等才算过。

## 现状

P0–P4 全部落地：四个面板 + 底栏契约自检读数。底栏读数有三种诚实状态——

- **取不到夹具**：`file://` 与 Pages 下读不到 `mcp/fixtures/`（`_config.yml` 排除了
  `mcp/`），此时只声明环境限制，不亮绿。
- **夹具与登记册同版**：浏览器只验证夹具版本与三项计数和 `index.json` 一致；
  逐字比对由 CI `workbench-contract` job 执行，浏览器不冒充 CI。
- **夹具过期**：提示运行 `python3 mcp/test_workbench.py` 刷新。

## 盲区记录：名言/ 未入登记册

审计台覆盖率与检索台都只看 `index.json`，而 `名言/` 下的主题 md 从未登记——发现过程：
P3 接入 `graph.json` 投影时按目录树对照登记册，`名言/` 一栏恒空。这不是面板漏做，
而是投影如实暴露的登记册盲区：**数据库登记了什么，工作台就显示什么；登记册没有的，
台面不会假装存在。**修复（把名言条目纳入登记册）属内容侧独立议题，不在工作台范围内。
