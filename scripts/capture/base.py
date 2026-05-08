"""BaseCapture — 共享的字体/Playwright/临时文件生命周期

所有截图模块（TerminalCapture, BrowserCapture, CodeCapture, FlowchartCapture）继承此类，
自动获取:
  - 统一的 CJK 字体检测
  - 单例 Playwright 浏览器（多次截图复用）
  - 临时文件自动追踪与清理
  - 主题/颜色令牌

用法:
    from capture.base import BaseCapture
    from capture.themes import ThemeRegistry

    with BaseCapture(theme="ocean") as cap:
        page = cap.browser_page()
        page.goto("https://example.com")
        page.screenshot(path="output.png")
    # 退出 with 块时自动清理临时文件和关闭浏览器
"""

from __future__ import annotations

import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

from .fonts import FontManager, get_font_manager
from .themes import ColorTokens, ThemeRegistry


class BaseCapture:
    """截图基类 — 提供 Playwright、字体、主题、临时文件的统一管理。

    支持上下文管理器协议:
        with BaseCapture() as cap:
            ...

    退出时自动:
      - 关闭 Playwright 浏览器
      - 清理所有追踪的临时文件
    """

    def __init__(
        self,
        theme: str = "catppuccin-mocha",
        viewport: tuple[int, int] = (1280, 800),
        device_scale: float = 2.0,
        headless: bool = True,
    ):
        self._font_manager: Optional[FontManager] = None
        self._playwright = None
        self._browser = None
        self._theme_name = theme
        self._theme: Optional[ColorTokens] = None
        self.viewport = viewport
        self.device_scale = device_scale
        self.headless = headless
        self._temp_files: list[str] = []

    # ── 属性 ──────────────────────────────────

    @property
    def fonts(self) -> FontManager:
        if self._font_manager is None:
            self._font_manager = get_font_manager()
        return self._font_manager

    @property
    def theme(self) -> ColorTokens:
        if self._theme is None:
            self._theme = ThemeRegistry.get(self._theme_name)
        return self._theme

    def set_theme(self, name: str) -> None:
        """切换主题"""
        self._theme_name = name
        self._theme = ThemeRegistry.get(name)

    # ── Playwright 管理 ────────────────────────

    @contextmanager
    def browser_page(self, width: int = None, height: int = None):
        """获取 Playwright page 的上下文管理器。

        浏览器按需启动（懒加载），多次调用复用同一实例。
        退出 page 上下文时关闭 page，但保留浏览器。
        """
        if self._playwright is None:
            from playwright.sync_api import sync_playwright

            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(headless=self.headless)

        vw, vh = width or self.viewport[0], height or self.viewport[1]
        page = self._browser.new_page(viewport={"width": vw, "height": vh})
        try:
            yield page
        finally:
            try:
                page.close()
            except Exception:
                pass

    def screenshot_element(
        self, page, selector: str, output_path: str
    ) -> str:
        """截图指定元素（等待 selector 出现后截图）"""
        page.wait_for_selector(selector, timeout=15000)
        page.wait_for_timeout(300)
        el = page.query_selector(selector)
        if el:
            el.screenshot(path=output_path)
        else:
            page.screenshot(path=output_path, full_page=True)
        self._log_screenshot(output_path)
        return output_path

    def screenshot_full_page(self, page, output_path: str) -> str:
        """全页截图"""
        page.screenshot(path=output_path, full_page=True)
        self._log_screenshot(output_path)
        return output_path

    # ── 临时文件管理 ────────────────────────────

    def temp_html(self, html: str) -> str:
        """将 HTML 写入临时文件，返回文件路径"""
        fd, path = tempfile.mkstemp(suffix=".html", prefix="capture_")
        os.close(fd)
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        self._temp_files.append(path)
        return path

    def file_url(self, file_path: str) -> str:
        """将本地文件路径转为 file:// URL (Playwright 兼容)"""
        abs_path = os.path.abspath(file_path)
        return f"file:///{abs_path.replace(os.sep, '/')}"

    def navigate_and_wait(self, page, url: str, timeout: int = 60000) -> None:
        """导航到 URL 并等待网络空闲"""
        page.goto(url, wait_until="networkidle", timeout=timeout)

    # ── 清理 ──────────────────────────────────

    def cleanup(self) -> None:
        """清理所有临时文件和浏览器"""
        for fp in self._temp_files:
            try:
                if os.path.exists(fp):
                    os.unlink(fp)
            except Exception:
                pass
        self._temp_files.clear()

        if self._browser:
            try:
                self._browser.close()
            except Exception:
                pass
            self._browser = None

        if self._playwright:
            try:
                self._playwright.stop()
            except Exception:
                pass
            self._playwright = None

    # ── 上下文管理器 ────────────────────────────

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.cleanup()

    # ── 工具方法 ──────────────────────────────

    @staticmethod
    def _log_screenshot(output_path: str) -> None:
        """打印截图完成信息"""
        try:
            size_kb = os.path.getsize(output_path) / 1024
            print(f"  [capture] → {output_path} ({size_kb:.0f} KB)")
        except Exception:
            print(f"  [capture] → {output_path}")
