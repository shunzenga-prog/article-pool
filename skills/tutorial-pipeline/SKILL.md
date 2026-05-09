---
name: tutorial-pipeline
description: 教程类文章专属创作流水线。分步骤写作，每一步写完后立即生成配图，确保图文一一对应。触发：写教程、教程文章、AI实战教程。
---

# 教程文章创作链（Tutorial Pipeline）

教程文章与普通文章的本质区别：**读者要跟着操作，每一步都需要看到真实的执行过程和结果。** 因此教程流水线的核心设计是"写一步 → 截图 → 验证 → 下一步"，而非"写完再补图"。

**⚠️ 教程覆盖 wechat-writer 的简洁规则：** `wechat-writer/SKILL.md` 中的"段落 ≤5 行""表格 ≤2 个""金句 ≥1 句"等规则针对深度解析和观点文章。教程类文章需要充分展开——代码需要完整展示（10-30 行而非 3-5 行）、概念需要多次解释、工具需要完整函数而非片段。详见下方「教程写作深度标准」。

## 触发场景

- "写一篇教程"
- "写教程文章"
- "AI实战教程"
- 分流官识别到文章类型为"教程"

## 架构设计

```
用户请求（教程类）
    ↓
┌─────────────┐
│ 步骤规划官  │ ← 拆解教程为 N 个步骤，标注每步需要的截图
└─────┬───────┘
      ↓
┌─────────────┐
│ Guardrails  │ ← 输入验证（可复现性检查）
└─────┬───────┘
      ↓
┌─────────────────────────────────────┐
│  分步创作官（核心差异）              │
│                                     │
│  for 每一步 in 步骤列表:            │
│    1. 写这一步的文字内容             │
│    2. 执行代码/命令，截取真实输出    │
│    3. 将截图嵌入文章该步骤位置       │
│    4. 验证截图与文字描述一致         │
│    5. 进入下一步                     │
└─────────────────────────────────────┘
      ↓
┌─────────────┐
│ Guardrails  │ ← 输出验证（截图覆盖检查）
└─────┬───────┘
      ↓
┌─────────────┐
│ 审阅官      │ ← 教程专项检查
└─────┬───────┘
      ↓
┌─────────────┐
│ 润色官      │ ← 语言优化（保留所有截图位置）
└─────┬───────┘
      ↓
┌─────────────┐
│ 评估官      │ ← 教程实用性评分
└─────┬───────┘
      ↓
┌─────────────┐
│ Human Loop  │ ← 人工确认
└─────┬───────┘
      ↓
┌─────────────┐
│ 发布官      │ ← 封面生成 + 发布
└─────────────┘
```

## ⛔ 硬性质量门禁（HARD GATE — 全流程）

以下检查点在每个阶段结束时执行。**任一不通过即阻断，不得跳到下一阶段。** 不可用"后面补"绕过。

### G1: 步骤规划完成后
```
□ 步骤数 ≥ 3
□ 每类步骤至少 1 张规划截图（截图规划数 ≥ 步骤数 × 0.8）
□ overview 步骤已规划流程图
□ execute/output 步骤已规划终端截图
□ 代码文件路径已验证存在（ls 确认）
```

### G2: 每个步骤写完后
```
□ 代码展示：完整可运行（10-30 行），非伪代码
□ 代码讲解：≥3 处 L2 逐行解释 + ≥1 处 L3 设计决策说明
□ 截图已生成且文件存在（ls 确认文件 > 10KB）
□ 截图已嵌入文章中（HTML 中有对应 <img> 标签）
□ 截图中无本地路径（E:\、/Users/、教程资源/ 等）
```

### G3: 全部步骤写完后
```
□ 截图总数 ≥ 步骤数 × 0.8（用 ls | wc -l 确认）
□ 每 1500 字 ≥ 1 张图（估算字数后确认）
□ 有且 ≥1 张流程图
□ 有且 ≥2 张终端执行截图
□ 有避坑指南章节（≥3 个具体错误 + 正确做法）
□ 代码与教程资源目录中的文件一致
```

### G4: HTML 生成后（审阅阶段）
```
□ 运行: python scripts/review_html.py article.html --tutorial --json
□ 退出码必须为 0（passed: true）
□ H1/H2/H3 三项硬检查全部 PASS
□ 教程统计：截图 ≥ 步骤数 × 0.8
```

### G5: 发布前
```
□ 封面图文件存在且 > 100KB
□ 选题已入库（python scripts/topic_tracker.py add "标题" "关键词" "教程"）
□ review_html.py --tutorial 再次确认通过
```

## Context Variables（教程专属扩展）

