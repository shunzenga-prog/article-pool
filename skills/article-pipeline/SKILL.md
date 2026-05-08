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
  5级级联获取配图       │ 失败不阻塞   │
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
    "article_type": "tutorial|news|opinion|recommendation|general",  # 🆕 文章类型
    "topic": "选题内容",
    "stage": "triage|creation|review|...",
    "revisions": 0,
    "issues": [],
    "score": 0,
    "human_review": False,  # 是否需要人工确认
    # ⚠️ 真实性约束（新增）
    "real_experience": [],  # 真实实践记录
    "hypothetical_parts": [],  # 假设性内容标记
    "truth_check": {"passed": True, "fabricated_parts": [], "suggestions": []},
    "illustration_config": "config/illustration_rules.json",  # 🆕 插图规则配置
    "pipeline": "article-pipeline",  # 🆕 当前使用的 pipeline（用于追踪）
}
```

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

**输出：** 确定平台 + 文章类型 + 路由目标 Pipeline + Context Variables 初始化

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

**职责：** 根据 skills 写初稿

**选择 Skill：**
```
if platform == "小红书":
    使用 xiaohongshu-writer
else:
    使用 wechat-writer
```

### ⚠️ 真实性约束（核心原则）

**禁止编造"我实践过"的内容！**

| ✅ 允许 | ❌ 禁止 |
|--------|--------|
| 真实发生的事情 | 编造"我昨天做了 xxx" |
| 查到的公开信息 | 虚构数据、案例 |
| 假设性叙述（"假如..."） | 假装亲历者 |
| 标注"（示例）" | 假装实践过 |

**没有真实实践时怎么办？**
1. 用"假设性叙述"：「假如你要 xxx，可以这样...」
2. 用"通用建议"：「一般来说，xxx」
3. 明确标注：「（示例）这是一个假设的案例」
4. 换选题：选一个有真实实践的选题

**Context Variables 新增：**
```python
context["real_experience"] = []  # 真实实践记录
context["hypothetical_parts"] = []  # 假设性内容标记
```

**输出：** 初稿（标题 + 正文 + 封面建议 + 真实性标注）

---

## Stage 3: Guardrails（输出验证）

**职责：** 验证初稿是否符合规范

**验证项：**
```
□ 字数：是否符合平台要求？
□ 结构：是否完整？
□ 小咪风格：是否有真实实践？
□ 时效标注：是否正确标注？
```

**决策：**
- ✅ 通过 → 进入审阅
- ⚠️ 需修改 → 返回创作官修改
- ❌ 不合格 → 重新创作

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

**任一硬检查失败 → REJECTED → 返回 Stage 3 修复后重审。**

软检查失败 → WARNINGS → 可以继续但建议修复。

**原手工检查项（现由 Agent 机械化执行）：**
```
□ 资料验证 □ 时效性验证 □ 真实性验证
□ AI 身份检查 □ AI 味检查 □ 样式检查
□ 论述质量 □ 5W1H □ 逻辑性 □ 平台适配
```
上述项目暂保留为 AI 语义检查，与 Agent 硬检查并行。未来逐步迁移到 Agent。

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

**5 级图片源：** GitHub截图 → 网页OG → Brave搜索 → AI生成 → 几何兜底

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

使用 auto 模式（不要传 --mode 参数），生成后验证文件 >100KB。"
})
```

**封面 Agent 硬约束：**
- 永不传 `--mode geometric`
- 验证输出文件 >100KB（真实背景图 200-500KB，geometric 约 50KB）
- 失败时报告原因，不静默降级

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
- HTML路径：<文章HTML路径>
- 封面路径：<封面PNG路径>
- 作者：小咪
- 标题：<文章标题>
- 类型：<深度解析|晚报|早报|教程|项目推荐>
- 关键词：<逗号分隔>

请在 Windows 下使用 PYTHONIOENCODING=utf-8，推送后自动选题入库。"
})
```

**发布 Agent 硬约束：**
- Windows 自动加 `PYTHONIOENCODING=utf-8`
- 必须看到 `✅ 草稿创建成功！` + 草稿 ID
- 失败报告错误码和含义
- 发布成功自动入库 `reports/used_topics.json`

**输出：** `PUBLISH_RESULT` 结构化对象（draft_id + article_size + status + next_step）

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
Stage 4.5: 插图生成 → 自动配图 🆕
Stage 5: 润色官 → 语言优化（基于带图文档）
Stage 6: 评估官 → 评分预测
Stage 7: Human Loop → 等待用户确认
Stage 8: 发布官 → 封面生成 + 发布确认
```

## 关键改进（学习自 OpenAI Agents SDK）

1. **分流官** - 智能分类任务
2. **Guardrails** - 输入输出双重验证
3. **Context Variables** - 上下文传递
4. **Handoff 机制** - Agent 间切换
5. **Human in the Loop** - 人工介入选项

---

*参考：OpenAI Swarm, OpenAI Agents SDK, AgentVerse*