#!/usr/bin/env node
// 应用 /tmp/rename-map.json 中的 git mv 操作。
// 顺序: 1) 所有文件 mv  2) 所有目录 mv (按深度倒序, 深的先动)
const fs = require('fs');
const { execSync } = require('child_process');
const path = require('path');

const ROOT = '/Users/allengaller/Documents/GitHub/peace-lab-global/open-cognition';
const map = require('/tmp/rename-map.json');

function depth(p) { return p.split('/').length; }

const files = map.filter(m => m.new.endsWith('.md'));
const dirs = map.filter(m => !m.new.endsWith('.md'));
dirs.sort((a, b) => depth(b.old) - depth(a.old));

let ok = 0, skip = 0, fail = 0;
const failures = [];

function gitMv(oldPath, newPath) {
  if (!fs.existsSync(oldPath)) {
    skip++;
    return;
  }
  if (fs.existsSync(newPath)) {
    failures.push({ reason: 'target-exists', old: oldPath, new: newPath });
    fail++;
    return;
  }
  try {
    execSync(`git mv -- ${JSON.stringify(oldPath)} ${JSON.stringify(newPath)}`, {
      cwd: ROOT, stdio: ['ignore', 'pipe', 'pipe'],
    });
    ok++;
  } catch (e) {
    failures.push({ reason: 'git-mv-error', old: oldPath, new: newPath, msg: (e.stderr || '').toString().slice(0, 200) });
    fail++;
  }
}

console.log(`Processing ${files.length} file renames...`);
for (const m of files) gitMv(m.old, m.new);

console.log(`Processing ${dirs.length} dir renames...`);
for (const m of dirs) gitMv(m.old, m.new);

console.log(`\nDone: ${ok} ok, ${skip} skipped, ${fail} failed`);
if (failures.length) {
  fs.writeFileSync('/tmp/rename-failures.json', JSON.stringify(failures, null, 2));
  console.log(`Failures written to /tmp/rename-failures.json`);
  console.log('First 5:');
  failures.slice(0, 5).forEach(f => console.log(' ', f.reason, path.relative(ROOT, f.old), '->', path.relative(ROOT, f.new)));
}
