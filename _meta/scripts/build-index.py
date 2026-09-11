#!/usr/bin/env python3
"""
build-index.py — rebuild index.json by scanning Chinese domain directories.

Usage:
    python3 _meta/scripts/build-index.py          # write to index.json (default)
    python3 _meta/scripts/build-index.py --check  # exit non-zero if stale
    python3 _meta/scripts/build-index.py --out path/to/file.json

Output schema (per entry):
    { path, id, title, type, domain, school?, tags?, channel?, category?, angle?, count? }

Plus top-level `stats` and `skills` arrays.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("ERROR: pyyaml is required. Install with `pip install pyyaml`.")


REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Legacy skill directories (kept for backwards compatibility; current skills live
# under each domain's 技能/ folder and are picked up by scan_entries).
SKILLS_DIR = REPO_ROOT / "skills"
BUDDHISM_SKILLS_DIR = (
    REPO_ROOT
    / "domains"
    / "religion"
    / "buddhism"
    / "concepts"
    / "cognitive-theory"
    / "skills"
)

SKIP_FILENAMES = {"README.md", "INDEX.md", "QUICKSTART.md", "SKILLS.md", "AGENT.md"}

_DOMAIN_DIR_NAMES = [
    "哲学", "宗教", "伦理政治", "心理学", "社会学", "美学",
    "文学", "艺术", "认知系统", "清单", "研究", "TECH",
]
_DOMAIN_DIRS = [REPO_ROOT / d for d in _DOMAIN_DIR_NAMES]
VERSION = "v0.6"


def extract_frontmatter(path: Path) -> dict:
    """Read YAML frontmatter from a markdown file."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    # Find the closing ---
    try:
        end = text.index("---", 3)
    except ValueError:
        return {}
    fm_text = text[3:end]
    try:
        return yaml.safe_load(fm_text) or {}
    except yaml.YAMLError:
        return {}


def domain_from_path(path: Path) -> str:
    """Extract the top-level domain name from a file path."""
    rel = path.relative_to(REPO_ROOT).as_posix()
    parts = rel.split("/")
    if parts and parts[0] in _DOMAIN_DIR_NAMES:
        return parts[0]
    return ""


def classify_entry(path: Path) -> str | None:
    """Determine entry type: thinker / concept / skill / list / None."""
    rel = path.relative_to(REPO_ROOT).as_posix()
    # Reports/audit files are not entries — skip them.
    if "/reports/" in rel or "/审计/" in rel or "/内容审计/" in rel:
        return None

    # Prefer explicit type declared in frontmatter.
    fm = extract_frontmatter(path)
    known_types = {"thinker", "concept", "skill", "text", "tradition", "list", "redirect"}
    fm_type = fm.get("type")
    if fm_type in known_types:
        return fm_type

    # Path-based fallback (supports both legacy English and Chinese subdirs).
    if ("/skills/" in rel or "/技能/" in rel) and path.name == "SKILL.md":
        return "skill"
    if "/schools/" in rel or "/学派/" in rel:
        return "thinker"
    if "/concepts/" in rel or "/概念/" in rel:
        return "concept"
    if "/masters/" in rel or "/智慧大师/" in rel:
        return "thinker"
    if "/sutras/" in rel or "/佛经/" in rel:
        return "text"
    if "/core-concepts/" in rel or "/核心概念/" in rel:
        return "concept"
    if "/traditions/" in rel or "/传统/" in rel:
        return "tradition"
    return None


def scan_entries() -> list[dict]:
    """Walk domain directories and extract entries."""
    entries = []
    for domain_dir in _DOMAIN_DIRS:
        if not domain_dir.exists():
            continue
        for path in sorted(domain_dir.rglob("*.md")):
            if path.name in SKIP_FILENAMES:
                continue
            entry_type = classify_entry(path)
            if entry_type is None:
                continue
            fm = extract_frontmatter(path)
            rel = path.relative_to(REPO_ROOT).as_posix()
            entry_id = fm.get("id") or path.stem
            if path.name == "SKILL.md":
                # SKILL.md files use `name:` not `id:`; the stem is literally
                # "SKILL" for all 137 of them. Fall back to the skill slug.
                entry_id = fm.get("id") or fm.get("name") or path.parent.name
            entry = {
                "path": rel,
                "id": entry_id,
                "title": fm.get("title") or fm.get("name") or path.stem,
                "type": entry_type,
                "domain": domain_from_path(path),
            }
            if fm.get("school"):
                entry["school"] = fm["school"]
            if fm.get("tags"):
                entry["tags"] = fm["tags"]
            if fm.get("channel"):
                entry["channel"] = fm["channel"]
            if fm.get("category"):
                entry["category"] = fm["category"]
            if fm.get("angle"):
                entry["angle"] = fm["angle"]
            if fm.get("count") is not None:
                entry["count"] = fm["count"]
            entries.append(entry)
    return namespace_duplicate_ids(entries)


