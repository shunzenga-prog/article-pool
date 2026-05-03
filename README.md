# Article Pool —— AI 内容创作生产线

> 微信公众号文章的选题、创作、排版、封面生成、发布一站式自动化系统。

## 项目概述

Article Pool 是一套完整的 AI 辅助内容创作工具链，覆盖从选题查重、内容生成、HTML 排版、封面图制作到一键发布公众号草稿箱的完整流程。

**核心设计理念**：Harness Engineering（ harness 工程）—— 人定约束，AI 执行。通过约束层（config）、信息层（AGENTS.md）、验证层（validator）三层架构确保 AI 产出质量可控。

**作者身份**：小咪（笔名），专注编程技术、AI 前沿、开发工具领域的内容创作。

---

## 目录结构总览

```
微信公众号/
├── user_preferences.json          # 🔧 用户偏好配置（集中管理所有可调参数）
├── preview.html                   # 封面预览页面
│
├── 工作流/
│   └── article-pool/              # 📦 核心项目（Git 仓库）
│       ├── CLAUDE.md              #    Claude Code 项目指令（创作铁律 + CSS 规则）
│       ├── README.md              #    你正在读的文件
│       ├── install.sh             #    一键安装脚本
│       ├── sync.sh                #    双向同步脚本
│       │
│       ├── config/                # ⚙️ 密钥与配置
│       │   ├── .env               #    API 密钥（WeChat、Brave、Pexels 等）
│       │   ├── .env.example       #    密钥模板
│       │   └── cron-examples.md   #    定时任务示例
│       │
│       ├── scripts/               # 🛠 Python 工具脚本
│       │   ├── gen_cover.py       #    ★ 封面图生成器（双模式：auto/geometric）
│       │   ├── gen_cover_themes.json # 14 套封面主题（8 深色 + 6 浅色）
│       │   ├── publish_html.py    #    ★ HTML 直传公众号草稿箱
│       │   ├── topic_tracker.py   #    选题查重工具
│       │   ├── preferences.py     #    用户偏好加载器
│       │   ├── scrape-36kr-fixed.py   # 36氪新闻抓取
│       │   ├── scrape-aibase-v2.py    # AI Base 新闻抓取
│       │   ├── fetch-news.py      #    通用新闻抓取
│       │   ├── wechat-upload-image.py # 图片上传到微信
│       │   ├── check-css.sh       #    CSS 兼容性静态检查
│       │   └── requirements.txt   #    Python 依赖
│       │
│       ├── skills/                # 🧠 AI 创作技能（7 个）
│       │   ├── article-pipeline/  #    完整创作链路（6 Agent 协作）
│       │   ├── wechat-writer/     #    公众号爆款写作规范
│       │   ├── hotspot-tracker/   #    热点追踪与早报制作
│       │   ├── cover-gen/         #    封面图生成规范
│       │   ├── xiaohongshu-writer/#   小红书笔记写作
│       │   ├── ai-daily-news-get/ #    AI 早报自动生成
│       │   └── news-aggregator/   #    新闻聚合
│       │
│       ├── templates/             # 📄 HTML 模板（13 个，全部适配微信公众号 CSS）
│       │   ├── README.md          #    模板使用说明 + CSS 兼容性指南
│       │   ├── morning-briefing.html  # 早报
│       │   ├── evening-briefing.html  # 晚报
│       │   ├── daily-report.html      # 日报/深度长文
│       │   ├── weekly-report.html     # 周报
│       │   ├── tech-tutorial.html     # 技术教程
│       │   ├── news-digest.html       # 资讯速递
│       │   ├── monthly-summary.html   # 月度总结
│       │   ├── yearly-summary.html    # 年终总结
│       │   ├── article-template.html  # 通用文章
│       │   └── cover-previews/        # 封面预览模板
│       │
│       ├── agents/                # 🤖 Agent 系统文档
│       ├── docs/                  # 📚 详细文档（安装/API/排错）
│       ├── reports/               # 📊 运行时数据
│       │   ├── publish_log.json   #    发布历史
│       │   ├── used_topics.json   #    选题去重库
│       │   └── used_images.json   #    图片去重库
│       └── examples/              # 📝 示例文章
│
├── 模板/                           # 模板副本 + Python 自动化子系统
│   ├── 工作流/
│   │   └── 公众号自动创作/        #    Python 自动化创作系统
│   │       ├── README.md          #    Harness Engineering 架构说明
│   │       ├── AGENTS.md          #    Agent 行为指南
│   │       ├── config.py          #    约束层（安全红线 + 可配参数）
│   │       ├── main.py            #    编排器（fetch/generate/fill/validate/publish）
│   │       ├── content_fetcher.py #    内容采集（HN、GitHub Trending、RSS）
│   │       ├── content_generator.py   # AI 内容生成（8 种模板的提示词）
│   │       ├── template_filler.py     # 模板填充器（REPLACE 标记替换）
│   │       ├── validator.py       #    验证层（HTML/字数/敏感词/重复检查）
│   │       ├── wechat_publisher.py    # 浏览器自动化发布
│   │       ├── output/            #    生成的文章输出
│   │       └── logs/              #    运行日志
│   ├── *.html                     # 11 个 HTML 模板副本
│   └── 使用说明.md                # 模板使用说明
│
└── 文章/                           # 📰 已发布文章存档
    ├── 2026年04月/                 #   按月份组织
    └── 2026年05月/                 #   HTML + PNG 封面成对存放
```

