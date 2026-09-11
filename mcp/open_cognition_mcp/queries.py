"""queries.py — 纯函数查询层，供 MCP server 与测试复用。

不依赖任何第三方包：只读 index.json 与仓库内 markdown 文件。
所有路径入参一律相对仓库根（与 index.json 中的 `path` 一致）。
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
INDEX_PATH = REPO_ROOT / "index.json"

# 带关联类型的跨链：[标签](路径) `[类型]`（允许全角/直角引号）
CROSS_LINK_RE = re.compile(
    r"\[([^\]]+)\]\(([^)]+\.md)\)\s*[`「]\[([^\]]+)\][`」]"
)


@lru_cache(maxsize=1)
def _load_index() -> dict:
    with INDEX_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def repo_root() -> Path:
    return REPO_ROOT


def stats() -> dict:
    d = _load_index()
    return d["stats"]


def list_skills(domain: str | None = None) -> list[dict]:
    """列出 Skill（来自 index.json 顶层 skills 数组，含 name/description/domain/tags）。"""
    skills = _load_index().get("skills", [])
    if domain:
        dl = domain.lower()
        skills = [s for s in skills
                  if dl in str(s.get("domain", "")).lower()
                  or dl in {str(t).lower() for t in s.get("tags", [])}]
    return skills


def get_skill(skill_id: str) -> dict | None:
    """按 name（skill-id）或路径片段定位一个 Skill。"""
    for s in _load_index().get("skills", []):
        if s.get("name") == skill_id or skill_id in str(s.get("path", "")):
            return s
    return None


def read_entry(path: str, section: str | None = None) -> str:
    """读取条目全文或其中某个 `## 小节`。路径必须落在仓库根之内。"""
    p = (REPO_ROOT / path).resolve()
    if not str(p).startswith(str(REPO_ROOT)):
        raise ValueError(f"path escapes repo root: {path}")
    if not p.exists():
        raise FileNotFoundError(f"entry not found: {path}")
    text = p.read_text(encoding="utf-8")
    if section:
        m = re.search(
            rf"(?ms)^## {re.escape(section)}.*?(?=^## |\Z)", text)
        if not m:
            raise ValueError(f"section not found: {section}")
        return m.group(0).rstrip() + "\n"
    return text


def search(query: str, domain: str | None = None, type: str | None = None,
           limit: int = 20) -> list[dict]:
    """在 index.json 的 id/title/school/tags 上做子串检索。"""
    q = query.lower()
    hits = []
    for e in _load_index()["entries"]:
        if domain and e.get("domain") != domain:
            continue
        if type and e.get("type") != type:
            continue
        hay = " ".join(str(e.get(k, "")) for k in ("id", "title", "school"))
        hay += " " + " ".join(str(t) for t in e.get("tags", []))
        if q in hay.lower():
            hits.append({k: e.get(k) for k in
                         ("path", "id", "title", "type", "domain")})
        if len(hits) >= limit:
            break
    return hits


def cross_links(path: str) -> list[dict]:
    """解析条目的显式关联类型跨链，返回边表 [{source, target, relation, label}]。"""
    text = read_entry(path)
    base = (REPO_ROOT / path).parent
    edges = []
    for m in CROSS_LINK_RE.finditer(text):
        label, target, relation = m.group(1), m.group(2), m.group(3)
        resolved = (base / target).resolve()
        try:
            rel = resolved.relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel = target
        edges.append({"source": path, "target": rel,
                      "relation": relation, "label": label.strip()})
    return edges


def apply_skill(skill_id: str, task: str) -> str:
    """按 AGENT.md 模板 A 拼装可直接投喂 LLM 的 prompt。"""
    skill = get_skill(skill_id)
    if skill is None:
        raise ValueError(f"skill not found: {skill_id}")
    skill_text = read_entry(skill["path"])
    return (
        "你是相关领域的认知助手。请严格按以下 Skill 的「操作流程」执行任务。\n\n"
        f"<skill>\n{skill_text}\n</skill>\n\n"
        f"<task>\n{task}\n</task>\n\n"
        "输出要求：\n"
        "1. 按 Step 1 → Step N 顺序推进，每步明确写出判断依据\n"
        "2. 使用 Skill 中的「提问范式」生成问题\n"
        "3. 在「完整示例」的格式下给出输出\n"
        "4. 末尾附「反例（误用）」警告\n"
    )
