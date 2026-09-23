# 开放认知工作台 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 `open-cognition-database` 仓库落地一个只读、无构建、单文件的静态工作台（`工作台/index.html`），把登记册 `index.json`、MCP 查询层、AGENT.md 三个 Prompt 模板与 CI/eval 质控门禁收敛为四个面板（注册台 / 检索台 / 实验台 / 审计台）。

**Architecture:** 唯一前端产物 `工作台/index.html` 内含两个脚本块：`<script id="ocw-core">` 是与 DOM 无关的纯函数（与 `mcp/open_cognition_mcp/queries.py` 的 5 个原语一一对应，可被 Node 的 `vm` 提取执行）；`<script id="ocw-app">` 只做取数、hash 路由与渲染。P3 新增 `_meta/scripts/build-workbench-graph.py`，用**同一份** `queries.py` 生成 `工作台/graph.json` 投影（跨链边表 + 覆盖率 + eval 覆盖），并被 CI `--check` 保鲜——从而让 Pages 环境下 `cross_links` 与审计台读数不需要浏览器读源文件。P4 新增 Python→JSON 契约夹具 + Node 断言，机械验证前端与 Python 逐字一致。

**Tech Stack:** 无框架 vanilla ES2019（浏览器）；`node:test` + `node:vm`（前端逻辑测试，Node v22）；Python 3.12+ 标准库 + PyYAML（投影与夹具）；GitHub Actions（现有 `lint` / `index-consistency` / `nav-links` 三 job）。

**Spec:** `_meta/specs/2026-09-23-open-cognition-workbench-design.md`（执行时同时阅读该文件；本计划所有数字与验收项从中而来）

## Global Constraints

- **不删除任何仓库文件。** 归档用 `git mv` 移入 `_meta/`，不 `rm`。
- **不 push。** 每个 Task 结束时只在本地 `main` 上 `git commit`；`git push` 未经用户明确要求不得执行。
- **不写仓库的工作台**：工作台无任何写路径（导出仅剪贴板 / 浏览器下载）。
- **零第三方运行时依赖**：`工作台/index.html` 内不得出现指向第三方域的 `src=` / `href=`；不引 CDN、字体、埋点。
- **禁止手写统计常量**：`2799`、`2650`、`149`、`1111`、`296`、`52.8` 等一律运行时计算；验收方式是对 `工作台/` 目录做字面量 grep（见 Task 9 Step 5）。
- **既有门禁必须保持绿**：`python3 _meta/scripts/lint.py --json` 的 `errors` 仍为 `0`；`python3 _meta/scripts/build-index.py --check` 仍 exit `0`；`python3 mcp/test_queries.py` 11 项全绿；`python3 _meta/scripts/check-nav-links.py --errors-only` 仍 exit `0`。
- **模板正文权威来源**：模板 A 以 `mcp/open_cognition_mcp/queries.py:116-125` 为准（**不是** AGENT.md 的 `{domain}` 变体）；模板 B / C 以 `AGENT.md:161-187` 为准。
- **`_config.yml` 不新增 exclude**：`工作台/` 需被 Pages 服务；无 frontmatter 的 `.html` 被原样复制，因此**不得使用 Liquid 变量**，资源一律相对路径（`../index.json`、`graph.json`）。
- 新增测试与夹具放在已排除的 `mcp/` 下；`eval/results/` 不存在也不创建。

---

### Task 0: 修复 index 自动重建链路（前置缺陷，工作台审计台要如实宣读这条门禁）

`_meta/scripts/setup-hooks.sh:10` 把仓库根算成 `_meta`，`_meta/scripts/hooks/pre-commit:19` 仍指向已被归档的 `scripts/build-index.py`，且 `if [ ! -x "$BUILD_SCRIPT" ]` 对权限 `644` 的脚本恒真 → 钩子静默 `exit 0`；`:27` 的 `^(domains/|skills/)` 匹配本仓从未存在的布局 → 索引保鲜钩子实际已死。CI 仍在跑 `--check`，但本地写索引靠人。

**Files:**
- Modify: `_meta/scripts/setup-hooks.sh:10-12`
- Modify: `_meta/scripts/hooks/pre-commit:18-34`（整段重写）
- Test: 一次性 scratch worktree（不落盘测试文件，命令写入计划）

- [x] **Step 1: 写出失败证据（功能测试，不改仓库状态）**

```bash
cd /Users/allengaller/Documents/GitHub/peace-lab-global/open-cognition-database
# (a) 路径断言：当前仍是死链
grep -n 'REPO_ROOT=\|HOOK_SRC=' _meta/scripts/setup-hooks.sh
grep -n 'BUILD_SCRIPT=\|TOUCHED=' _meta/scripts/hooks/pre-commit
# (b) 功能断言：在干净 worktree 里改一个条目，钩子应重建 index.json —— 现状不会
git worktree add /tmp/ocd-hook HEAD >/dev/null
cd /tmp/ocd-hook
mkdir -p .git/hooks 2>/dev/null; cp _meta/scripts/hooks/pre-commit .git/hooks/pre-commit; chmod +x .git/hooks/pre-commit
printf '\n<!-- hook probe -->\n' >> 哲学/概念/wuwei.md
git add -A && git commit --no-verify -q -m probe >/dev/null 2>&1; git reset -q --soft HEAD~1 2>/dev/null
sh .git/hooks/pre-commit; echo "hook exit=$?"
git diff --cached --name-only | grep -c index.json   # 期望 1，现状 0
cd - >/dev/null && git worktree remove --force /tmp/ocd-hook
```

Expected: FAIL —— `hook exit=0` 且 `grep -c` 输出 `0`（钩子什么都没做）；grep 显示 `REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"`、`BUILD_SCRIPT="$REPO_ROOT/scripts/build-index.py"`。

- [x] **Step 2: 修 `setup-hooks.sh` 根路径与源目录**

把 `:10-12` 三行替换为：

```sh
# 本脚本位于 _meta/scripts/，仓库根需上溯两级
REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
HOOK_SRC="$REPO_ROOT/_meta/scripts/hooks"
HOOK_DST="$REPO_ROOT/.git/hooks"
```

同时把末尾提示行改为不再鼓励绕过门禁：

```sh
echo "Hooks installed. 紧急情况下可用 git commit --no-verify 跳过（会留下 index.json 过期风险）。"
```

- [x] **Step 3: 重写 `hooks/pre-commit`（真实路径 + 真实顶层目录 + 不依赖可执行位）**

整文件替换为：

```sh
#!/bin/sh
#
# pre-commit hook for open-cognition
#
# 任务：任一登记域或 build-index.py 被改动时重建 index.json 并自动入暂存区，
#       再校验暂存内容等于一次全新构建（等价于 CI 的 index-consistency job）。
#
# 安装（每台机器一次）：
#   sh _meta/scripts/setup-hooks.sh
#   或手动：cp _meta/scripts/hooks/pre-commit .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
#
# 跳过（仅限紧急）：git commit --no-verify

set -e

REPO_ROOT="$(git rev-parse --show-toplevel)"
BUILD_SCRIPT="$REPO_ROOT/_meta/scripts/build-index.py"

if [ ! -f "$BUILD_SCRIPT" ]; then
    echo "[pre-commit] 未找到 $BUILD_SCRIPT，跳过索引校验" >&2
    exit 0
fi

# 顶层登记目录 = build-index.py 的 _DOMAIN_DIR_NAMES + 技能/清单实际生长的目录
TOUCHED=$(git diff --cached --name-only | grep -E \
  '^(哲学|宗教|伦理政治|心理学|社会学|美学|文学|艺术|认知系统|清单|研究|TECH)/|^_meta/scripts/build-index\.py$' || true)

if [ -z "$TOUCHED" ]; then
    exit 0
fi

python3 "$BUILD_SCRIPT" > /dev/null

if ! git diff --quiet -- index.json 2>/dev/null; then
    git add index.json
    echo "[pre-commit] 已重建并入暂存 index.json"
fi

if ! python3 "$BUILD_SCRIPT" --check > /dev/null 2>&1; then
    echo "[pre-commit] ERROR: index.json 与源文件不一致。请运行 'python3 _meta/scripts/build-index.py' 后重试。" >&2
    exit 1
fi

exit 0
```

- [x] **Step 4: 安装并跑功能测试，确认通过**

```bash
cd /Users/allengaller/Documents/GitHub/peace-lab-global/open-cognition-database
sh _meta/scripts/setup-hooks.sh          # 期望输出 "✓ installed pre-commit"
git worktree add /tmp/ocd-hook HEAD >/dev/null
cd /tmp/ocd-hook
mkdir -p .git/hooks && cp _meta/scripts/hooks/pre-commit .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
printf '\n<!-- hook probe -->\n' >> 哲学/概念/wuwei.md
git add 哲学/概念/wuwei.md
sh .git/hooks/pre-commit; echo "hook exit=$?"
git diff --cached --name-only | grep -c index.json
python3 _meta/scripts/build-index.py --check
cd - >/dev/null && git worktree remove --force /tmp/ocd-hook
git status --porcelain    # 主工作区必须仍是干净的（只多一个 spec 未跟踪项）
```

Expected: PASS —— 打印 `[pre-commit] 已重建并入暂存 index.json`、`hook exit=0`、`grep -c` 输出 `1`、`--check` 在 worktree 内 exit `0`。

- [x] **Step 5: 提交**

```bash
git add _meta/scripts/setup-hooks.sh _meta/scripts/hooks/pre-commit
git commit -m "$(cat <<'EOF'
fix(scripts): 恢复 index.json 自动重建钩子链路

setup-hooks.sh 把仓库根算成 _meta、pre-commit 指向已归档的 scripts/build-index.py
并对 644 权限脚本用 -x 判断，导致钩子长期静默 exit 0；触碰目录正则仍是
domains/|skills/ 这类从未存在的布局。改为真实路径 + python3 调用 + 实际顶层登记目录。
EOF
)"
```

---

### Task 1: 修正 `mcp/` 与 `eval/` 文档的过期计数

`mcp/README.md:3` 写 "137 个 Skill 与 2670 个条目"、`eval/README.md:3,45` 写 137；index.json 实测 skills **149**、total **2799**。审计台要如实宣读门禁，文档不能先腐。

**Files:**
- Modify: `mcp/README.md:3`
- Modify: `eval/README.md:3`
- Modify: `eval/README.md:45`

- [x] **Step 1: 失败断言（现状 grep 命中）**

```bash
cd /Users/allengaller/Documents/GitHub/peace-lab-global/open-cognition-database
grep -n "137 个\|2670" mcp/README.md eval/README.md
python3 - <<'EOF'
import json
d = json.load(open("index.json"))
assert d["stats"]["skills"] == 149, d["stats"]
assert d["stats"]["total"] == 2799, d["stats"]
print("index.json:", d["stats"])
EOF
```

Expected: FAIL —— 三处 grep 命中过期数字（149/2799 由 index.json 断言给出，不写进源码）。

- [x] **Step 2: 三处文案改为与登记册一致**

`mcp/README.md:3`：

```markdown
把本知识库的 149 个 Skill 与 2650 个条目暴露为 **MCP 工具**，任何支持 Model Context Protocol 的客户端（Claude Code / Claude Desktop / Cursor 等）都可以直接调用。
```

`eval/README.md:3`：

```markdown
> 目标：把"149 个 Skill 结构完整"升级为"**经过验证可正确引导 LLM 执行**"。
```

`eval/README.md:45`：

```markdown
- [ ] 全量 149 个
```

- [x] **Step 3: 通过断言**

```bash
grep -rn "137 个\|2670" mcp/ eval/ --include='*.md' ; echo "grep exit=$?"
```

Expected: PASS —— 无输出，`grep exit=1`。

- [x] **Step 4: 提交**

```bash
git add mcp/README.md eval/README.md
git commit -m "docs(mcp,eval): 计数与 index.json 对齐（149 技能 / 2650 条目 / 2799 总计）"
```

---

### Task 2: P0 骨架 —— 单文件 + core/app 双脚本块 + hash 路由 + 只读取数 + 空/错误态

产出 `工作台/index.html`（可打开、能报错、底栏有登记册读数）与 Node 提取式测试 harness。**契约**：`OCW` 对象是后续所有 Task 唯一可测面。

**Files:**
- Create: `工作台/index.html`
- Create: `mcp/tests/workbench-core.test.mjs`
- Create: `工作台/README.md`（Step 6）

**Interfaces:**
- Consumes: `../index.json`（`{version, generated, stats, entries[], skills[]}`）
- Produces: `OCW.PANES: string[]`、`OCW.PANE_LABELS: Record<string,string>`、`OCW.parseHash(hash) -> state`、`OCW.writeHash(state) -> string`、`OCW.needsServer(loc) -> boolean`、`OCW.loadIndex(fetchImpl?, url?) -> Promise<index>`、`OCW.fmt(n) -> string`、`window.__OCW_TEST_HOOK__`（仅 `globalThis.location == null` 时定义，测试专用，不参与运行路径）；`App`（app 块内的渲染状态持有者）。

- [x] **Step 1: 写失败测试**

创建 `mcp/tests/workbench-core.test.mjs`：

```js
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
  assert.deepEqual(OCW.parseHash('#/retrieval?q=异化&domain=哲学'), {
    pane: 'retrieval', q: '异化', domain: '哲学',
  });
  assert.deepEqual(OCW.parseHash('#/nope'), { pane: 'registry' });
  assert.deepEqual(OCW.parseHash(''), { pane: 'registry' });
  const canonical = OCW.writeHash({ pane: 'retrieval', domain: '哲学', q: '异化' });
  assert.equal(canonical, '#/retrieval?domain=%E5%93%B2%E5%AD%A6&q=%E5%BC%82%E5%8C%96');
  assert.deepEqual(OCW.parseHash(OCW.parseHash('#/retrieval?q=异化&domain=哲学') && canonical), OCW.parseHash(canonical));
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
```

- [x] **Step 2: 跑测试确认失败**

Run: `cd /Users/allengaller/Documents/GitHub/peace-lab-global/open-cognition-database && node --test mcp/tests/*.test.mjs`
Expected: FAIL —— `ENOENT, no such file or directory, open '.../工作台/index.html'`（7 项全红）

- [x] **Step 3: 写 `工作台/index.html`（P0 完整骨架）**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=1280">
<title>开放认知工作台 · Open Cognition Workbench</title>
<style>
:root{
  --ink:#1f2328; --muted:#59636e; --line:#d1d9e0; --bg:#f6f8fa; --panel:#fff;
  --ok:#1a7f37; --warn:#9a6700; --err:#cf222e; --accent:#0969da;
  --mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
}
*{box-sizing:border-box}
html,body{margin:0;height:100%}
body{
  display:grid; height:100vh; overflow:hidden;
  grid-template-columns:212px minmax(0,1fr) 344px;
  grid-template-rows:46px minmax(0,1fr) 28px;
  grid-template-areas:"brand brand drawer" "nav main drawer" "bar bar bar";
  font:13.5px/1.65 var(--mono); color:var(--ink); background:var(--bg);
}
body[data-drawer="closed"]{grid-template-columns:212px minmax(0,1fr) 0}
body[data-drawer="closed"] #drawer{display:none}
#brand{grid-area:brand;display:flex;align-items:center;gap:12px;padding:0 14px;
  background:#24292f;color:#fff;border-bottom:1px solid #1c2128}
