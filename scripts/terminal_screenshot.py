#!/usr/bin/env python3
"""
终端截图生成器 v2 — 使用 xterm.js 渲染逼真的终端窗口截图

自动检测操作系统，匹配对应的终端标题栏样式：
  - Windows → Windows Terminal 标签页风格
  - macOS   → 原生 Terminal（交通灯按钮）
  - Linux   → GNOME Terminal 风格

用法:
  python terminal_screenshot.py textfile.txt -o terminal.png
  python terminal_screenshot.py -t "Hello World" -o terminal.png
  python terminal_screenshot.py textfile.txt --os windows --title "PowerShell" -o terminal.png

依赖: playwright (pip install playwright && playwright install chromium)
"""

import argparse
import os
import sys
import tempfile
import json
import platform

# xterm.js + xterm-addon-fit CDN URLs（固定版本，离线可缓存）
XTERM_CSS = "https://cdn.jsdelivr.net/npm/xterm@5.3.0/css/xterm.min.css"
XTERM_JS  = "https://cdn.jsdelivr.net/npm/xterm@5.3.0/lib/xterm.min.js"
FIT_JS    = "https://cdn.jsdelivr.net/npm/xterm-addon-fit@0.8.0/lib/xterm-addon-fit.min.js"


# ═══════════════════════════════════════════════════════════
#  终端外观定义 — 按 OS 适配
# ═══════════════════════════════════════════════════════════
TERMINAL_STYLES = {
    "windows": {
        "name": "Windows Terminal",
        "default_title": "PowerShell",
        "wrapper_style": """
background: #0c0c0c;
border-radius: 8px;
box-shadow: 0 18px 48px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.06);
overflow: hidden;
""",
        "titlebar_html": r"""
<div class="wt-titlebar">
  <div class="wt-tab active">
    <span class="wt-tab-icon">>_</span>
    <span class="wt-tab-title">__TITLE__</span>
  </div>
  <div class="wt-tab-bar-spacer"></div>
</div>
""",
        "titlebar_css": r"""
.wt-titlebar {
  background: #1f1f1f;
  display: flex; align-items: stretch;
  height: 32px;
  border-bottom: 1px solid #2d2d2d;
  user-select: none;
}
.wt-tab {
  display: flex; align-items: center; gap: 8px;
  background: #0c0c0c;
  padding: 0 20px; min-width: 140px;
  border-right: 1px solid #2d2d2d;
  font-family: 'Segoe UI', system-ui, sans-serif;
  font-size: 12px; color: #cccccc;
}
.wt-tab-icon { color: #569cd6; font-weight: bold; font-size: 11px; }
.wt-tab-title { color: #cccccc; }
.wt-tab-bar-spacer { flex: 1; }
""",
    },
    "macos": {
        "name": "Terminal",
        "default_title": "bash",
        "wrapper_style": """
background: #1e1e2e;
border-radius: 12px;
box-shadow: 0 18px 48px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.05);
overflow: hidden;
""",
        "titlebar_html": r"""
<div class="mac-titlebar">
  <div class="mac-dots">
    <div class="mac-dot r" title="关闭"></div>
    <div class="mac-dot y" title="最小化"></div>
    <div class="mac-dot g" title="全屏"></div>
  </div>
  <div class="mac-title">__TITLE__</div>
</div>
""",
        "titlebar_css": r"""
.mac-titlebar {
  background: #2d2a2e;
  padding: 10px 16px;
  display: flex; align-items: center;
  border-bottom: 1px solid #3b3a3e;
  user-select: none;
}
.mac-dots { display: flex; gap: 7px; margin-right: 14px; }
.mac-dot {
  width: 11px; height: 11px; border-radius: 50%;
  border: 1px solid rgba(0,0,0,0.15);
}
.mac-dot.r { background: #ff5f57; }
.mac-dot.y { background: #febc2e; }
.mac-dot.g { background: #28c840; }
.mac-title {
  font-family: -apple-system, 'SF Pro', system-ui, sans-serif;
  font-size: 12px; color: #9995a0;
  text-align: center; flex: 1; margin-right: 56px;
}
""",
    },
    "linux": {
        "name": "GNOME Terminal",
        "default_title": "Terminal",
        "wrapper_style": """
background: #300a24;
border-radius: 8px;
box-shadow: 0 18px 48px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.06);
overflow: hidden;
""",
        "titlebar_html": r"""
<div class="gnome-titlebar">
  <span class="gnome-title">__TITLE__</span>
</div>
""",
        "titlebar_css": r"""
.gnome-titlebar {
  background: #2b1f2d;
  padding: 8px 16px;
  display: flex; align-items: center;
  border-bottom: 1px solid #3d2e3f;
  user-select: none;
}
.gnome-title {
  font-family: 'Ubuntu', 'Cantarell', system-ui, sans-serif;
  font-size: 12px; color: #a59ea7;
  text-align: center; flex: 1;
}
""",
    },
}


