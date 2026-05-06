---
name: flowchart-gen
description: 流程图生成技能。将流水线/架构/流程描述转换为设计级 Mermaid 流程图，通过 Playwright 渲染为暗色卡片 PNG。触发：画流程图、架构全景、流水线图、流程示意。
---

# 流程图生成（Flowchart Gen）

为教程文章、技术文档生成设计级流程图。完整的设计令牌系统（Design Token System）：7 套内容感知色板 + 7 类节点样式自动映射 + 4 类连接线样式 + 卡片居中布局。

**核心理念**：Mermaid 负责布局（dagre 自动路由 + 8 种节点形状 + subgraph），CSS 容器负责卡片视觉（玻璃拟态、径向光晕、标题装饰），SVG 后处理负责画质提升（节点渐变填充、外发光阴影、连线渐变）。所有视觉参数由设计令牌系统驱动，不硬编码颜色值。

> ⚠️ Mermaid v11.12+ 存在 `classDef` 语法错误回归。此版本使用**逐节点 `style` 指令**，功能等价且更稳定。

## 触发场景

- "画一个流程图"
- "把这个架构画成图"
- "流水线示意图"
- "架构全景"
- 教程中包含多步骤流程

## 设计系统概览

三层渲染架构，Mermaid 负责布局，CSS 负责容器视觉，SVG 负责画质：

```
输入 JSON → 色板令牌 → Mermaid 标记 → HTML 玻璃卡片 → SVG 后处理 → Playwright → PNG
     │                   │                    │                  │
     └─ 7 色板 ──────────┘                    │                  │
        × 7 节点类别                           │                  │
        × 4 连线类型                           │                  │
        × 效果参数 ────────────────────────────┘                  │
          (渐变/光晕/阴影/边框)  ──────────────────────────────────┘
```

### 色板（Palette）

| Key | 名称 | 基调 | 适用内容 |
|-----|------|------|---------|
| `tech-dark` | 科技暗色 | 专业、冷静、未来感 | **AI/编程教程**（默认） |
| `ocean` | 深海蓝 | 稳重、深邃、架构感 | 系统架构、基础设施 |
| `forest` | 森林绿 | 自然、生长、可持续 | 能源、环保、健康 |
| `sunset` | 日落暖 | 温暖、创造、人文感 | 创意、观点、生活方式 |
| `midnight` | 极夜黑 | 现代、锐利、极客感 | 创业、创新、产品 |
| `paper` | 宣纸白 | 优雅、人文、书卷气 | 文学、历史、教育 |

每个色板包含分层令牌：

```
palette
├── canvas / surface          # 画布与卡片背景
├── text / text_dim           # 文字层级
├── line / line_strong        # 线条色彩
├── categories (7 类)          # 节点样式
│   ├── step      # 流程步骤（主色）
│   ├── start     # 起点（绿色系）
│   ├── end       # 终点（红色系）
│   ├── decision  # 决策分支（暖色系）
│   ├── data      # 数据/存储（蓝色系）
│   ├── highlight # 重点步骤（紫色系）
│   └── external  # 外部系统（灰色系）
├── subgraph                  # 子图区域
├── edges (4 类)              # 连接线样式
│   ├── main      # 主流程：实线粗箭头 (2.5px)
│   ├── data      # 数据流：实线细箭头 (1.5px)
│   ├── feedback  # 反馈/循环：虚线 (4,4 dash)
│   └── trigger   # 触发/事件：点线 (2,4 dash)
├── font                      # 字体设置
└── effects                   # 视觉效果参数
    ├── canvas_glow           # 画布径向光晕色
    ├── card_bg / card_border # 玻璃拟态卡片
    ├── accent_from / to      # 标题装饰线渐变色
    ├── edge_gradient         # 连线渐变起止色
    └── gradient_boost        # 节点渐变亮度增量
```

### 视觉层次（从外到内）

1. **画布背景** — 深色底 + 双径向渐变光晕（蓝/紫色微弱辉光）
2. **玻璃卡片** — `linear-gradient(135deg, ...)` 半透明背景 + `backdrop-filter: blur(16px)` + 4 层 box-shadow（含 `inset` 高光）+ 1px 彩色边框
3. **点阵装饰** — 卡片左上角 3×3 CSS radial-gradient 点阵
4. **标题区** — 22px 粗体标题 + 13px 细字副标题 + 60px 宽渐变装饰线（`accent_from → accent_to → transparent`）
5. **Mermaid SVG** — dagre 自动布局的节点和连线
6. **SVG 后处理** — 注入 `<linearGradient>` 节点渐变、`<filter>` 阴影、连线渐变、箭头着色

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
| `circle` | 连接点 | `id(("text"))` |

### 节点内富文本

每个节点支持三层内容（自动布局）：

```
[图标] 粗体标题
细字描述（可选）
```

图标用 emoji（如 📥⚙️📄📝），描述支持 `\n` 换行。

## 输入格式

完整 JSON schema：

```json
{
  "direction": "LR",
  "title": "图表标题",
  "desc": "副标题（可选）",
  "palette": "tech-dark",
  "nodes": [
    {
      "id": "fetch",
      "label": "1. 抓取",
      "desc": "Hacker News API\n免费 JSON 接口",
      "shape": "rounded",
      "category": "step",
      "icon": "📥"
    }
  ],
  "edges": [
    {"from": "fetch", "to": "process", "label": "数据流", "category": "data"}
  ],
  "subgraphs": [
    {"title": "外部系统", "nodes": ["external_api"]}
  ]
}
```