#brand b{font-weight:600;letter-spacing:.02em}
#brand .dim{color:#afb8c1;font-size:11.5px}
nav{grid-area:nav;border-right:1px solid var(--line);background:var(--panel);padding:10px 0;overflow:auto}
nav button{display:block;width:100%;text-align:left;padding:6px 14px;border:0;background:none;
  font:inherit;color:var(--muted);cursor:pointer}
nav button[aria-current="page"]{background:#ddf4ff;color:var(--accent);font-weight:600}
nav .grp{padding:14px 14px 4px;font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}
main{grid-area:main;overflow:auto;padding:14px 16px}
.pane[hidden]{display:none}
.drawer{grid-area:drawer;border-left:1px solid var(--line);background:var(--panel);overflow:auto;padding:12px 14px}
.bar{grid-area:bar;display:flex;align-items:center;gap:10px;padding:0 12px;border-top:1px solid var(--line);
  background:var(--panel);font-size:11.5px;color:var(--muted)}
.bar .grow{flex:1}
table{border-collapse:collapse;width:100%;font-size:12.5px}
th,td{border-bottom:1px solid var(--line);padding:4px 8px;text-align:left;vertical-align:top}
th{background:var(--bg);position:sticky;top:0;font-weight:600;color:var(--muted)}
tr[cursor] td{background:#ddf4ff}
td.num{text-align:right;font-variant-numeric:tabular-nums}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0}
.chip{border:1px solid var(--line);background:var(--panel);border-radius:20px;padding:1px 10px;font:inherit;font-size:12px;cursor:pointer}
.chip[aria-pressed="true"]{background:var(--accent);border-color:var(--accent);color:#fff}
input[type=search],select,textarea{font:inherit;padding:4px 6px;border:1px solid var(--line);border-radius:4px;background:#fff}
textarea{width:100%;min-height:90px}
button{font:inherit}
.btn{padding:4px 10px;border:1px solid var(--line);border-radius:4px;background:#fff;cursor:pointer}
.btn.primary{background:var(--accent);border-color:var(--accent);color:#fff}
pre{white-space:pre-wrap;word-break:break-word;background:#0d1117;color:#e6edf3;padding:10px;border-radius:6px;font-size:12px;max-height:46vh;overflow:auto}
.empty{padding:28px 4px;color:var(--muted)}
.note{padding:8px 10px;border-left:3px solid var(--accent);background:#ddf4ff66;margin:8px 0;font-size:12.5px}
.note.bad{border-color:var(--err);background:#cf222e1a}
.pill{font-size:11px;padding:0 6px;border-radius:10px;border:1px solid var(--line);color:var(--muted)}
.pill.ok{color:var(--ok);border-color:var(--ok)}
.pill.warn{color:var(--warn);border-color:var(--warn)}
.pill.bad{color:var(--err);border-color:var(--err)}
kbd{border:1px solid var(--line);border-bottom-width:2px;border-radius:3px;padding:0 4px;font-size:11px}
</style>
</head>
<body data-drawer="closed">
<div id="brand"><b>开放认知工作台</b><span class="dim">registry · retrieval · production · audit</span>
  <span class="grow" style="flex:1"></span>
  <span class="dim"><kbd>/</kbd> 检索 <kbd>1..4</kbd> 面板 <kbd>j/k</kbd> 行 <kbd>Enter</kbd> 溯源 <kbd>Esc</kbd> 关</span>
</div>
<nav id="nav" aria-label="面板"></nav>
<main id="main">
  <section id="pane-registry" class="pane" hidden></section>
  <section id="pane-retrieval" class="pane" hidden></section>
  <section id="pane-production" class="pane" hidden></section>
  <section id="pane-audit" class="pane" hidden></section>
  <section id="pane-boot" class="pane"></section>
</main>
<aside id="drawer" class="drawer" aria-label="溯源"></aside>
<footer class="bar"><span id="bar-read">正在读取登记册…</span><span class="grow"></span>
  <button class="btn" id="copy-url" type="button">当前 URL</button></footer>

<script id="ocw-core">
/* 与 DOM 无关的纯函数层。每个原语旁边标注它在 Python 侧的出处，
   改动 queries.py 时必须同步这里（见 CONTRIBUTING.md 评审项 / Task 9 的自检）。 */
globalThis.OCW = (function () {
  'use strict';

  const PANES = ['registry', 'retrieval', 'production', 'audit'];
  const PANE_LABELS = { registry: '注册台', retrieval: '检索台', production: '实验台', audit: '审计台' };

  /* ---- 路由：面板状态全进 hash（可复现） ---- */
  function parseHash(hash) {
    const raw = String(hash || '').replace(/^#/, '');
    const cut = raw.indexOf('?');
    const path = cut < 0 ? raw : raw.slice(0, cut);
    const query = cut < 0 ? '' : raw.slice(cut + 1);
    const pane = path.replace(/^\//, '');
    const state = { pane: PANES.indexOf(pane) >= 0 ? pane : 'registry' };
    new URLSearchParams(query).forEach(function (v, k) { state[k] = v; });
    return state;
  }

  function writeHash(state) {
    const pane = PANES.indexOf(state.pane) >= 0 ? state.pane : 'registry';
    const keys = Object.keys(state).filter(function (k) {
      return k !== 'pane' && state[k] !== '' && state[k] != null;
    }).sort();
    const q = new URLSearchParams();
    keys.forEach(function (k) { q.set(k, String(state[k])); });
    const qs = q.toString();
    return '#' + pane + (qs ? '?' + qs : '');
  }

  /* ---- 取数：只读，唯一数据源是登记册 ---- */
  function needsServer(loc) {
    return String(loc || '').indexOf('file:') === 0;
  }

  async function loadIndex(fetchImpl, url) {
    const f = fetchImpl || globalThis.fetch;
    if (!f) throw new Error('此环境无 fetch：请用 python3 -m http.server 8000 后访问 /工作台/');
    const res = await f(url || '../index.json');
    if (!res.ok) throw new Error('index.json HTTP ' + res.status);
    const data = await res.json();
    if (!data || !Array.isArray(data.entries) || !Array.isArray(data.skills)) {
      throw new Error('index.json 结构不符（缺 entries/skills 数组）');
    }
    return data;
  }

  function fmt(n) {
    return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
  }

  /* OCW:CONTRACT-FUNCS */
  return { PANES, PANE_LABELS, parseHash, writeHash, needsServer, loadIndex, fmt };
})();
</script>

<script id="ocw-app">
(function () {
  'use strict';
  const OCW = globalThis.OCW;

  const App = {
    index: null, graph: null, error: null,
    state: OCW.parseHash(globalThis.location ? globalThis.location.hash : ''),
    rows: [], cursor: 0,
  };
  globalThis.__OCW_APP__ = App;

  function el(tag, attrs, kids) {
    const n = document.createElement(tag);
    for (const k in attrs || {}) {
      if (k === 'text') n.textContent = attrs[k];
      else if (k === 'html') n.innerHTML = attrs[k];
      else if (k.slice(0, 2) === 'on') n.addEventListener(k.slice(2).toLowerCase(), attrs[k]);
      else if (attrs[k] === true) n.setAttribute(k, '');
      else if (attrs[k] !== false && attrs[k] != null) n.setAttribute(k, attrs[k]);
    }
    (Array.isArray(kids) ? kids : kids == null ? [] : [kids]).forEach(function (c) {
      if (c != null) n.appendChild(typeof c === 'string' ? document.createTextNode(c) : c);
    });
    return n;
  }
  App.el = el;

  function renderBar() {
    const bar = document.getElementById('bar-read');
    if (App.error) { bar.textContent = '登记册不可读：' + App.error; return; }
    if (!App.index) { bar.textContent = '正在读取登记册…'; return; }
    const s = App.index.stats;
    bar.textContent = App.index.version + ' · generated ' + App.index.generated +
      ' · 条目 ' + OCW.fmt(s.entries) + ' · 技能 ' + OCW.fmt(s.skills) +
      ' · 合计 ' + OCW.fmt(s.total) + ' · 契约自检 未启用(P4 前)';
  }

  function renderNav() {
    const nav = document.getElementById('nav');
    nav.textContent = '';
    nav.appendChild(el('div', { class: 'grp', text: '面板' }));
    OCW.PANES.forEach(function (p, i) {
      nav.appendChild(el('button', {
        type: 'button',
        'aria-current': App.state.pane === p ? 'page' : false,
        onclick: function () { go({ pane: p }); },
      }, (i + 1) + '. ' + OCW.PANE_LABELS[p]));
    });
  }

  function go(patch) {
    const next = Object.assign({}, App.state, patch);
    App.state = next;
    globalThis.history.pushState(null, '', OCW.writeHash(next));
    render();
  }

  function show(id, on) { document.getElementById(id).hidden = !on; }

  function renderPanes() {
    OCW.PANES.forEach(function (p) { show('pane-' + p, p === App.state.pane && !App.error && App.index); });
    show('pane-boot', App.error ? App.rows.length === 0 : !App.index);
    const boot = document.getElementById('pane-boot');
    if (!App.index && !App.error) { boot.textContent = ''; return; }
    if (App.error) {
      boot.textContent = '';
      boot.appendChild(el('div', { class: 'note bad', text: App.error }));
      if (OCW.needsServer(globalThis.location.href)) {
        boot.appendChild(el('div', { class: 'note', text:
          'file:// 下 fetch ../index.json 会被 CORS 拦截。请在仓库根执行 python3 -m http.server 8000，再访问 http://localhost:8000/工作台/' }));
      }
    }
  }

  function render() { renderBar(); renderNav(); renderPanes(); }

  document.getElementById('copy-url').addEventListener('click', function () {
    const url = globalThis.location.href;
    if (navigator.clipboard) navigator.clipboard.writeText(url);
    this.textContent = '已复制';
    setTimeout(() => { this.textContent = '当前 URL'; }, 1200);
  });
  globalThis.addEventListener('hashchange', function () {
    App.state = OCW.parseHash(globalThis.location.hash);
    App.cursor = 0;
    render();
  });

  OCW.loadIndex().then(function (index) { App.index = index; render(); })
    .catch(function (e) { App.error = String(e && e.message || e); render(); });

  render();
})();
</script>
</body>
</html>
```

- [x] **Step 4: 跑测试确认通过**

Run: `node --test mcp/tests/*.test.mjs`
Expected: PASS —— 6 tests pass（`零第三方资源` 那条会拒绝任何 `https://` 外链）。
实测两处偏离：① core 不用 `URLSearchParams`，改自带 `enc/dec/parseQuery/encodeQuery`，因为 `vm.runInNewContext` 的 context 里没有这个浏览器全局，用了会让纯函数层无法在 Node 侧被测；② 断言跨 realm 需 `plain()` 归一（vm context 的对象字面量带 context 的 `Object.prototype`，`assert/strict` 的 `deepEqual` 比原型）。

- [x] **Step 5: 浏览器实机确认（不可省略的验收）**

```bash
python3 -m http.server 8000 >/dev/null 2>&1 &
sleep 1; curl -s -o /dev/null -w '%{http_code} %{size_download}\n' http://localhost:8000/工作台/
curl -s http://localhost:8000/工作台/ | grep -c 'ocw-core\|ocw-app'
kill %1
```

Expected: `200`；页面底栏显示 `v0.6 · generated … · 条目 2,650 · 技能 149 · 合计 2,799`（数值来自 fetch，非源码字面量）。人工再用浏览器打开 `file://` 版本，确认显示服务提示而非白屏。

- [x] **Step 6: 写 `工作台/README.md`**

```markdown
# 开放认知工作台

只读、无构建、单文件的研究所工作台台面。设计规格见
`_meta/specs/2026-09-23-open-cognition-workbench-design.md`。

## 运行

    python3 -m http.server 8000      # 仓库根
    → http://localhost:8000/工作台/

`file://` 直开会被 CORS 拦住取不到 `index.json`，首屏会给出这句提示。
Pages 部署后同一份文件在 `/open-cognition-database/工作台/` 可用，功能差异只有一处：
`file://`/Pages 下读不到源 `.md`，跨链与原文预览改由 `graph.json` 投影提供。

## 四个面板

| 面板 | 回答 | 原语 |
|---|---|---|
| 注册台 | 我们有什么 | `stats` / `list_skills` |
| 检索台 | 我们找什么 | `search` / `cross_links` / `read_entry` |
| 实验台 | 我们用它产出什么 | `apply_skill`（模板 A/B/C） |
| 审计台 | 我们知道得可靠吗 | CI 命令读数 + `graph.json` 覆盖率 |

5 个原语与 `mcp/open_cognition_mcp/queries.py` 一一对应、同名同参同谓词；
一致性由 `python3 mcp/test_workbench.py` 机械校验。

## 非目标

不编辑条目、不做语义检索、不引第三方脚本、不替代 MCP/CI/`_meta/quality-criteria.md`、
不适配移动端（台面假设 ≥1280px）。

## 自检

    node --test mcp/tests/*.test.mjs   # 前端纯函数（须给文件通配，Node 22 不吃目录参数）
    python3 mcp/test_workbench.py     # 前端 ↔ queries.py 契约一致
```

- [x] **Step 7: 门禁 + 提交**

```bash
python3 _meta/scripts/lint.py --json | python3 -c "import json,sys;print('errors',json.load(sys.stdin)['errors'])"
python3 _meta/scripts/build-index.py --check && python3 mcp/test_queries.py | tail -3
git add 工作台/index.html 工作台/README.md mcp/tests/workbench-core.test.mjs
git commit -m "feat(workbench): P0 单文件骨架（hash 路由 + 只读登记册取数 + 空/错误态）"
```

Expected: `errors 0`；`--check` exit 0；`test_queries.py` 全绿。

---

### Task 3: P1 注册台 —— 领域 × 类型交叉表 + facet 下钻

**Files:**
- Modify: `工作台/index.html`（core 块内 `/* OCW:CONTRACT-FUNCS */` 之前加函数，`return {...}` 里加名字；app 块加 `renderRegistry()`）
- Modify: `mcp/tests/workbench-core.test.mjs`

**Interfaces:**
- Consumes: `App.index`（Task 2）
- Produces: `OCW.matrix(index) -> {domains:string[], types:string[], cells:Record<domain,Record<type,number>>, substantive:number}`；`OCW.facets(index) -> {domain:[{value,count}], type:[...], school:[...], tags:[...]}`（按 count 降序，`school`/`tags` 仅计有值条目）；`OCW.selectEntries(index, state) -> entries[]`；`OCW.redirectCount(index) -> number`。

- [x] **Step 1: 写失败测试**（追加到 `mcp/tests/workbench-core.test.mjs` 末尾）

```js
test('注册台 matrix/facets/select 与登记册一致（真 index.json）', async () => {
  const OCW = loadCore();
  const { readFileSync } = await import('node:fs');
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
  assert.deepEqual(fx.type.map((x) => x.value).sort(),
    [...new Set(index.entries.map((e) => e.type))].sort());
  assert.equal(fx.domain.find((x) => x.value === '宗教').count,
    index.entries.filter((e) => e.domain === '宗教').length);
  assert.equal(fx.school.reduce((a, s) => a + s.count, 0),
    index.entries.filter((e) => e.school).length);

  assert.equal(OCW.selectEntries(index, { type: 'list' }).length,
    index.entries.filter((e) => e.type === 'list').length);
  assert.deepEqual(
    OCW.selectEntries(index, { domain: '哲学', type: 'concept' }).map((e) => e.path).slice(0, 3),
    index.entries.filter((e) => e.domain === '哲学' && e.type === 'concept').map((e) => e.path).slice(0, 3)
  );
  assert.equal(OCW.selectEntries(index, { domain: '不存在' }).length, 0);
});
```

- [x] **Step 2: 跑测试确认失败**

Run: `node --test mcp/tests/*.test.mjs`
Expected: FAIL —— `OCW.matrix is not a function`

- [x] **Step 3: 在 core 里实现（插入 `/* OCW:CONTRACT-FUNCS */` 之前）**

```js
  /* ---- 注册台：一切读数由登记册现算 ---- */
  const LIST_ONLY_FIELDS = ['category', 'channel', 'angle'];

  function bump(table, key, sub) {
    const row = table[key] || (table[key] = {});
    row[sub] = (row[sub] || 0) + 1;
  }

  function matrix(index) {
    const cells = {};
    const types = [];
    for (const e of index.entries) {
      bump(cells, e.domain, e.type);
      if (types.indexOf(e.type) < 0) types.push(e.type);
    }
    const domains = Object.keys(cells).sort();
    let substantive = 0;
    for (const e of index.entries) if (e.type !== 'redirect') substantive += 1;
    return { domains: domains, types: types, cells: cells, substantive: substantive };
  }

  function tally(map, value) {
    if (value == null || value === '') return;
    map[value] = (map[value] || 0) + 1;
  }

  function toSorted(map) {
    return Object.keys(map).map(function (value) {
      return { value: value, count: map[value] };
    }).sort(function (a, b) { return b.count - a.count || (a.value < b.value ? -1 : 1); });
  }

  function facets(index) {
    const d = {}, t = {}, s = {}, g = {};
    for (const e of index.entries) {
      tally(d, e.domain); tally(t, e.type); tally(s, e.school);
      (e.tags || []).forEach(function (x) { tally(g, x); });
    }
    return { domain: toSorted(d), type: toSorted(t), school: toSorted(s), tags: toSorted(g) };
  }

  function selectEntries(index, state) {
    return index.entries.filter(function (e) {
      if (state.domain && e.domain !== state.domain) return false;
      if (state.type && e.type !== state.type) return false;
      if (state.school && e.school !== state.school) return false;
      if (state.tag && (e.tags || []).indexOf(state.tag) < 0) return false;
      for (const f of LIST_ONLY_FIELDS) if (state[f] && String(e[f] || '') !== state[f]) return false;
      return true;
    });
  }

  function redirectCount(index) {
    return index.entries.filter(function (e) { return e.type === 'redirect'; }).length;
  }
```

`return` 行改为：

```js
  return { PANES, PANE_LABELS, parseHash, writeHash, needsServer, loadIndex, fmt,
           matrix, facets, selectEntries, redirectCount, LIST_ONLY_FIELDS };
```

- [x] **Step 4: app 块渲染注册台（在 `renderPanes()` 之前插入 `renderRegistry()`，并在 `renderPanes` 末尾调用）**

```js
  function chips(kind, list, active) {
    const box = el('div', { class: 'chips' });
    list.slice(0, kind === 'tags' ? 40 : 400).forEach(function (f) {
      box.appendChild(el('button', {
        class: 'chip', type: 'button', 'aria-pressed': active === f.value ? 'true' : 'false',
        onclick: function () { go(App.state[kind] === f.value ? { [kind]: '' } : { [kind]: f.value }); },
      }, f.value + ' (' + OCW.fmt(f.count) + ')'));
    });
    return box;
  }

  function renderRegistry() {
    const host = document.getElementById('pane-registry');
    host.textContent = '';
    const mx = OCW.matrix(App.index);
    const table = el('table');
    table.appendChild(el('tr', {}, [el('th', { text: '领域' })].concat(
      mx.types.map((t) => el('th', { class: 'num', text: t })),
      [el('th', { class: 'num', text: '小计' })])));
    mx.domains.forEach(function (d) {
      let rowTotal = 0;
      const cells = mx.types.map(function (t) {
        const n = (mx.cells[d][t] || 0); rowTotal += n;
        return el('td', { class: 'num' }, [n ? el('button', {
          class: 'btn', type: 'button', text: OCW.fmt(n),
          onclick: function () { go({ domain: d, type: t, cell: '' }); },
        }) : el('span', { class: 'dim', text: '0' })]);
      });
      table.appendChild(el('tr', {}, [el('th', { text: d })].concat(cells, [el('td', { class: 'num', text: OCW.fmt(rowTotal) })])));
    });
    host.appendChild(el('h2', { text: '注册台 · 领域 × 类型' }));
    host.appendChild(table);
    host.appendChild(el('div', { class: 'note', text:
      '登记册合计 ' + OCW.fmt(App.index.stats.entries) + '；其中 redirect ' +
      OCW.fmt(OCW.redirectCount(App.index)) + ' 条为子树指针，不计入实质条目（实质 ' +
      OCW.fmt(mx.substantive) + '）。全部数字现算自 index.json。' }));

    const fx = OCW.facets(App.index);
    host.appendChild(el('h3', { text: 'facet' }));
    host.appendChild(chips('domain', fx.domain, App.state.domain));
    host.appendChild(chips('type', fx.type, App.state.type));
    host.appendChild(chips('school', fx.school, App.state.school));
    host.appendChild(chips('tags', fx.tags, App.state.tag));
    if (App.state.type === 'list') {
      const extra = {};
      OCW.LIST_ONLY_FIELDS.forEach(function (f) {
        const m = {};
        App.index.entries.forEach(function (e) { if (e[f]) tallyInto(m, e[f]); });
        extra[f] = Object.keys(m).map((v) => ({ value: v, count: m[v] })).sort((a, b) => b.count - a.count);
      });
      OCW.LIST_ONLY_FIELDS.forEach(function (f) { host.appendChild(chips(f, extra[f], App.state[f])); });
    }

    const rows = OCW.selectEntries(App.index, App.state);
    App.rows = rows;
    host.appendChild(el('h3', { text: '清单 · ' + OCW.fmt(rows.length) + ' 条' }));
    if (!rows.length) { host.appendChild(el('div', { class: 'empty', text: '该组合无登记条目' })); return; }
    const list = el('table');
    list.appendChild(el('tr', {}, ['path', 'id', '标题', '类型', '域'].map((h) => el('th', { text: h }))));
    rows.slice(0, 300).forEach(function (e, i) {
      const tr = el('tr', {
        onclick: function () { App.cursor = i; openDrawer(e); },
      }, [
        el('td', { text: e.path }), el('td', { text: e.id }),
        el('td', { text: e.title }),
        el('td', { text: e.type + (e.type === 'redirect' ? ' · 指向子树' : '') }),
        el('td', { text: e.domain }),
      ]);
      if (i === App.cursor) tr.setAttribute('cursor', '');
      list.appendChild(tr);
    });
    host.appendChild(list);
    if (rows.length > 300) host.appendChild(el('div', { class: 'note', text: '仅渲染前 300 行；用 facet 或检索台缩小范围。' }));
  }

  function tallyInto(m, v) { m[v] = (m[v] || 0) + 1; }
```

并在 `renderPanes()` 的末尾追加：

```js
    if (App.index && !App.error) {
      if (App.state.pane === 'registry') renderRegistry();
    }
```

- [x] **Step 5: 跑测试 + 实机验证**

Run: `node --test mcp/tests/*.test.mjs` → Expected: PASS（计划写 8，实测 7：P0 的 6 个 + 本任务的注册台对照 1 个）

实测偏离两处（已按实况落地）：① `matrix()` 的 `cells[domain][type]` 改为满格输出（缺组合补 0），
因为测试与行小计都直接消费该表达式，否则求和为 `NaN`；`renderRegistry` 里因此去掉了 `|| 0`。
② `assert.deepEqual(fx.type…)` 需先 `plain()` 归一——vm context 返回的数组带该 context 的
`Array.prototype`，`assert/strict` 判原不等。
浏览器：点 `1. 注册台` → 交叉表出现；点任一非零单元格 → 清单表出现且 URL hash 变为 `#/registry?domain=…&type=…`；刷新后视图完整恢复；facet 组合命中 0 时显示"该组合无登记条目"。

- [x] **Step 6: 提交**

```bash
git add 工作台/index.html mcp/tests/workbench-core.test.mjs
git commit -m "feat(workbench): P1 注册台（领域×类型交叉表 + facet 下钻 + 深链）"
```

---

### Task 4: P1 检索台 —— `search` 与 `queries.py:73-90` 严格同谓词

**Files:**
- Modify: `工作台/index.html`（core 加 `search`；app 加 `renderRetrieval()` + `/` 与 `j/k` 键盘流）
- Modify: `mcp/tests/workbench-core.test.mjs`

**Interfaces:**
- Consumes: `App.index`
- Produces: `OCW.search(index, query, domain, type, limit) -> [{path,id,title,type,domain}]`（谓词逐字对齐 Python）。
  （本计划原文另列 `OCW.searchFacets(index, hits)`，但没有任何 Step 或后续 Task 消费它——按 YAGNI 不实现；检索结果的域/类型分布由 facet 下拉与命中表本身承载。执行时确认：全计划仅此处出现该名字。）

- [x] **Step 1: 写失败测试**

```js
import { execFileSync } from 'node:child_process';

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
    assert.deepEqual(OCW.search(index, q), pySearch(q), q);
  }
  assert.deepEqual(OCW.search(index, '概念', '哲学', 'concept', 5), pySearch('概念', '哲学', 'concept', 5));
  assert.deepEqual(OCW.search(index, '异化', '哲学', null, 3).length, pySearch('异化', '哲学', null, 3).length);
});
```

- [x] **Step 2: 跑测试确认失败**

Run: `node --test mcp/tests/*.test.mjs` → Expected: FAIL —— `OCW.search is not a function`

实测：新测试 FAIL 于 `OCW.search is not a function`，既有测试仍 PASS，符合预期。

- [x] **Step 3: 实现 `search`（core，插在 `matrix` 之前并加入 `return`）**

```js
  /* 对应 queries.py:73-90 —— 谓词是 id/title/school + tags 上的大小写不敏感子串匹配。
     默认顺序 = 登记册索引序，前端不做任何隐式加权（要加权必须在此处显式实现并标注）。 */
  function search(index, query, domain, type, limit) {
    const q = String(query == null ? '' : query).toLowerCase();
    const cap = limit == null ? 20 : limit;
    const hits = [];
    for (const e of index.entries) {
      if (domain && e.domain !== domain) continue;
      if (type && e.type !== type) continue;
      let hay = ['id', 'title', 'school'].map(function (k) { return String(e[k] == null ? '' : e[k]); }).join(' ');
      hay += ' ' + (e.tags || []).map(String).join(' ');
      if (hay.toLowerCase().indexOf(q) >= 0) {
        hits.push({ path: e.path, id: e.id, title: e.title, type: e.type, domain: e.domain });
      }
      if (hits.length >= cap) break;
    }
    return hits;
  }
```

Python 的 `hay = " ".join(...)` + `hay += " " + tags` 拼接顺序与空格必须一致——上面两行即是该结构的直译。

- [x] **Step 4: app 渲染检索台 + 键盘流**

（本 Step 下方代码里的 `oninput: go({ q: this.value })` 在执行时被替换为 `setQuery()`：
`go()` 走 `pushState + render()`，会重建整个面板 DOM，每敲一个字符输入框节点就被换掉——
焦点丢失、光标跳回行首。改为只重绘结果区（`renderHits()`）+ `history.replaceState` 同步 hash，
键盘输入不再打断。详见 Step 5 的实测记录。）

```js
  function renderRetrieval() {
    const host = document.getElementById('pane-retrieval');
    host.textContent = '';
    host.appendChild(el('h2', { text: '检索台 · search(query, domain?, type?, limit)' }));
    const box = el('div', { class: 'chips' });
    const input = el('input', { type: 'search', id: 'ocw-q', placeholder: '/ 聚焦后输入子串，如 异化',
      value: App.state.q || '', oninput: function () { go({ q: this.value }); } });
    box.appendChild(input);
    [['domain', '域'], ['type', '类型']].forEach(function (kv) {
      const sel = el('select', { onchange: function () { go({ [kv[0]]: this.value }); } });
      sel.appendChild(el('option', { value: '', text: kv[1] + '：全部' }));
      OCW.facets(App.index)[kv[0]].forEach(function (f) {
        sel.appendChild(el('option', { value: f.value, text: f.value, selected: App.state[kv[0]] === f.value ? 'selected' : false }));
      });
      box.appendChild(sel);
    });
    box.appendChild(el('label', { text: 'limit ' }, el('input', { type: 'search', id: 'ocw-limit', value: App.state.limit || '20',
      style: 'width:56px', onchange: function () { go({ limit: this.value }); } })));
    host.appendChild(box);

    if (!App.state.q) { host.appendChild(el('div', { class: 'empty', text: '尚未输入查询词。' })); return; }
    const hits = OCW.search(App.index, App.state.q, App.state.domain || null, App.state.type || null,
      App.state.limit ? Number(App.state.limit) : null);
    App.rows = hits;
    host.appendChild(el('div', { class: 'note', text:
      '谓词与 mcp/open_cognition_mcp/queries.py 的 search() 严格一致：id/title/school/tags 上的大小写不敏感子串匹配，返回登记册索引序（前端无加权）。命中 ' +
      OCW.fmt(hits.length) + '（受 limit 截断）。' }));
    if (!hits.length) { host.appendChild(el('div', { class: 'empty', text: '该组合无登记条目' })); return; }
    const t = el('table');
    t.appendChild(el('tr', {}, ['path', 'id', '标题', '类型', '域'].map((h) => el('th', { text: h }))));
    hits.forEach(function (h, i) {
      const tr = el('tr', { onclick: function () { App.cursor = i; openDrawer(h); } }, [
        el('td', { text: h.path }), el('td', { text: h.id }), el('td', { text: h.title }),
        el('td', { text: h.type }), el('td', { text: h.domain }),
      ]);
      if (i === App.cursor) tr.setAttribute('cursor', '');
      t.appendChild(tr);
    });
    host.appendChild(t);
  }
```

键盘流（在 app 块末尾、`render()` 调用之前加）：

```js
  function moveCursor(delta) {
    if (!App.rows.length) return;
    App.cursor = Math.min(Math.max(App.cursor + delta, 0), App.rows.length - 1);
    render();
  }
  document.addEventListener('keydown', function (ev) {
    const typing = /^(INPUT|TEXTAREA|SELECT)$/.test(ev.target.tagName);
    if (ev.key === '/' && !typing) { ev.preventDefault(); go({ pane: 'retrieval' }); setTimeout(() => { const i = document.getElementById('ocw-q'); if (i) i.focus(); }, 0); return; }
    if (ev.key === 'Escape') { closeDrawer(); return; }
    if (typing) return;
    if (ev.key >= '1' && ev.key <= '4') { go({ pane: OCW.PANES[Number(ev.key) - 1] }); return; }
    if (ev.key === 'j') { ev.preventDefault(); moveCursor(1); return; }
    if (ev.key === 'k') { ev.preventDefault(); moveCursor(-1); return; }
    if (ev.key === 'Enter' && App.rows[App.cursor]) { openDrawer(App.rows[App.cursor]); }
  });
```

`renderPanes()` 的分派里补 `if (App.state.pane === 'retrieval') renderRetrieval();`。
溯源抽屉（Task 4 一并落地，后续面板复用）：

```js
  function openDrawer(entry) {
    const d = document.getElementById('drawer');
    d.textContent = '';
    d.appendChild(el('h3', { text: '溯源' }));
    d.appendChild(el('dl', {}, [
      el('dt', { text: 'path' }), el('dd', { text: entry.path }),
      el('dt', { text: 'id' }), el('dd', { text: entry.id }),
      el('dt', { text: '域 · 类型' }), el('dd', { text: entry.domain + ' · ' + entry.type }),
      el('dt', { text: '登记册' }), el('dd', { text: App.index.version + ' / generated ' + App.index.generated }),
    ]));
    d.appendChild(el('a', { class: 'btn', href: '../' + encodeURI(entry.path), target: '_blank', rel: 'noopener', text: '打开源文件（站点/仓库）' }));
    document.body.setAttribute('data-drawer', 'open');
    App.drawerEntry = entry;
    renderCrossLinkPane(entry);
  }
  function closeDrawer() {
    document.body.setAttribute('data-drawer', 'closed');
    document.getElementById('drawer').textContent = '';
    App.drawerEntry = null;
  }
```

`renderCrossLinkPane(entry)` 在 Task 5 实现；此 Task 内先占位为说明函数：

```js
  function renderCrossLinkPane(entry) {
    const d = document.getElementById('drawer');
    d.appendChild(el('h4', { text: '跨链（cross_links）' }));
    d.appendChild(el('div', { class: 'note', text: 'Task 5 起由本地图投影提供；当前未加载。' }));
  }
```

- [x] **Step 5: 跑测试 + 实机验证**

Run: `node --test mcp/tests/*.test.mjs` → Expected: PASS（计划写 9，实测 8：P0 的 6 个 + 注册台对照 1 个 + 本任务的 search Python 对照 1 个；对照查询实为 7 组——5 条裸查询 + 深度对照 + limit 边界）

实测偏离四处（已按实况落地）：
① 查询输入不再走 `go({q})`（会重建面板、抢焦点），改 `setQuery()` → `renderHits()` + `replaceState`；
   CDP 检里断言了敲入 `场域` 后 `activeElement.id === 'ocw-q'` 且 `selectionStart === 2`。
② `limit` 是用户输入，属系统边界：新增 `limitArg()`，非整数/空一律回到 MCP 默认 20
   （JS 里 `Number('abc') = NaN`，`hits.length >= NaN` 永假 → 会退化成全表扫描；Python 侧则直接 TypeError）。
③ `OCW.searchFacets` 不实现（见 Interfaces 的 YAGNI 说明）。
④ 本 Step 原拟的浏览器用例 `#/retrieval?q=异化&domain=哲学` 实际命中 0 条
   （`异化` 的两条条目都在 社会学），改用六组 Python 实测计数校准：
   `异化`→2、`自由`→20（limit 截断）、`alienation`（大小写不敏感）→8、`zzz-不存在`→0、
   `概念`+`哲学`+`concept`+`limit=5`→5、`场域`→5。

浏览器（headless Chrome + 自建 CDP 驱动，17 项断言全通过，`/tmp/ocw-task4-check.mjs`，一次性脚本不入库）：
深链 `#/retrieval?q=异化` 粘贴直出 2 行、首行 `社会学/学派/古典社会学/马克思/概念/异化.md`；`&limit=abc` 不抛异常且回落 20 行；
`/` 从注册台跳到检索台并聚焦输入框；`j j` 游标 2、`k` 回 1 且 `tr[cursor]` 随游标移动；`Enter` 开溯源抽屉（含源文件链接）；
`Esc` 关抽屉（`body[data-drawer=closed]`）；`1` 回注册台且 hash 保留 `q`；全程无 `Runtime.exceptionThrown`。

- [x] **Step 6: 提交**

```bash
git add 工作台/index.html mcp/tests/workbench-core.test.mjs
git commit -m "feat(workbench): P1 检索台（search 与 queries.py 同谓词 + 溯源抽屉 + 键盘流）"
```

（提交同时带上本计划文件的 Task 4 勾选与实测记录，与 Task 3 一致。）

---

### Task 5: P1 跨链解析 —— `crossLinks` 对齐 `CROSS_LINK_RE`，Pages 显式降级

**Files:**
- Modify: `工作台/index.html`（core 加 `crossLinks` / `resolveEntryPath`；app 把 Task 4 的占位函数换成真实实现）
- Modify: `mcp/tests/workbench-core.test.mjs`

**Interfaces:**
- Consumes: `App.index`；`App.graph`（Task 7 才有，缺失时走降级）
- Produces: `OCW.crossLinks(mdText, entryPath) -> [{source,target,relation,label}]`（正则 = `queries.py:17-19`）；`OCW.resolveEntryPath(entryPath, target) -> string`；`OCW.edgesFrom(graph, path) -> edges[]`；`OCW.canReadSources(loc) -> boolean`（`file:` → false）。

- [x] **Step 1: 写失败测试**（最终断言见 Step 2 的偏差说明；另加 `crossLinks('')/crossLinks(null)` 与 `edgesFrom` 空投影/坏投影两条边界）

```js
const MD_SAMPLE = [
  '## 跨学科关联', '',
  '- [异化](../概念/alienation.md) `[借用]` 马克思的劳动异化',
  '- 无类型的普通链接 [x](./y.md) 不算边',
  "- 全角引号式：[缘起](./p.md) 「[同构]」",
].join('\n');

test('crossLinks 与 CROSS_LINK_RE 一致：只认带类型的互链，路径归一到仓库根相对', () => {
  const OCW = loadCore();
  const edges = OCW.crossLinks(MD_SAMPLE, '哲学/学派/马克思/README.md');
  assert.deepEqual(edges, [
    { source: '哲学/学派/马克思/README.md', target: '哲学/概念/alienation.md', relation: '借用', label: '异化' },
    { source: '哲学/学派/马克思/README.md', target: '哲学/学派/马克思/p.md', relation: '同构', label: '缘起' },
  ]);
  assert.equal(OCW.canReadSources('file:///x'), false);
  assert.equal(OCW.canReadSources('https://p.github.io/r/工作台/'), true);
});
```

- [x] **Step 2: 跑测试确认失败** → Expected: FAIL —— `OCW.crossLinks is not a function`
  实测：新测试 FAIL 于 `OCW.crossLinks is not a function`，既有 8 个测试仍 PASS。

  **Step 1 的两处偏差（已按实测改写测试，实现未动）：**
  1. 计划期望 `../概念/alienation.md` 从 `哲学/学派/马克思/README.md` 归一到 `哲学/概念/alienation.md`——**少跳一层**。以 Python `(Path('哲学/学派/马克思')/'../概念/alienation.md').resolve().relative_to(REPO)` 为真值，正确结果是 `哲学/学派/概念/alienation.md`。测试断言按 Python 改正并留注释。
  2. Step 5 建议的浏览器夹具 `宗教/佛教/概念/缘起.md` **不存在**（Python `FileNotFoundError`）。改用三个 Python 实测有边的真实条目：`宗教/传统/道教/大师/庄子/概念/庄周梦蝶.md`(4)、`认知系统/学派/分布式认知/哈钦斯.md`(6)、`哲学/学派/存在主义/加缪/概念/哲学性自杀.md`(1)，并加 `assert.ok(want.length, '样例失效…')` 让夹具腐坏时测试炸掉而不是静默通过。

- [x] **Step 3: 实现（core）**（另在 `return` 导出四项，`/* OCW:CONTRACT-FUNCS */` 标记保持在 `return` 前供 Task 9 机械核对）

  与计划的唯一实质差别：`resolveEntryPath` 显式处理**绝对目标**与**跳出仓库根**两种情况并原样返回目标，对齐 Python `relative_to()` 抛 `ValueError` 时 `rel = target` 的分支（`queries.py:99-104`）。先行取证：对 220 个真实条目跑 `queries.cross_links()` 得 95 条边，**无一条绝对或跳出根**，故词法归一在本语料上与 `Path.resolve()` 等价（纯字符串路径不涉及符号链接）——但分支仍写出来，因为降级面板的正确性不能依赖语料巧合。

```js
  /* 对应 queries.py:17-19 的 CROSS_LINK_RE（带类型的跨链：[标签](路径) `[类型]`，允许全角/直角引号） */
  const CROSS_LINK_RE = /\[([^\]]+)\]\(([^)]+\.md)\)\s*[`「]\[([^\]]+)\][`」]/g;

  function resolveEntryPath(entryPath, target) {
    const segs = entryPath.split('/').slice(0, -1);
    for (const part of target.split('/')) {
      if (part === '' || part === '.') continue;
      if (part === '..') segs.pop();
      else segs.push(part);
    }
    return segs.join('/');
  }

  function crossLinks(mdText, entryPath) {
    const re = new RegExp(CROSS_LINK_RE.source, 'g');
    const out = [];
    let m;
    while ((m = re.exec(String(mdText || ''))) !== null) {
      out.push({ source: entryPath, target: resolveEntryPath(entryPath, m[2]),
                 relation: m[3], label: m[1].trim() });
    }
    return out;
  }

  function canReadSources(loc) {
    return !needsServer(loc);
  }

  function edgesFrom(graph, path) {
    if (!graph || !Array.isArray(graph.edges)) return [];
    return graph.edges.filter(function (e) { return e.source === path || e.target === path; });
  }
```

（`needsServer` 已在 Task 2 定义，可直接引用。）`return` 增加 `crossLinks, resolveEntryPath, edgesFrom, canReadSources`。

- [x] **Step 4: app 内把占位换成真实三分支（读得到源 → 现读；有投影 → 用投影；都没有 → 说明原因）**

  在计划片段之上加了三处，均为实测驱动：
  1. `const stale = () => App.drawerEntry !== entry;` —— `renderCrossLinkPane` 是 async，本地分支 `await fetch` 回来时用户可能已点到别的条目；不加守卫就会把 A 的边追加到 B 的抽屉里（`App` 因此补 `drawerEntry: null` 初值，`openDrawer/closeDrawer` 原本已在维护它）。
  2. 本地分支补 `.empty` 措辞「该条目正文没有带类型的互链（登记册未记录即为无，不代表概念上无关联）」——计划的本地分支只打印边数、无边时什么都不说，与"读不到"难以区分，违反规格的认识论底线。
  3. 投影加载成功时除 `render()` 外再 `if (App.drawerEntry) openDrawer(App.drawerEntry)` —— 投影晚到（网络抖动）时抽屉还开着，不重开就停留在降级文案上。投影 404/未生成走 `.catch` 静默降级，不是错误。

```js
  async function renderCrossLinkPane(entry) {
    const d = document.getElementById('drawer');
    const head = el('h4', { text: '跨链（cross_links）' });
    d.appendChild(head);
    if (App.graph) {
      const edges = OCW.edgesFrom(App.graph, entry.path);
      if (!edges.length) { d.appendChild(el('div', { class: 'empty', text: '该条目无显式类型跨链（登记册未记录即为无，不代表概念上无关联）' })); return; }
      const t = el('table');
      t.appendChild(el('tr', {}, ['方向', '关系', '对端'].map((h) => el('th', { text: h }))));
      edges.forEach(function (e) {
        const outgoing = e.source === entry.path;
        t.appendChild(el('tr', {}, [
          el('td', { text: outgoing ? '→' : '←' }),
          el('td', { text: '[' + e.relation + ']' }),
          el('td', { text: outgoing ? e.target : e.source }),
        ]));
      });
      d.appendChild(t);
      d.appendChild(el('div', { class: 'note', text: '边表来自 graph.json（由 build-workbench-graph.py 复用 queries.cross_links 生成，CI --check 保鲜）。' }));
      return;
    }
    if (OCW.canReadSources(globalThis.location.href)) {
      try {
        const res = await fetch('../' + encodeURI(entry.path));
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const edges = OCW.crossLinks(await res.text(), entry.path);
        d.appendChild(el('div', { class: 'note', text: '本地模式：直接解析源 md（' + edges.length + ' 条边）。' }));
        edges.forEach(function (e) { d.appendChild(el('div', { text: '[' + e.relation + '] ' + e.target })); });
      } catch (err) {
        d.appendChild(el('div', { class: 'note bad', text: '源文件读取失败：' + err.message }));
      }
      return;
    }
    d.appendChild(el('div', { class: 'note bad', text:
      '此环境（file://）无法读源 md，且尚未加载 graph.json 投影 → 跨链面板不可用。这不是"无关联"。' +
      '请用 http.server 打开，或等 P3 的 graph.json 落地。' }));
  }
```

`App.graph` 的取数（可选，缺失不报错）：在 `loadIndex().then(...)` 之后加

```js
  OCW.loadGraph ? null : null;
  fetch('graph.json').then(function (r) { return r.ok ? r.json() : null; })
    .then(function (g) { if (g) { App.graph = g; render(); } })
    .catch(function () { /* 投影尚未生成：走降级路径 */ });
```

- [x] **Step 5: 跑测试 + 实机验证**

Run: `node --test mcp/tests/*.test.mjs` → Expected: PASS（10 tests）
**实测 11 pass / 0 fail**（计划写 10，因 Task 4 已把检索台测试从 1 条拆成 2 条：`search` 逐条一致 + `limit` 边界）。

浏览器（`http.server`）：`#/registry` 选一个已知有互链的条目（如 `宗教/佛教/概念/缘起.md`），抽屉出现带 `[关系]` 的边表；改开 `file://` 版本 → 出现"跨链面板不可用"的红色说明而非空表。

**实机改法与结果**（Chrome headless + CDP，一次性脚本，不入库）：
- 计划给的夹具 `宗教/佛教/概念/缘起.md` 不存在（Python `FileNotFoundError`）。换成三个 Python 已 dump 的真实条目，逐格比对 DOM 表格：
  `宗教/传统/道教/大师/庄子/概念/庄周梦蝶.md` → 4 行（发展/平行×3，目标均为同目录 `README.md`）✅ 与 `queries.cross_links()` 逐格一致
  `哲学/学派/存在主义/加缪/概念/哲学性自杀.md` → 1 行（批判，跨域目标 `哲学/学派/宗教/传统/基督教/帕斯卡尔.md`）✅
  `哲学/学派/分析哲学/丹尼特/概念/模因.md` → 0 行 → 渲染 `.empty`「不代表概念上无关联」而非空表 ✅
- 竞态守卫：同一 tick 内先开 A(4 边) 再开 B(1 边)，等待后抽屉只有 1 个 `h4`、只有 B 的 `[批判]`、note 计数「1 条出边」→ A 的迟到响应确被丢弃 ✅
- 投影分支：Task 7 才有真 `graph.json`，故注入同结构假投影 → 表头变 `方向/关系/对端`，三条假边只渲染与当前条目相关的两条且 `→/←` 方向正确，note 说明来源为 `graph.json` ✅（真投影落地后 Task 7 再复验一次）
- `file://` 降级：**抽屉的降级路径只能在 file:// 里手工开**——file:// 下 `index.json` 取不到、四个面板全隐藏，没有可行走的清单，所以先断言启动区给出 `http.server` + CORS 的可执行提示（非白屏），再注入最小合成为 `index` 让 `openDrawer` 可达，断言出现 `.note.bad`「跨链面板不可用…这不是"无关联"」且 `table` 不存在 ✅
- 全程 `Runtime.exceptionThrown` 计数 0 ✅
- 踩坑记录：初版 harness 多带了 `--allow-file-access-from-files=0`，Chrome 把 `=0` 也当开关存在，于是 file:// 竟能 fetch 到 `index.json` → 启动区无提示、误判 FAIL。删掉该 flag 后复现真实浏览器行为。**这条不影响工作台代码，只影响验证脚本。**

- [x] **Step 6: 提交**（提交同时带上本计划文件的 Task 5 勾选与实测记录，与 Task 3/4 一致）

```bash
git add 工作台/index.html mcp/tests/workbench-core.test.mjs
git commit -m "feat(workbench): P1 跨链面板（对齐 CROSS_LINK_RE + 投影/本地/降级三态）"
```

---

### Task 6: P2 实验台 —— 模板 A 与 `queries.apply_skill()` 逐字一致，B/C 依 AGENT.md

**Files:**
- Modify: `工作台/index.html`（core 加 `applySkill` / `templateB` / `templateC` / `exportTriple`；app 加 `renderProduction()`）
- Modify: `mcp/tests/workbench-core.test.mjs`

**Interfaces:**
- Consumes: `App.index.skills`（`{path,name,description,domain,tags}`）
- Produces: `OCW.applySkill(skillText, task) -> string`（== `queries.py:116-125`）；`OCW.templateB(t1, t2, task) -> string`；`OCW.templateC(entryPath) -> string`；`OCW.exportTriple(meta, prompt) -> string`（元信息三元组 + prompt 全文）；`OCW.findSkill(index, idOrPath) -> skill|null`（== `get_skill`）。

- [x] **Step 1: 写失败测试（对照 Python 真值，覆盖一个佛教技能）**

```js
function pyApply(skillId, task) {
  const py = ['import json,sys;sys.path.insert(0,"mcp")',
    'from open_cognition_mcp import queries',
    'sys.stdout.write(queries.apply_skill(sys.argv[1], sys.argv[2]))'].join(';');
  return execFileSync('python3', ['-c', py, skillId, task], { cwd: REPO_ROOT }).toString();
}
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
    assert.equal(mine.charCodeAt(mine.length - 1), 10, '末尾保留换行');
  }
});

test('findSkill 双寻址：英文 slug 或中文路径片段都能定位', () => {
  const OCW = loadCore();
  const index = JSON.parse(readFileSync(REPO_ROOT + 'index.json', 'utf8'));
  assert.equal(OCW.findSkill(index, 'cbt-cognitive-distortion').domain, '心理学');
  assert.equal(OCW.findSkill(index, '认知扭曲识别').name, 'cbt-cognitive-distortion');
  assert.equal(OCW.findSkill(index, '没有这个技能'), null);
});

test('exportTriple 含技能 path、任务、generated 日期三要素', () => {
  const OCW = loadCore();
  const s = OCW.exportTriple({ kind: 'A', skills: ['宗教/佛教/技能/七处征心/SKILL.md'], task: 'T', generated: '2026-09-23' }, 'PROMPT');
  for (const frag of ['宗教/佛教/技能/七处征心/SKILL.md', 'T', '2026-09-23', 'PROMPT']) assert.ok(s.includes(frag), s);
});
```

- [x] **Step 2: 跑测试确认失败** → Expected: FAIL —— `OCW.applySkill is not a function`

- [x] **Step 3: 实现（core）。字符串必须与 `queries.py:116-125` 字符级一致，含 `「」` 与 `→`**

```js
  /* 对应 queries.py:110-125 的 apply_skill()。模板正文以该函数为唯一权威：
     AGENT.md 的 {domain} 变体只是文档示意，改动本函数前先看 mcp/tests 的逐字比对。 */
  function applySkill(skillText, task) {
    return '你是相关领域的认知助手。请严格按以下 Skill 的「操作流程」执行任务。\n\n' +
      '<skill>\n' + skillText + '\n</skill>\n\n' +
      '<task>\n' + task + '\n</task>\n\n' +
      '输出要求：\n' +
      '1. 按 Step 1 → Step N 顺序推进，每步明确写出判断依据\n' +
      '2. 使用 Skill 中的「提问范式」生成问题\n' +
      '3. 在「完整示例」的格式下给出输出\n' +
      '4. 末尾附「反例（误用）」警告\n';
  }

  /* 对应 queries.get_skill()：name 精确匹配，否则按路径子串匹配 */
  function findSkill(index, idOrPath) {
    for (const s of index.skills || []) {
      if (s.name === idOrPath || String(s.path || '').indexOf(idOrPath) >= 0) return s;
    }
    return null;
  }

  /* 模板 B / C 以 AGENT.md:161-187 为准 */
  function templateB(t1, t2, task) {
    return '用两个 Skill 对同一情境做交叉分析：\n\n' +
      '<skill-1>\n' + t1 + '\n</skill-1>\n\n' +
      '<skill-2>\n' + t2 + '\n</skill-2>\n\n' +
      '<task>' + task + '</task>\n\n' +
      '输出：先独立跑两个 Skill，再写一段"两个视角的交叉洞察"。\n';
  }

  function templateC(entryPath) {
    return '我正在读 ' + entryPath + '。请：\n' +
      '1. 用一句话总结核心命题\n' +
      '2. 列出其 `linked_concepts` 中最重要的 3 个，并各写 1 句关系说明\n' +
      '3. 找出 `跨学科关联` 中最有意思的 1 条，展开比较\n' +
      '4. 推荐 1 个最适合此概念的 Skill 来落地使用\n';
  }

  function exportTriple(meta, prompt) {
    const head = [
      '<!-- 开放认知工作台导出 · 只读产物，不写仓库 -->',
      '模板: ' + meta.kind,
      '技能/条目: ' + (meta.skills || [meta.path]).join(' , '),
      '任务: ' + (meta.task || '—'),
      '登记册: ' + meta.version + ' / generated ' + meta.generated,
      '时间: ' + meta.at,
      '---', '', '',
    ].join('\n');
    return head + prompt;
  }
```

（`exportTriple` 的字段按 app 侧传入；测试只断言包含性，故不锁字段顺序。）`return` 增加 `applySkill, templateB, templateC, findSkill, exportTriple`。

- [x] **Step 4: app 渲染实验台（技能表 + 任务框 + prompt 预览 + 复制/下载）**

```js
  function skillTable(host) {
    const q = (App.state.sk || '').toLowerCase();
    const skills = (App.index.skills || []).filter(function (s) {
      if (App.state.domain && s.domain !== App.state.domain) return false;
      if (!q) return true;
      return (String(s.name) + ' ' + String(s.path) + ' ' + String(s.description)).toLowerCase().indexOf(q) >= 0;
    });
    host.appendChild(el('div', { class: 'note', text:
      '技能名是英文 slug、目录与正文是中文 —— 检索同时支持两者（findSkill 与 queries.get_skill 同规则）。当前 ' +
      OCW.fmt(skills.length) + ' / ' + OCW.fmt(App.index.stats.skills) + '。' }));
    const t = el('table');
    t.appendChild(el('tr', {}, ['name', '域', 'description（含触发词）', '选择'].map((h) => el('th', { text: h }))));
    skills.slice(0, 200).forEach(function (s) {
      const picked = App.state.skill === s.name;
      t.appendChild(el('tr', {}, [
        el('td', { text: s.name }), el('td', { text: s.domain }),
        el('td', { text: String(s.description || '').slice(0, 160) }),
        el('td', {}, [el('button', { class: 'btn' + (picked ? ' primary' : ''), type: 'button',
          text: picked ? '已选' : '选为主技能',
          onclick: function () { go({ skill: picked ? '' : s.name, sk2: picked ? App.state.sk2 : App.state.skill }); } })]),
      ]));
    });
    host.appendChild(t);
  }

  async function renderProduction() {
    const host = document.getElementById('pane-production');
    host.textContent = '';
    host.appendChild(el('h2', { text: '实验台 · 模板 A / B / C' }));
    const picker = el('input', { type: 'search', placeholder: '按中文名/slug/触发词筛技能',
      value: App.state.sk || '', style: 'width:340px', oninput: function () { go({ sk: this.value }); } });
    host.appendChild(el('div', { class: 'chips' }, [picker]));
    skillTable(host);

    const ta = el('textarea', { id: 'ocw-task', placeholder: '具体情境/问题/材料',
      oninput: function () { App.taskText = this.value; } });
    if (App.taskText) ta.value = App.taskText;
    host.appendChild(el('h3', { text: '任务' }));
    host.appendChild(ta);

    const out = el('pre', { id: 'ocw-prompt', text: '（选择技能后自动拼装；文本与 queries.apply_skill() 逐字一致）' });
    host.appendChild(el('h3', { text: 'Prompt' }));
    const row = el('div', { class: 'chips' });
    row.appendChild(el('button', { class: 'btn primary', type: 'button', text: 'A 单技能', onclick: () => build('A') }));
    row.appendChild(el('button', { class: 'btn', type: 'button', text: 'B 双技能并行', onclick: () => build('B') }));
    row.appendChild(el('button', { class: 'btn', type: 'button', text: 'C 概念追溯', onclick: () => build('C') }));
    row.appendChild(el('button', { class: 'btn', type: 'button', text: '复制', onclick: () => copy() }));
    row.appendChild(el('button', { class: 'btn', type: 'button', text: '下载 .md', onclick: () => download() }));
    host.appendChild(row);
    host.appendChild(out);

    async function readSkillText(s) {
      const res = await fetch('../' + encodeURI(s.path));
      if (!res.ok) throw new Error('读不到 ' + s.path + '（HTTP ' + res.status + '）：本面板需要本地 http.server 或 Pages 源可读');
      return res.text();
    }

    async function build(kind) {
      const task = App.taskText || '';
      try {
        let prompt;
        const used = [];
        if (kind === 'A') {
          const s = OCW.findSkill(App.index, App.state.skill);
          if (!s) throw new Error('先在上方选一个技能');
          used.push(s.path);
          prompt = OCW.applySkill(await readSkillText(s), task);
        } else if (kind === 'B') {
          const a = OCW.findSkill(App.index, App.state.skill), b = OCW.findSkill(App.index, App.state.sk2);
          if (!a || !b) throw new Error('模板 B 需要选两个技能（先主技能，再点另一个技能的"选为主技能"前用 sk2）');
          used.push(a.path, b.path);
          prompt = OCW.templateB(await readSkillText(a), await readSkillText(b), task);
        } else {
          const p = App.state.path || (App.rows[App.cursor] && App.rows[App.cursor].path);
          if (!p) throw new Error('模板 C 需要先在注册台/检索台用 Enter 选中一个条目');
          used.push(p);
          prompt = OCW.templateC(p);
        }
        App.prompt = prompt;
        App.exportMeta = { kind: kind, skills: used, task: task, version: App.index.version,
          generated: App.index.generated, at: new Date().toISOString().slice(0, 10) };
        out.textContent = prompt;
      } catch (e) { out.textContent = '未拼装：' + e.message; }
    }
    function copy() {
      if (!App.prompt) return;
      const payload = OCW.exportTriple(App.exportMeta, App.prompt);
      if (navigator.clipboard) navigator.clipboard.writeText(payload);
    }
    function download() {
      if (!App.prompt) return;
      const blob = new Blob([OCW.exportTriple(App.exportMeta, App.prompt)], { type: 'text/markdown' });
      const a = el('a', { href: URL.createObjectURL(blob), download: 'ocw-' + App.exportMeta.kind + '-' + App.exportMeta.at + '.md' });
      document.body.appendChild(a); a.click(); a.remove();
    }
  }
```

`renderPanes()` 分派补 `production`；B 的第二技能选择按钮文案与 `sk2` 状态：在 `skillTable` 的按钮点击逻辑里已按"先主后副"迁移旧主技能，UI 上再加一行说明：

```js
    host.appendChild(el('div', { class: 'note', text:
      'B 模板：先点第一个技能，再点第二个（第一次点击会把已选主技能挪到 sk2）。C 模板：用注册台/检索台 Enter 选中的条目路径。' }));
```

- [x] **Step 5: 跑测试 + 实机验证**

Run: `node --test mcp/tests/*.test.mjs` → Expected: PASS（13 tests）
浏览器：选 `cbt-cognitive-distortion`、填同一任务、点 A → 预览与终端 `python3 -c "...print(queries.apply_skill('cbt-cognitive-distortion','同一任务'))"` 完全一致；宗教域选 `七处征心` 再验一次；导出"下载 .md"落地在浏览器下载目录（**不是仓库**）。

> 实测：`node --test` 15 pass / 0 fail（计划写 13，Task 5 落地时核心用例多了 2 条，非回归）。
> 浏览器（headless Chrome + CDP，`node /tmp/ocw-task6-check.mjs`）13 组全绿：A 与 `queries.apply_skill()` 逐字相同（cbt 2528 字符、七处征心 2642 字符）；B 与 AGENT.md 模板 + Python 技能正文逐字相同（5393 字符）；C 由 `openDrawer` 写入 hash 的 `path` 深链直接复现；导出落 `/var/folders/…/ocw-dl-*`，`git status --porcelain` 无新增未跟踪文件；file:// 下给 `http.server` 红色提示且不产半成品；外部 `src/href` 计数 0；`Runtime.exceptionThrown` 计数 0。

- [x] **Step 6: 提交**

> 与计划的实现偏差（均为可用性问题，非契约变更）：
> 1. 技能表每行给「设为主 / 设为副」两个按钮，取代计划的"先点第一个再点第二个、首次点击自动把主技能挪到 sk2"——迁移式单选在误点后不可见地改掉了已选主技能，回显成本高于两个按钮。
> 2. 状态提示写入独立的 `#ocw-msg .note`（成功=灰、错误=红），不写进 `<pre>` 预览区，避免把提示当 Prompt 内容一起复制。
> 3. 域 `<select>` 复用共享的 `state.domain`（与注册台/检索台同一个键），而非实验台私有键；`sk`（技能子串）为实验台私有。
> 4. 任务正文留在 `App.taskText`，刻意不进 hash（可达数千字符且含换行，深链无意义）；技能/副技能/域/条目路径进 hash。
> 5. `openDrawer()` 除渲染抽屉外，把选中条目 `path` 写入 hash（`replaceState`，不产生历史噪声）——模板 C 因此可从 URL 直接复现。
> 6. 模板 B 增加"同一技能既主又副"守护并报错，不出半截交叉分析 Prompt。
> 7. `readSkillText()` 在 file:// 下先拦一道给出 `python3 -m http.server 8000` 的可执行提示，而不是让 fetch 抛 `TypeError` 被误读为模板坏了。

```bash
git add 工作台/index.html mcp/tests/workbench-core.test.mjs
git commit -m "feat(workbench): P2 实验台（模板 A/B/C，A 与 queries.apply_skill 逐字一致）"
```

---

### Task 7: P3 投影 —— `build-workbench-graph.py`（复用 `queries.py`）+ CI `--check`

**Files:**
- Create: `_meta/scripts/build-workbench-graph.py`
- Create: `工作台/graph.json`（脚本产物）
- Modify: `.github/workflows/ci.yml`（`index-consistency` job 内加一步）
- Test: 命令行（Step 1/4）

**Interfaces:**
- Consumes: `mcp/open_cognition_mcp/queries.py`（`stats`、`list_skills`、`get_skill`、`cross_links`、`read_entry`）；`eval/cases/*.yaml`
- Produces: `工作台/graph.json` = `{version, generated, edges:[{source,target,relation,label}], typed_entries, eval:{cases:[{skill_id,domain,file}],skills_total,covered,domains:Record<domain,number>}, coverage:{entries,school_filled,tags_filled,unique_tags,skills}}`；CLI `--out` / `--check`（语义同 `build-index.py`：只比内容，忽略 `generated`）

- [x] **Step 1: 失败断言**

```bash
ls 工作台/graph.json 2>/dev/null || echo "MISSING (expected)"
python3 _meta/scripts/build-workbench-graph.py --check; echo "exit=$? (expected 2 / no such file)"
```

- [x] **Step 2: 写脚本**（`_meta/scripts/build-workbench-graph.py`）

```python
#!/usr/bin/env python3
"""
build-workbench-graph.py — 为 工作台/ 生成只读投影 graph.json。

刻意复用 mcp/open_cognition_mcp/queries.py 的实现来产出边表与覆盖率，
这样前端拿到的投影与 MCP 服务永远同源（漂移由 Task 9 的契约自检兜底）。
派生数据必须保鲜，因此提供 --check：语义与 build-index.py 一致——
只比较内容，忽略 generated 日期。

Usage:
    python3 _meta/scripts/build-workbench-graph.py           # 写 工作台/graph.json
    python3 _meta/scripts/build-workbench-graph.py --check   # 过期则 exit 1
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "mcp"))

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("ERROR: pyyaml is required. Install with `pip install pyyaml`.")

from open_cognition_mcp import queries  # noqa: E402

VERSION = "v0.6"
DEFAULT_OUT = REPO_ROOT / "工作台" / "graph.json"


def index() -> dict:
    return json.loads((REPO_ROOT / "index.json").read_text(encoding="utf-8"))


def build_edges(idx: dict) -> tuple[list[dict], int]:
    """对每个登记条目跑 queries.cross_links（读源 md），汇总全库边表。"""
    edges: list[dict] = []
    typed = 0
    for e in idx["entries"] + idx.get("skills", []):
        path = e.get("path")
        if not path or not (REPO_ROOT / path).exists():
            continue
        try:
            found = queries.cross_links(path)
        except (OSError, ValueError):
            continue
        if found:
            typed += 1
        edges.extend(found)
    return sorted(edges, key=lambda x: (x["source"], x["target"], x["relation"])), typed


def build_eval() -> dict:
    cases = []
    for f in sorted((REPO_ROOT / "eval" / "cases").glob("*.yaml")):
        data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        cases.append({
            "file": f"eval/cases/{f.name}",
            "skill_id": str(data.get("skill_id") or data.get("skill") or ""),
            "domain": str(data.get("domain") or ""),
        })
    skills = idx = queries.list_skills()
    by_name = {s.get("name"): s for s in skills}
    by_path = {s.get("path"): s for s in skills}
    covered = set()
    for c in cases:
        sid = c["skill_id"]
        if sid in by_name or sid in by_path:
            covered.add(sid)
    domains: dict[str, int] = {}
    for c in cases:
        d = c["domain"] or "（未标注）"
        domains[d] = domains.get(d, 0) + 1
    return {
        "cases": cases,
        "skills_total": len(skills),
        "covered": len(covered),
        "domains": dict(sorted(domains.items(), key=lambda kv: (-kv[1], kv[0]))),
    }


def build_coverage(idx: dict) -> dict:
    entries = idx["entries"]
    tags: set[str] = set()
    for e in entries:
        tags.update(str(t) for t in (e.get("tags") or []))
    return {
        "entries": len(entries),
        "school_filled": sum(1 for e in entries if e.get("school")),
        "tags_filled": sum(1 for e in entries if e.get("tags")),
        "unique_tags": len(tags),
        "skills": len(idx.get("skills", [])),
    }


def build_graph() -> dict:
    idx = index()
    edges, typed = build_edges(idx)
    return {
        "version": VERSION,
        "generated": date.today().isoformat(),
        "typed_entries": typed,
        "edges": edges,
        "eval": build_eval(),
        "coverage": build_coverage(idx),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=DEFAULT_OUT, type=Path)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    payload = json.dumps(build_graph(), ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if not args.out.exists():
            print(f"MISSING: {args.out}", file=sys.stderr)
            return 1
        current = args.out.read_text(encoding="utf-8")
        strip = lambda o: {k: v for k, v in o.items() if k != "generated"}
        try:
            same = strip(json.loads(current)) == strip(json.loads(payload))
        except json.JSONDecodeError:
            same = False
        if same:
            print(f"OK: {args.out} 与源一致")
            return 0
        print(f"STALE: {args.out} — 运行 python3 _meta/scripts/build-workbench-graph.py", file=sys.stderr)
        return 1
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(payload, encoding="utf-8")
    g = json.loads(payload)
    print(f"Wrote {args.out}: {len(g['edges'])} edges / {g['typed_entries']} typed entries; "
          f"eval {g['eval']['covered']}/{g['eval']['skills_total']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [x] **Step 3: 生成并核对与规格实测数字一致**

```bash
python3 _meta/scripts/build-workbench-graph.py
python3 - <<'EOF'
import json
g = json.load(open("工作台/graph.json"))
assert g["typed_entries"] == 296, g["typed_entries"]
assert len(g["edges"]) == 1111, len(g["edges"])
assert g["eval"]["skills_total"] == 149 and g["eval"]["covered"] == 10
assert g["coverage"]["school_filled"] == 1400 and g["coverage"]["tags_filled"] == 1897
print("projection matches spec measurements")
EOF
```

Expected: PASS。若 `edges` 不等于 1111：以脚本输出为准（登记册自上次测量后可能新增互链），**不要**回改断言成硬编码常量，改为记录新基线并在 commit message 里说明——工作台的原则是"数字来自投影"。

- [x] **Step 4: 验证 `--check` 的腐坏检测**

```bash
python3 _meta/scripts/build-workbench-graph.py --check; echo "fresh exit=$? (期望 0)"
python3 - <<'EOF'
from pathlib import Path
p = Path("工作台/graph.json"); t = p.read_text(encoding="utf-8")
p.write_text(t.replace('"typed_entries": 296', '"typed_entries": 999'), encoding="utf-8")
EOF
python3 _meta/scripts/build-workbench-graph.py --check; echo "stale exit=$? (期望 1)"
python3 _meta/scripts/build-workbench-graph.py   # 复原
```

Expected: `fresh exit=0`、`stale exit=1`（STALE 提示），最后复原。

实测（2026-09-23）：`fresh exit=0` → 篡改 `typed_entries` 后 `STALE: …工作台/graph.json — 运行 python3 _meta/scripts/build-workbench-graph.py` / `stale exit=1` → 重生成后 `restored exit=0`。另测得缺失文件时 exit=2（与 `build-index.py` 的 MISSING 约定一致）。

- [x] **Step 5: CI 保鲜步骤**（`.github/workflows/ci.yml`，`index-consistency` job 的 `--check` 那步之后追加）

```yaml
      - name: Verify workbench projection matches sources
        run: python3 _meta/scripts/build-workbench-graph.py --check
```

- [x] **Step 6: 提交**

```bash
git add _meta/scripts/build-workbench-graph.py 工作台/graph.json .github/workflows/ci.yml \
    工作台/index.html mcp/tests/workbench-core.test.mjs _meta/plans/2026-09-23-open-cognition-workbench.md
git commit -m "feat(workbench): P3 跨链图投影 graph.json（复用 queries.py）+ CI 保鲜"
```

**Task 7 实测与偏差（执行时记录）**

1. **Step 3 数字**：`Wrote 工作台/graph.json: 1111 edges / 296 typed entries; eval 10/149; dangling targets 62`。计划的四条规格断言（296 / 1111 / 149·10 / 1400·1897）全中，不需要改基线。关系分布：88 种标签，Top = 平行 255、基础 129、互补 100、发展 95。
2. **投影日期拆开**：计划里 `generated` 一个字段同时当"登记册日期"和"构建日期"。改为 `generated` 继承 index.json 且**参与** `--check` 比较（投影必须自述它是哪一版登记册派生的），另加 `projection` = 构建当日且**不**参与比较。否则登记册每天重建会让投影误报 STALE，或者反过来让投影谎报自己的新鲜度。
3. **`dangling` 字段（计划外）**：1111 条边里 62 个目标文件不存在（涉及 52 个源条目，另有 1 条自环——自环不是错，条目可以引用自己）。根因是早期中文化把旧英文路径留在正文里。**没有**去改 md 正文：那超出 Task 7 范围，而且会让投影与 `queries.cross_links()` 不再逐字段同源。改为投影自述 `dangling` 清单，抽屉里断链对端标红 + 一句"边本身是真的，断的是落点——修的是 md 链接，不是删掉这条边"。
4. **eval 域直方图回填**：`eval/cases/*.yaml` 里没有一条写了 `domain:`，照计划直算会得到空方图。改为从解析到的技能回填 domain，并给每个 case 记 `resolved`（10 命中登记册 / 139 未覆盖）——缺口本身就是审计台要显示的东西。
5. **exit 码**：文件缺失 → 2（对齐 `build-index.py` 的 MISSING），计划正文只写了 0/1。
6. **同源性改成机械证据**：新增测试 `graph.json 出边与 queries.cross_links() 逐字段一致`——从真投影取排序后 source 序列的首/中/尾三条，与 Python 现算结果比**多重集**（投影按 (source,target,relation) 全局排序，Python 按正文顺序；顺序差不是漂移，字段差才是）。这是 Task 9 契约自检的前置。
7. **技能文件目前零出边**：296 个 typed source 全部来自 entries，149 个 SKILL.md 无一命中 `CROSS_LINK_RE`。首版测试按"概念/技能/其他"分层抽样，因此拿不到第三个样本而失败——改为首/中/尾，并把这一事实写进测试注释而不是假装分层成立。
8. **file:// 文案过期**：降级提示原文是"…或等 P3 的 graph.json 落地"，投影落地后这句成了谎话 → 改为"取不到 graph.json 投影，也无法读源 md"，并把可执行的下一步写全（`python3 -m http.server 8000` → `http://localhost:8000/工作台/`）。

**实机验证**（`/tmp/ocw-task7-check.mjs`，一次性脚本不入库）：http:// 下投影加载并与磁盘逐字段一致；混合条目 17 行表格 / 1 处断链标红 / 两条 note 到位；纯入边条目 4 行全为 ←；零边条目走"无显式类型跨链"而不是"面板不可用"；file:// 下 `App.graph === null` 且降级措辞如实；全程 `Runtime.exceptionThrown == 0`。门禁：`node --test` 17/17、lint errors 0、`build-index --check` 0、`build-workbench-graph --check` 0、`mcp/test_queries.py` 全绿、`check-nav-links --errors-only` 0。

---

### Task 8: P3 审计台 —— 门禁命令原样可读 + 覆盖率现算 + eval 缺口显式

**Files:**
- Modify: `工作台/index.html`（core 加 `gates()` / `coverageRows(graph)`；app 加 `renderAudit()`）
- Modify: `mcp/tests/workbench-core.test.mjs`

**Interfaces:**
- Consumes: `App.index`、`App.graph`
- Produces: `OCW.gates(index)` → `[{name, cmd, note}]`（4 条 = CI 实际跑的命令）；`OCW.coverageRows(graph)` → `[{dim, value, ratio, gap:boolean, why}]`；`OCW.pct(n, d) -> string`

- [x] **Step 1: 写失败测试**

```js
test('审计台读数来自投影，不出现手写常量', () => {
  const OCW = loadCore();
  const graph = JSON.parse(readFileSync(REPO_ROOT + '工作台/graph.json', 'utf8'));
  const rows = OCW.coverageRows(graph);
  const byDim = Object.fromEntries(rows.map((r) => [r.dim, r]));
  assert.equal(byDim['显式跨链条目'].value, graph.typed_entries);
  assert.equal(byDim['eval 覆盖'].ratio,
    (100 * graph.eval.covered / graph.eval.skills_total).toFixed(1) + '%');
  assert.ok(byDim['eval 覆盖'].gap);           // 缺口必须显式而非省略
  assert.ok(byDim['school 填充'].gap);
  assert.ok(!rows.some((r) => typeof r.value === 'string' && /^[\d.]+$/.test(r.value) === false && r.value === ''));
  const gates = OCW.gates(JSON.parse(readFileSync(REPO_ROOT + 'index.json', 'utf8')));
  assert.equal(gates.length, 4);
  assert.ok(gates.every((g) => /^python3 /.test(g.cmd)), JSON.stringify(gates));
  assert.ok(gates.map((g) => g.cmd).join('\n').includes('_meta/scripts/build-workbench-graph.py --check'));
});
```

- [x] **Step 2: 跑测试确认失败** → Expected: FAIL —— `OCW.coverageRows is not a function`

- [x] **Step 3: 实现（core）**

```js
  function pct(n, d) { return d ? (100 * n / d).toFixed(1) + '%' : '—'; }

  /* 审计台读的就是 CI 跑的同一批命令，原样可复制（不另造质量标准）。 */
  function gates(index) {
    return [
      { name: '条目 lint', cmd: 'python3 _meta/scripts/lint.py --json', note: 'errors 必须为 0；warns 是设计内 backlog（W006 等），不阻塞' },
      { name: '索引新鲜', cmd: 'python3 _meta/scripts/build-index.py --check', note: 'index.json 必须等于一次全新构建（忽略 generated 日期）' },
      { name: '导航机械断链', cmd: 'python3 _meta/scripts/check-nav-links.py --errors-only', note: '只阻塞目标在库内存在的错链；未撰写条目属内容 backlog' },
      { name: '投影新鲜', cmd: 'python3 _meta/scripts/build-workbench-graph.py --check', note: '跨链图/覆盖率/eval 覆盖的投影保鲜门禁' },
      { name: 'eval 拼装（离线）', cmd: 'python3 eval/run_eval.py --dry', note: '只校验用例格式与 prompt 拼装；真实跑需 OPENAI_BASE_URL/API_KEY/MODEL' },
    ].filter(function (g) { return index && g.cmd !== '__never__'; });
  }

  function coverageRows(graph) {
    const c = graph.coverage, ev = graph.eval;
    return [
      { dim: '登记条目', value: c.entries, ratio: '—', gap: false, why: 'index.json entries（不含 skills）' },
      { dim: '技能', value: c.skills, ratio: '—', gap: false, why: 'index.json skills' },
      { dim: 'school 填充', value: c.school_filled, ratio: pct(c.school_filled, c.entries), gap: c.school_filled / c.entries < 0.8, why: '学派归属未覆盖即无法按学派导航' },
      { dim: 'tags 填充', value: c.tags_filled, ratio: pct(c.tags_filled, c.entries), gap: c.tags_filled / c.entries < 0.8, why: '唯一标签 ' + c.unique_tags + ' 个 → 长尾极碎，需受控词表' },
      { dim: '显式跨链条目', value: graph.typed_entries, ratio: pct(graph.typed_entries, c.entries), gap: graph.typed_entries / c.entries < 0.5, why: '质量标准要求"至少 1 条跨领域互链"；边数 ' + graph.edges.length },
      { dim: 'eval 覆盖', value: ev.covered, ratio: pct(ev.covered, ev.skills_total), gap: ev.covered / ev.skills_total < 0.5, why: '结构完整 ≠ 已验证能正确引导 LLM 执行' },
    ];
  }
```

`gates()` 的 5 条里前 4 条即 CI 门禁；第 5 条是本地离线校验（验收标准要求"4 条门禁命令 + 可复制"，多给的 eval 行同样可复制且注明离线，不构成偏差）。若评审严格要求恰好 4 条，删掉 `eval 拼装` 那一项即可——测试断言 `>= 4` 时改回 `=== 4` 并同步删除该对象。

- [x] **Step 4: app 渲染审计台**

```js
  function renderAudit() {
    const host = document.getElementById('pane-audit');
    host.textContent = '';
    host.appendChild(el('h2', { text: '审计台 · 我们知道得可靠吗' }));
    if (!App.graph) {
      host.appendChild(el('div', { class: 'note bad', text:
        '缺 graph.json 投影 → 覆盖率与跨链密度不可读。本地请运行 python3 _meta/scripts/build-workbench-graph.py 后刷新。' }));
    }
    host.appendChild(el('h3', { text: '门禁（与 CI 同源，可复制执行）' }));
    const gt = el('table');
    gt.appendChild(el('tr', {}, ['项', '命令', '判定'].map((h) => el('th', { text: h }))));
    OCW.gates(App.index).forEach(function (g) {
      gt.appendChild(el('tr', {}, [
        el('th', { text: g.name }),
        el('td', {}, [el('code', { text: g.cmd, style: 'user-select:all' }), ' ',
          el('button', { class: 'btn', type: 'button', text: '复制', onclick: function () { navigator.clipboard && navigator.clipboard.writeText(g.cmd); } })]),
        el('td', { text: g.note }),
      ]));
    });
    host.appendChild(gt);
    host.appendChild(el('div', { class: 'note', text:
      '浏览器不能执行 Python：本表只给命令与 CI 的判定规则。真实读数由投影 graph.json 承载的部分见下表，其余以本地实跑 / Actions 三色为准。' }));

    if (App.graph) {
      host.appendChild(el('h3', { text: '结构健康与缺口' }));
      const ct = el('table');
      ct.appendChild(el('tr', {}, ['维度', '读数', '占比', '说明'].map((h) => el('th', { text: h }))));
      OCW.coverageRows(App.graph).forEach(function (r) {
        ct.appendChild(el('tr', {}, [
          el('th', { text: r.dim }),
          el('td', { class: 'num', text: OCW.fmt(r.value) }),
          el('td', {}, [el('span', { class: 'pill ' + (r.gap ? 'bad' : 'ok'), text: r.ratio })]),
          el('td', { text: r.why }),
        ]));
      });
      host.appendChild(ct);

      host.appendChild(el('h3', { text: 'eval 覆盖矩阵（技能 × 有无用例）' }));
      const ev = App.graph.eval;
      const names = {};
      (App.index.skills || []).forEach(function (s) { names[s.name] = s; });
      const withCase = {};
      ev.cases.forEach(function (c) { withCase[c.skill_id] = c.file; });
      const byDomain = {};
      (App.index.skills || []).forEach(function (s) {
        byDomain[s.domain] = byDomain[s.domain] || { total: 0, covered: 0 };
        byDomain[s.domain].total += 1;
        if (withCase[s.name]) byDomain[s.domain].covered += 1;
      });
      const et = el('table');
      et.appendChild(el('tr', {}, ['域', '技能', '有用例', '覆盖率'].map((h) => el('th', { text: h }))));
      Object.keys(byDomain).sort().forEach(function (d) {
        const v = byDomain[d];
        et.appendChild(el('tr', {}, [
          el('th', { text: d }), el('td', { class: 'num', text: OCW.fmt(v.total) }),
          el('td', { class: 'num', text: OCW.fmt(v.covered) }),
          el('td', {}, [el('span', { class: 'pill ' + (v.covered ? 'warn' : 'bad'), text: OCW.pct(v.covered, v.total) })]),
        ]));
      });
      host.appendChild(et);
      host.appendChild(el('div', { class: 'note bad', text:
        '全库 eval 覆盖 ' + ev.covered + ' / ' + ev.skills_total + '（' + OCW.pct(ev.covered, ev.skills_total) +
        '）。这是本台面最需要说出口的数字：绝大多数技能从未被验证过能正确引导执行。' }));
      host.appendChild(el('details', { class: 'note' }, [
        el('summary', { text: '已覆盖技能（' + ev.cases.length + ' 个用例）' }),
      ]).appendChild((function () {
        const ul = el('ul');
        ev.cases.forEach(function (c) { ul.appendChild(el('li', { text: c.skill_id + ' → ' + c.file })); });
        return ul;
      })()));
    }
    host.appendChild(el('div', { class: 'note bad', text:
      '登记册盲区：' });
    );
  }
```

`renderPanes()` 分派补 `audit`。底栏"契约自检"读数在 Task 9 前保持 `未启用(P4 前)`。

- [x] **Step 5: 跑测试 + 实机验证**

Run: `node --test mcp/tests/*.test.mjs` → Expected: PASS（14 tests）
浏览器：面板 4 显示门禁表 + 覆盖率 + eval 矩阵；把命令粘进终端逐条执行，与 Actions 三色一致；删掉 `工作台/graph.json` 刷新 → 出现红色缺失说明而非空白（测完 `git checkout 工作台/graph.json` 复原）。

- [x] **Step 6: 提交**

```bash
git add 工作台/index.html mcp/tests/workbench-core.test.mjs
git commit -m "feat(workbench): P3 审计台（门禁同源 + 投影覆盖率 + eval 缺口显式）"
```

**Task 8 实测与偏差（执行时记录）**

1. **门禁 4→5 行，每行带 `ci` 布尔**：计划测试断言 `gates.length === 4`，而 Step 3 实现列了 5 条（末条是真实的离线校验 `eval/run_eval.py --dry`，删掉它反而违反"可复制"的初衷）。决议：`gates()` 返回 5 行，每行带 `ci: true/false`，"4 条 = CI 实际跑的命令"按字面成立——node 测试解析 ci.yml 的 `run:` 步骤，逐条证明 4 条 `ci:true` 命令都在其中且只有 1 条非 CI 行。计划 1764 行的备选（删 eval 行、断言改回 `=== 4`）未采用。
2. **`gates()` 签名**：计划版 `gates(index)` 的 `index` 是死参——`g.cmd !== '__never__'` 过滤器永不触发。改为无参 `gates()`：CI 命令清单不依赖登记册内容。core 返回行同步更新。
3. **Step 1 恒真式断言重写**：原断言 `!rows.some((r) => typeof r.value === 'string' && /^[\d.]+$/.test(r.value) === false && r.value === '')` 对任何 rows 都为真。改为两条实质断言：(a) 凡有 ratio 的行 `Number.isFinite(value) && ratio 非空`；(b) 用变异投影（篡改 coverage/eval 数值的 `fake` graph）喂 `coverageRows`，行读数跟随变异——证明读数现算、没有手写常量。
4. **计划 Step 4 片段两处缺陷**：(a) `el('details', …, [[sum, ul]])` 嵌套数组——`el()` 只展开一层，嵌套数组被直接 `appendChild` 抛类型错；异常逃出 `renderAudit` 被 App 全局 handler 捕获 → `App.error` 置位 → 全部面板被隐藏（浏览器实测首跑即此症状）。修法：提 `caseList` 变量、传平铺 `[summary, caseList]`，并让 summary 带上未解析用例计数。(b) 片段末尾 `host.appendChild(el('div', { class: 'note bad', text: '登记册盲区：' });` 语法未闭合且只有标题。实作补全为 6 条盲区清单（dangling 62 落点、技能文件零出边、tags 长尾 6770、eval 10/149、check-nav 203 backlog、门禁绿≠语义有效），并在 core 增 `evalMatrix(index, graph)` 出"域 × 技能 × 有无用例"矩阵——矩阵行和 = `stats.skills`、Σ有用例 = `eval.covered` 的不变量在浏览器 harness 里对磁盘读数核过。
5. **Step 5"删掉 graph.json"改为可逆改名**：`renameSync` 到 `/tmp`（不 `rm`、不 `git checkout`），`finally` 改回并断言 sha256 前后相等。顺带发现 `python3 -m http.server` 只发 `Last-Modified`，Chrome 启发式缓存会端出改名前的旧文件，造成"缺投影"测试假阴性——测试加 `Network.setCacheDisabled` 并轮询 `App.graph === null`。
6. **实测**：`/tmp/ocw-task8-check.mjs`（一次性脚本不入库）11 节全过——`#/audit` 深链直达、门禁表 5 行（前 4 无 ⊘、第 5 行 ⊘ 前缀）、复制按钮落在"已复制/请手动选中"之一、覆盖率 6 行读数与磁盘 graph.json 逐字段一致、eval 矩阵行和、盲区 6 条、用例 `<details>` 10 项、无假 STALE + 注入旧 `generated` 后出真 STALE、footer 仍是"未启用(P4 前)"、全程 `Runtime.exceptionThrown == 0`、缺投影降级文案如实。5 条门禁命令本机逐条 exit 0（lint errors 0 / index --check OK 2799 / graph --check OK / nav-links 0 机械错链 / eval --dry 10 用例全过）；`node --test` 19/19。
7. **提交范围**：在本步两文件之外补加本计划文件（偏差块所在），与 Task 7 同例。

---

### Task 9: P4 契约自检 + 文档入口 + 验收

**Files:**
- Create: `mcp/test_workbench.py`
- Create: `mcp/fixtures/workbench-parity.json`（由上者生成，纳入版本控制）
- Create: `mcp/tests/workbench-parity.test.mjs`
- Modify: `.github/workflows/ci.yml`（新增 `workbench-contract` job）
- Modify: `README.md`、`README.en.md`、`AGENT.md`、`INDEX.md`、`CONTRIBUTING.md`、`工作台/README.md`
- Modify: `_meta/scripts/check-nav-links.py:31`（`SKIP_DIRS` 里失效的 `"scripts"` → 移除，并对新增入口做一次全量确认）

**Interfaces:**
- Consumes: `queries.search/apply_skill/list_skills/stats/cross_links`
- Produces: `python3 mcp/test_workbench.py [--check]`（exit 0/1）；夹具结构 `{version, stats, search:{q:[hits]}, apply_skill:[{skill_id,path,task,prompt}], list_skills:{domain:count}, cross_links:[{entry_path, md_excerpt, edges}]}`

- [x] **Step 1: 写夹具生成器（Python 侧真值来源）** — `mcp/test_workbench.py`（含 run_node 显式展开 *.test.mjs，见偏差 1）

```python
#!/usr/bin/env python3
"""
test_workbench.py — 校验 工作台/index.html 的前端纯函数与 queries.py 逐字一致。

两步：
  1. 由 Python 侧（唯一权威）生成契约夹具 mcp/fixtures/workbench-parity.json；
     --check 时不写文件，只比较现有夹具是否等于当前真值。
  2. 用 node --test 跑 mcp/tests/，让前端 core 重放同一夹具并断言相等。

Usage:
    python3 mcp/test_workbench.py           # 刷新夹具 + 跑 node
    python3 mcp/test_workbench.py --check  # CI：夹具过期或前端漂移则 exit 1
    python3 mcp/test_workbench.py --python-only
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "mcp"))

from open_cognition_mcp import queries  # noqa: E402

FIXTURE = REPO_ROOT / "mcp" / "fixtures" / "workbench-parity.json"
QUERIES = ["异化", "ALIENATION", "wuwei", "场域", "zzz-不存在"]
SKILLS = ["cbt-cognitive-distortion", "qichu-zhengxin-deconstruction",
          "madhyamaka-four-fallacies", "bourdieu-field-analysis"]
TASK = "我连续三周在评审会上说不出反驳意见，回家又觉得自己错了。"

failures: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"{'ok' if ok else 'FAIL'}   {label}" + (f"  — {detail}" if detail and not ok else ""))
    if not ok:
        failures.append(label)


def build_fixture() -> dict:
    idx = json.loads((REPO_ROOT / "index.json").read_text(encoding="utf-8"))
    fx: dict = {
        "version": idx["version"],
        "stats": idx["stats"],
        "search": {q: queries.search(q) for q in QUERIES},
        "search_filtered": {
            "哲学/concept/5": queries.search("概念", domain="哲学", type="concept", limit=5),
        },
        "apply_skill": [],
        "list_skills": {},
        "cross_links": [],
    }
    for sid in SKILLS:
        skill = queries.get_skill(sid)
        if skill is None:
            raise SystemExit(f"fixture 需要技能存在于登记册: {sid}")
        fx["apply_skill"].append({
            "skill_id": sid, "path": skill["path"], "task": TASK,
            "prompt": queries.apply_skill(sid, TASK),
        })
    for s in idx["skills"]:
        d = s.get("domain") or ""
        fx["list_skills"][d] = fx["list_skills"].get(d, 0) + 1
    # 跨链样本：取第一条含类型互链的条目，连原文片段一起入夹具（前端无需读源文件即可断言）
    for e in idx["entries"]:
        edges = queries.cross_links(e["path"])
        if edges:
            text = queries.read_entry(e["path"])
            fx["cross_links"].append({
                "entry_path": e["path"],
                "md_excerpt": text[:4000],
                "edges": edges,
            })
            break
    return fx


def run_node() -> int:
    return subprocess.call(["node", "--test", str(REPO_ROOT / "mcp" / "tests")], cwd=str(REPO_ROOT))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--python-only", action="store_true")
    args = ap.parse_args()

    fx = build_fixture()
    payload = json.dumps(fx, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        current = FIXTURE.read_text(encoding="utf-8") if FIXTURE.exists() else ""
        same = current == payload
        check("夹具等于当前 Python 真值", same, "夹具过期：运行 python3 mcp/test_workbench.py")
    else:
        FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE.write_text(payload, encoding="utf-8")
        check("夹具已生成", True, str(FIXTURE.relative_to(REPO_ROOT)))
    check("stats 三数自洽", fx["stats"]["total"] == fx["stats"]["entries"] + fx["stats"]["skills"])
    check("search 返回条目的键集合固定", all(
        set(h) == {"path", "id", "title", "type", "domain"}
        for hits in fx["search"].values() for h in hits))
    check("apply_skill 均非空且以换行结尾", all(
        a["prompt"].endswith("\n") and "<skill>" in a["prompt"] for a in fx["apply_skill"]))
    check("cross_links 样本含边", bool(fx["cross_links"]) and bool(fx["cross_links"][0]["edges"]))

    if failures:
        return 1
    if args.python_only:
        return 0
    return run_node()


if __name__ == "__main__":
    raise SystemExit(main())
```

- [x] **Step 2: 写前端重放测试** — `mcp/tests/workbench-parity.test.mjs`（plain() 归一化 + md_text 全文，见偏差 3/4；另加契约标记测试，见偏差 5）

```js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import { loadCore, REPO_ROOT } from './workbench-core.test.mjs';

const FIXTURE = REPO_ROOT + 'mcp/fixtures/workbench-parity.json';
const fx = existsSync(FIXTURE) ? JSON.parse(readFileSync(FIXTURE, 'utf8')) : null;
const index = JSON.parse(readFileSync(REPO_ROOT + 'index.json', 'utf8'));
const OCW = loadCore();

test('夹具存在（先运行 python3 mcp/test_workbench.py）', () => {
  assert.ok(fx, 'mcp/fixtures/workbench-parity.json 缺失');
});

test('search 与夹具（= queries.search）逐条一致', { skip: !fx }, () => {
  for (const [q, expected] of Object.entries(fx.search)) {
    assert.deepEqual(OCW.search(index, q), expected, `query=${q}`);
  }
  assert.deepEqual(OCW.search(index, '概念', '哲学', 'concept', 5), fx.search_filtered['哲学/concept/5']);
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

test('crossLinks 与夹具（= queries.cross_links）一致', { skip: !fx }, () => {
  for (const sample of fx.cross_links) {
    assert.deepEqual(OCW.crossLinks(sample.md_excerpt, sample.entry_path), sample.edges);
  }
});
```

并在 core 里补 `listSkills`（对应 `queries.py:37-45`，含 tags 命中的大小写规则）：

```js
  function listSkills(index, domain) {
    let skills = (index && index.skills) || [];
    if (domain) {
      const dl = String(domain).toLowerCase();
      skills = skills.filter(function (s) {
        return dl.indexOf(String(s.domain || '').toLowerCase()) >= 0 || dl === String(s.domain || '').toLowerCase()
          || (s.tags || []).map(String).map(function (t) { return t.toLowerCase(); }).indexOf(dl) >= 0;
      });
    }
    return skills;
  }
```

注意 Python 侧是 `dl in str(domain).lower()`（子串包含，方向是"参数在域名里"），上面第一行 `dl.indexOf(...) >= 0` 与之同向，测试须覆盖 `listSkills(index, '宗')` 与 `listSkills(index, '宗教')` 两种：

```js
test('list_skills 的 domain 匹配方向与 Python 一致（参数是域名子串）', () => {
  const all = OCW.listSkills(index);
  assert.equal(all.length, index.stats.skills);
  assert.equal(OCW.listSkills(index, '宗教').length, index.skills.filter((s) => s.domain === '宗教').length);
  assert.equal(OCW.listSkills(index, '宗').length, index.skills.filter((s) => s.domain && s.domain.includes('宗')).length);
  assert.equal(OCW.listSkills(index, 'zzz').length, 0);
});
```

- [x] **Step 3: 生成夹具并跑全量测试**

```bash
python3 mcp/test_workbench.py
```

Expected: 全 `ok` + node 侧全 pass（`mcp/tests/` 现共 19 项，含 parity 6 项）。
实测：46/46 pass / 0 fail（测试 19 已随偏差 7 扩到 6 行门禁）。

- [x] **Step 4: CI 新增契约 job**（`.github/workflows/ci.yml` 末尾；已加，见偏差 7 的同源联动）

```yaml
  workbench-contract:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - uses: actions/setup-node@v4
        with:
          node-version: "22"
      - name: Install deps
        run: pip install pyyaml
      - name: Workbench ↔ queries.py parity (fixture freshness + JS replay)
        run: python3 mcp/test_workbench.py --check
```

- [x] **Step 5: 手写常量 grep（验收 1 / 6 的机械化）**（两次 grep 均 exit 1，无命中）

```bash
cd /Users/allengaller/Documents/GitHub/peace-lab-global/open-cognition-database
grep -n "2799\|2650\|\b149\b\|1111\|\b296\b\|52\.8\|71\.6" 工作台/index.html; echo "grep exit=$? (期望 1)"
grep -nE '(src|href)="https?://' 工作台/index.html; echo "external exit=$? (期望 1)"
```

Expected: 两次 grep 均无输出（exit 1）。若命中，把常量改为运行时计算或改为夹具/投影读取。

- [x] **Step 6: 四处文档入口（各 1 处 + 一句话）**（按实况落位，见偏差 10）

`README.md` 与 `README.en.md`：在"如何使用 / How to use"类小节末尾加

```markdown
- **开放认知工作台**（只读、单文件、无构建）：`python3 -m http.server 8000` → `http://localhost:8000/工作台/`。
  把登记册、MCP 查询层、Prompt 模板与 CI 质控收敛到一个台面：[`工作台/README.md`](./工作台/README.md)。
```

（英文版对应：`- **Open Cognition Workbench** (read-only, single-file, no build): serve the repo root with `python3 -m http.server 8000` and open `http://localhost:8000/工作台/`. It puts the registry, the MCP query layer, the prompt templates and the CI gates on one surface — see [`工作台/README.md`](./工作台/README.md).`）

`AGENT.md` 的"目录结构"块内加一行：

```markdown
工作台/          开放认知工作台（只读单文件台面，读 index.json + graph.json）
```

`INDEX.md` 顶部"速查"区加：

```markdown
> 想在浏览器里操作这些条目：[开放认知工作台](./工作台/index.html)（只读，需本地 http.server 或 Pages）。
```

`CONTRIBUTING.md` 的评审清单加：

```markdown
- [ ] 改了 `mcp/open_cognition_mcp/queries.py` 或 AGENT.md 的 Prompt 模板 → 同步 `工作台/index.html` 的 `ocw-core`，并跑 `python3 mcp/test_workbench.py`
```

`_meta/scripts/check-nav-links.py:31` 的 `SKIP_DIRS` 里删掉 `"scripts"`（该目录已归档到 `_meta/scripts/`，条目失效）。

- [x] **Step 7: 全门禁 + Pages 实机**（六门禁全 exit 0；三种底栏状态经 agent-browser 实机核验，含夹具过期与 file:// 降级）

```bash
python3 _meta/scripts/lint.py --json | python3 -c "import json,sys;d=json.load(sys.stdin);print('errors',d['errors'],'warns',d['warns'])"
python3 _meta/scripts/build-index.py --check
python3 _meta/scripts/build-workbench-graph.py --check
python3 _meta/scripts/check-nav-links.py --errors-only
python3 mcp/test_queries.py
python3 mcp/test_workbench.py --check
node --test mcp/tests/
node --version && python3 _meta/scripts/check-nav-links.py | tail -3
```

Expected: `errors 0`；三个 `--check` 全 exit 0；`test_queries.py` 11 项全绿；`test_workbench.py` 全绿；nav 断链总数不高于基线 203。
Pages 实机（提交后由用户在 Actions 部署，或本地 `bundle exec jekyll build` 目视）：确认 `/open-cognition-database/工作台/` 可打开、底栏读数正确、跨链面板走 `graph.json` 而非空表。若本地无 Jekyll，则以此命令替代并把结果写进提交信息：`python3 -m http.server 8000` 下访问 `工作台/`，逐条对照验收 1–7。

- [x] **Step 8: 提交**（本地 main 提交，不 push；计划文件一并入库，见偏差 10）

```bash
git add mcp/test_workbench.py mcp/fixtures/workbench-parity.json mcp/tests/workbench-parity.test.mjs \
  .github/workflows/ci.yml README.md README.en.md AGENT.md INDEX.md CONTRIBUTING.md \
  工作台/README.md 工作台/index.html _meta/scripts/check-nav-links.py
git commit -m "$(cat <<'EOF'
test(workbench): P4 契约自检 + 文档入口

新增 mcp/test_workbench.py：由 queries.py 生成 workbench-parity.json 夹具，
再让前端 ocw-core 在 node --test 里重放（search / apply_skill / list_skills /
cross_links 逐条与逐字比对）。CI 增加 workbench-contract job；四处文档加入口。
EOF
)"
```

### Task 9 实测与偏差（执行时记录）

1. `run_node()` 改为显式展开 `*.test.mjs`：目录形式 `node --test mcp/tests` 在 Node 22 上被当成模块路径解析而失败。
2. 计划的 `listSkills` 片段子串方向写反；按 Python 规则实现（`d.indexOf(dl) >= 0`），并把脆弱的 `likePython` 期望改为重算同一条规则。
3. 前端 core 经 `vm.runInNewContext` 求值，返回值携带沙箱 realm 原型，`deepStrictEqual` 对同结构数组/对象恒红（"not reference-equal"）；parity 断言改用 `workbench-core.test.mjs` 已有的 `plain()`（JSON 归一化）包住 OCW 结果，原语断言不受影响。
4. 计划夹具存 `md_excerpt: text[:4000]`，而 `queries.cross_links` 解析全文——截断点之后的边在前端重放中消失。改存全文，键名 `md_excerpt` → `md_text`。
5. 超出计划补一个机械测试：`/* OCW:CONTRACT-FUNCS */` 契约标记——解析 core 返回行上的函数名清单，逐一断言在活 `OCW` 上存在，防「改名但契约清单未同步」。
6. 底栏契约读数定为三种诚实状态（取不到夹具 / 夹具与登记册同版·逐字比对由 CI / 夹具过期），不冒充绿灯；浏览器实机核验时发现 `vv0.6` 双 v（`fx.version` 自带 `v` 前缀），去掉硬编码前缀后复验通过。
7. CI 追加第 5 个 run 步骤后，审计台 `gates()` 与 ci.yml 的同源承诺被打破 → 门禁清单 4→6 行（5 条 CI + 1 条离线 `--check`），core 测试 19 更名并同步断言（CI 行数 4→5、清单总长 5→6），面板注释 4→5 / 5→6。
8. `check-nav-links.py` 的 `SKIP_DIRS` 实际在第 27 行（计划写 31 行）；移除失效的 `"scripts"` 后 nav 无回归。
9. `工作台/README.md` 的「现状」段停留在 P0 期文本，重写为三条底栏状态的如实描述；新增「盲区记录：名言/ 未入登记册」一节（P3 投影如实暴露的登记册盲区，修复属内容侧独立议题）。
10. 文档入口按实况落位：README.md 加在「给人类读者」清单（无 How-to-use 节）；README.en.md 无 How-to-use，放 Repository Structure 末尾；CONTRIBUTING 无 checkbox 评审清单 → 加为「十、PR 审核标准」第 8 条。计划文件本身随本任务一并提交（沿 Task 7/8 先例）。

---

## Self-Review（计划完成后自查，已就地修正）

1. **Spec coverage**：规格第三节四面板 → Task 3/4/5（注册+检索+跨链）、Task 6（实验台）、Task 7/8（投影+审计台）；第四节技术选型（单文件、`http.server`、无 Liquid、相对路径）→ Task 2 骨架与 Step 5 的 grep 断言；第六节缺口表 → Task 8 `coverageRows` + `graph.json` 断言（含 `名言/` 盲区，由 Task 8 Step 4 末尾的红色 note 呈现；执行时把该 note 写成：`登记册盲区：名言/ 的 md 未入 index.json，故本台面不显示它——这是投影暴露的真问题，修复属后续独立议题`，其计数不写死，改由 `工作台/README.md` 记录发现过程）；第七节 IA 与键盘 → Task 2（底栏/抽屉）+ Task 4（键盘流）；第八节验收 1–9 → Task 9 Step 5/6/7 与 Task 2 Step 5；第九节分期 → Task 2–9 一一对应；第十一节文件清单 → 各 Task Files（新增：`工作台/index.html`、`工作台/README.md`、`工作台/graph.json`、`_meta/scripts/build-workbench-graph.py`、`mcp/fixtures/`、`mcp/tests/`、`mcp/test_workbench.py`；修改：README×2、AGENT、INDEX、CONTRIBUTING、ci.yml、check-nav-links.py，另加计划外的钩子与文档计数修复 Task 0/1）。
2. **Placeholder scan**：Task 8 Step 4 末尾那条未闭合的 `el('div', ...)` 与"盲区"文案在自审中改成了明确的字符串指令（见上第 1 点的说明），执行时以完整 note 节点写入，不留 `——` 式待办；其余步骤均含可运行代码或完整命令。
3. **Type consistency**：`OCW.matrix/facets/selectEntries/redirectCount/search/crossLinks/resolveEntryPath/edgesFrom/canReadSources/applySkill/templateB/templateC/findSkill/exportTriple/listSkills/gates/coverageRows/pct/fmt/parseHash/writeHash/needsServer/loadIndex/PANES/PANE_LABELS/LIST_ONLY_FIELDS` 与 app 侧调用一一对应；App 字段 `index/graph/state/rows/cursor/error/taskText/prompt/exportMeta/drawerEntry` 全程同名；夹具键名 `search/search_filtered/apply_skill/list_skills/cross_links` 与 `workbench-parity.test.mjs` 读取键一致；`graph.json` 键 `edges/typed_entries/eval{cases,skills_total,covered,domains}/coverage{entries,school_filled,tags_filled,unique_tags,skills}` 在 Task 7 生成、Task 5 `edgesFrom`、Task 8 `coverageRows` 三处消费且拼写一致。
