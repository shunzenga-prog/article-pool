"""代码截图 + 终端输出 + 动画 — 基于 Pillow 的纯 Python 渲染

用法:
    from capture.code import CodeCapture, code_to_image

    # 代码截图
    code_to_image("print('hello')", "code.png", lang="python")

    # 执行代码并截取终端输出
    from capture.code import exec_to_image
    exec_to_image("print(1+1)", "output.png")

    # 代码逐行动画 GIF
    from capture.code import code_to_animation
    code_to_animation("for i in range(5):\n    print(i)", "anim.gif")
"""

from __future__ import annotations

import subprocess
import tempfile
import os
from dataclasses import dataclass
from pathlib import Path

from .base import BaseCapture

# ═══════════════════════════════════════════════
#  内部渲染函数（从 code_image_generator.py 抽取）
# ═══════════════════════════════════════════════


def _to_hex_color(raw) -> str:
    if not raw:
        return "#f8f8f2"
    c = str(raw).strip()
    if not c.startswith("#"):
        c = "#" + c
    if len(c) == 4:
        c = "#" + "".join(ch * 2 for ch in c[1:])
    return c


def _token_color(style_obj, ttype) -> str:
    s = style_obj.style_for_token(ttype)
    c = s.get("color") or ""
    if c:
        return _to_hex_color(c)
    parent = ttype.parent
    while parent:
        s = style_obj.style_for_token(parent)
        c = s.get("color") or ""
        if c:
            return _to_hex_color(c)
        parent = parent.parent
    return "#f8f8f2"


