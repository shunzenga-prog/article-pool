#!/usr/bin/env python3
"""
Flowchart generator for WeChat tutorials — Mermaid.js + Playwright.

Generates professional flowcharts as PNG images for use in tutorial articles.
Mermaid handles auto-layout and rendering; Playwright screenshots the SVG.

Usage:
  # From JSON file
  python flowchart_gen.py --file flow.json -o flowchart.png

  # From inline JSON
  python flowchart_gen.py --inline '{"direction":"LR","nodes":[...],"edges":[...]}' -o flowchart.png

  # Custom theme + width
  python flowchart_gen.py --file flow.json -o chart.png --theme catppuccin --width 670

Input JSON schema:
  {
    "direction": "LR|TB",
    "title": "Optional diagram title",
    "nodes": [
      {"id": "fetch", "label": "1. 抓取", "desc": "Hacker News API\n免费 JSON 接口",
       "shape": "rounded|rectangle|diamond|cylinder"}
    ],
    "edges": [
      {"from": "fetch", "to": "process", "label": "数据流"}
    ]
  }
"""

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False


# ── Theme presets ──

THEMES = {
    "catppuccin": {
        "bg": "#1e1e2e",
        "primary_color": "#89b4fa",
        "primary_border": "#89b4fa",
        "primary_text": "#cdd6f4",
        "secondary_color": "#313244",
        "secondary_border": "#45475a",
        "tertiary_color": "#1e1e2e",
        "tertiary_border": "#45475a",
        "line_color": "#6c7086",
        "edge_label_bg": "#313244",
        "edge_label_text": "#a6adc8",
        "note_bg": "#45475a",
        "note_border": "#585b70",
    },
    "github": {
        "bg": "#ffffff",
        "primary_color": "#0969da",
        "primary_border": "#0969da",
        "primary_text": "#1f2328",
        "secondary_color": "#f6f8fa",
        "secondary_border": "#d0d7de",
        "tertiary_color": "#ffffff",
        "tertiary_border": "#d0d7de",
        "line_color": "#656d76",
        "edge_label_bg": "#f6f8fa",
        "edge_label_text": "#656d76",
        "note_bg": "#f6f8fa",
        "note_border": "#d0d7de",
    },
    "dark": {
        "bg": "#0d1117",
        "primary_color": "#58a6ff",
        "primary_border": "#58a6ff",
        "primary_text": "#c9d1d9",
        "secondary_color": "#161b22",
        "secondary_border": "#30363d",
        "tertiary_color": "#0d1117",
        "tertiary_border": "#30363d",
        "line_color": "#8b949e",
        "edge_label_bg": "#161b22",
        "edge_label_text": "#8b949e",
        "note_bg": "#21262d",
        "note_border": "#30363d",
    },
}

MERMAID_CDN = "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"


# ── Mermaid markup generation ──

def _node_def(node):
    """Generate a Mermaid node definition line."""
    nid = node["id"]
    label = node.get("label", nid)
    desc = node.get("desc", "")
    shape = node.get("shape", "rounded")

    text = f"<b>{label}</b>"
    if desc:
        text += f"<br/>{desc}"

    text_escaped = text.replace('"', '&quot;')

    shape_map = {
        "rounded": f'{nid}("{text_escaped}")',
        "rectangle": f'{nid}["{text_escaped}"]',
        "stadium": f'{nid}(["{text_escaped}"])',
        "diamond": f'{nid}{{"{text_escaped}"}}',
        "hexagon": f'{nid}{{{{"{text_escaped}"}}}}',
        "cylinder": f'{nid}[("{text_escaped}")]',
        "subroutine": f'{nid}[["{text_escaped}"]]',
    }
    return shape_map.get(shape, shape_map["rounded"])


def _edge_def(edge):
    """Generate a Mermaid edge definition line."""
    frm = edge["from"]
    to = edge["to"]
    label = edge.get("label", "")
    style = edge.get("style", "arrow")

    base = f"{frm} -->{_edge_label(label)} {to}"
    if style == "dashed":
        base = f"{frm} -.->{_edge_label(label)} {to}"
    elif style == "thick":
        base = f"{frm} ==>{_edge_label(label)} {to}"
    return base


def _edge_label(label):
    """Format edge label."""
    if not label:
        return ""
    return f'|"{label}"|'


def _theme_config(theme_name="catppuccin"):
    """Generate Mermaid %%{init}%% theme config."""
    t = THEMES.get(theme_name, THEMES["catppuccin"])

    return f"""%%{{init: {{'theme':'base', 'themeVariables': {{
  'background': '{t["bg"]}',
  'primaryColor': '{t["primary_color"]}',
  'primaryBorderColor': '{t["primary_border"]}',
  'primaryTextColor': '{t["primary_text"]}',
  'secondaryColor': '{t["secondary_color"]}',
  'secondaryBorderColor': '{t["secondary_border"]}',
  'tertiaryColor': '{t["tertiary_color"]}',
  'tertiaryBorderColor': '{t["tertiary_border"]}',
  'lineColor': '{t["line_color"]}',
  'edgeLabelBackground': '{t["edge_label_bg"]}',
  'noteBkgColor': '{t["note_bg"]}',
  'noteBorderColor': '{t["note_border"]}'
}}, 'flowchart': {{'useMaxWidth': false, 'htmlLabels': true, 'curve': 'basis'}}}}}}%%"""


