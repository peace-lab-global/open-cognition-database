#!/usr/bin/env node
// 从 /tmp/renames.txt (git diff 输出) 生成 RENAME-MAP.md 文档。
const fs = require('fs');
const path = require('path');

function decodeOctal(s) {
  if (!s.startsWith('"') || !s.endsWith('"')) return s;
  const inner = s.slice(1, -1);
  const bytes = [];
  let i = 0;
  while (i < inner.length) {
    if (inner[i] === '\\' && /[0-7]{3}/.test(inner.slice(i+1, i+4))) {
      bytes.push(parseInt(inner.slice(i+1, i+4), 8));
      i += 4;
    } else {
      bytes.push(inner.charCodeAt(i));
      i += 1;
    }
  }
  return Buffer.from(bytes).toString('utf8');
}

const raw = fs.readFileSync('/tmp/renames.txt', 'utf8').split('\n').filter(Boolean);
const pairs = [];
for (const line of raw) {
  const parts = line.split('\t');
  if (parts.length < 3) continue;
  pairs.push({ old: parts[1], new: decodeOctal(parts[2]) });
}

// 分类
const groups = {
  '顶层领域': [],
  '二级目录': [],
  '学派子目录': [],
  '思想家目录与 stub': [],
  '概念文件': [],
  '技能目录': [],
  '传统与智慧大师': [],
  '附属文件 (reading-list/timeline/works)': [],
  '佛经文件': [],
  '其他': [],
};

for (const p of pairs) {
  const oldSegs = p.old.split('/');
  const newSegs = p.new.split('/');
  // 顶层领域
  if (oldSegs.length === 1 || (oldSegs.length === 2 && oldSegs[1] === 'README.md')) {
    groups['顶层领域'].push(p);
  }
  // 二级
  else if (oldSegs.length === 2 && ['concepts','schools','skills','traditions','wisdom-masters','buddhism'].includes(oldSegs[1])) {
    groups['二级目录'].push(p);
  }
  // 佛经
  else if (p.old.includes('/sutras/') || p.old.includes('/经典/') && p.old.endsWith('.md')) {
    groups['佛经文件'].push(p);
  }
  // 学派子目录 (philosophy/schools/analytic -> 哲学/学派/分析哲学)
  else if (oldSegs.length === 3 && oldSegs[1] === 'schools') {
    groups['学派子目录'].push(p);
  }
  // thinker stubs (X.md + X/ dir)
  else if (p.old.endsWith('.md') && p.new.endsWith('.md') && path.basename(p.old, '.md') === path.basename(path.dirname(p.new))) {
    // 这不太准确, 用 basename 判断
    groups['思想家目录与 stub'].push(p);
  }
  else if (p.old.endsWith('/concepts/') || p.new.endsWith('/概念/')) {
    groups['二级目录'].push(p);
  }
  else if (p.old.endsWith('/README.md') || p.old.endsWith('/timeline.md') || p.old.endsWith('/works.md') || p.old.endsWith('/reading-list.md')) {
    groups['附属文件 (reading-list/timeline/works)'].push(p);
  }
  else if (p.old.includes('/concepts/') && p.old.endsWith('.md')) {
    groups['概念文件'].push(p);
  }
  else if (p.old.includes('/skills/')) {
    groups['技能目录'].push(p);
  }
  else if (p.old.includes('/traditions/') || p.old.includes('/传统/') || p.old.includes('/智慧大师/')) {
    groups['传统与智慧大师'].push(p);
  }
  else if (p.old.endsWith('.md')) {
    // 根据 new 路径中的 /概念/ 或 /学派/ 进一步判断
    if (newSegs.includes('概念')) groups['概念文件'].push(p);
    else if (newSegs.includes('学派')) groups['思想家目录与 stub'].push(p);
    else groups['其他'].push(p);
  }
  else {
    groups['其他'].push(p);
  }
}

// 生成 MD
let md = `# 重命名映射表 · Rename Map

> 本文件记录从 main 分支到 rename-to-chinese 分支的全部路径变更, 便于回查旧 URL / 旧引用。
> 自动生成自 \`git diff --name-status --diff-filter=R main..HEAD\`, 共 **${pairs.length}** 次重命名。

---

## 命名约定

| 层级 | 规则 | 示例 |
|---|---|---|
| 顶层领域 | 学科中文简称 (2-4 字) | \`philosophy/\` → \`哲学/\` |
| 二级目录 | 概念/学派/技能/传统/大师 等类型名 | \`concepts/\` → \`概念/\` |
| 学派子目录 | 学派中文简称 | \`analytic/\` → \`分析哲学/\` |
| 思想家目录 | frontmatter title 中文部分 | \`kant/\` → \`康德/\` |
| 概念文件 | frontmatter title 中文部分 + \`.md\` | \`dialectics.md\` → \`辩证法.md\` |
| 技能目录 | SKILL.md description 首个中文短语 | \`cbt-cognitive-distortion/\` → \`认知扭曲识别/\` |

## 保留英文 (不改名)

- 根文档: \`AGENT.md\`, \`README.md\`, \`INDEX.md\`, \`TAGS.md\`, \`CONTRIBUTING.md\`
- \`_meta/\` 元数据目录 (工具脚本、审计报告、模板)
- 各条目内的附属文件: \`README.md\`, \`INDEX.md\`, \`SKILL.md\`, \`QUICKSTART.md\`

---

`;

for (const [section, items] of Object.entries(groups)) {
  if (items.length === 0) continue;
  md += `## ${section} (${items.length})\n\n`;
  md += '| 旧路径 | → | 新路径 |\n|---|---|---|\n';
  // 截断显示 (前 30 项 + 折叠)
  const display = items.slice(0, 50);
  for (const p of display) {
    md += `| \`${p.old}\` | → | \`${p.new}\` |\n`;
  }
  if (items.length > 50) {
    md += `\n> *...另有 ${items.length - 50} 项, 见 git diff 完整记录*\n`;
  }
  md += '\n';
}

fs.writeFileSync('/Users/allengaller/Documents/GitHub/peace-lab-global/open-cognition/RENAME-MAP.md', md);
console.log('Generated RENAME-MAP.md');
console.log('Group counts:', Object.fromEntries(Object.entries(groups).map(([k, v]) => [k, v.length])));
