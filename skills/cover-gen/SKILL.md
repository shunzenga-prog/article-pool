---
name: cover-gen
description: Use when generating or repairing Article Pool WeChat cover images, including direct 1200x675 Agent/image_gen covers, legacy gen_cover.py fallback, or cover visual QA.
---

# 公众号封面图生成

公众号封面图必须是 1200×675px 的 16:9 纯图片封面。

**v3.0 更新：** 当前 Agent 支持 GPT Image / image_gen 时，必须由 Agent 根据文章语义直接生成最终封面图。不要把 Agent 生成图再交给 `gen_cover.py --background-image` 二次处理。`gen_cover.py` 只在当前环境没有生图能力、用户明确要图库/真实图，或作为旧链路兜底时使用。

## 触发场景

- "生成封面图" / "做封面" / "封面图片"
- 文章创作完成后自动生成封面
- 发布文章前准备封面图

## 快速使用

```bash
# Codex / GPT Image 模式（推荐）：Agent 直接生成最终 1200×675 PNG
# 不调用 gen_cover.py；直接把最终图片保存到文章月份目录的封面路径

# legacy 兜底：仅在 GPT Image 不可用、用户要求真实图/图库、或旧链路兜底时使用
python3 scripts/gen_cover.py --title "AI 圈沸腾的一周" --output cover.png

# legacy 兜底：指定文章文件，优先提取文章链接中的 OG 图片
python3 scripts/gen_cover.py --title "标题" --article article.html --output cover.png

# legacy 兜底：指定关键词辅助图片搜索
python3 scripts/gen_cover.py --title "标题" --keywords "AI,OpenAI,芯片" --output cover.png

# 禁止在默认流程中使用 --mode geometric；只有用户明确要求纯几何封面时才可手动调用
```

## 生成策略

**重要：** 在 Codex 且可用 GPT Image / image_gen 的环境中，封面不是“背景图 + 脚本合成”，而是 Agent 直接按文章语义生成最终封面。脚本不能替代语义判断，也不能把泛化背景当作合格封面。

推荐顺序：

| 优先级 | 来源 | 说明 |
|--------|------|------|
| T0 | Agent/Codex 直接生图 | 根据文章语义锚点生成最终 1200×675 PNG |
| T1 | 真实截图/事实图片 | 用户要求或文章需要事实型图片时使用 |
| T2 | `gen_cover.py` 旧 auto 链路 | 仅在无生图能力或旧流程兜底时使用 |

旧 `gen_cover.py` 自动模式内部来源如下，只能作为兜底参考：

| 优先级 | 来源 | 需要 API Key | 说明 |
|--------|------|-------------|------|
| T1 | OG:Image | 否 | 从文章链接的网页提取 og:image |
| T2 | Pexels | 是（推荐） | 高质量摄影照片，200次/小时免费 |
| T3 | Pollinations.ai | 否 | AI 生成，主题相关，完全免费 |
| T4 | Unsplash | 否 | 免费图库，可能被限速 |
| T5 | Brave 搜索 | 是 | Brave 图片搜索引擎 |
| T6 | 几何抽象 | 否 | 始终可用的兜底方案 |

如果封面最终走到 T6 几何抽象，在 Codex 环境中应视为失败，而不是正常完成。

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
| 模式 | Agent 直接生图优先；auto/geometric 仅为旧脚本兜底 |
| 设计原则 | 手机优先：封面缩略图约 375×150px，只保留大标题可读 |

## 语义贴合门禁

生成或修复封面时，必须先从文章里提炼 3-5 个核心语义锚点，再决定画面元素。封面至少命中其中 3 个，才算通过；不能只用“科技感、芯片、抽象线条”这类泛化元素。

检查方式：
- 文章讲具体设备：画面必须出现对应设备或清晰替代物，例如 Mac、本地电脑、桌面工作站。
- 文章讲具体能力：画面必须出现对应能力线索，例如本地运行、多模态输入、统一内存、离线节点。
- 文章讲具体数字或门槛：优先用视觉结构表达，例如 16 个内存块、低门槛设备群，而不是无关装饰。
- 若原文没有事实图片，优先生成语义化 AI 背景；禁止退回纯色几何图案当作合格封面。
- 发布前人工看图确认：如果遮住标题也看不出文章大概在讲什么，必须重做。

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
- 不保留来源角标、水印或脚本标识

## 自定义封面

以下参数仅适用于 `gen_cover.py` legacy 兜底链路；默认 Agent/image_gen 直接封面不使用这些参数：

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

生成封面后发布。Codex / image_gen 模式下不需要运行 `gen_cover.py`：

```bash
python3 scripts/publish_html.py article.html --cover cover.png
```
