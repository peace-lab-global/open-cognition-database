#!/usr/bin/env node
// 最后一遍补漏: 任意 md 文件, 只要 frontmatter title/name 含中文, 就改名为中文
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const ROOT = '/Users/allengaller/Documents/GitHub/peace-lab-global/open-cognition';

function extractChinese(title) {
  if (!title) return '';
  const parts = title.split(/[·•]/).map(s => s.trim()).filter(Boolean);
  for (const p of parts) {
    if (/[\u4e00-\u9fff]/.test(p)) {
      const segs = p.split(/\s*[\/:：]\s*|\s*\(|\)|\s+(?=[A-Za-z])/).filter(Boolean);
      for (const seg of segs) {
        if (/[\u4e00-\u9fff]/.test(seg)) {
          return seg.match(/[\u4e00-\u9fff]/g).join('');
        }
      }
      const all = p.match(/[\u4e00-\u9fff]/g);
      if (all) return all.join('');
    }
  }
  const all = title.match(/[\u4e00-\u9fff]/g);
  return all ? all.join('') : '';
}

function safe(s) {
  return s.replace(/[\/\\:*?"<>|'`\s\(\)\[\]{}]/g, '');
}

function walk(dir) {
  const out = [];
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    if (e.name.startsWith('.')) continue;
    const p = path.join(dir, e.name);
    if (e.isDirectory()) out.push(...walk(p));
    else if (e.isFile() && p.endsWith('.md')) out.push(p);
  }
  return out;
}

const files = walk(ROOT);
let ok = 0, skip = 0, fail = 0;
const failures = [];

for (const f of files) {
  const base = path.basename(f, '.md');
  if (base === 'README' || base === 'INDEX' || base === 'SKILL' || base === 'QUICKSTART') continue;
  if (base === 'AGENT' || base === 'TAGS' || base === 'CONTRIBUTING' || base === 'README.en') continue;
  if (/[\u4e00-\u9fff]/.test(base)) continue; // 已中文
  if (f.includes('/_meta/')) continue; // _meta 保持英文

  const text = fs.readFileSync(f, 'utf8');
  const m = text.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!m) continue;
  const fm = {};
  m[1].split(/\r?\n/).forEach(l => {
    const mm = l.match(/^([A-Za-z_][\w-]*):\s*(.*)$/);
    if (mm) fm[mm[1]] = mm[2].trim().replace(/^["']|["']$/g, '');
  });
  const title = fm.title || fm.name;
  const ch = safe(extractChinese(title));
  if (!ch) continue;
  const newF = path.join(path.dirname(f), ch + '.md');
  if (fs.existsSync(newF)) {
    // 冲突: 加旧 slug 后缀
    const dis = path.join(path.dirname(f), ch + '-' + base + '.md');
    if (fs.existsSync(dis)) { fail++; failures.push({ f, newF, dis, reason: 'exists' }); continue; }
    try {
      execFileSync('git', ['mv', '--', f, dis], { cwd: ROOT, stdio: ['ignore','pipe','pipe'] });
      ok++;
    } catch (e) { fail++; failures.push({ f, dis, reason: 'err', msg: e.message.slice(0,100) }); }
  } else {
    try {
      execFileSync('git', ['mv', '--', f, newF], { cwd: ROOT, stdio: ['ignore','pipe','pipe'] });
      ok++;
    } catch (e) { fail++; failures.push({ f, newF, reason: 'err', msg: e.message.slice(0,100) }); }
  }
}

console.log(`Done: ${ok} ok, ${skip} skip, ${fail} fail`);
if (failures.length) {
  fs.writeFileSync('/tmp/sweep-failures.json', JSON.stringify(failures, null, 2));
  console.log('First 5:');
  failures.slice(0, 5).forEach(x => console.log(' ', x.reason, path.relative(ROOT, x.f), '->', path.relative(ROOT, x.newF || x.dis)));
}
