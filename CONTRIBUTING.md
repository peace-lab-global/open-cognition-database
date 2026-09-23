# 贡献指南 · CONTRIBUTING

欢迎为 open-cognition 提交内容。本指南规定环境、流程、格式与质量要求。

> 📚 **配套文件**
> - 项目全貌：[README.md](README.md) / [README.en.md](README.en.md)
> - AI Agent 接入：[AGENT.md](AGENT.md)
> - 标签词典：[TAGS.md](TAGS.md)
> - 模板库：[_meta/templates/](./_meta/templates/)
> - 质量标准：[_meta/quality-criteria.md](./_meta/quality-criteria.md)
> - 引用源规范：[_meta/sources.md](./_meta/sources.md)
> - 许可：[LICENSE](LICENSE) (CC BY-SA 4.0)

---

## 一、本地开发环境

```bash
# 克隆
git clone https://github.com/peace-lab-global/open-cognition.git
cd open-cognition

# 安装 git hooks（一次性）
./_meta/scripts/setup-hooks.sh
# 效果：
#   - 每次 commit 自动重建并暂存 index.json
#   - 拒绝提交过期的 index.json

# 安装 Python 依赖（lint + index 构建）
pip install pyyaml
```

### 常用本地命令

| 命令 | 用途 |
|------|------|
| `python3 _meta/scripts/lint.py` | 全库条目质量检查 |
| `python3 _meta/scripts/lint.py path/to/file.md` | 单文件检查 |
| `python3 _meta/scripts/lint.py --json` | CI 友好 JSON 输出 |
| `python3 _meta/scripts/build-index.py` | 重建 index.json |
| `python3 _meta/scripts/build-index.py --check` | 检查 index.json 新鲜度（CI 用） |

---

## 二、贡献类型

1. **新增条目**：思想家、概念、学派、宗教传统
2. **新增 Skill**：将思想框架转化为可复用的 AI 调用模板
3. **完善互链**：补充已有条目之间的跨学科关联
4. **修订错误**：纠正事实性错误、引用错误、翻译歧义
5. **基础设施**：脚本、CI、模板、README 改进

请使用匹配的 GitHub issue 模板（见 [.github/ISSUE_TEMPLATE/](.github/ISSUE_TEMPLATE)）：
- 报 bug → `bug-report.yml`
- 提内容建议 → `content-proposal.yml`

---

## 三、写作流程

