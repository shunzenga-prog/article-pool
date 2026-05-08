"""终端截图 — xterm.js + Playwright 生成逼真的终端窗口截图

操作系统自适应标题栏：
  - Windows → Windows Terminal 标签页（>_ 图标 + 深色标签栏）
  - macOS   → 原生 Terminal（红黄绿交通灯按钮）
  - Linux   → GNOME Terminal 扁平标题栏

用法:
    from capture.terminal import TerminalCapture, terminal_screenshot

    # 类方式
    with TerminalCapture() as tc:
        tc.render("echo hello", output="terminal.png", os_name="windows")

    # 一键函数
    terminal_screenshot("ls -la", "output.png", title="PowerShell", os="windows")
"""

from __future__ import annotations

import json
from typing import Optional

from .base import BaseCapture

# xterm.js CDN URLs
XTERM_CSS = "https://cdn.jsdelivr.net/npm/xterm@5.3.0/css/xterm.min.css"
XTERM_JS = "https://cdn.jsdelivr.net/npm/xterm@5.3.0/lib/xterm.min.js"
FIT_JS = "https://cdn.jsdelivr.net/npm/xterm-addon-fit@0.8.0/lib/xterm-addon-fit.min.js"

# ═══════════════════════════════════════════════
#  终端外观定义 — 按 OS 适配
# ═══════════════════════════════════════════════

TERMINAL_STYLES = {
    "windows": {
        "name": "Windows Terminal",
        "default_title": "PowerShell",
        "wrapper_style": (
            "background: #0c0c0c; "
            "border-radius: 8px; "
            "box-shadow: 0 18px 48px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.06); "
            "overflow: hidden;"
        ),
        "titlebar_html": (
            '<div class="wt-titlebar">'
            '  <div class="wt-tab active">'
            '    <span class="wt-tab-icon">&gt;_</span>'
            '    <span class="wt-tab-title">__TITLE__</span>'
            '  </div>'
            '  <div class="wt-tab-bar-spacer"></div>'
            '</div>'
        ),
        "titlebar_css": (
            ".wt-titlebar {"
            "  background: #1f1f1f; display: flex; align-items: stretch;"
            "  height: 32px; border-bottom: 1px solid #2d2d2d; user-select: none; }"
            ".wt-tab {"
            "  display: flex; align-items: center; gap: 8px;"
            "  background: #0c0c0c; padding: 0 20px; min-width: 140px;"
            "  border-right: 1px solid #2d2d2d;"
            "  font-family: 'Segoe UI', system-ui, sans-serif;"
            "  font-size: 12px; color: #cccccc; }"
            ".wt-tab-icon { color: #569cd6; font-weight: bold; font-size: 11px; }"
            ".wt-tab-title { color: #cccccc; }"
            ".wt-tab-bar-spacer { flex: 1; }"
        ),
        "term_bg": "#0c0c0c",
    },
    "macos": {
        "name": "Terminal",
        "default_title": "bash",
        "wrapper_style": (
            "background: #1e1e2e; "
            "border-radius: 12px; "
            "box-shadow: 0 18px 48px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.05); "
            "overflow: hidden;"
        ),
        "titlebar_html": (
            '<div class="mac-titlebar">'
            '  <div class="mac-dots">'
            '    <div class="mac-dot r" title="关闭"></div>'
            '    <div class="mac-dot y" title="最小化"></div>'
            '    <div class="mac-dot g" title="全屏"></div>'
            '  </div>'
            '  <div class="mac-title">__TITLE__</div>'
            '</div>'
        ),
        "titlebar_css": (
            ".mac-titlebar {"
            "  background: #2d2a2e; padding: 10px 16px;"
            "  display: flex; align-items: center;"
            "  border-bottom: 1px solid #3b3a3e; user-select: none; }"
            ".mac-dots { display: flex; gap: 7px; margin-right: 14px; }"
            ".mac-dot { width: 11px; height: 11px; border-radius: 50%;"
            "  border: 1px solid rgba(0,0,0,0.15); }"
            ".mac-dot.r { background: #ff5f57; }"
            ".mac-dot.y { background: #febc2e; }"
            ".mac-dot.g { background: #28c840; }"
            ".mac-title {"
            "  font-family: -apple-system, 'SF Pro', system-ui, sans-serif;"
            "  font-size: 12px; color: #9995a0;"
            "  text-align: center; flex: 1; margin-right: 56px; }"
        ),
        "term_bg": "#1e1e2e",
    },
    "linux": {
        "name": "GNOME Terminal",
        "default_title": "Terminal",
        "wrapper_style": (
            "background: #300a24; "
            "border-radius: 8px; "
            "box-shadow: 0 18px 48px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.06); "
            "overflow: hidden;"
        ),
        "titlebar_html": (
            '<div class="gnome-titlebar">'
            '  <span class="gnome-title">__TITLE__</span>'
            '</div>'
        ),
        "titlebar_css": (
            ".gnome-titlebar {"
            "  background: #2b1f2d; padding: 8px 16px;"
            "  display: flex; align-items: center;"
            "  border-bottom: 1px solid #3d2e3f; user-select: none; }"
            ".gnome-title {"
            "  font-family: 'Ubuntu', 'Cantarell', system-ui, sans-serif;"
            "  font-size: 12px; color: #a59ea7;"
            "  text-align: center; flex: 1; }"
        ),
        "term_bg": "#300a24",
    },
}

