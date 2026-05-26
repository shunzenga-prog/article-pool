# Article Pool — 多平台文章创作工作流

微信公众号和 CSDN 文章的选题、创作、排版、封面生成、发布一站式项目。

**所有创作规范、格式约束、发布流程均来自本项目内的文件。** 本项目是自包含的完整工具集，clone 即用。

## ⚠️ 创作完成标志（不可跳过）

**文章写完 ≠ 创作完成。发布成功才算完成。**

创作流程由 Claude 直接按 `skills/` 中的 SKILL.md 执行。技能负责"做什么"，脚本负责"执行"，审阅脚本负责"质量门禁"。

### 创作前必须先选平台

```
公众号文章 → 写 .html（表格卡片、span 着色、border-bottom 标题）→ publish_html.py
CSDN 文章   → 写 .md  （# 标题、**粗体**、> 引用、|表格|、- 列表）→ publish_csdn.py
```

**两套格式体系完全不兼容。禁止先写一个平台再机械转换成另一个。**

### 质量门禁

| 阶段 | 公众号 | CSDN |
|------|--------|------|
| 审阅 | `python scripts/review_html.py <文章>.html` H1/H2/H3 PASS | 人工检查 Markdown 结构（标题层级、引用、表格） |
| 封面 | `python scripts/gen_cover.py` auto 模式 >100KB | CSDN 用文章首图自动提取 |
| 发布 | `python scripts/publish_html.py` 见 ✅ + draft ID | `python scripts/publish_csdn.py` 见 ✅ + articleId |

### 创作流程

```
用户选题 → 选平台（公众号/CSDN）→ Claude 读取对应 SKILL.md → 
  按 Stage 逐步执行 → 每个阶段结束运行对应质量门禁 → 
  全部通过 → 完成
```

## 项目结构

```
article-pool/
├── skills/                  # 创作技能（每个技能一个目录，含 SKILL.md）
│   ├── cover-gen/           # 封面图生成（PIL，1200×675 PNG）
│   ├── wechat-writer/       # 公众号文章创作规范
│   ├── hotspot-tracker/     # 热点追踪与早报制作
│   ├── article-pipeline/    # 多 Agent 协作创作链
│   └── ...
├── agents/                  # Agent 定义
│   └── article-pool/
│       ├── publish-agent.md         # 公众号发布
│       └── csdn-publish-agent.md    # CSDN 发布
├── templates/               # HTML 模板（兜底用）
├── scripts/                 # 工具脚本
│   ├── publish_html.py      # HTML → 公众号草稿箱
│   ├── publish_csdn.py      # Markdown → CSDN 编辑器（Playwright）
│   ├── gen_cover.py         # 封面图生成
│   ├── review_html.py       # HTML 结构审阅（质量门禁）
│   └── capture/             # 统一截图工具包
├── config/
│   ├── .env                 # API 密钥 + CSDN profile
│   └── csdn_profile/        # CSDN 浏览器登录状态（gitignore）
└── archive/                 # 已归档
```

## ⚠️ 创作铁律

### 1. 禁止暴露 AI 身份
- ❌ "作为 AI 助手"、"我是 AI"、"作为一个人工智能"
- ❌ "小智看到这个消息心情复杂" → ✅ "这个消息让人心情复杂"
- ✅ 可以用第三人称"小智"作为笔名

### 2. 去 AI 味
- ❌ 结构化分层（一、二、三）→ ✅ 自然叙述
- ❌ "小智观点"大标题 → ✅ 结尾自然表达
- ❌ 整段高亮颜色 → ✅ 适度加粗、引用
- ❌ 完全无样式 → ✅ 有层次感但不像写报告

### 3. 内容真实
- ❌ 禁止编造"我试过了"、"我采访了"
- ✅ 真实来源、可查数据
- ✅ 假设性内容标注"（示例）"或"假如…"

### 4. 选题查重
- 创作前必须读取 `reports/used_topics.json` 检查选题是否与近期已发布内容重复
- 做语义判断（非精确匹配）：同一事件的不同说法算重复，不同角度/不同公司不算
- 保护天数默认 7 天（可通过 `config/.env` 的 `TOPIC_PROTECTION_DAYS` 配置）
- 发布后必须执行 `python scripts/topic_tracker.py add "标题" "关键词" "类型"` 入库
- 脚本自动剔除过期记录，无需手动清理
- 详细规则见 `skills/article-pipeline/SKILL.md` Stage 1 和 `skills/wechat-writer/SKILL.md`