```python
context = {
    # 继承通用字段
    "platform": "wechat",
    "topic": "选题内容",
    "article_type": "tutorial",        # 🆕 教程类型标识
    # 教程专属字段
    "steps": [],                       # 步骤列表：[{"id":1, "title":"...", "screenshots":[], "code_file":"..."}]
    "current_step": 0,                 # 当前创作到第几步
    "screenshot_count": 0,             # 已生成的截图总数
    "reproducibility": {               # 可复现性验证
        "code_executed": False,        # 代码是否实际运行过
        "output_verified": False,      # 输出是否与文中描述一致
    },
}
```

---

## Stage 0: 步骤规划官（Step Planner）

**职责：** 将教程拆解为有序步骤，规划每步需要的截图

**输入：** 选题 + 教程主题

**输出：** 步骤列表，每步包含：
```python
step = {
    "id": 1,
    "title": "环境准备：安装 Python 和依赖",
    "type": "overview|setup|code|execute|output|config|chart|summary",
    "screenshots_needed": [
        {"type": "terminal", "desc": "python --version 命令输出"},
    ],
    "code_file": None,  # 如果有对应代码文件
    "must_execute": True,  # code/execute/chart/setup 默认 True，其余 False
    "screenshot_mode": "immediate",  # immediate（默认）| batch-per-round
}
```

**screenshot_mode 说明：**

| 模式 | 行为 | 适用步骤类型 |
|------|------|------------|
| `immediate` | 写一步 → 截图 → 嵌入 → 下一步 | execute, output, code, chart（必须实时验证） |
| `batch-per-round` | 同 round 步骤写完 → 批量截图 → 回填 | setup, config, overview, summary（不依赖实时输出） |

**must_execute 默认值：**
- `code / execute / chart / setup` → **True**（需要真实运行验证）
- `overview / summary / output / config` → **False**（描述性内容，不涉及执行）

**步骤类型与截图要求映射：**

| 步骤类型 | 必须截图 | 截图类型 | 截图模式 | 示例 |
|---------|---------|---------|---------|------|
| overview | 1 张 | 流程图 | batch-per-round | 流水线架构全景图 |
| setup | 1 张 | 终端安装输出 | batch-per-round | pip install 的输出 |
| code | 1-2 张 | 代码编辑器 + 终端运行 | immediate | 完整代码块 + 运行结果 |
| execute | 1 张 | 终端彩色输出 | immediate | python script.py 的真实输出 |
| output | 1 张 | 浏览器/界面截图 | immediate | 生成的 HTML、图表、页面 |
| chart | 1 张 | matplotlib 图表 | immediate | 数据可视化图表输出 |
| config | 1 张 | 配置界面截图 | batch-per-round | 环境变量设置、定时任务界面 |
| summary | 0-1 张 | 可选，汇总对比 | batch-per-round | 整体效果 |

**规划原则：**
- 每一类步骤至少 1 张截图
- execute 和 output 类步骤必须有图（这是读者最想看到的）
- 教程步骤总数 vs 截图总数，比例不低于 1:0.8
- ⭐ 规划完成后，定一张「风格卡」（基调+配色+强调方式+节奏），见 `skills/wechat-writer/SKILL.md` 风格规划章节。教程类文章推荐"干净理性"风格：蓝灰色系 + 暗色代码块 + 绿色标注成功项

---

## Stage 1: Guardrails（输入验证）

在通用验证之上，教程专属检查：

```
□ 可复现性 - 读者能否照着操作？需要的工具是否免费/可获取？
□ 环境假设 - 是否说明了操作系统、Python 版本等前置条件？
□ 代码完整性 - 所有引用的代码是否在教程资源目录中有实际文件？
□ 零依赖原则 - 是否优先使用标准库，避免复杂的依赖安装？
□ 国内可访问 - 用到的 API、网站是否国内能访问？
```

**决策：**
- ✅ 通过 → 进入分步创作
- ❌ 不通过 → 调整教程设计

---

## Stage 2: 分步创作官（Step-by-Step Creator）⭐ 核心

**职责：** 按步骤顺序创作，每步写完立即截图嵌入，再进入下一步。

**与通用 Pipeline 的本质区别：**
- 通用：写完所有文字 → 审阅 → 最后补图
- 教程：写第1步 → 截图 → 嵌入 → 写第2步 → 截图 → 嵌入 → ...

### 单步执行流程

**模式 A: immediate（默认 — execute/output/code/chart 类步骤）**