1. 选择模板：从 [_meta/templates/](./_meta/templates/) 复制匹配模板
2. 填写必填字段（见下文 frontmatter 规范）
3. 按 [TAGS.md](TAGS.md) 规范打标
4. 至少添加 2 条权威引用（原典或重要二手研究）
5. 如条目涉及其他领域，按 [TAGS.md 关联类型](TAGS.md#关联类型-relation-types) 标注互链
6. 在 [INDEX.md](INDEX.md) 对应位置增加链接（如 INDEX.md 仍手工维护）
7. **本地自检**：
   ```bash
   python3 _meta/scripts/lint.py --strict path/to/your/file.md
   ```
8. 提交 PR（使用 [.github/PULL_REQUEST_TEMPLATE.md](.github/PULL_REQUEST_TEMPLATE.md)）

---

## 四、Frontmatter 规范

### Thinker（思想家）

```yaml
---
id: <slug>
name: <中文名 · English Name>     # 或 title
type: thinker
domain: <philosophy|religion|sociology|psychology|ethics-politics|aesthetics|literature|arts|cognitive-systems>
school: <学派>
era: <时代>
tags: [<标签1>, <标签2>]
key_works: [<著作1>, <著作2>]
---
```

### Concept（概念）

```yaml
---
id: <slug>
title: <中文名 · English>
type: concept
domain: <domain>
school: <相关学派>
era: <时代>
tags: [<标签>]
aliases: [<别名>]
sources: [<权威文献>]
---
```

### Skill

```yaml
---
name: <skill-id>
description: <一句话功能>
domain: <domain>
linked_concepts: [<相对路径>]
tags: [<标签>]
---
```

校验脚本：`python3 _meta/scripts/lint.py path/to/file.md`

---

## 五、文件命名

- **思想家**：`schools/<学派>/<姓氏拼音或英文>.md`
  - 例：`socrates.md` `康德.md` `kongzi.md` `龙树.md`
- **概念**：`concepts/<概念英文小写连字符>.md`
  - 例：`辩证法.md` `cultural-capital.md` `五蕴的认知读法.md`
- **Skill**：`<领域>-frameworks/<skill-id>/SKILL.md`
  - 例：`psychology/技能/cbt-cognitive-distortion/SKILL.md`

---

## 六、引用规范

- **原典**：作者《书名》(出版年)，章节或边码
- **二手文献**：作者《书名》(出版年)，出版社
- **学术论文**：作者，论文标题，期刊名 卷(期), 出版年
- 中译本须同时标注原文标题与译者
- 详见 [_meta/sources.md](./_meta/sources.md)

---

## 七、质量底线

- 拒绝原创理论或个人感悟
- 拒绝政治/宗教传教式表达
- 拒绝引用未经核实的网络材料
- 争议性观点必须呈现至少两方立场
- 每个思想家/概念条目必须含 `## 常见误读` 段
- 每个条目必须含 `## 跨学科关联` 段，且至少 1 条跨域链接
- 详见 [_meta/quality-criteria.md](./_meta/quality-criteria.md)

---

## 八、Skill 撰写要求

详见 [_meta/templates/skill-template.md](./_meta/templates/skill-template.md)。每个 Skill 必须：
- 使用 YAML frontmatter（name、description、triggers）
- 包含明确的"何时使用 / 何时不使用"
- 提供 1 个完整使用示例与 1 个反例
- 链接到对应领域目录下相关的理论条目
- 操作流程分 Step 1..N，每步含"提问范式"

---

## 九、Commit 规范

推荐使用 `<scope>: <description>` 形式：

| scope | 示例 |
|---|---|
| `buddhism` | `buddhism: add koan-mechanics concept + skill` |
| `philosophy` | `philosophy: correct kant's categorical imperative` |
| `religion` | `religion: add 10 Buddhist practice skills` |
| `sociology` | `sociology: fix broken links in giddens` |
| `cse` | `cse: deepen safety-science school` |
| `repo` | `repo: add .gitignore, AGENT.md, reorganize reports/` |
| `infra` | `infra: add lint.py and CI workflow` |
| `docs` | `docs: update README with v0.7 stats` |

**信息性 commit message**：用 body 段解释 why 与 what，避免"update"等空词。

---

## 十、PR 审核标准

由维护者按 [_meta/quality-criteria.md](./_meta/quality-criteria.md) 审核，重点检查：
1. 事实准确性
2. 引用可靠性
3. 标签合规性
4. 互链有效性（含反向链接）
5. 是否符合"拒绝主观评价"原则
6. **lint 通过**（无 E 级错误）
7. **index.json 一致**（hook 会自动修复）
8. **改了 `mcp/open_cognition_mcp/queries.py` 或 AGENT.md 的 Prompt 模板** → 同步 `工作台/index.html` 的 `ocw-core`，并跑 `python3 mcp/test_workbench.py`（CI `workbench-contract` job 会做同样校验）

### 期望的 PR 规模

| 类型 | 建议文件数 |
|---|---|
| 单条目新增 | 1-3 |
| 主题批量新增 | 10-50 |
| 跨链修复 | 不限 |
| 基础设施 | 1-10 |

超过 50 文件的 PR 请先开 issue 讨论拆分策略。

---

## 十一、License

通过提交 PR，你确认：
- 你的贡献按 [CC BY-SA 4.0](LICENSE) 授权
- 你有权授权该内容
- 引用内容符合合理使用原则

---

## 十二、沟通渠道

- **Bug / 缺陷**：开 issue（用 `bug-report` 模板）
- **内容建议**：开 issue（用 `content-proposal` 模板）
- **一般讨论**：开 issue（blank）或在 PR 描述中 @maintainer
- **安全漏洞**：私有邮件（待补 maintainer 邮箱）

感谢你的贡献。🙏