def detect_os() -> str:
    """检测操作系统"""
    system = platform.system()
    if system == "Windows":
        return "windows"
    elif system == "Darwin":
        return "macos"
    else:
        return "linux"


# ═══════════════════════════════════════════════════════════
#  HTML 模板 — 按 OS 动态组装
# ═══════════════════════════════════════════════════════════
HTML_BASE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<link rel="stylesheet" href="__XTERM_CSS__">
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  background: #1a1a2e;
  display: flex; justify-content: center; align-items: center;
  min-height: 100vh; padding: 48px;
}
.terminal-wrapper {
  __WRAPPER_STYLE__
}
__TITLEBAR_CSS__
#terminal {
  padding: 10px 16px;
}
</style>
</head>
<body>
<div class="terminal-wrapper">
  __TITLEBAR__
  <div id="terminal"></div>
</div>
<script src="__XTERM_JS__"></script>
<script src="__FIT_JS__"></script>
<script>
const LINES = __LINES_JSON__;
const term = new Terminal({
  cols: __COLS__,
  rows: __ROWS__,
  fontSize: 14,
  fontFamily: "'Cascadia Code', 'Consolas', 'Courier New', monospace",
  letterSpacing: 0,
  lineHeight: 1.5,
  cursorBlink: false,
  cursorStyle: 'block',
  theme: {
    foreground: '#cdd6f4',
    background: '__TERM_BG__',
    cursor: '#f5e0dc',
    selectionBackground: '#585b70',
    black:   '#45475a',    red:     '#f38ba8',
    green:   '#a6e3a1',    yellow:  '#f9e2af',
    blue:    '#89b4fa',    magenta: '#f5c2e7',
    cyan:    '#94e2d5',    white:   '#bac2de',
    brightBlack:   '#585b70',  brightRed:     '#f38ba8',
    brightGreen:   '#a6e3a1',  brightYellow:  '#f9e2af',
    brightBlue:    '#89b4fa',  brightMagenta: '#f5c2e7',
    brightCyan:    '#94e2d5',  brightWhite:   '#a6adc8',
  },
  allowProposedApi: true,
});
const fitAddon = new FitAddon.FitAddon();
term.loadAddon(fitAddon);
term.open(document.getElementById('terminal'));

for (const line of LINES) {
  term.writeln(line);
}

