import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import vm from 'node:vm';

export const REPO_ROOT = new URL('../../', import.meta.url).pathname;

/** 从单文件工作台里抽出与 DOM 无关的 core 并在新 context 中求值。 */
export function loadCore(file = '工作台/index.html') {
  const html = readFileSync(REPO_ROOT + file, 'utf8');
  const m = html.match(/<script id="ocw-core">([\s\S]*?)<\/script>/);
  assert.ok(m, `未找到 <script id="ocw-core"> 于 ${file}`);
  const sandbox = {};
  vm.runInNewContext(m[1], sandbox);
  assert.ok(sandbox.OCW, 'core 未导出 globalThis.OCW');
  return sandbox.OCW;
}

/**
 * vm context 里的对象字面量带的是该 context 的 Object.prototype，而 assert/strict 的
 * deepEqual 会比较原型，跨 realm 直接判不相等。工作台状态都是纯数据，JSON 归一到宿主 realm。
 */
export const plain = (v) => JSON.parse(JSON.stringify(v));

test('工作台/index.html 存在且含两个脚本块', () => {
  const html = readFileSync(REPO_ROOT + '工作台/index.html', 'utf8');
  assert.match(html, /<script id="ocw-core">/);
  assert.match(html, /<script id="ocw-app">/);
  assert.match(html, /^<!DOCTYPE html>/i);
});