# xterm.js 默认 Catppuccin Mocha 主题
XTERM_THEME = {
    "foreground": "#cdd6f4",
    "cursor": "#f5e0dc",
    "selectionBackground": "#585b70",
    "black": "#45475a",
    "red": "#f38ba8",
    "green": "#a6e3a1",
    "yellow": "#f9e2af",
    "blue": "#89b4fa",
    "magenta": "#f5c2e7",
    "cyan": "#94e2d5",
    "white": "#bac2de",
    "brightBlack": "#585b70",
    "brightRed": "#f38ba8",
    "brightGreen": "#a6e3a1",
    "brightYellow": "#f9e2af",
    "brightBlue": "#89b4fa",
    "brightMagenta": "#f5c2e7",
    "brightCyan": "#94e2d5",
    "brightWhite": "#a6adc8",
}

HTML_TEMPLATE = (
    '<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">'
    '<link rel="stylesheet" href="__XTERM_CSS__"><style>'
    "* { margin: 0; padding: 0; box-sizing: border-box; }"
    "body {"
    "  background: #1a1a2e;"
    "  display: flex; justify-content: center; align-items: center;"
    "  min-height: 100vh; padding: 48px; }"
    ".terminal-wrapper { __WRAPPER_STYLE__ }"
    "__TITLEBAR_CSS__"
    "#terminal { padding: 10px 16px; }"
    "</style></head><body>"
    '<div class="terminal-wrapper">'
    "  __TITLEBAR__"
    '  <div id="terminal"></div>'
    "</div>"
    '<script src="__XTERM_JS__"></script>'
    '<script src="__FIT_JS__"></script>'
    "<script>"
    "const LINES = __LINES_JSON__;"
    "const term = new Terminal({"
    "  cols: __COLS__, rows: __ROWS__, fontSize: 14,"
    '  fontFamily: "\'Cascadia Code\', \'Consolas\', \'Courier New\', monospace",'
    "  letterSpacing: 0, lineHeight: 1.5,"
    "  cursorBlink: false, cursorStyle: 'block',"
    "  theme: __XTERM_THEME__,"
    "  allowProposedApi: true,"
    "});"
    "const fitAddon = new FitAddon.FitAddon();"
    "term.loadAddon(fitAddon);"
    "term.open(document.getElementById('terminal'));"
    "for (const line of LINES) { term.writeln(line); }"
    "setTimeout(() => { fitAddon.fit();"
    "  setTimeout(() => { document.body.setAttribute('data-ready', '1'); }, 100);"
    "}, 50);"
    "</script></body></html>"
)


