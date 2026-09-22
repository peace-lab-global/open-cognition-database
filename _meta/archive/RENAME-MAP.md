# 重命名映射表 · Rename Map

> 本文件记录从 main 分支到 rename-to-chinese 分支的全部路径变更, 便于回查旧 URL / 旧引用。
> 自动生成自 `git diff --name-status --diff-filter=R main..HEAD`, 共 **2366** 次重命名。

---

## 命名约定

| 层级 | 规则 | 示例 |
|---|---|---|
| 顶层领域 | 学科中文简称 (2-4 字) | `philosophy/` → `哲学/` |
| 二级目录 | 概念/学派/技能/传统/大师 等类型名 | `concepts/` → `概念/` |
| 学派子目录 | 学派中文简称 | `analytic/` → `分析哲学/` |
| 思想家目录 | frontmatter title 中文部分 | `kant/` → `康德/` |
| 概念文件 | frontmatter title 中文部分 + `.md` | `辩证法.md` → `辩证法.md` |
| 技能目录 | SKILL.md description 首个中文短语 | `cbt-cognitive-distortion/` → `认知扭曲识别/` |

## 保留英文 (不改名)

- 根文档: `AGENT.md`, `README.md`, `INDEX.md`, `TAGS.md`, `CONTRIBUTING.md`
- `_meta/` 元数据目录 (工具脚本、审计报告、模板)
- 各条目内的附属文件: `README.md`, `INDEX.md`, `SKILL.md`, `QUICKSTART.md`

---

## 顶层领域 (10)

| 旧路径 | → | 新路径 |
|---|---|---|
| `ethics-politics/README.md` | → | `伦理政治/README.md` |
| `philosophy/README.md` | → | `哲学/README.md` |
| `religion/README.md` | → | `宗教/README.md` |
| `psychology/README.md` | → | `心理学/README.md` |
| `literature/README.md` | → | `文学/README.md` |
| `research/README.md` | → | `研究/README.md` |
| `sociology/README.md` | → | `社会学/README.md` |
| `aesthetics/README.md` | → | `美学/README.md` |
| `arts/README.md` | → | `艺术/README.md` |
| `cognitive-systems/README.md` | → | `认知系统/README.md` |

## 思想家目录与 stub (214)

| 旧路径 | → | 新路径 |
|---|---|---|
| `ethics-politics/schools/care-ethics/noddings.md` | → | `伦理政治/学派/关怀伦理学/内尔.md` |
| `ethics-politics/schools/virtue-ethics/亚里士多德.md` | → | `伦理政治/学派/德性伦理学/亚里士多德.md` |
| `ethics-politics/schools/virtue-ethics/macintyre.md` | → | `伦理政治/学派/德性伦理学/阿拉斯戴尔.md` |
| `ethics-politics/schools/critical-theory/marcuse.md` | → | `伦理政治/学派/批判理论/赫伯特.md` |
| `ethics-politics/schools/social-contract/hobbes.md` | → | `伦理政治/学派/社会契约论/托马斯.md` |
| `ethics-politics/学派/社会契约论/约翰-rawls.md` | → | `伦理政治/学派/社会契约论/约翰-rawls.md` |
| `ethics-politics/schools/social-contract/约翰.md` | → | `伦理政治/学派/社会契约论/约翰.md` |
| `ethics-politics/schools/communitarianism/taylor.md` | → | `伦理政治/学派/社群主义/查尔斯.md` |
| `ethics-politics/schools/consequentialism/密尔.md` | → | `伦理政治/学派/结果主义/密尔.md` |
| `ethics-politics/schools/consequentialism/bentham.md` | → | `伦理政治/学派/结果主义/边沁.md` |
| `ethics-politics/schools/capability-approach/sen.md` | → | `伦理政治/学派/能力方法/森.md` |
| `ethics-politics/schools/capability-approach/nussbaum.md` | → | `伦理政治/学派/能力方法/纳斯鲍姆.md` |
| `ethics-politics/schools/libertarianism/nozick.md` | → | `伦理政治/学派/自由至上主义/罗伯特.md` |
| `ethics-politics/schools/deontology/康德.md` | → | `伦理政治/学派/道义论/康德.md` |
| `ethics-politics/schools/nonviolent-resistance/gandhi.md` | → | `伦理政治/学派/非暴力抵抗/圣雄甘地.md` |
| `philosophy/schools/eastern/confucius.md` | → | `哲学/学派/东方哲学/孔子.md` |
| `philosophy/schools/eastern/zhuangzi.md` | → | `哲学/学派/东方哲学/庄子.md` |
| `philosophy/schools/eastern/laozi.md` | → | `哲学/学派/东方哲学/老子.md` |
| `philosophy/schools/medieval-scholastic/aquinas.md` | → | `哲学/学派/中世纪经院/托马斯.md` |
| `philosophy/schools/medieval-scholastic/scotus.md` | → | `哲学/学派/中世纪经院/邓斯.md` |
| `philosophy/schools/analytic/dennett.md` | → | `哲学/学派/分析哲学/丹尼特.md` |
| `philosophy/schools/analytic/russell.md` | → | `哲学/学派/分析哲学/伯特兰.md` |
| `philosophy/schools/analytic/clark.md` | → | `哲学/学派/分析哲学/克拉克.md` |
| `philosophy/schools/analytic/nagel.md` | → | `哲学/学派/分析哲学/内格尔.md` |
| `philosophy/schools/analytic/carnap.md` | → | `哲学/学派/分析哲学/卡尔纳普.md` |
| `philosophy/schools/analytic/parfit.md` | → | `哲学/学派/分析哲学/帕菲特.md` |
| `philosophy/schools/analytic/whitehead.md` | → | `哲学/学派/分析哲学/怀特海.md` |
| `philosophy/schools/analytic/popper.md` | → | `哲学/学派/分析哲学/波普尔.md` |
| `philosophy/schools/analytic/fodor.md` | → | `哲学/学派/分析哲学/福多.md` |
| `philosophy/schools/analytic/维特根斯坦.md` | → | `哲学/学派/分析哲学/维特根斯坦.md` |
| `philosophy/schools/analytic/hohwy.md` | → | `哲学/学派/分析哲学/霍维.md` |
| `philosophy/schools/analytic/mcginn.md` | → | `哲学/学派/分析哲学/麦金.md` |
| `philosophy/古希腊/亚里士多德.md` | → | `哲学/学派/古希腊/亚里士多德.md` |
| `philosophy/schools/古希腊/柏拉图.md` | → | `哲学/学派/古希腊/柏拉图.md` |
| `philosophy/schools/ancient-greek/socrates.md` | → | `哲学/学派/古希腊/苏格拉底.md` |
| `philosophy/schools/post-structuralism/derrida.md` | → | `哲学/学派/后结构主义/雅克.md` |
| `philosophy/schools/enlightenment/rousseau.md` | → | `哲学/学派/启蒙运动/让雅克.md` |
| `哲学/学派/存在主义/尼采.md` | → | `哲学/学派/存在主义/尼采.md` |
| `philosophy/schools/存在主义/海德格尔.md` | → | `哲学/学派/存在主义/海德格尔.md` |
| `philosophy/schools/existentialism/kierkegaard.md` | → | `哲学/学派/存在主义/索伦.md` |
| `philosophy/schools/存在主义/萨特.md` | → | `哲学/学派/存在主义/萨特.md` |
| `philosophy/schools/existentialism/beauvoir.md` | → | `哲学/学派/存在主义/西蒙娜.md` |
| `philosophy/schools/pragmatism/peirce.md` | → | `哲学/学派/实用主义/皮尔士.md` |
| `philosophy/schools/pragmatism/dewey.md` | → | `哲学/学派/实用主义/约翰.md` |
| `philosophy/德国唯心论/康德.md` | → | `哲学/学派/德国唯心论/康德.md` |
| `philosophy/schools/german-idealism/黑格尔.md` | → | `哲学/学派/德国唯心论/黑格尔.md` |
| `philosophy/schools/pessimism/schopenhauer.md` | → | `哲学/学派/悲观主义/亚瑟.md` |
| `philosophy/schools/political-philosophy/arendt.md` | → | `哲学/学派/政治哲学/汉娜.md` |
| `philosophy/schools/comparative/borges-vs-yogacara.md` | → | `哲学/学派/比较哲学/博尔赫斯唯识.md` |
| `philosophy/schools/comparative/existentialism-vs-yogacara.md` | → | `哲学/学派/比较哲学/存在主义唯识.md` |

