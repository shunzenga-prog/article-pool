# -*- coding: utf-8 -*-
"""Professional cover image generator for WeChat articles.

Usage:
    python3 gen_cover.py --title "AI 圈沸腾的一周" --output cover.png
    python3 gen_cover.py --title "标题第一行\n标题第二行" --subtitle "副标题" --tag "MORNING BRIEF" --output cover.png
"""

from PIL import Image, ImageDraw, ImageFont
import os, math, random, argparse, textwrap
from datetime import datetime

# ── Constants ──
W, H = 1200, 675
LEFT = 80
ACCENT = (0xFF, 0x6B, 0x35)
LIGHT = (0xE8, 0xE8, 0xF0)
MID = (0x94, 0x94, 0xB8)
DIM = (0x64, 0x64, 0x88)
BASE = (0x0A, 0x0E, 0x1A)

FCJK = '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf'
FLAT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FLATB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'


def is_cjk(cp):
    return (0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF or
            0xF900 <= cp <= 0xFAFF or 0x3000 <= cp <= 0x303F or
            0xFF00 <= cp <= 0xFFEF or 0x2000 <= cp <= 0x206F)


def draw_text(draw, xy, text, fill, fcjk, flat):
    x, y = xy
    i = 0
    while i < len(text):
        cp = ord(text[i])
        use_cjk = is_cjk(cp)
        j = i + 1
        while j < len(text):
            if is_cjk(ord(text[j])) != use_cjk:
                break
            j += 1
        seg = text[i:j]
        f = fcjk if use_cjk else flat
        draw.text((x, y), seg, fill=fill, font=f)
        bbox = draw.textbbox((x, y), seg, font=f)
        x = bbox[2] + 1
        i = j


def build_background(img, draw, px):
    """Apply dual radial gradients, noise, and decorative elements."""
    # Warm violet glow top-right
    cx, cy, rg = W - 150, 0, 700
    for x in range(W):
        for y in range(H):
            d = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
            if d < rg:
                t = (1 - d / rg) ** 2.5
                o = px[x, y]
                px[x, y] = (
                    int(o[0] * (1 - t) + 0x5B * t),
                    int(o[1] * (1 - t) + 0x2C * t),
                    int(o[2] * (1 - t) + 0x6E * t),
                )

    # Cool blue glow bottom-left
    cx2, cy2, rg2 = 50, H, 650
    for x in range(W):
        for y in range(H):
            d = math.sqrt((x - cx2) ** 2 + (y - cy2) ** 2)
            if d < rg2:
                t = (1 - d / rg2) ** 3
                o = px[x, y]
                px[x, y] = (
                    int(o[0] * (1 - t) + 0x1A * t),
                    int(o[1] * (1 - t) + 0x3C * t),
                    int(o[2] * (1 - t) + 0x8A * t),
                )

    # Subtle noise
    for x in range(0, W, 3):
        for y in range(0, H, 3):
            n = random.randint(-6, 6)
            o = px[x, y]
            px[x, y] = (
                max(0, min(255, o[0] + n)),
                max(0, min(255, o[1] + n)),
                max(0, min(255, o[2] + n)),
            )

    # Geometric diagonal lines
    for i in range(8):
        x0 = W - 300 - i * 40
        y0 = 0
        x1 = x0 + 200
        y1 = 300
        alpha = 15 + i * 3
        c = (alpha, alpha + 20, alpha + 40)
        draw.line([(x0, y0), (x1, y1)], fill=c, width=1)

    draw.line([(0, 580), (W, 580)], fill=(0x2A, 0x2E, 0x3A), width=1)
    draw.line([(0, 585), (W, 585)], fill=(0x3A, 0x2E, 0x5A), width=1)

    # Circle decorations
    for cx_c, cy_c, r_c, alpha_c in [
        (W - 80, 80, 120, 0.06),
        (100, H - 100, 80, 0.04),
        (W - 200, H - 50, 60, 0.05),
    ]:
        for x in range(max(0, cx_c - r_c), min(W, cx_c + r_c)):
            for y in range(max(0, cy_c - r_c), min(H, cy_c + r_c)):
                d = math.sqrt((x - cx_c) ** 2 + (y - cy_c) ** 2)
                if d < r_c:
                    t = alpha_c * (1 - d / r_c)
                    o = px[x, y]
                    px[x, y] = (
                        int(o[0] * (1 - t) + 0x8A * t),
                        int(o[1] * (1 - t) + 0x6C * t),
                        int(o[2] * (1 - t) + 0xFE * t),
                    )

    # Dots grid
    for x in range(80, W - 80, 60):
        for y in range(500, 560, 30):
            nx = random.randint(-2, 2)
            ny = random.randint(-2, 2)
            alpha = random.randint(15, 30)
            draw.ellipse(
                [(x + nx, y + ny), (x + nx + 3, y + ny + 3)],
                fill=(alpha, alpha + 10, alpha + 20),
            )

    # Bottom gradient bar
    for y in range(H - 8, H):
        for x in range(W):
            ratio = x / W
            r = int(0xFF * (1 - ratio) + 0x7C * ratio)
            g = int(0x6B * (1 - ratio) + 0x3A * ratio)
            b = int(0x35 * (1 - ratio) + 0xED * ratio)
            px[x, y] = (r, g, b)

    # Thin border frame
    for y in range(H):
        px[0, y] = (0x1A, 0x1E, 0x2A)
        px[W - 1, y] = (0x1A, 0x1E, 0x2A)
    for x in range(W):
        px[x, 0] = (0x1A, 0x1E, 0x2A)
        px[x, H - 1] = (0x1A, 0x1E, 0x2A)


