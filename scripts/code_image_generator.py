#!/usr/bin/env python3
"""
代码图片生成器 - 为微信公众号文章生成代码截图、执行结果、图表和动画

核心能力:
  1. code_screenshot()    - Pygments 语法高亮代码截图
  2. exec_and_capture()   - 执行代码并渲染终端输出为截图
  3. chart_screenshot()   - Matplotlib 图表渲染
  4. code_animation()     - 代码逐行出现的 GIF 动画
  5. process_article()    - 扫描文章中的代码块，自动生成配图

环境要求:
  - Python >= 3.10
  - 系统必须安装 CJK 中文字体（Linux: DroidSansFallbackFull / NotoSansCJK; Windows: 微软雅黑/宋体）
  - pip install pillow pygments matplotlib imageio numpy (通常已预装)

用法:
  python code_image_generator.py process article.md -o images/ --execute --animate
"""

import subprocess
import tempfile
import textwrap
import os, io, re, shutil, sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

# ============================================================
# Pillow 兼容补丁 (Pillow 12+ 移除 getsize)
# ============================================================
from PIL import ImageFont as _IF

if not hasattr(_IF.FreeTypeFont, "getsize"):

    def _patch_getsize(self, text, *a, **kw):
        b = self.getbbox(text, *a, **kw)
        return (b[2] - b[0], b[3] - b[1]) if b else (0, 0)

    _IF.FreeTypeFont.getsize = _patch_getsize
    _IF.ImageFont.getsize = _patch_getsize


# ============================================================
# ⚠️ CJK 字体配置（中文支持 — 必须项）
# 如果字体未正确配置，生成的图片中中文将显示为方框或乱码。
# 系统必须至少有 DroidSansFallbackFull 或任意 CJK 字体。
# ============================================================
CJK_MONO_PATHS = [
    # Project merged font (ASCII + CJK in one font, for matplotlib charts)
    os.path.join(os.path.dirname(__file__), "..", "fonts", "DroidSansCJK.ttf"),
    # Also check relative to code location
    "/sessions/dazzling-jolly-fermi/mnt/微信公众号/工作流/article-pool/fonts/DroidSansCJK.ttf",
    # Linux: CJK 等宽字体（最佳）
    "/usr/share/fonts/truetype/noto/NotoSansMonoCJKsc-Regular.otf",
    "/usr/share/fonts/opentype/noto/NotoSansMonoCJKsc-Regular.otf",
    # Linux: CJK 回退字体（非等宽，但支持中文）
    "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    # Windows: CJK 字体
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/simsun.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    "C:/Windows/Fonts/Deng.ttf",
    # Windows: 等宽西文字体（无 CJK，最后回退）
    "C:/Windows/Fonts/consola.ttf",
    "C:/Windows/Fonts/CascadiaCode.ttf",
    # Linux: 等宽西文字体（无 CJK，最后回退）
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
]

_CJK_FONT_PATH = None


def _detect_cjk_font() -> str:
    """探测第一个可用的 CJK 字体路径"""
    global _CJK_FONT_PATH
    if _CJK_FONT_PATH:
        return _CJK_FONT_PATH
    for fp in CJK_MONO_PATHS:
        if os.path.exists(fp):
            _CJK_FONT_PATH = fp
            return fp
    return ""


def _find_font(size: int = 16):
    """获取当前最佳字体（优先 CJK）"""
    from PIL import ImageFont

    path = _detect_cjk_font()
    if path:
        return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _find_mono_font(size: int = 16):
    """获取等宽字体（用于终端输出、动画等需要对齐的场景）"""
    from PIL import ImageFont

    for fp in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
        "C:/Windows/Fonts/consola.ttf",
        "C:/Windows/Fonts/CascadiaCode.ttf",
    ]:
        if os.path.exists(fp):
            return ImageFont.truetype(fp, size)
    return ImageFont.load_default()


def _get_font_path() -> str:
    """返回当前最佳字体路径"""
    return _detect_cjk_font() or ""


# 注意: Pygments 字体补丁已移除。
# 旧版使用 Pygments ImageFormatter 时需要通过劫持 PIL.ImageFont.truetype()
# 来注入 CJK 字体。但新版的 code_screenshot() 已改为自主 Pillow 渲染,
# 自行管理 ASCII/CJK 双字体，不再依赖 ImageFormatter，补丁反而会干扰。
# 其他函数 (exec_and_capture, chart_screenshot, code_animation) 也都
# 使用各自的字体配置，不需要全局劫持。


