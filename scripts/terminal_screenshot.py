#!/usr/bin/env python3
"""
终端截图生成器 v2 — 使用 xterm.js 渲染逼真的终端窗口截图

用法:
  python terminal_screenshot.py textfile.txt -o terminal.png
  python terminal_screenshot.py -t "Hello World" -o terminal.png

依赖: playwright (pip install playwright && playwright install chromium)
"""

import argparse
import os
import sys
import tempfile
import json
from pathlib import Path

# xterm.js + xterm-addon-fit CDN URLs (固定版本，离线可缓存)
XTERM_CSS  = "https://cdn.jsdelivr.net/npm/xterm@5.3.0/css/xterm.min.css"
XTERM_JS   = "https://cdn.jsdelivr.net/npm/xterm@5.3.0/lib/xterm.min.js"
FIT_JS     = "https://cdn.jsdelivr.net/npm/xterm-addon-fit@0.8.0/lib/xterm-addon-fit.min.js"

HTML_TEMPLATE = r"""<!DOCTYPE html>
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
  background: #1e1e2e;
  border-radius: 12px;
  box-shadow: 0 18px 48px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.05);
  overflow: hidden;
}
.titlebar {
  background: #181825;
  padding: 12px 18px;
  display: flex; align-items: center;
  border-bottom: 1px solid #313244;
  user-select: none;
}
.titlebar-dots { display: flex; gap: 8px; margin-right: 18px; }
.titlebar-dot {
  width: 11px; height: 11px; border-radius: 50%;
  border: 1px solid rgba(0,0,0,0.12);
}
.titlebar-dot.r { background: #ff5f57; }
.titlebar-dot.y { background: #febc2e; }
.titlebar-dot.g { background: #28c840; }
.titlebar-text {
  font-family: -apple-system, 'Segoe UI', system-ui, sans-serif;
  font-size: 12px; color: #8b8fa4;
  text-align: center; flex: 1; margin-right: 60px;
}
#terminal {
  padding: 10px 16px;
}
</style>
</head>
<body>
<div class="terminal-wrapper">
  <div class="titlebar">
    <div class="titlebar-dots">
      <div class="titlebar-dot r"></div>
      <div class="titlebar-dot y"></div>
      <div class="titlebar-dot g"></div>
    </div>
    <div class="titlebar-text">__TITLE__</div>
  </div>
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
    background: '#1e1e2e',
    cursor: '#f5e0dc',
    selectionBackground: '#585b70',
    black: '#45475a',
    red: '#f38ba8',
    green: '#a6e3a1',
    yellow: '#f9e2af',
    blue: '#89b4fa',
    magenta: '#f5c2e7',
    cyan: '#94e2d5',
    white: '#bac2de',
    brightBlack: '#585b70',
    brightRed: '#f38ba8',
    brightGreen: '#a6e3a1',
    brightYellow: '#f9e2af',
    brightBlue: '#89b4fa',
    brightMagenta: '#f5c2e7',
    brightCyan: '#94e2d5',
    brightWhite: '#a6adc8',
  },
  allowProposedApi: true,
});
const fitAddon = new FitAddon.FitAddon();
term.loadAddon(fitAddon);
term.open(document.getElementById('terminal'));

// Write lines to terminal
for (const line of LINES) {
  term.writeln(line);
}

// Wait for rendering then adjust size
setTimeout(() => {
  fitAddon.fit();
  // Add a small delay to ensure xterm reflows before screenshot
  setTimeout(() => {
    document.body.setAttribute('data-ready', '1');
  }, 100);
}, 50);
</script>
</body>
</html>
"""


def escape_text(text: str) -> str:
    """Prepare text for JSON embedding"""
    return text


def generate_terminal_html(text: str, title: str = "bash") -> tuple[str, int, int]:
    """生成终端 HTML，返回 (html, cols, rows)"""
    lines = text.rstrip("\n").split("\n")

    # Calculate max line length (CJK chars count as 2)
    def line_width(line: str) -> int:
        w = 0
        for ch in line:
            if ord(ch) > 127:
                w += 2  # CJK = 2 cols
            else:
                w += 1
        return w

    max_width = max((line_width(line) for line in lines), default=80)
    cols = max(max_width + 2, 60)
    rows = max(len(lines) + 1, 6)

    # JSON-encode lines
    lines_json = json.dumps(lines, ensure_ascii=False)

    html = HTML_TEMPLATE.replace("__XTERM_CSS__", XTERM_CSS)
    html = html.replace("__XTERM_JS__", XTERM_JS)
    html = html.replace("__FIT_JS__", FIT_JS)
    html = html.replace("__TITLE__", title)
    html = html.replace("__LINES_JSON__", lines_json)
    html = html.replace("__COLS__", str(cols))
    html = html.replace("__ROWS__", str(rows))

    return html, cols, rows


def take_screenshot(html_path: str, output_path: str):
    """Use Playwright to screenshot the xterm.js terminal"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("请先安装 Playwright: pip install playwright && playwright install chromium")
        sys.exit(1)

    abs_path = os.path.abspath(html_path)
    url = f"file:///{abs_path.replace(os.sep, '/')}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto(url, wait_until="networkidle", timeout=60000)

        # Wait for xterm to finish rendering
        page.wait_for_selector('[data-ready="1"]', timeout=15000)
        page.wait_for_timeout(300)

        # Screenshot the terminal wrapper
        el = page.query_selector(".terminal-wrapper")
        if el:
            el.screenshot(path=output_path)
        else:
            page.screenshot(path=output_path, full_page=True)

        size_kb = os.path.getsize(output_path) / 1024
        print(f"  [OK] 终端截图 → {output_path} ({size_kb:.0f} KB)")
        browser.close()


def main():
    parser = argparse.ArgumentParser(description="生成 xterm.js 终端截图")
    parser.add_argument("input", nargs="?", default="-",
                        help="输入文件 (默认: stdin)")
    parser.add_argument("-o", "--output", default="terminal.png",
                        help="输出 PNG 路径")
    parser.add_argument("-t", "--text", help="直接指定文本")
    parser.add_argument("--title", default="bash",
                        help="终端标题栏文本")
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
    html, cols, rows = generate_terminal_html(text, title=args.title)
    print(f"  文本: {len(text.split(chr(10)))} 行, 最宽 {cols} 列 → 终端 {cols}×{rows}")

    # 写入临时 HTML
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
