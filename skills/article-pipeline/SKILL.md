---
name: article-pipeline
description: 文章创作完整流程。Stage 4(审阅)、Stage 4.8(封面)、Stage 8(发布) 由独立 Agent 硬约束执行。触发：创作文章、写文章、文章pipeline。
---

# 文章创作链（Article Pipeline）

多 Agent 协作创作流程。Stage 0-3 和 Stage 5-7 暂由 AI 语义执行，**Stage 4（审阅）、Stage 4.8（封面）、Stage 8（发布）已 Agent 化**——通过独立 Agent 工具调用执行，带硬约束和结构化校验。

## 触发场景

- "创作一篇文章"
- "写文章"
- "执行文章pipeline"

## 模板系统

`config/pipeline_templates/` 为每种文章类型提供默认 stage 组合：

| 模板文件 | 类型 | 核心特征 |
|---------|------|---------|
| 深度解析.json | 深度分析 | loop 写审循环 + 插图 + 封面 |
| 技术教程.json | 教程 | foreach 逐步骤写截审 |
| 早报_晚报.json | 新闻 | foreach 逐条目写作 |
| 项目推荐.json | 项目 | loop 写审循环 + GitHub 截图优先 |
| 小红书.json | 笔记 | 短 loop 写审 + 竖版封面 |

**模板是兜底，不是首选。** AI Planner 优先根据具体选题动态编排。只在不确定时读模板作为起点，读后按需加减 stage，不要照搬。

## 架构设计

```
Stage 0-3 (AI语义)
  分流 → Guardrails → 创作 → Guardrails
    ↓
Stage 4 (Agent)        ┌─ 审阅Agent ─┐
  bash扫描HTML结构      │ 硬检查3项    │
  → passed?            │ 软检查4项    │
    ↓ yes              └──────────────┘
Stage 4.5 (Agent)      ┌─ 插图Agent ─┐
  Agent图/旧级联配图    │ 失败不阻塞   │
  → _illustrated.html  └──────────────┘
    ↓
Stage 4.8 (Agent)      ┌─ 封面Agent ─┐
  强制auto模式          │ 验证>100KB  │
  绝不geometric         └──────────────┘
    ↓
Stage 5-6 (AI语义)
  润色 → 评估
    ↓
Stage 8 (Agent)        ┌─ 发布Agent ──┐
  PYTHONIOENCODING      │ 必须见✅输出 │
  → 草稿箱 + 入库       └──────────────┘
```

## Agent 调用方式

项目 Agent 定义在 `agents/article-pool/*.md`，调用时使用 `general-purpose` Agent，将对应 Agent 文件的规则编入 prompt：

```
Agent({
  subagent_type: "general-purpose",
  description: "审阅文章HTML",
  prompt: "你是文章审阅Agent。按照以下规则审阅 HTML 文件：

  [读取 agents/article-pool/review-agent.md 的完整规则]

  审阅文件：<文章路径>
  返回 REVIEW_RESULT 结构化结果。"
})
```

**原则：** Agent 定义文件是规则的唯一来源。调用时将其规则完整编入 prompt。`subagent_type` 统一用 `general-purpose`。

## Context Variables

```python
context = {
    "platform": "xiaohongshu|wechat",
    "article_type": "tutorial|news|opinion|recommendation|general",  # 文章类型
    "word_count_target": {"min": 1500, "max": 2500, "rationale": "观点/随笔"},  # 字数目标（Stage 0 设定）
    "topic": "选题内容",
    "stage": "triage|creation|review|...",
    "revisions": 0,
    "issues": [],
    "score": 0,
    "human_review": False,  # 是否需要人工确认
    # ⚠️ 真实性约束
    "real_experience": [],  # 真实实践记录
    "hypothetical_parts": [],  # 假设性内容标记
    "truth_check": {"passed": True, "fabricated_parts": [], "suggestions": []},
    # 文件约定
    "html_path": "",  # wechat-writer 产出：文章/{年份}年{月份}月/{日期}-{标题}.html
    "illustrated_path": "",  # Stage 4.5 产出：*_illustrated.html
    "cover_path": "",  # Stage 4.8 产出：同名 .png
    "style_card": {},  # wechat-writer 产出：配色/强调/节奏方案
    "title": "",  # wechat-writer 产出：最终标题
    # 配置引用
    "illustration_config": "config/illustration_rules.json",
    "pipeline": "article-pipeline",
}
```

