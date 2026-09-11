#!/usr/bin/env python3
"""
fix-yaml-frontmatter.py — repair YAML syntax errors inside frontmatter blocks.

Targets the E001 class ("missing or invalid YAML frontmatter"): the block
exists and is well-intentioned, but markdown-isms leaked into YAML:

  1. `* ` bullets inside a sequence (markdown italics/bullets) — YAML reads
     `*` as an alias token. Rewritten to `- ` when it sits in list position.
  2. Unquoted plain scalars containing ASCII `: ` ("mapping values are not
     allowed here"). The scalar is double-quoted in place — literal content
     is preserved.

The script never rewrites fields that already parse. Every candidate file is
re-parsed after each fix; files that still fail are reported for manual work.

Usage:
    python3 _meta/scripts/fix-yaml-frontmatter.py            # dry-run
    python3 _meta/scripts/fix-yaml-frontmatter.py --apply    # write fixes
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

try:
    from lint import _DOMAIN_DIRS, extract_frontmatter  # type: ignore
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from lint import _DOMAIN_DIRS, extract_frontmatter  # type: ignore

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def split_fm(text: str) -> tuple[str, str] | None:
    """Return (fm_text, body) if the file has a frontmatter block, else None."""
    if not text.startswith("---"):
        return None
    try:
        end = text.index("---", 3)
    except ValueError:
        return None
    return text[3:end], text[end:]


def yaml_error_line(fm_text: str) -> int | None:
    try:
        yaml.safe_load(fm_text)
        return None
    except yaml.YAMLError as e:
        mark = getattr(e, "problem_mark", None)
        return mark.line if mark else None


def fix_star_bullets(fm_text: str) -> str:
    # A `* ` or `| ` in list-item position (leading indent + bullet + text)
    # becomes `- `: both are markdown bullets that YAML cannot parse (`*` is
    # an alias token, `|` a block-scalar token), and every occurrence so far
    # was a typo'd sequence item. Skipped when the line already contains
    # quotes, which would suggest the bullet is inside a literal string.
    out = []
    for line in fm_text.split("\n"):
        m = re.match(r"^(\s*)[*|] (\S.*)$", line)
        if m and '"' not in line and "'" not in line:
            out.append(f"{m.group(1)}- {m.group(2)}")
        else:
            out.append(line)
    return "\n".join(out)


def quote_colon_scalars(fm_text: str) -> str:
    """Double-quote sequence items / mapping values whose plain scalar has `: `."""
    out = []
    for line in fm_text.split("\n"):
        m = re.match(r"^(\s*-\s)(.+)$", line)
        if m and ": " in m.group(2) and not m.group(2).startswith(('"', "'", "[", "{", "> ", "|")):
            out.append(f"{m.group(1)}\"{m.group(2)}\"")
            continue
        m = re.match(r"^(\s*[A-Za-z_][\w-]*:\s)(.+)$", line)
        if m and ": " in m.group(2) and not m.group(2).startswith(('"', "'", "[", "{", "> ", "|")):
            out.append(f"{m.group(1)}\"{m.group(2)}\"")
            continue
        out.append(line)
    return "\n".join(out)


def quote_inner_double_quote(fm_text: str) -> str:
    """Single-quote sequence items that contain a bare ASCII `"` (e.g.
    《带经堂诗话》"神韵说") — double-quoting would need escaping, single
    quoting preserves the literal as long as the scalar has no `'`."""
    out = []
    for line in fm_text.split("\n"):
        m = re.match(r"^(\s*-\s)(.+)$", line)
        if m and '"' in m.group(2) and "'" not in m.group(2) and not m.group(2).startswith(('"', "'", "[", "{")):
            out.append(f"{m.group(1)}'{m.group(2)}'")
            continue
        out.append(line)
    return "\n".join(out)


def dedent_orphan_key(fm_text: str) -> str:
    """A `key:` line indented to the same level as surrounding sequence items
    (indentation lost in a bulk edit) breaks the mapping. Dedent it to column
    zero so it becomes a top-level key; its 2-space items then parse as its
    sequence."""
    out = []
    prev_item = False
    for line in fm_text.split("\n"):
        m = re.match(r"^(\s{2,})([A-Za-z_][\w-]*):\s*$", line)
        if m and prev_item:
            out.append(f"{m.group(2)}:")
        else:
            out.append(line)
        stripped = line.strip()
        prev_item = stripped.startswith("- ") or (stripped != "" and not stripped.startswith(("-", "#")) and line.startswith(" "))
    return "\n".join(out)


def indent_orphan_item(fm_text: str) -> str:
    """A `- item` at column 0 following indented sequence items lost its
    indentation; re-indent it to 2 spaces so it rejoins the sequence."""
    out = []
    prev_indented_item = False
    for line in fm_text.split("\n"):
        if re.match(r"^- \S", line) and prev_indented_item:
            out.append("  " + line)
        else:
            out.append(line)
        stripped = line.strip()
        prev_indented_item = bool(re.match(r"^\s+- \S", line))
    return "\n".join(out)


def bullet_missing_item(fm_text: str) -> str:
    """A plain text line sandwiched between sequence items lost its `- `
    bullet (`  王夫之《姜斋诗话》`); restore it. Only fires while the file
    still fails to parse, so legitimate multi-line scalars are untouched."""
    out = []
    prev_item = False
    for line in fm_text.split("\n"):
        m = re.match(r"^(\s+)([^-\s#][^:]*\S)$", line)
        if m and prev_item and not re.match(r"^\s+[A-Za-z_][\w-]*:", line):
            out.append(f"{m.group(1)}- {m.group(2)}")
        else:
            out.append(line)
        stripped = line.strip()
        prev_item = stripped.startswith("- ")
    return "\n".join(out)


REPAIRS = [fix_star_bullets, quote_colon_scalars, quote_inner_double_quote,
           dedent_orphan_key, indent_orphan_item, bullet_missing_item]


def process(path: Path, apply: bool) -> str:
    text = path.read_text(encoding="utf-8")
    parts = split_fm(text)
    if parts is None:
        return "no-frontmatter"
    fm_text, body = parts
    if yaml_error_line(fm_text) is None:
        return "clean"

    orig = fm_text
    for _ in range(6):
        if yaml_error_line(fm_text) is None:
            break
        for repair in REPAIRS:
            fm_text = repair(fm_text)
            if yaml_error_line(fm_text) is None:
                break
    if yaml_error_line(fm_text) is not None:
        err = yaml_error_line(fm_text)
        return f"STILL-BROKEN (line {err + 1 if err is not None else '?'})"

    if apply and fm_text != orig:
        path.write_text("---" + fm_text + body, encoding="utf-8")
        return "fixed"
    return "fixable"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    results: dict[str, list[Path]] = {}
    for d in _DOMAIN_DIRS:
        if not d.exists():
            continue
        for p in sorted(d.rglob("*.md")):
            r = process(p, args.apply)
            results.setdefault(r, []).append(p)

    for r in ("fixed", "fixable", "STILL-BROKEN", "no-frontmatter", "clean"):
        paths = results.get(r, [])
        if not paths:
            continue
        print(f"{r}: {len(paths)}")
        if r != "clean":
            for p in paths:
                print(f"  {p.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
