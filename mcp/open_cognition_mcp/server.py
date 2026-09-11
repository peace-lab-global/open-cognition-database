"""server.py — open-cognition MCP server（FastMCP 封装）。

安装与运行见 mcp/README.md。所有工具都是只读的；apply_skill 只拼装
prompt，不发起任何网络请求。

    pip install "mcp[cli]"
    python mcp/open_cognition_mcp/server.py          # stdio 传输

Claude Code 注册：
    claude mcp add open-cognition -- python /path/to/repo/mcp/open_cognition_mcp/server.py
"""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from open_cognition_mcp import queries

mcp = FastMCP("open-cognition")


@mcp.tool()
def list_skills(domain: str | None = None) -> list[dict]:
    """列出知识库的操作框架（Skill）。domain 可传中文域名或英文别名（如 宗教 / religion）。"""
    return queries.list_skills(domain)


@mcp.tool()
def read_entry(path: str, section: str | None = None) -> str:
    """读取一个条目（相对仓库根的路径，如 心理学/概念/心流.md），可用 section 只取某个 `## 小节`。"""
    return queries.read_entry(path, section)


@mcp.tool()
def search(query: str, domain: str | None = None, type: str | None = None,
           limit: int = 20) -> list[dict]:
    """按关键词检索条目（匹配 id/title/school/tags），可按 domain 与 type（thinker/concept/skill/list）过滤。"""
    return queries.search(query, domain, type, limit)


@mcp.tool()
def cross_links(path: str) -> list[dict]:
    """解析条目的显式关联类型跨链（[同源]/[互补]/[对立]…），返回知识图谱边表。"""
    return queries.cross_links(path)


@mcp.tool()
def apply_skill(skill_id: str, task: str) -> str:
    """把指定 Skill 的 SKILL.md 与用户任务拼装成可直接执行的 prompt（按 AGENT.md 模板 A）。"""
    return queries.apply_skill(skill_id, task)


if __name__ == "__main__":
    mcp.run(transport="stdio")
