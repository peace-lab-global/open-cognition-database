#!/usr/bin/env python3
"""
test_workbench.py — 校验 工作台/index.html 的前端纯函数与 queries.py 逐字一致。

两步：
  1. 由 Python 侧（唯一权威）生成契约夹具 mcp/fixtures/workbench-parity.json；
     --check 时不写文件，只比较现有夹具是否等于当前真值。
  2. 用 node --test 跑 mcp/tests/，让前端 core 重放同一夹具并断言相等。

Usage:
    python3 mcp/test_workbench.py           # 刷新夹具 + 跑 node
    python3 mcp/test_workbench.py --check  # CI：夹具过期或前端漂移则 exit 1
    python3 mcp/test_workbench.py --python-only
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "mcp"))

from open_cognition_mcp import queries  # noqa: E402

FIXTURE = REPO_ROOT / "mcp" / "fixtures" / "workbench-parity.json"
QUERIES = ["异化", "ALIENATION", "wuwei", "场域", "zzz-不存在"]
SKILLS = ["cbt-cognitive-distortion", "qichu-zhengxin-deconstruction",
          "madhyamaka-four-fallacies", "bourdieu-field-analysis"]
TASK = "我连续三周在评审会上说不出反驳意见，回家又觉得自己错了。"

failures: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"{'ok' if ok else 'FAIL'}   {label}" + (f"  — {detail}" if detail and not ok else ""))
    if not ok:
        failures.append(label)


def build_fixture() -> dict:
    idx = json.loads((REPO_ROOT / "index.json").read_text(encoding="utf-8"))
    fx: dict = {
        "version": idx["version"],
        "stats": idx["stats"],
        "search": {q: queries.search(q) for q in QUERIES},
        "search_filtered": {
            "哲学/concept/5": queries.search("概念", domain="哲学", type="concept", limit=5),
        },
        "apply_skill": [],
        "list_skills": {},
        "cross_links": [],
    }
    for sid in SKILLS:
        skill = queries.get_skill(sid)
        if skill is None:
            raise SystemExit(f"fixture 需要技能存在于登记册: {sid}")
        fx["apply_skill"].append({
            "skill_id": sid, "path": skill["path"], "task": TASK,
            "prompt": queries.apply_skill(sid, TASK),
        })
    for s in idx["skills"]:
        d = s.get("domain") or ""
        fx["list_skills"][d] = fx["list_skills"].get(d, 0) + 1
    # 跨链样本：取第一条含类型互链的条目。queries.cross_links 解析的是全文，
    # 所以夹具必须存全文——截断会让位于截断点之后的边在前端重放中消失。
    for e in idx["entries"]:
        edges = queries.cross_links(e["path"])
        if edges:
            text = queries.read_entry(e["path"])
            fx["cross_links"].append({
                "entry_path": e["path"],
                "md_text": text,
                "edges": edges,
            })
            break
    return fx


def run_node() -> int:
    # 显式展开 *.test.mjs：目录形式 `node --test mcp/tests` 在部分 Node 版本里被当成模块路径。
    files = sorted(str(p) for p in (REPO_ROOT / "mcp" / "tests").glob("*.test.mjs"))
    return subprocess.call(["node", "--test", *files], cwd=str(REPO_ROOT))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--python-only", action="store_true")
    args = ap.parse_args()

    fx = build_fixture()
    payload = json.dumps(fx, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        current = FIXTURE.read_text(encoding="utf-8") if FIXTURE.exists() else ""
        same = current == payload
        check("夹具等于当前 Python 真值", same, "夹具过期：运行 python3 mcp/test_workbench.py")
    else:
        FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE.write_text(payload, encoding="utf-8")
        check("夹具已生成", True, str(FIXTURE.relative_to(REPO_ROOT)))
    check("stats 三数自洽", fx["stats"]["total"] == fx["stats"]["entries"] + fx["stats"]["skills"])
    check("search 返回条目的键集合固定", all(
        set(h) == {"path", "id", "title", "type", "domain"}
        for hits in fx["search"].values() for h in hits))
    check("apply_skill 均非空且以换行结尾", all(
        a["prompt"].endswith("\n") and "<skill>" in a["prompt"] for a in fx["apply_skill"]))
    check("cross_links 样本含边", bool(fx["cross_links"]) and bool(fx["cross_links"][0]["edges"]))

    if failures:
        return 1
    if args.python_only:
        return 0
    return run_node()


if __name__ == "__main__":
    raise SystemExit(main())
