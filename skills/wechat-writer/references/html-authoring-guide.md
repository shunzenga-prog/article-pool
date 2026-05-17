# HTML 编写规范

创作文章 HTML 时的结构规则和模板语法。

## 文件头部

**注释块后必须紧跟 `<meta charset="UTF-8">`**，否则 Windows 浏览器默认用 GBK 解码导致中文乱码。

```html
<!-- 文章标题或简短描述
-->
<meta charset="UTF-8">
```

> ⚠️ 注意：`<!--` 在第一行开头，`-->` 在第二行结尾，中间是注释内容。不要把 `-->` 写第一行——会导致注释提前闭合，第二行的 `-->` 裸露为可见文本。

## 文章 HTML 骨架

> ⚠️ 公众号后台会在正文外自动显示文章标题。HTML 正文第一块可见内容不要再写同名大标题，也不要用 `<h1>` 或大字号段落重复标题。文件头部注释可以写标题，正文应直接从导语/钩子开始。

```html
<!-- 标题
-->
<meta charset="UTF-8">

<!-- 正文：直接从导语开始，不重复公众号系统标题 -->
<p style="margin:0 0 8px 0; text-align:left;"><span style="color:#333; font-size:15px; line-height:1.8;">
正文文字放这里。样式放 span 上，不放在 p 上。
</span></p>

<!-- 章节标题：必须带 border-bottom -->
<p style="margin:32px 0 0 0; text-align:left;"><span style="color:#1a1a2e; font-size:17px; font-weight:bold; border-bottom:2px solid #1E88E5; padding-bottom:4px;">章节标题</span></p>

<!-- 图片：用 table 包裹，width="100%" -->
<table width="100%" cellpadding="0" cellspacing="0" style="margin:16px 0 0 0;"><tr><td style="padding:0; text-align:center;">
<img width="100%" src="screenshots/step1.png" alt="图片说明">
</td></tr></table>

<!-- 代码块 -->
<pre style="background:#1e1e2e; color:#cdd6f4; padding:14px 16px; font-size:13px; line-height:1.6; overflow-x:auto; white-space:pre-wrap;">code here</pre>

<!-- 卡片：用 table 做局部容器 -->
<table width="100%" cellpadding="0" cellspacing="0" style="margin:16px 0 0 0; background:#f5f7fa; border-left:3px solid #1E88E5;">
<tr><td style="padding:14px 16px;">
<p style="margin:0;"><span style="color:#333; font-size:14px;">卡片内容</span></p>
</td></tr>
</table>
```

## 占位符系统（模板专用）

仅在复用模板时使用。即时创作的文章不需要。

| 标记 | 用途 | 示例 |
|------|------|------|
| `<!-- REPLACE:key -->default<!-- /REPLACE -->` | 单值替换 | `<!-- REPLACE:标题 -->默认<!-- /REPLACE -->` |
| `<!-- REPEAT:名称 -->...<!-- /REPEAT -->` | 列表循环 | 夹在重复区块的首尾 |
| `<!-- REPLACE:keyN -->` | 固定编号 | `<!-- REPLACE:条件1 --><!-- /REPLACE -->` |

## ⚠️ HTML 实体陷阱

**微信会原样显示装饰性 HTML 实体，而不是渲染它们。** 以下实体在微信中**显示为裸代码**：

| ❌ 禁止使用 | 实际显示效果 | ✅ 用 Unicode 字符替代 |
|-----------|-------------|---------------------|
| `&middot;` | 显示为 `&middot;` 文字 | `·` (U+00B7) |
| `&bull;` | 显示为 `&bull;` 文字 | `•` (U+2022) |
| `&raquo;` `&laquo;` | 显示为裸代码 | `»` `«` |
| `&mdash;` `&ndash;` | 显示为裸代码 | `—` `–` |
| `&hellip;` | 显示为裸代码 | `…` (U+2026) |
| `&copy;` `&reg;` `&trade;` | 显示为裸代码 | `©` `®` `™` |

**例外：** 以下功能实体正常工作（因为它们有结构意义）：
- `&lt;` `&gt;` `&amp;` — 用于显示 `<` `>` `&` 字符本身
- `&#数字;` 形式的数字字符引用（如 `&#183;`）也正常

**原则：文章正文中一律使用 Unicode 字符本身，不要用 HTML 实体名。**

## WeChat CSS 兼容性

详见 `wechat-css-guide.md`。核心原则：

- ❌ 禁止 `<div>` / `<section>` — 会被转为 `<p>` 并剥离样式
- ❌ 禁止在 `<p>` 上放 `font-size` / `color` — 只能放 `text-align`
- ❌ 禁止用 `<table>` 包裹全文 — 手机上宽度问题和黑缝
- ❌ 禁止装饰性 HTML 实体（`&middot;` `&bull;` `&mdash;` 等）— 微信原样显示
- ✅ 卡片用 `<table><tr><td>` 做局部容器
- ✅ 文字样式放 `<span style="...">` 上
- ✅ 图片用 `<img width="100%">`
- ✅ 特殊字符直接用 Unicode（`·` `—` `…` 等），不用实体名
