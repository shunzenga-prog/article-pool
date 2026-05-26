# mm-article 输出契约

本文件规定 `mm-article` 的输出目录、文件命名、HTML 正文格式、配图流程和封面图生成流程。真实创作时必须遵守，不能临时散落到仓库根目录或工作区外部。

## 旧文章格式基线

`mm-article` 的默认产物格式参考现有老文章池，而不是新造一套路径：

```text
文章/2026年05月/0517-Claude Code新功能一屏管住所有Agent.html
文章/2026年05月/0517-Claude Code新功能一屏管住所有Agent_cdn.html
文章/2026年05月/0517-Claude Code新功能一屏管住所有Agent.png
文章/2026年05月/images_claude_agent_view/agent-view-blog-01.png
文章/2026年5月/2026-05-18-ClaudeCode自动干活Harness3车道才稳.html
```

默认使用主流老格式：`文章/{YYYY}年{MM}月/{MMDD}-{safe_title}.html`。少量旧文章存在 `{YYYY-MM-DD}-{title}.html` 或 `{YYYYMMDD}-{title}.html`，这些只作为兼容读取格式，新产物不要默认使用。

所有路径都按当前工作区或 `ARTICLE_ROOT` 解析；不要把 `E:\...` 这样的本地绝对路径写进正文或报告给读者。

## 输出目录

### 文章目录

公众号文章默认输出到：

```text
文章/{YYYY}年{MM}月/
```

文件命名：

```text
文章/{YYYY}年{MM}月/{MMDD}-{safe_title}.html
文章/{YYYY}年{MM}月/{MMDD}-{safe_title}_illustrated.html
文章/{YYYY}年{MM}月/{MMDD}-{safe_title}_cdn.html
文章/{YYYY}年{MM}月/{MMDD}-{safe_title}_publish.html
文章/{YYYY}年{MM}月/{MMDD}-{safe_title}.png
```

规则：

- `{MMDD}` 是两位月 + 两位日，例如 `0517`。
- `{MM}` 使用两位月份，默认写 `2026年05月`，贴近老文章池主流目录。
- `{safe_title}` 使用最终标题清理文件系统非法字符后生成；保留可读中文和必要空格。
- 原始 HTML、插图版 HTML、CDN HTML、封面 PNG 使用同一 basename。
- `_publish.html` 是兼容旧文章中的发布变体，需要时才生成，不是默认主链路。
- 正文不得出现本地绝对路径，例如 `E:\...`。

### 资产目录

图片资产放在月份目录下，使用有语义的相对目录名，参考旧文章的 `images_claude_agent_view/`、`screenshots_ep5/`、`claude-code-harness-images/`：

```text
文章/{YYYY}年{MM}月/{visual_slug}/
```

常用文件：

```text
01-topic.png
02-topic.png
img-01-step.png
step1-output.png
```

规则：

- 事实型截图目录优先用 `screenshots_{topic_slug}`。
- 文章配图目录优先用 `images_{topic_slug}` 或 `{topic_slug}-images`。
- HTML 正文只写相对路径，例如 `images_claude_agent_view/agent-view-blog-01.png`。
- 发布前由脚本上传或替换为 CDN URL。
- Agent 生成的封面背景默认放到月份目录：`文章/{YYYY}年{MM}月/{MMDD}_cover_bg.png`。

### 运行报告目录

每次运行保留一个报告目录：

```text
reports/mm-article/{YYYYMMDD-HHMMSS}-{slug}/
```

必须保存：

```text
evidence.json
title_decision.json
content_prompt.md
visual_plan.json
image_requests.json
generated_images.json
review.json
publish_result.json
```

报告目录用于运行审计，保留在 workflow/repo 内即可；文章正文、封面和读者可见图片仍按上面的老文章格式输出。

## 正文 HTML 格式

正文 HTML 参考老文章结构：

```html
<!-- 文章标题或简短描述
-->
<meta charset="UTF-8">

<p style="margin:0;text-align:left;"><span style="font-size:15px;color:#2b2b28;line-height:1.85;">正文从导语开始。</span></p>
```

硬规则：

- `<meta charset="UTF-8">` 必须靠前，避免 Windows/微信预览乱码。
- 公众号后台会显示系统标题，正文第一屏不要再写同名 `<h1>` 或大字号标题。
- 正文段落用 `p + span`，文字字号通常 15px，行高约 1.85-1.9。
- 章节标题用 `border-bottom` 下划线样式。
- 图片用 `table` 包裹，`img` 使用 `width="100%"` 或 `style="width:100%;max-width:100%;"`。
- 代码块用 `<pre>`，不要用 Markdown 围栏输出公众号正文。
- 卡片只用局部 `table`，不要用大块 `div/section` 包裹全文。

