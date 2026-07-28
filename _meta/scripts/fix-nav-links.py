#!/usr/bin/env python3
"""
fix-nav-links.py — repair broken relative links in navigation files.

Companion to check-nav-links.py / fix-broken-links.py. Navigation files
(README.md / INDEX.md / QUICKSTART.md) kept many pre-rename English paths
after the bulk Chinese rename (RENAME-MAP.md, 2366 renames). This tool
repairs them with three conservative, deterministic strategies:

  1. RENAME  — the broken target matches the tail of exactly one OLD path
               in RENAME-MAP.md and the mapped NEW path exists on disk.
  2. SINGLE  — the target basename exists exactly once in the repo.
  3. SIGNATURE — basename exists N times, but the target's own last two
               path segments narrow candidates to exactly one file.
  4. ALIAS   — the target uses pre-rename English structural segments
               (schools/concepts/skills/masters/...); translating them to
               the Chinese layer names yields an existing file.
  5. FUZZYSIG — the last-2-segment signature has exactly one repo match
               with similarity >= 0.90 (handles duplicated-character
               rename typos like 分析析 → 分析).

Anything ambiguous is left untouched and reported for manual triage.

Usage:
    python3 _meta/scripts/fix-nav-links.py            # dry-run report
    python3 _meta/scripts/fix-nav-links.py --apply    # write fixes to disk
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import urllib.parse
from difflib import SequenceMatcher
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RENAME_MAP_MD = REPO_ROOT / "RENAME-MAP.md"
MD_LINK_RE = re.compile(r"(\[[^\]]*\]\()([^)]+)(\))")
RENAME_ROW_RE = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*→\s*\|\s*`([^`]+)`\s*\|")
NAV_NAMES = {"README.md", "INDEX.md", "AGENT.md", "QUICKSTART.md"}
SKIP_DIRS = {".git", ".github", ".qoder", ".claude", "_meta", "node_modules", "scripts"}
FUZZY_THRESHOLD = 0.90
# pre-rename English structural segment -> current Chinese layer name
SEGMENT_ALIASES = {
    "schools": "学派",
    "concepts": "概念",
    "skills": "技能",
    "masters": "大师",
    "traditions": "传统",
    "classics": "经典",
    "treatises": "论典",
    "meta": "_meta",
}


def load_renames() -> list[tuple[str, str]]:
    pairs = []
    for line in RENAME_MAP_MD.read_text(encoding="utf-8").splitlines():
        m = RENAME_ROW_RE.match(line.strip())
        if m:
            pairs.append((m.group(1).strip(), m.group(2).strip()))
    return pairs


def all_repo_files() -> list[Path]:
    files = []
    for p in REPO_ROOT.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(REPO_ROOT)
        if rel.parts[0] in SKIP_DIRS:
            continue
        files.append(rel)
    return files


def nav_files() -> list[Path]:
    out = []
    for p in REPO_ROOT.rglob("*.md"):
        rel = p.relative_to(REPO_ROOT)
        if rel.parts[0] in SKIP_DIRS:
            continue
        if p.name in NAV_NAMES:
            out.append(p)
    return sorted(out)


def is_external(target: str) -> bool:
    return target.startswith(("http://", "https://", "mailto:", "#"))


def norm(target: str) -> str:
    t = urllib.parse.unquote(target).replace("\u00a0", " ").strip()
    while t.startswith("./"):
        t = t[2:]
    return t


def exists(base: Path, target: str) -> bool:
    t = norm(target.split("#")[0])
    if not t:
        return True
    return (base.parent / t).exists() or (REPO_ROOT / t).exists()


def alias_or_fuzzy(
    f: Path, t: str, by_signature: dict[str, list[Path]]
) -> tuple[Path | None, str]:
    # 4. ALIAS — translate English structural segments, then re-resolve
    parts = [SEGMENT_ALIASES.get(p, p) for p in Path(t).parts]
    aliased = Path(*parts)
    for cand in (f.parent / aliased, REPO_ROOT / aliased):
        try:
            if cand.exists():
                return cand.resolve().relative_to(REPO_ROOT), "ALIAS"
        except (OSError, ValueError):
            pass
    # 5. FUZZYSIG — unique high-similarity signature match (rename typos)
    sig = "/".join(Path(t).parts[-2:])
    best: list[tuple[float, Path]] = []
    for key, hits in by_signature.items():
        if len(hits) != 1:
            continue
        ratio = SequenceMatcher(None, sig, key).ratio()
        if ratio >= FUZZY_THRESHOLD:
            best.append((ratio, hits[0]))
    if len(best) == 1:
        return best[0][1], "FUZZYSIG"
    return None, ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    renames = load_renames()
    repo_files = all_repo_files()
    by_basename: dict[str, list[Path]] = {}
    by_signature: dict[str, list[Path]] = {}
    for rel in repo_files:
        by_basename.setdefault(rel.name, []).append(rel)
        if len(rel.parts) >= 2:
            by_signature.setdefault("/".join(rel.parts[-2:]), []).append(rel)

    stats = {"RENAME": 0, "SINGLE": 0, "SIGNATURE": 0, "ALIAS": 0, "FUZZYSIG": 0,
             "UNFIXED": 0}
    unfixed: list[tuple[str, str]] = []

    for f in nav_files():
        text = f.read_text(encoding="utf-8")
        changed = False

        def repair(m: re.Match) -> str:
            nonlocal changed
            prefix, target, suffix = m.group(1), m.group(2), m.group(3)
            if is_external(target) or exists(f, target):
                return m.group(0)
            path_part, _, anchor = target.partition("#")
            t = norm(path_part)

            new_rel: Path | None = None
            # 1. RENAME-MAP tail match
            tail_hits = [new for old, new in renames
                         if old == t or old.endswith("/" + t)]
            tail_hits = [n for n in set(tail_hits) if (REPO_ROOT / n).exists()]
            if len(tail_hits) == 1:
                new_rel, kind = Path(tail_hits[0]), "RENAME"
            else:
                # 2. unique basename
                base_hits = by_basename.get(Path(t).name, [])
                if len(base_hits) == 1:
                    new_rel, kind = base_hits[0], "SINGLE"
                else:
                    # 3. unique last-2-segment signature
                    sig = "/".join(Path(t).parts[-2:])
                    sig_hits = by_signature.get(sig, [])
                    if len(sig_hits) == 1:
                        new_rel, kind = sig_hits[0], "SIGNATURE"
                    else:
                        new_rel, kind = alias_or_fuzzy(f, t, by_signature)
                        if new_rel is None:
                            stats["UNFIXED"] += 1
                            unfixed.append((str(f.relative_to(REPO_ROOT)), target))
                            return m.group(0)

            fixed = os.path.relpath(REPO_ROOT / new_rel, f.parent)
            if anchor:
                fixed += "#" + anchor
            stats[kind] += 1
            changed = True
            return prefix + fixed + suffix

        new_text = MD_LINK_RE.sub(repair, text)
        if changed and args.apply:
            f.write_text(new_text, encoding="utf-8")

    mode = "APPLIED" if args.apply else "DRY-RUN"
    print(f"[{mode}] RENAME={stats['RENAME']} SINGLE={stats['SINGLE']} "
          f"SIGNATURE={stats['SIGNATURE']} ALIAS={stats['ALIAS']} "
          f"FUZZYSIG={stats['FUZZYSIG']} UNFIXED={stats['UNFIXED']}")
    if unfixed:
        print("\nUnfixed (manual triage):")
        for path, target in unfixed[:60]:
            print(f"  {path}: {target}")
        if len(unfixed) > 60:
            print(f"  ... and {len(unfixed) - 60} more")
    return 0


if __name__ == "__main__":
    sys.exit(main())