> *...另有 164 项, 见 git diff 完整记录*

## 概念文件 (978)

| 旧路径 | → | 新路径 |
|---|---|---|
| `ethics-politics/schools/care-ethics/noddings/concepts/ethics-of-care.md` | → | `伦理政治/学派/关怀伦理学/内尔/概念/关怀伦理学.md` |
| `ethics-politics/schools/care-ethics/noddings/concepts/caring-relation.md` | → | `伦理政治/学派/关怀伦理学/内尔/概念/关怀关系.md` |
| `ethics-politics/schools/care-ethics/noddings/concepts/caring-education.md` | → | `伦理政治/学派/关怀伦理学/内尔/概念/关怀教育.md` |
| `ethics-politics/schools/care-ethics/noddings/concepts/maternal-thinking.md` | → | `伦理政治/学派/关怀伦理学/内尔/概念/母性思维.md` |
| `ethics-politics/schools/care-ethics/noddings/concepts/natural-caring.md` | → | `伦理政治/学派/关怀伦理学/内尔/概念/自然关怀.md` |
| `ethics-politics/schools/virtue-ethics/aristotle/concepts/中道.md` | → | `伦理政治/学派/德性伦理学/亚里士多德/概念/中道.md` |
| `ethics-politics/schools/virtue-ethics/aristotle/concepts/four-causes.md` | → | `伦理政治/学派/德性伦理学/亚里士多德/概念/四因说.md` |
| `ethics-politics/schools/virtue-ethics/aristotle/concepts/polis.md` | → | `伦理政治/学派/德性伦理学/亚里士多德/概念/城邦.md` |
| `ethics-politics/schools/virtue-ethics/aristotle/concepts/phronesis.md` | → | `伦理政治/学派/德性伦理学/亚里士多德/概念/实践智慧.md` |
| `ethics-politics/schools/virtue-ethics/aristotle/concepts/幸福论.md` | → | `伦理政治/学派/德性伦理学/亚里士多德/概念/幸福.md` |
| `ethics-politics/schools/virtue-ethics/aristotle/concepts/telos.md` | → | `伦理政治/学派/德性伦理学/亚里士多德/概念/目的.md` |
| `ethics-politics/schools/virtue-ethics/aristotle/concepts/virtue-character.md` | → | `伦理政治/学派/德性伦理学/亚里士多德/概念/美德品格.md` |
| `ethics-politics/schools/virtue-ethics/macintyre/concepts/tradition.md` | → | `伦理政治/学派/德性伦理学/阿拉斯戴尔/概念/传统.md` |
| `ethics-politics/schools/virtue-ethics/macintyre/concepts/tradition-constituted.md` | → | `伦理政治/学派/德性伦理学/阿拉斯戴尔/概念/传统构成的合理性.md` |
| `ethics-politics/schools/virtue-ethics/macintyre/concepts/internal-goods.md` | → | `伦理政治/学派/德性伦理学/阿拉斯戴尔/概念/内在善与外在善.md` |
| `ethics-politics/schools/virtue-ethics/macintyre/concepts/narrative-unity.md` | → | `伦理政治/学派/德性伦理学/阿拉斯戴尔/概念/叙事统一性.md` |
| `ethics-politics/schools/virtue-ethics/macintyre/concepts/practice.md` | → | `伦理政治/学派/德性伦理学/阿拉斯戴尔/概念/实践.md` |
| `ethics-politics/schools/virtue-ethics/macintyre/concepts/practice-narrative.md` | → | `伦理政治/学派/德性伦理学/阿拉斯戴尔/概念/实践与叙事.md` |
| `ethics-politics/schools/virtue-ethics/macintyre/concepts/emotivism.md` | → | `伦理政治/学派/德性伦理学/阿拉斯戴尔/概念/情感主义.md` |
| `ethics-politics/schools/virtue-ethics/macintyre/concepts/emotivism-critique.md` | → | `伦理政治/学派/德性伦理学/阿拉斯戴尔/概念/情感主义批判.md` |
| `ethics-politics/schools/virtue-ethics/macintyre/concepts/after-德性.md` | → | `伦理政治/学派/德性伦理学/阿拉斯戴尔/概念/追寻美德.md` |
| `ethics-politics/schools/critical-theory/marcuse/concepts/one-dimensional-man.md` | → | `伦理政治/学派/批判理论/赫伯特/概念/单向度的人.md` |
| `ethics-politics/schools/critical-theory/marcuse/concepts/repressive-desublimation.md` | → | `伦理政治/学派/批判理论/赫伯特/概念/压抑性脱升华.md` |
| `ethics-politics/schools/critical-theory/marcuse/concepts/great-refusal.md` | → | `伦理政治/学派/批判理论/赫伯特/概念/大拒绝.md` |
| `ethics-politics/schools/critical-theory/marcuse/concepts/technological-rationality.md` | → | `伦理政治/学派/批判理论/赫伯特/概念/技术理性.md` |
| `ethics-politics/schools/critical-theory/marcuse/concepts/liberation.md` | → | `伦理政治/学派/批判理论/赫伯特/概念/解放.md` |
| `ethics-politics/schools/social-contract/hobbes/concepts/bellum-omnium.md` | → | `伦理政治/学派/社会契约论/托马斯/概念/一切人反对一切人的战争.md` |
| `ethics-politics/schools/social-contract/hobbes/concepts/sovereignty.md` | → | `伦理政治/学派/社会契约论/托马斯/概念/主权.md` |
| `ethics-politics/schools/social-contract/hobbes/concepts/leviathan.md` | → | `伦理政治/学派/社会契约论/托马斯/概念/利维坦.md` |
| `ethics-politics/schools/social-contract/hobbes/concepts/社会契约.md` | → | `伦理政治/学派/社会契约论/托马斯/概念/社会契约.md` |
| `ethics-politics/schools/social-contract/hobbes/concepts/natural-law.md` | → | `伦理政治/学派/社会契约论/托马斯/概念/自然法.md` |
| `ethics-politics/schools/social-contract/hobbes/concepts/state-of-nature.md` | → | `伦理政治/学派/社会契约论/托马斯/概念/自然状态.md` |
| `ethics-politics/schools/social-contract/rawls/concepts/justice-as-fairness.md` | → | `伦理政治/学派/社会契约论/约翰-rawls/概念/作为公平的正义.md` |
| `ethics-politics/schools/social-contract/rawls/concepts/original-position.md` | → | `伦理政治/学派/社会契约论/约翰-rawls/概念/原初状态.md` |
| `ethics-politics/schools/social-contract/rawls/concepts/reflective-equilibrium.md` | → | `伦理政治/学派/社会契约论/约翰-rawls/概念/反思平衡.md` |
| `ethics-politics/schools/social-contract/rawls/concepts/difference-principle.md` | → | `伦理政治/学派/社会契约论/约翰-rawls/概念/差别原则.md` |
| `ethics-politics/schools/social-contract/rawls/concepts/无知之幕.md` | → | `伦理政治/学派/社会契约论/约翰-rawls/概念/无知之幕.md` |
| `ethics-politics/schools/social-contract/rawls/concepts/overlapping-consensus.md` | → | `伦理政治/学派/社会契约论/约翰-rawls/概念/重叠共识.md` |
| `ethics-politics/schools/social-contract/locke/concepts/government-consent.md` | → | `伦理政治/学派/社会契约论/约翰/概念/基于同意的政府.md` |
| `ethics-politics/schools/social-contract/locke/concepts/toleration.md` | → | `伦理政治/学派/社会契约论/约翰/概念/宗教宽容.md` |
| `ethics-politics/schools/social-contract/locke/concepts/tabula-rasa.md` | → | `伦理政治/学派/社会契约论/约翰/概念/白板论.md` |
| `ethics-politics/schools/social-contract/locke/concepts/natural-rights.md` | → | `伦理政治/学派/社会契约论/约翰/概念/自然权利.md` |
| `ethics-politics/schools/social-contract/locke/concepts/property-labor.md` | → | `伦理政治/学派/社会契约论/约翰/概念/财产权劳动论.md` |
| `ethics-politics/schools/communitarianism/taylor/concepts/secular-age.md` | → | `伦理政治/学派/社群主义/查尔斯/概念/世俗时代.md` |
| `ethics-politics/schools/communitarianism/taylor/concepts/politics-of-recognition.md` | → | `伦理政治/学派/社群主义/查尔斯/概念/承认的政治.md` |
| `ethics-politics/schools/communitarianism/taylor/concepts/authenticity-ethics.md` | → | `伦理政治/学派/社群主义/查尔斯/概念/本真性伦理.md` |
| `ethics-politics/schools/communitarianism/taylor/concepts/social-imaginary.md` | → | `伦理政治/学派/社群主义/查尔斯/概念/社会想象.md` |
| `ethics-politics/schools/communitarianism/taylor/concepts/sources-of-self.md` | → | `伦理政治/学派/社群主义/查尔斯/概念/自我的根源.md` |
| `ethics-politics/schools/consequentialism/mill/concepts/harm-principle.md` | → | `伦理政治/学派/结果主义/密尔/概念/伤害原则.md` |
| `ethics-politics/schools/consequentialism/mill/concepts/tyranny-of-majority.md` | → | `伦理政治/学派/结果主义/密尔/概念/多数暴政.md` |