### 文件命名约定

```
HTML 原文：     文章/{年份}年{月份}月/{日期}-{标题}.html  （wechat-writer 产出）
插图版 HTML：   文章/{年份}年{月份}月/{日期}-{标题}_illustrated.html  （Stage 4.5 产出）
封面图：        文章/{年份}年{月份}月/{日期}-{标题}.png  （Stage 4.8 产出）
```

**⚠️ Stage 4.5 之后的所有操作（审阅终检、发布）都针对 `_illustrated.html`。**

## Stage 0: 分流官（Triage）

**职责：** 分类任务，按平台 + 文章类型路由到正确的创作流水线

**决策逻辑（两级路由）：**

```
第一级：平台路由
if 平台 == "小红书":
    handoff_to(xiaohongshu_creator)
elif 平台 == "公众号":
    → 进入第二级：文章类型路由
else:
    ask_user("请选择平台")

第二级：文章类型路由（公众号）
if 文章类型 in ["教程", "实战教程", "操作指南", "AI实战教程"]:
    handoff_to(tutorial-pipeline)       # → skills/tutorial-pipeline/SKILL.md
elif 文章类型 in ["早报", "晚报", "日报", "新闻简报"]:
    handoff_to(news-pipeline)           # → skills/news-pipeline/SKILL.md（待建，暂用通用）
elif 文章类型 in ["深度解析", "观点评论", "项目推荐"]:
    handoff_to(article-pipeline)        # → 使用当前通用流程
else:
    # 不确定类型时，用通用流程
    handoff_to(article-pipeline)
```

**文章类型自动识别：**

如果未显式指定类型，从选题和关键词推断：

| 关键词特征 | 推断类型 | 路由到 |
|-----------|---------|--------|
| "教程""实战""手把手""入门""搭建""配置" | 教程 | tutorial-pipeline |
| "日报""早报""晚报""简报""资讯" | 新闻 | news-pipeline |
| "深度""分析""趋势""解读""为什么" | 深度解析 | 通用 pipeline |
| GitHub 链接、项目名 | 项目推荐 | 通用 pipeline |

### 字数目标确定（Stage 0 必做）

**在确定文章类型后，立即根据以下对照表确定字数目标区间：**

| 内容目的 | 推荐字数区间 | 核心逻辑 | 对应 Pipeline 类型 |
|---------|------------|---------|-------------------|
| 短资讯/快讯/通知 | 300-800字 | 快速传达，内容精简 | 早报/晚报 |
| 观点/随笔/方法论 | 1500-2500字 | 黄金区间，5-8分钟阅读 | 深度解析 |
| ≈1500字 | 最佳平衡点 | 清晰表述+算法判定优质 | 深度解析 |
| 软文/营销推广 | 500-1000字 | 直接聚焦，突出卖点 | 项目推荐 |
| 情感故事(短篇) | 1000-1500字 | 小场景快速引发共鸣 | 深度解析 |
| 情感故事(常规) | ≈3000字 | 完整情节和人物刻画 | 深度解析 |
| 深度干货 | 无严格上限 | 太长可拆分系列 | 技术教程/深度解析 |

**决策流程：**

1. 从用户 prompt 中提取内容目的关键词（"快讯""观点""教程""故事""软文"等）
2. 对照上表确定字数目标区间
3. **如果无法明确判断 → 向用户确认：** "这篇文章更接近以下哪种类型？"（列出候选）
4. 将 `word_count_target` 写入 Context Variables

**输出：** 确定平台 + 文章类型 + 字数目标 + 路由目标 Pipeline + Context Variables 初始化

---

## Stage 1: Guardrails（输入验证）