# ============================================================
# 主题配置
# ============================================================
@dataclass
class Theme:
    name: str
    bg: str = "#1e1e2e"
    titlebar_bg: str = "#181825"
    text: str = "#cdd6f4"
    line_num: str = "#6c7086"
    line_num_dim: str = "#313244"
    highlight_line: str = "#313244"
    border: str = "#313244"
    keyword: str = "#89b4fa"
    string: str = "#a6e3a1"
    comment: str = "#6c7086"
    func: str = "#cba6f7"
    error: str = "#f38ba8"
    warning: str = "#f9e2af"


CATPPUCCIN = Theme("catppuccin")
GITHUB_DARK = Theme(
    "github-dark",
    bg="#0d1117",
    titlebar_bg="#161b22",
    text="#e6edf3",
    line_num="#484f58",
    line_num_dim="#21262d",
    highlight_line="#1f2429",
    keyword="#79c0ff",
    string="#a5d6ff",
    comment="#8b949e",
    func="#d2a8ff",
    error="#f85149",
    warning="#d29922",
)


# ============================================================
# 能力1: 代码截图
# ============================================================
def _to_hex_color(raw: str) -> str:
    """将 Pygments 颜色值标准化为 PIL 可用的 #RRGGBB 格式"""
    if not raw:
        return "#f8f8f2"
    c = str(raw).strip()
    if not c.startswith("#"):
        c = "#" + c
    if len(c) == 4:  # #RGB → #RRGGBB
        c = "#" + "".join(ch * 2 for ch in c[1:])
    return c


def _token_color(style_obj, ttype) -> str:
    """沿 token 层级向上查找颜色，返回标准化 hex"""
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


def code_screenshot(
    code: str,
    output_path: str,
    language: str = "python",
    style: str = "monokai",
    font_size: int = 14,
    line_numbers: bool = True,
    width: int = 750,
) -> str:
    """使用自主 Pillow 渲染器生成语法高亮代码截图。

    ASCII/Latin 用等宽字体(DejaVuSansMono)，CJK 用回退字体(DroidSansFallbackFull)。
    解决了 Pygments ImageFormatter 强制使用非等宽 CJK 字体导致渲染异常的问题。
    """
    from pygments import lex
    from pygments.lexers import get_lexer_by_name, PythonLexer
    from pygments.styles import get_style_by_name
    from PIL import Image, ImageDraw, ImageFont

    # --- 字体 ---
    mono_path = ""
    for fp in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
        "C:/Windows/Fonts/consola.ttf",
    ]:
        if os.path.exists(fp):
            mono_path = fp
            break
    if not mono_path:
        mono_path = _get_font_path()

    cjk_path = _get_font_path()
    if not cjk_path:
        cjk_path = mono_path

    mono_font = ImageFont.truetype(mono_path, font_size)
    cjk_font = ImageFont.truetype(cjk_path, font_size)

    # --- 等宽度量 ---
    space_bbox = mono_font.getbbox(" ")
    char_w = space_bbox[2] - space_bbox[0]
    if char_w <= 0:
        char_w = font_size // 2
    line_h = int(font_size * 1.6)
    padding = 16

    # --- Pygments 样式 ---
    pyg_style = get_style_by_name(style)
    bg_color = _to_hex_color(pyg_style.background_color)

    # --- 词法分析 ---
    try:
        lexer = get_lexer_by_name(language)
    except Exception:
        lexer = PythonLexer()

    char_color_pairs = []
    for ttype, text in lex(code, lexer):
        color = _token_color(pyg_style, ttype)
        for ch in text:
            char_color_pairs.append((ch, color))

    # 按换行拆分
    lines = []
    current_line = []
    for ch, color in char_color_pairs:
        if ch == "\n":
            lines.append(current_line)
            current_line = []
        else:
            current_line.append((ch, color))
    if current_line or (code.endswith("\n") and not lines):
        lines.append(current_line)

    # 计算尺寸
    max_line_px = 0
    for line in lines:
        lw = sum(char_w * (2 if ord(ch) > 127 else 1) for ch, _ in line)
        max_line_px = max(max_line_px, lw)

    ln_width = (len(str(len(lines))) + 1) * char_w + 8 if line_numbers else 0
    content_right = padding + ln_width + max_line_px + padding
    img_w = max(width, content_right)
    img_h = max(30, len(lines) * line_h + padding * 2)

    # --- 渲染 ---
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
                font = mono_font
                cw = char_w
            else:
                font = cjk_font
                cw = char_w * 2
            draw.text((x, y), ch, fill=color, font=font)
            x += cw

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    img.save(output_path)
    return output_path


