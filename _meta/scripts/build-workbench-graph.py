#!/usr/bin/env python3
"""
build-workbench-graph.py — 为 工作台/ 生成只读投影 graph.json。

刻意复用 mcp/open_cognition_mcp/queries.py 来实现边表与覆盖率，
这样前端拿到的投影与 MCP 服务永远同源（漂移由契约自检兜底）。
派生数据必须保鲜，因此提供 --check：语义与 build-index.py 一致——
只比较内容，忽略 generated 日期。

Usage:
    python3 _meta/scripts/build-workbench-graph.py           # 写 工作台/graph.json
    python3 _meta/scripts/build-workbench-graph.py --check   # 过期则 exit 1
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "mcp"))

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("ERROR: pyyaml is required. Install with `pip install pyyaml`.")

from open_cognition_mcp import queries  # noqa: E402

DEFAULT_OUT = REPO_ROOT / "工作台" / "graph.json"


def index() -> dict:
    return json.loads((REPO_ROOT / "index.json").read_text(encoding="utf-8"))


def build_edges(idx: dict) -> tuple[list[dict], int, list[str]]:
    """对每个登记条目跑 queries.cross_links（读源 md），汇总全库边表。

    边本身保持与 queries.cross_links() 逐字段同源，不额外加标记位；
    但目标文件不存在的边要单独列出来——工作台的原则是"能点开的才是条目"，
    把断链目标当可达对端展示等于用投影撒谎。
    """
    edges: list[dict] = []
    typed = 0
    for e in idx["entries"] + idx.get("skills", []):
        path = e.get("path")
        if not path or not (REPO_ROOT / path).exists():
            continue
        try:
            found = queries.cross_links(path)
        except (OSError, ValueError):
            continue
        if found:
            typed += 1
        edges.extend(found)
    dangling = sorted({e["target"] for e in edges
                       if not (REPO_ROOT / e["target"]).exists()})
    return sorted(edges, key=lambda x: (x["source"], x["target"], x["relation"])), typed, dangling


def build_eval(skills: list[dict]) -> dict:
    """eval 用例与技能的覆盖关系。用例里的域常缺省，以技能自身的域回填。"""
    by_name = {s.get("name"): s for s in skills}
    by_path = {s.get("path"): s for s in skills}
    cases = []
    covered = set()
    for f in sorted((REPO_ROOT / "eval" / "cases").glob("*.yaml")):
        data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        sid = str(data.get("skill_id") or data.get("skill") or "")
        skill = by_name.get(sid) or by_path.get(sid)
        if skill:
            covered.add(skill.get("name"))
        cases.append({
            "file": f"eval/cases/{f.name}",
            "skill_id": sid,
            "domain": str(data.get("domain") or (skill or {}).get("domain") or ""),
            "resolved": bool(skill),
        })
    domains: dict[str, int] = {}
    for c in cases:
        d = c["domain"] or "（未标注）"
        domains[d] = domains.get(d, 0) + 1
    return {
        "cases": cases,
        "skills_total": len(skills),
        "covered": len(covered),
        "domains": dict(sorted(domains.items(), key=lambda kv: (-kv[1], kv[0]))),
    }


def build_coverage(idx: dict) -> dict:
    entries = idx["entries"]
    tags: set[str] = set()
    for e in entries:
        tags.update(str(t) for t in (e.get("tags") or []))
    return {
        "entries": len(entries),
        "school_filled": sum(1 for e in entries if e.get("school")),
        "tags_filled": sum(1 for e in entries if e.get("tags")),
        "unique_tags": len(tags),
        "skills": len(idx.get("skills", [])),
    }


def build_graph() -> dict:
    idx = index()
    edges, typed, dangling = build_edges(idx)
    return {
        "version": idx.get("version"),
        "generated": idx.get("generated"),
        "projection": date.today().isoformat(),
        "typed_entries": typed,
        "dangling": dangling,
        "edges": edges,
        "eval": build_eval(queries.list_skills()),
        "coverage": build_coverage(idx),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="生成/校验 工作台只读投影")
    ap.add_argument("--out", default=DEFAULT_OUT, type=Path)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    payload = json.dumps(build_graph(), ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if not args.out.exists():
            print(f"MISSING: {args.out}", file=sys.stderr)
            return 2
        strip = lambda o: {k: v for k, v in o.items() if k != "projection"}
        try:
            current = strip(json.loads(args.out.read_text(encoding="utf-8")))
            same = current == strip(json.loads(payload))
        except json.JSONDecodeError:
            same = False
        if same:
            print(f"OK: {args.out} 与源一致")
            return 0
        print(f"STALE: {args.out} — 运行 python3 _meta/scripts/build-workbench-graph.py",
              file=sys.stderr)
        return 1
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(payload, encoding="utf-8")
    g = json.loads(payload)
    print(f"Wrote {args.out}: {len(g['edges'])} edges / {g['typed_entries']} typed entries; "
          f"eval {g['eval']['covered']}/{g['eval']['skills_total']}; "
          f"dangling targets {len(g['dangling'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
