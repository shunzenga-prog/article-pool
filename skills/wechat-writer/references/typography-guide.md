# 公众号排版规范 V4

基于 6 色语义调色板 + 8 档间距系统 + 5 型提示框系统的标准化排版体系。所有示例代码已适配微信公众号 CSS 兼容性。

## 一、核心参数

| 元素 | 推荐值 | 说明 |
|------|--------|------|
| 正文字号 | 15px | 正文/说明文字 |
| 小字 | 13px | 代码/辅助/标注 |
| 标题字号 | 17-24px | 分章节/大标题 |
| 行高（正文） | 1.8 | 15px 正文专用 |
| 行高（代码/标题） | 1.6 | 代码、标题、标签 |
| 段落长度 | ≤5 行 | 手机一屏 |

## 二、V4 调色板

### 语义色

| 用途 | 色值 | 背景色 | 应用组件 |
|------|------|--------|---------|
| 品牌蓝 | `#1E88E5` | `#EEF4FF` | 步骤编号、链接、TRY IT、信息提示 |
| 警示红 | `#C0392B` | `#FFF5F5` | 引子 HOOK、警告提示 |
| 成功绿 | `#27AE60` | `#EEF8F0` | OUTPUT 验证、正确做法 |
| 提示橙 | `#E67E22` | `#FFF9EE` | PITFALL 踩坑、小技巧 |
| 分析紫 | `#9B59B6` | `#F9F5FD` | DEEP DIVE 深度分析 |
| 深色底 | `#1A1B2E` | — | 代码块、下期预告 |

### 中性色

| 用途 | 色值 |
|------|------|
| 正文 | `#2C2C2C` / `#444444` |
| 标题 | `#1A1A2E` |
| 说明灰 | `#666666` |
| 日期/标注 | `#AAAAAA` / `#BBBBBB` |
| 浅灰背景 | `#F2F4F8` / `#F6F7FA` |
| 边框 | `#DDE1E8` / `#E8E8EC` / `#EEEEEE` |

## 三、间距系统

统一使用 4 的倍数，共 8 档：

| 间距 | 值 | 用途 |
|------|----|------|
| XS | 4px | 卡片内层 padding、标题与副标题间距 |
| SM | 8px | 卡片间距、标签与正文间距 |
| MD | 12px | PITFALL/OUTPUT 框间距、元信息间距 |
| LG | 16px | 步骤间正文间距、代码块间距 |
| XL | 20px | 经验/FAQ 卡片内边距、章节内间距 |
| 2XL | 24px | 导航/资源卡片 padding、章节间距 |
| 3XL | 28px | 色条分割器上下间距、大节间距 |
| 4XL | 32px | HERO 底部、章节尾间距 |

## 四、标题样式

### H1 主标题（HERO 区）

```html
<h1 style="font-size:24px; font-weight:800; color:#1A1A2E; margin:20px 0 0; line-height:1.45; text-align:center;">标题文字</h1>
```

### 超大序号 + STEP 标题（步骤区）

```html
<table width="100%" cellpadding="0" cellspacing="0">
<tr>
  <td width="48" style="vertical-align:top;">
    <p style="margin:0; line-height:1;">
      <span style="font-size:48px; font-weight:800; color:#1E88E5; line-height:1;">1</span>
    </p>
  </td>
  <td style="vertical-align:middle; padding-left:4px;">
    <p style="margin:0 0 4px;">
      <span style="font-size:11px; color:#1E88E5; font-weight:600;">STEP 1</span>
    </p>
    <p style="margin:0;">
      <span style="font-size:18px; font-weight:700; color:#1A1A2E; line-height:1.45;">步骤标题</span>
    </p>
  </td>
</tr>
</table>
```

### 章节标题（带装饰线）

```html
<!-- 微型色块装饰线 -->
<table width="100%" cellpadding="0" cellspacing="0">
<tr><td style="text-align:center; padding:16px 0 0;">
  <table width="48" cellpadding="0" cellspacing="0" style="border-top:3px solid #1E88E5;">
  <tr><td></td></tr>
  </table>
</td></tr>
</table>
```

## 五、5 型提示框系统

所有提示框使用 `table` + `border-left` 实现，与正文形成明确视觉区分。

### 类型速查

| 类型 | 背景色 | 左边框 | 标签色 | 徽章文字 |
|------|--------|--------|--------|---------|
| 引子 HOOK | `#FFF5F5` | `#C0392B` 6px | `#C0392B` | HOOK |
| 信息/准备 | `#EEF4FF` | `#1E88E5` 6px | — | — |
| 成功 OUTPUT | `#EEF8F0` | `#27AE60` 4px | `#27AE60` | OUTPUT |
| 警告 PITFALL | `#FFF9EE` | `#E67E22` 4px | `#E67E22` | PITFALL |
| 分析 DEEP DIVE | `#F9F5FD` | `#9B59B6` 6px | `#9B59B6` | DEEP DIVE |

### 通用模板

```html
<!-- 左边框 + 徽章型（HOOK / DEEP DIVE / TRY IT） -->
<table width="100%" cellpadding="0" cellspacing="0" style="background:#FFF5F5; border-left:6px solid #C0392B;">
<tr><td style="padding:24px 22px;">
  <p style="margin:0 0 8px;">
    <span style="font-size:11px; color:#FFFFFF; font-weight:700; background:#C0392B; padding:3px 10px;">HOOK</span>
  </p>
  <p style="margin:0 0 6px;">
    <span style="font-size:18px; font-weight:700; color:#1A1A2E; line-height:1.5;">标题</span>
  </p>
  <p style="margin:0;">
    <span style="font-size:15px; color:#2C2C2C; line-height:1.85;">正文内容</span>
  </p>
</td></tr>
</table>
```

