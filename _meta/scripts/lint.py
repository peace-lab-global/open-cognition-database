#!/usr/bin/env python3
"""
lint.py — quality checks for open-cognition markdown entries.

Usage:
    python3 _meta/scripts/lint.py                   # lint all entry files
    python3 _meta/scripts/lint.py path/to/file.md   # lint specific file(s)
    python3 _meta/scripts/lint.py --strict          # fail on warnings too
    python3 _meta/scripts/lint.py --json            # emit JSON for CI

Checks performed:
    1. Frontmatter: required fields by entry type
    2. Section presence: required H2 headings by entry type
    3. Line length: too short (<40) or too long (>600)
    4. Broken relative links:
         E003 (error)   — target exists in the repo but the link path is wrong
         W006 (warning) — target basename exists nowhere; entry not authored yet
                          (content backlog, tracked in reports/audit/, non-blocking)
    5. Tags: at least 1 tag on thinker/concept entries
    6. Cross-domain links: at least 1 link to another domain
    7. E004 (error) — the same frontmatter `id` declared by multiple entry
         files (double source of truth; child pages exempt)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("ERROR: pyyaml required. Install with `pip install pyyaml`.")


REPO_ROOT = Path(__file__).resolve().parent.parent.parent

SKIP_FILENAMES = {"README.md", "INDEX.md", "QUICKSTART.md", "SKILLS.md", "AGENT.md"}

_DOMAIN_DIR_NAMES = [
    "哲学", "宗教", "伦理政治", "心理学", "社会学", "美学",
    "文学", "艺术", "认知系统", "清单", "研究", "TECH",
]
_DOMAIN_DIRS = [REPO_ROOT / d for d in _DOMAIN_DIR_NAMES]

REQUIRED_FRONTMATTER = {
    # thinker: accept either `name` (Chinese + English) or `title` for legacy entries
    "thinker": ["id", "type", "domain", "school", "era", "tags"],
    "concept": ["id", "title", "type", "domain", "school", "era", "tags"],
    "skill":   ["name", "description", "domain", "tags"],
    "text":    ["id", "title", "type", "domain"],
    "tradition": ["id", "title", "type", "domain"],
    "school":  ["id", "title", "type", "domain", "era", "tags"],
    "list":    ["id", "title", "type", "channel", "category", "angle", "count", "tags"],
    # child pages attached to thinkers/schools/concepts: minimal metadata
    "child":   ["id", "title", "type"],
    "redirect": ["id", "title", "type"],
}

# Thinker entries must have either `name` or `title`
THINKER_NAME_OR_TITLE = True

REQUIRED_SECTIONS = {
    "thinker": ["核心命题", "关键著作", "跨学科关联", "进阶阅读"],
    "concept": ["一句话定义", "核心要义", "常见误读", "跨学科关联", "进阶阅读"],
    "school":  ["一句话定义", "历史脉络", "核心主张", "常见误读", "跨学科关联", "进阶阅读"],
    "skill":   ["何时使用", "何时不使用", "操作流程"],
    "list":    ["盘点逻辑", "清单", "常见误读", "跨学科关联", "进阶阅读"],
    "child":   [],
}


def is_child_page(path: Path) -> bool:
    """Return True for supplementary pages attached to a parent entry.

    These pages (timeline, works, reading-list, concept notes, dialogues, etc.)
    are not standalone entries and are held to lighter frontmatter/section rules.
    SKILL.md files are full skill entries and handled by the skill type.
    """
    rel = path.relative_to(REPO_ROOT).as_posix()
    name = path.name
    if name == "SKILL.md":
        return False
    if name in {"时间线.md", "著作.md", "阅读.md", "README.md", "速读.md", "内容审计.md"}:
        return True
    if "/概念/" in rel or "/concepts/" in rel:
        return True
    if "/对话/" in rel or "/dialogues/" in rel:
        return True
    if "/批评/" in rel or "/critiques/" in rel:
        return True
    return False

MIN_LINES = 40
MAX_LINES = 600

MD_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

# Index every .md file by basename once at import time. Used to distinguish a
# structurally-broken link (target exists somewhere, path is wrong → E003 error)
# from a link to an entry that has not been authored yet (→ W006 warn, content
# backlog, does not block CI).
ALL_FILES_BY_NAME: dict[str, list[Path]] = {}
for _domain_dir in _DOMAIN_DIRS:
    if not _domain_dir.exists():
        continue
    for _p in _domain_dir.rglob("*.md"):
        ALL_FILES_BY_NAME.setdefault(_p.name, []).append(_p)


@dataclass
class Finding:
    file: Path
    line: int
    severity: str  # "error" or "warn"
    code: str
    message: str


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)

    def add(self, f: Finding) -> None:
        self.findings.append(f)

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == "error"]

    @property
    def warns(self) -> list[Finding]:
        return [f for f in self.findings if f.severity == "warn"]


def extract_frontmatter(text: str) -> tuple[dict, int]:
    """Return (parsed fm, line-number where body starts)."""
    if not text.startswith("---"):
        return {}, 1
    try:
        end = text.index("---", 3)
    except ValueError:
        return {}, 1
    fm_text = text[3:end]
    try:
        fm = yaml.safe_load(fm_text) or {}
    except yaml.YAMLError:
        fm = {}
    body_start = text.count("\n", 0, end) + 2  # +1 for the `---`, +1 to move past
    return fm, body_start


def classify(path: Path) -> str | None:
    rel = path.relative_to(REPO_ROOT).as_posix()
    # Reports/audit files are not entries — skip them.
    if "/reports/" in rel or "/审计/" in rel or "/内容审计/" in rel:
        return None

    # Supplementary child pages are held to lighter rules, even if they
    # declare a stricter type in frontmatter (e.g. a concept note under a
    # thinker directory should not be linted as a standalone concept).
    if is_child_page(path):
        return "child"

    # Prefer explicit type declared in frontmatter.
    known_types = set(REQUIRED_FRONTMATTER.keys())
    text = path.read_text(encoding="utf-8")
    fm, _ = extract_frontmatter(text)
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


def lint_file(path: Path, report: Report) -> None:
    if not path.exists():
        report.add(Finding(path, 0, "error", "E000", f"file does not exist: {path}"))
        return

    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")
    line_count = len(lines)

    # Classify first: only entry files (thinker/concept/skill/...) are subject
    # to the per-entry checks below. Non-entry files living under domains/ (e.g.
    # a report dropped into domains/.../reports/) are skipped for frontmatter
    # and section checks. They still get the line-length advisory.
    entry_type = classify(path)

    # --- Line length (advisory for all files) ---
    if line_count < MIN_LINES:
        report.add(Finding(path, 1, "warn", "W001", f"too short ({line_count} < {MIN_LINES} lines)"))
    if line_count > MAX_LINES:
        report.add(Finding(path, 1, "warn", "W002", f"too long ({line_count} > {MAX_LINES} lines)"))

    if entry_type is None:
        return  # non-entry file (README, report, etc.)

    # --- Frontmatter (entries only) ---
    fm, body_start = extract_frontmatter(text)
    if not fm:
        report.add(Finding(path, 1, "error", "E001", "missing or invalid YAML frontmatter"))
        return

    # Redirect stubs point to the full entry; they only need id/title/type/redirect_to.
    if fm.get("redirect_to") or fm.get("redirect"):
        entry_type = "redirect"

    # Required fields
    for field_name in REQUIRED_FRONTMATTER.get(entry_type, []):
        if field_name not in fm or fm[field_name] in (None, "", []):
            report.add(Finding(path, 1, "error", "E002",
                               f"frontmatter missing required field: {field_name}"))

    # Thinker: must have either `name` or `title`
    if entry_type == "thinker" and not (fm.get("name") or fm.get("title")):
        report.add(Finding(path, 1, "error", "E002",
                           "thinker frontmatter needs either `name` or `title`"))

    # Tags
    tags = fm.get("tags")
    if not tags and entry_type not in ("child", "redirect"):
        report.add(Finding(path, 1, "warn", "W003", "no tags"))

    # --- Required sections ---
    h2s = [m.group(1) for m in re.finditer(r"^## (.+)$", text, re.MULTILINE)]
    for required in REQUIRED_SECTIONS.get(entry_type, []):
        if not any(required in h for h in h2s):
            report.add(Finding(path, 1, "warn", "W004", f"missing section: {required}"))

    # --- Relative link validity ---
    # Two failure modes:
    #   E003 (error, blocks CI): the target EXISTS somewhere in the repo but
    #     this link's path is wrong — a mechanical defect that should be fixed.
    #   W006 (warn): the target basename exists NOWHERE in the repo, meaning the
    #     linked concept/thinker has not been authored yet. This is a content
    #     backlog item (tracked in reports/audit/*-content-backlog.md), not a
    #     structural defect, so it warns rather than blocking CI.
    for i, line in enumerate(lines, start=1):
        for m in MD_LINK_RE.finditer(line):
            target = m.group(2)
            # Skip http(s), mailto, anchor-only, and absolute paths
            if target.startswith(("http://", "https://", "mailto:", "#", "/")):
                continue
            # Resolve relative to file's directory
            resolved = (path.parent / target).resolve()
            if resolved.exists():
                continue
            target_name = Path(target).name
            # Special case: SKILL.md targets share one basename across 100+ skill
            # dirs. The meaningful existence check is whether the *parent skill
            # dir* exists anywhere under skills/. If not, the skill itself has not
            # been authored → W006 content backlog, not E003 structural error.
            if target_name == "SKILL.md":
                skill_dir = Path(target).parent.name
                skills_root = REPO_ROOT / "skills"
                if skill_dir and (
                    not skills_root.exists()
                    or not any(
                        (skills_root / fw / skill_dir).exists()
                        for fw in (p.name for p in skills_root.iterdir()
                                   if p.is_dir())
                    )
                ):
                    report.add(Finding(path, i, "warn", "W006",
                                       f"link to unauthored skill: {target}"))
                    continue
            if ALL_FILES_BY_NAME and target_name in ALL_FILES_BY_NAME:
                # Path-aware disambiguation: even when the basename exists, the
                # link may name a sub-path (e.g. education/schools/.../piaget.md,
                # traditions/buddhism/core-teachings.md) that exists nowhere. If
                # no candidate shares the link's penultimate path segment, the
                # intended target is genuinely missing → W006, not E003.
                penult = Path(target).parent.name
                candidates = ALL_FILES_BY_NAME[target_name]
                if penult and not any(
                    penult == c.parent.name or penult in c.parent.as_posix()
                    for c in candidates
                ):
                    report.add(Finding(path, i, "warn", "W006",
                                       f"link to unauthored entry: {target}"))
                else:
                    report.add(Finding(path, i, "error", "E003",
                                       f"broken relative link: {target}"))
            else:
                report.add(Finding(path, i, "warn", "W006",
                                   f"link to unauthored entry: {target}"))

    # --- Cross-links (for thinker/concept) ---
    # Accept any relative link to another .md file as a cross-link
    if entry_type in ("thinker", "concept"):
        has_cross = False
        for line in lines:
            for m in MD_LINK_RE.finditer(line):
                target = m.group(2)
                if target.startswith(("http://", "https://", "mailto:", "#", "/")):
                    continue
                if target.endswith(".md"):
                    has_cross = True
                    break
            if has_cross:
                break
        if not has_cross:
            report.add(Finding(path, 1, "warn", "W005",
                               "no cross-link to another .md file detected"))


def check_duplicate_ids(files: list[Path], report: Report) -> None:
    """E004 — the same frontmatter `id` declared by more than one entry file.

    Duplicates make index.json list an entry twice and let two copies of the
    same entry diverge silently (double source of truth). Child pages are
    exempt: their ids are namespaced per parent and may legitimately repeat.
    """
    by_id: dict[str, list[Path]] = {}
    for path in files:
        text = path.read_text(encoding="utf-8")
        fm, _ = extract_frontmatter(text)
        if not fm or is_child_page(path):
            continue
        if fm.get("type") not in REQUIRED_FRONTMATTER:
            continue
        entry_id = fm.get("id")
        if entry_id:
            by_id.setdefault(str(entry_id), []).append(path)
    for entry_id, paths in sorted(by_id.items()):
        if len(paths) > 1:
            for path in paths:
                others = ", ".join(
                    str(p.relative_to(REPO_ROOT)) for p in paths if p != path
                )
                report.add(Finding(path, 1, "error", "E004",
                                   f"duplicate id `{entry_id}` also declared by: {others}"))


def collect_files(targets: list[Path]) -> list[Path]:
    if targets:
        return [p.resolve() for p in targets if p.exists()]
    files = []
    for domain_dir in _DOMAIN_DIRS:
        if not domain_dir.exists():
            continue
        for path in sorted(domain_dir.rglob("*.md")):
            if path.name in SKIP_FILENAMES:
                continue
            if classify(path) is None:
                continue
            files.append(path)
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path, help="Files to lint")
    parser.add_argument("--strict", action="store_true",
                        help="Fail on warnings too")
    parser.add_argument("--json", action="store_true",
                        help="Emit JSON output")
    parser.add_argument("--quiet", action="store_true",
                        help="Only print findings")
    args = parser.parse_args()

    report = Report()
    files = collect_files(args.paths)

    for path in files:
        lint_file(path, report)

    check_duplicate_ids(files, report)

    if args.json:
        out = {
            "files_scanned": len(files),
            "errors": len(report.errors),
            "warns": len(report.warns),
            "findings": [
                {
                    "file": str(f.file.relative_to(REPO_ROOT)),
                    "line": f.line,
                    "severity": f.severity,
                    "code": f.code,
                    "message": f.message,
                }
                for f in report.findings
            ],
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 1 if report.errors else (1 if args.strict and report.warns else 0)

    # Human-readable output
    if not args.quiet:
        print(f"Linted {len(files)} files")

    if not report.findings:
        print("✓ clean")
        return 0

    for f in sorted(report.findings, key=lambda x: (str(x.file), x.line)):
        rel = f.file.relative_to(REPO_ROOT)
        marker = "✗" if f.severity == "error" else "⚠"
        print(f"{marker} {rel}:{f.line} [{f.code}] {f.message}")

    print(f"\n{len(report.errors)} error(s), {len(report.warns)} warning(s)")
    if report.errors:
        return 1
    return 1 if args.strict and report.warns else 0


if __name__ == "__main__":
    raise SystemExit(main())