**职责：** 验证选题是否合适

**验证项：**
```
□ 选题查重：是否与近期已用选题重复？（见下方「选题查重」章节）
□ 时效性：新闻类是否在48小时内？
□ 敏感性：是否涉及敏感话题？
□ 可行性：是否有足够信息创作？
□ 合规性：是否符合平台规范？
```

### ⚠️ 选题查重（Stage 1 必做）

创作前必须检查选题是否与近期已发布内容重复，避免同一话题反复使用。

**步骤：**
1. 读取 `reports/used_topics.json`，查看保护期内的选题关键词
2. **语义判断**：将新选题的核心话题与已有记录对比，注意以下情况：
   - 同一事件的不同说法（如 "GPT-5 发布" ≈ "OpenAI 新旗舰模型亮相"）
   - 同一公司的连续报道（连续两天写 OpenAI 需要换角度或换公司）
   - 同一主题的不同侧面（"AI 烧钱" 和 "AI 融资" 可能有重叠）
3. 判断标准：
   - ✅ 全新话题、全新公司、全新角度 → 通过
   - ⚠️ 同一事件但有新进展（≥48h 后）→ 需标注与往期的区别
   - ❌ 同一事件、同一角度、同一批关键词 → 不通过，建议换选题

**不通过时的处理：**
- 换个角度（如从技术转商业，从国内转国际）
- 换个话题（选其他热点）
- 等保护期过后再写（适合重要但非突发的选题）

**相关工具：**
```bash
# 查看近期选题
python scripts/topic_tracker.py list
```

**决策：**
- ✅ 通过 → 进入创作
- ❌ 不通过 → 返回问题，建议换选题

---

## Stage 2: 创作官（初稿）

**职责：** 调用 `wechat-writer`（或 `xiaohongshu-writer`）完成写作+排版，产出 HTML 文件。

**选择 Skill：**
```
if platform == "小红书":
    使用 xiaohongshu-writer
else:
    使用 wechat-writer
```

**与 wechat-writer 的交接契约：**

| 方向 | 内容 | 说明 |
|------|------|------|
| → 传入 | 选题 + 平台 + Context Variables（含 word_count_target） | pipeline Stage 0-1 已确定 |
| ← 传回 | HTML 文件路径 | `文章/{年份}年{月份}月/{日期}-{标题}.html` |
| ← 传回 | 风格卡 | 已执行的配色/强调/节奏方案 |
| ← 传回 | 标题 | 20-30 字最终标题 |

**⚠️ wechat-writer 只负责写作+排版（步骤 1-11），不处理审阅/插图/封面/发布。** wechat-writer 步骤 11 通过后立即交还控制权。pipeline 从 Stage 4 继续。

### ⚠️ 真实性约束（核心原则）

**禁止编造"我实践过"的内容！**

| ✅ 允许 | ❌ 禁止 |
|--------|--------|
| 真实发生的事情 | 编造"我昨天做了 xxx" |
| 查到的公开信息 | 虚构数据、案例 |
| 假设性叙述（"假如..."） | 假装亲历者 |
| 标注"（示例）" | 假装实践过 |

**Context Variables 新增：**
```python
context["real_experience"] = []  # 真实实践记录
context["hypothetical_parts"] = []  # 假设性内容标记
```

**输出：** HTML 文件路径 + 风格卡 + 标题。交还 pipeline 进入 Stage 3。

---

## Stage 3: Guardrails（输出验证）

**职责：** 验证初稿是否符合规范

