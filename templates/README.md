# 微信公众号 HTML 模板库

共 13 个模板（含 1 个组件参考页），覆盖日常推送、专题内容、封面设计等场景。**所有文章模板已适配微信公众号编辑器 CSS 兼容性。**

## ⚠️ 微信公众号 CSS 兼容性（关键）

### 最严重的坑：发布时的 DOM 改写

微信公众号**预览时**样式正常，但**点击发布后**会做以下改写：

1. **所有 `<div>` 标签被转换为 `<p>` 标签**
2. **所有 `<p>` 标签上的 `style` 属性被全部剥离**
3. `<table>`、`<td>`、`<span>`、`<h1>`-`<h6>`、`<b>`、`<strong>`、`<pre>`、`<code>` 上的 style 保留

这意味着：
- ❌ `<div style="background:#fff; padding:20px;">` → 发布后变成 `<p>`（无样式）→ **布局崩坏**
- ❌ `<div style="font-size:15px; color:#333;">文字</div>` → 发布后变成 `<p>文字</p>`（无样式）
- ✅ `<table><tr><td style="background:#fff; padding:20px;">` → **正常**
- ✅ `<p><span style="font-size:15px; color:#333;">文字</span></p>` → **正常**

### 铁律

| 元素 | 能否用 style | 说明 |
|------|-------------|------|
| `<table>` `<td>` `<th>` | ✅ 可以 | 所有样式安全 |
| `<span>` | ✅ 可以 | 文字样式安全 |
| `<h1>`-`<h6>` | ✅ 可以 | 标题样式安全 |
| `<b>` `<strong>` | ✅ 可以 | 加粗+样式安全 |
| `<pre>` `<code>` | ✅ 可以 | 代码块样式安全 |
| `<img>` | ✅ 可以 | 图片样式安全 |
| `<p>` | ⚠️ 仅 text-align | 其他 style 会被剥离 |
| `<div>` `<section>` | ❌ 禁止 | 会被转成 `<p>` 并剥离样式 |

### 其他会被剥离的 CSS 属性

| ❌ 会失效 | ✅ 替代方案 |
|-----------|-----------|
| `linear-gradient(...)` | 实色背景 `background:#色值` |
| `display:flex` / `grid` | `<table>` 表格布局 |
| `display:inline-block` | 省略，span 内联 padding 即可 |
| `gap` / `justify-content` / `align-items` | `<td>` + `padding` / `vertical-align` |
| `border-radius` | 移除（微信不支持圆角） |
| `letter-spacing` | 移除 |
| `font-style:italic` | 移除 |
| `text-transform:uppercase` | 直接大写文本 |
| `opacity` | 使用直接色值 |
| `font-family` 自定义字体 | 移除（微信只用系统字体） |

### 容器转换模式

```html
<!-- ❌ 错误：div 做容器 -->
<div style="background:#f5f5f5; padding:20px;">
  <div style="font-size:15px; color:#333;">内容</div>
</div>

<!-- ✅ 正确：table 做容器，span 做文字 -->
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f5f5;">
<tr><td style="padding:20px;">
  <p><span style="font-size:15px; color:#333;">内容</span></p>
</td></tr>
</table>
```

**所有模板已基于以上规则完成转换。**

## 模板清单

### 文章模板
| 文件 | 类型 | 风格 | 适用场景 | WeChat安全 |
|------|------|------|---------|-----------|
| `article-template.html` | 通用文章 | 紫蓝科技风 | 通用长文，含完整样式系统 | ✅ |
| `daily-report.html` | 日报/长文 | 清爽结构风 | 每日知识分享、深度教程 | ✅ |
| `tech-tutorial.html` | 技术教程 | 色块分割 + 嵌套层次（V4） | 编程教学、步骤式教程，含完整组件系统 | ✅ |
| `component-reference.html` | 组件参考 | 可视化组件目录 | 所有组件渲染效果预览、设计系统参考 | — |

### 简报模板
| 文件 | 类型 | 风格 | 适用场景 | WeChat安全 |
|------|------|------|---------|-----------|
| `morning-briefing.html` | 早报 | 清新高效 | 每日早晨资讯简报，卡片式快速浏览 | ✅ |
| `evening-briefing.html` | 晚报 | 温暖沉思 | 每日晚间深度复盘+阅读推荐 | ✅ |
| `weekly-report.html` | 周报 | 专业严谨 | 每周技术动态汇总、数据回顾 | ✅ |
| `news-digest.html` | 资讯速递 | 黑红新闻风 | 重大事件解读、对比分析 | ✅ |

### 总结模板
| 文件 | 类型 | 风格 | 适用场景 | WeChat安全 |
|------|------|------|---------|-----------|
| `monthly-summary.html` | 月度总结 | 温暖叙事 | 每月内容回顾、学习心得、下月计划 | ✅ |
| `yearly-summary.html` | 年终总结 | 大气仪式感 | 年度盘点、关键词、读者感谢 | ✅ |

### 封面模板
| 文件 | 类型 | 风格 | 适用场景 |
|------|------|------|---------|
| `cover-tech.html` | 封面图 | 深色科技风 | 编程教程、技术干货、工具分享 |
| `cover-warm.html` | 封面图 | 暖色文艺风 | 个人成长、思维分享、经验总结 |
| `cover-news.html` | 封面图 | 黑红新闻风 | 重大事件解读、行业动态 |

> 封面模板为 HTML 预览参考。正式封面默认由 Agent/image_gen 根据文章语义直接生成 1200×675 PNG；`scripts/gen_cover.py` 仅作 legacy fallback。

## 使用方式

### 发布到公众号

```bash
# 1. 由 Agent/image_gen 直接生成最终封面图

# 2. 发布到公众号草稿箱
python3 scripts/publish_html.py 文章.html --cover 封面图.png --author "小咪"

# 3. 登录公众号后台 → 草稿箱 → 预览 → 群发
```

### 手动粘贴

1. 用浏览器打开 HTML 文件
2. 全选页面内容（Ctrl+A），复制（Ctrl+C）
3. 粘贴到微信公众号后台的富文本编辑器

### 模板中的占位符

每个模板中都有 `<!-- REPLACE:xxx -->` 标记的内容需要替换。

## 配色方案（V4）

| 用途 | 色值 | 应用 |
|------|------|------|
| 品牌蓝 | `#1E88E5` | 步骤编号、链接、信息提示框左边框 |
| 警示红 | `#C0392B` | 引子 HOOK、警告提示框 |
| 成功绿 | `#27AE60` | OUTPUT 验证框 |
| 提示橙 | `#E67E22` | PITFALL 踩坑框 |
| 分析紫 | `#9B59B6` | DEEP DIVE 深度分析框 |
| 代码暗底 | `#1A1B2E` | 代码块、下期预告背景 |
| 标题 | `#1A1A2E` | 各级标题 |
| 正文 | `#2C2C2C` | 正文文字 |
| 浅灰底 | `#F2F4F8` | 导航、资源卡片背景 |

详细设计规范见 `skills/wechat-writer/references/typography-guide.md`，组件预览见 `templates/component-reference.html`。

## 封面图生成

参见 `skills/cover-gen/SKILL.md`。正式封面默认由 Agent/image_gen 直接生成最终 1200×675 PNG。

`scripts/gen_cover.py` 是旧兜底工具，仅在无生图能力或用户明确要求图库/事实图片时使用。