> *...另有 928 项, 见 git diff 完整记录*

## 技能目录 (137)

| 旧路径 | → | 新路径 |
|---|---|---|
| `ethics-politics/skills/aristotle-virtue-test/SKILL.md` | → | `伦理政治/技能/亚里士多德德性检验性检验/SKILL.md` |
| `ethics-politics/skills/virtue-ethics-analysis/SKILL.md` | → | `伦理政治/技能/德性分析/SKILL.md` |
| `ethics-politics/skills/veil-of-ignorance-analysis/SKILL.md` | → | `伦理政治/技能/无知之幕分析/SKILL.md` |
| `ethics-politics/skills/justice-principle-test/SKILL.md` | → | `伦理政治/技能/正义原则检验/SKILL.md` |
| `ethics-politics/skills/capability-approach-analysis/SKILL.md` | → | `伦理政治/技能/能力方法分析/SKILL.md` |
| `ethics-politics/skills/natural-rights-analysis/SKILL.md` | → | `伦理政治/技能/自然权利分析/SKILL.md` |
| `ethics-politics/skills/state-of-nature-analysis/SKILL.md` | → | `伦理政治/技能/自然状态分析/SKILL.md` |
| `ethics-politics/skills/liberalism-analysis/SKILL.md` | → | `伦理政治/技能/自由主义论证/SKILL.md` |
| `ethics-politics/skills/pleasure-calculus/SKILL.md` | → | `伦理政治/技能/苦乐计算法/SKILL.md` |
| `ethics-politics/skills/nonviolent-resistance/SKILL.md` | → | `伦理政治/技能/非暴力抵抗/SKILL.md` |
| `philosophy/skills/east-west-ethics-comparison/SKILL.md` | → | `哲学/技能/东西方伦理对/SKILL.md` |
| `philosophy/skills/golden-mean-analysis/SKILL.md` | → | `哲学/技能/中庸之道分析/SKILL.md` |
| `philosophy/skills/ren-li-analysis/SKILL.md` | → | `哲学/技能/仁礼分析/SKILL.md` |
| `philosophy/skills/reverse-thinking/SKILL.md` | → | `哲学/技能/反向思维/SKILL.md` |
| `philosophy/skills/causation-analysis/SKILL.md` | → | `哲学/技能/因果问题分析/SKILL.md` |
| `philosophy/skills/existentialism-analysis/SKILL.md` | → | `哲学/技能/存在主义分析/SKILL.md` |
| `philosophy/skills/pragmatism-analysis/SKILL.md` | → | `哲学/技能/实用主义分析/SKILL.md` |
| `philosophy/skills/methodological-doubt/SKILL.md` | → | `哲学/技能/方法论怀疑/SKILL.md` |
| `philosophy/skills/uselessness-paradox/SKILL.md` | → | `哲学/技能/无用之用悖论/SKILL.md` |
| `philosophy/skills/will-to-power-analysis/SKILL.md` | → | `哲学/技能/权力意志分析/SKILL.md` |
| `philosophy/skills/dasein-analysis/SKILL.md` | → | `哲学/技能/此在分析/SKILL.md` |
| `philosophy/skills/allegory-of-cave-analysis/SKILL.md` | → | `哲学/技能/洞穴寓言分析/SKILL.md` |
| `philosophy/skills/phenomenological-reduction/SKILL.md` | → | `哲学/技能/现象学还原/SKILL.md` |
| `philosophy/skills/social-contract-analysis/SKILL.md` | → | `哲学/技能/社会契约分析/SKILL.md` |
| `philosophy/skills/categorical-imperative-test/SKILL.md` | → | `哲学/技能/绝对命令检验/SKILL.md` |
| `philosophy/skills/socratic-questioning/SKILL.md` | → | `哲学/技能/苏格拉底式诘/SKILL.md` |
| `philosophy/skills/language-game-analysis/SKILL.md` | → | `哲学/技能/语言游戏分析/SKILL.md` |
| `philosophy/skills/dialectical-analysis/SKILL.md` | → | `哲学/技能/辩证法分析/SKILL.md` |
| `philosophy/skills/qiwu-analysis/SKILL.md` | → | `哲学/技能/齐物论分析/SKILL.md` |
| `religion/buddhism/skills/qichu-zhengxin-deconstruction/SKILL.md` | → | `宗教/佛教/技能/七处征心/SKILL.md` |
| `religion/buddhism/skills/madhyamaka-four-fallacies/SKILL.md` | → | `宗教/佛教/技能/中观四句破/SKILL.md` |
| `religion/buddhism/skills/eight-consciousness-diagnosis/SKILL.md` | → | `宗教/佛教/技能/从前五识/SKILL.md` |
| `religion/buddhism/skills/five-aggregates-deconstruction/SKILL.md` | → | `宗教/佛教/技能/以五蕴/SKILL.md` |
| `religion/buddhism/skills/two-truths-reframing/SKILL.md` | → | `宗教/佛教/技能/以佛教二谛/SKILL.md` |
| `religion/buddhism/skills/pramana-validation/SKILL.md` | → | `宗教/佛教/技能/以佛教量论/SKILL.md` |
| `religion/buddhism/skills/three-natures-diagnosis/SKILL.md` | → | `宗教/佛教/技能/以唯识三性/SKILL.md` |
| `religion/buddhism/skills/baihuan-bianjian-naming/SKILL.md` | → | `宗教/佛教/技能/八还辨见/SKILL.md` |
| `religion/buddhism/skills/bija-pattern-analysis/SKILL.md` | → | `宗教/佛教/技能/后的种子类型/SKILL.md` |
| `religion/buddhism/skills/dependent-origination-tracing/SKILL.md` | → | `宗教/佛教/技能/定位关键断点/SKILL.md` |
| `religion/buddhism/skills/abhidharma-mind-mapping/SKILL.md` | → | `宗教/佛教/技能/心所正在主导/SKILL.md` |
| `religion/buddhism/skills/six-constituents-diagnosis/SKILL.md` | → | `宗教/佛教/技能/认知卡点在根/SKILL.md` |
| `religion/buddhism/skills/consciousness-transformation-diagnosis/SKILL.md` | → | `宗教/佛教/技能/转识成智诊断/SKILL.md` |
| `religion/buddhism/skills/mind-world-analysis/SKILL.md` | → | `宗教/佛教/技能/通过四分结构/SKILL.md` |
| `religion/buddhism/skills/diamond-sutra-no-dwelling/SKILL.md` | → | `宗教/佛教/技能/金刚经/SKILL.md` |
| `religion/skills/five-aggregates-contemplation/SKILL.md` | → | `宗教/技能/五蕴观/SKILL.md` |
| `religion/skills/buddhism-taoism-dialogue/SKILL.md` | → | `宗教/技能/佛教道教对话/SKILL.md` |
| `religion/skills/koan-practice/SKILL.md` | → | `宗教/技能/公案参究法/SKILL.md` |
| `religion/skills/twelve-links-contemplation/SKILL.md` | → | `宗教/技能/十二因缘观/SKILL.md` |
| `religion/skills/four-noble-truths-framework/SKILL.md` | → | `宗教/技能/四圣谛框架分/SKILL.md` |
| `religion/skills/biguan-meditation/SKILL.md` | → | `宗教/技能/壁观禅修引导/SKILL.md` |