**验证项：**
```
□ 标题：20-30 字？≥2 钩子？无弱词？无 AI 味句式？（详见 wechat-writer 标题生成流程）
□ 字数：实际字数是否在目标区间 [word_count_target.min] - [word_count_target.max] 内？
   - 统计方法：提取 HTML 纯文本，计中文字符数（不含 HTML 标签/空白）
   - 区间内 → PASS
   - 超出上限 >20% → WARN（建议缩短或拆分系列）
   - 超出上限 ≤20% → PASS（可接受浮动）
   - 低于下限 >20% → WARN（建议补充内容）
   - 低于下限 ≤20% → PASS（可接受浮动）
   - 深度干货（无上限类型）：≥1500 字即 PASS，>5000 字建议拆系列
□ 结构：是否完整？
□ 小咪风格：是否有真实实践？
□ 时效标注：是否正确标注？
□ 微信CSS：是否符合 wechat-css-guide.md？（公众号必查）
  - 无 <style> 块？
  - line-height 在 <span> 上不在 <p> 上？
  - font-size/color 在 <span> 上不在 <p> 上？
  - 无 <div>/<section>？
□ 标题去重：正文第一块可见内容不重复公众号系统标题？
```

**决策：**
- ✅ 通过 → 进入审阅
- ⚠️ 需修改 → 返回创作官修改
- ❌ 标题硬约束不通过 → 直接驳回，回 wechat-writer 步骤 5b 重新生成
- ❌ 不合格 → 重新创作（微信CSS不合格直接驳回）

---

## Stage 4: 审阅官（Agent 硬约束）

**职责：** 调用 `review-agent` 扫描 HTML，执行结构硬检查和视觉软检查。

**Agent 调用：**

```
Agent({
  subagent_type: "article-pool/review-agent",
  description: "审阅文章HTML",
  prompt: "审阅文章HTML文件：<文章路径>

请执行硬检查（根级table数量、禁用标签、样式位置）和软检查（标题下划线、色系统一、金句、行动号召）。
返回 REVIEW_RESULT 结构化结果。"
})
```

**审阅 Agent 自动执行以下硬检查：**
- H1：根级 `<table>` 数量 ≤1 且不包裹全文
- H2：无 `<div>` / `<section>` 标签
- H3：文字样式不在 `<p>` 上（必须在 `<span>` 内）
- H4：正文首块内容不重复公众号系统标题（避免预览双标题）

**任一硬检查失败 → REJECTED → 返回 Stage 3 修复后重审。**

软检查失败 → WARNINGS → 可以继续但建议修复。

**审阅官同时执行以下内容+视觉+兼容性检查（从 wechat-writer 整合）：**

### 内容
- [ ] 标题 20-30 字 + ≥2 钩子元素 + 无弱词（浅谈/浅析/关于/漫谈/初探）
- [ ] 开头 3 秒留人？ [ ] 表格 ≤2 个？
- [ ] 金句 ≥1 句？ [ ] 无编造？ [ ] 行动号召？
- [ ] 时效新鲜？ [ ] 真人感 ≥6 项？（见 `references/real-human-feel-checklist.md`）

### 视觉
- [ ] 风格卡已执行？（配色/强调/节奏是否跟风格卡一致）
- [ ] **全文一个色系？**（不会出现"这里冷蓝、那里暖黄"的拼贴感）
- [ ] **点缀色 ≤1 个且克制？**（仅在关键数字或核心结论处出现，全文不超过 5 处）
- [ ] **章节标题有下划线？**（不能只靠加粗，必须有 border-bottom 锚点）
- [ ] **大章节之间分隔明显？**（底色交替 或 装饰分隔线，不能只靠 `···` 过渡大章节）
- [ ] **卡片是调料不是主菜？**（大部分文字直接放页面上，不是每个段落都包卡片）
- [ ] 字号 15-16px？ [ ] 行距 1.75-1.8？ [ ] 段落 ≤5 行？
- [ ] 代码块暗底浅字？ [ ] 图片 width=100%？

### 微信兼容
- [ ] 无 `<div>`/`<section>`？
- [ ] 文字样式在 `<span>` 上不在 `<p>` 上？
- [ ] 容器用 `<table><tr><td>`？
- [ ] 无 flex/grid/border-radius/box-shadow？
- [ ] 正文开头没有重复文章标题？

**任一硬检查失败 → REJECTED → 返回 Stage 3 修复后重审。**
内容/视觉/兼容性不通过 → 回 wechat-writer 对应写作/排版步骤修复。

**输出：** `REVIEW_RESULT` 结构化对象（passed + hard_failures + warnings）