def _line_width(line: str) -> int:
    """计算行宽（CJK 字符算 2 列）"""
    return sum(2 if ord(ch) > 127 else 1 for ch in line)


class TerminalCapture(BaseCapture):
    """xterm.js 终端截图器。

    使用 CDN 加载的 xterm.js + Playwright 渲染逼真终端窗口。
    """

    def generate_html(
        self,
        text: str,
        title: str = "",
        os_name: str = "windows",
    ) -> tuple[str, int, int]:
        """生成终端 HTML。返回 (html, cols, rows)。"""
        style = TERMINAL_STYLES.get(os_name, TERMINAL_STYLES["windows"])
        if not title:
            title = style["default_title"]

        lines = text.rstrip("\n").split("\n")
        max_width = max((_line_width(line) for line in lines), default=80)
        cols = max(max_width + 2, 60)
        rows = max(len(lines) + 1, 6)

        html = HTML_TEMPLATE
        html = html.replace("__XTERM_CSS__", XTERM_CSS)
        html = html.replace("__XTERM_JS__", XTERM_JS)
        html = html.replace("__FIT_JS__", FIT_JS)
        html = html.replace("__WRAPPER_STYLE__", style["wrapper_style"])
        html = html.replace("__TITLEBAR_CSS__", style["titlebar_css"])
        html = html.replace(
            "__TITLEBAR__",
            style["titlebar_html"].replace("__TITLE__", title),
        )
        html = html.replace("__LINES_JSON__", json.dumps(lines, ensure_ascii=False))
        html = html.replace("__COLS__", str(cols))
        html = html.replace("__ROWS__", str(rows))
        html = html.replace(
            "__XTERM_THEME__",
            json.dumps(
                dict(XTERM_THEME, background=style["term_bg"])
            ),
        )

        return html, cols, rows

    def render(
        self,
        text: str,
        title: str = "",
        os_name: str = "windows",
        output_path: str = "terminal.png",
    ) -> str:
        """生成终端 HTML → Playwright 截图 → 保存 PNG。返回输出路径。"""
        import platform

        if not os_name or os_name not in TERMINAL_STYLES:
            system = platform.system()
            os_map = {"Windows": "windows", "Darwin": "macos"}
            os_name = os_map.get(system, "linux")

        html, cols, rows = self.generate_html(text, title=title, os_name=os_name)
        style_name = TERMINAL_STYLES[os_name]["name"]
        print(f"  OS: {os_name} ({style_name}) — {rows} 行 × {cols} 列")

        tmp_html = self.temp_html(html)
        url = self.file_url(tmp_html)

        with self.browser_page() as page:
            self.navigate_and_wait(page, url)
            page.wait_for_selector('[data-ready="1"]', timeout=15000)
            page.wait_for_timeout(300)
            el = page.query_selector(".terminal-wrapper")
            if el:
                el.screenshot(path=output_path)
            else:
                page.screenshot(path=output_path, full_page=True)
            self._log_screenshot(output_path)

        return output_path


# ── 便利函数 ──────────────────────────────────


def terminal_screenshot(
    text: str,
    output_path: str = "terminal.png",
    title: Optional[str] = None,
    os_name: Optional[str] = None,
) -> str:
    """一键终端截图。

    Args:
        text: 终端文本内容
        output_path: 输出 PNG 路径
        title: 标题栏文本（默认按 OS 自动选择）
        os_name: windows / macos / linux（默认自动检测）

    Returns:
        输出文件路径
    """
    with TerminalCapture() as tc:
        return tc.render(
            text,
            title=title or "",
            os_name=os_name or "",
            output_path=output_path,
        )
