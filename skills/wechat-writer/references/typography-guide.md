# 公众号排版规范

## 一、核心参数

| 元素 | 推荐值 | 说明 |
|------|--------|------|
| 正文字号 | 15-16px | 15px 是主流 |
| 行距 | 1.75-2.0 | 1.75 是黄金标准 |
| 字间距 | 0-1px | 一般不需要调整 |
| 段落间距 | 15-20px | 视觉分隔 |
| 段落长度 | ≤5 行 | 手机一屏 |

---

## 二、标题样式

### H2 标题（章节主标题）

**模板 A - 左侧线型**（推荐）
```html
<h2 style="font-size:18px;font-weight:bold;color:#1A1A1A;border-left:4px solid #1E88E5;padding-left:12px;margin:35px 0 15px 0;">标题文字</h2>
```

**模板 B - 底色块型**
```html
<h2 style="font-size:17px;font-weight:bold;background:linear-gradient(135deg,#667EEA 0%,#764BA2 100%);color:white;padding:10px 15px;border-radius:4px;margin:30px 0 15px 0;display:inline-block;">标题文字</h2>
```

**模板 C - 下划线型**
```html
<h2 style="font-size:18px;font-weight:bold;border-bottom:2px solid #E0E0E0;padding-bottom:10px;margin:30px 0 15px 0;color:#000;">标题文字</h2>
```

### H3 标题（小节标题）
```html
<h3 style="font-size:16px;font-weight:bold;color:#333;margin:25px 0 12px 0;">标题文字</h3>
```

---

## 三、重点标注

### 加粗强调
```html
<span style="font-weight:bold;">重点内容</span>
```

### 颜色强调
```html
<span style="font-weight:bold;color:#E74C3C;">重点内容</span>
```

### 底色高亮
```html
<span style="background-color:#FEF3C7;padding:2px 4px;border-radius:2px;">重点内容</span>
```

### 强调色推荐

| 用途 | 颜色 | 代码 |
|------|------|------|
| 重要/警示 | 红色 | #E74C3C |
| 链接/参考 | 蓝色 | #3498DB |
| 成功/正面 | 绿色 | #27AE60 |
| 警告/注意 | 橙色 | #F39C12 |

---

## 四、引用框

### 样式 A - 左侧线型（推荐）
```html
<div style="border-left:4px solid #1E88E5;padding:15px 20px;margin:20px 0;background:#F8F9FA;color:#555;font-style:italic;">
  引用内容...
</div>
```

### 样式 B - 完整边框型
```html
<div style="border:1px solid #E0E0E0;border-radius:8px;padding:20px;margin:20px 0;background:#FAFAFA;">
  引用内容...
</div>
```

### 样式 C - 带来源
```html
<div style="border-left:3px solid #9E9E9E;padding:15px 20px;margin:20px 0;color:#666;">
  引用内容...
  <div style="margin-top:10px;font-size:13px;color:#999;text-align:right;">—— 来源说明</div>
</div>
```

---

## 五、分割线

### 简约型
```html
<hr style="border:none;border-top:1px solid #E0E0E0;margin:40px 0;">
```

### 装饰型
```html
<hr style="border:none;border-top:2px dashed #BDBDBD;margin:40px 0;">
```

### 品牌色型
```html
<hr style="border:none;border-top:3px solid #1E88E5;width:100px;margin:40px auto;">
```

---

## 六、配图规范

### 尺寸

| 位置 | 尺寸 |
|------|------|
| 封面图 | 900×383px |
| 文中图 | 1080px 宽 |

### 图片代码
```html
<img src="图片URL" style="width:100%;max-width:1080px;height:auto;display:block;margin:20px auto;">
<div style="font-size:13px;color:#999;text-align:center;margin-top:10px;">图：说明文字</div>
```

### 密度建议

| 文章长度 | 图片数量 |
|----------|----------|
| 短文 (<1500字) | 2-4 张 |
| 中篇 (1500-3000字) | 4-8 张 |
| 长文 (>3000字) | 8-15 张 |

---

## 七、颜色搭配

### 60-30-10 原则

- **60% 主色**: 正文、背景（黑/深灰）
- **30% 辅助色**: 标题、引用框（品牌色）
- **10% 强调色**: 重点标注（亮色）

### 推荐配色

**科技蓝**
```
主色: #1A1A1A (正文)
辅助色: #1E88E5 (标题)
强调色: #E74C3C (重点)
背景: #FFFFFF
```

**温暖阅读**
```
主色: #2C2C2C (正文)
辅助色: #D4A574 (标题)
强调色: #E76F51 (重点)
背景: #FEFAF0
```

**极简黑白**
```
主色: #000000 (正文)
辅助色: #666666 (次级)
强调色: #000000 (加粗)
背景: #FFFFFF
```

---

## 八、移动端优化

### 必须遵守

- [ ] 段落 ≤5 行
- [ ] 单行 ≤25 字
- [ ] 图片 max-width: 100%
- [ ] 表格响应式或转图片

### 暗黑模式适配

```css
/* 避免纯黑背景 */
background: #1A1A1A; /* 而非 #000000 */

/* 文字使用相对亮度 */
color: #E0E0E0; /* 而非 #FFFFFF */
```

---

## 九、顶级公众号对比

| 公众号 | 字号 | 行距 | 标题样式 | 主色调 |
|--------|------|------|----------|--------|
| 量子位 | 15px | 1.75 | 左侧蓝线 | 科技蓝 |
| 机器之心 | 15px | 1.8 | 红色底块 | 品牌红 |
| 差评 | 16px | 1.8 | 下划线/emoji | 黑+亮色 |

---

## 十、发布前检查

- [ ] 正文字号 15-16px
- [ ] 行距 1.75-1.8
- [ ] 段落 ≤5 行
- [ ] 标题层级清晰
- [ ] 颜色 ≤4 种
- [ ] 图片有说明
- [ ] 重点有标注
- [ ] 引用框统一
- [ ] 分割线 <5 条
- [ ] 手机预览正常