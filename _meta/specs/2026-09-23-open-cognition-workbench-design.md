# 开放认知工作台 · 设计规格

状态：待评审
日期：2026-09-23
适用版本：`index.json` v0.6（generated 2026-09-23，entries 2650 / skills 149 / total 2799）

## 一、定位

一个**只读、无构建、单文件**的静态工作台，把本库已有的四层能力——登记（index.json）、检索（MCP 查询层）、产出（AGENT.md 模板 A/B/C）、质控（lint + CI + eval）——收敛为一个可分享的操作性界面。

它不是知识库的入口网站，而是**研究所的实验台面**：面向"今天要回答一个问题、产出一次分析、或判断这批条目还能不能信"的人。

当前状态：这四层各自存在但没有共同的操作性表面——index.json 只有程序能读，MCP 只有 agent 能用，eval 只有 `--dry` 一条命令，质量标准散在 `_meta/quality-criteria.md` 里靠人自觉。工作台补的是这一层。

## 二、设计原则：研究所最佳实践 → 本库决策

| # | 最佳实践 | 本库决策 | 拒绝的反模式 |
|---|---|---|---|
| 1 | 登记册优先（registry over memory） | 所有计数、清单、facet 一律来自运行时 fetch 的 `index.json`；UI 内不出现任何手写统计常量 | README 式硬编码数字，一改就腐 |
| 2 | 溯源到原始记录 | 每条结果携带 `path`，一键跳转已发布页面或仓库文件；任何结论旁标注 `generated` 日期 | 无出处的摘要 |
| 3 | 采编 / 查询 / 实验 / 质控分区 | 四个面板，各自独立 URL 与状态（见第三节） | 一个大搜索框包打天下 |
| 4 | 实验可复现 | 面板状态全部进 hash；实验台导出 prompt 时附技能路径 + 条目路径 + 日期三元组 | 一次性聊天输出，无法回溯 |
| 5 | 已知未知显式化 | 覆盖率面板直陈缺口（第六节实测数字），缺口用红，不用形容词 | "内容全面丰富" |
| 6 | 人机同一契约 | 工作台 5 个操作原语与 `mcp/open_cognition_mcp/queries.py` 的 5 个函数一一对应，同名、同参数、同匹配谓词 | UI 私有检索逻辑 |
| 7 | 门禁前置于界面 | 审计台读的就是 CI 跑的同一批命令，可原样复制 | 另造一套"质量标准" |
| 8 | 不破坏收藏 | 工作台无任何写路径；变更只能走 PR 过门禁 | 在 UI 里改条目 |
| 9 | 数据不出机器 | 零第三方脚本、零 CDN、零埋点；本地与 Pages 同构 | 引入分析/字体 CDN |
| 10 | 稠密、键盘优先、低装饰 | 表格 + 单页 + 抽屉；等宽字体优先；不做营销式 hero | landing page 化 |

## 三、四个面板

### 1. 注册台 Registry — "我们有什么"

- **视图**：领域 × 类型交叉表（实测 10 领域 / 7 类型，见 index.json）→ 单元格下钻到条目清单表。
- **facet**：`domain`、`type`、`school`(1400/2650 有值)、`tags`(1897/2650 有值，唯一标签 6770)；`type=list`（清单 99 条）额外启用 `category`(20 值) / `channel`(3 值) / `angle` 三个专有条。
- **原语**：`stats`、`list_skills`。
- **空态**：facet 命中为 0 时显示"该组合无登记条目"，不回落到"试试别的"文案。
- **纪律**：`redirect` 类型 5 条（如 `哲学/学派/古希腊/柏拉图.md`）在表中显式标记为"指向子树"，不计入实质条目读数。

### 2. 检索台 Retrieval — "我们找什么"

- **原语**：`search(query, domain?, type?, limit)`、`cross_links(path)`、`read_entry(path, section?)`。
- **匹配谓词与 `queries.py:71` 严格一致**：在 `id/title/school/tags` 上做大小写不敏感子串匹配。默认返回顺序 = index.json 索引序；若叠加本地加权排序，UI 须显式标注"排序为前端加权，MCP 返回索引序"。
- **跨链面板**：`cross_links` 需在浏览器侧读源 md。Pages 环境无源文件读权限 → 该面板在 Pages 上降级为"需要本地模式或 P3 图投影"，并说明原因（不静默返回空表）。
- **深链**：`#/retrieval?q=异化&domain=哲学`。

