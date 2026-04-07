# Article Pool - AI 内容创作生产线

> 🐱 小咪的完整内容创作链路 - 一键安装，智能同步

## 项目简介

Article Pool 是一个完整的 AI 内容创作生产线：

- **完整创作链路** - 从选题 → 创作 → 审阅 → 发布的全流程
- **多平台支持** - 微信公众号、小红书、知乎、抖音
- **自动化工具** - 封面生成、新闻抓取、API 对接
- **龙虾军团** - 6 个 Agent 协作，分工明确

## 核心改进 🆕

### 1. 单一目录架构

所有创作相关文件都在一个目录中，同步更方便：

```
article-pool/
├── skills/          # 完整 skills 目录（新增文件自动同步）
├── scripts/         # 完整 scripts 目录（新增文件自动同步）
├── templates/       # HTML 模板
├── agents/          # Agent 配置模板（龙虾军团）
├── config/          # API 配置模板
├── install.sh       # 安装脚本
└── sync.sh          # 智能同步（使用 rsync）
```

### 2. 智能同步方案

使用 `rsync` 自动同步整个目录：

```bash
# 同步到 OpenClaw Workspace
./sync.sh to

# 从 Workspace 同步回项目
./sync.sh from

# 查看状态
./sync.sh status
```

**关键改进：新增文件自动包含，无需手动更新脚本！**

## 快速安装

### 方式一：独立模式（推荐）

```bash
git clone https://github.com/shunzenga-prog/article-pool.git
cd article-pool

# 安装
./install.sh standalone

# 配置 API Keys
nano config/.env

# 配置 Agents（参考 agents/lobster-config.json）
# 重启 Gateway
openclaw gateway restart
```

### 方式二：集成模式

```bash
git clone https://github.com/shunzenga-prog/article-pool.git
cd article-pool

# 安装到现有 Workspace
./install.sh integrated

# 配置后重启
openclaw gateway restart
```

## 核心功能

### Skills（创作技能）

| Skill | 功能 | 触发 |
|-------|------|------|
| article-pipeline | 完整创作链路 | `创作文章` |
| wechat-writer | 公众号爆款写作 | `写公众号` |
| xiaohongshu-writer | 小红书笔记 | `写小红书` |
| ai-daily-news-get | AI 早报生成 | `生成早报` |
| hotspot-tracker | 热点追踪 | `追踪热点` |
| news-aggregator | 新闻聚合 | `聚合新闻` |

### Scripts（工具脚本）

| Script | 功能 |
|--------|------|
| wechat_publish.py | 公众号发布 |
| generate-cover.py | 封面生成 |
| add-cover-text.py | 封面加文字 |
| scrape-36kr-fixed.py | 36氪抓取 |
| scrape-aibase-v2.py | AI Base 抓取 |

### Agents（龙虾军团）

| Agent | 职责 | 推荐 Model |
|-------|------|------------|
| 🦞 代码龙虾 | 脚本编写、自动化 | glm-5 |
| 🎨 设计龙虾 | 封面设计、排版 | kimi-k2.5 |
| 🔍 研究龙虾 | 热点追踪、素材整理 | glm-5 |
| 📁 档案龙虾 | Memory 整理、归档 | qwen3.5-plus |
| 🏄 冲浪龙虾 | 爆款案例收集 | kimi-k2.5 |
| 📱 运营龙虾 | 公众号运营 | qwen3.5-plus |

## API 配置

需要配置以下 API Keys：

| API | 用途 | 获取方式 |
|-----|------|----------|
| Brave Search | 网络搜索 | https://brave.com/search/api/ |
| 微信公众号 | 发布文章 | https://mp.weixin.qq.com |
| Pollinations AI | 封面生成 | 免费，无需 Key |

配置文件：`config/.env`

详见 [docs/API-KEYS.md](docs/API-KEYS.md)

## 同步维护

### 从项目同步到 Workspace

```bash
./sync.sh to
```

适用场景：从 GitHub 拉取更新后，同步到本地 OpenClaw

### 从 Workspace 同步到项目

```bash
./sync.sh from
git add . && git commit -m "sync" && git push
```

适用场景：修改了本地 Skills/Scripts 后，同步回 GitHub

详见 [docs/SYNC.md](docs/SYNC.md)

## 使用示例

### 公众号文章创作

```
用户：创作一篇关于 DeepSeek V4 的公众号文章

小咪：
→ 调用 hotspot-tracker 追踪热点
→ 调用 article-pipeline 执行创作链路
→ 自动生成封面并上传
```

### AI 早报生成

```
用户：生成今天的 AI 早报

小咪：
→ 调用 news-aggregator 抓取最新新闻
→ 调用 ai-daily-news-get 生成早报
→ 自动封面 + 上传草稿箱
```

## 项目结构

```
article-pool/
├── skills/                      # 创作技能
│   ├── article-pipeline/
│   ├── wechat-writer/
│   ├── xiaohongshu-writer/
│   ├── ai-daily-news-get/
│   ├── hotspot-tracker/
│   ├── news-aggregator/
│   └── research-lobster/
│
├── scripts/                     # 工具脚本
│   ├── wechat_publish.py
│   ├── generate-cover.py
│   ├── add-cover-text.py
│   ├── scrape-36kr-fixed.py
│   └── ...
│
├── templates/                   # HTML 模板
│   └── article-template.html
│
├── agents/                      # Agent 配置
│   ├── lobster-config.json      # 龙虾配置模板
│   └── lobster-farm/            # 龙虾 workspace 模板
│       ├── code/
│       ├── design/
│       ├── research/
│       ├── archive/
│       ├── surf/
│       └── growth/
│
├── config/                      # 配置模板
│   └── .env.example
│
├── docs/                        # 文档
│
├── install.sh                   # 安装脚本
├── sync.sh                      # 智能同步脚本
└
└── README.md
```

## 文档

- [安装指南](docs/INSTALL.md)
- [API 配置](docs/API-KEYS.md)
- [同步维护](docs/SYNC.md)
- [架构设计](docs/ARCHITECTURE.md)

## 许可证

MIT License

## 作者

小咪 (Xiao Mi) 🐱

---

*Made with ❤️ by Xiao Mi*