# AGENT.md — AI Agent 接入指南

> 本文件是 AI Agent（Qoder、Claude Code、Claude Skills、Cursor、自定义 RAG 等）调用本知识库的快速入口。人类读者请从 [README.md](README.md) 进入。

[![Skills](https://img.shields.io/badge/skills-137-blue.svg)](#代表-skill-示例)
[![Concepts](https://img.shields.io/badge/concepts-1112-green.svg)](./INDEX.md)
[![Thinkers](https://img.shields.io/badge/thinkers-1075-orange.svg)](./INDEX.md)

> 以上计数以 `index.json`（`_meta/scripts/build-index.py` 生成）为单一数据源，含思想家专题子条目。

---

## TL;DR — 30 秒接入

1. **找 Skill**：`<domain>/skills/<skill-id>/SKILL.md`
2. **读 Schema**：每个 Skill 文件以 YAML frontmatter 开头，含 `name / description / domain / tags / linked_concepts`
3. **调用**：把 SKILL.md 全文塞给 LLM，让它按 "操作流程" 段执行
4. **跨链**：条目之间用相对路径显式链接，带关联类型标注（`[同源]`、`[互补]`、`[对立]`…）

最小可用示例：

```bash
# 用 Qoder CLI 调用一个 Skill
qodercli skill run 心理学/技能/认知扭曲识别/SKILL.md \
  --input "分析这段独白：……"
```

---

## 仓库结构（Agent 视角）

```
open-cognition/
├── index.json                          # 机器可读索引（v0.3，189 entries）
├── INDEX.md                            # 人类可读双视角索引
├── TAGS.md                             # 统一标签词典 + 关联类型规范
│
├── <domain>/                           # 思想家 + 概念条目 + Skills
│   ├── 哲学/    (42 thinkers / 8 concepts / 19 skills)
│   ├── 宗教/      (34 thinkers / 127 concepts / 39 skills) ← 含佛教认知专题
│   ├── 社会学/     (18 thinkers / 7 concepts / 15 skills)
│   ├── 心理学/    (42 thinkers / 8 concepts / 16 skills)
│   ├── 伦理政治/ (15 / 11 / 10 skills)
│   ├── 美学/    (23 / 9 / 3 skills)
│   ├── 文学/    (5 / 8 / 5 skills)
│   ├── 艺术/          (3 / 8 / 3 skills)
│   └── 认知系统/ (28 / 27 / 16 skills)
│
├── 宗教/佛教/概念/cognitive-theory/   # 🌟 佛教认知专题
│   ├── <concept>.md                    # 19 概念
│   └── skills/<skill-id>/SKILL.md      # 15 专项 Skill
│
└── _meta/                              # 元数据、模板、报告、可视化
```

---

## 三类条目的 Schema

### Thinker（思想家）

```yaml
---
id: <thinker-slug>
name: <中文名 · English Name>
type: thinker
domain: <philosophy|religion|sociology|psychology|ethics-politics|aesthetics|literature|arts|cognitive-systems>
school: <主要学派>
era: <时代>
tags: [...]
key_works: [...]
---
```

段结构：`一句话定位 → 核心命题 → 思想脉络 → 关键著作 → 重要概念 → 思想坐标 → 当代应用 → 常见误读 → 跨学科关联 → 进阶阅读 → 关联 Skills`

### Concept（概念）

```yaml
---
id: <concept-slug>
title: <中文名 · English>
type: concept
domain: <domain>
school: <相关学派>
era: <时代>
tags: [...]
aliases: [...]
sources: [...]
---
```

段结构：`一句话定义 → 历史脉络 → 核心要义 → 通俗 vs 学术 → 与相关概念关系 → 应用场景 → 常见误读 → 跨学科关联 → 进阶阅读`

### Skill（操作框架）— Agent 主要调用对象

```yaml
---
name: <skill-id>                    # 唯一 ID，同目录名
description: <一句话功能。Triggers on …>  # 触发条件写在 description 里
domain: <domain>
school: <相关学派>
linked_thinker: <相对路径>           # 可选
linked_concepts:                     # 1–N 个相关概念
  - <相对路径>
tags: [...]
---
```

段结构：`一句话功能 → 何时使用 → 何时不使用 → 理论基础 → 操作流程（Step 1..N，每步含提问范式） → 完整示例 → 反例（误用） → 关联条目`

---

## 跨链约定

所有跨条目链接使用相对路径 + 关联类型前缀。关联类型在 [TAGS.md](TAGS.md) 中定义：

| 类型 | 含义 | 示例 |
|---|---|---|
| `[同源]` | 出自同一思想家/原典 | 八识体系 `[同源]` 转识成智 |
| `[互补]` | 不同角度指向同一对象 | 中观 `[互补]` 唯识 |
| `[对立]` | 立场相反 | 实在论 `[对立]` 唯名论 |
| `[发展]` | 后出者推进前出者 | 法称 `[发展]` 陈那 |
| `[批判]` | 对前出者的批评 | 月称 `[批判]` 清辨 |
| `[平行]` | 不同传统中结构相似 | 量论 `[平行]` 证伪主义 |
| `[张力]` | 同中有异，未完全解决 | 自证论 `[张力]` 高阶理论 |
| `[继承]` | 学派内传承 | 窥基 `[继承]` 玄奘 |
| `[借用]` | 跨领域概念移植 | 具身认知 `[借用]` 梅洛-庞蒂 |
| `[下位]` | 子概念 | 末那识 `[下位]` 八识 |

Agent 解析时，把 `[类型]` 作为边的 label 即可建立知识图谱。

---

## 标准 Prompt 模板

### 模板 A：单 Skill 调用

```
你是 {domain} 领域的认知助手。请严格按以下 Skill 的"操作流程"执行任务。

<skill>
{把 SKILL.md 全文贴这里}
</skill>

<task>
{用户的具体情境/问题/材料}
</task>

输出要求：
1. 按 Step 1 → Step N 顺序推进，每步明确写出判断依据
2. 使用 Skill 中的"提问范式"生成问题
3. 在"完整示例"的格式下给出输出
4. 末尾附"反例（误用）"警告
```

### 模板 B：双 Skill 并行分析

```
用两个 Skill 对同一情境做交叉分析：

<skill-1>
{SKILL-1 全文}
</skill-1>

<skill-2>
{SKILL-2 全文}
</skill-2>

<task>{情境}</task>

输出：先独立跑两个 Skill，再写一段"两个视角的交叉洞察"。
```

### 模板 C：概念追溯

```
我正在读 {概念条目路径}。请：
1. 用一句话总结核心命题
2. 列出其 `linked_concepts` 中最重要的 3 个，并各写 1 句关系说明
3. 找出 `跨学科关联` 中最有意思的 1 条，展开比较
4. 推荐 1 个最适合此概念的 Skill 来落地使用
```

---

## 代表 Skill 示例

### 通用类（在各 `<domain>/skills/` 下）

| Skill | 用途 | 路径 |
|---|---|---|
| CBT 认知扭曲识别 | 识别 10 类认知扭曲并重构 | [cbt-cognitive-distortion](./心理学/技能/认知扭曲识别/SKILL.md) |
| 布迪厄场域分析 | 分析权力/资本/惯习结构 | [bourdieu-field-analysis](./社会学/技能/布迪厄场域分析/SKILL.md) |
| 四圣谛诊断 | 用佛教诊断框架看具体困境 | [four-noble-truths-framework](./宗教/技能/四圣谛框架分/SKILL.md) |
| 康德绝对命令检验 | 检验行为准则是否可普遍化 | [categorical-imperative-test](./哲学/技能/绝对命令检验/SKILL.md) |
| STPA 事故分析 | 系统理论事故分析 | [stpa-accident-analysis](./认知系统/技能/STPA事故分析/SKILL.md) |

### 佛教认知专题类（在 `religion/buddhism/skills/` 下）

| Skill | 用途 | 路径 |
|---|---|---|
| 八识认知诊断 | 定位认知卡点在哪一识 | [eight-consciousness-diagnosis](宗教/佛教/技能/从前五识/SKILL.md) |
| 三性诊断 | 剥离叙事，看见缘起事实 | [three-natures-diagnosis](宗教/佛教/技能/以唯识三性/SKILL.md) |
| 种子模式分析 | 追溯认知惯性的熏习来源 | [bija-pattern-analysis](宗教/佛教/技能/后的种子类型/SKILL.md) |
| 量论三量验证 | 评估认知的有效性来源 | [pramana-validation](宗教/佛教/技能/以佛教量论/SKILL.md) |
| 二谛重构 | 在冲突陈述间切换世俗/胜义视角 | [two-truths-reframing](宗教/佛教/技能/以佛教二谛/SKILL.md) |
| 五蕴解构 | 把实体化"我"解构为过程束 | [five-aggregates-deconstruction](宗教/佛教/技能/以五蕴/SKILL.md) |
| 缘起链追溯 | 逆向追溯困境的 12 支生成链 | [dependent-origination-tracing](宗教/佛教/技能/定位关键断点/SKILL.md) |

完整列表见 [佛教认知专题 README (Buddhist Cognitive Theory)](宗教/佛教/概念/cognitive-theory/README.md) 的"认知地图"表。

---

## 集成选项

### 1. Qoder CLI（本地 agent）

```bash
# 列出所有可用 Skill
qodercli skill list --repo .

# 用 Skill 处理输入
qodercli skill run <path-to-SKILL.md> --input "…"

# 在对话中调用
qodercli chat --skills-dir <domain>/skills/
```

### 2. Claude Code / Claude Skills

在 Claude Code 会话中加载 SKILL.md 作为 system 指令：

```
请把这个 SKILL.md 当作你的操作手册：
{粘贴 SKILL.md 全文}

现在按它执行：{用户输入}
```

或配置为 Claude Skills（在 `.claude/settings.json` 中注册）。

### 3. Cursor / IDE agent

把 SKILL.md 文件拖入对话窗口，加上 "请按此文件执行：{任务}"。

### 4. 自定义 RAG / Embedding 索引

```bash
# 推荐切分粒度：每段（## 二级标题）一个 chunk
# 推荐 embedding 模型：text-embedding-3-large 或 bge-m3（中文）
# 推荐 metadata：path, domain, type, tags

find . -name "*.md" -not -name "README.md" -not -name "INDEX.md" -not -path "./_meta/*" \
  | xargs -I{} your-indexer {} --chunk-by h2
```

每条 chunk 建议附以下 metadata：

```json
{
  "path": "religion/buddhism/concepts/cognitive-theory/量论.md",
  "id": "pramana",
  "title": "量论 · Pramāṇa",
  "type": "concept",
  "domain": "religion",
  "school": "buddhism-pramana",
  "tags": ["量论", "因明", "陈那", "法称", "认识论"],
  "section": "核心要义"
}
```

### 5. MCP Server（规划中）

v0.7 路线图计划提供 MCP server，暴露：

- `list_skills(domain?)` — 列出 Skill
- `read_entry(path)` — 读条目（含解析 frontmatter）
- `apply_skill(skill_id, task)` — 直接调用
- `cross_links(path, type?)` — 查跨链

---

## 质量与限制

- **不传教**：所有条目以学术中立为准则，从认知/哲学/心理学角度提取。
- **常见误读段**：每条目都设此段，提示哪些流行说法偏离原意——Agent 引用时务必复核此段。
- **通俗 vs 学术表**：概念条目都有此表，Agent 在面向大众输出时优先用"通俗"列的措辞。
- **跨学科关联**：标注了关联类型（平行/对立/继承等），Agent 推理时保留这些 label，不要抹平。
- **原典优先**：进阶阅读段总是"原典 → 二手研究 → 中文资源"的顺序，Agent 推荐时也请按此优先级。

---

## 故障排查

| 现象 | 可能原因 | 处理 |
|---|---|---|
| 链接 404 | 相对路径基于仓库根 | 从仓库根解析 |
| Skill 不匹配任务 | description 触发词不命中 | 换更接近的 Skill；或组合多个 |
| 输出太抽象 | 没要求"示例"段 | 在 prompt 中显式要求"按完整示例格式" |
| 跨学科错乱 | Agent 抹平了关联类型 | 在 prompt 中要求保留 `[类型]` label |
| 佛教条目被当成宗教宣传 | 未读取"常见误读"段 | 在 prompt 中要求复核此段 |

---

## 进一步阅读

- [README.md](README.md) — 项目全貌
- [INDEX.md](INDEX.md) — 人类视角索引
- [TAGS.md](TAGS.md) — 标签与关联类型规范
- [_meta/templates/](./_meta/templates/) — 思想家/概念/学派/Skill 模板
- [_meta/quality-criteria.md](./_meta/quality-criteria.md) — 质量标准
- [宗教/佛教/INDEX.md](宗教/佛教/INDEX.md) — 佛教认知专题导航

---

## License

内容 CC BY-SA 4.0。Agent 调用本仓库内容生成的输出，请在适当处标注"基于 open-cognition 仓库"。
