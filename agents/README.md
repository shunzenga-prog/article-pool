# Agents 配置说明

Article Pool 包含 4 个独立 Agent，由 `skills/article-pipeline/SKILL.md` 编排调用。

## 已实施的 Agent（硬约束）

| Agent | 文件 | 硬约束 |
|-------|------|--------|
| 🔍 审阅 Agent | `article-pool/review-agent.md` | HTML 结构扫描（table/div 数量、样式位置），硬检查失败 = 驳回 |
| 🎨 封面 Agent | `article-pool/cover-agent.md` | 强制 auto 模式，绝不用 geometric，验证 >100KB |
| 🚀 发布 Agent | `article-pool/publish-agent.md` | Windows PYTHONIOENCODING=utf-8，必须见 ✅ + draft ID，自动入库 |

## 编排流程

```
Stage 0-3 (AI语义)  →  Stage 4 审阅Agent  →  Stage 4.8 封面Agent  →  Stage 5-6 (AI语义)  →  Stage 8 发布Agent
                           ↑___(fail→修复→重审)___↓
```

## Agent 定义格式

每个 Agent 是一个 Markdown 文件，包含：
- YAML frontmatter：name, description, tools, color
- Prompt 正文：职责、硬约束、执行命令、输出格式

## 使用方式

通过 `skills/article-pipeline/SKILL.md` 自动调用，无需手动配置。

```bash
# 触发创作链路
"创作一篇公众号文章"
```