---

## Stage 4.5: 插图生成（Agent）

**职责：** 调用 `illustration-agent` 分析文章内容，自动获取配图，嵌入 HTML。

**Agent 定义：** `agents/article-pool/illustration-agent.md`

**触发时机：** Stage 4 审阅通过后、Stage 5 润色之前。插图是锦上添花，失败不阻塞发布。

**Agent 调用：**

```
Agent({
  subagent_type: "general-purpose",
  description: "生成文章插图",
  prompt: "按照 illustration-agent 的规则，为文章生成插图：

  [读取 agents/article-pool/illustration-agent.md 的完整规则]

  文章路径：<HTML路径>
  文章类型：<深度解析|项目推荐|技术教程|早报_晚报>
  输出 _illustrated.html（不覆盖原文件）。"
})
```

**图片策略：** 默认 `auto`。Agent/Codex 本地图可用时优先使用；不可用时自动回退旧级联。事实型图片优先真实来源。

**旧级联兜底：** GitHub截图 → 网页OG → Brave搜索 → AI生成 → 几何兜底

**输出：** `_illustrated.html` + 插图清单 JSON。插图 Agent 失败不阻塞后续 Stage。

---

## Stage 4.8: 封面生成（Agent 硬约束）

**职责：** 调用 `cover-agent` 生成 1200×675 封面图。强制 auto 模式，绝不 geometric。

**Agent 调用：**

```
Agent({
  subagent_type: "article-pool/cover-agent",
  description: "生成文章封面图",
  prompt: "为文章生成封面图：
- 标题：<标题>
- 副标题：<副标题>
- 标签：<标签>
- 日期：<YYYY / MM / DD>
- 文章路径：<HTML路径>
- 输出路径：<PNG路径>
- 关键词：<逗号分隔>

使用 auto 模式（不要传 --mode 参数）。如果当前 Agent/Codex 已生成本地背景图，传 --background-image；生成后验证文件 >100KB。"
})
```

**封面 Agent 硬约束：**
- 永不传 `--mode geometric`
- 验证输出文件 >100KB（真实背景图 200-500KB，geometric 约 50KB）
- 失败时报告原因，不静默降级

**封面图规格：** 1200×675px PNG，16:9 比例。配色与文章风格卡协调。

**手动备用命令：**
```bash
python scripts/gen_cover.py --title "标题" --keywords "关键词1,关键词2" --output cover.png
python scripts/gen_cover.py --title "标题" --background-image cover-bg.png --keywords "关键词1,关键词2" --output cover.png
# 不要加 --mode geometric
```

**输出：** `COVER_RESULT` 结构化对象（cover_path + source + file_size_kb + status）

---

## Stage 5: 润色官（优化）

**职责：** 语言优化 + 图文整合润色

**优化维度：**
- 标题吸引力
- 开头抓眼球
- 正文流畅度
- 图片与文字配合（插图已在 Stage 4.5 嵌入）
- 结尾互动引导

**注意：** 插图生成已在 Stage 4.5 完成，润色官基于带图的完整文档进行最终润色，无需再单独处理配图。

**输出：** 优化稿 + 优化说明

---

## Stage 6: 评估官（评分）

**职责：** 爆款潜力评估

**评分维度：**
```
标题（30%）: ⭐⭐⭐⭐⭐
内容（30%）: ⭐⭐⭐⭐⭐
体验（20%）: ⭐⭐⭐⭐⭐
传播（20%）: ⭐⭐⭐⭐⭐
```

**输出：** 总分 + 爆款潜力预测

---

## Stage 7: Human in the Loop（可选）

**职责：** 人工确认

**触发条件：**
```
context["human_review"] == True
# 或评分低于阈值
# 或首次发布
```

**流程：**
1. 发送终稿给用户
2. 等待用户确认
3. 根据反馈修改或发布

---

## Stage 8: 发布官（Agent 硬约束，不可跳过）

**职责：** 调用 `publish-agent` 推送文章到公众号草稿箱。

