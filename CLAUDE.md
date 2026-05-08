# Article Pool — 公众号文章创作工作流

微信公众号文章的选题、创作、排版、封面生成、发布一站式项目。

## ⚠️ 创作完成标志（不可跳过）

**文章写完 ≠ 创作完成。Stage 8 发布 Agent 执行完毕，才算完成。**

创作流程由 `skills/article-pipeline/SKILL.md` 编排。以下 3 个 Stage 已 Agent 化，不接受跳过：

| Stage | Agent | 硬约束 |
|-------|-------|--------|
| Stage 4 审阅 | `review-agent` | HTML 结构扫描（table/div/style），hard check 失败 = 驳回 |
| Stage 4.8 封面 | `cover-agent` | 强制 auto 模式，绝不用 geometric，验证 >100KB |
| Stage 8 发布 | `publish-agent` | Windows 自动 PYTHONIOENCODING，必须见 ✅ + draft ID |

**Agent 定义：** `agents/article-pool/*.md`

## 项目结构

```
article-pool/
├── skills/                  # 创作技能（每个技能一个目录，含 SKILL.md）
│   ├── cover-gen/           # 封面图生成（PIL，1200×675 PNG）
│   ├── wechat-writer/       # 公众号文章创作规范
│   ├── hotspot-tracker/     # 热点追踪与早报制作
│   ├── article-pipeline/    # 多 Agent 协作创作链
│   └── ...
├── templates/               # HTML 模板（兜底用，首选根据风格卡即时生成）
├── scripts/                 # 工具脚本
│   ├── gen_cover.py         # 封面图生成
│   └── publish_html.py      # HTML 直传公众号草稿箱
└── config/.env              # 公众号 API 密钥
```

## ⚠️ 创作铁律

### 1. 禁止暴露 AI 身份
- ❌ "作为 AI 助手"、"我是 AI"、"作为一个人工智能"
- ❌ "小咪看到这个消息心情复杂" → ✅ "这个消息让人心情复杂"
- ✅ 可以用第三人称"小咪"作为笔名

### 2. 去 AI 味
- ❌ 结构化分层（一、二、三）→ ✅ 自然叙述
- ❌ "小咪观点"大标题 → ✅ 结尾自然表达
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
- **章节之间必须可见分隔**：`···` 用于章节内小过渡，大章节间用更明显的分隔（装饰线或底色交替）。
- **卡片是调料不是主菜**：大部分文字放页面上，卡片只在摘要/关键数据/结尾金句出现。
- **结构：内容直接在 `<p>` 中自然流动**，不要用 `<table>` 包裹全文——手机上会产生宽度问题和黑缝。`<table>` 仅用于数据卡片、摘要框等局部区块。

模板（`templates/`）作为兜底方案保留，仅在需快速产出时使用。

### 7. 教程文章必须带实操截图
- 每 1500 字至少 1 张真实截图（终端执行、浏览器界面、原文内容）
- 关键步骤（执行命令 → 中间输出 → 最终结果）必须有图
- **禁止用文字代码块模拟终端输出**——真实截图才有说服力
- **禁止在文章中出现本地文件路径**（如 `教程资源/xx/xx.py`、`E:\xxx`）——公众号读者看不到本地文件，用"后台回复 xxx 获取"替代
- 详细规范见 `skills/wechat-writer/SKILL.md` 「教程类文章截图规范」

## ⚠️ 微信公众号 CSS 兼容性

完整规范见 `skills/wechat-writer/references/wechat-css-guide.md`。核心原则：

- ❌ 禁止 `<div>` / `<section>` → 会被转为 `<p>` 并剥离样式
- ❌ 禁止在 `<p>` 上放文字样式 → 只能放 `text-align`
- ❌ 禁止用 `<table>` 包裹全文 → 手机上宽度问题和黑缝。页面内容直接放在 `<p>` 中
- ✅ 卡片/数据区用 `<table><tr><td>` 做局部容器
- ✅ 文字样式用 `<span style="...">`

发布前必须通过「发布前检查」（内容+视觉+微信兼容三维度，见 `skills/wechat-writer/SKILL.md`）。

### 8. 风格先行，模板兜底
- 创作前先定「风格卡」（基调+配色+强调+节奏），而不是先选模板
- HTML 根据风格卡即时生成，模板仅在风格卡匹配或快速产出时使用
- 视觉去 AI 味与文字去 AI 味同等重要——整段高亮、过度用色也是 AI 味

