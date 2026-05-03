---
name: cover-gen
description: 公众号封面图生成。自动搜索网络图片作为背景（Pexels→AI→Unsplash→Brave→几何），生成 1200x675 专业封面。触发：生成封面、做封面图、封面图片。
---

# 公众号封面图生成

基于 Python PIL 的专业封面图生成器，生成 1200×675px 的公众号 16:9 封面。

**v2.0 重大更新：** 支持自动从网络获取真实照片作为背景（Pexels 图库 → AI 生成 → Unsplash → 几何抽象），不再是纯渐变效果。

## 触发场景

- "生成封面图" / "做封面" / "封面图片"
- 文章创作完成后自动生成封面
- 发布文章前准备封面图

## 快速使用

```bash
# 智能模式（推荐）：自动搜索网络图片作为背景
python3 scripts/gen_cover.py --title "AI 圈沸腾的一周" --output cover.png

# 指定文章文件，优先提取文章链接中的 OG 图片
python3 scripts/gen_cover.py --title "标题" --article article.html --output cover.png

# 指定关键词辅助图片搜索
python3 scripts/gen_cover.py --title "标题" --keywords "AI,OpenAI,芯片" --output cover.png

# 纯几何模式（如果不需要照片背景）
python3 scripts/gen_cover.py --title "标题" --mode geometric --output cover.png
```

## 背景图片获取策略（自动模式）

脚本按以下优先级自动获取背景图片：

| 优先级 | 来源 | 需要 API Key | 说明 |
|--------|------|-------------|------|
| T1 | OG:Image | 否 | 从文章链接的网页提取 og:image |
| T2 | Pexels | 是（推荐） | 高质量摄影照片，200次/小时免费 |
| T3 | Pollinations.ai | 否 | AI 生成，主题相关，完全免费 |
| T4 | Unsplash | 否 | 免费图库，可能被限速 |
| T5 | Brave 搜索 | 是 | Brave 图片搜索引擎 |
| T6 | 几何抽象 | 否 | 始终可用的兜底方案 |

**推荐配置 Pexels API Key**（免费注册，2分钟搞定）：
1. 访问 https://www.pexels.com/api/
2. 注册账号，创建应用获取 API Key
3. 填入 `config/.env` 的 `PEXELS_API_KEY=`

即使不配任何 API Key，也能通过 T3（AI生成）和 T4（Unsplash）获取照片。

## 设计规格

| 属性 | 值 |
|------|-----|
| 尺寸 | 1200 × 675 px |
| 格式 | PNG |
| 模式 | auto（智能背景）/ geometric（几何抽象） |

## 照片背景模式

当获取到真实照片时：
- 照片保持明亮清晰，不会过度压暗
- 左侧文字区域添加半透明深色背板，确保白色文字可读
- 标题使用多层阴影增强立体感和可读性
- 底部渐变暗条保护页脚文字
- 保留所有装饰元素（强调竖条、渐变下划线、日期水印等）

## 几何抽象模式

当无法获取照片时使用，包含：
- 8 种配色主题（深海、暖橙、翠绿、霓虹、金棕、玫红、灰蓝、靛蓝）
- 渐变光斑 + 对角线 + 噪点纹理 + 点阵
- 保持专业感和品牌一致性

## 文字布局

- 标签：左上角（如 "EVENING DIGEST"）
- 主标题：大字 68px（自动换行）
- 副标题：中字 20px
- 日期 + 元信息
- 大号日期数字水印
- 底部信息
- 图片来源标识（左下角小字）

## 自定义封面

通过命令行参数控制：

```
--title "主标题"
--subtitle "副标题"
--tag "标签文字"
--date "2026 / 05 / 02"
--reading-time "深度解读 · 约 1,200 字"
--footer "每晚 21:30 与你一起回顾这一天"
--keywords "AI,芯片,大模型"         # 辅助图片搜索
--article article.html             # 从文章提取 OG 图片
--theme ocean|sunset|forest|...    # 强制几何主题
--mode auto|geometric              # 背景模式
```

## 依赖

```bash
pip install Pillow requests --break-system-packages
```

系统字体：
```bash
sudo apt-get install fonts-droid-fallback fonts-dejavu-core
```

## 发布集成

生成封面后发布：

```bash
python3 scripts/gen_cover.py --title "标题" --output cover.png
python3 scripts/wechat_publish.py article.html --cover cover.png
```
