#!/usr/bin/env python3
"""
build-deep-index.py — build a cross-domain index of all "deep research" thinkers.

A thinker qualifies as "deep research" when their folder under 学派/ contains
a README.md plus companion files (时间线.md, 著作.md, 阅读.md).

Output: 索引/README.md

Usage:
    python3 _meta/scripts/build-deep-index.py
    python3 _meta/scripts/build-deep-index.py --check   # exit 1 if stale
"""

from __future__ import annotations

import argparse
import sys
from collections import OrderedDict
from datetime import date, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("ERROR: pyyaml is required. Install with `pip install pyyaml`.")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT = REPO_ROOT / "索引" / "README.md"

DOMAIN_ORDER = [
    "哲学", "伦理政治", "社会学", "心理学",
    "文学", "美学", "艺术", "认知系统",
    "宗教", "清单", "研究", "TECH",
]

STANDARD_COMPANIONS = {"README.md", "时间线.md", "著作.md", "阅读.md"}


def extract_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    try:
        end = text.index("---", 3)
    except ValueError:
        return {}
    try:
        return yaml.safe_load(text[3:end]) or {}
    except yaml.YAMLError:
        return {}


def domain_sort_key(domain: str) -> int:
    try:
        return DOMAIN_ORDER.index(domain)
    except ValueError:
        return len(DOMAIN_ORDER)


def scan_deep_thinkers() -> list[dict]:
    thinkers = []
    seen = set()

    for readme in sorted(REPO_ROOT.rglob("学派/**/README.md")):
        rel = readme.relative_to(REPO_ROOT)
        parts = rel.parts
        if len(parts) < 5:
            continue

        domain = parts[0]
        school = parts[2]
        thinker_folder = parts[3]
        folder = readme.parent
        key = f"{domain}/{school}/{thinker_folder}"

        if key in seen:
            continue
        seen.add(key)

        fm = extract_frontmatter(readme)
        title = fm.get("title") or thinker_folder

        companions = []
        subdirs = []
        extra_files = []

        for item in sorted(folder.iterdir()):
            if item.is_file() and item.suffix == ".md":
                name = item.name
                if name in STANDARD_COMPANIONS:
                    companions.append(name)
                else:
                    extra_files.append(name)
            elif item.is_dir():
                md_count = len(list(item.rglob("*.md")))
                if md_count > 0:
                    subdirs.append((item.name, md_count))

        thinkers.append({
            "domain": domain,
            "school": school,
            "folder": thinker_folder,
            "title": title,
            "readme_path": str(rel),
            "folder_path": str(folder.relative_to(REPO_ROOT)),
            "companions": companions,
            "subdirs": subdirs,
            "extra_files": extra_files,
            "fm": fm,
        })

    return thinkers


def build_markdown(thinkers: list[dict]) -> str:
    by_domain: OrderedDict[str, list[dict]] = OrderedDict()
    for t in thinkers:
        by_domain.setdefault(t["domain"], []).append(t)

    sorted_domains = sorted(by_domain.keys(), key=domain_sort_key)

    lines = []
    lines.append("# 深度研究索引 · Deep Research Index")
    lines.append("")
    lines.append("本索引聚合全库所有**深度研究**级别的思想家条目——即拥有专属文件夹（README + 时间线 + 著作 + 阅读）的条目。")
    lines.append("")
    lines.append(f"> 共 **{len(thinkers)}** 位思想家，跨 **{len(by_domain)}** 个领域。")
    lines.append(f"> 自动生成于 {date.today().isoformat()}，运行 `python3 _meta/scripts/build-deep-index.py` 更新。")
    lines.append("")
    lines.append("---")
    lines.append("")

    for domain in sorted_domains:
        entries = by_domain[domain]
        lines.append(f"## {domain}（{len(entries)}）")
        lines.append("")

        by_school: OrderedDict[str, list[dict]] = OrderedDict()
        for e in entries:
            by_school.setdefault(e["school"], []).append(e)

        for school, school_entries in by_school.items():
            lines.append(f"### {school}")
            lines.append("")

            for t in school_entries:
                folder = t["folder_path"]
                title = t["title"]

                links = [f"[要义]({t['readme_path']})"]
                for comp in ["时间线.md", "著作.md", "阅读.md"]:
                    if comp in t["companions"]:
                        label = comp.replace(".md", "")
                        links.append(f"[{label}]({folder}/{comp})")

                extra_parts = []
                for dirname, count in t["subdirs"]:
                    extra_parts.append(f"[{dirname}]({folder}/{dirname}/)（{count}篇）")
                for ef in t["extra_files"]:
                    label = ef.replace(".md", "")
                    extra_parts.append(f"[{label}]({folder}/{ef})")

                link_str = " · ".join(links)
                if extra_parts:
                    link_str += " | 扩展：" + " · ".join(extra_parts)

                lines.append(f"- **{title}** — {link_str}")

            lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Exit 1 if output is stale")
    args = parser.parse_args()

    thinkers = scan_deep_thinkers()
    md = build_markdown(thinkers) + "\n"

    if args.check:
        if not OUTPUT.exists():
            print(f"MISSING: {OUTPUT}", file=sys.stderr)
            return 1
        existing = OUTPUT.read_text(encoding="utf-8")
        if existing == md:
            print(f"OK: {OUTPUT} is up to date ({len(thinkers)} thinkers)")
            return 0
        print(f"STALE: {OUTPUT}", file=sys.stderr)
        return 1

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(md, encoding="utf-8")
    print(f"Wrote {OUTPUT}: {len(thinkers)} thinkers across {len(set(t['domain'] for t in thinkers))} domains")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
