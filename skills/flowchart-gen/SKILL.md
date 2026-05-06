---
name: flowchart-gen
description: 流程图生成技能。将流水线/架构/流程描述转换为 Mermaid 流程图，通过 Playwright 渲染为 PNG 配图。触发：画流程图、架构全景、流水线图、流程示意。
---

# 流程图生成（Flowchart Gen）

为教程文章、技术文档生成专业流程图。基于 Mermaid.js 自动布局，Playwright 渲染为高分辨率 PNG。

## 触发场景

- "画一个流程图"
- "把这个架构画成图"
- "流水线示意图"
- "架构全景"
- 教程中包含多步骤流程

## 输入格式

JSON 描述，支持以下字段：

```json
{
  "direction": "LR",
  "title": "可选标题",
  "nodes": [
    {"id": "fetch", "label": "1. 抓取", "desc": "Hacker News API\n免费 JSON 接口"},
    {"id": "process", "label": "2. 处理", "desc": "自动分类\n热度排序"},
    {"id": "output", "label": "3. 输出", "desc": "HTML 日报"}
  ],
  "edges": [
    {"from": "fetch", "to": "process", "label": "数据流"},
    {"from": "process", "to": "output"}
  ]
}
```

### 字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| `direction` | ✅ | `LR`（左→右）或 `TB`（上→下） |
| `title` | - | 图表标题（可选） |
| `nodes[].id` | ✅ | 唯一标识符（英文） |
| `nodes[].label` | ✅ | 节点标题（支持中文） |
| `nodes[].desc` | - | 节点描述（`\n` 换行） |
| `nodes[].shape` | - | `rounded`（默认）、`rectangle`、`stadium`、`diamond`（决策）、`hexagon`、`cylinder`、`subroutine` |
| `edges[].from` | ✅ | 起点节点 ID |
| `edges[].to` | ✅ | 终点节点 ID |
| `edges[].label` | - | 连接线标签 |
| `edges[].style` | - | `arrow`（默认实线箭头）、`dashed`（虚线）、`thick`（粗线） |

### 节点形状速查

| shape | 用途 | Mermaid 语法 |
|-------|------|-------------|
| `rounded` | 流程步骤（默认） | `id("text")` |
| `rectangle` | 数据/文件 | `id["text"]` |
| `stadium` | 起点/终点 | `id(["text"])` |
| `diamond` | 决策/分支 | `id{"text"}` |
| `hexagon` | 准备工作 | `id{{"text"}}` |
| `cylinder` | 数据库/存储 | `id[("text")]` |
| `subroutine` | 子流程 | `id[["text"]]` |

## CLI 用法

```bash
# JSON 文件输入
python scripts/flowchart_gen.py --file flow.json -o flowchart.png

# 内联 JSON 输入
python scripts/flowchart_gen.py --inline '{"direction":"LR","nodes":[...],"edges":[...]}' -o chart.png

# 指定主题
python scripts/flowchart_gen.py --file flow.json -o chart.png --theme github

# 自定义宽度（默认 670px，公众号最佳宽度）
python scripts/flowchart_gen.py --file flow.json -o chart.png --width 600

# 只看 Mermaid 标记（不渲染，用于调试）
python scripts/flowchart_gen.py --file flow.json --markup-only
```

## 主题选择

| 主题 | 背景 | 适用场景 |
|------|------|---------|
| `catppuccin`（默认） | 深色 `#1e1e2e` | AI 教程、技术文章（与代码截图风格统一） |
| `github` | 白色 `#ffffff` | 正式文档、打印输出 |
| `dark` | 深色 `#0d1117` | GitHub 风格深色 |

## 输出规格

- **格式**：PNG
- **宽度**：670px（公众号内容区标准宽度）
- **缩放**：2x Retina（实际输出 1340px，显示时 `width="100%"`）
- **质量**：▶ Playwright 无损截图

## 与教程流水线的集成

在 `tutorial-pipeline` 的 Stage 0（步骤规划），如果教程包含"架构全景"或"流程概述"章节，规划官应添加 flowchart 类型截图：

```python
step = {
    "id": 0,
    "title": "架构全景：先看懂流水线",
    "type": "overview",
    "screenshots_needed": [
        {"type": "flowchart", "desc": "流水线四环节架构图"},
    ],
}
```

在 Stage 2（分步创作），先于文字生成流程图：

```
写架构全景文字 → 生成流程图 PNG → 嵌入 → 进入步骤1
```

## 参考

- [Mermaid Flowchart 文档](https://mermaid.js.org/syntax/flowchart.html)
- `scripts/flowchart_gen.py` — 实现源码
- `skills/tutorial-pipeline/SKILL.md` — 教程流水线集成