## 配图流程

配图按“事实优先，概念补充”的顺序执行。

### 事实型图片

以下场景必须优先使用真实来源：

- 教程步骤、终端输出、代码运行结果。
- 产品界面、官方文档、项目页面。
- Logo、新闻图、数据图表。

可用方式：

- 浏览器截图。
- 终端截图。
- 官方页面截图。
- GitHub/文档/产品页面截图。

事实型图片不得用生成图替代。

### 概念型图片

以下场景可以使用 Agent/Codex 生图：

- 抽象概念解释。
- 方法论、趋势、观点类章节开头。
- 非事实型氛围图。
- 封面背景。

生图要求：

- 输出 PNG。
- 不伪装成真实截图、新闻现场、官方照片或产品 UI。
- 每张图必须绑定段落、用途和插入位置。
- 不生成只有装饰意义、无法支撑内容的图片。

### Agent-first 插图执行

1. 先用文章和视觉计划生成图片请求：

```powershell
python scripts/illustration_gen.py <article.html> --emit-image-requests reports/mm-article/{run_id}/image_requests.json --dry-run
```

2. Agent 按 `image_requests.json` 逐张生成本地图片，保存到月份目录下的语义图片目录，例如 `文章/{YYYY}年{MM}月/images_{topic_slug}/` 或 `screenshots_{topic_slug}/`。

3. 写入生成结果清单：

```text
reports/mm-article/{run_id}/generated_images.json
```

格式示例：

```json
{
  "images": [
    {
      "id": "image_001",
      "path": "文章/2026年05月/images_topic/01-concept.png",
      "intended_use": "解释第二节的抽象概念",
      "kind": "concept"
    }
  ]
}
```

4. 嵌入本地图片：

```powershell
python scripts/illustration_gen.py <article.html> --use-local-images reports/mm-article/{run_id}/generated_images.json
```

5. 输出 `_illustrated.html` 后再做视觉审阅。

## 封面图生成

封面是独立生产链，不能直接用旧 fallback 糊过去。

### 默认策略

1. 先写封面 brief，并保存为 `cover_brief_artifact` 或写入运行报告。brief 必须从文章主张提炼，包含文章主张、内容符号、品牌元素、主体、构图、禁用元素、缩略图目标和模型归因边界。
2. 如果当前环境支持 `image_gen`，Agent 先生成无文字封面背景：

```text
文章/{YYYY}年{MM}月/{MMDD}_cover_bg.png
```

3. 再调用封面脚本输出最终封面：

```powershell
python scripts/gen_cover.py --title "<title>" --background-image "文章/{YYYY}年{MM}月/{MMDD}_cover_bg.png" --output "文章/{YYYY}年{MM}月/{MMDD}-{safe_title}.png"
```

当前封面脚本是纯图封面模式，`--title` 主要用于关键词、主题和元数据选择；生成背景图的 prompt 里不要写标题文字。

如果使用内置生图工具且宿主没有暴露底层模型名，报告里只能记录“内置 image_gen / Agent 生成”，不得声称具体底层模型名。只有显式 CLI/API 返回模型配置时，才能记录具体模型。

### 封面要求

- 尺寸 1200x675。
- 默认不在图片里重复文章标题。
- 亮度自然，主体明确，背景简洁。
- 缩略图尺寸下仍能看清主体。
- 不伪造产品 UI、官方截图、Logo 或新闻现场。
- 封面要看得出文章主张、内容机制和合法品牌元素；不能只有通用芯片、通用光线或普通素材站科技图。
- 用户反馈“难看”“不像你的水平”“缺少品牌元素”等审美失败时，必须回到 brief 改文章主张、品牌元素、构图和避雷词，再重新生成封面。
- 在支持生图时，`geometric` 兜底不能当作成功；要重试或报告生图不可用。

## 发布前输出检查

发布前必须确认：

- 原始 HTML 存在。
- `_illustrated.html` 存在，或明确说明本篇不需要插图。
- 封面 `.png` 存在且通过视觉检查。
- `review.json` 存在且硬门禁通过。
- `publish_result.json` 在发布后写入草稿 ID 或文章 ID。
- 正文没有本地绝对路径。
- 所有本地正文图片已上传或替换为 CDN URL。