### 3. 实验台 Production — "我们用库产出什么"

把 AGENT.md 的三个 prompt 模板做成可执行界面，而不是文档里的一段代码块：

| 模板 | 界面 | 对应原语 |
|---|---|---|
| A 单 Skill 调用 | 选技能 → 填任务 → 出 prompt | `apply_skill` |
| B 双 Skill 并行 | 选两个技能 → 同一任务 → 出对照 prompt | `apply_skill` ×2 + 拼装 |
| C 概念追溯 | 选概念条目 → 出追问链 prompt | `read_entry` + `cross_links` |

- **硬要求**：模板 A 拼装文本与 `queries.apply_skill()` 逐字一致（模板正文以 `queries.py:130-145` 为准，B/C 以 `AGENT.md:161-190` 为准）。这是可测的（见第八节）。
- **导出物**：prompt 全文 + 元信息三元组（技能 path、任务、`generated` 日期），只复制到剪贴板 / 下载为 `.md`，不写仓库。
- **149 个技能的入口**：技能清单表含 `name`(英文 slug) 与 `description` 内嵌触发词，支持按中文名/触发词检索——本库技能名是英文、正文是中文，这层双寻址是必须的。

### 4. 审计台 Audit — "我们知道得可靠吗"

- **门禁读数**（每项显示命令 + 本地实际结果，可复制）：
  - `python3 _meta/scripts/lint.py --json` → errors 必须 0（当前 0；warns 2490）
  - `python3 _meta/scripts/build-index.py --check` → 索引新鲜（当前 exit 0）
  - `python3 _meta/scripts/check-nav-links.py --errors-only` → 机械性断链
  - `python3 eval/run_eval.py --dry` → 用例格式与拼装
- **eval 覆盖矩阵**：149 技能 × 有/无用例，当前 **10/149 = 6.7%**（`eval/cases/` 9 个领域分布不均）。这是工作台最需要说出口的数字。
- **结构健康**：字段填充率（school 52.8%、tags 71.6%）、typed cross-link 密度（**296 个条目 / 1111 条边**，即 11% 条目参与显式互链）。
- **backlog**：W006 frontmatter 过期存量原样呈现，标明它是非阻塞设计内债务，不假装它归零。

### 骨架（spine）

左栏 = 面板 + facet；主区 = 表格/清单；右抽屉 = 溯源（path、所属域、类型、可跳转链接、原文引用位置）；底栏 = `index.json` 版本与 `generated`、当前 hash URL（一键复制）。契约自检指示器在 P4 的 fixture 落地前只显示"未启用"，不做无依据的绿灯。

## 四、数据流与技术选型

```
index.json (唯一登记册, 1.0MB) ──fetch ../index.json──┐
                                                       ├─> 工作台/index.html (vanilla JS, 无构建)
AGENT.md 模板 A/B/C  +  queries.apply_skill()  <─逐字对齐─┘
_meta/quality-criteria.md + eval/ + CI 命令  <──读数────┘
```

- **单文件、无构建步骤、无框架、无 CDN。** 与 `GTM/index.html` 同类（仓库已有先例：根级自包含 HTML 产物）。
- **不预生成派生数据副本**。index.json 1.0MB（实测 `gzip -c index.json | wc -c` = 175851，即 Pages 传输约 172KB）直接 fetch 可接受；派生副本意味着多一份要保鲜的产物，违反原则 1。**唯一例外**：P3 的跨链图投影 `工作台/graph.json`——允许的前提是它由脚本生成且被 CI `--check` 保鲜，即"生成投影"而非"手抄清单"。
- **运行方式**：`python3 -m http.server 8000` → `http://localhost:8000/工作台/`（`file://` 下 fetch 被 CORS 拦截，首屏须给出这句提示而非白屏）。
- **Jekyll 约束**：无 frontmatter 的 `.html` 被按静态文件原样复制，因此**不得使用 Liquid 变量**（如 `{{ site.baseurl }}`）；资源引用一律相对路径 `../index.json`，Pages 子路径 `/open-cognition-database/` 下自然解析。
- **中文目录名**与仓库惯例一致；站点已在服务中文路径页面，URL 编码由浏览器处理，风险可接受。
- **正文渲染**：不在工作台内复刻全站 markdown 渲染（那是 Jekyll 的职责且依赖主题）。溯源抽屉只做"定位 + 跳转"，本地 `http.server` 模式下可选启用原文预览（fetch 原始 `.md` 后前端渲染），Pages 模式隐藏该开关并说明原因。

