#!/usr/bin/env python3
"""
dedup-legacy-entries.py — remove legacy English-named duplicates of Chinese entries.

After the bulk English→Chinese rename, ~90 entry files kept their old ASCII
basenames alongside the new Chinese-named canonical file in the same directory.
Both carry the same frontmatter `id`, so index.json lists the entry twice and
the two copies slowly diverge (double source of truth).

Strategy (conservative):
  1. Candidate = domain .md file whose stem is pure ASCII, not README/INDEX/
     SKILL/QUICKSTART, entry type in {thinker, concept, text, tradition, school}.
  2. A twin must exist in the SAME directory: Chinese basename, same `id`,
     parsable frontmatter. Otherwise the ASCII file is left untouched.
  3. Guard: skip when content diverged (line-count diff > 30) — manual triage.
  4. All relative links across the repo that resolve to the ASCII file are
     rewritten to the twin BEFORE deletion.
  5. Only then is the ASCII file deleted.

Usage:
    python3 _meta/scripts/dedup-legacy-entries.py            # dry-run
    python3 _meta/scripts/dedup-legacy-entries.py --apply
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.parse
from pathlib import Path

import yaml

try:
    from lint import _DOMAIN_DIRS, extract_frontmatter  # type: ignore
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from lint import _DOMAIN_DIRS, extract_frontmatter  # type: ignore

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MD_LINK_RE = re.compile(r"(\[[^\]]*\]\()([^)]+)(\))")
SKIP_NAMES = {"README.md", "INDEX.md", "SKILL.md", "QUICKSTART.md", "AGENT.md"}
ENTRY_TYPES = {"thinker", "concept", "text", "tradition", "school"}
ASCII_STEM_RE = re.compile(r"^[a-z][a-z0-9-]*$")
MAX_DIVERGENCE = 30


def has_cjk(s: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", s))


def fm_of(path: Path) -> dict:
    try:
        fm, _ = extract_frontmatter(path.read_text(encoding="utf-8"))
        return fm or {}
    except Exception:
        return {}


def norm_target(target: str) -> str:
    t = urllib.parse.unquote(target.split("#")[0]).replace("\u00a0", " ").strip()
    while t.startswith("./"):
        t = t[2:]
    return t


def find_candidates() -> list[Path]:
    out = []
    for d in _DOMAIN_DIRS:
        if not d.exists():
            continue
        for p in sorted(d.rglob("*.md")):
            if p.name in SKIP_NAMES or not ASCII_STEM_RE.match(p.stem):
                continue
            fm = fm_of(p)
            if fm.get("type") not in ENTRY_TYPES:
                continue
            if fm.get("redirect_to") or fm.get("redirect"):
                continue
            out.append(p)
    return out


def find_twin(ascii_file: Path, entry_id: str) -> Path | None:
    twins = []
    for sib in ascii_file.parent.glob("*.md"):
        if sib == ascii_file or sib.name in SKIP_NAMES or not has_cjk(sib.stem):
            continue
        fm = fm_of(sib)
        if fm.get("id") == entry_id and fm.get("type") in ENTRY_TYPES:
            twins.append(sib)
    return twins[0] if len(twins) == 1 else None


def scan_md_files() -> list[Path]:
    skip_dirs = {".git", ".github", ".mimosa", ".v2c", ".video_agent", ".qoder",
                 ".claude", "node_modules"}
    out = []
    for p in REPO_ROOT.rglob("*.md"):
        rel = p.relative_to(REPO_ROOT)
        if rel.parts[0] in skip_dirs:
            continue
        out.append(p)
    return out


def rewrite_inbound(ascii_file: Path, twin: Path, files: list[Path], apply: bool) -> int:
    """Rewrite links resolving to ascii_file so they point at twin. Returns count."""
    rewritten = 0
    for f in files:
        if f == ascii_file:
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except Exception:
            continue
        changed = False

        def sub(m: re.Match) -> str:
            nonlocal rewritten, changed
            target = m.group(2)
            if target.startswith(("http://", "https://", "mailto:", "#", "/")):
                return m.group(0)
            resolved = (f.parent / norm_target(target)).resolve()
            if resolved != ascii_file.resolve():
                return m.group(0)
            import os
            new_rel = os.path.relpath(twin.resolve(), f.parent.resolve()).replace(os.sep, "/")
            rewritten += 1
            changed = True
            return f"{m.group(1)}{new_rel}{m.group(3)}"

        new_text = MD_LINK_RE.sub(sub, text)
        if changed and apply:
            f.write_text(new_text, encoding="utf-8")
    return rewritten


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    candidates = find_candidates()
    all_md = scan_md_files()

    pairs, skipped = [], []
    for c in candidates:
        fm = fm_of(c)
        twin = find_twin(c, fm.get("id", ""))
        if twin is None:
            skipped.append((c, "no unique same-id Chinese twin"))
            continue
        if len(twin.read_text(encoding="utf-8").split("\n")) <= 0:
            skipped.append((c, "twin unreadable"))
            continue
        d = abs(len(c.read_text(encoding="utf-8").split("\n"))
                - len(twin.read_text(encoding="utf-8").split("\n")))
        if d > MAX_DIVERGENCE:
            skipped.append((c, f"diverged by {d} lines — manual triage"))
            continue
        pairs.append((c, twin))

    for path, reason in skipped:
        print(f"SKIP  {path.relative_to(REPO_ROOT)} — {reason}")
    print(f"\n{len(pairs)} removable duplicate(s), {len(skipped)} skipped\n")

    total_links = 0
    for ascii_file, twin in sorted(pairs):
        n = rewrite_inbound(ascii_file, twin, all_md, args.apply)
        total_links += n
        if args.apply:
            ascii_file.unlink()
        print(f"{'DEL ' if args.apply else 'WOULD DEL '} "
              f"{ascii_file.relative_to(REPO_ROOT)} -> {twin.name} "
              f"({n} inbound link(s) rewritten)")

    print(f"\nMode: {'APPLIED' if args.apply else 'DRY-RUN'}; "
          f"{total_links} inbound link(s) {'rewritten' if args.apply else 'would be rewritten'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
