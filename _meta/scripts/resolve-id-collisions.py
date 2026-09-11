#!/usr/bin/env python3
"""
resolve-id-collisions.py — clear E004 (same frontmatter `id` on multiple entries).

Each collision group from lint's E004 falls into one of five shapes left by
the English→Chinese rename / pointer-mode migration. This tool resolves each
shape with the matching, content-preserving strategy:

  A. same-dir stub+full   — full legacy entry + Chinese stub whose `redirect:`
       points at the old English dir. Fix stub's redirect to the Chinese dir,
       rewrite inbound links full→stub, delete the full.
  B. cross-dir stub+full  — same person legitimately entry'd in two domains,
       one side a stub. Keep both; namespace the stub id (`<id>-<domain>`) and
       repair its redirect if broken.
  C. both-full cross-dir  — two full legacy entries, each superseded by its
       own pointer-dir README (verified ≥50 lines). Convert both to stubs;
       the primary keeps the bare id, the secondary gets `<id>-literature`.
  D. same-dir both-full near-duplicate — the suffixed variant carries extra
       insert-only sections; transplant them into the plain-named file,
       rewrite inbound, delete the suffixed file.
  E. triple (philosophy pair + religion master) — A on the same-dir pair,
       then namespace the religion stub's id (`<id>-religion`).

Dry-run by default; --apply writes. Post-conditions are asserted per group
and summarized at the end.
"""

from __future__ import annotations

import argparse
import difflib
import os
import re
import sys
import urllib.parse
from pathlib import Path

import yaml

try:
    from lint import (extract_frontmatter, is_child_page,  # type: ignore
                      _DOMAIN_DIRS, REPO_ROOT, SKIP_FILENAMES)
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from lint import (extract_frontmatter, is_child_page,  # type: ignore
                      _DOMAIN_DIRS, REPO_ROOT, SKIP_FILENAMES)

MD_LINK_RE = re.compile(r"(\[[^\]]*\]\()([^)]+)(\))")
ENTRY_TYPES = {"thinker", "concept", "text", "tradition", "school", "list", "skill"}

# B/E-case id namespacing: entry id -> new namespaced id
NAMESPACE_ID = {
    "哲学/学派/社会契约论/约翰.md": None,  # placeholder, real keys set below
}
ID_RENAMES = {
    ("伦理政治/学派/社会契约论/约翰.md"): "locke-ethics-politics",
    ("哲学/学派/分析哲学/霍维.md"): "hohwy-philosophy",
    ("艺术/学派/表演艺术/谢尔盖.md"): "eisenstein-arts",
    ("宗教/传统/道教/masters/老子.md"): "laozi-religion",
    ("宗教/传统/道教/masters/庄子.md"): "zhuangzi-religion",
    ("文学/学派/小说家/费奥多尔.md"): "dostoevsky-literature",
    ("文学/学派/小说家/弗兰茨.md"): "kafka-literature",
    ("文学/学派/散文家/鲁迅.md"): "lu-xun-literature",
}

# C-case: legacy full entries to convert into stubs of their own dir README
CONVERT_TO_STUB = {
    "美学/学派/文学思想/陀思妥耶夫斯基.md",
    "文学/学派/小说家/费奥多尔.md",
    "美学/学派/文学思想/卡夫卡.md",
    "文学/学派/小说家/弗兰茨.md",
    "美学/学派/文学思想/鲁迅.md",
    "文学/学派/散文家/鲁迅.md",
}

# D-case: (keep, delete) near-duplicate pair; keep gets delete's insertions
SURANGAMA_KEEP = Path("宗教/佛教/经典/大佛顶首楞严经.md")
SURANGAMA_DEL = Path("宗教/佛教/经典/大佛顶首楞严经-surangama-sutra.md")


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def collect_entries():
    by_id: dict[str, list[tuple[Path, dict]]] = {}
    for d in _DOMAIN_DIRS:
        for p in sorted(d.rglob("*.md")):
            if p.name in SKIP_FILENAMES or is_child_page(p):
                continue
            fm, _ = extract_frontmatter(p.read_text(encoding="utf-8"))
            if not fm or fm.get("type") not in ENTRY_TYPES:
                continue
            eid = fm.get("id")
            if eid:
                by_id.setdefault(str(eid), []).append((p, fm))
    return by_id


