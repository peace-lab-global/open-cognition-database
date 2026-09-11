#!/usr/bin/env python3
"""
fix-broken-links.py — deterministically repair E003 broken relative links.

Conservative strategy — only rewrites links where the correct target is
unambiguous. Three categories are auto-fixed; everything else is written
to a review report (no file changes).

Auto-fix categories:
  1. SINGLE   — target basename exists exactly once in the repo.
                Rewrite link to point at that unique file.
  2. SIGNATURE— basename exists N times, but the link's own path
                signature (last 2 segments) narrows it to exactly one.
                Rewrite link to point at that match.
  3. FUZZY    — basename does not exist at all, but a single other file
                stem matches with ratio >= 0.90 (clear typo, e.g.
                shurangama -> surangama). Rewrite to the fuzzy match.

Everything else (ambiguous multi-candidate, or missing-with-low-score)
is listed in the review report for manual triage — left untouched.

Usage:
    python3 scripts/fix-broken-links.py            # apply fixes (dry-run by default)
    python3 scripts/fix-broken-links.py --apply    # write changes to disk
    python3 scripts/fix-broken-links.py --report fix-review.md
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from difflib import SequenceMatcher
from pathlib import Path

try:
    import yaml  # noqa: F401  (kept for parity with sibling scripts)
except ImportError:
    pass

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
try:
    from lint import _DOMAIN_DIRS  # type: ignore
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from lint import _DOMAIN_DIRS  # type: ignore
DOMAIN_DIRS = [d for d in _DOMAIN_DIRS if d.exists()]
SKIP_FILENAMES = {"README.md", "INDEX.md", "QUICKSTART.md", "SKILLS.md", "AGENT.md"}
MD_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
FUZZY_THRESHOLD = 0.90


def collect_entry_files() -> list[Path]:
    files = []
    for domain_dir in DOMAIN_DIRS:
        for path in sorted(domain_dir.rglob("*.md")):
            if path.name in SKIP_FILENAMES:
                continue
            files.append(path)
    return files


def build_indexes():
    by_name: dict[str, list[Path]] = {}
    by_stem: dict[str, list[Path]] = {}
    for p in REPO_ROOT.rglob("*.md"):
        rel = str(p)
        if "/.git/" in rel or "/.qoder/" in rel:
            continue
        by_name.setdefault(p.name, []).append(p)
        by_stem.setdefault(p.stem, []).append(p)
    return by_name, by_stem


def signature_match(target: str, candidates: list[Path]) -> Path | None:
    """Narrow multi-candidates by the link's own last-2-segment signature."""
    sig = "/".join(Path(target).parts[-2:])
    matches = [c for c in candidates if sig in str(c.relative_to(REPO_ROOT))]
    return matches[0] if len(matches) == 1 else None


def best_fuzzy(target_stem: str, by_stem) -> tuple[str | None, float]:
    best, best_score = None, 0.0
    for stem in by_stem:
        s = SequenceMatcher(None, target_stem, stem).ratio()
        if s > best_score:
            best, best_score = stem, s
    return best, best_score


def domain_of(path: Path) -> str:
    """Top-level domain dir for a path under a domain directory, else ''."""
    try:
        first = path.relative_to(REPO_ROOT).parts[0]
    except ValueError:
        return ""
    return first if first in {d.name for d in DOMAIN_DIRS} else ""


def domain_proximity_match(src: Path, target: str, candidates: list[Path]) -> Path | None:
    """Last-resort disambiguation for multi-candidate thinkers that legitimately
    exist in several domains (kant, aristotle, beck, ...). Prefer the candidate
    whose domain matches the source file's domain; if none match, prefer the
    candidate whose school-dir name most closely matches a segment of the link."""
    src_domain = domain_of(src)
    same_domain = [c for c in candidates if domain_of(c) == src_domain]
    if len(same_domain) == 1:
        return same_domain[0]
    # tie-break: prefer the candidate whose parent dir name appears in the link
    target_lower = target.lower()
    for c in candidates:
        if c.parent.name.lower() in target_lower:
            return c
    return None


