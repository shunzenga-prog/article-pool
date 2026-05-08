"""统一颜色令牌系统 — 所有截图/渲染模块的颜色来源

提供:
  - ColorTokens dataclass: 可跨模块复用的标准颜色令牌
  - ThemeRegistry: 中心化调色板注册/查询
  - 预设调色板: Catppuccin Mocha, GitHub Dark, 13 套流程图色板

用法:
    from capture.themes import ThemeRegistry
    t = ThemeRegistry.get("catppuccin-mocha")
    print(t.bg)     # "#1e1e2e"
    print(t.text)   # "#cdd6f4"
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ColorTokens:
    """通用颜色令牌 — 所有渲染模块共享此结构"""

    name: str = "default"

    # 画布
    bg: str = "#1e1e2e"
    surface: str = "#181825"
    surface_alt: str = "#313244"

    # 文本层级
    text: str = "#cdd6f4"
    text_dim: str = "#6c7086"
    text_bright: str = "#f5f0ec"

    # 语义色
    accent: str = "#89b4fa"
    success: str = "#a6e3a1"
    warning: str = "#f9e2af"
    error: str = "#f38ba8"
    info: str = "#94e2d5"

    # 边框/分割线
    border: str = "#313244"
    border_bright: str = "#45475a"

    # 代码高亮
    keyword: str = "#89b4fa"
    string: str = "#a6e3a1"
    comment: str = "#6c7086"
    func: str = "#cba6f7"
    number: str = "#fab387"

    # 标题栏
    titlebar_bg: str = "#181825"
    titlebar_text: str = "#cdd6f4"

    # 行号/水印
    line_num: str = "#6c7086"
    line_num_dim: str = "#313244"
    highlight_line: str = "#313244"
    watermark: str = "#313244"

    def to_dict(self) -> dict[str, str]:
        """转为简单 dict（用于 Template 替换等场景）"""
        return {k: v for k, v in self.__dict__.items() if isinstance(v, str)}


# ═══════════════════════════════════════════════
#  预定义主题
# ═══════════════════════════════════════════════

CATPPUCCIN_MOCHA = ColorTokens(
    name="catppuccin-mocha",
    bg="#1e1e2e",
    surface="#181825",
    surface_alt="#313244",
    text="#cdd6f4",
    text_dim="#6c7086",
    text_bright="#f5f0ec",
    accent="#89b4fa",
    success="#a6e3a1",
    warning="#f9e2af",
    error="#f38ba8",
    info="#94e2d5",
    border="#313244",
    border_bright="#45475a",
    keyword="#89b4fa",
    string="#a6e3a1",
    comment="#6c7086",
    func="#cba6f7",
    number="#fab387",
    titlebar_bg="#181825",
    titlebar_text="#cdd6f4",
    line_num="#6c7086",
    line_num_dim="#313244",
    highlight_line="#313244",
    watermark="#313244",
)

GITHUB_DARK = ColorTokens(
    name="github-dark",
    bg="#0d1117",
    surface="#161b22",
    surface_alt="#21262d",
    text="#e6edf3",
    text_dim="#8b949e",
    text_bright="#ffffff",
    accent="#79c0ff",
    success="#56d364",
    warning="#d29922",
    error="#f85149",
    info="#79c0ff",
    border="#30363d",
    border_bright="#484f58",
    keyword="#79c0ff",
    string="#a5d6ff",
    comment="#8b949e",
    func="#d2a8ff",
    number="#79c0ff",
    titlebar_bg="#161b22",
    titlebar_text="#e6edf3",
    line_num="#484f58",
    line_num_dim="#21262d",
    highlight_line="#1f2429",
    watermark="#21262d",
)

# 流程图色板（从 flowchart_gen.py 抽取）
TECH_DARK = ColorTokens(
    name="tech-dark",
    bg="#0d1117",
    surface="#161b22",
    surface_alt="#1c2333",
    text="#c9d1d9",
    text_dim="#8b949e",
    text_bright="#f0f6fc",
    accent="#58a6ff",
    success="#3fb950",
    warning="#d29922",
    error="#f85149",
    info="#79c0ff",
    border="#30363d",
    border_bright="#484f58",
    keyword="#58a6ff",
    string="#a5d6ff",
    comment="#8b949e",
    func="#d2a8ff",
    number="#79c0ff",
    titlebar_bg="#0d1117",
    titlebar_text="#c9d1d9",
)

OCEAN = ColorTokens(
    name="ocean",
    bg="#0a1929",
    surface="#132f4c",
    surface_alt="#173a5e",
    text="#b3d4fc",
    text_dim="#7fa8c9",
    text_bright="#e6f0fa",
    accent="#5090d3",
    success="#43a9a4",
    warning="#d4a843",
    error="#d9594c",
    info="#5090d3",
    border="#1e4976",
    border_bright="#265d97",
    keyword="#5090d3",
    string="#6bc9c4",
    comment="#5d80a6",
    func="#a78bfa",
    number="#d4a843",
    titlebar_bg="#0a1929",
    titlebar_text="#b3d4fc",
)

FOREST = ColorTokens(
    name="forest",
    bg="#0d1f17",
    surface="#132a1e",
    surface_alt="#1a3829",
    text="#b8d4c3",
    text_dim="#6b9e7a",
    text_bright="#e0f0e5",
    accent="#4caf7a",
    success="#66bb6a",
    warning="#c4a43e",
    error="#d9594c",
    info="#4caf7a",
    border="#1e5234",
    border_bright="#2d6b45",
    keyword="#4caf7a",
    string="#81c784",
    comment="#5d8a6e",
    func="#a78bfa",
    number="#c4a43e",
    titlebar_bg="#0d1f17",
    titlebar_text="#b8d4c3",
)

SUNSET = ColorTokens(
    name="sunset",
    bg="#1a0f14",
    surface="#2d1620",
    surface_alt="#3d1f2a",
    text="#e8ccd4",
    text_dim="#b58496",
    text_bright="#fae8ee",
    accent="#e47c6c",
    success="#9dc97c",
    warning="#e8b84b",
    error="#e45c4c",
    info="#e47c6c",
    border="#4d2a36",
    border_bright="#6b3d4c",
    keyword="#e47c6c",
    string="#9dc97c",
    comment="#8a6d7a",
    func="#cba6f7",
    number="#e8b84b",
    titlebar_bg="#1a0f14",
    titlebar_text="#e8ccd4",
)

MIDNIGHT = ColorTokens(
    name="midnight",
    bg="#0c0e14",
    surface="#12151e",
    surface_alt="#1a1e2a",
    text="#c0c4d4",
    text_dim="#6e738a",
    text_bright="#dfe2ed",
    accent="#7c8cf8",
    success="#78c89c",
    warning="#e0b050",
    error="#e06070",
    info="#6cb8e4",
    border="#252940",
    border_bright="#363b5c",
    keyword="#7c8cf8",
    string="#78c89c",
    comment="#5d6380",
    func="#c4a0f8",
    number="#e0b050",
    titlebar_bg="#0c0e14",
    titlebar_text="#c0c4d4",
)

PAPER = ColorTokens(
    name="paper",
    bg="#faf9f6",
    surface="#ffffff",
    surface_alt="#f0ede8",
    text="#2c2c2c",
    text_dim="#8c8c8c",
    text_bright="#0c0c0c",
    accent="#2563eb",
    success="#16a34a",
    warning="#ca8a04",
    error="#dc2626",
    info="#2563eb",
    border="#e0dcd5",
    border_bright="#d0cbc4",
    keyword="#2563eb",
    string="#16a34a",
    comment="#9ca3af",
    func="#7c3aed",
    number="#ca8a04",
    titlebar_bg="#f0ede8",
    titlebar_text="#2c2c2c",
)

CYBERPUNK = ColorTokens(
    name="cyberpunk",
    bg="#0a0a0f",
    surface="#12081c",
    surface_alt="#1c0f2e",
    text="#d6b8ff",
    text_dim="#7a5a9e",
    text_bright="#f0e0ff",
    accent="#ff6ec7",
    success="#00ff88",
    warning="#ffb340",
    error="#ff4060",
    info="#00ccff",
    border="#2a1548",
    border_bright="#4a2870",
    keyword="#ff6ec7",
    string="#00ff88",
    comment="#5c3d7a",
    func="#c07aff",
    number="#ffb340",
    titlebar_bg="#0a0a0f",
    titlebar_text="#d6b8ff",
)

EMBER = ColorTokens(
    name="ember",
    bg="#1a1008",
    surface="#261a0c",
    surface_alt="#362410",
    text="#e0c8a0",
    text_dim="#8a7050",
    text_bright="#f5e4c8",
    accent="#f09050",
    success="#7cb860",
    warning="#e0b448",
    error="#d05040",
    info="#e08850",
    border="#3d2a14",
    border_bright="#5c3d20",
    keyword="#f09050",
    string="#7cb860",
    comment="#6c5a40",
    func="#d0a0f0",
    number="#e0b448",
    titlebar_bg="#1a1008",
    titlebar_text="#e0c8a0",
)

AURORA = ColorTokens(
    name="aurora",
    bg="#0d141e",
    surface="#131d2e",
    surface_alt="#1a2840",
    text="#b8d0e8",
    text_dim="#58789e",
    text_bright="#d8e8f8",
    accent="#40c4b8",
    success="#60d880",
    warning="#e8c840",
    error="#e85868",
    info="#50b8e8",
    border="#1e3050",
    border_bright="#2d4870",
    keyword="#40c4b8",
    string="#60d880",
    comment="#4c6890",
    func="#9880f0",
    number="#e8c840",
    titlebar_bg="#0d141e",
    titlebar_text="#b8d0e8",
)

NAVY = ColorTokens(
    name="navy",
    bg="#0a1020",
    surface="#111d38",
    surface_alt="#182848",
    text="#b0c4e0",
    text_dim="#5470a0",
    text_bright="#d0dcf0",
    accent="#5088e0",
    success="#48b880",
    warning="#d8b050",
    error="#e05860",
    info="#58a0e8",
    border="#1c3460",
    border_bright="#2a4880",
    keyword="#5088e0",
    string="#48b880",
    comment="#486898",
    func="#9078e8",
    number="#d8b050",
    titlebar_bg="#0a1020",
    titlebar_text="#b0c4e0",
)

SLATE = ColorTokens(
    name="slate",
    bg="#1a1c1e",
    surface="#242628",
    surface_alt="#2e3034",
    text="#c0c4c8",
    text_dim="#6c7078",
    text_bright="#e0e4e8",
    accent="#7890b0",
    success="#78a878",
    warning="#c8b060",
    error="#c06068",
    info="#6898b8",
    border="#383a40",
    border_bright="#4c4e54",
    keyword="#7890b0",
    string="#78a878",
    comment="#5c6068",
    func="#a088c8",
    number="#c8b060",
    titlebar_bg="#1a1c1e",
    titlebar_text="#c0c4c8",
)

ROSE = ColorTokens(
    name="rose",
    bg="#1a1018",
    surface="#241820",
    surface_alt="#302028",
    text="#d0bcc8",
    text_dim="#786878",
    text_bright="#e8dce8",
    accent="#d08090",
    success="#80b870",
    warning="#d8b050",
    error="#d85868",
    info="#c080a0",
    border="#382830",
    border_bright="#504050",
    keyword="#d08090",
    string="#80b870",
    comment="#685868",
    func="#b890d0",
    number="#d8b050",
    titlebar_bg="#1a1018",
    titlebar_text="#d0bcc8",
)

# ═══════════════════════════════════════════════
#  注册表
# ═══════════════════════════════════════════════


class ThemeRegistry:
    """集中式主题注册表 — 所有模块通过此获取颜色"""

    _themes: dict[str, ColorTokens] = {
        "catppuccin-mocha": CATPPUCCIN_MOCHA,
        "github-dark": GITHUB_DARK,
        "tech-dark": TECH_DARK,
        "ocean": OCEAN,
        "forest": FOREST,
        "sunset": SUNSET,
        "midnight": MIDNIGHT,
        "paper": PAPER,
        "cyberpunk": CYBERPUNK,
        "ember": EMBER,
        "aurora": AURORA,
        "navy": NAVY,
        "slate": SLATE,
        "rose": ROSE,
    }

    @classmethod
    def get(cls, name: str = "catppuccin-mocha") -> ColorTokens:
        """获取指定主题，不存在时回退到 Catppuccin Mocha"""
        return cls._themes.get(name, CATPPUCCIN_MOCHA)

    @classmethod
    def list_names(cls) -> list[str]:
        return sorted(cls._themes.keys())

    @classmethod
    def register(cls, tokens: ColorTokens) -> None:
        """动态注册新主题"""
        cls._themes[tokens.name] = tokens