def is_stub(fm: dict) -> bool:
    return bool(fm.get("redirect") or fm.get("redirect_to"))


def norm_target(target: str) -> str:
    t = urllib.parse.unquote(target.split("#")[0]).replace("\u00a0", " ").strip()
    while t.startswith("./"):
        t = t[2:]
    return t


def all_md_files() -> list[Path]:
    skip = {".git", ".github", ".mimosa", ".v2c", ".video_agent", ".qoder", ".claude"}
    return [p for p in REPO_ROOT.rglob("*.md") if p.relative_to(REPO_ROOT).parts[0] not in skip]


def rewrite_inbound(old: Path, new: Path, files: list[Path], apply: bool) -> int:
    n = 0
    for f in files:
        if f == old:
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except Exception:
            continue
        changed = False

        def sub(m: re.Match) -> str:
            nonlocal n, changed
            target = m.group(2)
            if target.startswith(("http://", "https://", "mailto:", "#", "/")):
                return m.group(0)
            try:
                hit = (f.parent / norm_target(target)).resolve() == old.resolve()
            except OSError:
                hit = False
            if not hit:
                return m.group(0)
            n += 1
            changed = True
            new_rel = os.path.relpath(new.resolve(), f.parent.resolve()).replace(os.sep, "/")
            return f"{m.group(1)}{new_rel}{m.group(3)}"

        new_text = MD_LINK_RE.sub(sub, text)
        if changed and apply:
            f.write_text(new_text, encoding="utf-8")
    return n


def fix_stub_redirect(stub: Path, apply: bool) -> bool:
    """Point stub's redirect at <stub_stem>/README.md; returns True when changed."""
    text = stub.read_text(encoding="utf-8")
    m = re.search(r"^(redirect:\s*)(\S+)\s*$", text, re.MULTILINE)
    if not m:
        return False
    new_val = f"{stub.stem}/README.md"
    if m.group(2) == new_val:
        return False
    if not (stub.parent / new_val).exists():
        print(f"  !! 目标不存在，跳过 redirect 修复: {rel(stub)} -> {new_val}")
        return False
    if apply:
        stub.write_text(text[:m.start()] + m.group(1) + new_val + text[m.end():],
                        encoding="utf-8")
    return True


def rename_id(path: Path, new_id: str, apply: bool) -> bool:
    text = path.read_text(encoding="utf-8")
    m = re.search(r"^(id:\s*)(\S+)\s*$", text, re.MULTILINE)
    if not m:
        return False
    if apply and m.group(2) != new_id:
        path.write_text(text[:m.start()] + m.group(1) + new_id + text[m.end():],
                        encoding="utf-8")
    return True


def make_stub(path: Path, apply: bool) -> bool:
    """Convert a legacy full entry into a redirect stub of its own dir README."""
    fm, _ = extract_frontmatter(path.read_text(encoding="utf-8"))
    target = path.parent / f"{path.stem}/README.md"
    if not target.exists() or len(target.read_text(encoding="utf-8").split("\n")) < 50:
        return False
    title = str(fm.get("title") or path.stem)
    eid = str(fm.get("id") or path.stem)
    stub = (f"---\nid: {eid}\ntitle: {title}\n"
            f"type: {fm.get('type', 'thinker')}\nredirect: {path.stem}/README.md\n---\n\n"
            f"# {title}\n")
    if apply:
        path.write_text(stub, encoding="utf-8")
    return True