def generate_cover(title, subtitle, tag, date_str, reading_info, footer, output_path):
    """Generate a 1200x675 cover image with the given text content.

    Args:
        title: Main title (use \\n to split lines manually; otherwise auto-split)
        subtitle: Subtitle below the title
        tag: Small tag label top-left (e.g. 'EVENING DIGEST')
        date_str: Date string (e.g. '2026 / 04 / 27')
        reading_info: Meta line below date (e.g. '深度解读 · 约 1,200 字')
        footer: Bottom info line (e.g. '每晚 21:30 与你一起回顾这一天')
        output_path: Where to save the PNG
    """
    img = Image.new('RGB', (W, H), BASE)
    draw = ImageDraw.Draw(img)
    px = img.load()

    build_background(img, draw, px)

    # ── Fonts ──
    f68c = ImageFont.truetype(FCJK, 68)
    f68l = ImageFont.truetype(FLATB, 68)
    f48c = ImageFont.truetype(FCJK, 48)
    f48l = ImageFont.truetype(FLATB, 48)
    f20c = ImageFont.truetype(FCJK, 20)
    f20l = ImageFont.truetype(FLAT, 20)
    f16c = ImageFont.truetype(FCJK, 16)
    f16l = ImageFont.truetype(FLAT, 16)
    f14l = ImageFont.truetype(FLAT, 14)

    # ── Accent bar ──
    draw.rectangle([LEFT - 20, 120, LEFT - 16, 320], fill=ACCENT)
    draw.ellipse([(LEFT - 22, 110), (LEFT - 14, 118)], fill=ACCENT)

    # ── Tag line ──
    draw_text(draw, (LEFT, 100), tag,
              ACCENT, ImageFont.truetype(FCJK, 16), ImageFont.truetype(FLAT, 16))

    # ── Main title (handle line breaks) ──
    title_lines = title.split('\\n') if '\\n' in title else [title]
    # If single line and too long (>10 chars for CJK), try to split
    if len(title_lines) == 1 and len(title) > 10:
        mid = len(title) // 2
        # Prefer splitting at spaces or natural breaks
        for sep in [' ', '|', '，', '、', '的']:
            idx = title.rfind(sep, mid - 3, mid + 4)
            if idx > 0:
                mid = idx + 1
                break
        title_lines = [title[:mid], title[mid:]]

    TITLE_FONT_C = f68c if len(title_lines) <= 2 else f48c
    TITLE_FONT_L = f68l if len(title_lines) <= 2 else f48l

    for i, line in enumerate(title_lines):
        y_pos = 135 + i * 80 if len(title_lines) <= 2 else 120 + i * 55
        draw_text(draw, (LEFT, y_pos), line, LIGHT, TITLE_FONT_C, TITLE_FONT_L)

    # ── Gradient underline ──
    UNDERLINE_Y = 310 if len(title_lines) <= 2 else 120 + len(title_lines) * 55 + 10
    for x in range(LEFT, LEFT + 240):
        ratio = (x - LEFT) / 240.0
        r = int(0xFF * (1 - ratio) + 0x7C * ratio)
        g = int(0x6B * (1 - ratio) + 0x3A * ratio)
        b = int(0x35 * (1 - ratio) + 0xED * ratio)
        for y in range(UNDERLINE_Y, UNDERLINE_Y + 4):
            if 0 <= x < W and 0 <= y < H:
                px[x, y] = (r, g, b)

    # ── Subtitle ──
    SUB_Y = UNDERLINE_Y + 45
    draw_text(draw, (LEFT, SUB_Y), subtitle, MID, f20c, f20l)

    # ── Date ──
    DATE_Y = SUB_Y + 60
    draw_text(draw, (LEFT, DATE_Y), date_str, MID, f16c, f16l)

    draw.line([(LEFT, DATE_Y + 35), (LEFT + 60, DATE_Y + 35)], fill=ACCENT, width=2)

    # ── Reading info ──
    draw_text(draw, (LEFT, DATE_Y + 55), reading_info, DIM, f16c, f14l)

    # ── Right side: day number watermark ──
    day_num = _extract_day(date_str)
    f_big = ImageFont.truetype(FLATB, 200)
    draw.text((W - 280, 80), day_num, fill=(0x2A, 0x2E, 0x4A), font=f_big)

    # ── Footer ──
    draw_text(draw, (LEFT, 605), footer, DIM, f16c, f14l)

    # ── Save ──
    img.save(output_path)
    size_kb = os.path.getsize(output_path) / 1024
    print(f'OK: {output_path} ({size_kb:.1f} KB)')


