import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
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
