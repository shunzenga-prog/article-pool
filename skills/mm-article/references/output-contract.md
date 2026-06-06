# mm-article 输出契约

本文件规定 `mm-article` 的输出目录、文件命名、HTML 正文格式、配图流程和封面图生成流程。真实创作时必须遵守，不能临时散落到仓库根目录或工作区外部。

## 旧文章格式基线

`mm-article` 的默认产物格式参考现有老文章池的命名，但根目录固定为 `ARTICLE_ROOT=/Users/mulin/workspace/公众号/文章`，不能写到仓库内的相对 `文章/` 目录。

```text
/Users/mulin/workspace/公众号/文章/2026年05月/0517-Claude Code新功能一屏管住所有Agent.html
/Users/mulin/workspace/公众号/文章/2026年05月/0517-Claude Code新功能一屏管住所有Agent_cdn.html
/Users/mulin/workspace/公众号/文章/2026年05月/0517-Claude Code新功能一屏管住所有Agent.png
/Users/mulin/workspace/公众号/文章/2026年05月/0517-Claude Code新功能一屏管住所有Agent-image-01.png
/Users/mulin/workspace/公众号/文章/2026年06月/0605-claude code最新实践指南.html
```

默认使用主流老格式：`/Users/mulin/workspace/公众号/文章/{YYYY}年{MM}月/{MMDD}-{safe_title}.html`。少量旧文章存在 `{YYYY-MM-DD}-{title}.html` 或 `{YYYYMMDD}-{title}.html`，这些只作为兼容读取格式，新产物不要默认使用。

所有正式文章产物都按 `ARTICLE_ROOT` 解析；不要把 `E:\...` 这样的本地绝对路径写进正文或报告给读者。

## 输出目录

### 文章目录

公众号文章默认输出到：

```text
/Users/mulin/workspace/公众号/文章/{YYYY}年{MM}月/
```

文件命名：

```text
/Users/mulin/workspace/公众号/文章/{YYYY}年{MM}月/{MMDD}-{safe_title}.html
/Users/mulin/workspace/公众号/文章/{YYYY}年{MM}月/{MMDD}-{safe_title}_illustrated.html
/Users/mulin/workspace/公众号/文章/{YYYY}年{MM}月/{MMDD}-{safe_title}_cdn.html
/Users/mulin/workspace/公众号/文章/{YYYY}年{MM}月/{MMDD}-{safe_title}_publish.html
/Users/mulin/workspace/公众号/文章/{YYYY}年{MM}月/{MMDD}-{safe_title}.png
```

规则：

- `{MMDD}` 是两位月 + 两位日，例如 `0517`。
- `{MM}` 使用两位月份，默认写 `2026年05月`，贴近老文章池主流目录。
- `{safe_title}` 使用最终标题清理文件系统非法字符后生成；保留可读中文和必要空格。
- 原始 HTML、插图版 HTML、CDN HTML、封面 PNG 使用同一 basename。
- `_publish.html` 是兼容旧文章中的发布变体，需要时才生成，不是默认主链路。
- 正文不得出现本地绝对路径，例如 `E:\...`。

### 资产目录

图片资产平铺放在文章所在的月份目录下，和 HTML 或 Markdown 文件同目录，不再为正式文章插图创建 `images_*` 或 `screenshots_*` 子目录：

```text
/Users/mulin/workspace/公众号/文章/{YYYY}年{MM}月/
```

常用文件：

```text
{MMDD}-{safe_title}-image-01.png
{MMDD}-{safe_title}-image-02.png
{MMDD}-{safe_title}-screenshot-01.png
{MMDD}-{safe_title}-source-x-01-compact.png
{MMDD}-{safe_title}-terminal-01.png
```

规则：