```
for step in steps:
    ① 写文字
      - 这一步做什么、为什么
      - ⭐ 展示关键代码片段并逐行解释逻辑（不是只描述结果）
      - ⭐ 解释设计决策：为什么选这个方案？有没有替代方案？
      - 预期结果说明
    
    ② 生成截图（立即！）
      - 执行代码 → 捕获真实输出
      - 或打开界面 → Playwright 截图
      - 或渲染终端 → terminal_screenshot.py（xterm.js + OS 自适应标题栏）
      - 或图表 → chart_screenshot()（capture.chart）
    
    ③ 嵌入文章
      - 截图插入到该步骤文字之后
      - 用 table 布局包裹 <img>
      - 加引导文字说明
    
    ④ 自检
      - 截图内容是否与文字描述一致？
      - 输出数据是否真实？
      - 截图中有没有泄露本地路径？
      - ⭐ 代码解释是否到位？（读者看完这一步能理解代码在做什么）
    
    ⑤ 进入下一步
```

**模式 B: batch-per-round（setup/config/overview/summary 类步骤）**

```
同轮 immediate 步骤完成 → 收集本 round 所有 batch 步骤 → 批量截图 → 回填嵌入

例如：
  Round 1: step1(overview) + step2(setup)  → 都标 batch-per-round
    先写 step1 文字、step2 文字 → 批量生成 overview 流程图 + setup 终端截图 → 分别嵌入
  Round 2: step3(code) + step4(execute) + step5(output) → 标 immediate
    逐个写 → 截图 → 嵌入（正常 immediate 流程）
```

### ⭐ 教程写作深度标准（覆盖 wechat-writer 的简洁规则）

> wechat-writer 的"段落 ≤5 行""表格 ≤2 个"不适用于教程。教程需要更多篇幅来充分讲解每一步。

**教程代码必须满足以下 3 层讲解，缺一不可：**

| 层次 | 要求 | 错误示例 | 正确示例 |
|------|------|---------|---------|
| L1 代码展示 | 完整可运行的代码块（10-30 行），不是伪代码或函数签名 | "Agent 循环调用 think() 和工具" | 展示完整的 run_agent() 函数 20 行代码 |
| L2 逐行解释 | 挑 3-5 个关键行，逐一说明：这行做什么、为什么这样写、改一个参数会怎样 | （无解释） | "MAX_STEPS=10 → 安全阀，防止无限循环。设成 3 太激进，设成 50 太长。10 是经验值" |
| L3 设计决策 | 说明为什么选这个方案而不是替代方案 | "用了装饰器模式" | "用装饰器而非手动字典：手动要改两处(定义+注册)，装饰器一处搞定。接 AI API 时装饰器能自动生成 tool definitions" |

**教程内容密度要求：**

- 每个核心概念至少用两种方式解释（文字 + 代码 + 对比表格中选两种）
- 每个工具的代码必须展示<b>完整函数</b>（不是"关键几行"）
- 必须有"避坑指南"或"常见错误"章节（≥3 个具体错误 + 正确做法）
- 必须有多轮终端执行输出（不是 1 次，是不同输入/不同场景的多次运行）
- 教程篇幅应显著长于同主题的深度解析文章（教程教人上手，深度解析让人理解）
- **安全相关代码必须展示攻击输入 + 过滤后结果对比**（如 calculator 的正则过滤前后对比）

**领域特定要求（AI/编程教程）：**

- Agent/API 类教程：必须展示"模拟版本"和"产品化版本"的代码对比
- 数据处理类教程：必须展示清洗前后的数据对比
- 任何涉及用户输入的工具：必须展示安全过滤的效果

### 截图生成工具速查

```bash
# 流程图 / 架构全景图 → Mermaid 流程图
python scripts/flowchart_gen.py --file flow.json -o step0_flowchart.png

# 终端命令输出 → 终端风格截图（xterm.js + OS 自适应标题栏）
python scripts/terminal_screenshot.py output.txt --os windows --title "PowerShell" -o stepN_terminal.png

# 浏览器页面/工具界面 → Playwright 截图
python scripts/screenshot_util.py single https://example.com --width 800 --height 900 -o stepN_browser.png

# HTML 文件效果 → 本地文件截图
python scripts/screenshot_util.py file output.html --width 800 --height 900 -o stepN_output.png

# 代码截图：代码块语法高亮
python scripts/code_image_generator.py code script.py -o stepN_code.png

# Matplotlib 图表 → 子进程执行 + 自动 CJK 字体注入
python scripts/code_image_generator.py chart chart_code.py -o stepN_chart.png

# 配置界面 → 手动截图后放入 screenshots 目录
```

> **编程调用：** 所有截图工具已统一为 `scripts/capture/` 模块。
> ```python
> from capture import terminal_screenshot, browser_screenshot, code_to_image, flowchart_to_image, chart_screenshot
> ```

