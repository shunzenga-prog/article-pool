# Article Pool 项目问题分析报告

---

## 一、样式问题（严重）

### 1.1 文章模板 `article-template.html` 致命问题

**h1 标题在微信中不可见**

第 72-76 行使用了 `-webkit-background-clip: text` + `-webkit-text-fill-color: transparent` 实现渐变色标题。这在微信公众号编辑器里会被完全剥离，导致标题文字消失，只留下底部的 border-bottom 线。

```css
/* ❌ 当前写法 — 微信不支持 */
h1 {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
```

微信内置浏览器对 CSS 属性支持非常有限。需要改用纯色 + border-left 或底部渐变装饰条。

**暗黑模式适配完全无效**

全文大量使用 `@media (prefers-color-scheme: dark)`——这在微信里完全不起作用。微信内置浏览器不传递系统主题偏好，且微信公众号文章的 CSS 会被编辑器二次处理。这些暗黑模式代码纯属死代码，徒增文件体积。

**h1 的 `padding: 15px 0` + `border-bottom` 组合导致视觉上标题与装饰线分离**

渐变文字不可见时，用户看到的是一段空白区域下面有一条灰线，非常诡异。

**表格移动端适配方案粗糙**

第 184 行 `display: block; overflow-x: auto;` 让表格在小屏上横向滚动，但没有任何视觉提示（如滚动阴影），用户不知道可以横滑。

**模板内容与规范自相矛盾**

模板里示例标题写着"二、代码示例"、"三、数据对比"、"四、配图展示"，但 SKILL.md 里明确规定"不要用一、二、三的序号"。模板本身就在教用户犯错。

### 1.2 封面模板 `cover-template.html` 问题

**中文标题溢出**

主标题字号 72px，line-height 1.4，宽度 60%。中文 12 个字在大约 864px 宽（900*60%*1.6 估算）内容区域内必然溢出——但实际可用的汉字宽度远小于此。实际测试：标题超过 8 个字就会折行或溢出。

**下载功能是假的**

`downloadCover()` 函数（357 行）只弹出一个 alert，告诉用户"用截图工具"。这不是功能，这是一个解释为什么功能不存在的对话框。

**配色方案混乱**

第 7 个配色方案（287 行）同时设置了 `background` 和 `background-image`——后者覆盖前者，实际显示纯黑色 `#1a1a2e`。而且内嵌的 SVG data URI 因为引号转义问题根本不会渲染。

**封面生成逻辑缺少关键输出**

脚本只能生成 URL，无法直接生成可用的 JPG/PNG 文件供公众号 API 上传。cover-template.html 是浏览器端的，「截图保存」是唯一靠谱的导出方式——这不能叫"生成器"。

### 1.3 每日早报模板 `daily-brief-template.html` 简陋

与 article-template.html 精心的 400+ 行 CSS 形成鲜明对比，这个模板仅有 65 行样式，且：

- 没有中文字体栈（只有 system-ui 字体）
- 没有响应式适配
- 没有图片样式
- 没有链接样式
- `.section-title` 用 border-bottom 做彩色下划线，视觉效果单调
- 卡片间距用 margin-bottom，缺乏呼吸感

给人的感觉像是两个不同的人写的，完全不统一。

### 1.4 `wechat_publish.py` 的 Markdown→HTML 转换原始

`markdown_to_html()` 函数（47-152 行）输出的 HTML 极其简陋：

- 标题全是裸 `<h1>` `<h2>` `<h3>` 标签，无任何样式，字体大小全由浏览器默认决定
- blockquote 只有 `border-left: 3px solid #ccc` 和灰色文字
- 表格样式是浅灰表头 `#f5f5f5` + 浅灰边框 `#ddd`，与 article-template 的渐变紫表头完全不一致
- 代码块用 `#f6f8fa`（GitHub 配色），但 article-template 用 `#f5f5f5`
- 没有文章级别的包装结构——article-template 有精心的 body/max-width/font 设置，而 publish 脚本的输出是裸 HTML 片段
- 分隔线 `hr` 样式与 article-template 不同

**这导致一个严重问题：通过 SKILL.md 规范写出的 HTML（参考 article-template）和通过脚本自动转换的 HTML（使用 publish 脚本）外观完全不同。**

### 1.5 模板文件重复

以下文件内容完全相同但各自维护：

| 文件 1 | 文件 2 |
|--------|--------|
| `templates/article-template.html` | `skills/wechat-writer/templates/article-template.html` |
| `templates/cover-template.html` | `scripts/cover-template.html` |

重复意味着修改一处忘了另一处就会产生不一致。

### 1.6 AI 早报 SKILL.md 的内联样式散乱

`ai-daily-news-get/SKILL.md` 中硬编码了大段带内联 style 的 HTML 模板。各元素的颜色值、字号、边距散布在各处，没有形成可复用的设计令牌（design tokens）。

---

## 二、功能问题

### 2.1 Agent 管线只是文档，没有实现