### 5. 时效性
- 创作前必须搜索验证信息发布时间
- <24h：实时热点 | 24-48h：近期热点 | >48h：转分析角度

### 6. 配色与样式（AI 自主生成，不锁死具体色值）

**每篇文章的配色由 AI 根据选题气质自主生成。** 以下为设计原则，不是色值锁：

- **一个主色系贯穿全文**：全文底色、卡片、分隔线、标签都从同一色系衍生，仅靠深浅变化产生层次。严禁暖色调区和冷色调区混搭。
- **点缀色最多 1 个**：仅用于关键数字和章节标题下划线，用量 <5%。
- **章节标题必须有下划线**（`border-bottom`）：不能只靠加粗+放大，扫读时一眼定位。
- **章节之间必须可见分隔**：用 Unicode `·  ·  ·`（不是 `&middot;` 实体）做章节内小过渡，大章节间用更明显的分隔（装饰线或底色交替）。
- **卡片是调料不是主菜**：大部分文字放页面上，卡片只在摘要/关键数据/结尾金句出现。
- **结构：内容直接在 `<p>` 中自然流动**，不要用 `<table>` 包裹全文——手机上会产生宽度问题和黑缝。`<table>` 仅用于数据卡片、摘要框等局部区块。

模板（`templates/`）作为兜底方案保留，仅在需快速产出时使用。

### 7. 教程文章必须带实操截图
- 每 1500 字至少 1 张真实截图（终端执行、浏览器界面、原文内容）
- 关键步骤（执行命令 → 中间输出 → 最终结果）必须有图
- **禁止用文字代码块模拟终端输出**——真实截图才有说服力
- **禁止在文章中出现本地文件路径**（如 `教程资源/xx/xx.py`、`E:\xxx`）——公众号读者看不到本地文件，用"后台回复 xxx 获取"替代
- 详细规范见 `skills/wechat-writer/SKILL.md` 「教程类文章截图规范」

## ⚠️ 微信公众号 CSS 兼容性（创作前必读，违反即驳回）

> **微信发布时强制改写 DOM：** `<div>`→`<p>`、删除 `<style>` 块、剥离 `<p>` 上除 `text-align` 外的所有 style。**预览正常 ≠ 发布正常。**

完整规范见 `skills/wechat-writer/references/wechat-css-guide.md`。核心原则：

- ❌ **禁止 `<style>` 块** → 微信全部删除，全局样式归零
- ❌ 禁止 `<div>` / `<section>` → 会被转为 `<p>` 并剥离样式
- ❌ **禁止在 `<p>` 上放 `font-size` / `color` / `line-height`** → 只能放 `text-align`（`margin` 也可能丢失）
- ❌ 禁止用 `<table>` 包裹全文 → 手机上宽度问题和黑缝。页面内容直接放在 `<p>` 中
- ❌ 禁止正文第一块重复文章标题 → 公众号顶部已自动显示标题，正文重复会出现双标题
- ✅ 卡片/数据区用 `<table><tr><td>` 做局部容器
- ✅ **所有文字样式用 `<span style="...">`**，包括 `line-height`、`font-size`、`color`
- ✅ **段落间距用 `<p style="margin:10px 0 0 0;text-align:left;">`**（仅 inline margin-top）
- ✅ 编写模式统一为：`<p style="margin:Xpx 0 0 0;text-align:left;"><span style="font-size:15px;color:#2c2c2c;line-height:1.85;">正文</span></p>`

发布前必须通过「发布前检查」（内容+视觉+微信兼容三维度，见 `skills/wechat-writer/SKILL.md`）。**每篇创作的第一步，先读 `wechat-css-guide.md` 检查清单。**

### 8. 风格先行，模板兜底
- 创作前先定「风格卡」（基调+配色+强调+节奏），而不是先选模板
- HTML 根据风格卡即时生成，模板仅在风格卡匹配或快速产出时使用
- 视觉去 AI 味与文字去 AI 味同等重要——整段高亮、过度用色也是 AI 味

### 9. 标题钩子 ⚠️
- **20-30 字硬约束**（不足 20 = 驳回重写）
- **≥2 个钩子元素**（数字/反常识/紧迫感/承诺价值/制造好奇/身份认同）
- 禁止弱词：浅谈/浅析/关于/漫谈/初探/之我见
- 详细公式见 `skills/wechat-writer/SKILL.md` 标题钩子公式（8 个）