test('零第三方资源：无外部 src/href 指向其他域', () => {
  const html = readFileSync(REPO_ROOT + '工作台/index.html', 'utf8');
  const urls = [...html.matchAll(/(?:src|href)="([^"]+)"/g)].map((x) => x[1]);
  for (const u of urls) {
    assert.ok(
      /^(#|\.{1,2}\/|[^:/?#]+\.md$|graph\.json$|javascript:void)/.test(u) || u === '',
      `疑似外部资源: ${u}`
    );
  }
});

test('hash 路由：深链解析 + 规范化写回 + 幂等', () => {
  const OCW = loadCore();
  assert.deepEqual(plain(OCW.parseHash('#/retrieval?q=异化&domain=哲学')), {
    pane: 'retrieval', q: '异化', domain: '哲学',
  });
  assert.deepEqual(plain(OCW.parseHash('#/nope')), { pane: 'registry' });
  assert.deepEqual(plain(OCW.parseHash('')), { pane: 'registry' });
  const canonical = OCW.writeHash({ pane: 'retrieval', domain: '哲学', q: '异化' });
  assert.equal(canonical, '#/retrieval?domain=%E5%93%B2%E5%AD%A6&q=%E5%BC%82%E5%8C%96');
  assert.deepEqual(
    plain(OCW.parseHash(canonical)),
    plain(OCW.parseHash('#/retrieval?q=异化&domain=哲学'))
  );
  assert.equal(OCW.writeHash(OCW.parseHash(canonical)), canonical);
  assert.equal(OCW.writeHash({ pane: 'audit', x: '' }), '#/audit');
});

test('file:// 必须给出服务提示而非白屏', () => {
  const OCW = loadCore();
  assert.equal(OCW.needsServer('file:///tmp/index.html'), true);
  assert.equal(OCW.needsServer('http://localhost:8000/工作台/'), false);
  assert.equal(OCW.needsServer('https://x.github.io/open-cognition-database/工作台/'), false);
});

test('loadIndex 走注入的 fetch，结构不符时报错而非崩', async () => {
  const OCW = loadCore();
  const ok = { ok: true, json: async () => ({ entries: [], skills: [] }) };
  const idx = await OCW.loadIndex(async () => ok, '../index.json');
  assert.deepEqual(idx, { entries: [], skills: [] });
  await assert.rejects(() => OCW.loadIndex(async () => ({ ok: false, status: 404 }), 'x'), /HTTP 404/);
  await assert.rejects(
    () => OCW.loadIndex(async () => ({ ok: true, json: async () => ({ foo: 1 }) }), 'x'),
    /结构不符/
  );
});

test('fmt 千分位（底栏读数用）', () => {
  const OCW = loadCore();
  assert.equal(OCW.fmt(27990), '27,990');
  assert.equal(OCW.fmt(999), '999');
});

/* ---------------------------------- Task 3: 注册台 --------------------------------- */

test('注册台 matrix/facets/select 与登记册一致（真 index.json）', () => {
  const OCW = loadCore();
  const index = JSON.parse(readFileSync(REPO_ROOT + 'index.json', 'utf8'));

  const mx = OCW.matrix(index);
  assert.equal(mx.domains.length, index.stats.domains.length);
  assert.equal(
    mx.domains.reduce((a, d) => mx.types.reduce((b, t) => b + mx.cells[d][t], a), 0),
    index.stats.entries
  );
  // redirect 是子树指针，不计入实质条目读数
  assert.equal(mx.substantive, index.entries.filter((e) => e.type !== 'redirect').length);
  assert.ok(mx.substantive < index.stats.entries);

  const fx = OCW.facets(index);
  assert.deepEqual(plain(fx.type).map((x) => x.value).sort(),
    [...new Set(index.entries.map((e) => e.type))].sort());
  assert.equal(fx.domain.find((x) => x.value === '宗教').count,
    index.entries.filter((e) => e.domain === '宗教').length);
  assert.equal(fx.school.reduce((a, s) => a + s.count, 0),
    index.entries.filter((e) => e.school).length);

  assert.equal(plain(OCW.selectEntries(index, { type: 'list' })).length,
    index.entries.filter((e) => e.type === 'list').length);
  assert.deepEqual(
    plain(OCW.selectEntries(index, { domain: '哲学', type: 'concept' })).map((e) => e.path).slice(0, 3),
    index.entries.filter((e) => e.domain === '哲学' && e.type === 'concept').map((e) => e.path).slice(0, 3)
  );
  assert.equal(plain(OCW.selectEntries(index, { domain: '不存在' })).length, 0);
  assert.equal(OCW.redirectCount(index),
    index.entries.filter((e) => e.type === 'redirect').length);
});

/* --------------------------------- Task 4: 检索台 -------------------------------- */

/** Python 真值：直接调 MCP 的 queries.search()。 */
function pySearch(query, domain, type, limit) {
  const py = [
    'import json,sys;sys.path.insert(0,"mcp")',
    'from open_cognition_mcp import queries',
    'print(json.dumps(queries.search(sys.argv[1],' +
    (domain ? JSON.stringify(domain) : 'None') + ',' + (type ? JSON.stringify(type) : 'None') +
    ',' + (limit || 20) + '), ensure_ascii=False))',
  ].join(';');
  return JSON.parse(execFileSync('python3', ['-c', py, query], { cwd: REPO_ROOT }).toString());
}

test('search 结果与 queries.search() 逐条一致（含大小写与 limit 边界）', () => {
  const OCW = loadCore();
  const index = JSON.parse(readFileSync(REPO_ROOT + 'index.json', 'utf8'));
  for (const q of ['异化', 'ALIENATION', 'wuwei', '场域', 'zzz-不存在']) {
    assert.deepEqual(plain(OCW.search(index, q)), pySearch(q), q);
  }
  assert.deepEqual(plain(OCW.search(index, '概念', '哲学', 'concept', 5)), pySearch('概念', '哲学', 'concept', 5));
  assert.equal(OCW.search(index, '异化', '哲学', null, 3).length, pySearch('异化', '哲学', null, 3).length);
});

/* -------------------------------- Task 5: 跨链 -------------------------------- */

/** Python 真值：queries.cross_links() 自己读磁盘上的源文件。 */
function pyCrossLinks(path) {
  const py = [
    'import json,sys;sys.path.insert(0,"mcp")',
    'from open_cognition_mcp import queries',
    'print(json.dumps(queries.cross_links(sys.argv[1]), ensure_ascii=False))',
  ].join(';');
  return JSON.parse(execFileSync('python3', ['-c', py, path], { cwd: REPO_ROOT }).toString());
}

const MD_SAMPLE = [
  '## 跨学科关联', '',
  '- [异化](../概念/alienation.md) `[借用]` 马克思的劳动异化',
  '- 无类型的普通链接 [x](./y.md) 不算边',
  '- 全角引号式：[缘起](./p.md) 「[同构]」',
].join('\n');

test('crossLinks 与 CROSS_LINK_RE 一致：只认带类型的互链，路径归一到仓库根相对', () => {
  const OCW = loadCore();
  /* 基准目录 = 条目所在目录 哲学/学派/马克思，故 ../概念/ 上跳一层是 哲学/学派/概念/
     （计划原文写成 哲学/概念/，少跳一层；此处以 Path(base/t).resolve() 的 Python 实测为准） */
  assert.deepEqual(plain(OCW.crossLinks(MD_SAMPLE, '哲学/学派/马克思/README.md')), [
    { source: '哲学/学派/马克思/README.md', target: '哲学/学派/概念/alienation.md', relation: '借用', label: '异化' },
    { source: '哲学/学派/马克思/README.md', target: '哲学/学派/马克思/p.md', relation: '同构', label: '缘起' },
  ]);
  assert.deepEqual(plain(OCW.crossLinks('', 'x/README.md')), []);
  assert.deepEqual(plain(OCW.crossLinks(null, 'x/README.md')), []);
  assert.equal(OCW.canReadSources('file:///x'), false);
  assert.equal(OCW.canReadSources('https://p.github.io/r/工作台/'), true);
});

test('crossLinks 对真实条目与 queries.cross_links() 逐条一致（含 ../ 归一）', () => {
  const OCW = loadCore();
  for (const p of [
    '宗教/传统/道教/大师/庄子/概念/庄周梦蝶.md',
    '认知系统/学派/分布式认知/哈钦斯.md',
    '哲学/学派/存在主义/加缪/概念/哲学性自杀.md',
  ]) {
    const want = pyCrossLinks(p);
    assert.ok(want.length, `样例失效：${p} 已无显式跨链`);
    const text = readFileSync(REPO_ROOT + p, 'utf8');
    assert.deepEqual(plain(OCW.crossLinks(text, p)), want, p);
  }
});

test('edgesFrom：只取与当前条目相关的边；无投影时返回空而非崩', () => {
  const OCW = loadCore();
  const graph = { edges: [
    { source: 'a.md', target: 'b.md', relation: '互补' },
    { source: 'c.md', target: 'a.md', relation: '继承' },
    { source: 'c.md', target: 'b.md', relation: '平行' },
  ] };
  assert.equal(OCW.edgesFrom(graph, 'a.md').length, 2);
  assert.deepEqual(plain(OCW.edgesFrom(graph, 'a.md').map((e) => e.relation)), ['互补', '继承']);
  assert.deepEqual(plain(OCW.edgesFrom(graph, 'z.md')), []);
  assert.deepEqual(plain(OCW.edgesFrom(null, 'a.md')), []);
  assert.deepEqual(plain(OCW.edgesFrom({ edges: 'oops' }, 'a.md')), []);
});

/* ---------------- Task 6 · P2 实验台：模板 A/B/C + 导出 ---------------- */

/** queries.apply_skill() 的真值：Python 自己取技能正文并拼装。 */
function pyApply(skillId, task) {
  const py = ['import sys;sys.path.insert(0,"mcp")',
    'from open_cognition_mcp import queries',
    'sys.stdout.write(queries.apply_skill(sys.argv[1], sys.argv[2]))'].join(';');
  return execFileSync('python3', ['-c', py, skillId, task], { cwd: REPO_ROOT }).toString();
}

/** 技能正文真值：与 apply_skill 内部同一次 read_entry() 调用。 */
function pySkillText(skillId) {
  const py = ['import json,sys;sys.path.insert(0,"mcp")',
    'from open_cognition_mcp import queries',
    'print(json.dumps(queries.read_entry(queries.get_skill(sys.argv[1])["path"])))'].join(';');
  return JSON.parse(execFileSync('python3', ['-c', py, skillId], { cwd: REPO_ROOT }).toString());
}

test('applySkill 与 queries.apply_skill() 逐字相同（3 技能，含宗教/佛教/技能/ 下 1 个）', () => {
  const OCW = loadCore();
  const task = '我连续三周在评审会上说不出反驳意见，回家又觉得自己错了。';
  for (const id of ['cbt-cognitive-distortion', 'qichu-zhengxin-deconstruction', 'madhyamaka-four-fallacies']) {
    const mine = OCW.applySkill(pySkillText(id), task);
    const theirs = pyApply(id, task);
    assert.equal(mine, theirs, id + ' prompt 不逐字一致');
    assert.equal(mine.length, theirs.length, id + ' 长度不一致');
    assert.equal(mine.charCodeAt(mine.length - 1), 10, '末尾保留换行');
  }
  /* 模板 A 的权威是 queries.py：引号用「」（AGENT.md 的直引号 + {domain} 只是文档示意），
     且首行无 {domain}。下面这行钉住这个差异，防止有人"照文档改齐"。 */
  assert.ok(OCW.applySkill('S', 'T').includes('「操作流程」'), 'A 模板引号形态已偏离 queries.py');
});

test('findSkill 双寻址：英文 slug 或中文路径片段都能定位（与 queries.get_skill 同规则）', () => {
  const OCW = loadCore();
  const index = JSON.parse(readFileSync(REPO_ROOT + 'index.json', 'utf8'));
  assert.equal(OCW.findSkill(index, 'cbt-cognitive-distortion').domain, '心理学');
  assert.equal(OCW.findSkill(index, '认知扭曲识别').name, 'cbt-cognitive-distortion');
  assert.equal(OCW.findSkill(index, '七处征心').name, 'qichu-zhengxin-deconstruction');
  assert.equal(OCW.findSkill(index, '没有这个技能'), null);
  assert.equal(OCW.findSkill({ skills: null }, 'x'), null);
});

/** AGENT.md 的模板正文（B/C 的唯一权威：MCP 层没有这两个函数，只能对文档）。 */
function agentTemplate(name) {
  const md = readFileSync(REPO_ROOT + 'AGENT.md', 'utf8');
  const m = md.match(new RegExp('### ' + name + '[^\\n]*\\n+```\\n([\\s\\S]*?)\\n```'));
  assert.ok(m, `AGENT.md 未找到 ${name} 的 fenced 模板（模板改了？先同步这里）`);
  return m[1];
}

test('templateB / templateC 与 AGENT.md 的模板正文逐字一致（占位符代入后）', () => {
  const OCW = loadCore();
  const b = OCW.templateB('T1', 'T2', '同一情境');
  const docB = agentTemplate('模板 B')
    .replace('{SKILL-1 全文}', 'T1')
    .replace('{SKILL-2 全文}', 'T2')
    .replace('{情境}', '同一情境');
  assert.equal(b, docB + '\n');
  const c = OCW.templateC('哲学/学派/存在主义/克尔凯郭尔.md');
  assert.equal(c, agentTemplate('模板 C').replace('{概念条目路径}', '哲学/学派/存在主义/克尔凯郭尔.md') + '\n');
});

test('exportTriple 含技能 path、任务、generated 日期与 prompt 全文，且不留 undefined', () => {
  const OCW = loadCore();
  const meta = { kind: 'A', skills: ['宗教/佛教/技能/七处征心/SKILL.md'], task: 'T',
    version: 'v0.6', generated: '2026-09-23', at: '2026-09-23' };
  const s = OCW.exportTriple(meta, 'PROMPT');
  for (const frag of ['宗教/佛教/技能/七处征心/SKILL.md', 'T', '2026-09-23', 'PROMPT']) {
    assert.ok(s.includes(frag), frag);
  }
  assert.ok(!s.includes('undefined'), s);
  assert.ok(s.indexOf('PROMPT') > s.indexOf('---'), '元信息在 prompt 之前');
});

test('danglingSet：投影自述的断链目标可判定；缺字段/缺投影时为空集而非崩', () => {
  const OCW = loadCore();
  const g = { dangling: ['a/x.md', 'b/y.md'] };
  assert.equal(OCW.danglingSet(g).has('a/x.md'), true);
  assert.equal(OCW.danglingSet(g).has('a/z.md'), false);
  assert.equal(OCW.danglingSet({}).size, 0);
  assert.equal(OCW.danglingSet(null).size, 0);
});

/** 投影与 MCP 服务同源的机械证据：真 graph.json 的出边 == queries.cross_links() 逐字段 */
test('graph.json 出边与 queries.cross_links() 逐字段一致（3 个真实条目 + 计数自洽）', () => {
  const graph = JSON.parse(readFileSync(REPO_ROOT + '工作台/graph.json', 'utf8'));
  assert.ok(Array.isArray(graph.edges) && graph.edges.length > 1000, '投影应为全库边表');
  assert.equal(graph.typed_entries, new Set(graph.edges.map((e) => e.source)).size,
    'typed_entries 应等于有出边的条目数');

  const pyCross = (p) => {
    const py = ['import json,sys;sys.path.insert(0,"mcp")',
      'from open_cognition_mcp import queries',
      'sys.stdout.write(json.dumps(queries.cross_links(sys.argv[1]),ensure_ascii=False))'].join(';');
    return JSON.parse(execFileSync('python3', ['-c', py, p], { cwd: REPO_ROOT }).toString());
  };
  /* 目前没有任何 SKILL.md 正文命中 cross_links 的语法，故样本全部落在 entries 上；
     取排序后 source 序列的首/中/尾，跨域抽样而不是写死某个目录名。 */
  const allSources = [...new Set(graph.edges.map((e) => e.source))];
  const sources = [allSources[0], allSources[(allSources.length / 2) | 0], allSources[allSources.length - 1]];
  assert.equal(new Set(sources).size, 3, '样本不足');
  /* 投影按 (source,target,relation) 全局排序，Python 按正文出现顺序返回：
     比的是同一条目出边的多重集，不是顺序——顺序不同不是漂移，字段不同才是。 */
  const bag = (list) => plain(list)
    .map((e) => JSON.stringify([e.target, e.relation, e.label]))
    .sort()
    .join('\n');
  for (const src of sources) {
    assert.equal(bag(graph.edges.filter((e) => e.source === src)), bag(pyCross(src)),
      src + ' 投影出边与 Python 不一致');
  }

  /* 断链清单必须真断：逐条 stat，且与投影里的边目标自洽 */
  for (const t of graph.dangling) {
    assert.equal(existsSync(REPO_ROOT + t), false, t + ' 被误报为断链');
  }
  const edgeTargets = new Set(graph.edges.map((e) => e.target));
  for (const t of graph.dangling) assert.equal(edgeTargets.has(t), true, t + ' 不在任何边上');
});

/* ----------------------- Task 8 · P3 审计台：门禁与覆盖率 ----------------------- */

test('审计台覆盖率读数现算自投影，不出现手写常量', () => {
  const OCW = loadCore();
  const graph = JSON.parse(readFileSync(REPO_ROOT + '工作台/graph.json', 'utf8'));
  const rows = OCW.coverageRows(graph);
  const byDim = Object.fromEntries(rows.map((r) => [r.dim, r]));
  const c = graph.coverage, ev = graph.eval;

  assert.equal(byDim['登记条目'].value, c.entries);
  assert.equal(byDim['技能'].value, c.skills);
  assert.equal(byDim['school 填充'].value, c.school_filled);
  assert.equal(byDim['school 填充'].ratio, (100 * c.school_filled / c.entries).toFixed(1) + '%');
  assert.equal(byDim['tags 填充'].ratio, (100 * c.tags_filled / c.entries).toFixed(1) + '%');
  assert.equal(byDim['显式跨链条目'].value, graph.typed_entries);
  assert.equal(byDim['显式跨链条目'].why.includes(String(graph.edges.length)), true, '边数应来自投影');
  assert.equal(byDim['eval 覆盖'].value, ev.covered);
  assert.equal(byDim['eval 覆盖'].ratio, (100 * ev.covered / ev.skills_total).toFixed(1) + '%');
  assert.ok(rows.every((r) => Number.isFinite(r.value) && r.ratio), '每行都要有读数与占比');

  /* 缺口必须显式判出来，而不是"这一行不写" */
  assert.ok(byDim['eval 覆盖'].gap, 'eval 覆盖 10/149 必须标红');
  assert.ok(byDim['school 填充'].gap);

  /* 换一份投影，读数跟着变——这是对"没有手写常量"的机械证明 */
  const fake = plain(graph);
  fake.typed_entries = 7;
  fake.edges = fake.edges.slice(0, 13);
  fake.coverage = Object.assign({}, fake.coverage, { entries: 100 });
  fake.eval = Object.assign({}, fake.eval, { covered: 1, skills_total: 4 });
  const fakeRows = Object.fromEntries(OCW.coverageRows(fake).map((r) => [r.dim, r]));
  assert.equal(Object.keys(fakeRows).length, rows.length, '维度集合固定，不随数据增减');
  assert.equal(fakeRows['显式跨链条目'].value, 7);
  assert.equal(fakeRows['显式跨链条目'].ratio, '7.0%');
  assert.equal(fakeRows['显式跨链条目'].why.includes('13'), true);
  assert.equal(fakeRows['eval 覆盖'].ratio, '25.0%');
});

test('审计台门禁与 ci.yml 同源：5 条 CI 命令逐条可回查 + 1 条离线校验标明', () => {
  const OCW = loadCore();
  const ciText = readFileSync(REPO_ROOT + '.github/workflows/ci.yml', 'utf8');
  const ciRuns = ciText.split('\n')
    .filter((l) => /^\s*(- )?run:/.test(l))
    .map((l) => l.replace(/^\s*(- )?run:\s*/, '').trim());
  const gates = OCW.gates();

  const inCI = (cmd) => ciRuns.some((line) => line === cmd || line.indexOf(cmd + ' ') === 0);
  assert.equal(gates.filter((g) => g.ci).length, 5, 'CI 实际跑的门禁恰好 5 条');
  for (const g of gates.filter((x) => x.ci)) {
    assert.equal(/^python3 \S+/.test(g.cmd), true, g.name + ' 命令形态异常');
    assert.equal(inCI(g.cmd), true, '审计台里的门禁命令不在 ci.yml 的 run 步骤中：' + g.cmd);
    assert.ok(g.note, g.name + ' 必须写清判定规则');
  }
  assert.ok(gates.map((g) => g.cmd).join('\n').includes('_meta/scripts/build-workbench-graph.py --check'));
  assert.ok(gates.map((g) => g.cmd).join('\n').includes('mcp/test_workbench.py --check'));

  /* 第 6 条是本地离线校验：CI 不跑它，就必须标 ci:false，否则审计台在冒充门禁 */
  assert.equal(gates.length, 6);
  assert.equal(gates.filter((g) => !g.ci).map((g) => g.cmd).join('\n'), 'python3 eval/run_eval.py --dry');
});
