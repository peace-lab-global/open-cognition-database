# 2026-09-05 一致性还债执行报告 · 整体评估后续

> 背景：2026-09-04 整体评估指出"质量门禁存在却持续失守"。本次执行按评估建议完成全部修复。
> 执行时基线：lint 70 errors / index.json 过期（2438 vs 实际 2723）/ Pages 部署失败 / 导航断链 1841。

## 结果总览

| 指标 | 修复前 | 修复后 |
|---|---|---|
| lint errors（阻断 CI） | 70（E001×24 + E003×46） | **0** |
| index.json | 过期（2438 条，7-28 生成） | **2670 条 + 137 skills，id 全库唯一**，`--check` 通过 |
| 导航文件断链 | 1841 | **203**（全部为内容缺口 backlog；机械性错误 0） |
| 同 id 双重条目 | ~66 组 | **0** |
| GitHub Pages | 未启用（部署失败） | **已启用**（workflow 构建型） |
| CI | lint + index 两 job 全红 | 三 job（含新增 nav-links）本地全绿 |

## 执行内容

### 1. E001 YAML 语法修复（24 文件）
frontmatter 中混入 markdown 语法（`*` 项目符号、`|` 项目符号、含裸 `:` / 裸 `"` 的值、丢缩进的 `related:`、丢 `- ` 的列表项）。
新增 `_meta/scripts/fix-yaml-frontmatter.py`（六规则、全量重解析验证、逐文件可复核）。

### 2. E003 断链修复（80 条）
`fix-broken-links.py` 此前扫描已不存在的 `domains/` 目录（死代码），已修活指向中文域目录；跑 SINGLE×78 + FUZZY×2（人工核验为改名而非缺稿）。

### 3. 中英文双重条目清理
- 新增 `_meta/scripts/dedup-legacy-entries.py`：31 对同 id 真重复删除（保中文版），80 条入链改写；142 处桩显示文本 `[weber/README.md]`→`[韦伯/README.md]` 修正。
- 新增 `_meta/scripts/resolve-id-collisions.py`：解决 21 组 E004 同 id 冲突——
  - A（15 组）：删 ASCII 遗留完整条目（已被更大的目录 README 取代，如 weber 102 行 vs 韦伯/README 144 行），修复桩 redirect 指向中文目录（原指向已不存在的英文目录），改写入链；
  - B（4 组）：跨域同 id（locke/hohwy/rogers/eisenstein），桩 id 命名空间化（如 `locke-ethics-politics`）；
  - C（3 组）：陀思妥耶夫斯基/卡夫卡/鲁迅 美学×文学双正本，双双转为目录桩，文学侧 id 命名空间化；
  - D：楞严经两版本（97.7% 相似，带后缀版多"认知架构"节）→ 增量移植到标准命名版；
  - E（2 组）：老子/庄子三元组，哲学侧删遗留，宗教侧 id 命名空间化。
- 5 组换名真重复合并：法律社会学→法社会学、解构批评→解构文论、概念艺术→观念艺术（10 入链改写）、身份与暴力全版顶替简版、schopenhauer.md 删除。
- 余 48 个 ASCII 唯一副本（无同 id 冲突、非阻断）见 [2026-09-04-legacy-ascii-triage.md](2026-09-04-legacy-ascii-triage.md)。

### 4. lint.py 升级
新增 **E004**：同一 frontmatter `id` 被多个条目文件声明即报错（child 页豁免）。防止双重条目再次累积。

### 5. 导航断链（README/INDEX/AGENT）
`fix-nav-links.py` 新增四类策略，**1841 → 203**：
- CONTENT（1584）：按 frontmatter id/school/title/aliases 中的英文 slug 匹配（改名后的条目 id 仍编码旧英文路径，如 `社会学.classical.durkheim`），目录 README 优先；
- SUFFIX（51）：相对层级数错误/中英混合路径，按最长后缀重根；
- BASENAME/CONTEXT（18）：多域同名按"与源文件公共路径前缀 + 顶层枢纽页"消歧。
- `check-nav-links.py` 新增 `--errors-only`：仅"目标存在于库内别处"的机械错误阻断，backlog 非阻断；已接入 CI 第三 job。
- 剩余 203 条 backlog 归档：[2026-09-05-nav-content-backlog.md](2026-09-05-nav-content-backlog.md)。

### 6. index.json 重建与 schema 修复
`build-index.py`：SKILL.md 的 id 从字面 "SKILL" 改为取 `name`/技能目录名；重复子页 id 以全路径命名空间化（`哲学.学派.东方哲学.老子.概念.wuwei` 式），**索引 id 全库唯一**；`skills` 顶层数组从空修复为 137 条（扫描各域 `技能/`）。TECH 已加入两处 `_DOMAIN_DIR_NAMES`。

### 7. 文档同步
README.md（徽章/总览/九域表）、README.en.md（徽章/总览/结构）、AGENT.md（徽章/结构节/index 说明）全部对齐 index.json 实际计数。

### 8. 仓库卫生与基础设施
- `.video_agent/plugin_root`（本地机器路径）移出跟踪；`expand-thinkers.js`（指针桩历史生成器）归档至 `_meta/archive/`；
- `.gitignore` 补 `.mimosa/ .v2c/ .video_agent/ .qoder/ lint-report.json` 等；
- **GitHub Pages 已启用**：https://peace-lab-global.github.io/open-cognition-database/ （下次 push 自动部署）。

## 遗留事项（非阻断）
1. **48 个 ASCII 唯一副本**：见 legacy-ascii-triage，需逐条决定改名或确认被目录 README 取代。
2. **203 条导航 backlog**：目标条目未撰写，属内容建设；清单已归档。
3. **标签词汇混用**（802 纯英 / 351 纯中 / 538 混用）：需按 TAGS.md 定词典后批量归一，属内容治理，未自动化。
4. W006 警告 ~2400 条：未撰写条目链接（backlog），设计上非阻断。
