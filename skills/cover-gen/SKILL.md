---
name: cover-gen
description: 公众号封面图生成。使用 PIL 生成 1200x675 专业封面图，支持中英文混排、渐变背景、装饰元素。触发：生成封面、做封面图、封面图片。
---

# 公众号封面图生成

基于 Python PIL 的专业封面图生成器，生成 1200×675px 的公众号 16:9 封面。

## 触发场景

- "生成封面图" / "做封面" / "封面图片"
- 文章创作完成后自动生成封面
- 发布文章前准备封面图

## 快速使用

```bash
python3 scripts/gen_cover.py
```

脚本会读取硬编码的标题、副标题、日期等元信息，生成封面图并保存到指定路径。

## 设计规格

| 属性 | 值 |
|------|-----|
| 尺寸 | 1200 × 675 px |
| 格式 | PNG |
| 底色 | #0A0E1A（深蓝黑） |
| 字体 | DroidSansFallbackFull（中文）+ DejaVu Sans（拉丁） |

## 设计元素

### 背景
- 深蓝黑底色 (#0A0E1A)
- 右上角暖紫光渐变（#5B2C6E）
- 左下角冷蓝光渐变（#1A3C8A）
- 随机噪点纹理（增加质感）

### 装饰
- 对角线几何线条（8条，半透明）
- 半透明圆形光斑（3个位置）
- 底部点阵网格
- 橙色强调竖条（左侧，带圆点装饰）
- 渐变下划线（标题下方）
- 右下角大号日期数字水印
- 底部渐变彩色条
- 1px 外框

### 文字区域
- 小标签：EVENING DIGEST（橙色，左上）
- 主标题：大字 68px（可换行）
- 副标题：中字 20px
- 日期：16px
- 元信息：16px（如"深度解读 · 约 1,200 字"）
- 底部信息：16px

## 中英文混排

脚本使用 `draw_text()` 函数实现中英文自动切换字体：

```python
def is_cjk(cp):
    return (0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF or
            0xF900 <= cp <= 0xFAFF or 0x3000 <= cp <= 0x303F or
            0xFF00 <= cp <= 0xFFEF or 0x2000 <= cp <= 0x206F)

def draw_text(draw, xy, text, fill, fcjk, flat):
    # 逐字符检测 Unicode 范围，自动切换 CJK/Latin 字体
```

**字体路径：**
- CJK: `/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf`
- Latin: `/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf`
- Latin Bold: `/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf`

## 自定义封面

修改 `gen_cover.py` 中的以下变量：

```python
# 主标题（第146-149行）
draw_text(draw, (LEFT, 135), u'你的主标题第一行', LIGHT, f68c, f68l)
draw_text(draw, (LEFT, 220), u'你的主标题第二行', LIGHT, f68c, f68l)

# 副标题（第163-165行）
draw_text(draw, (LEFT, 355), u'副标题内容', MID, f20c, f20l)

# 日期（第168-169行）
draw_text(draw, (LEFT, 430), u'2026 / 04 / 27', MID, f16c, f16l)

# 元信息（第173行）
draw_text(draw, (LEFT, 485), u'深度解读 · 约 1,200 字', DIM, f16c, f14l)

# 右下角日期数字（第178行）
draw.text((W - 280, 80), '27', fill=(0x2A, 0x2E, 0x4A), font=f_big)

# 底部信息（第190-191行）
draw_text(draw, (LEFT, 605), u'每晚 21:30 与你一起回顾这一天', DIM, f16c, f14l)

# 输出路径（第202行）
out = '/path/to/output.png'
```

## 配色

| 用途 | 色值 |
|------|------|
| 强调色（Accent） | #FF6B35（橙） |
| 浅色文字（Light） | #E8E8F0 |
| 中等文字（Mid） | #9494B8 |
| 暗文字（Dim） | #646488 |
| 底色 | #0A0E1A |
| 暖紫渐变 | #5B2C6E |
| 冷蓝渐变 | #1A3C8A |

## 依赖

```bash
pip install Pillow --break-system-packages
```

需要系统字体：
```bash
sudo apt-get install fonts-droid-fallback fonts-dejavu-core
```

## 发布集成

生成封面后，使用 `publish_html.py` 上传到公众号：

```bash
python3 scripts/publish_html.py 文章.html --cover 封面图.png
```

## 参考

- 脚本：`scripts/gen_cover.py`
- 封面模板（HTML预览）：`templates/cover-tech.html`、`templates/cover-warm.html`、`templates/cover-news.html`
- 发布脚本：`scripts/publish_html.py`