> *...另有 87 项, 见 git diff 完整记录*

## 传统与智慧大师 (17)

| 旧路径 | → | 新路径 |
|---|---|---|
| `religion/traditions/islam/五功.md` | → | `宗教/传统/伊斯兰教/五功.md` |
| `religion/traditions/islam/苏菲主义.md` | → | `宗教/传统/伊斯兰教/苏菲主义.md` |
| `religion/传统/佛教/四圣谛与八正道.md` | → | `宗教/传统/佛教/四圣谛与八正道.md` |
| `religion/传统/佛教/大乘空性.md` | → | `宗教/传统/佛教/大乘空性.md` |
| `religion/traditions/buddhism/amitabha-pure-land.md` | → | `宗教/传统/佛教/弥陀净土.md` |
| `religion/传统/佛教/禅宗.md` | → | `宗教/传统/佛教/禅宗.md` |
| `religion/traditions/confucianism/religion-dimension.md` | → | `宗教/传统/儒教/儒教的宗教维度.md` |
| `religion/traditions/hinduism/karma-samsara.md` | → | `宗教/传统/印度教/业与轮回.md` |
| `religion/traditions/christianity/mysticism.md` | → | `宗教/传统/基督教/基督教神秘主义.md` |
| `religion/传统/基督教/恩典与救赎.md` | → | `宗教/传统/基督教/恩典与救赎.md` |
| `religion/traditions/judaism/covenant.md` | → | `宗教/传统/犹太教/律法与盟约.md` |
| `religion/traditions/judaism/kabbalah.md` | → | `宗教/传统/犹太教/犹太教卡巴拉神秘主义.md` |
| `religion/traditions/shinto/core-teachings.md` | → | `宗教/传统/神道教/神道教核心教义.md` |
| `religion/traditions/taoism/masters/zhuangzi.md` | → | `宗教/传统/道教/masters/庄子.md` |
| `religion/传统/道教/masters/老子.md` | → | `宗教/传统/道教/masters/老子.md` |
| `religion/traditions/taoism/无为.md` | → | `宗教/传统/道教/无为.md` |
| `religion/traditions/sikhism/core-teachings.md` | → | `宗教/传统/锡克教/锡克教核心教义.md` |

