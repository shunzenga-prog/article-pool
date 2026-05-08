"""流程图生成 — Mermaid.js + Playwright 渲染设计级流程图

13 套设计色板 + 4 种卡片风格 + SVG 后处理注入。

用法:
    from capture.flowchart import FlowchartCapture, flowchart_to_image

    # 从 dict 生成
    flow = {"nodes": [{"id":"a","label":"开始"}],
            "edges": [{"from":"a","to":"b","label":"→"}]}
    flowchart_to_image(flow, "flow.png", palette="ocean")

    # 从 JSON 文件生成
    from capture.flowchart import FlowchartCapture
    FlowchartCapture().generate_from_file("flow.json", "flow.png")
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from .base import BaseCapture

# ═══════════════════════════════════════════════
#  Mermaid.js 流程图渲染器
# ═══════════════════════════════════════════════

MERMAID_CDN = "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"

# 色板元数据（完整色板定义在 flowchart_gen.py 中）
PALETTE_NAMES = [
    "tech-dark", "ocean", "forest", "sunset", "midnight", "paper",
    "cyberpunk", "ember", "aurora", "navy", "slate", "rose",
]

CARD_STYLES = ["glass", "solid", "neon", "minimal"]

# 色板 → 背景色/文本色映射（用于 HTML 卡片渲染）
_PALETTE_COLORS = {
    "tech-dark":  ("#0d1117", "#c9d1d9", "rgba(22,27,34,0.95)", "rgba(48,54,61,0.5)"),
    "ocean":      ("#0a1628", "#a8d8ea", "rgba(13,25,48,0.95)", "rgba(30,60,100,0.5)"),
    "forest":     ("#0d1f0d", "#a3d9a5", "rgba(18,36,18,0.95)", "rgba(30,65,30,0.5)"),
    "sunset":     ("#1f1410", "#f0c8a0", "rgba(36,24,18,0.95)", "rgba(70,40,25,0.5)"),
    "midnight":   ("#0a0a1a", "#b8b8d8", "rgba(16,16,36,0.95)", "rgba(40,40,70,0.5)"),
    "paper":      ("#fafaf8", "#1a1a1a", "rgba(252,252,250,0.95)", "rgba(200,200,195,0.5)"),
    "cyberpunk":  ("#0d0d0d", "#ff6b9d", "rgba(20,20,20,0.95)", "rgba(80,20,60,0.5)"),
    "ember":      ("#1a0c0c", "#ff8844", "rgba(30,16,16,0.95)", "rgba(70,30,20,0.5)"),
    "aurora":     ("#081a14", "#5eead4", "rgba(12,30,24,0.95)", "rgba(20,60,50,0.5)"),
    "navy":       ("#0c1220", "#94a3b8", "rgba(16,22,40,0.95)", "rgba(30,40,65,0.5)"),
    "slate":      ("#1a1a1e", "#d4d4d8", "rgba(30,30,34,0.95)", "rgba(50,50,55,0.5)"),
    "rose":       ("#1a1018", "#f0a0b8", "rgba(30,20,28,0.95)", "rgba(60,30,40,0.5)"),
}


class FlowchartCapture(BaseCapture):
    """Mermaid.js 流程图渲染器。

    通过 Playwright 将 Mermaid 标记渲染为带有设计色板卡片背景的 PNG。
    """

    def generate_mermaid_markup(
        self,
        flow: dict,
        direction: str = "LR",
    ) -> str:
        """从 dict 生成 Mermaid.js 标记。

        Args:
            flow: {"nodes": [...], "edges": [...], "subgraphs": [...]}
            direction: LR | RL | TB | BT
        """
        direction = flow.get("direction", direction)
        lines = [f"graph {direction}"]

        # Subgraphs
        for sg in flow.get("subgraphs", []):
            title = sg.get("title", "")
            style_sg = sg.get("style", "")
            lines.append(f'  subgraph "{title}"')
            if style_sg:
                lines.append(f'    style "{title}" {style_sg}')
            for nid in sg.get("nodes", []):
                label = self._find_node_label(flow, nid)
                shape_def = self._node_shape(flow, nid, label)
                lines.append(f"    {shape_def}")
            lines.append("  end")

        # Nodes
        for node in flow.get("nodes", []):
            nid = node.get("id", "")
            label = node.get("label", nid)
            desc = node.get("desc", "")
            display = f"{label}\\n{desc}" if desc else label
            shape = node.get("shape", "rounded")
            shape_def = self._node_def(nid, display, shape)
            lines.append(f"  {shape_def}")

        # Edges
        for edge in flow.get("edges", []):
            frm = edge.get("from", "")
            to = edge.get("to", "")
            label = edge.get("label", "")
            link = f"{frm} -->|{label}| {to}" if label else f"{frm} --> {to}"
            lines.append(f"  {link}")

        return "\n".join(lines)

    def generate_from_dict(
        self,
        flow: dict,
        output_path: str,
        palette: str = "tech-dark",
        card_style: str = "glass",
        width: int = 720,
    ) -> str:
        """从 Python dict 生成流程图 PNG。"""
        title = flow.get("title", "")
        subtitle = flow.get("subtitle", "")
        direction = flow.get("direction", "LR")
        mermaid = self.generate_mermaid_markup(flow, direction)
        return self._render(mermaid, output_path, palette, card_style, width, title, subtitle)

    def generate_from_json(
        self,
        json_str: str,
        output_path: str,
        palette: str = "tech-dark",
        card_style: str = "glass",
        width: int = 720,
    ) -> str:
        """从 JSON 字符串生成流程图 PNG。"""
        return self.generate_from_dict(
            json.loads(json_str), output_path, palette, card_style, width
        )

    def generate_from_file(
        self,
        json_path: str,
        output_path: str,
        palette: str = "tech-dark",
        card_style: str = "glass",
        width: int = 720,
    ) -> str:
        """从 JSON 文件生成流程图 PNG。"""
        with open(json_path, "r", encoding="utf-8") as f:
            flow = json.load(f)
        return self.generate_from_dict(flow, output_path, palette, card_style, width)

    def _render(
        self,
        mermaid_markup: str,
        output_path: str,
        palette: str,
        card_style: str,
        width: int,
        title: str = "",
        subtitle: str = "",
    ) -> str:
        """通过 Playwright 渲染 Mermaid → SVG → PNG。"""
        html = self._build_html(mermaid_markup, palette, card_style, width, title, subtitle)
        tmp_html = self.temp_html(html)
        url = self.file_url(tmp_html)

        with self.browser_page(width=width, height=600) as page:
            self.navigate_and_wait(page, url)
            page.wait_for_selector("svg", timeout=15000)
            page.wait_for_timeout(1000)

            el = page.query_selector(".flowchart-card")
            if el:
                el.screenshot(path=output_path)
            else:
                page.screenshot(path=output_path, full_page=True)

        self._log_screenshot(output_path)
        return output_path

    def _build_html(
        self,
        mermaid: str,
        palette: str,
        card_style: str,
        width: int,
        title: str = "",
        subtitle: str = "",
    ) -> str:
        """构建包含 Mermaid 渲染的 HTML 页面，应用选定色板颜色。"""
        card_pad = 32
        bg, text_c, card_bg, card_border = _PALETTE_COLORS.get(
            palette, _PALETTE_COLORS["tech-dark"]
        )
        # 检测深色/浅色模式：paper 色板使用深色副标题
        is_dark = palette != "paper"
        sub_c = "#8b949e" if is_dark else "#6b6b6b"

        return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{
  background:{bg};display:flex;justify-content:center;align-items:center;
  min-height:100vh;padding:32px;font-family:system-ui,sans-serif;
}}
.flowchart-card{{
  background:{card_bg};border:1px solid {card_border};
  border-radius:12px;padding:{card_pad}px;width:{width}px;
}}
.flowchart-title{{color:{text_c};font-size:18px;font-weight:600;margin-bottom:4px;}}
.flowchart-subtitle{{color:{sub_c};font-size:13px;margin-bottom:20px;}}
.mermaid{{display:flex;justify-content:center;}}
.mermaid svg{{max-width:100%;height:auto;}}
</style></head><body>
<div class="flowchart-card">
  {"<div class='flowchart-title'>"+title+"</div>" if title else ""}
  {"<div class='flowchart-subtitle'>"+subtitle+"</div>" if subtitle else ""}
  <div class="mermaid">{mermaid}</div>
</div>
<script src="{MERMAID_CDN}"></script>
<script>mermaid.initialize({{startOnLoad:true,theme:'dark'}});</script>
</body></html>"""

    # ── 节点形状辅助 ────────────────────────────

    @staticmethod
    def _node_def(nid: str, label: str, shape: str) -> str:
        shapes = {
            "rounded":   '{0}("{1}")',
            "rectangle": '{0}["{1}"]',
            "stadium":   '{0}(["{1}"])',
            "hexagon":   '{0}{{{{"{1}"}}}}',
            "cylinder":  '{0}[("{1}")]',
            "diamond":   '{0}{{"{1}"}}',
            "subroutine":'{0}[["{1}"]]',
            "circle":    '{0}(("{1}"))',
        }
        tmpl = shapes.get(shape, '{0}("{1}")')
        return tmpl.format(nid, label)

    @staticmethod
    def _find_node_label(flow: dict, nid: str) -> str:
        for n in flow.get("nodes", []):
            if n.get("id") == nid:
                return n.get("label", nid)
        return nid


# ── 便利函数 ──────────────────────────────────


def flowchart_to_image(
    flow: dict | str,
    output: str,
    palette: str = "tech-dark",
    style: str = "glass",
    width: int = 720,
) -> str:
    """一键流程图生成。

    Args:
        flow: dict 或 JSON 字符串
        output: 输出 PNG 路径
        palette: 色板名称
        style: 卡片风格 (glass/solid/neon/minimal)
        width: 卡片宽度
    """
    if isinstance(flow, str):
        flow = json.loads(flow)

    with FlowchartCapture() as fc:
        return fc.generate_from_dict(flow, output, palette=palette, card_style=style, width=width)


def list_palettes() -> list[str]:
    """列出可用色板"""
    return PALETTE_NAMES