---

## 快速开始

### 1. 环境准备

```bash
# Python 依赖
pip install -r scripts/requirements.txt

# 中文字体（封面生成必需）
# Windows: 系统自带微软雅黑，无需额外安装
# Linux:   sudo apt install fonts-noto-cjk
# macOS:   系统自带苹方，无需额外安装
```

### 2. 配置 API 密钥

```bash
cp config/.env.example config/.env
# 编辑 config/.env，填入你的密钥
```

| 密钥 | 用途 | 必需 |
|------|------|------|
| `WECHAT_APPID` / `WECHAT_SECRET` | 发布到公众号草稿箱 | 发布时必需 |
| `BRAVE_API_KEY` | Brave 图片搜索（封面素材） | 可选 |
| `PEXELS_API_KEY` | Pexels 图片搜索（封面素材） | 可选 |

### 3. 配置用户偏好

项目根目录的 `user_preferences.json` 集中管理所有可调参数。**删除此文件将恢复全部默认值。**

```json
{
  "author": { "name": "小咪", "signature_emoji": "🐱" },
  "cover": {
    "default_mode": "auto",
    "preferred_theme": null
  },
  "article": {
    "max_daily_drafts": 3,
    "min_length": 300,
    "max_length": 5000,
    "default_style": "专业流畅"
  },
  "footers": {
    "morning-briefing": "扫码关注，每天早晨 8:00 准时推送",
    "daily-report": "关注公众号，每天获取实用编程技巧"
  }
}
```

修改后下次调用自动生效，无需重启。

### 4. 测试

```bash
# 测试封面生成
python scripts/gen_cover.py --title "Hello World" --mode geometric --output test.png

# 查看所有封面主题
python scripts/gen_cover.py --list-themes
```

---

## 封面图生成

封面生成器 `scripts/gen_cover.py` 是项目的核心工具之一，生成 1200×675px 的 PNG 封面图。

### 两种模式

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| `auto`（默认） | 6 级智能回退链：OG 图片 → Pexels → AI 生成 → Unsplash → Brave → 几何图形 | 有网络、追求真实摄影质感 |
| `geometric` | 纯代码生成的抽象几何设计，14 套主题可选 | 离线、追求一致风格 |

### 14 套几何主题

**深色主题（8 套）**：深海科技、暖橙日落、翠绿清新、霓虹紫青、金棕奢华、玫红柔美、灰蓝简约、靛蓝深邃

**浅色主题（6 套）**：云雾白、晨曦金、薄荷绿、樱花粉、天空蓝、象牙白

浅色主题自动切换文字为深色（`#1A1A28`），确保在亮色背景上清晰可读。

### 用法

```bash
# Auto 模式（智能选择背景图）
python scripts/gen_cover.py \
  --title "GPT-5 发布深度解析" \
  --subtitle "多模态能力再进化" \
  --tag "AI FRONTIER" \
  --output cover.png

# Geometric 模式（指定主题）
python scripts/gen_cover.py \
  --title "GPT-5 发布深度解析" \
  --mode geometric \
  --theme cloud \
  --output cover.png

# 从文章提取 OG 图片
python scripts/gen_cover.py \
  --title "GPT-5 发布" \
  --article article.html \
  --output cover.png

# 查看所有主题
python scripts/gen_cover.py --list-themes
```

