"""test_queries.py — queries 层单元测试（不依赖 mcp 包）。

    python3 mcp/test_queries.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from open_cognition_mcp import queries  # noqa: E402

failures = []


def check(name, cond, detail=""):
    status = "✓" if cond else "✗"
    print(f"{status} {name}" + (f" — {detail}" if detail and not cond else ""))
    if not cond:
        failures.append(name)


def main():
    st = queries.stats()
    check("stats.entries >= 2600", st.get("entries", 0) >= 2600, str(st))
    check("stats.skills >= 137", st.get("skills", 0) >= 137, str(st))

    skills = queries.list_skills()
    check("list_skills 与 stats.skills 一致",
          len(skills) == st.get("skills"), f"{len(skills)} vs {st.get('skills')}")
    check("list_skills 全量唯一 name",
          len({s["name"] for s in skills}) == len(skills))
    check("skill 条目含 name/description/path",
          all(k in skills[0] for k in ("name", "description", "path")))
    cbt = queries.get_skill("认知扭曲识别")
    check("get_skill 中文名命中", cbt is not None and "认知扭曲识别" in cbt["path"])

    text = queries.read_entry("心理学/概念/心流.md", section="一句话定义")
    check("read_entry 取节", "心流" in text and "## " not in text.split("\n", 1)[1])

    try:
        queries.read_entry("../outside.md")
        check("路径逃逸被拒", False)
    except ValueError:
        check("路径逃逸被拒", True)

    hits = queries.search("心流", type="concept")
    check("search 命中概念", any("心流" in h["title"] for h in hits), str(hits[:2]))

    edges = queries.cross_links("哲学/学派/东方哲学/孔子.md")
    check("cross_links 解析关联类型",
          len(edges) >= 1 and all(e["relation"] for e in edges),
          str(edges[:2]))

    prompt = queries.apply_skill("认知扭曲识别", "分析这段独白：我什么都做不好。")
    check("apply_skill 拼装 prompt",
          "<skill>" in prompt and "我什么都做不好" in prompt and "反例" in prompt)

    print()
    if failures:
        print(f"FAILED: {failures}")
        return 1
    print("all tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
