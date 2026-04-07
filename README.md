# Article Pool - AI 内容创作生产线

> 🐱 小咪的完整内容创作链路 - 一键安装，即刻生产

## 项目简介

Article Pool 是一个完整的 AI 内容创作生产线，包含：

- **创作链路**：从选题 → 创作 → 审阅 → 润色 → 评估 → 发布的全流程
- **多平台支持**：微信公众号、小红书、知乎、抖音等
- **自动化工具**：封面生成、图片处理、API 对接
- **热点追踪**：实时追踪 AI 领域热点，智能选题

## 快速安装

```bash
# 克隆仓库
git clone https://github.com/xiaomi-ai/article-pool.git

# 安装到 OpenClaw
cd article-pool
./install.sh

# 配置 API Keys
cp config/.env.example config/.env
# 编辑 config/.env 填入你的 API Keys
```

## 核心功能

### 1. 创作链路 (Article Pipeline)

多 Agent 协作的完整创作流程：

```
选题 → 分流 → 创作 → 审阅 → 润色 → 评估 → 发布
```

**触发命令**：`创作一篇文章`

### 2. 微信公众号写作 (WeChat Writer)

深度长文创作，爆款公式驱动：

- 爆款标题模板（6 个套路）
- 黄金开头（3 秒留人）
- SCQA 结构
- 真人感检查清单

**触发命令**：`写公众号文章`

### 3. 小红书笔记 (Xiaohongshu Writer)

小红书爆款笔记创作：

- 标题 + 正文 + 封面建议 + 标签
- CES 算法优化

**触发命令**：`写小红书笔记`

### 4. AI 早报 (AI Daily News)

每日 AI 新闻自动聚合：

- 新闻抓取 → 素材整理 → 早报创作 → 封面生成 → 上传

**触发命令**：`生成 AI 早报`

### 5. 热点追踪 (Hotspot Tracker)

实时追踪 AI 领域热点：

- 微博热搜、知乎热榜、AI 媒体动态
- 智能选题建议

**触发命令**：`追踪 AI 热点`

## 项目结构

```
article-pool/
├── skills/              # 核心创作技能
│   ├── article-pipeline/    # 创作链路
│   ├── wechat-writer/       # 公众号写作
│   ├── xiaohongshu-writer/  # 小红书写作
│   ├── ai-daily-news-get/   # AI 早报
│   ├── hotspot-tracker/     # 热点追踪
│   ├── news-aggregator/     # 新闻聚合
│   └── research-lobster/    # 研究龙虾
│
├── scripts/             # 工具脚本
│   ├── wechat_publish.py    # 公众号发布
│   ├── generate-cover.py    # 封面生成
│   ├── add-cover-text.py    # 封面加文字
│   ├── scrape-36kr-fixed.py # 36氪抓取
│   └── scrape-aibase-v2.py  # AI Base 抓取
│
├── config/              # 配置文件
│   ├── .env.example         # API 配置模板
│   └── brave-config.json    # Brave 搜索配置
│
├── docs/                # 文档
│   ├── INSTALL.md           # 安装指南
│   ├── USAGE.md             # 使用手册
│   └── API-KEYS.md          # API 配置说明
│
├── templates/           # 模板文件
│   └── article-template.html # 公众号文章模板
│
└── examples/            # 示例文章
    └── sample-article.md    # 示例文章
```

## API 配置

需要配置以下 API Keys：

| API | 用途 | 获取方式 |
|-----|------|----------|
| Brave Search API | 网络搜索 | https://brave.com/search/api/ |
| 微信公众号 API | 发布文章 | https://mp.weixin.qq.com |
| Pollinations AI | 封面生成 | 免费，无需 API Key |

详见 [docs/API-KEYS.md](docs/API-KEYS.md)

## 使用示例

### 公众号文章创作

```
用户：创作一篇关于 DeepSeek V4 的公众号文章

小咪：
1. 调用 hotspot-tracker 追踪 DeepSeek 热点
2. 调用 article-pipeline 执行创作链路
3. 自动生成封面图
4. 上传到公众号草稿箱
```

### AI 早报生成

```
用户：生成今天的 AI 早报

小咪：
1. 调用 news-aggregator 抓取最新新闻
2. 调用 ai-daily-news-get 生成早报
3. 自动生成封面并上传
```

## 同步维护

本项目支持与 OpenClaw workspace 同步维护：

```bash
# 从 workspace 同步更新到项目
./sync-from-workspace.sh

# 从项目同步更新到 workspace
./sync-to-workspace.sh
```

详见 [docs/SYNC.md](docs/SYNC.md)

## 贡献指南

欢迎贡献代码、报告问题、提出建议！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 许可证

MIT License - 详见 [LICENSE](LICENSE)

## 作者

小咪 (Xiao Mi) 🐱 - AI 内容创作助手

---

*Made with ❤️ by Xiao Mi*