### 10. 字数目标 ⚠️
- **创作前必须确定字数目标区间**——不同内容目的有不同的黄金区间
- 字数目标在 pipeline Stage 0 根据内容目的自动判定，若不明确则向用户确认
- **在目标区间内才算 PASS**，超出/不足 >20% 需调整

| 内容目的 | 推荐字数区间 | 核心逻辑 |
|---------|------------|---------|
| 短资讯/快讯/通知 | 300-800字 | 快速传达，内容精简 |
| 观点/随笔/方法论 | 1500-2500字 | 黄金区间，5-8分钟阅读 |
| ≈1500字 | 最佳平衡点 | 清晰表述+算法判定优质 |
| 软文/营销推广 | 500-1000字 | 直接聚焦，突出卖点 |
| 情感故事(短篇) | 1000-1500字 | 小场景快速引发共鸣 |
| 情感故事(常规) | ≈3000字 | 完整情节和人物刻画 |
| 深度干货 | 无严格上限 | 垂直领域深度分析，太长可拆分系列 |

- 详细执行规则见 `skills/article-pipeline/SKILL.md` Stage 0（字数目标确定）和 Stage 3（输出验证）
- 写作指引见 `skills/wechat-writer/SKILL.md` 「字数目标参考」

### HTML 编写规范

详见 `skills/wechat-writer/references/html-authoring-guide.md`（文件头部格式、HTML 骨架、占位符系统、WeChat CSS 兼容性）。

## 封面图生成

由 `cover-agent`（`agents/article-pool/cover-agent.md`）自动执行。强制 auto 模式，绝不 geometric。

**Codex / GPT Image 硬约束：** 当前 Agent 具备 GPT Image / image_gen 生图能力时，封面必须先由 Agent 生成 1200×675 本地背景图，再调用 `gen_cover.py --background-image`。不允许直接跑旧 auto 级联并把 geometric 兜底当作成功；除非用户明确要求事实型真实图片，或当前环境确实没有生图工具。

```bash
# 手动备用（Agent 会自动调）
python scripts/gen_cover.py --title "标题" --subtitle "副标题" --output cover.png

# Codex / GPT Image 首选：如果当前 Agent 已生成本地封面背景
python scripts/gen_cover.py --title "标题" --subtitle "副标题" --background-image cover-bg.png --output cover.png
# 不要加 --mode geometric
```

详情见 `skills/cover-gen/SKILL.md`。

## 插图生成

在审阅官确认内容定稿后（Stage 4.5），自动分析文章内容并生成配图：

```bash
# 自动检测文章类型
python scripts/illustration_gen.py article.html

# 指定文章类型
python scripts/illustration_gen.py article.html --type 项目推荐

# 干跑测试
python scripts/illustration_gen.py article.html --type 项目推荐 --dry-run

# Codex/Agent 图片生成请求（支持时使用；不支持时继续旧流程）
python scripts/illustration_gen.py article.html --type 深度解析 --emit-image-requests reports/image_requests.json --dry-run
python scripts/illustration_gen.py article.html --type 深度解析 --use-local-images reports/generated_images.json

# 限制图片数量
python scripts/illustration_gen.py article.html --type 技术教程 --max-images 5
```

**图片策略：** 默认 `auto`。有 Agent/Codex 本地图时优先使用；没有时自动回退旧级联。事实型图片（项目截图、教程截图、Logo、新闻图）优先真实来源，不用 AI 伪造。

**Codex / GPT Image 硬约束：** 当前 Agent 具备 GPT Image / image_gen 生图能力时，插图必须先由 `illustration_gen.py --emit-image-requests` 产出请求，再由 Agent 逐张生成本地图，最后用 `--use-local-images` 上传和嵌入。只有事实型图片或 GPT Image 不可用时，才直接走旧级联。

**兼容旧流程：** 需要完全旧链路时传 `--image-strategy legacy`。

**旧级联兜底：** GitHub截图 → 网页OG图片 → Brave搜索 → AI生成 → 几何兜底

**配置驱动：** `config/illustration_rules.json` 按文章类型定义规则，新增类型只需加 JSON 条目。

**输出：** `*_illustrated.html`（不覆盖原文件）+ `reports/illustrations_*.json`

详情见 `skills/illustration-gen/SKILL.md`。

