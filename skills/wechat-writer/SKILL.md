---
name: wechat-writer
description: 公众号爆款文章创作。深度长文，结构严谨。触发：写公众号、发文章、公众号创作。
---

# 公众号爆款文章创作

## 触发
- "写一篇公众号文章" / "发公众号" / "公众号创作"

## ⚠️ 核心原则
### 爆款公式
```
爆款 = 热点选题 × 情绪价值 × 结构化表达 × 视觉呈现
```

### ⚠️ 禁止暴露 AI 身份（核心！）

| ❌ 禁止 | ✅ 正确 |
|--------|--------|
| "作为 AI 助手" | 直接表达观点 |
| "我是 AI" | 无需说明身份 |
| "作为一个人工智能" | 直接写观点 |
| "小咪看到这个消息心情复杂" | "这个消息让人心情复杂" |

**小咪的定位：**
- ✅ 可以用第三人称"小咪"（笔名/昵称）
- ✅ 可以有观点、情绪、态度
- ❌ 不能说"我是 AI""作为 AI 助手"

### ⚠️ 去 AI 味写作（核心！）

| ❌ AI 味太重 | ✅ 自然写作 |
|------------|------------|
| 未来展望分"短期/中期/长期" | 用几句话自然收尾 |
| "小咪观点"搞大标题 | 结尾自然表达想法 |
| 引用原文用翻译后的语言 | 原话说出来 |
| 大量颜色高亮语法 | 适度强调，简洁为主 |
| 结构化分层（一、二、三） | 流畅叙述，自然过渡 |
| 完全无样式，太平淡 | 适当加粗、引用，有层次感 |

**样式使用原则：**
- ✅ 重点内容可以**加粗**
- ✅ 引用原文用引用格式（灰色边框）
- ✅ 关键数据可以突出
- ❌ 不要整段高亮颜色
- ❌ 不要过度使用<span style="color:red">

**核心：有层次感，但不像写报告！**

### ⚠️ 时效性验证（必查！）
**创作前必须验证每条信息的时效性：**
- 搜索确认事件发生时间
- 检查是否有最新进展/辟谣
- 标注超过30天的信息为"旧闻"
- 避免使用过时信息当新闻

**过时信息判断原则：**
- 搜索时确认模型/产品的最新版本号，避免引用已被替代的旧版本
- 人物/公司动态类信息需确认是否为近期事件
- 如有疑问，用 web_search 搜索 "xxx 最新" 确认时效性

**时效规则：**
- <24h：🔥 实时热点
- 24-48h：📈 近期热点
- >48h：💡 转分析角度，不当新闻

### ⚠️ 选题查重（创作前必做）

**目的：** 防止同一话题在保护期内重复创作，保持内容多样性。

**操作步骤：**
1. 先读取 `reports/used_topics.json` 了解近期已用选题
2. 将你打算写的选题核心关键词与已有记录对比
3. 做**语义判断**（不是精确匹配）：

**判断示例：**
| 新选题 | 已有记录 | 判断 |
|--------|---------|------|
| "GPT-5 正式发布" | "OpenAI 增速预警" | ✅ 不重复 — 不同角度 |
| "OpenAI 营收不及预期" | "OpenAI 增速预警" | ❌ 重复 — 同一事件 |
| "谷歌 AI 芯片突破" | "OpenAI 增速预警" | ✅ 不重复 — 不同公司 |
| "AI 概念股集体跳水" | "OpenAI 增速预警" | ⚠️ 可能重叠 — 需注意角度区分 |

**关键词选取参考：**
- 提取 3-5 个核心词：公司名、产品名、事件主题、行业标签
- 覆盖文章涉及的 2-3 条主要话题线

**如果查重不通过：**
- 换角度（技术→商业，国内→国际）
- 换话题（选其他热点）
- 等保护期过后再写

**辅助命令：**
```bash
python scripts/topic_tracker.py list          # 查看保护期内选题
python scripts/topic_tracker.py list --days 14  # 自定义天数
```