setTimeout(() => {
  fitAddon.fit();
  setTimeout(() => {
    document.body.setAttribute('data-ready', '1');
  }, 100);
}, 50);
</script>
</body>
</html>
"""


def generate_terminal_html(
    text: str, title: str = "", os_name: str = "windows"
) -> tuple[str, int, int]:
    """生成终端 HTML，返回 (html, cols, rows)"""

    style = TERMINAL_STYLES.get(os_name, TERMINAL_STYLES["windows"])
    if not title:
        title = style["default_title"]

    lines = text.rstrip("\n").split("\n")

    # 计算最大行宽（CJK 字符算 2 列）
    def line_width(line: str) -> int:
        w = 0
        for ch in line:
            w += 2 if ord(ch) > 127 else 1
        return w

    max_width = max((line_width(line) for line in lines), default=80)
    cols = max(max_width + 2, 60)
    rows = max(len(lines) + 1, 6)

    # 终端背景色（与标题栏协调）
    term_bg = {"windows": "#0c0c0c", "macos": "#1e1e2e", "linux": "#300a24"}.get(
        os_name, "#0c0c0c"
    )

    # 组装 HTML
    html = HTML_BASE
    html = html.replace("__XTERM_CSS__", XTERM_CSS)
    html = html.replace("__XTERM_JS__", XTERM_JS)
    html = html.replace("__FIT_JS__", FIT_JS)
    html = html.replace("__WRAPPER_STYLE__", style["wrapper_style"])
    html = html.replace("__TITLEBAR_CSS__", style["titlebar_css"])
    html = html.replace("__TITLEBAR__", style["titlebar_html"].replace("__TITLE__", title))
    html = html.replace("__TERM_BG__", term_bg)
    html = html.replace("__LINES_JSON__", json.dumps(lines, ensure_ascii=False))
    html = html.replace("__COLS__", str(cols))
    html = html.replace("__ROWS__", str(rows))

    return html, cols, rows


def take_screenshot(html_path: str, output_path: str):
    """使用 Playwright 截图"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("请先安装: pip install playwright && playwright install chromium")
        sys.exit(1)

    abs_path = os.path.abspath(html_path)
    url = f"file:///{abs_path.replace(os.sep, '/')}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto(url, wait_until="networkidle", timeout=60000)

        page.wait_for_selector('[data-ready="1"]', timeout=15000)
        page.wait_for_timeout(300)

        el = page.query_selector(".terminal-wrapper")
        if el:
            el.screenshot(path=output_path)
        else:
            page.screenshot(path=output_path, full_page=True)

        size_kb = os.path.getsize(output_path) / 1024
        print(f"  [OK] 终端截图 → {output_path} ({size_kb:.0f} KB)")
        browser.close()


def main():
    current_os = detect_os()
    default_style = TERMINAL_STYLES[current_os]
    os_names = "|".join(TERMINAL_STYLES.keys())

    parser = argparse.ArgumentParser(description="生成 xterm.js 终端截图")
    parser.add_argument(
        "input", nargs="?", default="-", help="输入文件 (默认: stdin)"
    )
    parser.add_argument("-o", "--output", default="terminal.png", help="输出 PNG 路径")
    parser.add_argument("-t", "--text", help="直接指定文本")
    parser.add_argument(
        "--os",
        choices=list(TERMINAL_STYLES.keys()),
        default=current_os,
        help=f"终端样式: {os_names} (默认: {current_os})",
    )
    parser.add_argument(
        "--title",
        default="",
        help=f"标题栏文本 (默认: {default_style['default_title']})",
    )
    args = parser.parse_args()

    # 读取文本
    if args.text:
        text = args.text
    elif args.input == "-":
        text = sys.stdin.read()
    else:
        with open(args.input, "r", encoding="utf-8") as f:
            text = f.read()

    if not text.strip():
        print("没有输入文本")
        sys.exit(1)

    # 生成 HTML
    html, cols, rows = generate_terminal_html(text, title=args.title, os_name=args.os)
    style_name = TERMINAL_STYLES[args.os]["name"]
    print(f"  OS: {args.os} ({style_name})")
    print(f"  文本: {len(text.split(chr(10)))} 行, 最宽 {cols} 列 → 终端 {cols}×{rows}")

    # 写入临时 HTML → 截图
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".html", encoding="utf-8", delete=False
    ) as f:
        f.write(html)
        tmp_html = f.name

    try:
        take_screenshot(tmp_html, args.output)
    finally:
        os.unlink(tmp_html)


if __name__ == "__main__":
    main()
