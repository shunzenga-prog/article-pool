# 微信公众号 CSS 兼容性规范

创作流程中最容易出问题的一环。公众号**预览时样式正常**，但**点击发布后**会对 HTML 做强制改写，导致样式丢失。发布前必须逐条检查。

## 发布时 DOM 改写的坑

```
预览时正常的样式 → 发布后可能崩掉，因为：
1. 所有 <div> / <section> → 被转为 <p>（且 <p> 上的 style 被全部剥离）
2. <table> / <td> / <span> / <h1>-<h6> / <b> / <strong> / <pre> / <code> → style 保留
```

## 元素安全清单

| 元素 | style 是否安全 | 用途 |
|------|--------------|------|
| `<table>` `<td>` `<th>` | ✅ 安全 | 容器布局、背景色、内边距 |
| `<span>` | ✅ 安全 | 文字颜色、字号、加粗 |
| `<h1>`-`<h6>` | ✅ 安全 | 标题样式 |
| `<b>` `<strong>` | ✅ 安全 | 加粗+颜色 |
| `<pre>` `<code>` | ✅ 安全 | 代码块 |
| `<img>` | ✅ 安全 | 图片尺寸、边距 |
| `<p>` | ⚠️ 仅保留 `text-align` | 段落文本（样式必须放内嵌 `<span>` 上） |
| `<div>` `<section>` | ❌ 完全不可用 | 会转为 `<p>` 并丢失所有样式 |

## 编写铁律

```html
<!-- ❌ 错误：div 做容器 + p 上放样式 -->
<div style="background:#f5f5f5; padding:20px;">
  <p style="font-size:15px; color:#333;">内容</p>
</div>

<!-- ✅ 正确：table 做容器，span 做文字 -->
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f5f5;">
<tr><td style="padding:20px;">
  <p><span style="font-size:15px; color:#333;">内容</span></p>
</td></tr>
</table>
```

## CSS 属性黑名单

| ❌ 会失效 | ✅ 替代方案 |
|-----------|-----------|
| `border-radius` | 移除（微信不支持圆角） |
| `box-shadow` | 移除 |
| `display:flex` / `display:grid` | `<table>` 表格布局 |
| `display:inline-block` | 省略，span 内联即可 |
| `gap` / `justify-content` / `align-items` | `<td>` + `padding` / `vertical-align` |
| `linear-gradient(...)` | 实色 `background:#色值` |
| `letter-spacing` | 移除 |
| `font-style:italic` | 移除 |
| `text-transform:uppercase` | 直接大写文本 |
| `opacity` | 使用直接色值 |
| `font-family` 自定义字体 | 移除，用系统默认字体 |
| `padding` / `margin` 在 `<p>` 上 | 在 `<td>` 或 `<span>` 上设置 |

## 快速检查清单（发布前逐条过）

- [ ] 没有使用 `<div>` / `<section>` 标签
- [ ] 所有文字样式用 `<span style="...">` 包裹，不在 `<p>` 上设置
- [ ] 没有 `border-radius`、`flex`/`grid`、`box-shadow`、`gradient` 等黑名单属性
- [ ] 所有容器布局用 `<table><tr><td>` 实现
- [ ] 正文第一块可见内容不是文章标题（公众号系统会自动显示标题）
- [ ] 图片用 `<img style="width:100%; max-width:100%;">` 确保自适应
- [ ] 代码块用 `<pre style="...">` 并确保暗色背景＋浅色字体
- [ ] 没有装饰性 HTML 实体（`&middot;` `&bull;` `&mdash;` 等），特殊字符用 Unicode 本体
