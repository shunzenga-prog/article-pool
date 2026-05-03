---
name: illustration-gen
description: 文章插图自动生成。分析文章内容，通过5级级联获取配图（GitHub截图→OG图片→Brave搜索→AI生成→几何兜底），上传微信CDN，嵌入HTML。触发：插图生成、配图、文章插图。
---

# 文章插图自动生成

分析文章内容，自动匹配、获取、上传、嵌入插图到文章 HTML 中。是 Article Pipeline 的 **Stage 4.5**（位于审阅官之后、润色官之前）。

## 触发场景

- "给文章配图" / "生成插图" / "文章插图"
- 文章创作完成后自动触发（Stage 4.5）
- 单独对已有文章补插图

## 快速使用

```bash
# 自动检测文章类型
python scripts/illustration_gen.py article.html

# 指定文章类型
python scripts/illustration_gen.py article.html --type 项目推荐

# 干跑（仅分析，不下载）
python scripts/illustration_gen.py article.html --type 技术教程 --dry-run

# 不上传微信 CDN（仅本地处理）
python scripts/illustration_gen.py article.html --type 深度解析 --no-upload

# 限制最大图片数
python scripts/illustration_gen.py article.html --type 项目推荐 --max-images 5
```

## 工作流程

```
文章 HTML → 内容分析 → 匹配规则 → 5级级联获取 → 缩放处理 → 微信上传 → 嵌入HTML → 输出
```

### 1. 内容分析
根据文章类型的 `triggers` 配置，提取：
- GitHub 仓库链接（owner/repo）
- 项目/工具名称（从 `<b>` 标签）
- 代码块（`<pre><code>`）
- 章节结构（`<h2>/<h3>` 或粗体段落标记）
- 新闻条目（编号表格结构 01-05...）
- 公司/组织名称（可配置列表）
- 概念术语（粗体关键词 + 标题）
- 数据点（金额、百分比等技术指标）
- 外部链接

### 2. 配置匹配
读取 `config/illustration_rules.json`，根据文章类型加载对应的图片来源优先级和插入位置策略。

### 3. 5 级图片源级联

| 级别 | 来源 | 适用场景 | 需要 Key |
|------|------|---------|---------|
| T1 | GitHub Social Preview (`opengraph.githubassets.com`) | 项目推荐 | 否 |
| T2 | 网页 OG:Image 提取 | 有外部链接的文章 | 否 |
| T3 | Brave 图片搜索 | 通用 | BRAVE_API_KEY |
| T4 | Pollinations.ai AI 生成 | 概念性插图 | 否 |
| T5 | PIL 几何抽象图案 | 兜底 | 否 |

每种文章类型可独立配置启用/禁用哪些级别、每级生成几张图。

### 4. 图片处理
- 缩放至 670px 宽度（微信公众号正文宽度）
- 格式统一为 PNG
- 微信上传（cgi-bin/media/uploadimg），2MB 限制

### 5. HTML 嵌入
按文章类型的 `placement` 策略插入 `<table>` 包裹的 `<img>` 标签：
- `after_project_intro` — 每个项目介绍后
- `after_code_block_or_section` — 代码块或小节后
- `after_section_header` — 章节标题后
- `before_section` — 章节前

输出文件命名为 `*_illustrated.html`，不覆盖原文件。

## 文章类型与配置

预设 4 种文章类型，每种有独立的触发条件、图片源优先级和插入策略：

| 类型 | 触发条件 | 图片源优先级 | 插入位置 |
|------|---------|-------------|---------|
| 项目推荐 | GitHub链接、项目名 | GitHub截图 → OG → 搜索 → AI → 几何 | 项目介绍后 |
| 技术教程 | 代码块、工具名 | 代码截图 → OG → 搜索 → AI → 几何 | 代码块/小节后 |
| 深度解析 | 概念术语、公司名、数据点 | OG → AI → 搜索 → 几何 | 章节标题后 |
| 早报_晚报 | 新闻条目、公司名 | OG → 搜索 → 几何 | 章节前 |

### 添加新文章类型

只需在 `config/illustration_rules.json` 的 `article_types` 中添加条目，无需改代码：

```json
"新类型名": {
  "description": "...",
  "triggers": { ... },
  "sources": {
    "og_image": { "enabled": true, "priority": 1, "per_section": 1 },
    "fallback_pattern": { "enabled": true, "priority": 5 }
  },
  "placement": "after_section_header"
}
```

同时添加 `auto_detect.rules` 条目以支持自动检测。

## 自动类型检测

不指定 `--type` 时，脚本根据 HTML 内容特征自动判定文章类型：

- 包含 `github.com/` + "开源项目" → 项目推荐
- 包含 `<pre><code>` + "教程" → 技术教程
- 包含 "深度" + "解析" → 深度解析
- 包含 "早报" / "晚报" → 早报_晚报

## 输出

- `{article}_illustrated.html` — 带插图的文章
- `test_images/illustrations/ill_*.png` — 本地图片副本
- `reports/illustrations_*.json` — 插图清单（来源、URL、大小）

## 与 Pipeline 集成

Stage 4.5 在审阅官确认内容定稿后执行：

```
Stage 4: 审阅官 → 内容定稿
Stage 4.5: 插图生成 → 分析→获取→上传→嵌入
Stage 5: 润色官 → 基于带图完整文档做最终润色
```

与封面生成（Stage 8）完全独立，不共享流程。

## 依赖

```bash
pip install Pillow requests --break-system-packages
```

配置：`config/.env` 中需要 `WECHAT_APPID`、`WECHAT_SECRET`（微信上传），可选 `BRAVE_API_KEY`（图片搜索）。
