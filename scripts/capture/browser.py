"""浏览器截图 — Playwright 驱动的网页/本地文件截图

支持: URL 截图、批量截图、本地 HTML 文件截图、标注截图

用法:
    from capture.browser import BrowserCapture, browser_screenshot

    # 单个 URL
    browser_screenshot("https://example.com", "output.png")

    # 批量
    from capture.browser import batch_screenshots
    batch_screenshots(["url1", "url2"], "screenshots/")

    # 本地 HTML
    from capture.browser import file_screenshot
    file_screenshot("output.html", "preview.png")
"""

from __future__ import annotations

import os
from pathlib import Path

from .base import BaseCapture


class BrowserCapture(BaseCapture):
    """Playwright 浏览器截图器。"""

    def single(
        self,
        url: str,
        output_path: str,
        selector: str = None,
        width: int = 1280,
        height: int = 800,
        timeout: int = 30000,
    ) -> str:
        """截取单个网页。

        Args:
            url: 网页 URL
            output_path: 输出 PNG 路径
            selector: CSS 选择器（指定时仅截图该元素）
            width/height: 视口尺寸
            timeout: 导航超时毫秒

        Returns:
            输出文件路径
        """
        with self.browser_page(width=width, height=height) as page:
            page.goto(url, wait_until="networkidle", timeout=timeout)
            page.wait_for_timeout(1000)

            if selector:
                el = page.query_selector(selector)
                if el:
                    el.screenshot(path=output_path)
                else:
                    print(f"  ⚠️ 未找到元素: {selector}，改用全页截图")
                    page.screenshot(path=output_path, full_page=True)
            else:
                page.screenshot(path=output_path, full_page=True)

        self._log_screenshot(output_path)
        return output_path

    def batch(
        self,
        urls: list[str],
        output_dir: str,
        width: int = 1280,
        height: int = 800,
        timeout: int = 30000,
    ) -> list[str]:
        """批量截图 URL 列表。

        Returns:
            生成的截图路径列表
        """
        os.makedirs(output_dir, exist_ok=True)
        outputs = []

        for i, url in enumerate(urls):
            name = f"screenshot_{i + 1:02d}.png"
            out = os.path.join(output_dir, name)
            try:
                with self.browser_page(width=width, height=height) as page:
                    page.goto(url, wait_until="networkidle", timeout=timeout)
                    page.wait_for_timeout(1000)
                    page.screenshot(path=out, full_page=True)
                outputs.append(out)
                print(f"  [{i + 1}/{len(urls)}] {url} → {out}")
            except Exception as e:
                print(f"  [{i + 1}/{len(urls)}] 失败: {url} — {e}")

        return outputs

    def file(
        self,
        html_path: str,
        output_path: str,
        selector: str = None,
        width: int = 1280,
        height: int = 800,
    ) -> str:
        """截取本地 HTML 文件。

        Args:
            html_path: HTML 文件路径
            output_path: 输出 PNG 路径
            selector: CSS 选择器（指定时仅截图该元素）
            width/height: 视口尺寸
        """
        url = self.file_url(html_path)
        return self.single(url, output_path, selector=selector, width=width, height=height)

    def annotate(
        self,
        url: str,
        output_path: str,
        click_selector: str = None,
        text: str = None,
        width: int = 1280,
        height: int = 800,
    ) -> str:
        """截图并添加标注叠加层。

        Args:
            url: 网页 URL
            output_path: 输出 PNG 路径
            click_selector: 截图前点击的元素
            text: 叠加到底部的标注文字
            width/height: 视口尺寸
        """
        with self.browser_page(width=width, height=height) as page:
            page.goto(url, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(1000)

            if click_selector:
                try:
                    page.click(click_selector)
                    page.wait_for_timeout(1000)
                except Exception as e:
                    print(f"  ⚠️ 点击失败: {click_selector} — {e}")

            page.screenshot(path=output_path, full_page=False)

        # 可选：PIL 文字叠加
        if text:
            self._add_text_annotation(output_path, text)

        self._log_screenshot(output_path)
        return output_path

    @staticmethod
    def _add_text_annotation(image_path: str, text: str) -> None:
        """在截图底部添加半透明文字条"""
        try:
            from PIL import Image, ImageDraw, ImageFont

            img = Image.open(image_path).convert("RGBA")
            overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)

            bar_h = 48
            y0 = img.height - bar_h
            for x in range(img.width):
                for y in range(y0, img.height):
                    ratio = (y - y0) / bar_h
                    alpha = int(120 + 60 * ratio)
                    overlay.putpixel((x, y), (0, 0, 0, alpha))

            try:
                font = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 16)
            except Exception:
                font = ImageFont.load_default()

            bbox = draw.textbbox((0, 0), text, font=font)
            tw = bbox[2] - bbox[0]
            tx = (img.width - tw) // 2
            ty = y0 + (bar_h - (bbox[3] - bbox[1])) // 2
            draw.text((tx, ty), text, fill=(255, 255, 255, 220), font=font)

            img = Image.alpha_composite(img, overlay)
            img = img.convert("RGB")
            img.save(image_path)
        except Exception:
            pass  # 标注失败不影响截图


# ── 便利函数 ──────────────────────────────────


def browser_screenshot(
    url: str,
    output_path: str,
    selector: str = None,
    width: int = 1280,
    height: int = 800,
) -> str:
    """一键网页截图"""
    with BrowserCapture() as bc:
        return bc.single(url, output_path, selector=selector, width=width, height=height)


def batch_screenshots(
    urls: list[str],
    output_dir: str,
    width: int = 1280,
    height: int = 800,
) -> list[str]:
    """一键批量截图"""
    with BrowserCapture() as bc:
        return bc.batch(urls, output_dir, width=width, height=height)


def file_screenshot(
    html_path: str,
    output_path: str,
    selector: str = None,
    width: int = 1280,
    height: int = 800,
) -> str:
    """一键本地 HTML 截图"""
    with BrowserCapture() as bc:
        return bc.file(html_path, output_path, selector=selector, width=width, height=height)


def annotated_screenshot(
    url: str,
    output_path: str,
    click: str = None,
    text: str = None,
    width: int = 1280,
    height: int = 800,
) -> str:
    """一键标注截图"""
    with BrowserCapture() as bc:
        return bc.annotate(url, output_path, click_selector=click, text=text, width=width, height=height)
