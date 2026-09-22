#!/usr/bin/env node
// 在 INDEX.md / README.md / AGENT.md / TAGS.md 中为中文链接文本添加 (English) 备注。
const fs = require('fs');
const path = require('path');
const ROOT = process.cwd();

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
const chToEn = new Map();
const fileTitle = new Map();

for (const f of files) {
  try {
    const text = fs.readFileSync(f, 'utf8');
    const m = text.match(/^---\r?\n([\s\S]*?)\r?\n---/);
    const fm = {};
    if (m) {
      m[1].split(/\r?\n/).forEach(l => {
        const mm = l.match(/^([A-Za-z_][\w-]*):\s*(.*)$/);
        if (mm) fm[mm[1]] = mm[2].trim().replace(/^["']|["']$/g, '');
      });
    }
    let title = fm.title || fm.name;
    if (!title) {
      const h1 = text.match(/^#\s+(.+)$/m);
      if (h1) title = h1[1].trim();
    }
    if (!title) continue;
    const rel = path.relative(ROOT, f);
    fileTitle.set(rel, title);

    const parts = title.split(/[·•]|\s+\/\s+/).map(s => s.trim()).filter(Boolean);
    if (parts.length < 2) continue;
    let ch = '', en = '';
    for (const p of parts) {
      if (/[\u4e00-\u9fff]/.test(p) && !ch) {
        const segs = p.split(/\s*[\/:：]\s*|\s*\(|\)|\s+(?=[A-Za-z])/).filter(Boolean);
        for (const seg of segs) {
          if (/[\u4e00-\u9fff]/.test(seg)) { ch = seg.match(/[\u4e00-\u9fff]/g).join(''); break; }
        }
        if (!ch) ch = p.match(/[\u4e00-\u9fff]/g).join('');
      } else if (/[A-Za-z]/.test(p) && !en) {
        // 清理: 去掉 (Redirect) (已迁移) 等尾巴
        en = p.replace(/\s*\((?:Redirect|已迁移|deprecated)[^)]*\)\s*$/i, '').trim();
      }
    }
    if (ch && en && en.length > 1) chToEn.set(ch, en);
  } catch (e) {
    console.error('Error reading', f, e.message);
  }
}
console.log('Chinese -> English mappings:', chToEn.size);

function annotate(text) {
  let count = 0;
  // Pass 1: markdown links [label](path.md) - allow bold markers in label
  let updated = text.replace(/\[([^\]]+)\]\(([^)]+\.md)\)/g, (full, label, linkPath) => {
    // 已含英文括号或 · 分隔的跳过
    if (/\(.*[A-Za-z]{3,}.*\)/.test(label)) return full;
    if (/[·•]/.test(label)) return full;
    // 剥掉 ** 标记
    const stripped = label.replace(/\*\*/g, '');
    if (!/[\u4e00-\u9fff]/.test(stripped)) return full;
    if (stripped.length > 20) return full;

    let en = chToEn.get(stripped);
    if (!en) {
      const cleanPath = linkPath.replace(/^\.\//, '');
      const fullTitle = fileTitle.get(cleanPath);
      if (fullTitle) {
        const parts = fullTitle.split(/[·•]|\s+\/\s+/).map(s => s.trim()).filter(Boolean);
        const enPart = parts.find(p => /[A-Za-z]/.test(p) && !/[\u4e00-\u9fff]/.test(p));
        if (enPart) en = enPart.replace(/\s*\((?:Redirect|已迁移|deprecated)[^)]*\)\s*$/i, '').trim();
      }
    }
    if (!en || en.length < 2) return full;
    if (en === stripped) return full;
    count++;
    return `[${label} (${en})](${linkPath})`;
  });

  // Pass 2: 节标题 ## 中文 -> ## 中文 (English) (仅在行尾无英文时)
  updated = updated.replace(/^(#{1,4})\s+([^\n]+)$/gm, (full, hashes, heading) => {
    // 跳过: heading 已含英文字母
    if (/[A-Za-z]/.test(heading)) return full;
    // 跳过: heading 含 ·
    if (/[·•]/.test(heading)) return full;
    if (!/[\u4e00-\u9fff]/.test(heading)) return full;
    if (heading.length > 30) return full;
    const en = chToEn.get(heading);
    if (!en) return full;
    count++;
    return `${hashes} ${heading} (${en})`;
  });

  return { updated, count };
}

const targetFiles = ['INDEX.md', 'README.md', 'AGENT.md', 'TAGS.md', 'README.en.md', 'CONTRIBUTING.md'];
for (const f of targetFiles) {
  const fp = path.resolve(ROOT, f);
  if (fp !== ROOT && !fp.startsWith(ROOT + path.sep)) { console.log(f, 'outside repo, skip'); continue; }
  if (!fs.existsSync(fp)) { console.log(f, 'not found'); continue; }
  const text = fs.readFileSync(fp, 'utf8');
  const { updated, count } = annotate(text);
  if (updated !== text) fs.writeFileSync(fp, updated, 'utf8');
  console.log(`${f}: ${count} links annotated`);
}
