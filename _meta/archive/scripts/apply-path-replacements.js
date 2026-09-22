#!/usr/bin/env node
// 用 git diff 的 rename 列表, 在所有 md/json 文件里把旧英文路径替换为新中文路径。
// 策略: 以目录为粒度做替换, 从最深的路径开始替换到最浅, 避免前缀互相干扰。
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const ROOT = '/Users/allengaller/Documents/GitHub/peace-lab-global/open-cognition';

// 解码 git 的 octal UTF-8 转义 (形如 "\344\274\246\...")
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

// 读取 rename 列表
const raw = fs.readFileSync('/tmp/renames.txt', 'utf8').split('\n').filter(Boolean);
const renamePairs = []; // {old, new}
for (const line of raw) {
  const parts = line.split('\t');
  if (parts.length < 3) continue;
  const old = parts[1];
  const neo = decodeOctal(parts[2]);
  renamePairs.push({ old, new: neo });
}
console.log('Rename pairs:', renamePairs.length);

// 抽取目录级映射 (去重, 深的优先)
const dirMap = new Map(); // oldDir -> newDir
const fileMap = new Map(); // oldFile -> newFile (用于精确匹配)
for (const p of renamePairs) {
  const oldDir = path.dirname(p.old);
  const newDir = path.dirname(p.new);
  if (oldDir === '.' && newDir === '.') {
    // 顶层文件
  } else {
    if (!dirMap.has(oldDir) || dirMap.get(oldDir).length < oldDir.length) {
      dirMap.set(oldDir, newDir);
    }
  }
  fileMap.set(p.old, p.new);
}

// 构建替换表: 按 oldDir 长度倒序
const replacements = [];
for (const [oldDir, newDir] of dirMap) {
  if (oldDir === newDir) continue;
  if (oldDir === '.') continue;
  // 忽略 _meta (保持英文)
  if (oldDir.startsWith('_meta') || oldDir === '_meta') continue;
  replacements.push({ old: oldDir, new: newDir });
}
replacements.sort((a, b) => b.old.length - a.old.length);
console.log('Directory replacements:', replacements.length);

// 还要处理顶层领域 (philosophy/ religion/ 等) - 已经在 dirMap 里 (作为所有子的前缀)
// 但顶层本身若出现在 `philosophy/README.md` 里, 它的前缀就是 `philosophy`
// dirMap 的 key 是 `philosophy` 当且仅当有 `philosophy/X` -> `哲学/X` 的记录
// 检查:
const topLevel = ['philosophy','religion','sociology','psychology','ethics-politics','aesthetics','literature','arts','cognitive-systems','research'];
for (const t of topLevel) {
  if (!dirMap.has(t)) {
    const ch = {'philosophy':'哲学','religion':'宗教','sociology':'社会学','psychology':'心理学','ethics-politics':'伦理政治','aesthetics':'美学','literature':'文学','arts':'艺术','cognitive-systems':'认知系统','research':'研究'}[t];
    replacements.push({ old: t, new: ch });
  }
}

// 还要处理文件级映射 (用于 .md 精确路径, 如 `kant.md` -> `康德.md`)
// 但路径里通常带目录, 目录替换后 kant.md 仍在; 需要再替换文件 slug
// 为简化, 我们对每个 replacement 也加一个 basename-level 替换:
//   e.g. "kant.md" -> "康德.md", 但只在正确父目录下
// 这个更复杂, 我们先用目录级替换, 然后用 fileMap 做精确路径替换。

// 收集目标文件: 所有 md + json
function walk(dir) {
  const out = [];
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    if (e.name === '.git' || e.name === 'node_modules' || e.name === 'scripts') continue;
    const p = path.join(dir, e.name);
    if (e.isDirectory()) out.push(...walk(p));
    else if (e.isFile() && (p.endsWith('.md') || p.endsWith('.json'))) out.push(p);
  }
  return out;
}
const targets = walk(ROOT);
console.log('Target files:', targets.length);

// 替换
let modified = 0;
const changes = [];
for (const f of targets) {
  const text = fs.readFileSync(f, 'utf8');
  let updated = text;
  // Pass 1: 目录前缀替换 (深的先)
  for (const r of replacements) {
    // 匹配 oldDir 后接 / 或 .md 或 边界
    // 避免替换 URL 里的 domain (如 "arts.example.com")
    // 模式: 前面是 ( [ 空格 或行首, 后面是 / 或 .md 或 空格 或 ) ] 或行尾
    const re = new RegExp('(^|[\\s\\(\\[]|\\./)' + r.old.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&') + '($|/|\\.|[\\s\\)\\]])', 'g');
    updated = updated.replace(re, (m, pre, post) => {
      // 如果 post 是 . 且后面不是 md, 可能不是路径; 但保守起见都替换
      return pre + r.new + post;
    });
  }
  // Pass 2: 文件级精确替换
  for (const [oldFile, newFile] of fileMap) {
    if (oldFile === newFile) continue;
    // 跳过顶层文档 (AGENT.md 等不应被替换)
    if (oldFile === 'AGENT.md' || oldFile === 'INDEX.md' || oldFile === 'README.md' || oldFile === 'TAGS.md' || oldFile === 'CONTRIBUTING.md') continue;
    // 匹配完整路径或 basename 带扩展名
    const oldBase = path.basename(oldFile);
    const newBase = path.basename(newFile);
    if (oldBase === newBase) continue;
    // 只替换完整 oldFile 路径
    const re = new RegExp('(^|[\\s\\(\\[]|\\./)' + oldFile.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&') + '($|[\\s\\)\\]])', 'g');
    updated = updated.replace(re, `$1${newFile}$2`);
  }
  if (updated !== text) {
    fs.writeFileSync(f, updated, 'utf8');
    modified++;
    changes.push(f);
  }
}
console.log('Modified files:', modified);
fs.writeFileSync('/tmp/replaced-files.json', JSON.stringify(changes, null, 2));