# ============================================================
# 能力2: 代码执行 + 终端截图
# ============================================================
def exec_and_capture(
    code: str,
    output_path: str,
    language: str = "python",
    timeout: int = 30,
    theme: Theme = CATPPUCCIN,
    width: int = 750,
) -> dict:
    """执行代码并捕获输出，渲染为模拟终端窗口的截图。"""
    result = {
        "path": output_path, "stdout": "", "stderr": "",
        "returncode": -1, "timed_out": False,
    }

    if language == "python":
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp:
            tmp.write(code)
            tmp_path = tmp.name
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

    output = result["stdout"]
    if result["stderr"]:
        output += "\n" + result["stderr"]

    _render_terminal(output, output_path, theme=theme, width=width)
    return result


def _render_terminal(
    output_text: str,
    filepath: str,
    theme: Theme = CATPPUCCIN,
    width: int = 750,
    font_size: int = 14,
    title: str = "terminal",
):
    """将文本渲染为带终端窗口装饰的 PNG 截图"""
    from PIL import Image, ImageDraw

    mono_font = _find_mono_font(font_size)
    cjk_font = _find_font(font_size)
    title_font = _find_mono_font(12)
    line_height = int(font_size * 1.45)
    padding = 18
    title_height = 30
    char_w = mono_font.getbbox(" ")[2] or font_size // 2

    lines = output_text.split("\n")
    display_lines = []
    for line in lines:
        display_lines.append(line)

    content_height = max(len(display_lines) * line_height + padding * 2, 40)
    total_height = title_height + content_height

    img = Image.new("RGB", (width, total_height), theme.bg)
    draw = ImageDraw.Draw(img)

    # 标题栏
    draw.rectangle([(0, 0), (width, title_height)], fill=theme.titlebar_bg)
    for x, color in [(14, "#f38ba8"), (32, "#f9e2af"), (50, "#a6e3a1")]:
        draw.ellipse([x, 9, x + 11, 20], fill=color)
    draw.text((width // 2, 6), title, fill=theme.line_num, font=title_font, anchor="mt")

    # 内容
    y = title_height + padding
    for i, line in enumerate(display_lines):
        if not line.strip() and i >= len(display_lines) - 1:
            break
        ln = f"{i+1:3d} "
        draw.text((padding, y), ln, fill=theme.line_num, font=mono_font)

        # 逐字符渲染，ASCII 用等宽字体，CJK 用回退字体
        x = padding + 38
        for ch in line:
            if ord(ch) < 128:
                font = mono_font
                cw = char_w
            else:
                font = cjk_font
                cw = char_w * 2
            draw.text((x, y), ch, fill=theme.text, font=font)
            x += cw
        y += line_height

    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    img.save(filepath)


# ============================================================
# 能力3: Matplotlib 图表渲染
# ============================================================
def chart_screenshot(
    code: str, output_path: str,
    width: int = 750, dpi: int = 150,
    theme: Theme = CATPPUCCIN,
) -> dict:
    """执行 Matplotlib 绘图代码并渲染为 PNG。"""
    import matplotlib
    matplotlib.use("Agg")

    cjk_path = _get_font_path()
    result = {"path": output_path, "stdout": "", "error": ""}

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp:
        # 在子进程中注入 CJK 字体配置（因为子进程有独立的 matplotlib 环境）
        cjk_setup = ""
        if cjk_path:
            is_merged = "DroidSansCJK" in cjk_path
            if is_merged:
                cjk_setup = f"""
# CJK+ASCII merged font (injected by code_image_generator)
import matplotlib
matplotlib.use('Agg')
from matplotlib import font_manager as _fm
_fm.fontManager.addfont('{cjk_path}')
_prop = _fm.FontProperties(fname='{cjk_path}')
_font_name = _prop.get_name()
import matplotlib.pyplot as plt
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = [_font_name]
plt.rcParams['axes.unicode_minus'] = False
"""
            else:
                cjk_setup = f"""
# CJK font setup (injected by code_image_generator)
import matplotlib
matplotlib.use('Agg')
from matplotlib import font_manager as _fm
_fm.fontManager.addfont('{cjk_path}')
_prop = _fm.FontProperties(fname='{cjk_path}')
_font_name = _prop.get_name()
import matplotlib.pyplot as plt
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = [_font_name, 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
"""


        wrapped = f"""import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
{cjk_setup}
try:
    plt.style.use('dark_background')
except Exception:
    pass

{code}

if plt.get_fignums():
    # Note: We do NOT use tight_layout or bbox_inches='tight' with CJK merged fonts.
    # CJK characters have wider metrics that cause tight_layout to fail and
    # bbox_inches='tight' to incorrectly inflate the output size.
    # matplotlib's default margins (left=12.5%, right=10%, top=12%, bottom=11%)
    # work correctly with the merged font.
    plt.savefig('{output_path}', dpi={dpi}, facecolor='{theme.bg}')
"""
        tmp.write(wrapped)
        tmp_path = tmp.name

    try:
        proc = subprocess.run(
            ["python3", tmp_path], capture_output=True, text=True, timeout=60,
            env={**os.environ, "MPLBACKEND": "Agg"},
        )
        result["stdout"] = proc.stdout
        result["error"] = proc.stderr
    except subprocess.TimeoutExpired:
        result["error"] = "图表渲染超时"
    finally:
        os.unlink(tmp_path)
        import matplotlib.pyplot as _plt
        _plt.close("all")

    return result


# ============================================================
# 能力4: 代码逐行动画 GIF
# ============================================================
def code_animation(
    code: str, output_path: str,
    language: str = "python",
    duration: float = 0.4,
    hold_frames: int = 15,
    theme: Theme = CATPPUCCIN,
    font_size: int = 16,
    width: int = 700,
) -> str:
    """将代码渲染为逐行出现的 GIF 动画。"""
    import imageio
    from PIL import Image, ImageDraw

    lines = code.rstrip().split("\n")
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()

    if not lines:
        lines = ["# (empty)"]

    mono_font = _find_mono_font(font_size)
    cjk_font = _find_font(font_size)
    line_height = int(font_size * 1.6)
    padding = 18
    height = len(lines) * line_height + padding * 2 + 40
    char_w = mono_font.getbbox(" ")[2] or font_size // 2
    frames = []

    for step in range(1, len(lines) + 1):
        img = Image.new("RGB", (width, height), theme.bg)
        draw = ImageDraw.Draw(img)
        draw.text((padding, 10), f"[{language}]", fill=theme.line_num, font=mono_font)
        draw.line([(padding, 34), (width - padding, 34)], fill=theme.border, width=1)

        y = 42
        for i, line_text in enumerate(lines):
            if i < step:
                color = _syntax_color(line_text.strip(), theme)
                if i == step - 1:
                    draw.rectangle(
                        [(padding - 4, y - 1), (width - padding + 4, y + line_height - 2)],
                        fill=theme.highlight_line,
                    )
                ln = f"{i+1:2d}"
                draw.text((padding + 4, y), ln, fill=theme.line_num, font=mono_font)
                # 逐字符渲染，ASCII 用等宽，CJK 用回退
                x = padding + 34
                for ch in line_text:
                    if ord(ch) < 128:
                        font = mono_font
                        cw = char_w
                    else:
                        font = cjk_font
                        cw = char_w * 2
                    draw.text((x, y), ch, fill=color, font=font)
                    x += cw
            else:
                ln = f"{i+1:2d}"
                draw.text((padding + 4, y), ln, fill=theme.line_num_dim, font=mono_font)
                x = padding + 34
                for ch in line_text:
                    if ord(ch) < 128:
                        font = mono_font
                        cw = char_w
                    else:
                        font = cjk_font
                        cw = char_w * 2
                    draw.text((x, y), ch, fill=theme.line_num_dim, font=font)
                    x += cw
            y += line_height

        frames.append(img)

    for _ in range(hold_frames):
        frames.append(frames[-1].copy())

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    imageio.mimsave(output_path, frames, duration=duration, loop=0)
    return output_path


def _syntax_color(line: str, theme: Theme) -> str:
    """简单的伪语法高亮"""
    s = line.strip()
    if s.startswith(("def ", "class ", "async def ")):
        return theme.keyword
    if s.startswith(("import ", "from ")):
        return theme.func
    if s.startswith(("#", "//", "/*", "<!--")):
        return theme.comment
    if s.startswith(('"""', "'''")) or s.endswith(('"""', "'''")):
        return theme.comment
    if any(kw in s for kw in ["return ", "yield ", "raise ", "pass", "break"]):
        return theme.error
    if any(kw in s for kw in ["if ", "elif ", "else:", "for ", "while "]):
        return theme.func
    if any(kw in s for kw in ["print(", "input("]):
        return theme.string
    return theme.text


# ============================================================
# 能力5: 文章批量处理
# ============================================================
@dataclass
class ArticleImageResult:
    article_path: str
    images: list = field(default_factory=list)
    errors: list = field(default_factory=list)


def process_article(
    md_path: str, output_dir: str,
    execute_code: bool = False,
    generate_animations: bool = False,
) -> ArticleImageResult:
    """
    扫描 Markdown 文章中的代码块和图表标记，自动生成配图。

    代码块标记:
      ```python          → 代码截图
      ```python exec     → 执行代码 + 终端截图
      ```python chart    → Matplotlib 图表
      ```python anim     → 代码逐行动画 GIF

    Args:
        md_path: Markdown 文章路径
        output_dir: 图片输出目录
        execute_code: 是否执行代码块（安全考量，默认关闭）
        generate_animations: 是否生成 GIF（较耗时，默认关闭）

    Returns:
        ArticleImageResult
    """
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    os.makedirs(output_dir, exist_ok=True)
    result = ArticleImageResult(article_path=md_path)

    pattern = re.compile(r"```(\w+)(?:\s+(\w+))?\s*\n(.*?)```", re.DOTALL)
    basename = Path(md_path).stem

    for idx, match in enumerate(pattern.finditer(content)):
        lang = match.group(1)
        tag = match.group(2) or ""
        code = match.group(3)

        if not code.strip():
            continue

        img_path = os.path.join(output_dir, f"{basename}_code{idx+1:02d}.png")
        gif_path = os.path.join(output_dir, f"{basename}_code{idx+1:02d}.gif")

        try:
            if tag == "anim":
                if generate_animations:
                    code_animation(code, gif_path, language=lang)
                    result.images.append(("animation", gif_path))
                else:
                    code_screenshot(code, img_path, language=lang)
                    result.images.append(("code", img_path))
            elif tag == "chart":
                if execute_code:
                    chart_screenshot(code, img_path)
                    result.images.append(("chart", img_path))
            elif tag == "exec":
                if execute_code:
                    exec_and_capture(code, img_path, language=lang)
                    result.images.append(("terminal", img_path))
            else:
                code_screenshot(code, img_path, language=lang)
                result.images.append(("code", img_path))
        except Exception as e:
            result.errors.append(f"代码块 #{idx+1}: {e}")

    return result


# ============================================================
# CLI 入口
# ============================================================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="代码图片生成器")
    subparsers = parser.add_subparsers(dest="command")

    # code
    p = subparsers.add_parser("code", help="生成代码截图")
    p.add_argument("input", help="代码文件路径")
    p.add_argument("-o", "--output", required=True, help="输出 PNG 路径")
    p.add_argument("-l", "--language", default="python")
    p.add_argument("-s", "--style", default="monokai")

    # exec
    p = subparsers.add_parser("exec", help="执行代码并截图")
    p.add_argument("input", help="代码文件路径")
    p.add_argument("-o", "--output", required=True, help="输出 PNG 路径")

    # chart
    p = subparsers.add_parser("chart", help="Matplotlib 图表渲染")
    p.add_argument("input", help="绘图代码文件路径")
    p.add_argument("-o", "--output", required=True, help="输出 PNG 路径")

    # anim
    p = subparsers.add_parser("anim", help="生成代码动画 GIF")
    p.add_argument("input", help="代码文件路径")
    p.add_argument("-o", "--output", required=True, help="输出 GIF 路径")

    # process
    p = subparsers.add_parser("process", help="批量处理文章")
    p.add_argument("input", help="Markdown 文件路径")
    p.add_argument("-o", "--output-dir", required=True, help="图片输出目录")
    p.add_argument("--execute", action="store_true", help="允许执行代码")
    p.add_argument("--animate", action="store_true", help="生成 GIF 动画")

    args = parser.parse_args()

    if args.command == "code":
        with open(args.input, "r") as f:
            code = f.read()
        path = code_screenshot(code, args.output, language=args.language, style=args.style)
        print(f"OK code: {path}")

    elif args.command == "exec":
        with open(args.input, "r") as f:
            code = f.read()
        r = exec_and_capture(code, args.output)
        print(f"OK exec: {r['path']}")
        if r["returncode"] != 0:
            print(f"  exit={r['returncode']}")

    elif args.command == "chart":
        with open(args.input, "r") as f:
            code = f.read()
        r = chart_screenshot(code, args.output)
        print(f"OK chart: {r['path']}")
        if r["error"]:
            print(f"  stderr: {r['error'][:200]}")

    elif args.command == "anim":
        with open(args.input, "r") as f:
            code = f.read()
        path = code_animation(code, args.output)
        print(f"OK anim: {path}")

    elif args.command == "process":
        r = process_article(
            args.input, args.output_dir,
            execute_code=args.execute, generate_animations=args.animate,
        )
        print(f"OK: {len(r.images)} images")
        for typ, path in r.images:
            print(f"  [{typ}] {os.path.basename(path)} ({os.path.getsize(path)//1024}KB)")
        if r.errors:
            print(f"ERRORS ({len(r.errors)}):")
            for e in r.errors:
                print(f"  - {e}")

    else:
        parser.print_help()
