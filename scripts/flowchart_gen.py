#!/usr/bin/env python3
"""
流程图生成器 — 薄 CLI 包装器，核心逻辑在 scripts/capture/flowchart.py

用法:
  python flowchart_gen.py --file flow.json -o chart.png
  python flowchart_gen.py --file flow.json -o chart.png --palette ocean --style glass
  python flowchart_gen.py --inline '{"nodes":[...]}' --markup-only
  python flowchart_gen.py --list-palettes
"""

import argparse
import json
import sys

from capture.flowchart import FlowchartCapture, list_palettes, CARD_STYLES


def main():
    # Fix Windows GBK stdout for emoji output
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    p = argparse.ArgumentParser(
        description="Design-grade flowcharts (Mermaid.js + Playwright)")

    p.add_argument("--file", help="JSON file with flow definition")
    p.add_argument("--inline", help="Inline JSON flow definition")
    p.add_argument("--output", "-o", help="Output PNG path")
    p.add_argument("--palette", default="tech-dark",
                   help="Design palette (tech-dark/ocean/forest/sunset/midnight/paper/cyberpunk/ember/aurora/navy/slate/rose)")
    p.add_argument("--style", "-s", default="glass",
                   help="Card visual style: glass|solid|neon|minimal")
    p.add_argument("--width", type=int, default=720,
                   help="Canvas width in px (default: 720)")
    p.add_argument("--markup-only", action="store_true",
                   help="Print Mermaid markup only (debug)")
    p.add_argument("--list-palettes", action="store_true",
                   help="Show available palettes & card styles and exit")

    args = p.parse_args()

    if args.list_palettes:
        for name in list_palettes():
            print(f"  {name}")
        print(f"\n  card styles: {', '.join(CARD_STYLES)}")
        return

    fc = FlowchartCapture()

    if args.markup_only:
        if args.file:
            with open(args.file, "r", encoding="utf-8") as f:
                flow = json.load(f)
        elif args.inline:
            flow = json.loads(args.inline)
        else:
            p.error("Either --file or --inline is required")
        print(fc.generate_mermaid_markup(flow))
        return

    if not args.output:
        p.error("--output/-o is required for rendering")

    if args.file:
        fc.generate_from_file(args.file, args.output,
                              palette=args.palette, card_style=args.style,
                              width=args.width)
    elif args.inline:
        fc.generate_from_json(args.inline, args.output,
                              palette=args.palette, card_style=args.style,
                              width=args.width)
    else:
        p.error("Either --file or --inline is required")


if __name__ == "__main__":
    main()