- 事实型截图和概念插图都平铺在同一个月份目录，用 basename 派生命名。
- 原文证据截图使用 `{MMDD}-{safe_title}-source-{platform}-{NN}-compact.png`，例如 `0606-Magenta实时音乐模型-source-x-01-compact.png`。
- HTML 正文只写同目录相对文件名，例如 `{MMDD}-{safe_title}-image-01.png`。
- 发布前由脚本上传或替换为 CDN URL。
- Agent/image_gen 直接生成的最终封面默认放到月份目录：`/Users/mulin/workspace/公众号/文章/{YYYY}年{MM}月/{MMDD}-{safe_title}.png`。

### 运行报告目录

每次运行保留一个报告目录：

```text
reports/mm-article/{YYYYMMDD-HHMMSS}-{slug}/
```

必须保存：

```text
evidence.json
source_capture.json
title_decision.json
content_prompt.md
visual_plan.json
image_requests.json
generated_images.json
review.json
publish_result.json
delivery_gate.json
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

### 原文证据截图

原文证据截图属于证据产物，先于正文起草和后续配图规划生成。它用于证明“原始网页、X 发帖、官方公告或论文页面确实这样表述”，不是装饰图。

保存规则：

- 图片平铺在文章月份目录，文件名使用 `{MMDD}-{safe_title}-source-{platform}-{NN}-compact.png`。
- 运行报告写入 `reports/mm-article/{run_id}/source_capture.json`。
- 每条记录至少包含 `source_url`、`captured_at`、`screenshot_path`、`claim_supported`、`translated`、`crop_style`、`visual_slot_id`、`reader_use`。
- 社交平台发帖默认使用 compact 截图，只保留头像、账号、正文和必要时间信息；不要把侧栏、浏览器导航、视频大块区域、推荐流一起截入正文素材。

与后续配图协调：

- `source_capture.json` 中的 `visual_slot_id` 会先占用同一视觉槽位。
- `visual_plan.json`、`image_requests.json` 和 `generated_images.json` 必须避开已占用槽位。
- 同一段落或同一视觉槽位已有原文证据截图时，后续概念插图默认跳过；如确有必要，只能改为替换该截图，或移动到下一小节的独立槽位。
- 不允许同一段落连续堆叠“原文截图 + 产品截图 + 概念图”。连续图片之间必须有承接文字、不同 claim 和明确阅读价值。

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
- 每条 `image_requests.json` 请求必须带 `paragraph_context` 和 `context_source`；生图时优先依据该段落的内容、机制、场景和关系构图，而不是只依据标题或关键词。
- 不生成只有装饰意义、无法支撑内容的图片。

### Agent-first 插图执行

1. 先用文章和视觉计划生成图片请求：

```powershell
python scripts/illustration_gen.py <article.html> --emit-image-requests reports/mm-article/{run_id}/image_requests.json --dry-run
```

2. Agent 按 `image_requests.json` 逐张生成本地图片，平铺保存到文章所在月份目录，例如 `/Users/mulin/workspace/公众号/文章/{YYYY}年{MM}月/{MMDD}-{safe_title}-image-01.png`。
   生成前先核对每条请求的 `paragraph_context`。如果上下文为空、过泛或与插入位置不一致，先回到文章段落修正请求，不直接生图。

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
      "path": "/Users/mulin/workspace/公众号/文章/2026年05月/0517-topic-image-01.png",
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
2. 如果当前环境支持 `image_gen`，Agent 直接生成无文字最终封面：

```text
/Users/mulin/workspace/公众号/文章/{YYYY}年{MM}月/{MMDD}-{safe_title}.png
```

3. 不调用 `gen_cover.py --background-image`。`gen_cover.py` 只在没有 image_gen 能力、用户明确要求真实图库/事实图片，或旧链路兜底时使用。

生成 prompt 里不要写标题文字；封面必须是纯图，不带水印、角标或来源标识。

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
- `delivery_gate.json` 存在且全部检查通过；命令为 `python scripts/validate_mm_delivery.py <文章.html> --run-dir reports/mm-article/<run_id> --title "<title>" --write-report`。
- `publish_result.json` 在发布后写入草稿 ID 或文章 ID。
- 正文没有本地绝对路径。
- 所有本地正文图片已上传或替换为 CDN URL。