### 高级：图片去重

系统自动记录最近 30 天内使用过的图片 URL（存储在 `reports/used_images.json`），避免封面图重复。每次搜索时会自动跳过已用图片，已过期记录自动清理。

---

## Python 自动化创作系统

位于 `模板/工作流/公众号自动创作/`，是一个完整的命令行创作工具链。

### Harness Engineering 架构

```
约束层 (config.py)        →  安全红线（禁止自动发布、每日上限）
信息层 (AGENTS.md)        →  AI 行为规范（写作风格、去 AI 味规则）
生成层 (content_generator) →  8 种模板的结构化提示词
填充层 (template_filler)  →  HTML 模板占位符替换
验证层 (validator.py)     →  质量门禁（HTML 完整性、字数、敏感词、重复）
```

### 命令

```bash
cd 模板/工作流/公众号自动创作/

# 生成内容提示词
python main.py generate <模板类型> [主题]

# 填充模板
python main.py fill <模板类型>

# 验证 HTML
python main.py validate <HTML文件>

# 完整流程（生成 → 填充 → 验证）
python main.py full <模板类型> [主题]
```

### 8 种模板类型

| 模板类型 | 中文名 | 说明 |
|----------|--------|------|
| `morning-briefing` | 早报 | 每日科技早报，含资讯列表 + 每日词汇 |
| `evening-briefing` | 晚报 | 每日科技晚报，含事件列表 + 今日思考 |
| `daily-report` | 日报/长文 | 深度技术长文，支持代码块 |
| `weekly-report` | 周报 | 一周技术动态总结 |
| `tech-tutorial` | 技术教程 | 实战编程教程，含步骤 + 代码 |
| `news-digest` | 资讯速递 | 重大事件深度解读 |
| `monthly-summary` | 月度总结 | 月度内容复盘 |
| `yearly-summary` | 年终总结 | 年度创作回顾 |

---

## HTML 模板系统

`templates/` 目录包含 13 个 HTML 模板，全部已完成微信公众号 CSS 兼容性适配。

### 微信公众号 CSS 铁律

发布时公众号后台会改写 DOM，**预览看不出问题，发布后才暴露**：

| 改写行为 | 影响 |
|----------|------|
| 所有 `<div>` → `<p>` | 块级容器样式全部丢失 |
| `<p>` 上的 `style` 被剥离 | 文字样式必须放在 `<span>` 上 |
| `<table>` / `<td>` / `<span>` 的 style **保留** | ✅ 唯一可靠的布局方案 |

### CSS 兼容性速查

| ❌ 不能使用 | ✅ 替代方案 |
|-------------|------------|
| `<div>` `<section>` 做容器 | `<table width="100%"><tr><td style="...">` |
| `display: flex / grid` | `<table>` 表格布局 |
| `border-radius` | 移除（微信不支持） |
| `linear-gradient(...)` | 实色 `background` |
| `letter-spacing` | 移除 |
| `opacity` | 直接用色值代替 |
| 自定义 `font-family` | 移除，用系统默认 |

---

## 文章发布

### 方式一：API 直传（推荐）

```bash
python scripts/publish_html.py <文章.html> \
  --cover <封面图.png> \
  --author "小咪"
```

标题自动从 HTML 的 `<h1>` 提取，也可手动指定：
```bash
python scripts/publish_html.py article.html "自定义标题" --cover cover.png
```

### 方式二：手动复制

浏览器打开 HTML 文件 → 全选 → 复制 → 粘贴到公众号后台编辑器。

---

## 选题查重

创作前必须检查选题是否与近期已发布内容重复。

```bash
# 添加已发布选题
python scripts/topic_tracker.py add "GPT-5 发布" "GPT-5 OpenAI 大模型" "daily-report"

# 查看所有已记录选题
python scripts/topic_tracker.py list

# 清理过期记录
python scripts/topic_tracker.py clean
```

保护天数默认 7 天，可通过 `user_preferences.json` 的 `article.topic_protection_days` 配置。

---

## Skills 技能系统

7 个 AI 创作技能，每个技能目录包含 `SKILL.md` 规范文件：