### 模板编写规范

> **模板现在是兜底方案。** 创作时应先根据选题定「风格卡」（见 `skills/wechat-writer/SKILL.md` 风格规划章节），然后即时生成 HTML。只有当风格卡与某个模板高度匹配、或需要快速产出时，才使用模板。

**文件头部**：注释块后必须紧跟 `<meta charset="UTF-8">`，否则 Windows 浏览器默认用 GBK 解码导致乱码。

```html
<!-- 模板注释 -->
-->
<meta charset="UTF-8">
<table width="100%">
```

**占位符系统**：
| 标记 | 用途 | 示例 |
|------|------|------|
| `<!-- REPLACE:key -->default<!-- /REPLACE -->` | 单值替换 | `<!-- REPLACE:标题 -->默认标题<!-- /REPLACE -->` |
| `<!-- REPEAT:名称 -->...<!-- /REPEAT -->` | 列表循环 | 夹在重复区块的首尾 |
| `<!-- REPLACE:keyN -->` (N=1,2,3...) | 固定编号替换 | `<!-- REPLACE:前提条件1 -->条件1<!-- /REPLACE -->` |

**REPEAT 区块规则**：
- ✅ 标题、表头放在 REPEAT 区块**外部**，避免每项重复
- ✅ `_strip_replace_comments` 会自动清理所有未替换的 REPLACE 和 REPEAT 标记
- ✅ `template_filler.py` 的 `_fill_repeat_*` 方法匹配 `<!-- REPEAT:名称 -->` 前缀

**注释规范**：
- 章节分隔注释中使用 "循环区块" 而非 "REPEAT 区块"（避免干扰自动化测试）

## 封面图生成

由 `cover-agent`（`agents/article-pool/cover-agent.md`）自动执行。强制 auto 模式，绝不 geometric。

```bash
# 手动备用（Agent 会自动调）
python scripts/gen_cover.py --title "标题" --subtitle "副标题" --output cover.png
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

# 限制图片数量
python scripts/illustration_gen.py article.html --type 技术教程 --max-images 5
```

**5 级图片源级联：** GitHub截图 → 网页OG图片 → Brave搜索 → AI生成 → 几何兜底

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

## 文章发布

由 `publish-agent`（`agents/article-pool/publish-agent.md`）自动执行。强制 PYTHONIOENCODING=utf-8，必须见 ✅ + draft ID。

```bash
# 手动备用（Agent 会自动调）
PYTHONIOENCODING=utf-8 python scripts/publish_html.py <文章.html> --cover <封面图.png> --author "小咪"
```

## 📋 创作完成检查清单（每篇必过）

文章创作结束后，必须逐项确认以下 **7 项**全部完成：

### 流程完成度（5 项）

| # | 检查项 | 验证方法 |
|---|--------|----------|
| 1 | HTML 文章已生成 | 文件存在于 `文章/{年份}年{月份}月/` |
| 2 | 封面图已生成 | 同名 `.png` 与 HTML 同目录 |
| 3 | 选题已入库 | `reports/used_topics.json` 有新条目 |
| 4 | **已推送到草稿箱** | 看到 `✅ 草稿创建成功！` + 草稿 ID |
| 5 | 已告知用户草稿位置 | 输出草稿 ID + "登录后台 → 草稿箱"指引 |

### 视觉质量（3 项）⚠️ 新增

| # | 检查项 | 验证方法 |
|---|--------|----------|
| 6 | **全文一个色系** | 能用一个颜色形容词描述全文，不会出现冷暖混搭 |
| 7 | **章节标题有下划线** | 扫一眼能看到每个大章节标题下的装饰线 |
| 8 | **章节分隔明显** | 大章节之间不会只靠 `···` 过渡，有更明显的分隔方式 |

**8 项全部 ✅ 才算创作完成。第 4 项（推送）和第 6 项（色系统一）最容易漏，特别注意。**

## 文件命名

文章：`E:\WorkSpace\创作\微信公众号\文章\{年份}年{月份}月\{日期}-{标题}.html`
封面：同目录，`.png` 后缀，与文章同名。

## 参考

- 完整写作规范：`skills/wechat-writer/SKILL.md`
- 模板清单与配色：`templates/README.md`
- 封面生成：`skills/cover-gen/SKILL.md`
- 发布脚本：`scripts/publish_html.py`
