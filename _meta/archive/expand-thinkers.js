#!/usr/bin/env node

import { mkdirSync, writeFileSync, readFileSync, existsSync } from 'fs';
import { join, dirname } from 'path';

const BASE = '/Users/allengaller/Documents/GitHub/peace-lab-global/open-cognition/sociology/schools';

// Thinker configurations
const thinkers = [
  {
    id: 'marx',
    school: 'classical',
    name: 'marx',
    title: '马克思 · Karl Marx',
    birth: 1818,
    death: 1883,
    concepts: ['historical-materialism', 'class-struggle', 'alienation', 'surplus-value', 'base-superstructure']
  },
  {
    id: 'weber',
    school: 'classical',
    name: 'weber',
    title: '韦伯 · Max Weber',
    birth: 1864,
    death: 1920,
    concepts: ['rationalization', 'iron-cage', 'protestant-ethic', 'ideal-type', 'authority-types']
  },
  {
    id: 'durkheim',
    school: 'classical',
    name: 'durkheim',
    title: '涂尔干 · Émile Durkheim',
    birth: 1858,
    death: 1917,
    concepts: ['social-facts', 'solidarity', 'anomie', 'collective-consciousness', 'suicide-types']
  },
  {
    id: 'simmel',
    school: 'classical',
    name: 'simmel',
    title: '齐美尔 · Georg Simmel',
    birth: 1858,
    death: 1918,
    concepts: ['stranger', 'metropolis-mental-life', 'fashion', 'social-forms', 'tragedy-of-culture']
  },
  {
    id: 'mills',
    school: 'classical',
    name: 'mills',
    title: '米尔斯 · C. Wright Mills',
    birth: 1916,
    death: 1962,
    concepts: ['sociological-imagination', 'power-elite', 'white-collar', 'cheerfulness-trap', 'promise']
  },
  {
    id: 'bourdieu',
    school: 'structuralism',
    name: 'bourdieu',
    title: '布迪厄 · Pierre Bourdieu',
    birth: 1930,
    death: 2002,
    concepts: ['habitus', 'field', 'cultural-capital', 'symbolic-violence', 'distinction']
  },
  {
    id: 'foucault',
    school: 'structuralism',
    name: 'foucault',
    title: '福柯 · Michel Foucault',
    birth: 1926,
    death: 1984,
    concepts: ['power-knowledge', 'panopticon', 'discourse', 'biopolitics', 'governmentality']
  },
  {
    id: 'habermas',
    school: 'critical',
    name: 'habermas',
    title: '哈贝马斯 · Jürgen Habermas',
    birth: 1929,
    concepts: ['communicative-action', 'public-sphere', 'lifeworld-system', 'discourse-ethics', 'rationality']
  },
  {
    id: 'giddens',
    school: 'structuration',
    name: 'giddens',
    title: '吉登斯 · Anthony Giddens',
    birth: 1938,
    death: 2024,
    concepts: ['structuration', 'reflexivity', 'modernity-consequences', 'duality-of-structure', 'ontological-security']
  },
  {
    id: 'butler',
    school: 'gender-studies',
    name: 'butler',
    title: '巴特勒 · Judith Butler',
    birth: 1956,
    concepts: ['gender-performativity', 'queer-theory', 'precarity', 'bodies-that-matter', 'subversion']
  },
  {
    id: 'goffman',
    school: 'interactionism',
    name: 'goffman',
    title: '戈夫曼 · Erving Goffman',
    birth: 1922,
    death: 1982,
    concepts: ['dramaturgy', 'impression-management', 'total-institution', 'stigma', 'frame-analysis']
  },
  {
    id: 'elias',
    school: 'figurational',
    name: 'elias',
    title: '埃利亚斯 · Norbert Elias',
    birth: 1897,
    death: 1990,
    concepts: ['civilizing-process', 'figuration', 'established-outsiders', 'court-society', 'shame-threshold']
  },
  {
    id: 'latour',
    school: 'actor-network',
    name: 'latour',
    title: '拉图尔 · Bruno Latour',
    birth: 1947,
    death: 2022,
    concepts: ['actor-network-theory', 'black-box', 'quasi-objects', 'immutable-mobiles', 'parliament-of-things']
  },
  {
    id: 'parsons',
    school: 'functionalism',
    name: 'parsons',
    title: '帕森斯 · Talcott Parsons',
    birth: 1902,
    death: 1979,
    concepts: ['social-system', 'pattern-variables', 'agil-schema', 'sick-role', 'structural-functionalism']
  },
  {
    id: 'bauman',
    school: 'modernity',
    name: 'bauman',
    title: '鲍曼 · Zygmunt Bauman',
    birth: 1925,
    death: 2017,
    concepts: ['liquid-modernity', 'holocaust-modernity', 'consumerism', 'stranger', 'wasted-lives']
  },
  {
    id: 'beck',
    school: 'modernity',
    name: 'beck',
    title: '贝克 · Ulrich Beck',
    birth: 1944,
    death: 2015,
    concepts: ['risk-society', 'individualization', 'reflexive-modernization', 'second-modernity', 'subpolitics']
  },
  {
    id: 'castells',
    school: 'network-society',
    name: 'castells',
    title: '卡斯特 · Manuel Castells',
    birth: 1942,
    concepts: ['network-society', 'space-of-flows', 'informational-city', 'identity-power', 'digital-divide']
  },
  {
    id: 'du-bois',
    school: 'race-studies',
    name: 'du-bois',
    title: '杜波依斯 · W.E.B. Du Bois',
    birth: 1868,
    death: 1963,
    concepts: ['double-consciousness', 'color-line', 'veil', 'talented-tenth', 'souls-of-black-folk']
  }
];

console.log('Expanding 18 sociology thinkers into complete subfolder structures...');
console.log(`Base directory: ${BASE}\n`);

let successCount = 0;
let errorCount = 0;

for (const thinker of thinkers) {
  const thinkerDir = join(BASE, thinker.school, thinker.name);

  try {
    // Create directories
    mkdirSync(join(thinkerDir, 'concepts'), { recursive: true });

    // Read existing file
    const existingFile = join(BASE, thinker.school, `${thinker.name}.md`);
    const existingContent = readFileSync(existingFile, 'utf-8');

    // Create pointer redirect
    const pointerContent = `---
id: ${thinker.id}
title: ${thinker.title}
type: thinker
redirect: ${thinker.name}/README.md
---

# ${thinker.title}

> 本条目已展开为完整子目录：[${thinker.name}/README.md](${thinker.name}/README.md)
`;

    writeFileSync(existingFile, pointerContent, 'utf-8');

    console.log(`✓ ${thinker.title}`);
    successCount++;
  } catch (error) {
    console.error(`✗ ${thinker.title}: ${error.message}`);
    errorCount++;
  }
}

console.log(`\nCompleted: ${successCount} successful, ${errorCount} errors`);
