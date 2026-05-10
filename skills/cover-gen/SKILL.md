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
| 设计原则 | 手机优先：封面缩略图约 375×150px，只保留大标题可读 |

## 照片背景模式

当获取到真实照片时：
- 照片保持明亮清晰，左侧轻量背板（自适应亮度，opacity 25%-35%）
- AI 图片生成主动使用明亮 prompt（bright and airy）
- 标题内侧单层阴影，减少暗沉感
- 底部短渐变条（80px），仅作装饰边沿

## 几何抽象模式

当无法获取照片时使用，包含：
- 17 种配色主题（8 深色 + 9 明亮），明亮主题占比提升
- 渐变光斑 + 对角线 + 噪点纹理 + 点阵
- 保持专业感和品牌一致性

## 文字布局（纯图片，无文字）

封面为纯图片，标题在订阅号列表中已并排显示，无需在图片上重复。
- 主图片：AI 生成或网络图库照片
- 无标题、无副标题、无任何文字覆盖
- 仅左下角保留微小的来源标识（9px，几乎不可见）

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
python3 scripts/publish_html.py article.html --cover cover.png
```
