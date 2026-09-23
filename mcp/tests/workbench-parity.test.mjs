import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import { loadCore, plain, REPO_ROOT } from './workbench-core.test.mjs';

const FIXTURE = REPO_ROOT + 'mcp/fixtures/workbench-parity.json';
const fx = existsSync(FIXTURE) ? JSON.parse(readFileSync(FIXTURE, 'utf8')) : null;
const index = JSON.parse(readFileSync(REPO_ROOT + 'index.json', 'utf8'));
const OCW = loadCore();

test('夹具存在（先运行 python3 mcp/test_workbench.py）', () => {
  assert.ok(fx, 'mcp/fixtures/workbench-parity.json 缺失');
});

test('夹具版本/计数与登记册同版（新鲜度最低线）', { skip: !fx }, () => {
  assert.equal(fx.version, index.version);
  assert.deepEqual(fx.stats, index.stats);
});

test('search 与夹具（= queries.search）逐条一致', { skip: !fx }, () => {
  for (const [q, expected] of Object.entries(fx.search)) {
    assert.deepEqual(plain(OCW.search(index, q)), expected, `query=${q}`);
  }
  assert.deepEqual(plain(OCW.search(index, '概念', '哲学', 'concept', 5)), fx.search_filtered['哲学/concept/5']);
});

test('applySkill 与夹具 prompt 逐字相同', { skip: !fx }, () => {
  for (const a of fx.apply_skill) {
    const skill = OCW.findSkill(index, a.skill_id);
    assert.ok(skill, a.skill_id);
    const text = readFileSync(REPO_ROOT + a.path, 'utf8');
    assert.equal(OCW.applySkill(text, a.task), a.prompt, a.skill_id + ' 与 queries.apply_skill 不一致');
  }
});

test('list_skills 计数与夹具一致', { skip: !fx }, () => {
  const mine = {};
  for (const s of OCW.listSkills(index)) mine[s.domain] = (mine[s.domain] || 0) + 1;
  assert.deepEqual(mine, fx.list_skills);
});

/* queries.list_skills 的方向是"参数在域名里"（dl in domain.lower()），标签为小写精确命中。
   期望值在测试里按同一条 Python 规则独立重算，不依赖数据里碰巧没有重名标签。 */
test('listSkills 的 domain 匹配规则与 Python 同向', () => {
  const likePython = (dl) => index.skills.filter((s) =>
    String(s.domain || '').toLowerCase().includes(dl) ||
    (s.tags || []).map((t) => String(t).toLowerCase()).includes(dl)).length;
  assert.equal(OCW.listSkills(index).length, index.stats.skills);
  assert.equal(OCW.listSkills(index, '宗教').length, likePython('宗教'));
  assert.equal(OCW.listSkills(index, '宗').length, likePython('宗'));
  assert.equal(OCW.listSkills(index, 'zzz').length, 0);
});

test('crossLinks 与夹具（= queries.cross_links）一致', { skip: !fx }, () => {
  for (const sample of fx.cross_links) {
    assert.deepEqual(plain(OCW.crossLinks(sample.md_text, sample.entry_path)), sample.edges);
  }
});

// 契约面机械核对：源码里的契约标记之后必须紧跟 return 导出块，导出名 = 本文件声明的
// 契约清单，且每个导出名确实挂在 OCW 上（防止改名后 return 与实现脱节）。
test('OCW:CONTRACT-FUNCS return 导出与契约清单逐名一致', () => {
  const html = readFileSync(REPO_ROOT + '工作台/index.html', 'utf8');
  const at = html.indexOf('/* OCW:CONTRACT-FUNCS */');
  assert.ok(at >= 0, '契约标记 /* OCW:CONTRACT-FUNCS */ 缺失');
  const m = html.slice(at).match(/return\s*\{([^}]*)\}/);
  assert.ok(m, '标记后未找到 return 导出块');
  const names = m[1].split(',').map((s) => s.trim()).filter(Boolean);
  const required = [
    'PANES', 'PANE_LABELS', 'parseHash', 'writeHash', 'needsServer', 'loadIndex', 'fmt', 'enc', 'dec',
    'search', 'crossLinks', 'resolveEntryPath', 'edgesFrom', 'danglingSet', 'canReadSources',
    'applySkill', 'findSkill', 'templateB', 'templateC', 'exportTriple',
    'matrix', 'facets', 'selectEntries', 'redirectCount', 'LIST_ONLY_FIELDS',
    'pct', 'gates', 'coverageRows', 'evalMatrix', 'listSkills',
  ];
  for (const n of required) assert.ok(names.includes(n), 'return 导出缺 ' + n);
  for (const n of names) assert.ok(n in OCW, 'return 导出 ' + n + ' 不在 OCW 上');
});
