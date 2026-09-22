#!/usr/bin/env node
// v3: 暴力但可靠 — 对每个含中文的目录, 列出其中英文 .md 引用, 尝试匹配到该目录下的中文 .md 文件。
// 匹配策略: 用 frontmatter id 的最后一段; 如果不行, 用文件名相似度 (子串)。
const fs = require('fs');
const path = require('path');
const ROOT = '/Users/allengaller/Documents/GitHub/peace-lab-global/open-cognition';

function walk(dir) {
  const out = [];
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    if (e.name === '.git' || e.name === 'node_modules' || e.name === 'scripts') continue;
    const p = path.join(dir, e.name);
    if (e.isDirectory()) out.push(...walk(p));
    else if (e.isFile() && p.endsWith('.md')) out.push(p);
  }
  return out;
}

const files = walk(ROOT);

// Step 1: 为每个含中文的目录, 建立 {英文 slug 候选 -> 中文文件名}
// 候选来源: 同目录下的中文 .md 文件的 frontmatter id 最后一段 + 标题英文部分的 slug 化
const byDir = {}; // dirRel -> { slug -> 中文.md }

function toSlug(s) {
  return s.toLowerCase().replace(/[^a-z0-9\s-]/g, '').trim().replace(/\s+/g, '-').replace(/-+/g, '-');
}

for (const f of files) {
  const base = path.basename(f, '.md');
  if (!/[\u4e00-\u9fff]/.test(base)) continue;
  const dirRel = path.relative(ROOT, path.dirname(f));
  if (!dirRel || !/[\u4e00-\u9fff]/.test(dirRel)) continue;

  const text = fs.readFileSync(f, 'utf8');
  const m = text.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!m) continue;
  const fm = {};
  m[1].split(/\r?\n/).forEach(l => {
    const mm = l.match(/^([A-Za-z_][\w-]*):\s*(.*)$/);
    if (mm) fm[mm[1]] = mm[2].trim().replace(/^["']|["']$/g, '');
  });

  const slugs = new Set();
  if (fm.id) {
    // id 可能是多段
    fm.id.split('.').forEach(p => { if (p) slugs.add(p); });
    slugs.add(fm.id);
  }
  // 从 title 英文部分 slug 化
  if (fm.title) {
    const parts = fm.title.split(/[·•]/);
    for (const p of parts) {
      if (/[A-Za-z]/.test(p)) {
        const s = toSlug(p);
        if (s) slugs.add(s);
      }
    }
  }

  if (!byDir[dirRel]) byDir[dirRel] = {};
  for (const s of slugs) {
    if (/^[a-z0-9-]{2,}$/.test(s)) {
      byDir[dirRel][s] = base + '.md';
    }
  }
}

// 构建替换表
const replacements = [];
for (const [dir, map] of Object.entries(byDir)) {
  for (const [slug, chFile] of Object.entries(map)) {
    if (slug + '.md' === chFile) continue;
    replacements.push({
      old: dir + '/' + slug + '.md',
      new: dir + '/' + chFile,
    });
    replacements.push({
      old: dir + '/' + slug,
      new: dir + '/' + chFile.replace(/\.md$/, ''),
    });
  }
}
replacements.sort((a, b) => b.old.length - a.old.length);
console.log('Total replacement rules:', replacements.length);

// 目标文件
const targets = [];
function walkT(dir) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    if (e.name === '.git' || e.name === 'node_modules' || e.name === 'scripts') continue;
    const p = path.join(dir, e.name);
    if (e.isDirectory()) walkT(p);
    else if (e.isFile() && (p.endsWith('.md') || p.endsWith('.json'))) targets.push(p);
  }
}
walkT(ROOT);

let modified = 0;
for (const t of targets) {
  const text = fs.readFileSync(t, 'utf8');
  let updated = text;
  for (const r of replacements) {
    if (!updated.includes(r.old)) continue;
    const esc = r.old.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    updated = updated.replace(new RegExp(esc, 'g'), r.new);
  }
  if (updated !== text) {
    fs.writeFileSync(t, updated, 'utf8');
    modified++;
  }
}
console.log('Modified files:', modified);

// 验证
const idx = fs.readFileSync(path.join(ROOT, 'INDEX.md'), 'utf8');
for (const key of ['aesthetics', 'mysticism', 'religion-dimension', 'core-teachings', 'kabbalah']) {
  const m = idx.match(new RegExp('.{0,40}' + key + '.{0,40}', 'g'));
  if (m) console.log('Still has ' + key + ':', m[0]);
}
const matches = idx.match(/\([^\)]*[a-z]{3,}\.md\)/g);
console.log('Remaining English .md links in INDEX.md:', matches ? matches.length : 0);
if (matches) matches.slice(0, 10).forEach(m => console.log('  ' + m));
