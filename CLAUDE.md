# Article Pool — 公众号文章创作工作流

微信公众号文章的选题、创作、排版、封面生成、发布一站式项目。

## 项目结构

```
article-pool/
├── skills/                  # 创作技能（每个技能一个目录，含 SKILL.md）
│   ├── cover-gen/           # 封面图生成（PIL，1200×675 PNG）
│   ├── wechat-writer/       # 公众号文章创作规范
│   ├── hotspot-tracker/     # 热点追踪与早报制作
│   ├── article-pipeline/    # 多 Agent 协作创作链
│   └── ...
├── templates/               # HTML 模板（全部适配微信公众号 CSS）
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

### 6. 风格约束
- 标题 ≤30 字，正文不用 emoji（结尾可 1 个 🐱）
- 表格 ≤2 个/篇，段落 ≤5 行
- 金句 ≥1 句/篇，行动号召必须

### 7. 教程文章必须带实操截图
- 每 1500 字至少 1 张真实截图（终端执行、浏览器界面、原文内容）
- 关键步骤（执行命令 → 中间输出 → 最终结果）必须有图
- **禁止用文字代码块模拟终端输出**——真实截图才有说服力
- **禁止在文章中出现本地文件路径**（如 `教程资源/xx/xx.py`、`E:\xxx`）——公众号读者看不到本地文件，用"后台回复 xxx 获取"替代
- 详细规范见 `skills/wechat-writer/SKILL.md` 「教程类文章截图规范」

## ⚠️ 微信公众号 CSS 兼容性

### 最严重的坑：发布时 DOM 改写（预览看不出来！）

公众号**预览时样式正常**，但**点击发布后**会做以下改写：
1. **所有 `<div>` → `<p>`**（包括 `<section>` 等块级元素）
2. **所有 `<p>` 上的 `style` 属性被全部剥离**
3. `<table>`、`<td>`、`<span>`、`<h1>`-`<h6>`、`<b>`、`<strong>`、`<pre>`、`<code>` 上的 style **保留**

**铁律：**
- ❌ 禁止用 `<div>` / `<section>` 做任何带样式的容器
- ❌ 禁止在 `<p>` 上放文字样式（颜色、字号等），只能放 `text-align`
- ✅ 所有容器用 `<table width="100%"><tr><td style="...">`
- ✅ 所有文字样式用 `<span style="...">`

### CSS 属性黑名单

| ❌ 会失效 | ✅ 替代方案 |
|-----------|-----------|
| `<div>` `<section>` 标签 | `<table><tr><td>` 表格布局 |
| `display:flex` / `grid` | `<table><tr><td>` 表格布局 |
| `display:inline-block` | 省略（span 内联即可） |
| `gap` / `align-items` | `<td>` + `padding` / `vertical-align` |
| `linear-gradient(...)` | 实色 `background:#色值` |
| `border-radius` | 移除（微信不支持） |
| `letter-spacing` | 移除 |
| `font-style:italic` | 移除 |
| `text-transform:uppercase` | 直接大写 |
| `opacity` | 直接色值 |
| `font-family` 自定义字体 | 移除 |

所有 `templates/` 下的 HTML 模板已完成转换。新建模板时必须遵守以上规则。

### 模板编写规范

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

```bash
# 编辑 scripts/gen_cover.py 修改标题等信息，然后：
python3 scripts/gen_cover.py
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

```bash
python3 scripts/publish_html.py <文章.html> --cover <封面图.png> --author "小咪"
```

或手动：浏览器打开 HTML → 全选复制 → 粘贴到公众号后台编辑器。

## 文件命名

文章：`E:\WorkSpace\创作\微信公众号\文章\{年份}年{月份}月\{日期}-{标题}.html`
封面：同目录，`.png` 后缀，与文章同名。

## 参考

- 完整写作规范：`skills/wechat-writer/SKILL.md`
- 模板清单与配色：`templates/README.md`
- 封面生成：`skills/cover-gen/SKILL.md`
- 发布脚本：`scripts/publish_html.py`