## 终端截图生成

使用 xterm.js + Playwright 生成带操作系统原生标题栏的逼真终端截图：

```bash
# 从文本文件生成终端截图（自动检测 OS）
python scripts/terminal_screenshot.py textfile.txt -o terminal.png

# 指定 OS 样式：windows / macos / linux
python scripts/terminal_screenshot.py textfile.txt --os windows --title "PowerShell" -o terminal.png

# 从管道输入
echo "Hello World" | python scripts/terminal_screenshot.py -o terminal.png
```

**OS 自适应标题栏**：Windows → Windows Terminal 标签页（`>_` 图标 + 深色标签栏）、macOS → 原生 Terminal（红黄绿交通灯）、Linux → GNOME Terminal（扁平标题栏）。

**依赖**：playwright（`pip install playwright && playwright install chromium`），xterm.js 通过 CDN 加载无需本地安装。

## 代码图片生成

从 Markdown 文章中的代码块自动生成配图（代码截图、终端输出、图表、动画）：

```bash
# 从文章生成所有配图
python3 scripts/code_image_generator.py process article.md -o output_dir --execute --animate

# 单独生成某类图
python3 scripts/code_image_generator.py chart code.py -o chart.png
```

5 种图片类型：code01(代码截图)、code02(终端)、code03(代码+注释)、code04(matplotlib图表)、code05(动画)。

**CJK 字体依赖**：matplotlib 图表使用合并字体 `fonts/DroidSansCJK.ttf`（ASCII + CJK 字形合一，EM=2048），由 `scripts/rebuild_cjk_font.py` 从系统 DroidSansFallbackFull + DejaVu Sans 构建。

## 工作目录配置

项目通过 `scripts/paths.py` 集中管理所有输出/临时文件路径，可通过 `config/.env` 覆盖默认值。

### 默认路径（不配任何东西）
- 插图本地副本：`test_images/illustrations/`
- 报告/日志/缓存：`reports/`
- 通用输出：`output/`
- 爬虫素材：`~/.openclaw/workspace/reports/materials/`

### 一键配置 WORK_DIR

```bash
# 所有临时文件统一到一个目录
echo "WORK_DIR=E:/WorkSpace/创作/temp" >> config/.env
# → temp/illustrations/  temp/reports/  temp/output/
```

### 细粒度覆盖

```bash
# 报告留在项目内，其余到 WORK_DIR
echo "REPORTS_DIR=reports" >> config/.env

# 爬虫输出单独配置
echo "SCRAPE_OUTPUT_DIR=E:/data/news" >> config/.env
```

优先级：`独立 *_DIR` > `WORK_DIR` > 硬编码默认值

## 文章审阅（质量门禁）

创作完成后、推送前，必须运行 HTML 结构审阅：

```bash
# 通用检查
python scripts/review_html.py article.html --json

# 教程模式（额外检查截图覆盖率）
python scripts/review_html.py article.html --tutorial --json

# 退出码 0 = 通过，非 0 = 被驳回
```

检查项：
- H1: 外层 `<table>` 包裹全文 → 驳回
- H2: `<div>` / `<section>` 禁用标签 → 驳回
- H3: `<p>` 标签上的 font-size/color → 驳回
- H4: 正文首块内容重复公众号系统标题 → 驳回
- S1-S4: 章节标题下划线、颜色种类、金句、行动号召（软警告）

## 文章发布

由 Claude 直接执行发布命令：

```bash
# 微信公众号（默认）
PYTHONIOENCODING=utf-8 python scripts/publish_html.py <文章.html> --cover <封面图.png> --author "小智"

# CSDN（接受 .md 文件，不是 .html）
PYTHONIOENCODING=utf-8 python scripts/publish_csdn.py <文章.md> --tags "标签1,标签2" --author "小智"
```

**必须看到 `✅ 草稿创建成功！` / `✅ 内容已填入 CSDN 编辑器`** 才算完成。

### CSDN 发布（可选）

**⚠️ CSDN 和公众号是两套完全不兼容的格式体系。** 公众号用 HTML + 表格卡片 + span 着色，CSDN 用纯 Markdown 结构元素。**两者不能互相机械转换。**

#### 创作铁律：先选平台，原生创作

```
公众号文章 → 写 .html（表格卡片、span 着色、border-bottom 标题）→ publish_html.py
CSDN 文章   → 写 .md  （# 标题、**粗体**、> 引用、|表格|、- 列表）→ publish_csdn.py
```

