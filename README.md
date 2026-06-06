# Article Pool — AI 内容创作生产线

微信公众号文章的选题、创作、排版、封面生成、发布一站式系统。

## 目录结构

```
article-pool/
├── CLAUDE.md                  # 项目指令（创作铁律 + CSS 规则 + Agent 表）
├── README.md                  # 本文件
├── VERSION / LICENSE / CHANGELOG.md
│
├── config/
│   ├── .env / .env.example    # API 密钥（WeChat、Brave、Pexels）
│   ├── capabilities.json      # 能力注册表（自动生成，24 项）
│   ├── capabilities_overrides.json  # 手工语义标注
│   ├── illustration_rules.json      # 插图规则
│   ├── pipeline_templates/     # 类型模板（5 种文章类型默认 stage 组合）
│   └── cron-examples.md
│
├── scripts/
│   ├── orchestrator.py        # 编排引擎（stage/loop/foreach + Hook 补偿）
│   ├── discover_capabilities.py    # 能力自动发现
│   ├── gen_cover.py           # legacy 封面兜底（无 image_gen/真实图库时）
│   ├── gen_cover_themes.json  # 14 套封面主题
│   ├── illustration_gen.py    # 插图自动配图（Agent/Codex 本地图 + 旧级联）
│   ├── publish_html.py        # HTML 直传公众号草稿箱
│   ├── topic_tracker.py       # 选题查重入库
│   ├── flowchart_gen.py       # 流程图生成
│   ├── code_image_generator.py     # 代码截图
│   ├── terminal_screenshot.py      # 终端截图
│   ├── paths.py / preferences.py   # 路径/偏好工具
│   ├── fetch-news.py          # 新闻抓取
│   ├── scrape-36kr-fixed.py / scrape-aibase-v2.py  # 定向抓取
│   └── capture/               # 统一截图工具包（terminal/browser/code/chart/flowchart/fonts）
│
├── skills/                    # 13 个 AI 创作技能
│   ├── article-pipeline/      # 多 Agent 协作创作链（编排入口）
│   ├── pipeline-planner/      # AI Planner（读 registry → 输出 PipelinePlan）
│   ├── wechat-writer/         # 公众号爆款写作（SCQA + 反 AI 模式 + 10 篇参考）
│   ├── tutorial-pipeline/     # 教程分步创作（写→截图→验证）
│   ├── cover-gen/             # 封面生成规范 [已废弃，用 cover-agent]
│   ├── illustration-gen/      # 插图生成规范 [已废弃，用 illustration-agent]
│   ├── flowchart-gen/         # 流程图生成
│   ├── capture/               # 截图工具包
│   ├── hotspot-tracker/       # 热点追踪 + 早报制作
│   ├── news-aggregator/       # 多源新闻聚合
│   ├── ai-daily-news-get/     # AI 早报自动生成
│   ├── xiaohongshu-writer/    # 小红书笔记写作
│   └── research-lobster/      # 新闻素材搜索研究
│
├── agents/                    # 4 个 Agent（硬约束执行）
│   ├── README.md
│   └── article-pool/
│       ├── review-agent.md    # HTML 结构扫描（硬检查 3 项）
│       ├── cover-agent.md     # image_gen 直接生成最终封面
│       ├── illustration-agent.md  # 插图自动配图
│       └── publish-agent.md   # 发布到草稿箱（不可跳过）
│
├── templates/                 # 11 个 HTML 模板（已适配微信 CSS）
│   ├── README.md
│   ├── article-template.html / tech-tutorial.html / daily-report.html
│   ├── morning-briefing.html / evening-briefing.html
│   ├── news-digest.html / weekly-report.html
│   ├── monthly-summary.html / yearly-summary.html
│   ├── component-reference.html
│   └── cover-previews/（4 个封面预览模板）
│
├── reports/                   # 运行时数据
│   ├── publish_log.json       # 发布历史
│   ├── used_topics.json       # 选题去重库
│   └── used_images.json       # 图片去重库
│
├── docs/                      # 详细文档（安装/API/排错/同步）
├── examples/                  # 示例文章
├── fonts/                     # CJK 字体（封面渲染）
└── test_images/               # 测试插图输出
```

## 快速开始

```bash
# 安装依赖
pip install -r scripts/requirements.txt

# 配置密钥
cp config/.env.example config/.env
# 编辑 config/.env，填入 WECHAT_APPID / WECHAT_SECRET

# 生成能力注册表
python scripts/discover_capabilities.py

# 干跑验证编排引擎
python scripts/orchestrator.py config/pipeline_templates/深度解析.json --dry-run
```

## 创作工作流

### 方式一：编排引擎（结构化）

