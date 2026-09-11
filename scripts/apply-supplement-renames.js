#!/usr/bin/env node
// 补充重命名: thinker 子目录内的 concepts/ -> 概念/,
// 以及 thinker 目录里的 reading-list/timeline/works.md -> 阅读/时间线/著作.md
const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');
const ROOT = '/Users/allengaller/Documents/GitHub/peace-lab-global/open-cognition';

const dirRenames = { concepts: '概念' };
const fileRenames = {
  'reading-list.md': '阅读.md',
  'timeline.md': '时间线.md',
  'works.md': '著作.md',
};

function walk(dir) {
  const out = [];
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.name === '.git' || e.name === 'node_modules' || e.name === '_meta' || e.name === 'scripts') continue;
    if (e.isDirectory()) out.push(p, ...walk(p));
    else if (e.isFile() && p.endsWith('.md')) out.push(p);
  }
  return out;
}

const items = walk(ROOT);
let ok = 0, skip = 0, fail = 0;
const log = [];

function gitMv(oldPath, newPath) {
  if (!fs.existsSync(oldPath)) { skip++; return; }
  if (fs.existsSync(newPath)) { fail++; log.push({ reason: 'exists', old: oldPath, new: newPath }); return; }
  try {
    execFileSync('git', ['mv', '--', oldPath, newPath], {
      cwd: ROOT, stdio: ['ignore', 'pipe', 'pipe'],
    });
    ok++;
    log.push({ ok: true, old: path.relative(ROOT, oldPath), new: path.relative(ROOT, newPath) });
  } catch (e) {
    fail++;
    log.push({ reason: 'err', old: oldPath, new: newPath, msg: (e.stderr || '').toString().slice(0, 100) });
  }
}

// Pass 1: files first (avoid path invalidation)
for (const p of items) {
  if (!p.endsWith('.md')) continue;
  const base = path.basename(p);
  const target = fileRenames[base];
  if (!target) continue;
  gitMv(p, path.join(path.dirname(p), target));
}

// Pass 2: directories, depth desc
const allDirs = [];
function walkDirs(dir) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    if (!e.isDirectory() || e.name.startsWith('.')) continue;
    const p = path.join(dir, e.name);
    allDirs.push(p);
    walkDirs(p);
  }
}
walkDirs(ROOT);
allDirs.sort((a, b) => b.split('/').length - a.split('/').length);

for (const p of allDirs) {
  const base = path.basename(p);
  const target = dirRenames[base];
  if (!target) continue;
  gitMv(p, path.join(path.dirname(p), target));
}

console.log(`Done: ${ok} ok, ${skip} skip, ${fail} fail`);
fs.writeFileSync('/tmp/supplement-renames.json', JSON.stringify(log, null, 2));