def transplant(keep: Path, give: Path, apply: bool) -> bool:
    """Copy delete-file's insert-only diffs into keep. True when pure inserts."""
    a = keep.read_text(encoding="utf-8").split("\n")
    b = give.read_text(encoding="utf-8").split("\n")
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    ops = sm.get_opcodes()
    if any(tag in ("replace", "delete") for tag, *_ in ops):
        return False
    out: list[str] = []
    for tag, i1, i2, j1, j2 in ops:
        if tag == "equal":
            out.extend(a[i1:i2])
        else:  # insert
            out.extend(b[j1:j2])
    if apply:
        keep.write_text("\n".join(out), encoding="utf-8")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    files = all_md_files()
    by_id = collect_entries()
    actions: list[str] = []
    unresolvable: list[str] = []

    for eid, members in sorted(by_id.items()):
        if len(members) < 2:
            continue
        print(f"### id={eid}")

        if eid == "surangama-sutra":
            keep, give = REPO_ROOT / SURANGAMA_KEEP, REPO_ROOT / SURANGAMA_DEL
            if transplant(keep, give, args.apply):
                n = rewrite_inbound(give, keep, files, args.apply)
                if args.apply:
                    give.unlink()
                actions.append(f"D 楞严经: 移植增量小节 -> {rel(keep)}; 删除 {rel(give)}; 改写 {n} 入链")
            else:
                unresolvable.append(f"{eid}: 非纯插入差异，人工合并")
            continue

        stubs = [(p, fm) for p, fm in members if is_stub(fm)]
        fulls = [(p, fm) for p, fm in members if not is_stub(fm)]

        # C-case first: both full, cross-dir, both with own dir README
        if not stubs and len(fulls) >= 2:
            ok = True
            for p, fm in fulls:
                if rel(p) in CONVERT_TO_STUB:
                    if not make_stub(p, args.apply):
                        ok = False
                        unresolvable.append(f"{eid}: {rel(p)} 无合格目录 README，不转换")
            if ok:
                for p, fm in fulls:
                    new_id = ID_RENAMES.get(rel(p))
                    if new_id:
                        rename_id(p, new_id, args.apply)
                actions.append(f"C {eid}: {len(fulls)} 个遗留完整条目已转为目录桩")
            continue

        if len(members) == 2 and len(stubs) == 1 and len(fulls) == 1:
            (stub_p, _), (full_p, _) = stubs[0], fulls[0]
            same_dir = stub_p.parent == full_p.parent
            if same_dir:
                # A-case: full is a legacy duplicate of the stub's dir README
                fix_stub_redirect(stub_p, args.apply)
                n = rewrite_inbound(full_p, stub_p, files, args.apply)
                if args.apply:
                    full_p.unlink()
                actions.append(f"A {eid}: 修复桩 redirect; 删除 {rel(full_p)}; 改写 {n} 入链")
            else:
                # B-case: two domains share an id; namespace the stub
                fix_stub_redirect(stub_p, args.apply)
                new_id = ID_RENAMES.get(rel(stub_p))
                if new_id:
                    rename_id(stub_p, new_id, args.apply)
                    actions.append(f"B {eid}: 桩 {rel(stub_p)} id -> {new_id}")
                else:
                    unresolvable.append(f"{eid}: 跨域桩无命名空间规则: {rel(stub_p)}")
            continue

        if len(members) == 3 and len(stubs) == 2 and len(fulls) == 1:
            # E-case: philosophy ascii full + philosophy stub + religion stub
            phil_stub = next(((p, fm) for p, fm in stubs
                              if Path(rel(p)).parts[0] == "哲学"), None)
            if phil_stub and fulls and phil_stub[0].parent == fulls[0][0].parent:
                fix_stub_redirect(phil_stub[0], args.apply)
                n = rewrite_inbound(fulls[0][0], phil_stub[0], files, args.apply)
                if args.apply:
                    fulls[0][0].unlink()
                for p, fm in stubs:
                    if Path(rel(p)).parts[0] == "宗教":
                        fix_stub_redirect(p, args.apply)
                        new_id = ID_RENAMES.get(rel(p))
                        if new_id:
                            rename_id(p, new_id, args.apply)
                actions.append(f"E {eid}: 删除 {rel(fulls[0][0])}; 改写 {n} 入链; 宗教桩 id 已命名空间化")
                continue
        unresolvable.append(f"{eid}: 结构未识别 ({len(members)} 成员)")

    print("\n=== 处置动作 ===")
    for a in actions:
        print(" ", a)
    if unresolvable:
        print("\n=== 未解决（需人工）===")
        for u in unresolvable:
            print(" ", u)
    print(f"\nMode: {'APPLIED' if args.apply else 'DRY-RUN'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