| 技能 | 功能 | 触发方式 |
|------|------|----------|
| `article-pipeline` | 6 Agent 协作完整创作链路 | `/article-pipeline` |
| `wechat-writer` | 公众号爆款写作（SCQA 框架、反 AI 模式） | `/wechat-writer` |
| `cover-gen` | 封面图生成（auto + geometric 双模式） | `/cover-gen` |
| `hotspot-tracker` | 热点追踪 + 每日早报制作 | `/hotspot-tracker` |
| `ai-daily-news-get` | AI 领域早报自动生成 | `/ai-daily-news-get` |
| `xiaohongshu-writer` | 小红书笔记写作 | `/xiaohongshu-writer` |
| `news-aggregator` | 多源新闻聚合 | `/news-aggregator` |

### 6 Agent 创作链路

```
分流官 → 创作官 → 审阅官 → 润色官 → 评估官 → 发布官
             ↑__________|  (不通过则返回修改)
```

---

## 脚本速查

| 脚本 | 功能 | 用法示例 |
|------|------|----------|
| `gen_cover.py` | 封面图生成 | `python gen_cover.py --title "title" -o cover.png` |
| `publish_html.py` | 发布到公众号 | `python publish_html.py article.html --cover cover.png` |
| `topic_tracker.py` | 选题查重 | `python topic_tracker.py add "标题" "关键词" "类型"` |
| `preferences.py` | 偏好加载 | `from preferences import get_prefs` |
| `scrape-36kr-fixed.py` | 36氪新闻抓取 | `python scrape-36kr-fixed.py` |
| `scrape-aibase-v2.py` | AI Base 抓取 | `python scrape-aibase-v2.py` |
| `fetch-news.py` | 通用新闻抓取 | `python fetch-news.py` |
| `check-css.sh` | CSS 兼容性检查 | `bash check-css.sh` |

---

## 用户偏好完整参考

`user_preferences.json` 支持的全部配置项：

```json
{
  "author": {
    "name": "笔名",
    "signature_emoji": "个性签名 emoji"
  },
  "cover": {
    "default_mode": "auto | geometric",
    "preferred_theme": "cloud | dawn | mint | sakura | sky | ivory | ocean | sunset | ...",
    "title_font_size": 68,
    "subtitle_font_size": 20,
    "source_order": ["og", "pexels", "ai-gen", "unsplash", "brave"]
  },
  "article": {
    "max_daily_drafts": 3,
    "min_length": 300,
    "max_length": 5000,
    "auto_publish": false,
    "default_style": "写作风格提示词",
    "topic_protection_days": 7
  },
  "writing": {
    "title_length": [20, 30],
    "font_size_px": 15,
    "line_height": 1.9,
    "max_tables": 2,
    "max_paragraph_lines": 5,
    "end_emoji": "🐱"
  },
  "colors": {
    "body_text": "#1A1A1A",
    "heading_link": "#1E88E5",
    "emphasis": "#E74C3C",
    "success": "#27AE60",
    "max_colors": 4
  },
  "footers": {
    "morning-briefing": "早报页脚文案",
    "evening-briefing": "晚报页脚文案",
    "daily-report": "日报页脚文案",
    "weekly-report": "周报页脚文案",
    "tech-tutorial": "教程页脚文案",
    "news-digest": "资讯页脚文案",
    "monthly-summary": "月度总结页脚文案",
    "yearly-summary": "年度总结页脚文案"
  }
}
```

偏好加载采用深度合并策略：你只需在 JSON 中写要覆盖的字段，其余自动使用默认值。

---

## 文档索引

| 文档 | 内容 |
|------|------|
| `CLAUDE.md` | 创作铁律 + CSS 兼容性规则（AI Agent 必读） |
| `templates/README.md` | 模板使用说明 + CSS 兼容性详解 |
| `agents/README.md` | 6 Agent 协作系统说明 |
| `docs/INSTALL.md` | 安装指南 |
| `docs/API-KEYS.md` | API 密钥配置 |
| `docs/DEPENDENCIES.md` | 依赖说明 |
| `docs/TROUBLESHOOTING.md` | 故障排除 |
| `docs/SYNC.md` | 同步维护 |
| `模板/工作流/公众号自动创作/README.md` | Harness Engineering 架构 |
| `config/cron-examples.md` | 定时任务示例 |

---

## 许可证

MIT License

---

*Made with ❤️ by 小咪 🐱*