def namespace_duplicate_ids(entries: list[dict]) -> list[dict]:
    """Make `id` unique: repeated child-page ids (约翰-时间线 across three
    thinkers named 约翰, wuwei in three domains…) get a path-derived prefix.
    Entry ids that lint's E004 already guarantees unique are untouched."""
    counts: dict[str, int] = {}
    for e in entries:
        counts[e["id"]] = counts.get(e["id"], 0) + 1
    for e in entries:
        if counts[e["id"]] <= 1:
            continue
        parts = e["path"].split("/")
        prefix = ".".join(parts[:-1])  # full directory path; stem is parts[-1]
        e["id"] = f"{prefix}.{e['id']}"
    return entries


def scan_skills() -> list[dict]:
    """Extract Skills from each domain's 技能/ tree (plus legacy roots)."""
    skills = []
    seen: set[str] = set()
    base_dirs = [d for d in _DOMAIN_DIRS] + [SKILLS_DIR, BUDDHISM_SKILLS_DIR]
    for base_dir in base_dirs:
        if not base_dir.exists():
            continue
        for path in sorted(base_dir.rglob("SKILL.md")):
            rel = path.relative_to(REPO_ROOT).as_posix()
            if rel in seen:
                continue
            seen.add(rel)
            fm = extract_frontmatter(path)
            skill = {
                "path": rel,
                "name": fm.get("name") or path.parent.name,
                "description": fm.get("description") or "",
                "domain": fm.get("domain") or domain_from_path(path),
                "tags": fm.get("tags") or [],
            }
            skills.append(skill)
    return skills


def build_index() -> dict:
    entries = scan_entries()
    skills = scan_skills()
    domains_present = sorted({e["domain"] for e in entries if e.get("domain")})
    return {
        "version": VERSION,
        "generated": date.today().isoformat(),
        "stats": {
            "entries": len(entries),
            "skills": len(skills),
            "total": len(entries) + len(skills),
            "domains": domains_present,
        },
        "entries": entries,
        "skills": skills,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        default=REPO_ROOT / "index.json",
        type=Path,
        help="Output path (default: REPO_ROOT/index.json)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 if current index.json differs from rebuilt one",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        default=True,
        help="Pretty-print JSON (default)",
    )
    args = parser.parse_args()

    index = build_index()
    json_str = json.dumps(
        index,
        ensure_ascii=False,
        indent=2 if args.pretty else None,
    ) + "\n"

    if args.check:
        if not args.out.exists():
            print(f"MISSING: {args.out}", file=sys.stderr)
            return 1
        existing = args.out.read_text(encoding="utf-8")
        if existing == json_str:
            print(f"OK: {args.out} is up to date ({index['stats']['total']} entries)")
            return 0
        # Content drift vs. mere date drift: rebuild without the volatile
        # `generated` field and re-compare. Only flag STALE when the actual
        # entries/skills/stats changed — not when only the build date differs.
        def _strip_date(obj: dict) -> dict:
            return {k: v for k, v in obj.items() if k != "generated"}
        try:
            existing_obj = _strip_date(json.loads(existing))
        except json.JSONDecodeError:
            existing_obj = {}
        rebuilt_obj = _strip_date(json.loads(json_str))
        if existing_obj == rebuilt_obj:
            print(
                f"OK: {args.out} content is up to date "
                f"({index['stats']['total']} entries; only the build date differs)"
            )
            return 0
        print(f"STALE: {args.out}", file=sys.stderr)
        print(
            f"  declared: {json.loads(existing).get('stats', {})}",
            file=sys.stderr,
        )
        print(f"  actual:   {index['stats']}", file=sys.stderr)
        return 1

    args.out.write_text(json_str, encoding="utf-8")
    print(
        f"Wrote {args.out}: {index['stats']['entries']} entries + "
        f"{index['stats']['skills']} skills across "
        f"{len(index['stats']['domains'])} domains"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