## 附属文件 (reading-list/timeline/works) (921)

| 旧路径 | → | 新路径 |
|---|---|---|
| `ethics-politics/schools/care-ethics/noddings/README.md` | → | `伦理政治/学派/关怀伦理学/内尔/README.md` |
| `ethics-politics/schools/care-ethics/noddings/时间线.md` | → | `伦理政治/学派/关怀伦理学/内尔/时间线.md` |
| `ethics-politics/schools/care-ethics/noddings/著作.md` | → | `伦理政治/学派/关怀伦理学/内尔/著作.md` |
| `ethics-politics/schools/care-ethics/noddings/阅读.md` | → | `伦理政治/学派/关怀伦理学/内尔/阅读.md` |
| `ethics-politics/schools/virtue-ethics/aristotle/README.md` | → | `伦理政治/学派/德性伦理学/亚里士多德/README.md` |
| `ethics-politics/schools/virtue-ethics/aristotle/时间线.md` | → | `伦理政治/学派/德性伦理学/亚里士多德/时间线.md` |
| `ethics-politics/schools/virtue-ethics/aristotle/著作.md` | → | `伦理政治/学派/德性伦理学/亚里士多德/著作.md` |
| `ethics-politics/schools/virtue-ethics/aristotle/阅读.md` | → | `伦理政治/学派/德性伦理学/亚里士多德/阅读.md` |
| `ethics-politics/schools/virtue-ethics/macintyre/README.md` | → | `伦理政治/学派/德性伦理学/阿拉斯戴尔/README.md` |
| `ethics-politics/schools/virtue-ethics/macintyre/时间线.md` | → | `伦理政治/学派/德性伦理学/阿拉斯戴尔/时间线.md` |
| `ethics-politics/schools/virtue-ethics/macintyre/著作.md` | → | `伦理政治/学派/德性伦理学/阿拉斯戴尔/著作.md` |
| `ethics-politics/schools/virtue-ethics/macintyre/阅读.md` | → | `伦理政治/学派/德性伦理学/阿拉斯戴尔/阅读.md` |
| `ethics-politics/schools/critical-theory/marcuse/README.md` | → | `伦理政治/学派/批判理论/赫伯特/README.md` |
| `ethics-politics/schools/critical-theory/marcuse/时间线.md` | → | `伦理政治/学派/批判理论/赫伯特/时间线.md` |
| `ethics-politics/schools/critical-theory/marcuse/著作.md` | → | `伦理政治/学派/批判理论/赫伯特/著作.md` |
| `ethics-politics/schools/critical-theory/marcuse/阅读.md` | → | `伦理政治/学派/批判理论/赫伯特/阅读.md` |
| `ethics-politics/schools/social-contract/hobbes/README.md` | → | `伦理政治/学派/社会契约论/托马斯/README.md` |
| `ethics-politics/schools/social-contract/hobbes/时间线.md` | → | `伦理政治/学派/社会契约论/托马斯/时间线.md` |
| `ethics-politics/schools/social-contract/hobbes/著作.md` | → | `伦理政治/学派/社会契约论/托马斯/著作.md` |
| `ethics-politics/schools/social-contract/hobbes/阅读.md` | → | `伦理政治/学派/社会契约论/托马斯/阅读.md` |
| `ethics-politics/schools/social-contract/rawls/README.md` | → | `伦理政治/学派/社会契约论/约翰-rawls/README.md` |
| `ethics-politics/schools/social-contract/rawls/时间线.md` | → | `伦理政治/学派/社会契约论/约翰-rawls/时间线.md` |
| `ethics-politics/schools/social-contract/rawls/著作.md` | → | `伦理政治/学派/社会契约论/约翰-rawls/著作.md` |
| `ethics-politics/schools/social-contract/rawls/阅读.md` | → | `伦理政治/学派/社会契约论/约翰-rawls/阅读.md` |
| `ethics-politics/schools/social-contract/locke/README.md` | → | `伦理政治/学派/社会契约论/约翰/README.md` |
| `ethics-politics/schools/social-contract/locke/时间线.md` | → | `伦理政治/学派/社会契约论/约翰/时间线.md` |
| `ethics-politics/schools/social-contract/locke/著作.md` | → | `伦理政治/学派/社会契约论/约翰/著作.md` |
| `ethics-politics/schools/social-contract/locke/阅读.md` | → | `伦理政治/学派/社会契约论/约翰/阅读.md` |
| `ethics-politics/schools/communitarianism/taylor/README.md` | → | `伦理政治/学派/社群主义/查尔斯/README.md` |
| `ethics-politics/schools/communitarianism/taylor/时间线.md` | → | `伦理政治/学派/社群主义/查尔斯/时间线.md` |
| `ethics-politics/schools/communitarianism/taylor/著作.md` | → | `伦理政治/学派/社群主义/查尔斯/著作.md` |
| `ethics-politics/schools/communitarianism/taylor/阅读.md` | → | `伦理政治/学派/社群主义/查尔斯/阅读.md` |
| `ethics-politics/schools/consequentialism/mill/README.md` | → | `伦理政治/学派/结果主义/密尔/README.md` |
| `ethics-politics/schools/consequentialism/mill/时间线.md` | → | `伦理政治/学派/结果主义/密尔/时间线.md` |
| `ethics-politics/schools/consequentialism/mill/著作.md` | → | `伦理政治/学派/结果主义/密尔/著作.md` |
| `ethics-politics/schools/consequentialism/mill/阅读.md` | → | `伦理政治/学派/结果主义/密尔/阅读.md` |
| `ethics-politics/schools/consequentialism/bentham/README.md` | → | `伦理政治/学派/结果主义/边沁/README.md` |
| `ethics-politics/schools/consequentialism/bentham/时间线.md` | → | `伦理政治/学派/结果主义/边沁/时间线.md` |
| `ethics-politics/schools/consequentialism/bentham/著作.md` | → | `伦理政治/学派/结果主义/边沁/著作.md` |
| `ethics-politics/schools/consequentialism/bentham/阅读.md` | → | `伦理政治/学派/结果主义/边沁/阅读.md` |
| `ethics-politics/schools/capability-approach/sen/README.md` | → | `伦理政治/学派/能力方法/森/README.md` |
| `ethics-politics/schools/capability-approach/sen/时间线.md` | → | `伦理政治/学派/能力方法/森/时间线.md` |
| `ethics-politics/schools/capability-approach/sen/著作.md` | → | `伦理政治/学派/能力方法/森/著作.md` |
| `ethics-politics/schools/capability-approach/sen/阅读.md` | → | `伦理政治/学派/能力方法/森/阅读.md` |
| `ethics-politics/schools/capability-approach/nussbaum/README.md` | → | `伦理政治/学派/能力方法/纳斯鲍姆/README.md` |
| `ethics-politics/schools/capability-approach/nussbaum/时间线.md` | → | `伦理政治/学派/能力方法/纳斯鲍姆/时间线.md` |
| `ethics-politics/schools/capability-approach/nussbaum/著作.md` | → | `伦理政治/学派/能力方法/纳斯鲍姆/著作.md` |
| `ethics-politics/schools/capability-approach/nussbaum/阅读.md` | → | `伦理政治/学派/能力方法/纳斯鲍姆/阅读.md` |
| `ethics-politics/schools/libertarianism/nozick/README.md` | → | `伦理政治/学派/自由至上主义/罗伯特/README.md` |
| `ethics-politics/schools/libertarianism/nozick/时间线.md` | → | `伦理政治/学派/自由至上主义/罗伯特/时间线.md` |

