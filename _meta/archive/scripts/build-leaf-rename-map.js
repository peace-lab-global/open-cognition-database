#!/usr/bin/env node
// 批量读取 frontmatter 的中文名，作为叶子目录的 rename map。
// 输出: JSON 数组 [{oldDir, newDir, oldPath, newPath, file, chineseTitle}]
const fs = require('fs');
const path = require('path');

const ROOT = __dirname;

function parseFrontmatter(text) {
  const m = text.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!m) return {};
  const obj = {};
  m[1].split(/\r?\n/).forEach(line => {
    const m2 = line.match(/^([A-Za-z_][\w-]*):\s*(.*)$/);
    if (m2) obj[m2[1]] = m2[2].trim().replace(/^["']|["']$/g, '');
  });
  return obj;
}

function extractChinese(title) {
  // title like "康德 · Immanuel Kant" -> "康德"
  if (!title) return '';
  const parts = title.split(/[·•|]/).map(s => s.trim()).filter(Boolean);
  for (const p of parts) {
    if (/[\u4e00-\u9fff]/.test(p)) return p;
  }
  return parts[0] || '';
}

function walk(dir) {
  const out = [];
  if (!fs.existsSync(dir)) return out;
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) out.push(p, ...walk(p));
    else if (e.isFile()) out.push(p);
  }
  return out;
}

const map = [];

// 对每个叶子目录（含 thinker.md / concept.md / SKILL.md 同名文件）做映射
function scanDomain(domainPath) {
  // 递归找所有 .md 文件
  const files = walk(domainPath).filter(p => p.endsWith('.md') && !p.includes('README') && !p.includes('INDEX'));
  for (const file of files) {
    const text = fs.readFileSync(file, 'utf8');
    const fm = parseFrontmatter(text);
    if (!fm.name && !fm.title) continue;
    const chinese = extractChinese(fm.title || fm.name);
    if (!chinese) continue;
    const dir = path.dirname(file);
    const base = path.basename(file, '.md');
    // 目录名与 base 同名 → 目录是叶子
    if (path.basename(dir) === base) {
      const parentDir = path.dirname(dir);
      const newDirName = chinese;
      const newDir = path.join(parentDir, newDirName);
      if (newDir !== dir) {
        map.push({ oldDir: dir, newDir, file, chinese });
      }
    }
  }
}

// 扫描所有领域
for (const d of fs.readdirSync(ROOT, { withFileTypes: true })) {
  if (!d.isDirectory()) continue;
  if (d.name.startsWith('.') || d.name === '_meta' || d.name === 'node_modules' || d.name === 'scripts') continue;
  scanDomain(path.join(ROOT, d.name));
}

// 也扫描 religion 下的传统、智慧大师
scanDomain(path.join(ROOT, '宗教', '传统'));
scanDomain(path.join(ROOT, '宗教', '智慧大师'));

// 去重（同一 oldDir 只留一次，优先保留 SKILL.md 的映射）
const seen = new Map();
for (const m of map) {
  if (!seen.has(m.oldDir)) seen.set(m.oldDir, m);
}
const unique = [...seen.values()];

// 输出映射
fs.writeFileSync(path.join(ROOT, '_rename-map.json'), JSON.stringify(unique, null, 2));
console.log(`Mapped ${unique.length} leaf dirs`);
console.log('First 10:');
unique.slice(0, 10).forEach(m => console.log(`  ${m.oldDir}  ->  ${path.basename(m.newDir)}`));
