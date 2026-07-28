#!/usr/bin/env python3
"""
check-nav-links.py — audit relative links in navigation files (README/INDEX/AGENT).

lint.py deliberately skips README.md / INDEX.md navigation files, so broken
links left behind by the bulk Chinese rename campaign live undetected there.
This tool scans all navigation files, resolves each relative link from the
file's own directory (and from repo root as fallback, matching AGENT.md's
"resolve from repo root" convention), and reports targets that do not exist.

Usage:
    python3 _meta/scripts/check-nav-links.py            # report all broken nav links
    python3 _meta/scripts/check-nav-links.py --summary  # per-file counts only
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.parse
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MD_LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
NAV_NAMES = {"README.md", "INDEX.md", "AGENT.md", "QUICKSTART.md"}
SKIP_DIRS = {".git", ".github", ".qoder", ".claude", "_meta", "node_modules", "scripts"}


def nav_files() -> list[Path]:
    files = []
    for p in REPO_ROOT.rglob("*.md"):
        rel = p.relative_to(REPO_ROOT)
        if rel.parts[0] in SKIP_DIRS:
            continue
        if p.name in NAV_NAMES:
            files.append(p)
    return sorted(files)


def is_external(target: str) -> bool:
    return target.startswith(("http://", "https://", "mailto:", "#"))


def resolve(base: Path, target: str) -> bool:
    # strip anchor, decode %-encoding, tolerate stray spaces from line wrapping
    target = target.split("#")[0].strip()
    if not target:
        return True
    target = urllib.parse.unquote(target).replace("\u00a0", " ")
    candidates = [base.parent / target, REPO_ROOT / target]
    return any(c.exists() for c in candidates)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()

    total_broken = 0
    per_file: dict[str, list[tuple[int, str, str]]] = {}
    for f in nav_files():
        text = f.read_text(encoding="utf-8")
        broken = []
        for i, line in enumerate(text.splitlines(), 1):
            for m in MD_LINK_RE.finditer(line):
                label, target = m.group(1), m.group(2)
                if is_external(target):
                    continue
                if not resolve(f, target):
                    broken.append((i, label, target))
        if broken:
            per_file[str(f.relative_to(REPO_ROOT))] = broken
            total_broken += len(broken)

    for path, broken in sorted(per_file.items(), key=lambda kv: -len(kv[1])):
        print(f"\n## {path} — {len(broken)} broken")
        if not args.summary:
            for line_no, label, target in broken:
                print(f"  L{line_no}: [{label}]({target})")

    print(f"\nTOTAL: {total_broken} broken link(s) in {len(per_file)} nav file(s)")
    return 1 if total_broken else 0


if __name__ == "__main__":
    sys.exit(main())
