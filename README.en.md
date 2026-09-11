# Open Cognition

> A cross-disciplinary cognitive knowledge base for **human deep reading** and **AI agent consumption**.
> Structured, linkable, and searchable ideas, propositions, and methods from philosophy, religion, sociology, psychology, ethics, aesthetics, literature, arts, and cognitive systems engineering.

[![License: CC BY-SA 4.0](https://img.shields.io/badge/License-CC%20BY--SA%204.0-lightgrey.svg)](./LICENSE)
[![Status](https://img.shields.io/badge/status-v0.9%20buddhist--academy--deep-blue.svg)](#)
[![Domains](https://img.shields.io/badge/domains-9-orange.svg)](#domains)
[![Entries](https://img.shields.io/badge/entries-1027%20thinkers%20%7C%201392%20concepts%20%7C%20137%20skills-brightgreen.svg)](#content-overview)

**Chinese version**: see [README.md](README.md)

---

## Overview

Insights across disciplines are scattered across hard-to-read primary texts and mutually unintelligible schools. This project aims to:

1. **Lower the barrier** -- Build a holistic sense of a thinker or concept through compact ~100-line entries.
2. **Preserve depth** -- No pop-psychology simplifications. Each entry includes primary sources, scholarly references, and introductory readings.
3. **Cross-link disciplines** -- Explicitly annotate relationships: derivation, complementarity, opposition, development, critique, parallel, tension, inheritance, borrowing, and subordination.
4. **Serve AI agents directly** -- Distill standardized **Skills** (operational frameworks) so that LLMs and humans can work from the same knowledge base.
5. **Deep-dive topics** -- Build thematic deep-dives on key axes (e.g., Buddhist cognitive theory) forming sub-systems usable for research, teaching, and practice.

---

## Content Overview

```
9 domains x N thinker/concept entries + Skills + thematic deep-dives
= 1027 thinkers | 1392 concepts | 137 Skills | 2670 indexed entries (see index.json)
```

### Domains

| Domain | Thinkers | Concepts | Skills | Entry point |
|---|:---:|:---:|:---:|---|
| Philosophy | 42 | 8 | 19 | [哲学 (Philosophy)](哲学/README.md) |
| Religion | 34 | 127 | 39 | [宗教 (Religion)](宗教/README.md) |
| Sociology | 18 | 7 | 15 | [社会学 (Sociology)](社会学/README.md) |
| Psychology | 42 | 8 | 16 | [心理学 (Psychology)](心理学/README.md) |
| Ethics & Politics | 15 | 11 | 10 | [伦理政治 (Ethics & Political Philosophy)](伦理政治/README.md) |
| Aesthetics | 23 | 9 | 3 | [美学 (Aesthetics)](美学/README.md) |
| Literature | 5 | 8 | 5 | [文学 (Literature)](文学/README.md) |
| Arts | 3 | 8 | 3 | [艺术 (Arts)](艺术/README.md) |
| Cognitive Systems Engineering | 28 | 27 | 16 | [认知系统 (Cognitive Systems Engineering)](认知系统/README.md) |

Full index: [INDEX.md](INDEX.md) | Tag taxonomy: [TAGS.md](TAGS.md)

---

## Flagship: Buddhist Cognitive Theory

Under `religion/buddhism/concepts/cognitive-theory/`, this repository contains the deepest thematic treatment in the entire knowledge base -- a systematic treatment of Buddhism's cognitive science and epistemology resources.

Quick start guide: [QUICKSTART.md](宗教/佛教/概念/cognitive-theory/QUICKSTART.md)

### Scope

| Layer | Count | Coverage |
|------|------|------|
| Concept files | 15 core + 4 meditation topics = **19** | Yogacara, Madhyamaka, Abhidharma, Pramana, Early Buddhism, Chan/Zen |
| Applied Skills | **15** | Eight Consciousness diagnosis, Three Natures diagnosis, Pramana verification, Dependent Origination tracing, Five Aggregates deconstruction |
| Sutra cognitive architectures | **18 sutras** | Shurangama, Samdhinirmocana, Lankavatara, Heart Sutra, Diamond Sutra, Platform Sutra, and more |
| School cognitive frameworks | **8** | Theravada, Madhyamaka, Yogacara, Tiantai, Huayan, Chan, Pure Land, Vajrayana |
| Master cognitive contributions | **32** | Nagarjuna, Asanga/Vasubandhu, Zhiyi, Fazang, Huineng, Tsongkhapa, Dogen, Padmasambhava, and more |

### Entry Points

- **Main index**: [`religion/buddhism/INDEX.md`](宗教/佛教/INDEX.md)
- **Cognitive theory catalog**: [`concepts/cognitive-theory/README.md`](宗教/佛教/概念/cognitive-theory/README.md)
- **Representative concepts**: [Pramana](宗教/佛教/概念/cognitive-theory/量论.md) | [Three Natures](宗教/佛教/概念/cognitive-theory/三性.md) | [Consciousness Transformation](宗教/佛教/概念/cognitive-theory/六根六尘六识.md) | [Koan Mechanics](宗教/佛教/概念/cognitive-theory/公案与话头的认知机制.md)
- **Representative Skills**: [Eight Consciousness Diagnosis](宗教/佛教/技能/从前五识/SKILL.md) | [Three Natures Diagnosis](宗教/佛教/技能/以唯识三性/SKILL.md) | [Dependent Origination Tracing](宗教/佛教/技能/定位关键断点/SKILL.md) | [Five Aggregates Deconstruction](宗教/佛教/技能/以五蕴/SKILL.md)

### Dialogue with Contemporary Thought

Each concept file explicitly builds bridges to modern cognitive science, psychology, phenomenology, 哲学 of mind, and AI. For example:

- Eight Consciousnesses and the Default Mode Network (DMN)
- Five Aggregates and Hume's bundle theory / the binding problem
- Pramana and falsificationism / Carnap's internal-external distinction
- Koan and insight neuroscience (gamma band, Kounios & Beeman)
- Silent Illumination and pre-reflective self-awareness (Zahavi)
- Bija (seeds) and predictive coding (Friston)

---

## Repository Structure

```
open-cognition/
  README.md                   # Chinese README (project overview)
  README.en.md                # This file (English overview)
  AGENT.md                    # AI Agent integration guide
  INDEX.md                    # Full dual-perspective index
  TAGS.md                     # Unified tag taxonomy
  CONTRIBUTING.md             # Contribution guide
  index.json                  # Machine-readable index
  哲学/                  # Philosophy (280 thinkers / 251 concepts / 19 skills)
  宗教/                    # Religion (incl. Buddhist cognitive theory flagship)
  社会学/                   # Sociology
  心理学/                  # Psychology
  伦理政治/             # Ethics & Political Philosophy
  美学/                  # Aesthetics
  文学/                  # Literature
  艺术/                        # Arts
  认知系统/           # Cognitive Systems Engineering
  _meta/                       # Metadata, taxonomy, templates, reports
```

See the [Chinese README](README.md) for the full directory tree.

---

## Entry Types

### Thinker

Fixed structure: basic info, core propositions, intellectual context, key works, important concepts, coordinate mapping, contemporary applications, common misreadings, cross-disciplinary links, further reading, linked Skills.

Examples: [Freud](心理学/学派/精神分析/西格蒙德.md) | [Weber](社会学/学派/古典社会学/韦伯.md) | [Kant](哲学/学派/德国唯心论/康德.md) | [Nagarjuna](宗教/佛教/大师/龙树.md) | [Dogen](宗教/佛教/大师/道元.md)

### Concept

Fixed structure: one-line definition, historical context, core content, colloquial vs. scholarly framing, related concepts, representative thinkers, application scenarios, common misreadings, cross-disciplinary links, further reading.

Examples: [Flow](心理学/概念/心流.md) | [Cultural Capital](社会学/概念/文化资本.md) | [Sacred](宗教/概念/神圣性.md) | [Pramana](宗教/佛教/概念/cognitive-theory/量论.md)

### Skill

Agent-executable operational framework with YAML frontmatter, one-line function description, when-to-use / when-not-to-use guidance, theoretical basis, step-by-step procedure, worked examples, and counterexamples.

Examples: [CBT Cognitive Distortion](./心理学/技能/认知扭曲识别/SKILL.md) | [Bourdieu Field Analysis](./社会学/技能/布迪厄场域分析析/SKILL.md) | [Four Noble Truths](./宗教/技能/四圣谛框架分/SKILL.md) | [Eight Consciousness Diagnosis](宗教/佛教/技能/从前五识/SKILL.md)

---

## For AI Agents

All Skill files follow a unified frontmatter format:

```yaml
---
name: <skill-id>
description: <one-line function>
domain: <philosophy|religion|sociology|psychology|...>
linked_concepts: [relative paths to related concepts...]
tags: [...]
---
```

These can be directly indexed and invoked by agent runtimes (Claude Skills, Qoder Skills, custom RAG pipelines). Cross-references between entries use relative paths and explicit relationship-type annotations, supporting LLM graph reasoning.

Full agent integration guide: [AGENT.md](AGENT.md)

---

## License

Content is licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Free to use, modify, and distribute with attribution.

---

## Contributing

Contributions of new entries, misreading corrections, and cross-disciplinary links are welcome. See:

- [CONTRIBUTING.md](CONTRIBUTING.md) -- contribution workflow
- [_meta/quality-criteria.md](./_meta/quality-criteria.md) -- quality standards
- [_meta/taxonomy.md](./_meta/taxonomy.md) -- taxonomy
- [_meta/templates/](./_meta/templates/) -- entry templates

---

> "All conditioned phenomena are like dreams, illusions, bubbles, shadows; like dew and like lightning -- one should contemplate them thus." -- *Diamond Sutra*
>
> "The map is not the territory." -- Alfred Korzybski
