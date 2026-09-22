#!/usr/bin/env node
// 叶子重命名映射 (v2 - 精确规则)
const fs = require('fs');
const path = require('path');
const ROOT = '/Users/allengaller/Documents/GitHub/peace-lab-global/open-cognition';

function parseFrontmatter(text) {
  const m = text.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!m) return {};
  const obj = {};
  let currentKey = null;
  for (const line of m[1].split(/\r?\n/)) {
    if (/^\s+-\s+/.test(line) && currentKey) {
      if (!Array.isArray(obj[currentKey])) obj[currentKey] = [];
      obj[currentKey].push(line.replace(/^\s+-\s+/, '').trim().replace(/^["']|["']$/g, ''));
      continue;
    }
    const m2 = line.match(/^([A-Za-z_][\w-]*):\s*(.*)$/);
    if (m2) {
      currentKey = m2[1];
      let v = m2[2].trim();
      if ((v.startsWith('"') && v.endsWith('"')) || (v.startsWith("'") && v.endsWith("'"))) v = v.slice(1, -1);
      obj[currentKey] = v;
    }
  }
  return obj;
}

function extractChinese(title, slug) {
  if (!title) return slug || '';
  // 先在 · • 上分段
  const parts = title.split(/[·•]/).map(s => s.trim()).filter(Boolean);
  for (const p of parts) {
    if (!/[\u4e00-\u9fff]/.test(p)) continue;
    // 在 " / " " : " " (" ") " 等分隔符上再切, 取第一段 (通常是中文部分)
    const segs = p.split(/\s*[\/:：]\s*|\s*\(|\)|\s+(?=[A-Za-z])/).filter(Boolean);
    // 在 segs 里找第一个含中文的段
    for (const seg of segs) {
      if (/[\u4e00-\u9fff]/.test(seg)) {
        const chs = seg.match(/[\u4e00-\u9fff]/g);
        if (chs && chs.length >= 1) return chs.join('');
      }
    }
    // 都没有, 从整个 p 提取所有中文
    const chs = p.match(/[\u4e00-\u9fff]/g);
    if (chs && chs.length >= 1) return chs.join('');
  }
  // 全 title 范围
  const all = title.match(/[\u4e00-\u9fff]/g);
  if (all && all.length >= 1) return all.join('');
  return slug || '';
}

function safeFilename(s) {
  // 去除文件系统/ shell 不安全字符
  return s.replace(/[\/\\:*?"<>|'`\s\(\)\[\]{}]/g, '');
}

function walk(dir) {
  const out = [];
  if (!fs.existsSync(dir)) return out;
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.name === '.git' || e.name === 'node_modules' || e.name === '_meta' || e.name === 'scripts') continue;
    if (e.isDirectory()) out.push(...walk(p));
    else if (e.isFile() && p.endsWith('.md')) out.push(p);
  }
  return out;
}

const allFiles = walk(ROOT);
const renameMap = [];
const seen = new Set();

function add(type, oldPath, newPath, chinese, disambig) {
  if (oldPath === newPath) return false;
  if (seen.has(oldPath)) return false;
  seen.add(oldPath);
  renameMap.push({ type, old: oldPath, new: newPath, chinese, disambig: disambig || '' });
  return true;
}

// ===== STEP 1: 扫描 thinker 目录 (有 stub .md + 同名 dir) =====
const thinkerStubs = new Set(); // 记录 stub 文件的完整路径
for (const file of allFiles) {
  if (file.endsWith('README.md') || file.endsWith('INDEX.md') || file.endsWith('SKILL.md')) continue;
  const dir = path.dirname(file);
  const base = path.basename(file, '.md');
  const sibDir = path.join(dir, base);
  if (fs.existsSync(sibDir) && fs.statSync(sibDir).isDirectory()) {
    const text = fs.readFileSync(file, 'utf8');
    const fm = parseFrontmatter(text);
    const ch = safeFilename(extractChinese(fm.title || fm.name, base));
    if (ch && ch !== base) {
      thinkerStubs.add(file);
      add('thinker-dir', sibDir, path.join(dir, ch), ch);
      add('thinker-stub', file, path.join(dir, ch + '.md'), ch);
    }
  }
}

// ===== STEP 2: 独立概念文件 (不在 thinker 目录内) =====
for (const file of allFiles) {
  if (file.endsWith('README.md') || file.endsWith('INDEX.md') || file.endsWith('SKILL.md')) continue;
  if (thinkerStubs.has(file)) continue;
  // 排除 thinker 子目录里的附属文件 (reading-list, timeline, works)
  const base = path.basename(file, '.md');
  if (['reading-list', 'timeline', 'works'].includes(base)) continue;
  // 排除已有中文名的文件
  if (/[\u4e00-\u9fff]/.test(base)) continue;
  const text = fs.readFileSync(file, 'utf8');
  const fm = parseFrontmatter(text);
  if (fm.type !== 'concept' && fm.type !== 'thinker') continue;
  const ch = safeFilename(extractChinese(fm.title));
  if (!ch) continue;
  const dir = path.dirname(file);
  // 不要与目录下的其他文件冲突
  add('concept-file', file, path.join(dir, ch + '.md'), ch);
}

// ===== STEP 3: Skills =====
for (const file of allFiles) {
  if (!file.endsWith('SKILL.md')) continue;
  const skillDir = path.dirname(file);
  const skillId = path.basename(skillDir);
  if (skillId === '技能' || skillId === 'skills') continue;
  const text = fs.readFileSync(file, 'utf8');
  const fm = parseFrontmatter(text);
  // 从 description 提取: "能力方法分析 (Capability Approach Analysis)..." -> "能力方法分析"
  const desc = fm.description || '';
  let ch = '';
  // 先试 description 开头纯中文 (到括号/英文/标点为止), 至少 3 字
  let m = desc.match(/^([\u4e00-\u9fff]{3,8})(?:\s*[\(（,.，。、:：]|$)/);
  if (m) ch = m[1];
  if (!ch) {
    // 再试 description 中第一个中文短语
    m = desc.match(/([\u4e00-\u9fff]{3,6})(?:[\s\(\)（）])/);
    if (m) ch = m[1];
  }
  if (!ch) {
    // 从 H1 取
    const h1 = (text.match(/^#\s+(.+)$/m) || [])[1] || '';
    ch = extractChinese(h1);
  }
  if (!ch || ch.length < 3) continue;
  ch = safeFilename(ch);
  if (ch.length > 6) ch = ch.slice(0, 6);
  add('skill-dir', skillDir, path.join(path.dirname(skillDir), ch), ch);
}

// ===== STEP 4: 学派子目录 (school slugs -> 中文) =====
const schoolMap = {
  // philosophy
  analytic: '分析哲学', 'ancient-greek': '古希腊', comparative: '比较哲学', eastern: '东方哲学',
  empiricism: '经验主义', enlightenment: '启蒙运动', existentialism: '存在主义',
  'german-idealism': '德国唯心论', hermeneutics: '诠释学', 'medieval-scholastic': '中世纪经院',
  pessimism: '悲观主义', phenomenology: '现象学', 'political-philosophy': '政治哲学',
  'post-structuralism': '后结构主义', pragmatism: '实用主义', rationalism: '理性论',
  'scottish-common-sense': '苏格兰常识学派',
  // sociology
  'actor-network': '行动者网络', classical: '古典社会学', critical: '批判理论',
  figurational: '形态社会学', functionalism: '功能主义', 'gender-studies': '性别研究',
  interactionism: '互动论', modernity: '现代性', 'network-society': '网络社会',
  'race-studies': '种族研究', structuralism: '结构主义', structuration: '结构化理论',
  // psychology
  'analytical-psychology': '分析心理学', 'behavioral-economics': '行为经济学',
  behaviorism: '行为主义', cognitive: '认知心理学', developmental: '发展心理学',
  'existential-psychology': '存在心理学', 'interpersonal-neurobiology': '人际神经生物学',
  'narrative-therapy': '叙事疗法', 'object-relations': '客体关系', positive: '积极心理学',
  psychoanalysis: '精神分析', 'social-learning': '社会学习', 'trauma-psychology': '创伤心理学',
  'individual-psychology': '个体心理学', humanistic: '人本主义',
  // ethics-politics
  'capability-approach': '能力方法', 'care-ethics': '关怀伦理学', communitarianism: '社群主义',
  consequentialism: '结果主义', 'critical-theory': '批判理论', deontology: '道义论',
  libertarianism: '自由至上主义', 'nonviolent-resistance': '非暴力抵抗',
  'social-contract': '社会契约论', 'virtue-ethics': '德性伦理学',
  // aesthetics
  'arts-thought': '艺术思想', 'chinese-aesthetics': '中国美学', 'critical-aesthetics': '批判美学',
  'german-aesthetics': '德国美学', 'literary-theory': '文学理论', 'literary-thought': '文学思想',
  'nietzschean-aesthetics': '尼采美学', 'poetic-thought': '诗性思想', 'pragmatist-aesthetics': '实用主义美学',
  // arts
  music: '音乐', 'performing-arts': '表演艺术', 'visual-arts': '视觉艺术',
  // literature
  dramatists: '剧作家', essayists: '散文家', novelists: '小说家', poets: '诗人',
  // cognitive-systems
  'automation-sociotechnical': '自动化社会技术', 'cognitive-engineering': '认知工程',
  cybernetics: '控制论', distributed: '分布式认知', ecological: '生态认知',
  'naturalistic-decision': '自然决策', 'safety-science': '安全科学',
  // buddhism schools
  'chan-zen': '禅宗', chengshi: '成实宗', dilun: '地论宗', faxiang: '法相宗',
  huayan: '华严宗', 'jodo-shinshu': '净土真宗', kosa: '俱舍宗', madhyamaka: '中观学派',
  nichiren: '日莲宗', niepan: '涅槃宗', nyingma: '宁玛派', 'pure-land': '净土宗',
  rinzai: '临济宗', sanlun: '三论宗', shelun: '摄论宗', soto: '曹洞宗',
  theravada: '上座部', tiantai: '天台宗', vajrayana: '密宗', vinaya: '律宗', yogacara: '唯识学派',
};
for (const file of allFiles) {
  const idx = file.indexOf('/学派/');
  if (idx < 0) continue;
  const after = file.slice(idx + 4);
  const slashIdx = after.indexOf('/');
  if (slashIdx < 0) continue;
  const slug = after.slice(0, slashIdx);
  const ch = schoolMap[slug];
  if (!ch) continue;
  const oldDir = path.join(file.slice(0, idx), '学派', slug);
  const newDir = path.join(file.slice(0, idx), '学派', ch);
  add('school-dir', oldDir, newDir, ch);
}

// ===== STEP 5: 宗教/传统 + 宗教/智慧大师/masters 下子目录 =====
const tradMap = {
  buddhism: '佛教', christianity: '基督教', confucianism: '儒教', hinduism: '印度教',
  islam: '伊斯兰教', judaism: '犹太教', shinto: '神道教', sikhism: '锡克教', taoism: '道教',
};
const geoMap = { china: '中国', india: '印度', japan: '日本', thailand: '泰国', tibet: '西藏', west: '西方' };
const tradRoot = path.join(ROOT, '宗教', '传统');
if (fs.existsSync(tradRoot)) {
  for (const e of fs.readdirSync(tradRoot, { withFileTypes: true })) {
    if (!e.isDirectory()) continue;
    if (tradMap[e.name]) add('trad-dir', path.join(tradRoot, e.name), path.join(tradRoot, tradMap[e.name]), tradMap[e.name]);
  }
}
const geoRoot = path.join(ROOT, '宗教', '智慧大师', 'masters');
if (fs.existsSync(geoRoot)) {
  for (const e of fs.readdirSync(geoRoot, { withFileTypes: true })) {
    if (!e.isDirectory()) continue;
    if (geoMap[e.name]) add('geo-dir', path.join(geoRoot, e.name), path.join(geoRoot, geoMap[e.name]), geoMap[e.name]);
  }
}

// ===== STEP 6: 冲突消歧 - 同目录下同名者加旧 slug 后缀 =====
const targetGroups = {};
renameMap.forEach((r, i) => {
  if (!targetGroups[r.new]) targetGroups[r.new] = [];
  targetGroups[r.new].push(i);
});
const conflicts = Object.entries(targetGroups).filter(([, v]) => v.length > 1);
conflicts.forEach(([newPath, indices]) => {
  for (let k = 1; k < indices.length; k++) {
    const r = renameMap[indices[k]];
    const oldBase = path.basename(r.old).replace(/\.md$/, '');
    if (r.new.endsWith('.md')) {
      renameMap[indices[k]].new = r.new.replace(/\.md$/, '-' + oldBase + '.md');
    } else {
      renameMap[indices[k]].new = r.new + '-' + oldBase;
    }
    renameMap[indices[k]].disambig = oldBase;
  }
});

fs.writeFileSync('/tmp/rename-map.json', JSON.stringify(renameMap, null, 2));
console.log('Total:', renameMap.length);
const byType = {};
renameMap.forEach(m => byType[m.type] = (byType[m.type] || 0) + 1);
console.log('By type:', byType);

// 验证: 重新检查冲突
const verify = {};
renameMap.forEach(r => {
  if (!verify[r.new]) verify[r.new] = [];
  verify[r.new].push(r.old);
});
const remaining = Object.entries(verify).filter(([, v]) => v.length > 1);
console.log('Remaining conflicts:', remaining.length);
if (remaining.length) remaining.slice(0, 5).forEach(([k, v]) => console.log('  ' + k + ' <- ' + v.join(' | ')));
