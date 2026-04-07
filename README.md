# Article Pool - AI 内容创作生产线

> 🐱 完整的创作链路，一键安装到 OpenClaw，即刻开始生产

## 项目简介

Article Pool 是一个完整的 AI 内容创作生产线，包含：

- **创作链路**：分流 → 创作 → 审阅 → 润色 → 评估 → 发布
- **创作 Agent 系统**：6 个 Agent 协作完成内容生产
- **自动化工具**：封面生成、新闻抓取、公众号发布
- **6 个核心 Skills**：覆盖公众号、小红书、AI早报等场景

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/shunzenga-prog/article-pool.git
cd article-pool
```

### 2. 安装依赖

```bash
# Python 依赖
pip install -r scripts/requirements.txt

# Playwright 浏览器（用于新闻抓取）
playwright install chromium

# 中文字体（用于封面生成）
sudo apt install fonts-noto-cjk  # Ubuntu/Debian
```

### 3. 同步到 OpenClaw

```bash
./sync.sh to
```

这会将 skills、scripts 同步到 OpenClaw workspace。

### 4. 配置 API Keys

```bash
# 复制配置模板
cp config/.env.example ~/.openclaw/workspace/scripts/.env

# 编辑配置
nano ~/.openclaw/workspace/scripts/.env
```

填入你的 API Keys：

```env
# Brave Search（网络搜索）
BRAVE_API_KEY=你的Brave_API_Key

# 微信公众号（发布文章）
WECHAT_APPID=你的AppID
WECHAT_SECRET=你的AppSecret
```

### 5. 重启 Gateway

```bash
openclaw gateway restart
```

### 6. 测试

```
创作一篇测试文章
```

## 核心功能

### Skills（创作技能）

| Skill | 功能 | 触发命令 |
|-------|------|----------|
| article-pipeline | 完整创作链路 | `创作文章` |
| wechat-writer | 公众号爆款写作 | `写公众号` |
| xiaohongshu-writer | 小红书笔记 | `写小红书` |
| ai-daily-news-get | AI 早报生成 | `生成早报` |
| hotspot-tracker | 热点追踪 | `追踪热点` |
| news-aggregator | 新闻聚合 | `聚合新闻` |

### Agents（创作链路）

6 个 Agent 协作完成内容生产：

| Agent | 职责 |
|-------|------|
| 🎯 分流官 | 路由决策，分配任务 |
| ✍️ 创作官 | 写初稿 |
| 🔍 审阅官 | 质量检查 |
| ✨ 润色官 | 语言优化 |
| 📊 评估官 | 爆款评分 |
| 🚀 发布官 | 最终发布 |

**协作流程**：
```
分流官 → 创作官 → 审阅官 → 润色官 → 评估官 → 发布官
              ↑__________|  (如有问题返回修改)
```

详见：`agents/README.md`

### Scripts（工具脚本）

| Script | 功能 |
|--------|------|
| wechat_publish.py | 公众号发布 |
| generate-cover.py | 封面生成（Pollinations AI） |
| add-cover-text.py | 封面加文字 |
| scrape-36kr-fixed.py | 36氪新闻抓取 |
| scrape-aibase-v2.py | AI Base 新闻抓取 |
| fetch-news.py | 新闻聚合 |

## 使用示例

### 公众号文章创作

```
用户：创作一篇关于 DeepSeek V4 的公众号文章

执行流程：
1. 分流官 → 公众号创作官
2. 创作官写初稿
3. 审阅官质量检查
4. 润色官优化
5. 评估官评分
6. 发布官上传到公众号草稿箱
```

### AI 早报生成

```
用户：生成今天的 AI 早报

执行流程：
1. 抓取最新新闻
2. 生成早报内容
3. 自动生成封面
4. 上传到公众号
```

## 项目结构

```
article-pool/
├── skills/                  # 6 个核心 Skills
│   ├── article-pipeline/    # 创作链路
│   ├── wechat-writer/       # 公众号写作
│   ├── xiaohongshu-writer/  # 小红书写作
│   ├── ai-daily-news-get/   # AI 早报
│   ├── hotspot-tracker/     # 热点追踪
│   └── news-aggregator/     # 新闻聚合
│
├── scripts/                 # 工具脚本
│   ├── wechat_publish.py
│   ├── generate-cover.py
│   ├── add-cover-text.py
│   ├── scrape-36kr-fixed.py
│   └── ...
│
├── agents/                  # Agent 配置模板
│   ├── pipeline-config.json # 创作链路配置
│   └── README.md            # 说明文档
│
├── templates/               # HTML 模板
├── config/                  # 配置模板
├── docs/                    # 文档
├── install.sh               # 安装脚本
└── sync.sh                  # 同步脚本
```

## API 配置

### 必需的 API

| API | 用途 | 获取方式 |
|-----|------|----------|
| Brave Search | 网络搜索 | https://brave.com/search/api/ |
| 微信公众号 | 发布文章 | https://mp.weixin.qq.com |

### 可选的 API

| API | 用途 |
|-----|------|
| Pollinations AI | 封面生成（免费，无需 Key） |

详见 [docs/API-KEYS.md](docs/API-KEYS.md)

## 同步维护

### 从 GitHub 拉取更新

```bash
git pull
./sync.sh to
openclaw gateway restart
```

### 修改本地 Skills 后同步回项目

```bash
./sync.sh from
git add . && git commit -m "sync" && git push
```

详见 [docs/SYNC.md](docs/SYNC.md)

## 文档

- [安装指南](docs/INSTALL.md)
- [依赖说明](docs/DEPENDENCIES.md)
- [API 配置](docs/API-KEYS.md)
- [同步维护](docs/SYNC.md)
- [Agent 配置](agents/README.md)

## 常见问题

### Q: Skills 没有被识别？

```bash
# 确保执行了同步
./sync.sh to

# 重启 Gateway
openclaw gateway restart

# 检查 skills 列表
openclaw skills list | grep -E "wechat|article"
```

### Q: 封面生成失败？

```bash
# 安装中文字体
sudo apt install fonts-noto-cjk

# 测试
python scripts/generate-cover.py test
```

### Q: 新闻抓取失败？

```bash
# 安装 Playwright 浏览器
playwright install chromium
```

### Q: 公众号发布失败？

1. 检查 API Keys 是否正确
2. 确认 IP 白名单配置
3. 确认有发布权限

## 许可证

MIT License

## 作者

小咪 (Xiao Mi) 🐱

---

*Made with ❤️ by Xiao Mi*