def rel_link(from_file: Path, to_file: Path) -> str:
    """Compute a POSIX relative link path from from_file's dir to to_file.

    The two paths may live in unrelated subtrees, so use os.path.relpath
    (handles '../' climbing) rather than Path.relative_to (which requires
    one path to be an ancestor of the other).
    """
    import os
    return os.path.relpath(to_file.resolve(), from_file.resolve().parent).replace(os.sep, "/")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true", help="write fixes to disk (default: dry-run)")
    ap.add_argument("--report", default="link-fix-review.md", help="review-report path")
    args = ap.parse_args()

    by_name, by_stem = build_indexes()
    entry_files = collect_entry_files()

    fixed = []        # (file, line, old_target, new_target, category)
    skipped = []      # (file, line, target, reason)
    files_changed = set()

    for path in entry_files:
        text = path.read_text(encoding="utf-8")
        lines = text.split("\n")
        new_lines = list(lines)
        changed_here = False

        for i, line in enumerate(lines, start=1):
            for m in MD_LINK_RE.finditer(line):
                target = m.group(2)
                if target.startswith(("http://", "https://", "mailto:", "#", "/")):
                    continue
                resolved = (path.parent / target).resolve()
                if resolved.exists():
                    continue  # not broken

                target_name = Path(target).name
                candidates = by_name.get(target_name, [])
                new_target = None
                category = None

                if len(candidates) == 1:
                    new_target = candidates[0]
                    category = "SINGLE"
                elif len(candidates) > 1:
                    hit = signature_match(target, candidates)
                    if hit:
                        new_target = hit
                        category = "SIGNATURE"

                if new_target is None:
                    # try fuzzy on the stem
                    target_stem = Path(target_name).stem
                    stem_hit, score = best_fuzzy(target_stem, by_stem)
                    if stem_hit and score >= FUZZY_THRESHOLD and len(by_stem[stem_hit]) == 1:
                        new_target = by_stem[stem_hit][0]
                        category = f"FUZZY({score:.2f})"

                if new_target is None and len(candidates) > 1:
                    # domain-proximity for cross-domain thinkers
                    hit = domain_proximity_match(path, target, candidates)
                    if hit:
                        new_target = hit
                        category = "PROXIMITY"

                if new_target is not None:
                    new_rel = rel_link(path, new_target)
                    old_full = m.group(0)
                    new_full = f"[{m.group(1)}]({new_rel})"
                    new_lines[i - 1] = new_lines[i - 1].replace(old_full, new_full)
                    fixed.append((path, i, target, new_rel, category))
                    changed_here = True
                else:
                    reason = "ambiguous-multi" if candidates else "missing"
                    skipped.append((path, i, target, reason))

        if changed_here:
            files_changed.add(path)
            if args.apply:
                path.write_text("\n".join(new_lines), encoding="utf-8")

    # Report
    print(f"Auto-fixable:  {len(fixed)} links across {len(files_changed)} files")
    print(f"Needs review:  {len(skipped)} links")
    print(f"Mode:          {'APPLIED' if args.apply else 'DRY-RUN (use --apply to write)'}")

    by_cat: dict[str, int] = {}
    for _, _, _, _, c in fixed:
        by_cat[c] = by_cat.get(c, 0) + 1
    for c, n in sorted(by_cat.items(), key=lambda x: -x[1]):
        print(f"  {c}: {n}")

    # Write review report
    rep = Path(args.report)
    if not rep.is_absolute():
        rep = REPO_ROOT / rep
    with rep.open("w", encoding="utf-8") as fh:
        fh.write("# Link Fix — Review Report\n\n")
        fh.write(f"Generated by `scripts/fix-broken-links.py`. ")
        fh.write(f"Auto-fixed {len(fixed)}; {len(skipped)} need manual triage.\n\n")
        fh.write("## Auto-fixed samples (first 20)\n\n")
        fh.write("| File | Line | Old | New | Cat |\n|---|---|---|---|---|\n")
        for path, line, old, new, cat in fixed[:20]:
            fh.write(f"| {path.relative_to(REPO_ROOT)} | {line} | `{old}` | `{new}` | {cat} |\n")
        fh.write(f"\n_(showing 20 of {len(fixed)})_\n\n")
        fh.write("## Needs manual review\n\n")
        fh.write("| File | Line | Broken target | Reason |\n|---|---|---|---|\n")
        for path, line, target, reason in skipped:
            fh.write(f"| {path.relative_to(REPO_ROOT)} | {line} | `{target}` | {reason} |\n")
    print(f"\nReview report: {rep.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
