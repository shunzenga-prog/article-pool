#!/usr/bin/env python3
"""
终端截图生成器 — 将纯文本渲染为逼真的终端窗口截图

用法:
  # 从文件读取文本并生成截图
  python terminal_screenshot.py textfile.txt -o terminal.png

  # 从标准输入读取文本
  cat output.txt | python terminal_screenshot.py - -o terminal.png

  # 直接指定文本
  python terminal_screenshot.py -t "Hello World" -o terminal.png

依赖: playwright (pip install playwright && playwright install chromium)
"""

import argparse
import os
import sys
import tempfile
from pathlib import Path

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  background: #2d2d2d;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 40px;
}
.terminal-window {
  background: #1e1e2e;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.05);
  overflow: hidden;
  width: fit-content;
  min-width: 300px;
  max-width: 100%;
}
.titlebar {
  background: #181825;
  padding: 14px 18px;
  display: flex;
  align-items: center;
  user-select: none;
  border-bottom: 1px solid #313244;
}
.titlebar-dots { display: flex; gap: 8px; }
.titlebar-dot {
  width: 12px; height: 12px; border-radius: 50%;
}
.titlebar-dot.red { background: #f38ba8; }
.titlebar-dot.yellow { background: #f9e2af; }
.titlebar-dot.green { background: #a6e3a1; }
.titlebar-text {
  flex: 1; text-align: center;
  font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
  font-size: 12px; color: #6c7086; margin-right: 60px;
}
.terminal-body {
  padding: 20px 22px;
  font-family: 'Cascadia Code', 'Fira Code', 'Consolas', 'Microsoft YaHei', 'SimHei', monospace;
  font-size: 14px;
  line-height: 1.55;
  color: #cdd6f4;
  white-space: pre;
  overflow-x: auto;
}
.terminal-prompt {
  color: #a6e3a1;
}
.terminal-highlight {
  background: #313244;
  display: inline-block;
}
</style>
</head>
<body>
<div class="terminal-window">
  <div class="titlebar">
    <div class="titlebar-dots">
      <div class="titlebar-dot red"></div>
      <div class="titlebar-dot yellow"></div>
      <div class="titlebar-dot green"></div>
    </div>
    <div class="titlebar-text">__TITLE__</div>
  </div>
  <div class="terminal-body">__CONTENT__</div>
</div>
</body>
</html>
"""


def escape_html(text: str) -> str:
    """转义 HTML 特殊字符"""
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace('"', "&quot;")
    return text


def text_to_html(text: str) -> str:
    """将纯文本转换为终端 HTML 内容"""
    lines = text.rstrip("\n").split("\n")
    html_lines = []
    for line in lines:
        escaped = escape_html(line)
        html_lines.append(f"<div>{escaped}</div>")
    return "\n".join(html_lines)


def generate_terminal_html(text: str, title: str = "bash") -> str:
    """生成终端风格 HTML"""
    content = text_to_html(text)
    html = HTML_TEMPLATE.replace("__TITLE__", escape_html(title))
    html = html.replace("__CONTENT__", content)
    return html


def take_screenshot(html_path: str, output_path: str, padding: int = 40):
    """使用 Playwright 截图 HTML 文件"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("❌ 请先安装 Playwright:")
        print("   pip install playwright && python -m playwright install chromium")
        sys.exit(1)

    abs_path = os.path.abspath(html_path)
    url = f"file:///{abs_path.replace(os.sep, '/')}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        page.goto(url, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(500)

        # 截取终端窗口元素
        el = page.query_selector(".terminal-window")
        if el:
            el.screenshot(path=output_path)
        else:
            page.screenshot(path=output_path, full_page=True)

        print(f"✅ 截图已保存: {output_path} ({os.path.getsize(output_path)/1024:.0f} KB)")
        browser.close()


def main():
    parser = argparse.ArgumentParser(description="生成逼真的终端截图")
    parser.add_argument("input", nargs="?", default="-",
                        help="输入文件路径 (默认: stdin)")
    parser.add_argument("-o", "--output", default="terminal.png",
                        help="输出 PNG 路径")
    parser.add_argument("-t", "--text", help="直接指定文本内容")
    parser.add_argument("--title", default="bash",
                        help="终端标题栏文本 (默认: bash)")
    parser.add_argument("--padding", type=int, default=40,
                        help="窗口外边距 (默认: 40)")

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
        print("❌ 没有输入文本")
        sys.exit(1)

    # 生成 HTML
    html = generate_terminal_html(text, title=args.title)

    # 写入临时 HTML 文件
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".html", encoding="utf-8", delete=False
    ) as f:
        f.write(html)
        tmp_html = f.name

    try:
        take_screenshot(tmp_html, args.output, padding=args.padding)
    finally:
        os.unlink(tmp_html)


if __name__ == "__main__":
    main()
