#!/usr/bin/env python3
"""
教程截图工具 — 薄 CLI 包装器，核心逻辑在 scripts/capture/browser.py

用法：
  python screenshot_util.py single "https://example.com" --output demo.png
  python screenshot_util.py batch urls.txt --output-dir screenshots/
  python screenshot_util.py file output.html --width 800 --height 900 --output step1.png
  python screenshot_util.py annotate "https://example.com" --click ".btn" --output step1.png
"""

import argparse
import os
import sys

from capture.browser import BrowserCapture


def main():
    parser = argparse.ArgumentParser(description="教程截图工具")
    sub = parser.add_subparsers(dest="cmd")

    p_single = sub.add_parser("single", help="截取单个网页")
    p_single.add_argument("url")
    p_single.add_argument("--output", "-o", default="screenshot.png")
    p_single.add_argument("--width", type=int, default=1280)
    p_single.add_argument("--height", type=int, default=800)
    p_single.add_argument("--selector", help="CSS 选择器，只截取该元素")

    p_batch = sub.add_parser("batch", help="批量截图")
    p_batch.add_argument("urls_file")
    p_batch.add_argument("--output-dir", "-o", default="screenshots/")
    p_batch.add_argument("--width", type=int, default=1280)
    p_batch.add_argument("--height", type=int, default=800)

    p_file = sub.add_parser("file", help="截取本地 HTML 文件")
    p_file.add_argument("path", help="本地 HTML 文件路径")
    p_file.add_argument("--output", "-o", default="screenshot.png")
    p_file.add_argument("--width", type=int, default=1280)
    p_file.add_argument("--height", type=int, default=800)
    p_file.add_argument("--selector", help="CSS 选择器，只截取该元素")

    p_anno = sub.add_parser("annotate", help="截取并标注")
    p_anno.add_argument("url")
    p_anno.add_argument("--output", "-o", default="annotated.png")
    p_anno.add_argument("--click", help="截取前先点击的元素选择器")
    p_anno.add_argument("--text", help="底部标注文字")
    p_anno.add_argument("--width", type=int, default=1280)
    p_anno.add_argument("--height", type=int, default=800)

    args = parser.parse_args()

    with BrowserCapture() as bc:
        if args.cmd == "single":
            bc.single(args.url, args.output, selector=args.selector,
                      width=args.width, height=args.height)
        elif args.cmd == "batch":
            with open(args.urls_file, "r", encoding="utf-8") as f:
                urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
            bc.batch(urls, args.output_dir, width=args.width, height=args.height)
        elif args.cmd == "file":
            bc.file(args.path, args.output, selector=args.selector,
                    width=args.width, height=args.height)
        elif args.cmd == "annotate":
            bc.annotate(args.url, args.output, click_selector=args.click,
                        text=args.text, width=args.width, height=args.height)
        else:
            parser.print_help()


if __name__ == "__main__":
    main()
