# open-cognition MCP Server

把本知识库的 149 个 Skill 与 2650 个条目暴露为 **MCP 工具**，任何支持 Model Context Protocol 的客户端（Claude Code / Claude Desktop / Cursor 等）都可以直接调用。

## 工具一览

| 工具 | 功能 |
|---|---|
| `list_skills(domain?)` | 列出全部/指定领域的 Skill（名称、触发描述、路径） |
| `read_entry(path, section?)` | 读条目全文或某个 `## 小节` |
| `search(query, domain?, type?, limit?)` | 按 id/title/school/tags 子串检索条目 |
| `cross_links(path)` | 解析条目的显式关联类型跨链，返回图谱边表 |
| `apply_skill(skill_id, task)` | 按 AGENT.md 模板 A 拼装可直接执行的 prompt |

所有工具**只读**；`apply_skill` 只做本地拼装，不发起网络请求。

## 安装与运行

```bash
pip install "mcp[cli]"
python mcp/open_cognition_mcp/server.py        # stdio 传输
```

### Claude Code

```bash
claude mcp add open-cognition -- \
  python /绝对路径/open-cognition-database/mcp/open_cognition_mcp/server.py
```

### Claude Desktop（claude_desktop_config.json）

```json
{
  "mcpServers": {
    "open-cognition": {
      "command": "python",
      "args": ["/绝对路径/open-cognition-database/mcp/open_cognition_mcp/server.py"]
    }
  }
}
```

## 测试

查询层不依赖 `mcp` 包，可独立测试：

```bash
python3 mcp/test_queries.py
```
