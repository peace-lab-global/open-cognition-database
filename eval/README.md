# Skill 评测框架

> 目标：把"137 个 Skill 结构完整"升级为"**经过验证可正确引导 LLM 执行**"。
> 每个 Skill 配至少 1 个用例：真实感任务 + 期望要点（must_hit）+ 禁止项（must_avoid）。

## 运行

```bash
# 1. 只验证用例格式与 prompt 拼装（不需要 API key）
python3 eval/run_eval.py --dry

# 2. 真实评测：走任意 OpenAI 兼容端点
export OPENAI_BASE_URL=https://api.openai.com/v1
export OPENAI_API_KEY=sk-...
export OPENAI_MODEL=gpt-4o-mini        # 任意兼容模型名
python3 eval/run_eval.py               # 全量
python3 eval/run_eval.py --only 认知扭曲识别   # 单个
```

结果写入 `eval/results/report-<日期>.md` 与 `.json`。

## 判分规则

自动部分（run_eval.py）：
- `must_hit`：输出的前 1200 字内应出现的关键词/结构（按小写包含匹配；中文原样匹配）。
- `must_avoid`：不应出现的失败模式（如"鸡汤式安慰"替代了框架步骤）。
- 通过 = must_hit 全部命中 且 must_avoid 零命中。

人工复核（建议）：步骤是否真的被遵循、判断依据是否具体。判分只是初筛，**发布"已验证"标记前须人工抽查 10%**。

## 用例文件格式（eval/cases/*.yaml）

```yaml
skill: 认知扭曲识别          # 与 SKILL.md 目录名/frontmatter name 对应
task: |
  （真实感的用户输入）
must_hit: [关键词1, 关键词2]
must_avoid: [失败模式]
notes: 人工复核要点
```

## 覆盖进度

- [x] 先导批次：10 个代表性 Skill（通用/佛教/CSE 三类各取若干）
- [ ] 全量 137 个
