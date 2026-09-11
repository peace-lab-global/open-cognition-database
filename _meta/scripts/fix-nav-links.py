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

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RENAME_MAP_MD = REPO_ROOT / "RENAME-MAP.md"
MD_LINK_RE = re.compile(r"(\[[^\]]*\]\()([^)]+)(\))")
RENAME_ROW_RE = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*→\s*\|\s*`([^`]+)`\s*\|")
NAV_NAMES = {"README.md", "INDEX.md", "AGENT.md", "QUICKSTART.md"}
SKIP_DIRS = {".git", ".github", ".qoder", ".claude", ".mimosa", ".v2c",
             ".video_agent", "_meta", "node_modules", "scripts", "GTM"}
FUZZY_THRESHOLD = 0.90
DOMAINS = {"哲学", "宗教", "社会学", "心理学", "伦理政治", "美学", "文学",
           "艺术", "认知系统", "清单", "研究"}
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
# segments that carry no identifying content for the content-based matcher
STRUCTURAL_TOKENS = set(SEGMENT_ALIASES) | {
    "readme", "index", "skill", "core-concepts", "timeline", "works", "reading",
    "dialogues", "critiques", "reports", "domains", "texts", "list", "md",
}


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


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


def build_content_index() -> list[tuple[Path, str, set[str], bool, bool]]:
    """(path, blob-lower, id-keys, is_dir_readme, is_dir) for content matching.

    Entries plus directory targets: a CJK-named directory containing README.md
    is indexed through that README's frontmatter, so `../haydn/`-style dir
    links can resolve to 海顿/ when its entry exists.
    """
    index: list[tuple[Path, str, set[str], bool, bool]] = []
    skip = SKIP_DIRS | {"node_modules"}
    for p in REPO_ROOT.rglob("*.md"):
        if p.relative_to(REPO_ROOT).parts[0] in skip:
            continue
        blob, keys = "", set()
        try:
            text = p.read_text(encoding="utf-8")
        except OSError:
            continue
        if text.startswith("---"):
            try:
                fm = yaml.safe_load(text[3:text.index("---", 3)]) or {}
            except Exception:
                fm = {}
            blob = " ".join(str(x) for x in [
                fm.get("id", ""), fm.get("name", ""), fm.get("title", ""),
                fm.get("school", ""), " ".join(fm.get("aliases") or [])])
            eid, school = str(fm.get("id", "")), str(fm.get("school", ""))
            for k in (eid, f"{school}.{eid}", f"{eid}.{school}"):
                if k not in ("." , ""):
                    keys.add(norm(k))
        is_dir_readme = p.name == "README.md" and bool(
            re.search(r"[\u4e00-\u9fff]", p.parent.name))
        index.append((p, blob.lower(), keys, is_dir_readme, False))
    seen_dirs: set[Path] = set()
    for p, *_ in list(index):
        if p.name == "README.md" and re.search(r"[\u4e00-\u9fff]", p.parent.name):
            if p.parent not in seen_dirs:
                seen_dirs.add(p.parent)
                index.append((p.parent, "", set(), True, True))
    return index


def content_resolve(f: Path, target: str, index) -> Path | None:
    """6. CONTENT — locate the current entry by matching the target's English
    content tokens against frontmatter (id/school/title/aliases) and paths.
    Old slugs survive inside namespaced ids (`社会学.classical.durkheim`) and
    the school field, which is what makes this work after the bulk rename."""
    t = urllib.parse.unquote(target.split("#")[0]).strip().lstrip("./")
    if not t:
        return None
    wants_dir = t.endswith("/")
    segs = [s for s in t.split("/") if s]
    content = [s for s in segs if s.lower().rsplit(".", 1)[0] not in STRUCTURAL_TOKENS]
    if not content:
        return None
    toks: set[str] = set()
    for s in content:
        toks.update(x for x in re.split(r"[^a-zA-Z0-9]+", s.lower()) if len(x) >= 3)
    if not toks:
        return None
    hard = re.split(r"[^a-zA-Z0-9]+", content[-1].lower())[0]
    soft = toks - {hard}
    if len(content) >= 2 and not soft:
        return None
    slug = norm(".".join(content))
    dom = f.parts[0] if f.parts[0] in DOMAINS else None

    cands: list[tuple] = []
    for p, blob, keys, is_readme, is_dir in index:
        if is_dir:
            if not wants_dir:
                continue
            hay = str(p).lower().replace("/", " ")
        else:
            if wants_dir:
                continue
            hay = blob + " " + str(p).lower().replace("/", " ")
        if hard not in hay:
            continue
        got_soft = sum(1 for tk in soft if tk in hay)
        if len(content) >= 2 and got_soft == 0:
            continue
        extra = sum(1 for tk in re.split(r"[^a-z0-9]+", blob) if tk and tk not in toks)
        tier1 = any(slug and (k.endswith(slug) or k == slug) for k in keys)
        cands.append((not is_readme and not is_dir, not tier1, -got_soft,
                      extra, len(p.parts), str(p), p))
    if not cands:
        return None
    if dom:
        same = [c for c in cands if c[6].parts[0] == dom]
        if same:
            cands = same
    cands.sort(key=lambda c: c[:6])
    best = cands[0]
    ties = [c for c in cands if c[:6] == best[:6]]
    best_is_entry = not best[0]  # sorted: dir-readme/dir targets rank first
    if len(ties) == 1 or best_is_entry:
        return best[6]
    return None


def suffix_resolve(target: str) -> str | None:
    """7. SUFFIX — repair wrong relative-depth / mixed-language paths.

    Some links mix translated and untranslated segments or miscount `../`
    depth. If the longest trailing segment run of the target exists at repo
    root, the link can be rewritten to that path. A directory and its
    README.md count as ONE target; the directory wins for `/`-links."""
    t = norm_target_path(target)
    if not t:
        return None
    wants_dir = t.endswith("/")
    parts = [s for s in t.split("/") if s and s not in (".", "..")]
    for i in range(len(parts)):
        cand = "/".join(parts[i:])
        d = REPO_ROOT / cand
        if d.is_dir():
            return cand + "/" if wants_dir else cand
        if d.is_file():
            return cand
    return None


def unique_basename_resolve(target: str) -> str | None:
    """8. BASENAME — targets whose filename exists exactly once repo-wide are
    unambiguous regardless of wrong directory layers (e.g. concepts/辩证法.md)."""
    t = norm_target_path(target)
    if t.endswith("/"):
        return None
    base = t.split("/")[-1]
    if "/" not in t or not base.endswith(".md"):
        return None  # plain filenames were already handled by SINGLE
    hits = [p.relative_to(REPO_ROOT).as_posix()
            for p in REPO_ROOT.rglob(base)
            if "_meta" not in p.parts and ".git" not in p.parts]
    return hits[0] if len(hits) == 1 else None


def norm_target_path(target: str) -> str:
    t = urllib.parse.unquote(target.split("#")[0]).replace("\\", "/").strip()
    while t.startswith("./"):
        t = t[2:]
    return t



def context_basename_resolve(f: Path, target: str) -> str | None:
    """9. CONTEXT — disambiguate multi-copy basenames by context.

    Rank candidates by: longest common path prefix with the linking file
    (`佛教/学派/禅宗` beats `传统/佛教/禅宗` for a link from 佛教/大师/),
    then top-level hub pages (域/概念/x.md) over nested child pages."""
    t = norm_target_path(target)
    if t.endswith("/"):
        return None
    base = t.split("/")[-1]
    if "/" not in t or not base.endswith(".md"):
        return None
    src_parts = f.relative_to(REPO_ROOT).parts[:-1]
    cands = []
    for pp in REPO_ROOT.rglob(base):
        rel = pp.relative_to(REPO_ROOT)
        if any(seg in SKIP_DIRS for seg in rel.parts) or len(rel.parts) < 2:
            continue
        common = 0
        for a, b in zip(src_parts, rel.parts):
            if a != b:
                break
            common += 1
        is_hub = len(rel.parts) == 3 and rel.parts[1] in ("概念", "学派", "技能", "传统")
        cands.append((-common, 0 if is_hub else 1, len(rel.parts), rel.as_posix()))
    cands.sort()
    if len(cands) >= 2 and cands[0][:2] < cands[1][:2]:
        return cands[0][3]
    return cands[0][3] if len(cands) == 1 else None


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
             "CONTENT": 0, "SUFFIX": 0, "BASENAME": 0, "CONTEXT": 0, "UNFIXED": 0}
    unfixed: list[tuple[str, str]] = []
    index = build_content_index()

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
                            hit = content_resolve(f, target, index)
                            if hit is not None:
                                new_rel, kind = hit.relative_to(REPO_ROOT), "CONTENT"
                            else:
                                hit = suffix_resolve(target)
                                if hit is not None:
                                    new_rel, kind = hit, "SUFFIX"
                                else:
                                    hit = unique_basename_resolve(target)
                                    if hit is not None:
                                        new_rel, kind = hit, "BASENAME"
                                    else:
                                        hit = context_basename_resolve(f, target)
                                        if hit is not None:
                                            new_rel, kind = hit, "CONTEXT"
                                        else:
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
          f"FUZZYSIG={stats['FUZZYSIG']} CONTENT={stats['CONTENT']} "
          f"SUFFIX={stats['SUFFIX']} BASENAME={stats['BASENAME']} "
          f"CONTEXT={stats['CONTEXT']} "
          f"UNFIXED={stats['UNFIXED']}")
    if unfixed:
        print("\nUnfixed (manual triage):")
        for path, target in unfixed[:60]:
            print(f"  {path}: {target}")
        if len(unfixed) > 60:
            print(f"  ... and {len(unfixed) - 60} more")
    return 0


if __name__ == "__main__":
    sys.exit(main())