### 禁止事项

- ❌ 写完所有步骤再回头补图——输出可能变了，对不上
- ❌ 用历史截图冒充当前执行——时间戳、数据要一致
- ❌ 截图里出现 `E:\WorkSpace\创作\...` 等真实本地路径
- ❌ 用文字代码块模拟终端输出代替真实截图
- ❌ code/execute 类步骤只描述结果不展示代码——读者学不到东西
- ❌ code/execute 类步骤只列函数名不解释逻辑——读者不知道每行在干什么

---

## Stage 3: Guardrails（输出验证）

教程专属验证：

```
□ 步骤完整性 - 每个计划步骤都有对应的文字 + 截图？
□ 截图覆盖 - 截图数 ≥ 步骤数 × 0.8？
□ 截图真实性 - 所有截图都来自本次实际执行？（不是历史文件）
□ 代码一致性 - 文中的代码块和实际执行的脚本是否一致？
□ 代码解释完整性 - code/execute 类步骤是否展示了关键代码 + 解释了设计思路？（非 code 类步骤不检查）
□ 路径清洁 - 截图中没有 E:\WorkSpace、教程资源/ 等本地路径？
□ 输出一致性 - 文中描述的数据（条数、耗时）与截图中的一致？
```

---

## Stage 4: 审阅官（Tutorial Reviewer）

通用审阅 + 教程专项：

```
□ 步骤逻辑 - 步骤顺序是否合理？读者能按顺序操作吗？
□ 代码正确 - 文中的代码复制出来能直接跑吗？
□ 代码讲解 - 每个核心函数是否展示了关键代码 + 解释了设计思路？
□ 截图到位 - 每个关键操作都有截图吗？（≥1张/步骤）
□ 截图位置 - 截图是否紧跟对应的文字说明？
□ 本地路径 - 文章中没有任何本地文件路径？
□ 环境说明 - 是否说清了 OS、Python 版本等前提？
□ 前置知识 - 是否说明了读者需要什么基础？
□ 预期管理 - 是否写了"如果遇到 XX 错误怎么办"？
```

---

## Stage 5-8: 润色 → 评估 → 人工确认 → 发布

与通用 Pipeline 相同，但注意：
- **润色时保留所有截图位置**，不要在优化文字时打乱图文对应关系
- **评估时加入教程评分维度**：可复现性、截图质量、步骤清晰度
- **发布时确认封面图为教程风格**（tag 用 "AI 实战教程"）
- **选题入库时类型标记为 "教程"**

### Stage 8: 封面生成（教程专用）

```bash
# 教程封面：使用 gen_cover.py（强制 auto 模式，绝不传 --mode geometric）
python scripts/gen_cover.py \
    --title "保姆级教程：5 分钟上手 XX" \
    --subtitle "零基础也能学会" \
    --output cover.png
```

> ⚠️ **永不传 `--mode geometric`**。auto 模式内置了 geometric 兜底（5级级联的最后一级），无需手动指定。手动传 geometric 会跳过真实背景图搜索，产出的纯色封面只有 ~50KB，不符合 >100KB 的质量要求。

**教程封面参数建议：**
- 不传 `--mode`——默认 auto，自动级联搜索背景（OG→Pexels→AI→Unsplash→Brave→geometric）
- 标题格式偏好：「保姆级教程：xxx」或「手把手教你 xxx」
- tag 用 `AI 实战教程` / `技术教程`

---

## 发布后验证

```
□ 在手机端预览，检查截图是否清晰可读
□ 验证所有代码块在手机端不溢出
□ 检查图片 alt 文字
□ 确认后台回复关键词已配置
```

---

## 与其他 Pipeline 的关系

| Pipeline | 适用场景 | 截图策略 |
|---------|---------|---------|
| tutorial-pipeline | 教程、实战、操作指南 | 分步截图（核心） |
| article-pipeline（通用） | 深度分析、观点、热点 | Stage 4.5 统一配图 |
| news-pipeline（待建） | 早报、晚报、日报 | 封面图 + OG 图 |

分流逻辑见 `skills/article-pipeline/SKILL.md` Stage 0。

---

## 参考

- `skills/wechat-writer/SKILL.md` — 写作规范 + 教程截图规范 + 代码讲解规范
- `skills/cover-gen/SKILL.md` — 封面图生成
- `skills/illustration-gen/SKILL.md` — 通用插图生成（教程不依赖此流程）
- `skills/wechat-writer/references/html-authoring-guide.md` — HTML 编写规范（文件头部、骨架、WeChat CSS 兼容性）