> *...另有 871 项, 见 git diff 完整记录*

## 佛经文件 (21)

| 旧路径 | → | 新路径 |
|---|---|---|
| `religion/buddhism/sutras/README.md` | → | `宗教/佛教/经典/README.md` |
| `religion/buddhism/sutras/reports/sutras-audit-report.md` | → | `宗教/佛教/经典/reports/经典审计报告.md` |
| `religion/buddhism/sutras/amitayus-sutra.md` | → | `宗教/佛教/经典/佛说无量寿经.md` |
| `religion/buddhism/sutras/contemplation-sutra.md` | → | `宗教/佛教/经典/佛说观无量寿佛经.md` |
| `religion/buddhism/sutras/amitabha-sutra.md` | → | `宗教/佛教/经典/佛说阿弥陀经.md` |
| `religion/buddhism/sutras/platform-sutra.md` | → | `宗教/佛教/经典/六祖坛经.md` |
| `religion/buddhism/sutras/forty-two-sections.md` | → | `宗教/佛教/经典/四十二章经.md` |
| `religion/buddhism/sutras/ksitigarbha-sutra.md` | → | `宗教/佛教/经典/地藏菩萨本愿经.md` |
| `religion/buddhism/sutras/surangama-sutra.md` | → | `宗教/佛教/经典/大佛顶首楞严经-surangama-sutra.md` |
| `religion/buddhism/sutras/surangama-sutra-alt.md` | → | `宗教/佛教/经典/大佛顶首楞严经.md` |
| `religion/buddhism/sutras/华严经.md` | → | `宗教/佛教/经典/大方广佛华严经.md` |
| `religion/buddhism/sutras/perfect-enlightenment-sutra.md` | → | `宗教/佛教/经典/大方广圆觉修多罗了义经.md` |
| `religion/buddhism/sutras/mahaparinirvana-sutra.md` | → | `宗教/佛教/经典/大般涅槃经.md` |
| `religion/buddhism/sutras/妙法莲华经.md` | → | `宗教/佛教/经典/妙法莲华经.md` |
| `religion/buddhism/sutras/brahmajala-sutra.md` | → | `宗教/佛教/经典/梵网经菩萨戒本.md` |
| `religion/buddhism/sutras/lankavatara-sutra.md` | → | `宗教/佛教/经典/楞伽阿跋多罗宝经.md` |
| `religion/buddhism/sutras/vimalakirti-sutra.md` | → | `宗教/佛教/经典/维摩诘所说经.md` |
| `religion/buddhism/sutras/heart-sutra.md` | → | `宗教/佛教/经典/般若波罗蜜多心经.md` |
| `religion/buddhism/sutras/bhaisajyaguru-sutra.md` | → | `宗教/佛教/经典/药师琉璃光如来本愿功德经.md` |
| `religion/buddhism/sutras/sandhinirmocana-sutra.md` | → | `宗教/佛教/经典/解深密经.md` |
| `religion/buddhism/sutras/diamond-sutra.md` | → | `宗教/佛教/经典/金刚般若波罗蜜经.md` |