**禁止做法：** 先写完公众号 HTML，再机械转成 MD 发 CSDN。转换必然有损。

#### CSDN Markdown 格式规范

CSDN 支持的标准 Markdown 结构元素：

| 用途 | 语法 | 示例 |
|------|------|------|
| 标题层级 | `#` `##` `###` | `## 1. 章节标题` |
| 强调 | `**粗体**` | `**关键数据**` |
| 引用卡片 | `>` | `> 一句话金句` |
| 数据表格 | `\|列1\|列2\|` | 标准 GFM 表格 |
| 列表 | `-` `1.` | 无序/有序列表 |
| 代码 | ` ``` ` 围栏 | 带语言标识 |
| 分隔线 | `---` | 章节间过渡 |
| 图片 | `![alt](url)` | 必须用外部 URL |

**CSDN 不支持的（不要写）：** 内联 HTML、`<span style>`、`<table>` 卡片、彩色文字、border-bottom 装饰、emoji 装饰符。

#### 跨平台迁移：AI 重写流程（唯一推荐方式）

**禁止机械转换。** 机械转换对复杂排版文章必然有损。

当用户要求将公众号文章发到 CSDN 时，执行以下 AI 重写流程：

```
Step 1: 读取原文 HTML，理解语义结构
        - 识别：标题层级、章节编号、引用卡片、数据表格、要点列表
        - 区分：哪些是内容结构，哪些是微信专属样式

Step 2: 按 CSDN Markdown 格式规范重写
        - # → 文章标题（仅一个）
        - ## → 章节标题
        - > → 引用卡片/金句
        - |表格| → 数据表格
        - - → 列表项
        - ** → 强调
        - --- → 章节分隔

Step 3: 保存为 .md 文件（与原文同目录）

Step 4: 发布到 CSDN
        python scripts/publish_csdn.py <文章.md> --tags "标签"
```

#### 发布命令

```bash
# CSDN 原生 Markdown
python scripts/publish_csdn.py <文章.md> --tags "标签1,标签2"

# 如需自动发布（跳过人工确认）
python scripts/publish_csdn.py <文章.md> --tags "标签1,标签2" --publish
```

零配置。首次运行浏览器扫码登录，状态保存到 `config/csdn_profile/`。

## 📋 创作完成检查清单（每篇必过）

### 公众号文章

| # | 检查项 | 验证方法 |
|---|--------|----------|
| 1 | HTML 文章已生成 | 文件存在于 `文章/{年份}年{月份}月/` |
| 2 | 封面图已生成 | 同名 `.png` 与 HTML 同目录 |
| 3 | 选题已入库 | `reports/used_topics.json` 有新条目 |
| 4 | **已推送到草稿箱** | `✅ 草稿创建成功！` + 草稿 ID |
| 5 | 全文一个色系 | 不会出现冷暖混搭 |
| 6 | 正文不重复系统标题 | 顶部直接进入导语/钩子 |
| 7 | 章节标题有下划线 | border-bottom 装饰线 |
| 8 | 章节分隔明显 | 大章节间有可见分隔 |

### CSDN 文章

| # | 检查项 | 验证方法 |
|---|--------|----------|
| 1 | .md 文件已生成 | 含 `#` 标题、`##` 章节、`>` 引用、代码围栏 |
| 2 | 标题 20-30 字 | ≥2 个钩子元素 |
| 3 | 结构元素正确 | 无内联 HTML、无 span style、无 table 卡片 |
| 4 | **已推送到 CSDN** | `✅ 草稿已保存` + articleId |
| 5 | 图片用外部 URL | `![](https://...)` |

**7 项全部 ✅ 才算创作完成。**

## 文件命名

```
公众号：文章/{年份}年{月份}月/{日期}-{标题}.html（封面同名 .png）
CSDN：  文章/{年份}年{月份}月/{日期}-{标题}.md
```

## 参考

- 公众号写作规范：`skills/wechat-writer/SKILL.md`
- CSDN 格式规范：本文件 § CSDN Markdown 格式规范
- CSDN 发布 Agent：`agents/article-pool/csdn-publish-agent.md`
- 封面生成：`skills/cover-gen/SKILL.md`
- 公众号发布脚本：`scripts/publish_html.py`
- CSDN 发布脚本：`scripts/publish_csdn.py`
