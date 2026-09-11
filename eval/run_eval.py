"""run_eval.py — Skill 评测执行器。

  python3 eval/run_eval.py --dry           # 只验证用例与 prompt 拼装
  python3 eval/run_eval.py [--only <skill 名片段>]

需要 OpenAI 兼容端点：OPENAI_BASE_URL / OPENAI_API_KEY / OPENAI_MODEL。
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sys
import urllib.request
from pathlib import Path

import yaml

EVAL_DIR = Path(__file__).resolve().parent
REPO_ROOT = EVAL_DIR.parent
sys.path.insert(0, str(REPO_ROOT / "mcp"))

from open_cognition_mcp import queries  # noqa: E402


def load_cases(only: str | None):
    cases = []
    for f in sorted((EVAL_DIR / "cases").glob("*.yaml")):
        case = yaml.safe_load(f.read_text(encoding="utf-8"))
        case["_file"] = f.name
        if only and only not in case.get("skill", ""):
            continue
        cases.append(case)
    return cases


def call_model(prompt: str) -> str:
    base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    key = os.environ["OPENAI_API_KEY"]
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
    }).encode()
    req = urllib.request.Request(
        f"{base}/chat/completions", data=body,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.load(resp)
    return data["choices"][0]["message"]["content"]


def grade(case: dict, output: str) -> tuple[bool, list[str], list[str]]:
    head = output[:1200].lower()
    out_low = output.lower()
    missed = [k for k in case.get("must_hit", [])
              if str(k).lower() not in head and str(k).lower() not in out_low]
    violated = [k for k in case.get("must_avoid", [])
                if str(k).lower() in out_low]
    return (not missed and not violated), missed, violated


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--only", default=None)
    args = ap.parse_args()

    cases = load_cases(args.only)
    if not cases:
        print("no cases matched")
        return 1

    results, failed = [], 0
    for case in cases:
        skill = case["skill"]
        try:
            prompt = queries.apply_skill(skill, case["task"])
        except Exception as e:
            print(f"✗ {skill}: prompt 拼装失败 {e}")
            failed += 1
            continue
        if args.dry:
            print(f"✓ {skill}: prompt 拼装 OK（{len(prompt)} 字符）")
            continue
        output = call_model(prompt)
        ok, missed, violated = grade(case, output)
        status = "✓" if ok else "✗"
        print(f"{status} {skill}" + ("" if ok else f" 缺 {missed} / 触发禁止 {violated}"))
        results.append({"skill": skill, "ok": ok,
                        "missed": missed, "violated": violated,
                        "output": output})
        failed += 0 if ok else 1

    if args.dry:
        print(f"\n{len(cases)} 个用例格式与拼装全部通过")
        return 0

    day = _dt.date.today().isoformat()
    (EVAL_DIR / "results").mkdir(exist_ok=True)
    (EVAL_DIR / "results" / f"report-{day}.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [f"# Skill 评测报告 {day}", "",
             f"- 用例数：{len(cases)}　通过：{len(cases) - failed}　失败：{failed}", ""]
    for r in results:
        mark = "✅" if r["ok"] else "❌"
        lines.append(f"- {mark} **{r['skill']}**"
                     + ("" if r["ok"] else f"（缺 {r['missed']}；触发 {r['violated']}）"))
    (EVAL_DIR / "results" / f"report-{day}.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n报告已写入 eval/results/report-{day}.md")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
