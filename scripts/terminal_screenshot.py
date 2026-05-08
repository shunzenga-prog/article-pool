#!/usr/bin/env python3
"""
终端截图生成器 — 薄 CLI 包装器，核心逻辑在 scripts/capture/terminal.py

用法:
  python terminal_screenshot.py textfile.txt -o terminal.png
  python terminal_screenshot.py -t "Hello World" -o terminal.png
  python terminal_screenshot.py textfile.txt --os windows --title "PowerShell" -o terminal.png

依赖: playwright (pip install playwright && playwright install chromium)
"""

import argparse
import sys
from pathlib import Path

from capture.terminal import terminal_screenshot


def main():
    parser = argparse.ArgumentParser(description="生成 xterm.js 终端截图")
    parser.add_argument(
        "input", nargs="?", default="-", help="输入文件 (默认: stdin)"
    )
    parser.add_argument("-o", "--output", default="terminal.png", help="输出 PNG 路径")
    parser.add_argument("-t", "--text", help="直接指定文本")
    parser.add_argument(
        "--os",
        choices=["windows", "macos", "linux"],
        default=None,
        help="终端样式: windows|macos|linux (默认: 自动检测)",
    )
    parser.add_argument(
        "--title",
        default=None,
        help="标题栏文本 (默认: 按 OS 自动)",
    )
    args = parser.parse_args()

    # 读取文本
    if args.text:
        text = args.text
    elif args.input == "-":
        if sys.stdin.isatty():
            print("❌ 需要输入文本。用法：")
            print("   python terminal_screenshot.py textfile.txt -o out.png")
            print("   echo 'hello' | python terminal_screenshot.py -o out.png")
            print("   python terminal_screenshot.py -t 'hello' -o out.png")
            sys.exit(1)
        text = sys.stdin.read()
    else:
        if not Path(args.input).exists():
            print(f"❌ 文件不存在: {args.input}", file=sys.stderr)
            sys.exit(1)
        with open(args.input, "r", encoding="utf-8") as f:
            text = f.read()

    if not text.strip():
        print("❌ 输入文本为空")
        sys.exit(1)

    terminal_screenshot(
        text,
        output_path=args.output,
        title=args.title,
        os_name=args.os,
    )


if __name__ == "__main__":
    main()