```html
<!-- 细左边框 + 小标签型（OUTPUT / PITFALL） -->
<table width="100%" cellpadding="0" cellspacing="0" style="background:#EEF8F0; border-left:4px solid #27AE60;">
<tr><td style="padding:14px 18px;">
  <p style="margin:0 0 4px;">
    <span style="font-size:11px; color:#27AE60; font-weight:700;">OUTPUT</span>
  </p>
  <p style="margin:0;">
    <span style="font-size:13px; color:#2C3A2E; line-height:1.8;">正文内容</span>
  </p>
</td></tr>
</table>
```

## 六、色条分割器

替代传统 `<hr>`，提供 3 种视觉节奏：

```html
<!-- 品牌蓝 -->
<table width="100%" cellpadding="0" cellspacing="0">
<tr>
  <td width="40" style="background:#1E88E5; padding:0; height:4px;"></td>
  <td style="background:#EEEEEE; padding:0; height:4px;"></td>
</tr>
</table>

<!-- 分析紫 -->
<table width="100%" cellpadding="0" cellspacing="0">
<tr>
  <td width="48" style="background:#9B59B6; padding:0; height:4px;"></td>
  <td style="background:#EEEEEE; padding:0; height:4px;"></td>
</tr>
</table>

<!-- 深色收束 -->
<table width="100%" cellpadding="0" cellspacing="0">
<tr>
  <td width="56" style="background:#1A1A2E; padding:0; height:4px;"></td>
  <td style="background:#EEEEEE; padding:0; height:4px;"></td>
</tr>
</table>
```

## 七、深色代码块

强视觉对比，与浅色分析框明确区分。

```html
<table width="100%" cellpadding="0" cellspacing="0" style="background:#1A1B2E;">
<tr>
  <td style="padding:10px 20px 0;">
    <p style="margin:0;">
      <span style="font-size:11px; color:#7B83A8; font-weight:600;">● 终端</span>
    </p>
  </td>
</tr>
<tr>
  <td style="padding:8px 20px 16px;">
    <pre style="color:#C8D0E8; font-size:13px; line-height:1.65; margin:0; overflow-x:auto; white-space:pre-wrap;"><code>代码内容</code></pre>
  </td>
</tr>
</table>
```

## 八、嵌套卡片（核心经验）

双层 table 嵌套制造层次感：

```html
<table width="100%" cellpadding="0" cellspacing="0" style="background:#F6F7FA;">
<tr><td style="padding:4px;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#FFFFFF; border-left:4px solid #1E88E5;">
  <tr><td style="padding:16px 18px;">
    <p style="margin:0 0 6px;">
      <span style="font-size:15px; font-weight:700; color:#1A1A2E; line-height:1.5;">1. 经验标题</span>
    </p>
    <p style="margin:0;">
      <span style="font-size:14px; color:#444444; line-height:1.85;">经验描述文字</span>
    </p>
  </td></tr>
  </table>
</td></tr>
</table>
```

## 九、FAQ 卡片

```html
<table width="100%" cellpadding="0" cellspacing="0" style="background:#FAFAFB; border:1px solid #E8E8EC;">
<tr><td style="padding:16px 20px;">
  <p style="margin:0 0 8px;">
    <span style="font-size:14px; font-weight:700; color:#1A1A2E; line-height:1.6;">Q：问题</span>
  </p>
  <p style="margin:0;">
    <span style="font-size:13px; color:#555555; line-height:1.8;">A：回答</span>
  </p>
</td></tr>
</table>
```

## 十、深色反转卡片（下期预告）

```html
<table width="100%" cellpadding="0" cellspacing="0" style="background:#1A1B2E;">
<tr><td style="padding:24px 22px;">
  <p style="margin:0 0 8px;">
    <span style="font-size:11px; color:#7B83A8; font-weight:600;">NEXT EPISODE</span>
  </p>
  <p style="margin:0 0 8px;">
    <span style="font-size:17px; font-weight:700; color:#FFFFFF; line-height:1.5;">第 N+1 期：下期标题</span>
  </p>
  <p style="margin:0;">
    <span style="font-size:13px; color:#A0A6C0; line-height:1.8;">下期内容简介</span>
  </p>
</td></tr>
</table>
```

## 十一、60-30-10 配色原则

- **60% 主色**：正文 `#2C2C2C`、白色背景
- **30% 辅助色**：品牌蓝 `#1E88E5`、灰色卡片背景
- **10% 强调色**：警示红/成功绿/分析紫/提示橙（按语义选用）

## 十二、移动端优化

- [ ] 段落 ≤5 行
- [ ] 所有容器 `width="100%"` 自适应
- [ ] 代码块 `white-space:pre-wrap` 自动换行
- [ ] 图片 `max-width:100%` 不溢出
- [ ] 表格不超过 3 列

## 十三、发布前检查清单

- [ ] 没有使用 `<div>` / `<section>` 标签
- [ ] 所有文字样式用 `<span style="...">` 包裹，不在 `<p>` 上设置
- [ ] 没有 `border-radius`、`flex`/`grid`、`box-shadow`、`linear-gradient`
- [ ] 没有 `letter-spacing`、`font-style:italic`、`display:inline-block`
- [ ] 所有容器布局用 `<table><tr><td>` 实现
- [ ] 颜色 ≤6 种（含语义色）
- [ ] 间距统一为 4 的倍数
- [ ] 正文行高 1.8，代码/标题行高 1.6
- [ ] 提示框类型使用正确（HOOK/OUTPUT/PITFALL/DEEP DIVE）
- [ ] 手机预览正常