def _extract_day(date_str):
    """Extract the day number from a date string like '2026 / 04 / 27'."""
    import re
    nums = re.findall(r'\d+', date_str)
    if len(nums) >= 3:
        return nums[2]
    return '??'


def main():
    today = datetime.now()
    default_date = today.strftime('%Y / %m / %d')

    parser = argparse.ArgumentParser(
        description='Generate a 1200x675 WeChat cover image.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --title "AI 圈沸腾的一周" --output cover.png
  %(prog)s --title "第一行\\n第二行" --tag "MORNING BRIEF" --subtitle "副标题" --output cover.png
  %(prog)s --title "今天热点" --date "2026 / 04 / 27" --reading-time "约 800 字" --output cover.png
        """,
    )
    parser.add_argument('--title', required=True, help='Main title. Use \\\\n to split lines.')
    parser.add_argument('--subtitle', default='', help='Subtitle below the title.')
    parser.add_argument('--tag', default='EVENING DIGEST', help='Small tag label (default: EVENING DIGEST).')
    parser.add_argument('--date', default=default_date, help=f'Date string (default: "{default_date}").')
    parser.add_argument('--reading-time', default='深度解读', help='Meta text below date (default: 深度解读).')
    parser.add_argument('--footer', default='每晚 21:30 与你一起回顾这一天', help='Bottom footer text.')
    parser.add_argument('--output', '-o', required=True, help='Output PNG file path.')

    args = parser.parse_args()

    generate_cover(
        title=args.title,
        subtitle=args.subtitle,
        tag=args.tag,
        date_str=args.date,
        reading_info=args.reading_time,
        footer=args.footer,
        output_path=args.output,
    )


if __name__ == '__main__':
    main()