```
用户选题 → AI Planner 输出 PipelinePlan JSON → orchestrator.py 执行
                                                      │
                                          stage → loop → foreach
                                                      │
                                          handoff → AI Agent 消费 → resume
```

```bash
# 生成 PipelinePlan（AI Planner）
# → 保存为 plan.json

# 执行（两阶段）
python scripts/orchestrator.py plan.json          # Phase 1: 生成 handoff
# AI 处理 handoff 文件后回写
python scripts/orchestrator.py plan.json --resume reports/handoffs  # Phase 2: 恢复
```

### 方式二：手动创作 + Agent 辅助

```
写作 → 审阅 Agent（HTML 结构扫描）→ 封面 Agent（image_gen 直接最终图）→ 插图 Agent → 发布 Agent
```

## 文章类型模板

| 类型 | 文件 | 特征 |
|------|------|------|
| 深度解析 | `pipeline_templates/深度解析.json` | loop 写审循环 → 插图+封面并行 → 发布 |
| 技术教程 | `pipeline_templates/技术教程.json` | foreach 逐步骤(写→截图→验证) → 审阅 → 发布 |
| 早报/晚报 | `pipeline_templates/早报_晚报.json` | 素材抓取 → foreach 逐条目 → 聚合排版 → 发布 |
| 项目推荐 | `pipeline_templates/项目推荐.json` | loop 写审循环 → 插图(GitHub 截图优先) → 发布 |
| 小红书 | `pipeline_templates/小红书.json` | 短 loop 写审 → 竖版封面 → 发布 |

模板是**兜底**，AI Planner 优先根据具体选题动态编排。

## Stage 类型

| 类型 | 行为 | 场景 |
|------|------|------|
| `stage` | 线性执行 tasks | 素材采集、发布 |
| `loop` | 重复子 stages 直到条件满足（max 兜底） | 写审循环 |
| `foreach` | 遍历数组，对每个元素执行子 stages | 教程多步骤、早报多条目 |

## 4 个 Agent

| Agent | 硬约束 |
|-------|--------|
| review-agent | HTML 扫描（无 div、无 p 样式、无外层 table），失败驳回 |
| cover-agent | Agent/image_gen 直接生成最终封面；legacy auto 旧来源只兜底，验证 >100KB |
| illustration-agent | Agent/Codex 本地图优先，兼容旧级联配图，失败不阻塞 |
| publish-agent | Windows PYTHONIOENCODING=utf-8，必须见 draft ID，自动入库 |

## 封面图生成

默认由 `cover-agent` / `image_gen` 根据文章语义直接生成最终 1200×675 PNG 封面，不经过 `gen_cover.py`。

`scripts/gen_cover.py` 只作为 legacy fallback：当前环境没有生图能力、用户明确要求真实图库/事实图片，或旧链路兜底时才使用；`--mode geometric` 不能作为成功封面。

## 文章发布

```bash
# Windows 必须加 PYTHONIOENCODING=utf-8
PYTHONIOENCODING=utf-8 python scripts/publish_html.py <文章.html> --cover <封面.png> --author "小咪"
```

## 选题查重

```bash
python scripts/topic_tracker.py list                          # 查看保护期内选题
python scripts/topic_tracker.py add "标题" "关键词" "类型"     # 发布后入库
```

## 微信公众号 CSS 铁律

| ❌ 禁止 | ✅ 必须 |
|---------|--------|
| `<div>` / `<section>` 做容器 | 内容直接放 `<p>` 中 |
| `<p>` 上放 font-size / color | 文字样式放 `<span>` |
| `<table>` 包裹全文 | `<table>` 仅做局部卡片 |
| flex / grid / border-radius / box-shadow | 扁平布局 |

## 配色原则

- **一个主色系贯穿全文**（不能暖黄区和冷蓝区并存）
- **点缀色最多 1 个**（仅用于关键数字和章节标题下划线，用量 <5%）
- **卡片是调料不是主菜**（大部分文字直接放在页面上）
- 每篇文章 AI 自主生成配色，不锁死具体色值

## 文档索引

| 文档 | 内容 |
|------|------|
| `CLAUDE.md` | 创作铁律 + CSS 兼容性 + Agent 表 |
| `agents/README.md` | 4 Agent 架构说明 |
| `skills/article-pipeline/SKILL.md` | Pipeline 编排规范 + 模板系统 |
| `skills/pipeline-planner/SKILL.md` | AI Planner 工作指南 |
| `skills/wechat-writer/SKILL.md` | 公众号写作规范（风格卡 + 标题 + SCQA） |
| `templates/README.md` | 模板使用说明 + CSS 兼容性详解 |
| `docs/` | 安装 / API 密钥 / 依赖 / 排错 |

## 许可证

MIT License
