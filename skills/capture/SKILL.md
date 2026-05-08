---
name: capture
description: 统一截图工具包。终端截图、浏览器截图、代码高亮截图、流程图渲染、Matplotlib 图表 — 五个截图能力一个包，可被任何工作流独立引用。
---

# 截图能力工具包（Capture）

`scripts/capture/` 是一个独立的 Python 截图工具包，将项目中分散的 5 个截图工具统一为模块化架构，可被任何工作流（教程创作、早报、项目推荐等）独立引用。

## 核心理念

**一个基类，五种能力。** `BaseCapture` 统一管理 Playwright 浏览器生命周期（单例复用）、CJK 字体检测、临时文件追踪清理。五个子模块各司其职，接口一致。

```
scripts/capture/
├── __init__.py          # 公共 API 导出
├── fonts.py             # CJK 字体检测（跨平台 14 路径回退）
├── themes.py            # 统一颜色令牌系统（14 套色板）
├── base.py              # BaseCapture：Playwright/字体/临时文件 共享生命周期
├── terminal.py          # xterm.js 终端截图（Windows/macOS/Linux 自适应标题栏）
├── browser.py           # Playwright 网页/本地文件截图 + 标注
├── code.py              # Pillow 代码高亮截图 + 终端执行 + GIF 动画
├── flowchart.py         # Mermaid.js 流程图渲染（13 色板 × 4 卡片风格）
└── chart.py             # Matplotlib 图表子进程渲染
```

## 触发场景

- "截个图" / "生成终端截图" / "代码截图"
- "画个流程图" / "生成图表"
- 教程文章需要配图
- 任何需要生成 PNG 图片的工作流

## 快速使用

### 编程调用

```python
from scripts.capture import (
    # 子模块导出
    terminal_screenshot, browser_screenshot, batch_screenshots,
    file_screenshot, annotated_screenshot,
    code_to_image, exec_to_image, code_to_animation,
    flowchart_to_image, list_palettes,
    chart_screenshot,
    # 基础设施
    get_font_manager, ThemeRegistry, FontManager,
)

# 终端截图（xterm.js + Playwright）
terminal_screenshot("echo hello", "terminal.png", os_name="windows")

# 网页截图
browser_screenshot("https://example.com", "page.png")

# 批量截图
batch_screenshots(["url1", "url2"], "output_dir/")

# 代码高亮截图（Pygments + Pillow）
code_to_image("def foo(): pass", "code.png", lang="python")

# 执行代码并截取终端输出
exec_to_image("print(1+1)", "output.png")

# 代码逐行动画 GIF
code_to_animation("for i in range(5):\n    print(i)", "anim.gif")

# 流程图（dict/JSON → Mermaid → PNG）
flow = {"nodes": [{"id":"a","label":"开始"}], "edges": [{"from":"a","to":"b"}]}
flowchart_to_image(flow, "flow.png", palette="ocean")

# Matplotlib 图表
chart_screenshot("import matplotlib.pyplot as plt; plt.plot([1,2,3])", "chart.png")
```

### 类方式（复用浏览器实例）

```python
from scripts.capture.terminal import TerminalCapture
from scripts.capture.browser import BrowserCapture
from scripts.capture.code import CodeCapture
from scripts.capture.flowchart import FlowchartCapture
from scripts.capture.chart import ChartCapture

# 终端截图
with TerminalCapture() as tc:
    tc.render("ls -la", output_path="t1.png", os_name="macos")
    tc.render("echo done", output_path="t2.png")  # 复用浏览器

# 流程图
with FlowchartCapture() as fc:
    fc.generate_from_file("flow.json", "flow.png", palette="tech-dark")

# 代码截图
with CodeCapture() as cc:
    cc.code_screenshot("print('hi')", "code.png", language="python")
```

## 五个截图能力

### 1. Terminal（终端截图）

**技术栈：** xterm.js v5.3.0 (CDN) + xterm-addon-fit + Playwright

**OS 自适应标题栏：**

| OS | 风格 | 标题栏特征 |
|----|------|-----------|
| Windows | Windows Terminal | `>_` 图标 + 深色标签页 |
| macOS | 原生 Terminal | 红黄绿交通灯按钮 |
| Linux | GNOME Terminal | 扁平标题栏 |

**参数：**
- `text`: 终端文本内容
- `output_path`: 输出 PNG 路径
- `title`: 标题栏文本（默认按 OS 自动：PowerShell/bash/Terminal）
- `os_name`: `windows` / `macos` / `linux`（默认自动检测）

