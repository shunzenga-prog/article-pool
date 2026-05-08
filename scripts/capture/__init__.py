"""capture — 统一截图工具包

五个截图能力，一个包。可被任何工作流独立引用。

## 基础组件

- FontManager: 跨平台 CJK 字体检测（单例）
- ThemeRegistry: 14 套颜色令牌
- BaseCapture: Playwright 浏览器/临时文件 共享生命周期

## 五个截图能力

| 模块 | 能力 | 技术栈 |
|------|------|--------|
| terminal | 终端截图 | xterm.js + Playwright |
| browser  | 网页/本地文件截图 | Playwright |
| code     | 代码高亮 + 终端输出 + GIF 动画 | Pygments + Pillow + imageio |
| flowchart| 流程图渲染 | Mermaid.js + Playwright |
| chart    | Matplotlib 图表 | Matplotlib 子进程 |
"""

# ── 基础组件 ────────────────────────────────
from .fonts import FontManager, get_font_manager
from .themes import ColorTokens, ThemeRegistry, CATPPUCCIN_MOCHA, GITHUB_DARK
from .base import BaseCapture

# ── 终端截图 ────────────────────────────────
from .terminal import TerminalCapture, terminal_screenshot

# ── 浏览器截图 ──────────────────────────────
from .browser import (
    BrowserCapture,
    browser_screenshot,
    batch_screenshots,
    file_screenshot,
    annotated_screenshot,
)

# ── 代码截图 ────────────────────────────────
from .code import (
    CodeCapture,
    code_to_image,
    exec_to_image,
    code_to_animation,
)

# ── 流程图 ──────────────────────────────────
from .flowchart import (
    FlowchartCapture,
    flowchart_to_image,
    list_palettes,
    PALETTE_NAMES,
    CARD_STYLES,
)

# ── 图表 ───────────────────────────────────
from .chart import ChartCapture, chart_screenshot

__all__ = [
    # 基础
    "FontManager", "get_font_manager",
    "ColorTokens", "ThemeRegistry", "CATPPUCCIN_MOCHA", "GITHUB_DARK",
    "BaseCapture",
    # 终端
    "TerminalCapture", "terminal_screenshot",
    # 浏览器
    "BrowserCapture", "browser_screenshot", "batch_screenshots",
    "file_screenshot", "annotated_screenshot",
    # 代码
    "CodeCapture", "code_to_image", "exec_to_image", "code_to_animation",
    # 流程图
    "FlowchartCapture", "flowchart_to_image", "list_palettes",
    "PALETTE_NAMES", "CARD_STYLES",
    # 图表
    "ChartCapture", "chart_screenshot",
]