### 三大禁忌
1. ❌ **表格太多** - ≤2 个/篇
2. ❌ **论述太浅** - 需深入分析
3. ❌ **缺少真实感** - 禁止编造"我试过了"

### ⚠️ 表情符号
- **标题**：❌ 不用 | **正文**：⚠️ 极少 | **结尾**：✅ 1 个（🐱）

### ⚠️ 人味写作
- ❌ "该工具具有以下特点" → ✅ "根据文档和社区反馈，这工具有几个亮点"
- **禁止编造**：不能写"我试过了"、"我亲自体验过"

### 小咪特色
- 🐱 身份标识 | ✅ 真实来源 | 💡 金句（≥1 句） | 🎯 行动号召

---

## 创作流程
1. **选题** → 热点/教程/观点
2. **查重** → ⚠️ 读取 `reports/used_topics.json`，确认选题不与近期内容重复（详见「选题查重」）
3. **时效** → <24h 可用，>48h 转分析
4. **标题** → 20-30 字，爆款公式
5. **开头** → 3 秒钩子（见 `references/viral-guide.md`）
6. **正文** → SCQA，每段 3-5 行
7. **结尾** → 行动号召 + 金句
8. **去 AI 味** → ⭐ `references/anti-ai-patterns.md`
9. **自检** → 真人感 8 项≥6 项
10. **排版** → 根据文章类型选择模板。**注意：** 所有 HTML 必须遵循微信 CSS 规范（见 `references/wechat-css-guide.md`），从创作起就用 `<table>` + `<span>` 布局，避免返工
11. **终审** → ⭐ `references/final-review-checklist.md`
12. **微信兼容检查** → 对照 `references/wechat-css-guide.md` 的检查清单逐条验证（虽已按规范创作，仍需二次确认）
13. **发布** → 1) 上传图片到微信 CDN 生成 `_publish.html`; 2) `publish_html.py` 推送到草稿箱; 3) `topic_tracker.py add` 入库选题

---

## 爆款标题（6 个套路）
| 类型 | 公式 | 案例 |
|------|------|------|
| 数字型 | 数字 + 核心 | "3 小时搞定一周工作量" |
| 对比型 | A vs B 反差 | "卡里 10 万，下单 600 万房子" |
| 疑问型 | 如何/为什么 + 痛点 | "如何用 AI 写出 10 万 + 爆文？" |
| 教程型 | 手把手/保姆级 | "保姆级教程：5 分钟上手 DeepSeek" |
| 揭秘型 | 内幕/真相 | "AI 行业不愿告诉你的 5 个真相" |
| 复合型 | 2-3 个组合 | "全网粉丝 1800 万，如何玩转流量？" |
**更多**：见 `references/viral-guide.md`

---

## 黄金开头（3 秒留人）
### 常用钩子
- **提问法**："你知道...吗？"
- **数据法**：惊人数据 + 解读
- **故事法**：场景 + 人物 + 冲突
- **对比法**：Before/After
- **痛点法**：直击痛点
- **悬念法**：制造悬念

### 结构
```
钩子 → 背景 → 价值预告 → 引导阅读
```

---

## 正文（SCQA）
```
S 情境 → C 冲突 → Q 疑问 → A 答案
```
### 规范
- **段落**：3-5 行 | **小标题**：每 300-500 字 | **金句**：每 800 字≥1 个
### 去 AI 味
- ❌ "一、发生了什么" → ✅ "先看发生了什么。"
- ❌ "二、为什么重要" → ✅ "**为什么这很重要？**"
**详细**：见 `references/anti-ai-patterns.md`

---

## 结尾
### 必备
1. 核心观点（1 句）
2. 金句（可选）
3. 行动号召（必须）
### 模板
- **总结式**："以上就是...的 3 个关键方法"
- **提问式**："你觉得 AI 会取代人类吗？"
- **行动式**："现在就去试试，评论区告诉我结果"
- **金句式**："未来淘汰你的不是 AI，是会使用 AI 的人"