### 字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| `direction` | ✅ | `LR`（左→右）、`TB`（上→下）、`RL`、`BT` |
| `title` | - | 图表标题（居中显示在顶部） |
| `desc` | - | 副标题（标题下方细字） |
| `palette` | - | 色板 key，默认 `tech-dark` |
| `nodes[].id` | ✅ | 唯一标识符（英文） |
| `nodes[].label` | ✅ | 节点标题（支持中文） |
| `nodes[].desc` | - | 节点描述（`\n` 换行） |
| `nodes[].shape` | - | 形状（默认 `rounded`） |
| `nodes[].category` | - | 样式类别（默认 `step`） |
| `nodes[].icon` | - | 前置 emoji 图标 |
| `edges[].from` | ✅ | 起点 ID |
| `edges[].to` | ✅ | 终点 ID |
| `edges[].label` | - | 连接线标签 |
| `edges[].category` | - | 连接线类型：`main`/`data`/`feedback`/`trigger` |
| `subgraphs[].title` | ✅ | 子图标题 |
| `subgraphs[].nodes` | ✅ | 子图包含的节点 ID 列表 |

## CLI 用法

```bash
# JSON 文件输入
python scripts/flowchart_gen.py --file flow.json -o flowchart.png

# 指定色板
python scripts/flowchart_gen.py --file flow.json -o chart.png --palette ocean

# 内联 JSON
python scripts/flowchart_gen.py --inline '{"direction":"LR","nodes":[...],"edges":[...]}' -o chart.png

# 自定义宽度（默认 720px）
python scripts/flowchart_gen.py --file flow.json -o chart.png --width 670

# 只输出 Mermaid 标记（调试用）
python scripts/flowchart_gen.py --file flow.json --markup-only

# 列出所有色板
python scripts/flowchart_gen.py --list-palettes
```

## 输出规格

- **格式**：PNG（微博/微信直接上传）
- **宽度**：720px 画布，内容卡片居中，`max-width: 656px`（720 - 32×2 padding）
- **缩放**：2x Retina（设备像素比 2.0，文字清晰无锯齿）
- **卡片**：玻璃拟态（backdrop-filter blur + linear-gradient 半透明 + 4 层 box-shadow + 1px 彩色 border + 左上角点阵）
- **节点**：SVG `<linearGradient>` 垂直渐变（fill 亮色→底色）+ `<filter>` 双层阴影（3px/1px）
- **连线**：SVG `<linearGradient>` 水平渐变（起点色→终点色）+ 箭头着色匹配
- **标题**：22px/700 + 13px/400 + 60px 宽渐变装饰线
- **水印**：卡片外部底部，色板名称与基调，opacity: 0.4

### 嵌入文章

```html
<table width="100%" cellpadding="0" cellspacing="0"><tr><td style="text-align:center;">
  <img width="100%" src="流程图.png" alt="架构全景流程图">
</td></tr></table>
```

使用 `<table><tr><td>` 包裹（微信发布时 style 不丢失），`width="100%"` 用属性而非 CSS。

## 色板选择指南

AI/编程/技术教程 → `tech-dark`
系统架构/基础设施 → `ocean`
创意/观点/生活 → `sunset`
创业/产品/创新 → `midnight`
健康/环保/可持续 → `forest`
人文/教育/历史 → `paper`

## 与教程流水线的集成

在 `tutorial-pipeline` 的 Stage 0（步骤规划），如果教程包含架构全景章节，规划官添加 overview 类型步骤：

```python
step = {
    "id": 0,
    "title": "架构全景：先看懂流水线",
    "type": "overview",
    "screenshots_needed": [
        {"type": "flowchart", "desc": "流水线架构全景图"},
    ],
}
```

在 Stage 2（分步创作），先于文字生成流程图：

```
写架构全景文字 → 创建 flow.json → flowchart_gen.py 生成 PNG → 嵌入文章 → 下一步
```

### 典型工作流

```bash
# 1. 根据教程内容编写 flow.json
# 2. 生成流程图
python scripts/flowchart_gen.py --file flow.json -o step0_flowchart.png --palette tech-dark
# 3. 嵌入 HTML 文章（<table><tr><td> + <img>）
```

## 设计原则

1. **Mermaid 做布局，不做视觉**：dagre 引擎负责节点定位、自动换行、连线路由、子图分组。CSS 和 SVG 负责所有视觉效果。
2. **设计令牌驱动**：所有视觉参数在 PALETTES 中作为令牌集中管理，不硬编码颜色值。新增效果只需扩展 `effects` 字段。
3. **SVG 后处理提升画质**：Mermaid 渲染后注入 `<linearGradient>` 节点填充、`<filter>` 阴影、连线渐变——不修改 Mermaid 源码，兼容升级。
4. **玻璃拟态卡片**：`backdrop-filter: blur()` + `linear-gradient` 半透明背景 + 多层 box-shadow 营造景深感。
5. **暗色优先**：暗色主题与代码截图风格统一，白色 `paper` 仅用于人文类。
6. **WeChat 兼容**：输出 PNG 位图，不依赖 CSS（公众号会剥离 `<div>` 样式）。

## 参考

- [Mermaid Flowchart 文档](https://mermaid.js.org/syntax/flowchart.html)
- `scripts/flowchart_gen.py` — 实现源码
- `skills/tutorial-pipeline/SKILL.md` — 教程流水线集成
- `skills/wechat-writer/SKILL.md` — 截图嵌入规范
