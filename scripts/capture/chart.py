"""Matplotlib 图表截图 — 子进程执行绘图代码并捕获输出

用于从 Python matplotlib 代码生成数据可视化图表。
字体回退链自动注入，中文/¥符号正确渲染。

用法:
    from capture.chart import ChartCapture, chart_screenshot

    chart_screenshot(\"""
    import matplotlib.pyplot as plt
    plt.bar(['A','B','C'], [1,2,3])
    plt.title('示例图表')
    \""", "chart.png")
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import textwrap
from pathlib import Path

from .fonts import FontManager, get_font_manager


class ChartCapture:
    """Matplotlib 图表渲染器（子进程执行）。

    不使用 Playwright/Pillow 渲染，而是启动子进程执行用户代码。
    自动注入 CJK 字体配置确保中文正确显示。

    支持 context manager 协议（与其他 Capture 类保持一致）:
        with ChartCapture() as cc:
            cc.render(code, "chart.png")
    """

    def __init__(self, font_manager: FontManager = None):
        self._fonts = font_manager

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    @property
    def fonts(self) -> FontManager:
        if self._fonts is None:
            self._fonts = get_font_manager()
        return self._fonts

    def render(
        self,
        code: str,
        output_path: str,
        width: int = 750,
        dpi: int = 150,
        theme_bg: str = "#1e1e2e",
    ) -> dict:
        """执行 matplotlib 绘图代码，保存图表为 PNG。

        Args:
            code: 包含 matplotlib 绘图的 Python 代码
            output_path: 输出 PNG 路径
            width: 图片宽度（像素）
            dpi: 分辨率
            theme_bg: 图表背景色

        Returns:
            dict: {"path": str, "error": str|None}
        """
        result = {"path": output_path, "error": None}

        # 构建注入字体配置的包装脚本
        cjk_path = self.fonts.cjk_path.replace("\\", "/")
        wrapper = textwrap.dedent(f"""
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.font_manager import FontProperties
        import os, warnings
        warnings.filterwarnings("ignore")

        # 字体配置
        FONT_PATH = r"{cjk_path}"
        FONT_PROP = FontProperties(fname=FONT_PATH)

        plt.rcParams["font.family"] = "sans-serif"
        plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "PingFang SC", "WenQuanYi Micro Hei"]
        plt.rcParams["axes.unicode_minus"] = False
        plt.rcParams["figure.facecolor"] = "{theme_bg}"
        plt.rcParams["axes.facecolor"] = "{theme_bg}"
        plt.rcParams["text.color"] = "#cdd6f4"
        plt.rcParams["axes.labelcolor"] = "#cdd6f4"
        plt.rcParams["xtick.color"] = "#6c7086"
        plt.rcParams["ytick.color"] = "#6c7086"
        plt.rcParams["axes.edgecolor"] = "#313244"

        # 计算 figsize
        figsize = ({width} / {dpi}, ({width} * 0.6) / {dpi})

        # 用户代码
        {textwrap.indent(code, "        ").strip()}

        # 保存
        out_dir = os.path.dirname(r"{output_path.replace(chr(92), '/')}")
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        plt.savefig(r"{output_path.replace(chr(92), '/')}", dpi={dpi},
                    bbox_inches="tight", facecolor="{theme_bg}")
        plt.close()
        """)

        fd, tmp_path = tempfile.mkstemp(suffix=".py")
        os.close(fd)
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write(wrapper)

            proc = subprocess.run(
                ["python3", tmp_path],
                capture_output=True, text=True, timeout=60,
            )
            if proc.returncode != 0:
                result["error"] = proc.stderr or proc.stdout
        except subprocess.TimeoutExpired:
            result["error"] = "图表生成超时"
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

        if not result["error"] and os.path.exists(output_path):
            try:
                size_kb = os.path.getsize(output_path) / 1024
                print(f"  [capture] → {output_path} ({size_kb:.0f} KB)")
            except Exception:
                print(f"  [capture] → {output_path}")
        else:
            print(f"  [capture] ⚠️ 图表可能未生成: {result.get('error', 'unknown')}")

        return result


# ── 便利函数 ──────────────────────────────────


def chart_screenshot(code: str, output: str, width: int = 750, dpi: int = 150) -> dict:
    """一键 matplotlib 图表截图"""
    return ChartCapture().render(code, output, width=width, dpi=dpi)
