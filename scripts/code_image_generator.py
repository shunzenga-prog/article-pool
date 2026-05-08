#!/usr/bin/env python3
"""
代码图片生成器 — 薄 CLI 包装器，核心逻辑在 scripts/capture/code.py + scripts/capture/chart.py

用法:
  python code_image_generator.py code input.py -o code.png
  python code_image_generator.py exec input.py -o output.png
  python code_image_generator.py chart input.py -o chart.png
  python code_image_generator.py anim input.py -o anim.gif
  python code_image_generator.py process article.md -o images/ --execute --animate
"""

import argparse
import os
import re
from pathlib import Path

from capture.code import CodeCapture, code_to_image, exec_to_image, code_to_animation
from capture.chart import chart_screenshot


def process_article(md_path: str, output_dir: str,
                    execute_code: bool = False,
                    generate_animations: bool = False):
    """扫描 Markdown 文章中的代码块，自动生成配图。"""
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    os.makedirs(output_dir, exist_ok=True)
    images = []
    errors = []
    basename = Path(md_path).stem

    pattern = re.compile(r"```(\w+)(?:\s+(\w+))?\s*\n(.*?)```", re.DOTALL)

    with CodeCapture() as cc:
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
                        cc.code_animation(code, gif_path, language=lang)
                        images.append(("animation", gif_path))
                    else:
                        cc.code_screenshot(code, img_path, language=lang)
                        images.append(("code", img_path))
                elif tag == "chart":
                    if execute_code:
                        chart_screenshot(code, img_path)
                        images.append(("chart", img_path))
                elif tag == "exec":
                    if execute_code:
                        cc.exec_and_capture(code, img_path, language=lang)
                        images.append(("terminal", img_path))
                else:
                    cc.code_screenshot(code, img_path, language=lang)
                    images.append(("code", img_path))
            except Exception as e:
                errors.append(f"代码块 #{idx+1}: {e}")

    return images, errors


def main():
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
        path = code_to_image(code, args.output, lang=args.language, style=args.style)
        print(f"OK code: {path}")

    elif args.command == "exec":
        with open(args.input, "r") as f:
            code = f.read()
        r = exec_to_image(code, args.output)
        print(f"OK exec: {r['path']}")
        if r["returncode"] != 0:
            print(f"  exit={r['returncode']}")

    elif args.command == "chart":
        with open(args.input, "r") as f:
            code = f.read()
        r = chart_screenshot(code, args.output)
        print(f"OK chart: {r['path']}")
        if r.get("error"):
            print(f"  stderr: {r['error'][:200]}")

    elif args.command == "anim":
        with open(args.input, "r") as f:
            code = f.read()
        path = code_to_animation(code, args.output)
        print(f"OK anim: {path}")

    elif args.command == "process":
        images, errors = process_article(
            args.input, args.output_dir,
            execute_code=args.execute, generate_animations=args.animate,
        )
        print(f"OK: {len(images)} images")
        for typ, path in images:
            print(f"  [{typ}] {os.path.basename(path)} ({os.path.getsize(path)//1024}KB)")
        if errors:
            print(f"ERRORS ({len(errors)}):")
            for e in errors:
                print(f"  - {e}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