---

## 📐 排版
### 参数
| 元素 | 值 |
|------|-----|
| 字号 | 15-16px |
| 行距 | 1.75-2.0 |
| 段落 | ≤5 行 |
| 表格 | ≤2 个/篇 |
### 颜色
- **正文**：#1A1A1A | **标题/链接**：#1E88E5
- **重点**：#E74C3C | **成功**：#27AE60
**原则**：≤4 种。
**模板**：`templates/article-template.html`（通用）、`templates/tech-tutorial.html`（教程）、`templates/daily-report.html`（深度长文）

---

## ⚠️ 微信公众号 CSS 兼容性

公众号发布时会对 HTML 做 DOM 改写（`<div>`→`<p>`、剥离 `<p>` 上 style 等），导致预览正常的样式发布后崩坏。

**完整规范 + 检查清单：** `references/wechat-css-guide.md`

**发布前必须对照检查清单逐条过。**

---

## 自检
### 内容
- [ ] 标题 20-30 字？ [ ] 开头 3 秒留人？ [ ] 表格≤2 个？
- [ ] 金句≥1 句？ [ ] 无编造？ [ ] 行动号召？
- [ ] 时效新鲜？ [ ] 真人感≥6 项？
### 排版
- [ ] 字号 15-16px？ [ ] 行距 1.75-1.8？ [ ] 段落≤5 行？
- [ ] 标题清晰？ [ ] 颜色≤4 种？ [ ] 手机预览正常？
### ⚠️ 终审（必做）⭐
**清单**：`references/final-review-checklist.md`（8 大维度）

---

## 📸 教程类文章截图规范（必读）

**教程文章的核心竞争力是"实操感"——读者要看到真实的执行过程和结果，不是文字模拟。**

### ⭐ 核心原则：分步截图，同步嵌入

**写一步 → 截图一步 → 嵌入一步 → 再写下一步。** 这是教程流水线与通用流程最本质的区别。

教程不是写完所有文字再回头补图。原因：
1. 代码执行结果可能变化（API 数据、时间戳），回头补图会和文字对不上
2. 写完再截图容易漏掉关键步骤
3. 同步截图能第一时间发现"代码跑不通""输出不一致"等问题

### 截图类型（按优先级）

| 优先级 | 类型 | 说明 | 生成工具 |
|--------|------|------|---------|
| 0 | 流程图/架构图 | 流水线全景、系统架构、数据流 | Mermaid + Playwright 渲染 |
| 1 | 终端执行截图 | 命令运行的真实输出，逼真终端窗口 | terminal_screenshot.py（xterm.js + Playwright） |
| 2 | 界面/浏览器截图 | 生成的页面、工具界面、最终效果 | Playwright 全页截图 |
| 3 | 原文/源数据截图 | 点击链接后的实际内容页，证明数据真实 | Playwright viewport 截图 |
| 4 | 效果对比截图 | Before/After，或不同方案的对比 | 组合以上工具 |

### ⚠️ 截图规划（写生成脚本前必做）

**最容易犯的错误：用终端渲染工具生成所有截图。** 必须提前规划每张截图用什么工具。

**操作步骤：**
1. 列出文章中需要的所有截图
2. 对照上面的类型表，给每张图打上类型标签
3. 根据类型选择对应的生成工具
4. 再写生成脚本

**示例（本期就是反面教材）：**

| 截图 | 实际类型 | 应该用的工具 | 错误做法 |
|------|---------|-------------|---------|
| 终端运行输出 | 终端截图(类型1) | terminal_screenshot.py | ✅ |
| HTML 报告 | 界面截图(类型2) | Playwright | ❌ 用终端渲染画 ASCII 框 |
| 图表 | matplotlib 输出 | 直接保存 chart | ✅ |

**原则：** 终端输出 → `terminal_screenshot.py`（xterm.js 渲染，自动匹配操作系统标题栏）。网页/报告 → Playwright 浏览器截图。各用各的工具，不要混用。

