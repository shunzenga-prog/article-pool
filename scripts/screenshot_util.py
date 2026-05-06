#!/usr/bin/env python3
"""
教程截图工具 — 基于 Playwright 的自动化网页截图
用于 AI 实战教程系列的配图生成

用法：
  # 截取单个网页
  python screenshot_util.py single "https://example.com" --output demo.png

  # 截取多个 URL（批量教程配图）
  python screenshot_util.py batch urls.txt --output-dir screenshots/

  # 截取本地 HTML 文件
  python screenshot_util.py file output.html --width 800 --height 900 --output step1.png

  # 截取并标注（适合展示操作步骤）
  python screenshot_util.py annotate "https://example.com" --click ".btn" --output step1.png
"""

import argparse
import os
import sys
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("请先安装 Playwright: python -m pip install playwright && python -m playwright install chromium")
    sys.exit(1)


VIEWPORT = {"width": 1280, "height": 800}


def _launch(p):
    return p.chromium.launch(headless=True)


def cmd_single(url: str, output: str, width: int = 1280, height: int = 800, selector: str = None):
    """截取单个网页全页截图"""
    with sync_playwright() as p:
        browser = _launch(p)
        page = browser.new_page(viewport={"width": width, "height": height})
        page.goto(url, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(1000)

        if selector:
            el = page.query_selector(selector)
            if el:
                el.screenshot(path=output)
            else:
                print(f"未找到元素: {selector}，改为全页截图")
                page.screenshot(path=output, full_page=True)
        else:
            page.screenshot(path=output, full_page=True)

        print(f"截图已保存: {output}")
        browser.close()


def cmd_batch(urls_file: str, output_dir: str, width: int = 1280, height: int = 800):
    """批量截图 URL 列表"""
    os.makedirs(output_dir, exist_ok=True)
    with open(urls_file, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    with sync_playwright() as p:
        browser = _launch(p)
        for i, url in enumerate(urls):
            page = browser.new_page(viewport={"width": width, "height": height})
            try:
                page.goto(url, wait_until="networkidle", timeout=30000)
                page.wait_for_timeout(1000)
                name = f"screenshot_{i+1:02d}.png"
                out = os.path.join(output_dir, name)
                page.screenshot(path=out, full_page=True)
                print(f"[{i+1}/{len(urls)}] {url} → {out}")
            except Exception as e:
                print(f"[{i+1}/{len(urls)}] 失败: {url} — {e}")
            finally:
                page.close()
        browser.close()


def cmd_file(path: str, output: str, width: int = 1280, height: int = 800, selector: str = None):
    """截取本地 HTML 文件（自动转 file:// 路径）"""
    abs_path = os.path.abspath(path)
    url = f"file:///{abs_path.replace(os.sep, '/')}"
    cmd_single(url, output, width, height, selector)


def cmd_annotate(url: str, output: str, click_selector: str = None, text: str = None, width: int = 1280, height: int = 800):
    """截取并标注——先截图，再在上面加标注"""
    from PIL import Image, ImageDraw, ImageFont

    with sync_playwright() as p:
        browser = _launch(p)
        page = browser.new_page(viewport={"width": width, "height": height})
        page.goto(url, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(1000)

        if click_selector:
            try:
                page.click(click_selector, timeout=5000)
                page.wait_for_timeout(1000)
            except Exception:
                print(f"点击失败: {click_selector}")

        page.screenshot(path=output, full_page=False)
        browser.close()

    # PIL 标注
    img = Image.open(output).convert("RGBA")
    draw = ImageDraw.Draw(img)

    if text:
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        w, h = img.size
        # 底部半透明条
        overlay_draw.rectangle([(0, h - 60), (w, h)], fill=(0, 0, 0, 160))
        try:
            font = ImageFont.truetype("simhei.ttf", 24)
        except Exception:
            font = ImageFont.load_default()
        overlay_draw.text((20, h - 48), text, fill=(255, 255, 255, 255), font=font)
        img = Image.alpha_composite(img, overlay)

    img = img.convert("RGB")
    img.save(output, "PNG")
    print(f"标注截图已保存: {output}")


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
    if args.cmd == "single":
        cmd_single(args.url, args.output, args.width, args.height, args.selector)
    elif args.cmd == "batch":
        cmd_batch(args.urls_file, args.output_dir, args.width, args.height)
    elif args.cmd == "file":
        cmd_file(args.path, args.output, args.width, args.height, args.selector)
    elif args.cmd == "annotate":
        cmd_annotate(args.url, args.output, args.click, args.text, args.width, args.height)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