## 五、非目标

- 不做条目编辑、写入或任何仓库变更。
- 不做 embedding / 语义检索（AGENT.md 已把它列为外部集成选项）。
- 不做 SPA、组件库、路由库、状态管理库。
- 不替代 MCP server、CI 或 `_meta/quality-criteria.md`——只读它们。
- 不做移动端适配（台面设备假设：≥1280px 桌面）。

## 六、覆盖率与缺口（实测，将原样显示于审计台）

| 维度 | 实测 | 说明 |
|---|---|---|
| 登记条目 | 2650 entries + 149 skills = 2799 | index.json |
| `school` 填充 | 1400/2650 = **52.8%** | 学派归属未覆盖近半 |
| `tags` 填充 | 1897/2650 = **71.6%**，唯一标签 6770 | 长尾极碎，需要受控词表 |
| 显式跨链 | **296 条目 / 1111 边** ≈ 11% 参与率 | 与质量标准"至少 1 条跨领域互链"仍有距离 |
| eval 覆盖 | **10/149 = 6.7%** | 结构完整 ≠ 已验证可引导执行 |
| `名言/` | **238 个 md 未入 index.json** | 不在 domains、无 `quote` 类型 → 登记册盲区 |
| lint warns | 2490（含 W006 frontmatter 存量） | 设计内非阻塞 backlog |
| 导航断链 | 203（HEAD 基线 205，本次整理无回归） | 英文子目录遗留，范围外 |
| 门禁 | lint errors **0**、`build-index --check` **exit 0**、CI 三色 | 当前绿 |

`名言/` 盲区是本工作台暴露出来的第一个真问题：它是被 README 声明的辅助层，却不在唯一登记册里。修复属于后续独立议题（要么入册，要么显式声明为不入册），**不在本次范围**。

## 七、界面信息架构

```
┌────────────┬──────────────────────────────────────────┬──────────┐
│ 面板 4 选 1 │  主区：表格 / facet chips / 结果清单      │ 溯源抽屉 │
│ 领域 facet │                                          │ path     │
│ 类型 facet │                                          │ 域·类型  │
│ 搜索 (/)   │                                          │ 跳转源   │
├────────────┴──────────────────────────────────────────┴──────────┤
│ v0.6 · generated 2026-09-23 · 契约自检 ○(P4 前为禁用态) · 当前 URL [复制] │
└──────────────────────────────────────────────────────────────────┘
```

键盘：`/` 聚焦检索、`1..4` 切面板、`j/k` 移动行、`Enter` 开抽屉、`Esc` 关。无鼠标完整可用是研究所工作台的门槛，不是加分项。

## 八、验收标准（全部可机械验证）