def generate_mermaid(flow: dict, theme="catppuccin") -> str:
    """Convert flow dict to Mermaid.js markup string."""
    direction = flow.get("direction", "LR")
    nodes = flow.get("nodes", [])
    edges = flow.get("edges", [])
    title = flow.get("title", "")

    lines = [_theme_config(theme)]
    lines.append(f"flowchart {direction}")

    if title:
        lines.append(f"  title[\"<b>{title}</b>\"]")
        lines.append("  title ~~~ title")

    for node in nodes:
        lines.append(f"  {_node_def(node)}")

    for edge in edges:
        lines.append(f"  {_edge_def(edge)}")

    return "\n".join(lines)


# ── Playwright rendering ──

_HTML_TEMPLATE = """<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<style>
  body {{
    margin: 0;
    padding: 24px;
    background: {bg};
    display: flex;
    justify-content: center;
    align-items: flex-start;
    min-height: 100vh;
  }}
  .mermaid svg {{
    max-width: 100%;
    height: auto;
  }}
</style>
</head><body>
<pre class="mermaid">
{mermaid}
</pre>
<script src="{cdn}"></script>
<script>
  mermaid.initialize({{ startOnLoad: true }});
</script>
</body></html>"""


def render_mermaid_to_png(mermaid_markup: str, output_path: str,
                          theme="catppuccin", width: int = 670,
                          device_scale: float = 2.0):
    """Render Mermaid markup to a PNG image using Playwright.

    Args:
        mermaid_markup: Mermaid.js markup string
        output_path: PNG file path
        theme: Theme name (catppuccin, github, dark)
        width: Max viewport width in pixels
        device_scale: Scale factor (2.0 = Retina quality)
    """
    if not HAS_PLAYWRIGHT:
        print("ERROR: playwright not installed. Run: pip install playwright && playwright install chromium")
        sys.exit(1)

    t = THEMES.get(theme, THEMES["catppuccin"])
    bg = t["bg"]

    html = _HTML_TEMPLATE.format(
        bg=bg,
        mermaid=mermaid_markup,
        cdn=MERMAID_CDN,
    )

    with tempfile.NamedTemporaryFile(suffix=".html", mode="w", encoding="utf-8", delete=False) as f:
        f.write(html)
        html_path = f.name

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(
                viewport={"width": width, "height": 800},
                device_scale_factor=device_scale,
            )
            page.goto(f"file:///{html_path.replace(os.sep, '/')}", wait_until="networkidle", timeout=30000)

            # Wait for mermaid SVG to render
            page.wait_for_selector(".mermaid svg", timeout=15000)
            page.wait_for_timeout(500)  # extra render buffer

            svg_element = page.locator(".mermaid svg")
            svg_element.screenshot(path=output_path)

            browser.close()
    finally:
        os.unlink(html_path)


def generate_flowchart(flow: str | dict, output_path: str,
                       theme="catppuccin", width: int = 670):
    """End-to-end: flow dict/JSON → PNG.

    Args:
        flow: Flow dict or JSON string
        output_path: PNG file path
        theme: 'catppuccin' | 'github' | 'dark'
        width: Max viewport width
    """
    if isinstance(flow, str):
        flow = json.loads(flow)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    markup = generate_mermaid(flow, theme)
    render_mermaid_to_png(markup, output_path, theme=theme, width=width)

    size_kb = os.path.getsize(output_path) / 1024
    print(f"OK: {output_path} ({size_kb:.1f} KB) theme:{theme}")


# ── CLI ──

def main():
    p = argparse.ArgumentParser(
        description="Generate flowcharts for WeChat tutorials (Mermaid.js + Playwright)")
    p.add_argument("--file", help="JSON file with flow definition")
    p.add_argument("--inline", help="Inline JSON flow definition")
    p.add_argument("--output", "-o", required=True, help="Output PNG path")
    p.add_argument("--theme", choices=list(THEMES.keys()), default="catppuccin",
                   help="Color theme (default: catppuccin)")
    p.add_argument("--width", type=int, default=670,
                   help="Max viewport width in px (default: 670)")
    p.add_argument("--markup-only", action="store_true",
                   help="Print Mermaid markup only, don't render")

    args = p.parse_args()

    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            flow = json.load(f)
    elif args.inline:
        flow = json.loads(args.inline)
    else:
        p.error("Either --file or --inline is required")

    if args.markup_only:
        print(generate_mermaid(flow, args.theme))
    else:
        generate_flowchart(flow, args.output, theme=args.theme, width=args.width)


if __name__ == "__main__":
    main()