README 和 SKILL.md 中描述的 6 个 Agent（分流官、创作官、审阅官、润色官、评估官、发布官）及完整协作流程，在整个项目代码中没有任何实现。

`agents/pipeline-config.json` 是一个空壳 JSON。`article-pipeline/SKILL.md` 中的 Python 伪代码示例（如 `handoff_to_creator()`）只是示意，不存在可执行代码。

**这不是"不成熟"的问题——核心卖点根本没有实现。**

### 2.2 引用了不存在的脚本

以下文件在 SKILL.md 或代码中被引用但实际不存在：

- `scripts/generate-article-images.py` — wechat_publish.py 第 226 行动态导入
- `scripts/verify-news-date.py` — news-aggregator/SKILL.md 第 197 行引用
- `scripts/scrape-news-sources.py` — 被引用，但实现基本为空
- `scripts/wechat-upload-image.py` — 被引用，未审查但文件名暗示独立功能
- `skills/hotspot-tracker/scripts/check-hotspots.sh` — 存在但内容是占位符

### 2.3 错误处理几乎不存在

`scrape-36kr-fixed.py` 第 60 行：
```python
except:
    continue
```

裸 `except` 吞掉所有异常，包括 KeyboardInterrupt 和 SystemExit。一旦 Playwright 连接失败或页面结构变化，脚本静默返回空列表，用户完全不知道发生了什么。

`wechat_publish.py` 中上传封面失败只打印警告继续执行。获取 access_token 失败后直接 `sys.exit(1)` 但没有任何重试逻辑。

### 2.4 硬编码问题

- `wechat_publish.py` 第 167 行：digest 写死为 "智能体元年、NVIDIA Blackwell、政策定调、市场数据"
- `cover-template.html` 默认标题和副标题写死
- `scrape-36kr-fixed.py` 输出路径写死（虽然支持环境变量，但默认值指向特定用户目录）
- 多处引用 `~/.openclaw/workspace/` 路径，假设了特定的 OpenClaw 安装布局

### 2.5 时效性黑名单已过期

多个 SKILL.md 中的「过时信息黑名单」标注日期为 2026-04-07，距今已过 20 天。AI 领域月月有新模型，这份名单需要持续维护机制，而非静态列表。

### 2.6 缺少关键的 `generate-article-images.py`

wechat_publish.py 的 `process_article_images()` 函数尝试动态导入此模块，但它不存在。每 300 字配一张图的核心功能因此无法运行。

---

## 三、设计与架构问题

### 3.1 没有统一的设计系统

项目中至少有 4 套不同的 CSS 方案：

1. `article-template.html` — 精心设计的 400 行 CSS（含渐变、暗黑模式）
2. `daily-brief-template.html` — 65 行极简 CSS
3. `wechat_publish.py` markdown_to_html — 内联样式集合
4. `ai-daily-news-get/SKILL.md` — 硬编码内联 HTML 样式

它们之间颜色、字号、间距各不相同。例如强调色：article-template 用 `#667eea` 紫，daily-brief 用 `#E74C3C` 红，wechat_publish 用 `#ccc` 灰——同一个品牌下的产出看起来完全不像一家人。

### 3.2 配色方案不适合内容消费

article-template 主色调 `#667eea → #764ba2` 紫蓝渐变是典型的 SaaS 产品 / 后台管理配色。这不是内容阅读场景的合适选择。主流公众号（量子位、机器之心、差评）使用克制的中性色为主，品牌色只做点缀。

### 3.3 没有考虑微信公众号 CSS 白名单

微信公众号编辑器对 CSS 有严格限制。项目中的很多 CSS 属性（如 `background-clip: text`、`linear-gradient` 在非 background 上的使用、`transition`）会在粘贴时被剥离。大量精心编写的 CSS 实际上传不到公众号。

### 3.4 项目结构臃肿

对 6 个 Skills 每个都有独立的 `references/` 子目录，但 wechat-writer 下的 10 个 reference 文件有很多内容重复（如 viral-guide.md 和 xiaohongshu-writer 的 viral-guide.md 各自维护）。这些 reference 文件本质上是写给 AI 看的提示词，不需要分成 10 个文件。

---

## 四、优先级排序

| 优先级 | 问题 | 影响 |
|--------|------|------|
| P0 | h1 渐变文字在微信中不可见 | 文章发布后标题消失 |
| P0 | Agent 管线没有实现代码 | 核心卖点是假的 |
| P0 | 缺少 generate-article-images.py | 配图功能缺失 |
| P1 | 模板文件重复且不一致 | 维护混乱 |
| P1 | 4 套 CSS 方案各自为政 | 品牌形象割裂 |
| P1 | 封面下载功能是假的 | 用户体验断裂 |
| P1 | 暗黑模式代码完全无效 | 死代码 |
| P2 | 错误处理缺失 | 静默失败 |
| P2 | 时效性黑名单过时 | 产出可能过时 |
| P2 | 硬编码过多 | 部署困难 |
| P3 | 缺少测试 | 质量无保障 |
| P3 | 配色不适合内容消费 | 视觉体验不佳 |
