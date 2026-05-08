"""CJK 字体检测 — 单一真相源

为所有截图/封面/渲染模块提供统一的字体回退链和 CJK 文本测量工具。
Windows / macOS / Linux 自动适配，无需手动配置。

用法:
    from capture.fonts import FontManager
    fm = FontManager()
    # PIL 字体
    cjk = fm.cjk_pil(16)      # CJK 字体
    mono = fm.mono_pil(14)     # 等宽字体（无 CJK）
    lat = fm.latin_pil(14)     # 西文无衬线
    latb = fm.latin_pil(14, bold=True)  # 加粗西文
    # 路径
    print(fm.cjk_path)         # 字体文件路径
    # 文本工具
    from capture.fonts import is_cjk, draw_mixed_text
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

# Pillow 兼容补丁 (Pillow 12+)
from PIL import ImageFont as _IF

if not hasattr(_IF.FreeTypeFont, "getsize"):

    def _patch_getsize(self, text, *a, **kw):
        b = self.getbbox(text, *a, **kw)
        return (b[2] - b[0], b[3] - b[1]) if b else (0, 0)

    _IF.FreeTypeFont.getsize = _patch_getsize  # type: ignore[attr-defined]
    _IF.ImageFont.getsize = _patch_getsize  # type: ignore[attr-defined]

# ═══════════════════════════════════════════════
#  CJK 字符判断
# ═══════════════════════════════════════════════


def is_cjk(codepoint: int) -> bool:
    """判断 Unicode 码点是否属于 CJK 区块"""
    return (
        0x4E00 <= codepoint <= 0x9FFF  # CJK Unified
        or 0x3400 <= codepoint <= 0x4DBF  # CJK Extension A
        or 0xF900 <= codepoint <= 0xFAFF  # CJK Compatibility
        or 0x3000 <= codepoint <= 0x303F  # CJK Symbols/Punctuation
        or 0xFF00 <= codepoint <= 0xFFEF  # Half/Fullwidth
        or 0x2000 <= codepoint <= 0x206F  # General Punctuation
    )


# ═══════════════════════════════════════════════
#  字体候选路径（按平台组织）
# ═══════════════════════════════════════════════

_CJK_CANDIDATES = [
    # Project merged font (ASCII + CJK in one, for matplotlib charts)
    lambda: str(
        Path(__file__).resolve().parent.parent / "fonts" / "DroidSansCJK.ttf"
    ),
    # Linux
    "/usr/share/fonts/truetype/noto/NotoSansMonoCJKsc-Regular.otf",
    "/usr/share/fonts/opentype/noto/NotoSansMonoCJKsc-Regular.otf",
    "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    # macOS
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    # Windows
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/simsun.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    "C:/Windows/Fonts/Deng.ttf",
]

_LAT_CANDIDATES = [
    "C:/Windows/Fonts/segoeui.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
]

_LATB_CANDIDATES = [
    "C:/Windows/Fonts/segoeuib.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
]

_MONO_CANDIDATES = [
    "C:/Windows/Fonts/consola.ttf",
    "C:/Windows/Fonts/CascadiaCode.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
]


def _resolve(path_or_lambda) -> str:
    """解析候选路径：支持字符串和 lambda"""
    if callable(path_or_lambda):
        try:
            val = path_or_lambda()
        except Exception:
            return ""
        return str(val) if isinstance(val, (str, os.PathLike)) else ""
    return str(path_or_lambda) if path_or_lambda else ""


def _find_first(candidates: list) -> str:
    """返回第一个存在的字体路径"""
    for c in candidates:
        p = _resolve(c)
        if p and os.path.exists(p):
            return p
    return ""


class FontManager:
    """统一的 CJK/等宽/西文 字体管理器。

    单次实例化、懒加载、全平台的字体回退链。
    """

    def __init__(self, project_root: Optional[Path] = None):
        self._cjk_path: Optional[str] = None
        self._mono_path: Optional[str] = None
        self._latin_path: Optional[str] = None
        self._latinb_path: Optional[str] = None
        self._cache: dict[tuple, _IF.FreeTypeFont] = {}

    # ── 路径属性 ──────────────────────────────

    @property
    def cjk_path(self) -> str:
        if self._cjk_path is None:
            self._cjk_path = _find_first(_CJK_CANDIDATES)
        return self._cjk_path

    @property
    def mono_path(self) -> str:
        if self._mono_path is None:
            self._mono_path = _find_first(_MONO_CANDIDATES) or self.cjk_path
        return self._mono_path

    @property
    def latin_path(self) -> str:
        if self._latin_path is None:
            self._latin_path = _find_first(_LAT_CANDIDATES)
        return self._latin_path

    @property
    def latinb_path(self) -> str:
        if self._latinb_path is None:
            self._latinb_path = _find_first(_LATB_CANDIDATES) or self.latin_path
        return self._latinb_path

    # ── PIL 字体 ──────────────────────────────

    def cjk_pil(self, size: int = 16) -> _IF.FreeTypeFont:
        key = ("cjk", size)
        if key not in self._cache:
            if self.cjk_path:
                self._cache[key] = _IF.truetype(self.cjk_path, size)
            else:
                self._cache[key] = _IF.load_default()
        return self._cache[key]

    def mono_pil(self, size: int = 14) -> _IF.FreeTypeFont:
        key = ("mono", size)
        if key not in self._cache:
            if self.mono_path:
                self._cache[key] = _IF.truetype(self.mono_path, size)
            else:
                self._cache[key] = _IF.load_default()
        return self._cache[key]

    def latin_pil(self, size: int = 14, bold: bool = False) -> _IF.FreeTypeFont:
        bt = "bold" if bold else "regular"
        key = ("latin", size, bt)
        if key not in self._cache:
            path = self.latinb_path if bold else self.latin_path
            if path:
                self._cache[key] = _IF.truetype(path, size)
            else:
                self._cache[key] = _IF.load_default()
        return self._cache[key]

    # ── 工具 ──────────────────────────────────

    @property
    def has_cjk(self) -> bool:
        return bool(self.cjk_path)

    def cjk_ascent_delta(self) -> int:
        """CJK 字体相对于拉丁字体的 ascent 偏移（用于混合排版对齐）"""
        try:
            cjk_ascent, _ = self.cjk_pil(16).getmetrics()
            lat_ascent, _ = self.latin_pil(16).getmetrics()
            return cjk_ascent - lat_ascent
        except Exception:
            return 0


# ═══════════════════════════════════════════════
#  混合 CJK/Latin 文本排版工具
# ═══════════════════════════════════════════════


def measure_mixed_text_width(
    text: str, cjk_font: _IF.FreeTypeFont, latin_font: _IF.FreeTypeFont
) -> int:
    """测量混合 CJK/Latin 文本的像素宽度（逐字分字体）"""
    from PIL import Image, ImageDraw

    dummy = Image.new("RGB", (1, 1))
    draw = ImageDraw.Draw(dummy)
    total = 0
    i = 0
    while i < len(text):
        use_cjk = is_cjk(ord(text[i]))
        j = i + 1
        while j < len(text) and is_cjk(ord(text[j])) == use_cjk:
            j += 1
        seg = text[i:j]
        font = cjk_font if use_cjk else latin_font
        bbox = draw.textbbox((0, 0), seg, font=font)
        total += bbox[2] - bbox[0] + 1  # +1 inter-segment gap
        i = j
    return total


def draw_mixed_text(
    draw,
    xy: tuple[int, int],
    text: str,
    fill,
    cjk_font: _IF.FreeTypeFont,
    latin_font: _IF.FreeTypeFont,
) -> None:
    """在混合 CJK/Latin 文本上逐段绘制，自动对齐基线"""
    x, y = xy
    cjk_ascent, _ = cjk_font.getmetrics()
    lat_ascent, _ = latin_font.getmetrics()
    ascent_delta = cjk_ascent - lat_ascent
    i = 0
    while i < len(text):
        use_cjk = is_cjk(ord(text[i]))
        j = i + 1
        while j < len(text) and is_cjk(ord(text[j])) == use_cjk:
            j += 1
        seg = text[i:j]
        font = cjk_font if use_cjk else latin_font
        adj_y = y - ascent_delta if use_cjk else y
        draw.text((x, adj_y), seg, fill=fill, font=font)
        bbox = draw.textbbox((x, adj_y), seg, font=font)
        x = bbox[2] + 1
        i = j


# ── 模块级单例（向后兼容旧代码的全局变量用法） ──


_default_fm: Optional[FontManager] = None


def get_font_manager() -> FontManager:
    global _default_fm
    if _default_fm is None:
        _default_fm = FontManager()
    return _default_fm