1. 本地 `http.server` 下首屏 ≤ 2s 内显示 2799 / 2650 / 149，且三数与 `index.json` 实际内容一致（源码中 grep 不到这三个字面量）。
2. 四面板各有稳定 hash URL；刷新后状态完整恢复；`#/retrieval?q=异化&domain=哲学` 直接粘贴可复现同一视图。
3. 检索台 `q=异化` 的结果集合与 `python3 -c "import sys;sys.path.insert(0,'mcp');from open_cognition_mcp import queries;print(len(queries.search('异化')))"` 一致。
4. 实验台任取 3 技能（含 1 个 `宗教/佛教/技能/` 下的）拼装的 prompt，与 `queries.apply_skill(skill_id, 同一 task)` 输出**逐字相同**。
5. 审计台 4 条门禁命令与本地实跑结果一致，命令可原样复制执行。
6. 六节表格中每个数字均由运行时计算得出（无手写常量），缺口项以警示态显示而非省略。
7. 零第三方运行时依赖：`工作台/index.html` 内不出现任何外部 `src=` / `href=` 指向第三方域。
8. 既有门禁不受影响：`lint.py --json` errors 仍为 0；`build-index.py --check` 仍 exit 0；`mcp/test_queries.py` 11 项全绿。
9. 文档入口齐备：`README.md`、`README.en.md`、`AGENT.md`、`INDEX.md` 各新增 1 处工作台入口与一句话说明。

## 九、实施分期

| 期 | 内容 | 产出 |
|---|---|---|
| P0 | 骨架：单文件 + hash 路由 + 只读 fetch + 底栏读数 + 空/错误态 | `工作台/index.html` |
| P1 | 注册台 + 检索台（facet、清单专有条、深链、`/` 键盘流） | 同上 |
| P2 | 实验台（模板 A/B/C、逐字对齐 `queries.py`、导出三元组） | 同上 |
| P3 | 审计台（门禁读数、eval 覆盖矩阵、覆盖率）+ 跨链图投影与保鲜门禁 | `工作台/graph.json`、`_meta/scripts/build-workbench-graph.py`、CI 步骤 |
| P4 | 契约一致性自检 fixture + 四处文档入口 + Pages 实机验证 | `mcp/fixtures/`、README/AGENT/INDEX |

P0–P2 是"输出一个可用工作台"的最小完整集；P3 起才有新增脚本与 CI 变更。若评审希望更小的切片，P0–P1 可先独立成计划（只读浏览 + 检索），P2 起再谈。

## 十、风险与对策

| 风险 | 对策 |
|---|---|
| 前端检索语义与 MCP 漂移，两个门面各自演化 | 唯一谓词实现 + 源码注释指回 `queries.py` 行号；P4 用 fixture 做自检；评审清单项"改了 queries.py 必须同时看工作台" |
| 1MB JSON 首屏慢 | 已实测 gzip 172KB，Pages 有 CDN 压缩即够；仍加载态占位；确有必要才引入瘦投影（且必须带 `--check`） |
| Pages 下 `cross_links`/原文预览不可用 | 显式降级说明，不返回空表冒充"无关联" |
| 无 frontmatter 的 HTML 无法用 Liquid，baseurl 手写易错 | 一律相对路径；验收 1/2 覆盖 |
| 审计台读数在浏览器里跑不了 Python | 读数来自生成物/手工录入会腐 → 只显示"命令 + 如何运行"，CI 结果如需真实读数则由 P3 投影承载并保鲜 |
| 与 Jekyll 站点观感割裂 | 沿用 cayman 主题的中性配色与排版基调（深灰标题带 + 浅底），具体色值实现时从站点实测取，不自造设计语言 |

## 十一、文件清单

**新增**
- `工作台/index.html` — 单文件工作台（P0–P2）
- `工作台/README.md` — 运行方式、契约说明、非目标
- （P3）`_meta/scripts/build-workbench-graph.py` + `工作台/graph.json`
- （P4）`mcp/fixtures/workbench-parity.json`

**修改**
- `README.md`、`README.en.md`、`AGENT.md`、`INDEX.md` — 入口与一句话说明
- `CONTRIBUTING.md` — 新增"改 queries.py / 模板时同步工作台"评审项
- （P3）`.github/workflows/ci.yml` — 图投影保鲜步骤

不删除任何文件；`GTM/index.html`、`404.html`、`index.json` 位置与语义不变；`_config.yml` 无需变更（`工作台/` 需被站点服务，故**不**加入 exclude）。

## 十二、术语

台面（pane）= 四个面板之一；原语（primitive）= 与 `queries.py` 对应的 5 个操作；溯源抽屉（provenance drawer）= 右栏；投影（projection）= 由脚本生成且被 CI 保鲜的派生数据；登记册（registry）= `index.json`。