**前置条件：** Stage 4 审阅 Agent 返回 `passed=true`。

**Agent 调用：**

```
Agent({
  subagent_type: "article-pool/publish-agent",
  description: "发布文章到公众号草稿箱",
  prompt: "发布文章：
- HTML路径：<_illustrated.html路径>  ← ⚠️ 必须是插图版，不是原始 HTML
- 封面路径：<封面PNG路径>
- 作者：小咪
- 标题：<文章标题>
- 类型：<深度解析|晚报|早报|教程|项目推荐>
- 关键词：<逗号分隔>

请在 Windows 下使用 PYTHONIOENCODING=utf-8，推送后自动选题入库。"
})
```

**发布 Agent 硬约束：**
- ⚠️ HTML 路径必须是 `_illustrated.html`（含微信 CDN 插图），不是原始 HTML
- Windows 自动加 `PYTHONIOENCODING=utf-8`
- 必须看到 `✅ 草稿创建成功！` + 草稿 ID
- 失败报告错误码和含义
- 发布成功自动入库 `reports/used_topics.json`

**手动发布命令（备用）：**
```bash
# Windows 必须加 PYTHONIOENCODING=utf-8（否则 GBK 编码报错）
# ⚠️ 使用 _illustrated.html（含插图），不是原始 HTML
PYTHONIOENCODING=utf-8 python scripts/publish_html.py <文章_illustrated.html> "标题" --cover <封面图.png> --author "小咪"

# 发布后题目入库
python scripts/topic_tracker.py add "标题" "关键词1,关键词2,关键词3" "深度解析"
```

**输出：** `PUBLISH_RESULT` 结构化对象（draft_id + article_size + status + next_step）

---

## ⚠️ 创作完成检查清单（Stage 8 发布后逐项确认）

Stage 8 完成后，逐项确认以下 7 项：

| # | 检查项 | 通过标志 |
|---|--------|----------|
| 1 | HTML 已生成 | 文件在 `文章/{年份}年{月份}月/` 目录（wechat-writer 产出） |
| 2 | **插图已嵌入** | `_illustrated.html` 存在，含微信 CDN 图片链接（Stage 4.5 产出） |
| 3 | 封面图已生成 | 同名 `.png` 与 HTML 同目录，文件 >100KB（Stage 4.8 产出） |
| 4 | 审阅已通过 | `review_html.py --json` 返回 `passed: true`（Stage 4 产出） |
| 5 | 选题已入库 | `reports/used_topics.json` 有新条目 |
| 6 | **已推送草稿箱** | 终端输出 `✅ 草稿创建成功！` + 草稿 ID |
| 7 | 推送的是插图版 | 发布命令用的是 `_illustrated.html` |

**7 项全部 ✅ 才算创作完成。缺第 6 项 = 文章没发出。**

---

## 完整执行示例

```python
# 初始化 Context
context = {
    "platform": "小红书",
    "topic": "2026年最值得关注的AI工具",
    "human_review": True,
}

# 执行 Pipeline
result = article_pipeline.run(context)

# 流程自动执行
Stage 0: 分流官 → 确定小红书平台
Stage 1: Guardrails → 选题通过
Stage 2: 创作官 → 生成初稿
Stage 3: Guardrails → 初稿通过
Stage 4: 审阅官 → 质量检查（内容定稿）
Stage 4.5: 插图生成 → 自动配图
Stage 4.8: 封面生成 → 1200×675 PNG
Stage 5: 润色官 → 语言优化（基于带图文档）
Stage 6: 评估官 → 评分预测
Stage 7: Human Loop → 等待用户确认
Stage 8: 发布官 → 推送草稿箱 + 题目入库
```

## 关键改进（学习自 OpenAI Agents SDK）

1. **分流官** - 智能分类任务
2. **Guardrails** - 输入输出双重验证
3. **Context Variables** - 上下文传递
4. **Handoff 机制** - Agent 间切换
5. **Human in the Loop** - 人工介入选项

---

*参考：OpenAI Swarm, OpenAI Agents SDK, AgentVerse*
