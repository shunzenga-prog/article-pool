# -*- coding: utf-8 -*-
"""Professional cover image generator for WeChat articles.

Two modes:
  auto (default): OG image -> Brave Search -> Unsplash -> geometric fallback
  geometric:      abstract 8-theme design (original behavior)

Usage:
  python3 gen_cover.py --title "title" --output cover.png
  python3 gen_cover.py --title "title" --article article.html --output cover.png
  python3 gen_cover.py --title "title" --mode geometric --output cover.png
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os, math, random, argparse, hashlib, json, re, sys
from datetime import datetime
from pathlib import Path
from io import BytesIO
from urllib.parse import quote

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

W, H = 1200, 675
LEFT = 80
FCJK = '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf'
FLAT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FLATB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

SCRIPTS_DIR = Path(__file__).resolve().parent
THEMES_FILE = SCRIPTS_DIR / 'gen_cover_themes.json'
PROJECT_ROOT = SCRIPTS_DIR.parent

def load_themes():
    with open(THEMES_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_env(key):
    """Load a value from config/.env if present."""
    env_file = PROJECT_ROOT / 'config' / '.env'
    if not env_file.exists():
        return None
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith(f'{key}='):
                return line.split('=', 1)[1].strip().strip('"').strip("'")
    return None

# ── Image sourcing ──

def extract_urls(text):
    """Extract http/https URLs from article content."""
    return re.findall(r'https?://[^\s<>"\']+', text)

def fetch_og_image(url, timeout=8):
    """Try to extract og:image from a webpage."""
    if not HAS_REQUESTS:
        return None
    try:
        r = requests.get(url, timeout=timeout, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; ArticlePool/1.0)'
        })
        if r.status_code != 200:
            return None
        # Quick regex for og:image (avoid full HTML parse)
        m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', r.text)
        if not m:
            m = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', r.text)
        if not m:
            # Try twitter:image
            m = re.search(r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']', r.text)
        if m:
            img_url = m.group(1)
            if img_url.startswith('//'):
                img_url = 'https:' + img_url
            elif img_url.startswith('/'):
                from urllib.parse import urljoin
                img_url = urljoin(url, img_url)
            return download_image(img_url)
    except Exception:
        pass
    return None

def fetch_og_images_from_article(content, max_urls=3):
    """Given article HTML/text, find URLs and try to get their OG images."""
    urls = extract_urls(content)
    images = []
    for url in urls[:max_urls]:
        # Skip image URLs, only try article/news pages
        if re.search(r'\.(jpg|jpeg|png|gif|webp|svg)(\?|$)', url, re.I):
            continue
        img = fetch_og_image(url)
        if img:
            images.append(img)
    return images

def search_brave_images(keywords, api_key, count=5):
    """Search Brave for images matching keywords."""
    if not HAS_REQUESTS:
        return None
    try:
        query = ' '.join(keywords[:4]) if keywords else 'technology AI'
        r = requests.get(
            'https://api.search.brave.com/res/v1/images/search',
            params={'q': query, 'count': count, 'safesearch': 'strict'},
            headers={
                'Accept': 'application/json',
                'Accept-Encoding': 'gzip',
                'X-Subscription-Token': api_key,
            },
            timeout=10,
        )
        if r.status_code != 200:
            return None
        data = r.json()
        results = data.get('results', [])
        if not results:
            return None
        # Pick a random result from top results
        idx = random.randint(0, min(len(results)-1, count-1))
        img_url = results[idx].get('properties', {}).get('url') or results[idx].get('url')
        if img_url:
            return download_image(img_url)
    except Exception:
        pass
    return None

def fetch_unsplash_random(keywords):
    """Get a random Unsplash photo matching keywords (free, no API key)."""
    if not HAS_REQUESTS:
        return None
    try:
        query = ','.join(keywords[:3]) if keywords else 'technology'
        url = f'https://source.unsplash.com/1200x675/?{quote(query)}'
        r = requests.get(url, timeout=15, headers={'User-Agent': 'ArticlePool/1.0'})
        if r.status_code == 200 and len(r.content) > 1000:
            return BytesIO(r.content)
    except Exception:
        pass
    return None

def download_image(url, timeout=12):
    """Download an image from URL, return BytesIO or None."""
    if not HAS_REQUESTS:
        return None
    try:
        r = requests.get(url, timeout=timeout, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; ArticlePool/1.0)'
        })
        if r.status_code == 200 and len(r.content) > 500:
            return BytesIO(r.content)
    except Exception:
        pass
    return None

def get_background_image(title, keywords, article_content=None):
    """Four-tier fallback: OG images -> Brave -> Unsplash -> None (geometric).
    Returns (PIL.Image, source_name) or (None, None)."""
    # Tier 1: OG images from article URLs
    if article_content:
        og_images = fetch_og_images_from_article(article_content)
        if og_images:
            try:
                img = Image.open(og_images[0]).convert('RGB')
                print(f'  bg: OG image from article link')
                return img, 'og'
            except Exception:
                pass

    # Tier 2: Brave Image Search
    brave_key = load_env('BRAVE_API_KEY')
    if brave_key:
        img_data = search_brave_images(keywords, brave_key)
        if img_data:
            try:
                img = Image.open(img_data).convert('RGB')
                print(f'  bg: Brave Image Search')
                return img, 'brave'
            except Exception:
                pass

    # Tier 3: Unsplash
    img_data = fetch_unsplash_random(keywords)
    if img_data:
        try:
            img = Image.open(img_data).convert('RGB')
            print(f'  bg: Unsplash')
            return img, 'unsplash'
        except Exception:
            pass

    # Tier 4: geometric fallback
    return None, None

# ── Geometric theme system (unchanged from original) ──

def select_theme(title, themes):
    h = hashlib.md5(title.encode()).digest()[0]
    names = list(themes.keys())
    return themes[names[h % len(names)]]

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

def _tuple(c):
    return tuple(c)

def build_geometric_background(img, draw, px, theme):
    g1, g2 = theme["glow1"], theme["glow2"]
    LINEC = _tuple(theme["line_color"])

    for x in range(W):
        for y in range(H):
            d = math.sqrt((x - g1["cx"])**2 + (y - g1["cy"])**2)
            if d < g1["r"]:
                t = (1 - d/g1["r"])**g1["power"]
                o = px[x, y]
                rgb = g1["rgb"]
                px[x, y] = (int(o[0]*(1-t)+rgb[0]*t), int(o[1]*(1-t)+rgb[1]*t), int(o[2]*(1-t)+rgb[2]*t))
    for x in range(W):
        for y in range(H):
            d = math.sqrt((x - g2["cx"])**2 + (y - g2["cy"])**2)
            if d < g2["r"]:
                t = (1 - d/g2["r"])**g2["power"]
                o = px[x, y]
                rgb = g2["rgb"]
                px[x, y] = (int(o[0]*(1-t)+rgb[0]*t), int(o[1]*(1-t)+rgb[1]*t), int(o[2]*(1-t)+rgb[2]*t))
    for x in range(0, W, 3):
        for y in range(0, H, 3):
            n = random.randint(-6, 6)
            o = px[x, y]
            px[x, y] = (max(0,min(255,o[0]+n)), max(0,min(255,o[1]+n)), max(0,min(255,o[2]+n)))
    for sx, sy, ex, ey in theme["line_angles"]:
        for offset in range(0, 320, 40):
            draw.line([(sx-offset, sy), (sx+ex-offset, sy+ey)], fill=LINEC, width=1)
    draw.line([(0,580),(W,580)], fill=_tuple(theme["divider_color"]), width=1)
    draw.line([(0,585),(W,585)], fill=_tuple(theme["divider2_color"]), width=1)
    for cx_c, cy_c, r_c in theme["circle_positions"]:
        CC = _tuple(theme["circle_color"])
        for x in range(max(0,cx_c-r_c), min(W,cx_c+r_c)):
            for y in range(max(0,cy_c-r_c), min(H,cy_c+r_c)):
                d = math.sqrt((x-cx_c)**2 + (y-cy_c)**2)
                if d < r_c:
                    alpha = random.uniform(0.03, 0.08)
                    t = alpha*(1-d/r_c)
                    o = px[x, y]
                    px[x, y] = (int(o[0]*(1-t)+CC[0]*t), int(o[1]*(1-t)+CC[1]*t), int(o[2]*(1-t)+CC[2]*t))
    dr = theme["dot_range"]
    DC = _tuple(theme["dot_color_base"])
    for sx in range(dr[0][0], dr[0][1], 60):
        for sy in range(dr[1][0], dr[1][1], 30):
            nx, ny = random.randint(-2,2), random.randint(-2,2)
            draw.ellipse([(sx+nx,sy+ny),(sx+nx+3,sy+ny+3)], fill=DC)
    GS, GE = _tuple(theme["gradient_start"]), _tuple(theme["gradient_end"])
    for y in range(H-8, H):
        for x in range(W):
            ratio = x/W
            px[x, y] = (int(GS[0]*(1-ratio)+GE[0]*ratio), int(GS[1]*(1-ratio)+GE[1]*ratio), int(GS[2]*(1-ratio)+GE[2]*ratio))
    FC = _tuple(theme["base"])
    for y in range(H):
        px[0,y] = (FC[0]+10,FC[1]+10,FC[2]+10)
        px[W-1,y] = (FC[0]+10,FC[1]+10,FC[2]+10)
    for x in range(W):
        px[x,0] = (FC[0]+10,FC[1]+10,FC[2]+10)
        px[x,H-1] = (FC[0]+10,FC[1]+10,FC[2]+10)

# ── Dark gradient overlay for photo backgrounds ──

def apply_dark_overlay(img, px):
    """Apply dark semi-transparent gradient overlay for text readability."""
    # Main dark vignette
    for x in range(W):
        for y in range(H):
            o = px[x, y]
            # Distance-based darkening (stronger at edges)
            edge_factor = 1.0
            if x < 200:
                edge_factor = 0.4 + 0.6 * (x / 200)
            if x > W - 200:
                edge_factor = min(edge_factor, 0.4 + 0.6 * ((W - x) / 200))
            if y > H - 150:
                edge_factor = min(edge_factor, 0.3 + 0.7 * ((H - y) / 150))

            dark_r = int(o[0] * 0.45 * edge_factor)
            dark_g = int(o[1] * 0.40 * edge_factor)
            dark_b = int(o[2] * 0.50 * edge_factor)

            px[x, y] = (
                max(0, min(255, dark_r)),
                max(0, min(255, dark_g)),
                max(0, min(255, dark_b)),
            )

    # Bottom gradient bar (stronger darkening)
    for y in range(H - 120, H):
        for x in range(W):
            o = px[x, y]
            ratio = (y - (H - 120)) / 120.0
            factor = 0.3 + 0.7 * ratio
            px[x, y] = (
                int(o[0] * (1 - factor * 0.7)),
                int(o[1] * (1 - factor * 0.7)),
                int(o[2] * (1 - factor * 0.6)),
            )


def generate_cover(title, subtitle, tag, date_str, reading_info, footer, output_path,
                   mode='auto', theme_name=None, article_path=None, keywords=None):
    """Generate a 1200x675 cover image.

    mode='auto': intelligent background (OG->Brave->Unsplash->geometric)
    mode='geometric': abstract 8-theme design
    """
    themes = load_themes()

    # Determine keywords for image search
    if keywords is None:
        keywords = []
    if not keywords:
        # Simple keyword extraction from title
        kw_text = title.lower()
        kw_map = ['ai', 'gpt', 'openai', 'chip', 'code', 'tutorial', 'stock', 'business', 'tech']
        keywords = [k for k in kw_map if k in kw_text]
        if not keywords:
            keywords = ['technology', 'digital']

    # Read article content if path provided
    article_content = None
    if article_path and os.path.exists(article_path):
        try:
            with open(article_path, 'r', encoding='utf-8') as f:
                article_content = f.read()
        except Exception:
            pass

    bg_source = 'geometric'
    photo_bg = None

    if mode == 'auto':
        photo_bg, bg_source = get_background_image(title, keywords, article_content)

    if photo_bg:
        # Resize/crop to cover dimensions
        photo_bg = photo_bg.resize((W, H), Image.LANCZOS)
        img = photo_bg
        draw = ImageDraw.Draw(img)
        px = img.load()
        apply_dark_overlay(img, px)

        # Use light text colors for photo backgrounds
        ACCENT = (0xFF, 0x8C, 0x42)  # warm orange for visibility
        LIGHT = (0xF5, 0xF0, 0xEC)
        MID = (0xCC, 0xC8, 0xC4)
        DIM = (0x99, 0x95, 0x90)
        WM = (0x33, 0x30, 0x2D)
    else:
        # Geometric mode
        theme = themes[theme_name] if theme_name and theme_name in themes else select_theme(title, themes)
        img = Image.new('RGB', (W, H), _tuple(theme["base"]))
        draw = ImageDraw.Draw(img)
        px = img.load()
        build_geometric_background(img, draw, px, theme)

        ACCENT = _tuple(theme["accent"])
        LIGHT = (0xE8, 0xE8, 0xF0)
        MID = (0x94, 0x94, 0xB8)
        DIM = (0x64, 0x64, 0x88)
        WM = _tuple(theme["watermark_color"])
        theme_name = theme["name"]

    # ── Common text layout ──
    f68c = ImageFont.truetype(FCJK, 68); f68l = ImageFont.truetype(FLATB, 68)
    f48c = ImageFont.truetype(FCJK, 48); f48l = ImageFont.truetype(FLATB, 48)
    f20c = ImageFont.truetype(FCJK, 20); f20l = ImageFont.truetype(FLAT, 20)
    f16c = ImageFont.truetype(FCJK, 16); f16l = ImageFont.truetype(FLAT, 16)
    f14l = ImageFont.truetype(FLAT, 14)

    # Accent bar
    bar_h = 200 if photo_bg else 200
    draw.rectangle([LEFT-20, 120, LEFT-16, 120+bar_h], fill=ACCENT)
    draw.ellipse([(LEFT-22, 110), (LEFT-14, 118)], fill=ACCENT)

    # Tag
    draw_text(draw, (LEFT, 100), tag, ACCENT, ImageFont.truetype(FCJK, 16), ImageFont.truetype(FLAT, 16))

    # Title
    title_lines = title.split('\\n') if '\\n' in title else [title]
    if len(title_lines) == 1 and len(title) > 10:
        mid = len(title)//2
        for sep in [' ','|',',',':','-']:
            idx = title.rfind(sep, mid-3, mid+4)
            if idx > 0: mid = idx+1; break
        title_lines = [title[:mid], title[mid:]]

    TFC = f68c if len(title_lines)<=2 else f48c
    TFL = f68l if len(title_lines)<=2 else f48l
    for i, line in enumerate(title_lines):
        y_pos = 135 + i*80 if len(title_lines)<=2 else 120 + i*55
        # Add text shadow for photo backgrounds
        if photo_bg:
            draw_text(draw, (LEFT+2, y_pos+2), line, (0,0,0), TFC, TFL)
        draw_text(draw, (LEFT, y_pos), line, LIGHT, TFC, TFL)

    # Underline
    UY = 310 if len(title_lines)<=2 else 120+len(title_lines)*55+10
    if not photo_bg:
        theme_for_underline = themes[theme_name] if theme_name and theme_name in themes else select_theme(title, themes)
        GS = _tuple(theme_for_underline["gradient_start"])
        GE = _tuple(theme_for_underline["gradient_end"])
    else:
        GS, GE = ACCENT, (0xCC, 0x88, 0x44)
    for x in range(LEFT, LEFT+240):
        ratio = (x-LEFT)/240.0
        r = int(GS[0]*(1-ratio)+GE[0]*ratio)
        g = int(GS[1]*(1-ratio)+GE[1]*ratio)
        b = int(GS[2]*(1-ratio)+GE[2]*ratio)
        for y in range(UY, UY+4):
            if 0<=x<W and 0<=y<H: px[x,y] = (r,g,b)

    SY = UY+45
    draw_text(draw, (LEFT,SY), subtitle, MID, f20c, f20l)
    DY = SY+60
    draw_text(draw, (LEFT,DY), date_str, MID, f16c, f16l)
    draw.line([(LEFT,DY+35),(LEFT+60,DY+35)], fill=ACCENT, width=2)
    draw_text(draw, (LEFT,DY+55), reading_info, DIM, f16c, f14l)

    # Day number watermark
    nums = re.findall(r'\d+', date_str)
    day_num = nums[2] if len(nums)>=3 else '??'
    fb = ImageFont.truetype(FLATB, 200)
    draw.text((W-280, 80), day_num, fill=WM, font=fb)

    # Source badge
    ft = ImageFont.truetype(FLAT, 11)
    badge_text = bg_source if photo_bg else (theme_name if 'theme_name' in dir() else 'geometric')
    bb = draw.textbbox((0,0), badge_text, font=ft)
    bw = bb[2]-bb[0]+12
    draw.rectangle([W-bw-20, 592, W-20, 610], fill=WM)
    draw.text((W-bw-14, 593), badge_text, fill=DIM, font=ft)

    draw_text(draw, (LEFT, 605), footer, DIM, f16c, f14l)
    img.save(output_path)
    src_label = f'bg:{bg_source}' if photo_bg else f'theme:{theme_name}'
    print(f'OK: {output_path} ({os.path.getsize(output_path)/1024:.1f} KB) {src_label}')

def list_themes():
    themes = load_themes()
    print("Available themes (geometric mode):")
    for k, t in themes.items():
        c = t["accent"]
        print(f"  {k:12s} - {t['name']}  (#{c[0]:02x}{c[1]:02x}{c[2]:02x})")

def main():
    today = datetime.now()
    dd = today.strftime('%Y / %m / %d')
    themes = load_themes()

    p = argparse.ArgumentParser(description='Generate 1200x675 WeChat cover (auto/geometric).')
    p.add_argument('--title', help='Main title.')
    p.add_argument('--subtitle', default='')
    p.add_argument('--tag', default='EVENING DIGEST')
    p.add_argument('--date', default=dd)
    p.add_argument('--reading-time', default='深度解读')
    p.add_argument('--footer', default='每晚 21:30 与你一起回顾这一天')
    p.add_argument('--output', '-o', help='Output PNG file path.')
    p.add_argument('--mode', choices=['auto', 'geometric'], default='auto',
                   help='Background mode: auto (OG->Brave->Unsplash->geometric) or geometric (default: auto)')
    p.add_argument('--theme', choices=list(themes.keys()), help='Force geometric theme.')
    p.add_argument('--article', help='Article HTML/text file for OG image extraction.')
    p.add_argument('--keywords', help='Comma-separated keywords for image search.')
    p.add_argument('--list-themes', action='store_true', help='List themes and exit.')

    args = p.parse_args()
    if args.list_themes:
        list_themes()
        return
    if not args.title or not args.output:
        p.error("--title and --output are required for generation")

    keywords = [k.strip() for k in args.keywords.split(',')] if args.keywords else None

    generate_cover(
        title=args.title,
        subtitle=args.subtitle,
        tag=args.tag,
        date_str=args.date,
        reading_info=args.reading_time,
        footer=args.footer,
        output_path=args.output,
        mode=args.mode,
        theme_name=args.theme,
        article_path=args.article,
        keywords=keywords,
    )

if __name__ == '__main__':
    main()