### 数量要求

- **每个教程步骤至少 1 张截图**，execute 和 output 类步骤必须有图
- **每 1500 字至少 1 张截图**（最低标准）
- 截图总数与步骤总数比例不低于 **0.8:1**
- **用实际运行的真实输出，禁止用文字代码块模拟终端效果**

### 截图生成命令

```bash
# 流程图/架构图：从 JSON 生成 Mermaid 流程图
python scripts/flowchart_gen.py --file flow.json -o flowchart.png

# 终端执行截图：将文本内容渲染为逼真终端窗口
# --os 可选 windows/macos/linux，默认自动检测当前系统
python scripts/terminal_screenshot.py output.txt --os windows --title "PowerShell" -o stepN_terminal.png

# 终端截图也可以直接从管道读取
command > output.txt && python scripts/terminal_screenshot.py output.txt -o stepN_terminal.png

# 浏览器截图：打开 URL
python scripts/screenshot_util.py single https://example.com --width 800 --height 900 -o stepN_browser.png

# 本地 HTML 文件截图
python scripts/screenshot_util.py file output.html --width 800 --height 900 -o stepN_output.png

# 代码截图：代码块渲染
python scripts/code_image_generator.py code script.py -o stepN_code.png
```

### 图片嵌入规范

- 使用 `<table><tr><td>` 包裹 `<img>`，确保发布后 style 不被剥离
- `<img width="100%">` 用属性而非 CSS 控制尺寸
- alt 文本写清楚截图内容（便于读者理解，也便于搜索）
- 每张截图前有引导文字说明"这是什么"

### ⚠️ 工具依赖与字体配置（防止乱码）

**Python 数据类教程（matplotlib/pandas）必须注意：**

matplotlib 的字体回退链（font fallback chain）在某些环境中不可靠，**¥、CJK 等字形可能显示为方块（tofu）**。

**根因：** matplotlib 的 `font.sans-serif` 回退链在不同的 glyph 上可能选择不同字体，**而且 SimHei（黑体）根本不含 ¥（U+00A5）字形**，即使回退链生效也会显示 tofu。

**解决方案：**

```python
# ✅ 正确：使用 Microsoft YaHei（含 ¥）+ 显式 FontProperties
from matplotlib.font_manager import FontProperties
FONT_PATH = "C:/Windows/Fonts/msyh.ttc"  # Microsoft YaHei — 含 CJK + ¥
FONT_PROP = FontProperties(fname=FONT_PATH)
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]

# 在关键文本上显式指定 fontproperties
ax.set_title("标题", fontproperties=FONT_PROP, fontsize=14)
ax.set_xticklabels(labels, fontproperties=FONT_PROP)

# ❌ 错误1：仅靠 font.sans-serif 回退链——某些字形可能漏掉
plt.rcParams["font.sans-serif"] = ["SimHei"]
# ❌ 错误2：SimHei 本身缺少 ¥ 符号（U+00A5），即使回退链生效也没用
```

**跨平台注意事项：**
- **Windows**：优先 `C:/Windows/Fonts/msyh.ttc`（Microsoft YaHei，含 ¥），备选 `simhei.ttf`
- **macOS**：`/System/Library/Fonts/PingFang.ttc`（苹方，含 ¥）
- **Linux**：需安装 `fonts-wqy-microhei` 或 `fonts-noto-cjk`（均含 ¥）
- 脚本启动时检测系统，自动对应字体路径，**备选链必须测试所有用到的 glyph**

### 禁止事项

- ❌ 用文字代码块模拟终端输出——读者一眼识破，丧失信任
- ❌ 截图里出现本地绝对路径（如 `E:\WorkSpace\...`）——用示例路径
- ❌ 文章里写"完整源码: 教程资源/xxx/xxx.py"这种本地路径——公众号读者看不到
- ❌ 只在文末说"代码在xx"，正文没有任何截图做证据