## 其他 (68)

| 旧路径 | → | 新路径 |
|---|---|---|
| `religion/buddhism/INDEX.md` | → | `宗教/佛教/INDEX.md` |
| `religion/buddhism/masters/sengzhao.md` | → | `宗教/佛教/大师/僧肇.md` |
| `religion/buddhism/masters/yinguang.md` | → | `宗教/佛教/大师/印光.md` |
| `religion/buddhism/masters/jizang.md` | → | `宗教/佛教/大师/吉藏.md` |
| `religion/buddhism/masters/shandao.md` | → | `宗教/佛教/大师/善导.md` |
| `religion/buddhism/masters/taixu.md` | → | `宗教/佛教/大师/太虚.md` |
| `religion/buddhism/masters/tsongkhapa.md` | → | `宗教/佛教/大师/宗喀巴.md` |
| `religion/buddhism/masters/santideva.md` | → | `宗教/佛教/大师/寂天.md` |
| `religion/buddhism/masters/milarepa.md` | → | `宗教/佛教/大师/密勒日巴.md` |
| `religion/buddhism/masters/huineng.md` | → | `宗教/佛教/大师/慧能.md` |
| `religion/buddhism/masters/huiyuan.md` | → | `宗教/佛教/大师/慧远.md` |
| `religion/buddhism/masters/aryadeva.md` | → | `宗教/佛教/大师/提婆.md` |
| `religion/buddhism/masters/asanga-vasubandhu.md` | → | `宗教/佛教/大师/无著.md` |
| `religion/buddhism/masters/zhiyi.md` | → | `宗教/佛教/大师/智顗.md` |
| `religion/buddhism/masters/candrakirti.md` | → | `宗教/佛教/大师/月称.md` |
| `religion/buddhism/masters/faxian.md` | → | `宗教/佛教/大师/法显.md` |
| `religion/buddhism/masters/dharmakirti.md` | → | `宗教/佛教/大师/法称.md` |
| `religion/buddhism/masters/fazang.md` | → | `宗教/佛教/大师/法藏.md` |
| `religion/buddhism/masters/hakuin.md` | → | `宗教/佛教/大师/白隐慧鹤.md` |
| `"religion/buddhism/masters/hakuin/concepts/gozen-ho\346\202\237after-practice.md"` | → | `宗教/佛教/大师/白隐慧鹤/概念/gozen-ho悟after-practice.md` |
| `religion/buddhism/masters/paramartha.md` | → | `宗教/佛教/大师/真谛.md` |
| `religion/buddhism/masters/kukai.md` | → | `宗教/佛教/大师/空海.md` |
| `religion/buddhism/masters/窥基.md` | → | `宗教/佛教/大师/窥基.md` |
| `religion/buddhism/masters/yosai.md` | → | `宗教/佛教/大师/荣西.md` |
| `religion/buddhism/masters/padmasambhava.md` | → | `宗教/佛教/大师/莲花生大士.md` |
| `religion/buddhism/masters/bodhidharma.md` | → | `宗教/佛教/大师/菩提达摩.md` |
| `religion/buddhism/masters/道元.md` | → | `宗教/佛教/大师/道元.md` |
| `religion/buddhism/masters/daoxuan.md` | → | `宗教/佛教/大师/道宣.md` |
| `religion/buddhism/masters/atisha.md` | → | `宗教/佛教/大师/阿底峡.md` |
| `religion/buddhism/masters/dignaga.md` | → | `宗教/佛教/大师/陈那.md` |
| `religion/buddhism/masters/longchenpa.md` | → | `宗教/佛教/大师/隆钦巴.md` |
| `religion/buddhism/masters/ashvaghosha.md` | → | `宗教/佛教/大师/马鸣.md` |
| `religion/buddhism/masters/kumarajiva.md` | → | `宗教/佛教/大师/鸠摩罗什.md` |
| `religion/buddhism/大师/龙树.md` | → | `宗教/佛教/大师/龙树.md` |
| `arts/schools/performing-arts/.gitkeep` | → | `宗教/佛教/概念/cognitive-theory/中观/.gitkeep` |
| `religion/buddhism/concepts/cognitive-theory/consciousness-transformation/.gitkeep` | → | `宗教/佛教/概念/cognitive-theory/六根六尘六识/.gitkeep` |
| `religion/buddhism/concepts/cognitive-theory/madhyamaka/.gitkeep` | → | `宗教/佛教/概念/cognitive-theory/心物一元/.gitkeep` |
| `religion/buddhism/concepts/cognitive-theory/mind-world/.gitkeep` | → | `宗教/佛教/概念/cognitive-theory/转识成智/.gitkeep` |
| `religion/buddhism/treatises/mulamadhyamakakarika.md` | → | `宗教/佛教/论典/中论 Mūlamadhyamakakārikā.md` |
| `religion/buddhism/treatises/abhidharmakosa.md` | → | `宗教/佛教/论典/俱舍论 Abhidharmakośa.md` |
| `religion/buddhism/treatises/madhyamakavatara.md` | → | `宗教/佛教/论典/入中论 Madhyamakāvatāra.md` |
| `religion/buddhism/treatises/bodhicaryavatara.md` | → | `宗教/佛教/论典/入菩萨行论 Bodhicaryāvatāra.md` |
| `religion/buddhism/treatises/avatamsaka.md` | → | `宗教/佛教/论典/华严经 Avataṃsaka Sūtra.md` |
| `religion/buddhism/treatises/perfect-启蒙.md` | → | `宗教/佛教/论典/圆觉经 Sūtra of Perfect Enlightenment.md` |
| `religion/buddhism/treatises/awakening-of-faith.md` | → | `宗教/佛教/论典/大乘起信论 Awakening of Faith in Mahāyāna.md` |
| `religion/buddhism/treatises/mahavairocana.md` | → | `宗教/佛教/论典/大日经 Mahāvairocana Sūtra.md` |
| `religion/buddhism/treatises/mahaprajnaparamita-sastra.md` | → | `宗教/佛教/论典/大智度论 Mahāprajñāpāramitā-śāstra.md` |
| `religion/buddhism/treatises/mahapari涅槃.md` | → | `宗教/佛教/论典/大般涅槃经 Mahāparinirvāṇa Sūtra.md` |
| `religion/buddhism/treatises/cheng-weishi-lun.md` | → | `宗教/佛教/论典/成唯识论 Chéng Wéishí Lùn.md` |
| `religion/buddhism/treatises/surangama.md` | → | `宗教/佛教/论典/楞严经 Śūraṅgama Sūtra.md` |

> *...另有 18 项, 见 git diff 完整记录*