### 2. Browser（浏览器截图）

**技术栈：** Playwright

**功能：**
- `single()`: 截取单个网页（支持 CSS 选择器定位元素）
- `batch()`: 批量截图 URL 列表
- `file()`: 截取本地 HTML 文件
- `annotate()`: 截图 + PIL 文字标注叠加

### 3. Code（代码截图 + 终端执行 + 动画）

**技术栈：** Pygments（语法高亮）+ Pillow（渲染）+ imageio（GIF）

**三种模式：**
- **code_screenshot**: Pygments 词法分析 → 双字体渲染（ASCII 等宽 + CJK 回退）→ PNG
- **exec_and_capture**: 子进程执行代码 → 捕获 stdout/stderr → 渲染为终端窗口 PNG
- **code_animation**: 逐行出现 GIF 动画，带光标闪烁效果

### 4. Flowchart（流程图）

**技术栈：** Mermaid.js v11 (CDN) + Playwright + SVG 后处理

**13 套色板 × 4 种卡片风格 = 52 种视觉组合**
- 色板：tech-dark, ocean, forest, sunset, midnight, paper, cyberpunk, ember, aurora, navy, slate, rose
- 风格：glass（玻璃拟态）, solid（实色）, neon（霓虹）, minimal（极简）

**输入格式：** JSON dict 或 JSON 文件
```json
{
  "title": "流程图标题",
  "direction": "LR",
  "nodes": [{"id":"a", "label":"步骤1", "shape":"rounded", "category":"step"}],
  "edges": [{"from":"a", "to":"b", "label":"→"}]
}
```

### 5. Chart（Matplotlib 图表）

**技术栈：** Matplotlib（子进程执行，CJK 字体自动注入）

**特性：**
- 自动注入 CJK 字体配置（msyh.ttc/PingFang SC/NotoSansCJK）
- 暗色主题默认（#1e1e2e 背景，#cdd6f4 文字）
- 子进程隔离，超时保护

## 基础设施

### FontManager（fonts.py）

跨平台 CJK 字体检测，14 路径回退链：

```
Windows: msyh.ttc > simsun.ttc > simhei.ttf > Deng.ttf
Linux:   DroidSansFallbackFull > NotoSansMonoCJK > wqy-zenhei > wqy-microhei
macOS:   PingFang SC > STHeiti > Hiragino Sans GB
```

**API：**
```python
from scripts.capture.fonts import get_font_manager

fm = get_font_manager()
fm.cjk_path     # CJK 字体路径（str）
fm.mono_path    # 等宽字体路径（str）
fm.cjk_pil(16)  # PIL Font 对象（CJK, 16px）
fm.mono_pil(14) # PIL Font 对象（等宽, 14px）
fm.is_cjk("中") # True
```

### ThemeRegistry（themes.py）

14 套颜色令牌，统一 `ColorTokens` 接口：

```python
from scripts.capture.themes import ThemeRegistry

theme = ThemeRegistry.get("catppuccin-mocha")
print(theme.bg)       # "#1e1e2e"
print(theme.accent)   # "#89b4fa"
print(theme.keyword)  # "#cba6f7"
```

**预设色板：** catppuccin-mocha, github-dark, tech-dark, ocean, forest, sunset, midnight, paper, cyberpunk, ember, aurora, navy, slate, rose

### BaseCapture（base.py）

共享生命周期管理：
- Playwright 浏览器懒加载单例（首次使用时启动，后续截图复用）
- 临时文件自动追踪 + `__exit__` 清理
- 上下文管理器协议（`with XxxCapture() as cap:`）
- 统一的 `screenshot_element()` / `screenshot_full_page()` / `navigate_and_wait()`

## 依赖

```bash
pip install playwright pillow pygments matplotlib imageio numpy
playwright install chromium
```

xterm.js 和 Mermaid.js 通过 CDN 加载，无需本地安装。

## 现有脚本迁移

迁移后，5 个原始脚本保留为薄 CLI 包装器，向后兼容：

| 原始脚本 | 迁移后导入来源 |
|---------|-------------|
| `terminal_screenshot.py` | `capture.terminal` |
| `screenshot_util.py` | `capture.browser` |
| `code_image_generator.py` | `capture.code` + `capture.chart` |
| `flowchart_gen.py` | `capture.flowchart` |
| `gen_cover.py` | `capture.fonts.FontManager` |