---

## 📝 教程类文章代码讲解规范（必读）

**教程文章的核心价值不是"展示结果"，而是"解释过程"。** 读者看教程是为了学会自己怎么做，不是看 AI 怎么炫技。

### ⭐ 代码讲解三要素

每介绍一个关键函数或步骤，必须包含：

1. **代码片段** — 实际的关键代码（3-20行），不是伪代码或函数名列表
2. **逻辑解释** — 逐行/逐段说明代码在做什么，为什么这样写
3. **设计思路** — 为什么要选这个方案？有什么替代方案？踩了什么坑？

### 正反对比

| ❌ 错误：只描述结果 | ✅ 正确：展示代码 + 解释思路 |
|--------------------|---------------------------|
| "AI 用 IQR 法检测了异常值" | 展示 IQR 的计算代码：`q1, q3 = df.quantile([0.25, 0.75])`<br>解释：Q1 是 25% 分位数，1.5 倍 IQR 是统计学通用标准<br>说明：只标记不删除——因为高销售额也可能是真实大单 |
| "AI 自动选择了 utf-8-sig 编码" | 展示：`pd.read_csv(csv, encoding="utf-8-sig")`<br>解释：Excel 导出的 CSV 带 BOM 头（﻿），utf-8 读到列名会多个鬼字符<br>对比：utf-8 vs utf-8-sig 的区别就是自动去掉 BOM |
| "AI 生成了 5 张图表" | 挑一张图表展示完整代码（15-30行）<br>解释：figure→axes→plot→annotate→save 的 matplotlib 标准流水线<br>说明：为什么用 barh 而不是 bar（横向更利于手机端查看） |
| 只列 5 个函数名 | 展示 `main()` 函数代码<br>解释：为什么设计成 5 步流水线？每个函数只做一件事，方便单独修改<br>说明：如果加新图表只需改 `make_charts()`，不影响其他步骤 |

### 代码展示频率

- **每 800 字至少 1 个代码片段**（与金句频率持平）
- 代码片段 3-20 行最佳（太短没意义，太长手机端溢出）
- 挑 2-3 个最关键的代码块做深度讲解，其余的简要说明

### 代码讲解的层次

```
表层（展示）   → "AI 写了这段代码"
中层（解释）   → "这行代码做了什么"
深层（思考）   → "为什么这样做，而不是那样做"
```

**一篇文章至少要有 2-3 处到达"深层"——这才是读者真正付费的地方。**

---
## 参考
- `references/viral-guide.md` - 爆款指南
- `references/anti-ai-patterns.md` - 反 AI 指南 ⭐
- `references/final-review-checklist.md` - 终审清单 ⭐
- `templates/article-template.html` - 通用 HTML 模板
- `templates/tech-tutorial.html` - 技术教程模板
- `templates/daily-report.html` - 深度分享模板
- `templates/README.md` - 完整模板清单（含 WeChat 兼容性说明）
- `skills/cover-gen/SKILL.md` - 封面图生成技能 ⭐

---

## ⭐ 封面图生成（必做）

详见 `skills/cover-gen/SKILL.md`。

### 使用 gen_cover.py 生成封面

```bash
# 编辑 scripts/gen_cover.py 中的标题、副标题、日期等
# 然后运行：
python3 scripts/gen_cover.py
```

封面图规格：1200×675px PNG，16:9 比例，深蓝黑底色 + 双色渐变 + 几何装饰。

### 发布到公众号

```bash
# HTML 文章直接发布到草稿箱
python3 scripts/publish_html.py <文章.html> --cover <封面图.png> --author "小咪"
```

### ⚠️ 模板注意
所有文章模板（`templates/*.html`）已适配微信公众号 CSS 兼容性：flex→table，gradient→solid，border-radius/letter-spacing 已移除。详见 `templates/README.md`。

### ⚠️ 禁止
- ❌ 下期预告（除非已规划）
- ❌ 承诺后续更新