class CodeCapture(BaseCapture):
    """代码/终端/动画渲染器。

    所有渲染均为纯 Pillow，不需要浏览器。
    """

    def code_screenshot(
        self,
        code: str,
        output_path: str,
        language: str = "python",
        style: str = "monokai",
        font_size: int = 14,
        line_numbers: bool = True,
        width: int = 750,
    ) -> str:
        """Pygments 语法高亮代码截图。

        ASCII/Latin 使用等宽字体，CJK 使用回退字体。
        """
        from pygments import lex
        from pygments.lexers import get_lexer_by_name, PythonLexer
        from pygments.styles import get_style_by_name
        from PIL import Image, ImageDraw, ImageFont

        # 字体
        mono_path = self.fonts.mono_path or self.fonts.cjk_path
        cjk_path = self.fonts.cjk_path or mono_path

        mono_font = ImageFont.truetype(mono_path, font_size)
        cjk_font = ImageFont.truetype(cjk_path, font_size)

        space_bbox = mono_font.getbbox(" ")
        char_w = space_bbox[2] - space_bbox[0]
        if char_w <= 0:
            char_w = font_size // 2
        line_h = int(font_size * 1.6)
        padding = 16

        pyg_style = get_style_by_name(style)
        bg_color = _to_hex_color(pyg_style.background_color)

        try:
            lexer = get_lexer_by_name(language)
        except Exception:
            lexer = PythonLexer()

        char_color_pairs = []
        for ttype, text in lex(code, lexer):
            color = _token_color(pyg_style, ttype)
            for ch in text:
                char_color_pairs.append((ch, color))

        lines: list[list[tuple[str, str]]] = []
        current_line: list[tuple[str, str]] = []
        for ch, color in char_color_pairs:
            if ch == "\n":
                lines.append(current_line)
                current_line = []
            else:
                current_line.append((ch, color))
        if current_line or (code.endswith("\n") and not lines):
            lines.append(current_line)

        max_line_px = 0
        for line in lines:
            lw = sum(char_w * (2 if ord(ch) > 127 else 1) for ch, _ in line)
            max_line_px = max(max_line_px, lw)

        ln_width = (len(str(len(lines))) + 1) * char_w + 8 if line_numbers else 0
        content_right = padding + ln_width + max_line_px + padding
        img_w = max(width, content_right)
        img_h = max(30, len(lines) * line_h + padding * 2)

        img = Image.new("RGB", (img_w, img_h), bg_color)
        draw = ImageDraw.Draw(img)
        ln_color = "#90908a"
        ln_fmt_width = len(str(len(lines)))

        for i, line in enumerate(lines):
            y = padding + i * line_h
            if line_numbers:
                ln = str(i + 1).rjust(ln_fmt_width)
                draw.text((padding + 4, y), ln, fill=ln_color, font=mono_font)

            x = padding + ln_width
            for ch, color in line:
                if ord(ch) < 128:
                    font, cw = mono_font, char_w
                else:
                    font, cw = cjk_font, char_w * 2
                draw.text((x, y), ch, fill=color, font=font)
                x += cw

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        img.save(output_path)
        self._log_screenshot(output_path)
        return output_path

    def exec_and_capture(
        self,
        code: str,
        output_path: str,
        language: str = "python",
        timeout: int = 30,
        width: int = 750,
    ) -> dict:
        """执行代码并捕获输出，渲染为终端窗口截图。"""
        result = {
            "path": output_path, "stdout": "", "stderr": "",
            "returncode": -1, "timed_out": False,
        }

        if language == "python":
            fd, tmp_path = tempfile.mkstemp(suffix=".py")
            os.close(fd)
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write(code)
            try:
                proc = subprocess.run(
                    ["python3", tmp_path], capture_output=True, text=True, timeout=timeout
                )
                result["stdout"] = proc.stdout
                result["stderr"] = proc.stderr
                result["returncode"] = proc.returncode
            except subprocess.TimeoutExpired:
                result["stdout"] = "[执行超时]"
                result["timed_out"] = True
            finally:
                os.unlink(tmp_path)
        else:
            result["stdout"] = f"[不支持的语言: {language}]"

        output_text = result["stdout"]
        if result["stderr"]:
            output_text += "\n" + result["stderr"]

        self._render_terminal_pillow(output_text, output_path, width=width)
        return result

    def code_animation(
        self,
        code: str,
        output_path: str,
        language: str = "python",
        duration: float = 0.4,
        hold_frames: int = 15,
        font_size: int = 16,
        width: int = 700,
    ) -> str:
        """代码逐行出现的 GIF 动画。

        Args:
            duration: 每行之间的间隔秒数
            hold_frames: 最后帧保持的帧数
            font_size: 代码字体大小
            width: 图片宽度
        """
        from PIL import Image, ImageDraw, ImageFont
        import imageio

        mono_path = self.fonts.mono_path or self.fonts.cjk_path
        cjk_path = self.fonts.cjk_path or mono_path
        mono_font = ImageFont.truetype(mono_path, font_size)
        cjk_font = ImageFont.truetype(cjk_path, font_size)

        space_bbox = mono_font.getbbox(" ")
        char_w = space_bbox[2] - space_bbox[0]
        if char_w <= 0:
            char_w = font_size // 2
        line_h = int(font_size * 1.8)
        padding = 20

        code_lines = code.split("\n")
        frames = []
        fps = 10
        step_frames = max(1, int(duration * fps))

        for visible_count in range(1, len(code_lines) + 1):
            img_w = max(width, padding * 2 + 80 * char_w)
            img_h = len(code_lines) * line_h + padding * 2
            img = Image.new("RGB", (img_w, img_h), "#1e1e2e")
            draw = ImageDraw.Draw(img)

            for i in range(visible_count):
                line = code_lines[i]
                y = padding + i * line_h
                x = padding
                for ch in line:
                    if ord(ch) < 128:
                        font, cw = mono_font, char_w
                    else:
                        font, cw = cjk_font, char_w * 2
                    draw.text((x, y), ch, fill="#cdd6f4", font=font)
                    x += cw

                # 最后一行添加光标
                if i == visible_count - 1:
                    cursor_x = x
                    draw.rectangle(
                        [cursor_x, y + 2, cursor_x + char_w, y + line_h - 2],
                        fill="#f5e0dc",
                    )

            for _ in range(step_frames):
                frames.append(img.copy())

        # 保持最后一帧
        for _ in range(hold_frames):
            frames.append(frames[-1].copy())

        out_dir = os.path.dirname(output_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        imageio.mimsave(output_path, frames, duration=1 / fps, loop=0)
        self._log_screenshot(output_path)
        return output_path

    @staticmethod
    def _render_terminal_pillow(
        output_text: str,
        filepath: str,
        width: int = 750,
        font_size: int = 14,
        title: str = "terminal",
    ):
        """将文本渲染为带终端窗口装饰的 PNG（纯 Pillow）。"""
        from PIL import Image, ImageDraw, ImageFont

        lines = output_text.rstrip("\n").split("\n")
        if not lines:
            lines = ["(no output)"]

        try:
            mono_font = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", font_size)
        except Exception:
            try:
                mono_font = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", font_size
                )
            except Exception:
                mono_font = ImageFont.load_default()

        line_h = int(font_size * 1.8)
        padding = 16
        titlebar_h = 28
        max_chars = max(len(line) for line in lines)
        img_w = max(width, padding * 2 + max_chars * int(font_size * 0.62))
        img_h = titlebar_h + len(lines) * line_h + padding * 2

        img = Image.new("RGB", (img_w, img_h), "#1e1e2e")
        draw = ImageDraw.Draw(img)

        # 标题栏
        draw.rectangle([0, 0, img_w, titlebar_h], fill="#181825")
        # macOS 风格交通灯
        for cx, color in [(16, "#ff5f57"), (34, "#febc2e"), (52, "#28c840")]:
            draw.ellipse([cx - 6, 9, cx + 6, 21], fill=color)
        draw.text((70, 6), title, fill="#cdd6f4", font=mono_font)

        # 文本内容
        for i, line in enumerate(lines):
            y = titlebar_h + padding + i * line_h
            draw.text((padding, y), line, fill="#cdd6f4", font=mono_font)

        out_dir = os.path.dirname(filepath)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
        img.save(filepath)


# ── 便利函数 ──────────────────────────────────


def code_to_image(
    code: str,
    output: str,
    lang: str = "python",
    style: str = "monokai",
    font_size: int = 14,
) -> str:
    """一键代码截图"""
    with CodeCapture() as cc:
        return cc.code_screenshot(code, output, language=lang, style=style, font_size=font_size)


def exec_to_image(code: str, output: str, timeout: int = 30) -> dict:
    """一键执行代码并截取终端输出"""
    with CodeCapture() as cc:
        return cc.exec_and_capture(code, output, timeout=timeout)


def code_to_animation(code: str, output: str) -> str:
    """一键代码逐行动画"""
    with CodeCapture() as cc:
        return cc.code_animation(code, output)
