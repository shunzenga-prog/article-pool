# -*- coding: utf-8 -*-
"""Professional cover image generator for WeChat articles.

Two modes:
  auto (default): OG → Pexels → AI-gen(quality gate+retry) → Unsplash → Brave → geometric
  geometric:      abstract 8-theme design (original behavior)

Usage:
  python3 gen_cover.py --title "title" --output cover.png
  python3 gen_cover.py --title "title" --article article.html --output cover.png
  python3 gen_cover.py --title "title" --mode geometric --output cover.png
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os, math, random, argparse, hashlib, json, re, sys, time, tempfile
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

# Font detection via unified capture.fonts module (single source of truth)
from capture.fonts import get_font_manager as _get_font_manager
_fm = _get_font_manager()
FCJK = _fm.cjk_path
FLAT = _fm.latin_path
FLATB = _fm.latinb_path

# Validate CJK font availability — geometric mode works without it, but
# auto mode (photo background) needs CJK for title/subtitle rendering.
if not FCJK:
    print("⚠️  未检测到 CJK 字体（中文渲染将不可用）", file=sys.stderr)
    print("   Windows: 确保 C:\\Windows\\Fonts\\msyh.ttc 存在", file=sys.stderr)
    print("   macOS:   确保系统自带苹方字体", file=sys.stderr)
    print("   Linux:   sudo apt install fonts-noto-cjk", file=sys.stderr)
    print("   封面生成将以 geometric 模式继续（不依赖 CJK 文本渲染）", file=sys.stderr)
    # Use PIL default as last resort — will produce mojibake for CJK but won't crash
    FCJK = FLAT or ""
FLAT = FLAT or FCJK
FLATB = FLATB or FLAT or FCJK

from paths import SCRIPTS_DIR as _SCRIPTS_DIR, PROJECT_ROOT as _PROJECT_ROOT, USED_IMAGES_FILE, get_env

SCRIPTS_DIR = _SCRIPTS_DIR
PROJECT_ROOT = _PROJECT_ROOT
THEMES_FILE = SCRIPTS_DIR / 'gen_cover_themes.json'

try:
    from preferences import get_prefs as _get_prefs
    _cover_prefs = _get_prefs()
except Exception:
    _cover_prefs = {}

# ── Visual diversity: random style modifiers to avoid repetitive search results ──
_VISUAL_MODIFIERS = [
    # Composition & angle
    "wide angle", "close up macro", "aerial view", "low angle", "dutch angle",
    "symmetrical composition", "leading lines", "rule of thirds",
    # Lighting & mood
    "golden hour", "blue hour", "neon lights", "soft diffused light", "dramatic shadows",
    "backlit silhouette", "moody atmosphere", "bright and airy", "dark and moody",
    # Color palette
    "warm tones", "cool blue tones", "monochromatic", "vibrant colors", "muted pastels",
    "high contrast", "desaturated", "duotone",
    # Style & texture
    "minimalist", "futuristic abstract", "brutalist architecture", "organic texture",
    "glass and metal", "matte finish", "glossy surface", "grainy film texture",
    # Environment context
    "urban background", "nature backdrop", "studio lighting", "industrial setting",
    "office environment", "outdoor natural light", "laboratory setting",
    # Artistic references
    "cyberpunk aesthetic", "corporate clean style", "editorial photography",
    "fine art photography", "documentary style", "architectural photography",
]

def get_random_modifier(seed_text="", count=2):
    """Return 1-2 random visual modifiers, deterministically varied by seed_text."""
    rng = random.Random(hashlib.md5(seed_text.encode()).digest() if seed_text else None)
    n = rng.randint(1, min(count, len(_VISUAL_MODIFIERS)))
    return rng.sample(_VISUAL_MODIFIERS, n)

def augment_query(base_query, seed_text=""):
    """Augment a search query with random visual modifiers for diversity."""
    modifiers = get_random_modifier(seed_text)
    # Pick 1-2 modifiers and append
    return f"{base_query} {', '.join(modifiers)}"

# ── Image deduplication ──

def load_used_images(max_age_days=30):
    """Load recently used image URLs. Returns set of URLs."""
    if not USED_IMAGES_FILE.exists():
        return set()
    try:
        with open(USED_IMAGES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        return set()

    # Expire old entries
    cutoff = time.time() - max_age_days * 86400
    fresh = {url for url, ts in data.items() if ts > cutoff}
    if len(fresh) != len(data):
        _save_used_images(fresh)
    return fresh

def _save_used_images(url_set):
    """Save used image URLs with timestamps."""
    USED_IMAGES_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {url: time.time() for url in url_set}
    try:
        with open(USED_IMAGES_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f)
    except Exception:
        pass

def mark_image_used(img_url):
    """Record an image URL as used."""
    if not img_url:
        return
    used = load_used_images()
    used.add(img_url)
    _save_used_images(used)

def is_image_duplicate(img_url):
    """Check if image URL was recently used."""
    if not img_url:
        return False
    return img_url in load_used_images()

def load_themes():
    with open(THEMES_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

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

def search_brave_images(keywords, api_key, seed_text="", count=8):
    """Search Brave for images matching keywords, with diversity & dedup."""
    if not HAS_REQUESTS:
        return None
    try:
        base_query = ' '.join(keywords[:4]) if keywords else 'technology AI'
        query = augment_query(base_query, seed_text)
        # Add result offset to skip first page sometimes
        offset = random.randint(0, 15) if seed_text else 0

        r = requests.get(
            'https://api.search.brave.com/res/v1/images/search',
            params={'q': query, 'count': count, 'safesearch': 'strict', 'offset': offset},
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

        # Try up to 5 random picks, skip duplicates
        random.shuffle(results)
        for img in results[:min(len(results), 8)]:
            img_url = img.get('properties', {}).get('url') or img.get('url')
            if img_url and not is_image_duplicate(img_url):
                result = download_image(img_url)
                if result:
                    mark_image_used(img_url)
                    return result
        print(f'  brave: all {len(results)} results were duplicates, retrying with new query')
        # Fallback: retry with different modifiers
        query2 = augment_query(base_query, seed_text + 'retry')
        r2 = requests.get(
            'https://api.search.brave.com/res/v1/images/search',
            params={'q': query2, 'count': count, 'safesearch': 'strict', 'offset': offset + count},
            headers={
                'Accept': 'application/json',
                'Accept-Encoding': 'gzip',
                'X-Subscription-Token': api_key,
            },
            timeout=10,
        )
        if r2.status_code == 200:
            results2 = r2.json().get('results', [])
            for img in results2:
                img_url = img.get('properties', {}).get('url') or img.get('url')
                if img_url:
                    result = download_image(img_url)
                    if result:
                        mark_image_used(img_url)
                        return result
    except Exception:
        pass
    return None

def fetch_unsplash_random(keywords, seed_text=""):
    """Get a random Unsplash photo with diversity modifiers and dedup."""
    if not HAS_REQUESTS:
        return None
    try:
        base_query = ','.join(keywords[:3]) if keywords else 'technology'
        query = augment_query(base_query, seed_text).replace(',', ' ')
        # Try Unsplash search endpoint with pagination
        page = random.randint(1, 5) if seed_text else 1
        url = f'https://unsplash.com/napi/search/photos?query={quote(query)}&per_page=12&page={page}'
        r = requests.get(url, timeout=15, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; ArticlePool/1.0)',
            'Accept': 'application/json',
        })
        if r.status_code == 200:
            data = r.json()
            results = data.get('results', [])
            if results:
                random.shuffle(results)
                for photo in results:
                    img_url = photo.get('urls', {}).get('regular')
                    if img_url and not is_image_duplicate(img_url):
                        result = download_image(img_url)
                        if result:
                            mark_image_used(img_url)
                            return result
        # Fallback: source.unsplash.com with varied query
        fallback_query = augment_query(base_query, seed_text + 'fb')
        fallback_url = f'https://source.unsplash.com/1200x675/?{quote(fallback_query)}'
        r2 = requests.get(fallback_url, timeout=15, headers={'User-Agent': 'ArticlePool/1.0'})
        if r2.status_code == 200 and len(r2.content) > 1000:
            return BytesIO(r2.content)
    except Exception:
        pass
    return None

def search_pexels(keywords, api_key, seed_text="", count=8):
    """Search Pexels for images with diversity modifiers and dedup."""
    if not HAS_REQUESTS or not api_key:
        return None
    try:
        base_query = ' '.join(keywords[:3]) if keywords else 'technology'
        query = augment_query(base_query, seed_text)
        page = random.randint(1, 6) if seed_text else 1

        r = requests.get(
            'https://api.pexels.com/v1/search',
            params={'query': query, 'per_page': count, 'page': page, 'orientation': 'landscape', 'size': 'large'},
            headers={'Authorization': api_key},
            timeout=15,
        )
        if r.status_code != 200:
            print(f'  pexels: HTTP {r.status_code}')
            return None
        data = r.json()
        photos = data.get('photos', [])
        if not photos:
            # Retry without modifiers to broaden reach
            r2 = requests.get(
                'https://api.pexels.com/v1/search',
                params={'query': base_query, 'per_page': count, 'page': page + 2, 'orientation': 'landscape', 'size': 'large'},
                headers={'Authorization': api_key},
                timeout=15,
            )
            if r2.status_code == 200:
                photos = r2.json().get('photos', [])
        if not photos:
            print(f'  pexels: no results for "{query}"')
            return None

        random.shuffle(photos)
        for photo in photos:
            img_url = photo.get('src', {}).get('large2x') or photo.get('src', {}).get('large')
            if img_url and not is_image_duplicate(img_url):
                result = download_image(img_url)
                if result:
                    mark_image_used(img_url)
                    photographer = photo.get('photographer', 'unknown')
                    print(f'  pexels: by {photographer} (page {page})')
                    return result

        # All duplicates, try another page
        r3 = requests.get(
            'https://api.pexels.com/v1/search',
            params={'query': base_query, 'per_page': count, 'page': page + random.randint(3, 8), 'orientation': 'landscape', 'size': 'large'},
            headers={'Authorization': api_key},
            timeout=15,
        )
        if r3.status_code == 200:
            photos3 = r3.json().get('photos', [])
            for photo in photos3:
                img_url = photo.get('src', {}).get('large2x') or photo.get('src', {}).get('large')
                if img_url:
                    result = download_image(img_url)
                    if result:
                        mark_image_used(img_url)
                        print(f'  pexels: by {photo.get("photographer", "?")} (fallback page)')
                        return result
    except Exception as e:
        print(f'  pexels: error - {e}')
    return None

def score_cover_image(img_data: BytesIO) -> tuple:
    """Score AI-generated cover image quality (0-100). Tuned for 1200x675."""
    try:
        img = Image.open(img_data)
        w, h = img.size
        kb = len(img_data.getvalue()) / 1024
        pixel_count = w * h

        issues = []
        deductions = 0

        # 1. File size: 1200x675 photo should be 150-500KB
        if kb < 60:
            deductions += 40
            issues.append(f"tiny({kb:.0f}KB)")
        elif kb < 100:
            deductions += 20
            issues.append(f"small({kb:.0f}KB)")

        # 2. Histogram diversity
        if img.mode in ("RGB", "RGBA"):
            rgb = img.convert("RGB")
            hist = rgb.histogram()
            active_bins = sum(1 for v in hist if v > 0)
            if active_bins < 50:
                deductions += 40
                issues.append("near_uniform")
            elif active_bins < 100:
                deductions += 20
                issues.append("low_variety")

        # 3. Luminosity std dev: flat = bad
        gray = img.convert("L")
        pixels = list(gray.getdata())
        mean = sum(pixels) / len(pixels)
        std = (sum((p - mean) ** 2 for p in pixels) / len(pixels)) ** 0.5
        if std < 15:
            deductions += 30
            issues.append("too_flat")
        elif std < 25:
            deductions += 12
            issues.append("flat")

        score = max(5, 100 - deductions)
        detail = ",".join(issues) if issues else "ok"
        return score, detail
    except Exception:
        return 0, "error"


def generate_ai_background(keywords, title, seed_text="", quality_threshold=50, max_retries=3):
    """Generate an AI image using Pollinations.ai with quality gate + retry."""
    if not HAS_REQUESTS:
        return None
    topic = ' '.join(keywords[:3]) if keywords else 'technology'

    for attempt in range(max_retries):
        modifiers = get_random_modifier((seed_text or title) + str(attempt))

        style_templates = [
            "professional editorial photography, {topic}, {mods}, bright natural lighting, shallow depth of field, light and airy atmosphere, wide angle, negative space on left, 8k photorealistic, no text no watermark",
            "abstract {topic} concept art, {mods}, bright composition, clean light background, left side empty for text, ultra detailed, no text no watermark",
            "{mods} scene about {topic}, documentary photography style, bright natural lighting, rule of thirds, empty left composition, high resolution, no text no watermark",
            "minimalist {topic} illustration, {mods}, light theme, clean and bright design, empty space on left, professional quality, no text no watermark",
        ]
        style = style_templates[random.randint(0, len(style_templates)-1)]
        prompt = style.format(topic=topic, mods=', '.join(modifiers[:2]))

        seed_val = str(random.randint(1, 99999))
        url = f"https://image.pollinations.ai/prompt/{quote(prompt)}"
        params = {'width': 1200, 'height': 675, 'model': 'flux', 'nologo': 'true', 'seed': seed_val}

        try:
            print(f'  ai-gen (attempt {attempt+1}/{max_retries}): "{topic}" + "{modifiers[0]}" (seed={seed_val})...')
            r = requests.get(url, params=params, timeout=120)
            if r.status_code == 200 and len(r.content) > 1000:
                try:
                    img = Image.open(BytesIO(r.content))
                    img.verify()
                except Exception:
                    print(f'  ai-gen: invalid image')
                    continue

                q_score, q_detail = score_cover_image(BytesIO(r.content))
                print(f'  ai-gen: quality {q_score:.0f}/100 ({q_detail})')
                if q_score >= quality_threshold:
                    print(f'  ai-gen: generated ({len(r.content)/1024:.0f} KB)')
                    return BytesIO(r.content)
                if attempt < max_retries - 1:
                    print(f'  ai-gen: below threshold {quality_threshold}, retrying...')
            else:
                print(f'  ai-gen: HTTP {r.status_code}')
        except Exception as e:
            print(f'  ai-gen: error - {e}')
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

def load_local_background_image(image_path):
    """Load a local Agent/Codex-generated background image if available."""
    if not image_path:
        return None, None
    path = Path(image_path)
    if not path.exists():
        print(f'  bg: local background missing: {path}')
        return None, None
    try:
        img = Image.open(path).convert('RGB')
        print(f'  bg: [T0] Agent local background: {path}')
        return img, 'agent-local'
    except Exception as e:
        print(f'  bg: local background invalid - {e}')
        return None, None

def get_background_image(title, keywords, article_content=None):
    """Multi-tier fallback for cover backgrounds:
    Tier 1: OG images from article links
    Tier 2: Pexels API (free, 200 req/hour — needs PEXELS_API_KEY in .env)
    Tier 3: AI-generated image via Pollinations.ai (quality gate + max 3 retries)
    Tier 4: Unsplash search + source.unsplash.com fallback
    Tier 5: Brave Image Search (needs BRAVE_API_KEY in .env)
    Tier 6: None → geometric fallback
    Returns (PIL.Image, source_name) or (None, None)."""
    # Tier 1: OG images from article URLs
    if article_content:
        og_images = fetch_og_images_from_article(article_content)
        if og_images:
            try:
                img = Image.open(og_images[0]).convert('RGB')
                print(f'  bg: [T1] OG image from article link')
                return img, 'og'
            except Exception:
                pass

    # Build a seed for deterministic-but-varied randomization
    seed_text = f"{title}_{datetime.now().strftime('%Y%m%d')}"

    # Tier 2: Pexels API (best free source, real photography)
    pexels_key = get_env('PEXELS_API_KEY')
    if pexels_key:
        img_data = search_pexels(keywords, pexels_key, seed_text)
        if img_data:
            try:
                img = Image.open(img_data).convert('RGB')
                print(f'  bg: [T2] Pexels')
                return img, 'pexels'
            except Exception:
                pass
    else:
        print(f'  bg: [T2] Pexels skipped (no PEXELS_API_KEY in .env)')

    # Tier 3: AI-generated image via Pollinations.ai (creative, unique)
    img_data = generate_ai_background(keywords, title, seed_text)
    if img_data:
        try:
            img = Image.open(img_data).convert('RGB')
            print(f'  bg: [T3] AI-generated (Pollinations.ai)')
            return img, 'ai-gen'
        except Exception:
            pass

    # Tier 4: Unsplash (free, may be rate-limited)
    img_data = fetch_unsplash_random(keywords, seed_text)
    if img_data:
        try:
            img = Image.open(img_data).convert('RGB')
            print(f'  bg: [T4] Unsplash')
            return img, 'unsplash'
        except Exception:
            pass

    # Tier 5: Brave Image Search (needs API key)
    brave_key = get_env('BRAVE_API_KEY')
    if brave_key:
        img_data = search_brave_images(keywords, brave_key, seed_text)
        if img_data:
            try:
                img = Image.open(img_data).convert('RGB')
                print(f'  bg: [T5] Brave Image Search')
                return img, 'brave'
            except Exception:
                pass

    # Tier 6: geometric fallback
    print(f'  bg: [T6] No photo source available, using geometric design')
    return None, None

# ── Geometric theme system (unchanged from original) ──

def select_theme(title, themes):
    """Select a theme deterministically from title hash, with 2x weight on bright themes."""
    bright_names = []
    dark_names = []
    for k, t in themes.items():
        base = t.get("base", [0, 0, 0])
        if sum(base) > 500:
            bright_names.append(k)
        else:
            dark_names.append(k)
    # Triple bright themes for 3x selection probability (~77% bright)
    weighted = bright_names * 3 + dark_names
    h = hashlib.md5(title.encode()).digest()[0]
    return themes[weighted[h % len(weighted)]]

def is_cjk(cp):
    return (0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF or
            0xF900 <= cp <= 0xFAFF or 0x3000 <= cp <= 0x303F or
            0xFF00 <= cp <= 0xFFEF or 0x2000 <= cp <= 0x206F)

def draw_text(draw, xy, text, fill, fcjk, flat):
    x, y = xy
    cjk_ascent, _ = fcjk.getmetrics()
    lat_ascent, _ = flat.getmetrics()
    ascent_delta = cjk_ascent - lat_ascent
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
        adj_y = y - ascent_delta if use_cjk else y
        draw.text((x, adj_y), seg, fill=fill, font=f)
        bbox = draw.textbbox((x, adj_y), seg, font=f)
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

# ── Text backdrop overlay for photo backgrounds ──

def apply_text_backdrop(img, px):
    """Apply a subtle vignette and frame border — cover is pure image, title beside it in feed."""
    W, H = img.size

    # Very subtle edge vignette
    for x in range(W):
        for y in range(H):
            o = px[x, y]
            edge_factor = 1.0
            if x < 60:
                edge_factor = 0.92 + 0.08 * (x / 60)
            if x > W - 60:
                edge_factor = min(edge_factor, 0.92 + 0.08 * ((W - x) / 60))
            if y < 40:
                edge_factor = min(edge_factor, 0.92 + 0.08 * (y / 40))
            if y > H - 40:
                edge_factor = min(edge_factor, 0.92 + 0.08 * ((H - y) / 40))
            if edge_factor < 1.0:
                px[x, y] = (
                    int(o[0] * edge_factor),
                    int(o[1] * edge_factor),
                    int(o[2] * edge_factor),
                )

    # Subtle frame border
    border_color = (70, 75, 85)
    for y in range(H):
        px[0, y] = border_color
        px[W - 1, y] = border_color
    for x in range(W):
        px[x, 0] = border_color
        px[x, H - 1] = border_color


# ── Keyword extraction ──

# Chinese keyword dictionary: domain → representative terms (2-4 chars)
_CJK_KW_DICT = {
    "ai": ["人工智能", "AI", "大模型", "机器学习", "深度学习", "神经网络", "GPT", "OpenAI",
           "ChatGPT", "Claude", "Gemini", "智能体", "AGI", "LLM", "transformer"],
    "chip": ["芯片", "半导体", "GPU", "CPU", "NPU", "算力", "制程", "光刻", "英伟达",
             "NVIDIA", "AMD", "英特尔", "高通", "华为", "昇腾", "寒武纪"],
    "policy": ["规划", "政策", "战略", "十五五", "十四五", "新质生产力", "数字经济",
               "人工智能", "科技", "创新", "产业", "发展", "监管", "立法"],
    "cloud": ["云", "服务器", "数据中心", "SaaS", "PaaS", "容器", "Kubernetes",
              "AWS", "阿里云", "腾讯云", "华为云"],
    "coding": ["编程", "代码", "开发", "开源", "GitHub", "Python", "Rust", "JavaScript",
               "TypeScript", "Go", "Rust", "前端", "后端", "全栈", "框架"],
    "robot": ["机器人", "自动", "驾驶", "无人", "具身智能", "人形机器人", "Figure",
              "特斯拉", "Optimus", "波士顿动力"],
    "science": ["量子", "核聚变", "基因", "蛋白质", "AlphaFold", "材料", "太空",
                "SpaceX", "NASA", "火箭", "卫星", "登月"],
    "business": ["市值", "融资", "IPO", "上市", "股价", "营收", "利润", "裁员",
                 "收购", "投资", "独角兽", "估值"],
    "energy": ["能源", "电池", "光伏", "储能", "固态电池", "锂电", "钠离子",
               "新能源", "碳中和", "碳达峰"],
    "mobile": ["手机", "iPhone", "华为", "小米", "苹果", "Android", "iOS",
               "折叠屏", "卫星通信", "5G", "6G"],
}

_CJK_KW_FLAT = {}
for _domain, _terms in _CJK_KW_DICT.items():
    for _t in _terms:
        _CJK_KW_FLAT[_t.lower()] = _domain


def _strip_html(html_text):
    """Remove HTML tags and return plain text."""
    text = re.sub(r'<(style|script)[^>]*>.*?</\1>', '', html_text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _extract_keywords_from_body(body_text):
    """Extract keywords from article body text by term frequency.

    Returns list of (term, count) sorted by frequency descending, top 15.
    """
    text = body_text.lower()
    tf = {}
    for term in _CJK_KW_FLAT:
        count = text.count(term)
        if count > 0:
            domain = _CJK_KW_FLAT[term]
            # Keep highest count per domain for each term
            tf[term] = (count, domain)
    # Also count EN tech keywords
    en_tech = ["ai", "gpt", "openai", "llm", "api", "gpu", "cpu", "cloud",
               "code", "dev", "app", "data", "web", "security", "ios",
               "android", "chip", "robot", "space", "energy", "battery"]
    for k in en_tech:
        count = text.count(k)
        if count > 0 and k not in tf:
            tf[k] = (count, "tech")
    # Sort by count desc
    sorted_terms = sorted(tf.items(), key=lambda x: -x[1][0])
    return [(term, info[0], info[1]) for term, info in sorted_terms[:15]]


def _extract_keywords(title, subtitle="", body_text=None):
    """Extract search keywords from title/subtitle + optional article body.

    Strategy: title keywords get weight 3, body TF keywords get weight = frequency.
    Merged and ranked by total score, deduped by domain, top 5 returned.
    When body_text is None, falls back to original title-only extraction.
    """
    text = f"{title} {subtitle}".lower()
    title_keywords = {}

    en_tech = ["ai", "gpt", "openai", "llm", "api", "gpu", "cpu", "cloud",
               "code", "dev", "app", "data", "web", "security", "ios",
               "android", "chip", "robot", "space", "energy", "battery"]

    # 1. Title keyword extraction (weight = 3 per match)
    for term, domain in _CJK_KW_FLAT.items():
        if term in text:
            title_keywords[term] = {"score": 3, "domain": domain}

    for k in en_tech:
        if k in text and k not in title_keywords:
            title_keywords[k] = {"score": 3, "domain": "tech"}

    # 2. Body text TF extraction (weight = frequency)
    body_scores = {}
    if body_text:
        body_plain = _strip_html(body_text).lower()
        for term in _CJK_KW_FLAT:
            count = body_plain.count(term)
            if count > 0:
                body_scores[term] = {"score": count, "domain": _CJK_KW_FLAT[term]}
        for k in en_tech:
            count = body_plain.count(k)
            if count > 0 and k not in body_scores:
                body_scores[k] = {"score": count, "domain": "tech"}

    # 3. Merge: title + body scores, dedup by domain (keep highest)
    merged = {}
    for term, info in title_keywords.items():
        merged[term] = info["score"]

    for term, info in body_scores.items():
        combined = info["score"] + title_keywords.get(term, {}).get("score", 0)
        existing = merged.get(term, 0)
        merged[term] = max(combined, existing)

    # 4. CJK n-gram fallback for unmatched text
    if not merged:
        cjk_chars = [ch for ch in text if '一' <= ch <= '鿿']
        if len(cjk_chars) >= 4:
            stop_chars = set("的是我了在有不这一个人他她它吗们就来对和而以可要也都会去")
            ngrams = {}
            for n in [3, 2]:
                for i in range(len(cjk_chars) - n + 1):
                    ng = ''.join(cjk_chars[i:i+n])
                    score = sum(1 for c in ng if c not in stop_chars)
                    if score >= 2:
                        ngrams[ng] = max(ngrams.get(ng, 0), score)
            for ng, score in sorted(ngrams.items(), key=lambda x: -x[1])[:5]:
                merged[ng] = score

    # 5. Final fallback
    if not merged:
        merged["technology"] = 1
        merged["digital"] = 1

    sorted_kw = sorted(merged.items(), key=lambda x: -x[1])
    return [kw for kw, _ in sorted_kw[:5]]


def _measure_text_width(text, cjk_font, lat_font):
    """Measure the pixel width of mixed CJK/Latin text using segment-aware fonts."""
    dummy = Image.new('RGB', (1, 1))
    draw = ImageDraw.Draw(dummy)
    total = 0
    i = 0
    while i < len(text):
        use_cjk = is_cjk(ord(text[i]))
        j = i + 1
        while j < len(text) and is_cjk(ord(text[j])) == use_cjk:
            j += 1
        seg = text[i:j]
        font = cjk_font if use_cjk else lat_font
        bbox = draw.textbbox((0, 0), seg, font=font)
        total += bbox[2] - bbox[0] + 1  # +1 for inter-segment gap
        i = j
    return total


def _wrap_title_by_width(title, max_width, cjk_font, lat_font, max_lines=2):
    """Wrap title into balanced lines based on pixel width, not character count.

    Returns list of 1-N lines, each fitting within max_width.
    max_lines controls the maximum number of lines (default 2).
    When the title exceeds max_lines, the last line is truncated with …"""
    # Handle explicit line breaks
    if '\\n' in title:
        lines = title.split('\\n')
        return lines[:max_lines]

    ellipsis = '…'
    ellipsis_w = _measure_text_width(ellipsis, cjk_font, lat_font)

    width = _measure_text_width(title, cjk_font, lat_font)
    if width <= max_width:
        return [title]

    # Need wrapping: find best split point by pixel measurement
    n = len(title)
    widths = []
    cum = 0
    dummy = Image.new('RGB', (1, 1))
    draw = ImageDraw.Draw(dummy)
    i = 0
    while i < n:
        use_cjk = is_cjk(ord(title[i]))
        j = i + 1
        while j < n and is_cjk(ord(title[j])) == use_cjk:
            j += 1
        font = cjk_font if use_cjk else lat_font
        bbox = draw.textbbox((0, 0), title[i:j], font=font)
        cum += bbox[2] - bbox[0] + 1
        for k in range(i, j):
            widths.append(cum)
        i = j

    target = cum / 2
    sep_chars = set(' |,，:：-—·.。!！?？、/')

    valid_break = [False] * n
    for idx in range(1, n):
        prev_cjk = is_cjk(ord(title[idx - 1]))
        curr_cjk = is_cjk(ord(title[idx]))
        if title[idx - 1] in sep_chars or title[idx] in sep_chars:
            valid_break[idx] = True
        elif prev_cjk and curr_cjk:
            valid_break[idx] = True
        elif not prev_cjk and not curr_cjk:
            valid_break[idx] = False
        else:
            valid_break[idx] = True

    candidates = []
    for idx in range(len(title) - 1):
        if not valid_break[idx]:
            continue
        w = widths[idx]
        if w < max_width and cum - w < (max_width if max_lines >= 3 else max_width - ellipsis_w):
            priority = 0
            if title[idx] in sep_chars:
                priority = 10
            elif idx > 0 and title[idx - 1] in sep_chars:
                priority = 8
            elif idx > 0 and is_cjk(ord(title[idx - 1])) and is_cjk(ord(title[idx])):
                priority = 3
            candidates.append((abs(w - target), -priority, idx))

    candidates.sort()
    if candidates:
        split = candidates[0][2]
        if title[split] in sep_chars:
            split += 1
        elif split > 0 and title[split - 1] in sep_chars:
            pass
        line1 = title[:split].rstrip()
        line2 = title[split:].lstrip()
    else:
        mid = n // 2
        line1, line2 = title[:mid], title[mid:]

    # Check if line2 still too wide
    l2w = _measure_text_width(line2, cjk_font, lat_font)
    if l2w > max_width:
        if max_lines >= 3:
            # Try 3-way split
            third = n // 3
            two_thirds = (n * 2) // 3
            split1, split2 = third, two_thirds
            for sp in range(third, 0, -1):
                if sp < n and valid_break[sp]:
                    split1 = sp; break
            for sp in range(two_thirds, 0, -1):
                if sp < n and valid_break[sp]:
                    split2 = sp; break
            if split2 <= split1:
                split2 = min(split1 + (n - split1) // 2, n)
            line1 = title[:split1].rstrip()
            line2 = title[split1:split2].strip()
            line3 = title[split2:].lstrip()
            return [line1, line2, line3]
        else:
            # Truncate line2 to fit with ellipsis
            for i in range(len(line2) - 1, 0, -1):
                if _measure_text_width(line2[:i] + ellipsis, cjk_font, lat_font) <= max_width:
                    line2 = line2[:i] + ellipsis
                    break

    return [line1, line2]


def _extract_adaptive_colors(px):
    """Sample the photo background to derive a harmonious accent + text palette.

    Strategy:
      1. Sample the left-side text region for dominant hue and brightness.
      2. Pick an accent that complements the background hue (analogous or triadic).
      3. Set text brightness based on backdrop darkness — lighter text on dark,
         slightly darker text on bright backgrounds.
    """
    # Sample strategically: left text zone (columns 80-500, rows 60-500)
    sample_colors = []
    for y in range(60, 500, 20):
        for x in range(80, 500, 40):
            sample_colors.append(px[x, y])

    if not sample_colors:
        return (0xFF, 0x8C, 0x42), (0xF5, 0xF0, 0xEC), (0xCC, 0xC8, 0xC4), (0x99, 0x95, 0x90), (0x33, 0x30, 0x2D)

    # Average brightness in the sampling region
    avg_lum = sum(r * 0.299 + g * 0.587 + b * 0.114 for r, g, b in sample_colors) / len(sample_colors)

    # Find the most saturated color as potential accent inspiration
    best_sat, best_rgb = 0, (0xFF, 0x8C, 0x42)
    for r, g, b in sample_colors:
        mx = max(r, g, b)
        mn = min(r, g, b)
        sat = (mx - mn) / mx if mx > 0 else 0
        # Prefer moderately bright saturated colors
        score = sat * min(mx / 255, 0.7)
        if score > best_sat:
            best_sat = score
            best_rgb = (r, g, b)

    # Generate accent: boost saturation + shift hue slightly for contrast
    r, g, b = best_rgb
    mx, mn = max(r, g, b), min(r, g, b)
    if best_sat > 0.15:
        # Amplify the natural accent color
        boost = 1.3
        r2 = min(255, int(r * boost))
        g2 = min(255, int(g * boost))
        b2 = min(255, int(b * boost))
        # Shift hue by ~15° for better contrast
        avg = (r2 + g2 + b2) // 3
        if r2 > avg:
            r2 = min(255, r2 + 20)
            b2 = max(0, b2 - 10)
        elif b2 > avg:
            b2 = min(255, b2 + 20)
            r2 = max(0, r2 - 10)
        else:
            g2 = min(255, g2 + 20)
        accent = (r2, g2, b2)
    else:
        # Low saturation → use a warm or cool accent based on luminance
        accent = (0xFF, 0xA0, 0x40) if avg_lum < 120 else (0x40, 0x90, 0xFF)

    # Text palette: lightness depends on background brightness
    if avg_lum < 90:
        # Dark background → bright text
        light = (0xF5, 0xF0, 0xEC)
        mid = (0xCC, 0xC8, 0xC4)
        dim = (0x99, 0x95, 0x90)
        wm = (0x33, 0x30, 0x2D)
    elif avg_lum < 140:
        # Medium-dark → bright but slightly muted
        light = (0xF2, 0xEE, 0xEA)
        mid = (0xBB, 0xB7, 0xB3)
        dim = (0x88, 0x84, 0x80)
        wm = (0x44, 0x40, 0x3C)
    elif avg_lum < 180:
        # Medium-bright → darker text for readability
        light = (0x1A, 0x18, 0x20)
        mid = (0x44, 0x40, 0x4C)
        dim = (0x66, 0x62, 0x6E)
        wm = (0xCC, 0xC8, 0xC4)
    else:
        # Very bright background → deep text, high contrast
        light = (0x0D, 0x0C, 0x16)
        mid = (0x33, 0x30, 0x40)
        dim = (0x55, 0x52, 0x60)
        wm = (0xBB, 0xB8, 0xB4)

    return accent, light, mid, dim, wm


def generate_cover(title, subtitle, tag, date_str, reading_info, footer, output_path,
                   mode='auto', theme_name=None, article_path=None, keywords=None,
                   background_image=None, image_strategy='auto'):
    """Generate a 1200x675 cover image.

    mode='auto': intelligent background (local Agent image->OG->Pexels->AI->Unsplash->Brave->geometric)
    mode='geometric': abstract 8-theme design
    """
    themes = load_themes()

    # Read article content if path provided (before keyword extraction)
    article_content = None
    if article_path and os.path.exists(article_path):
        try:
            with open(article_path, 'r', encoding='utf-8') as f:
                article_content = f.read()
        except Exception:
            pass

    # Determine keywords for image search (uses article body when available)
    if keywords is None:
        keywords = []
    if not keywords:
        keywords = _extract_keywords(title, subtitle, body_text=article_content)

    bg_source = 'geometric'
    photo_bg = None

    if mode == 'auto':
        if image_strategy != 'legacy':
            photo_bg, bg_source = load_local_background_image(background_image)
        if not photo_bg:
            photo_bg, bg_source = get_background_image(title, keywords, article_content)

    if photo_bg:
        # Resize/crop to cover dimensions
        photo_bg = photo_bg.resize((W, H), Image.LANCZOS)
        img = photo_bg
        draw = ImageDraw.Draw(img)
        px = img.load()
        apply_text_backdrop(img, px)

        # Adaptive colors sampled from the photo background
        ACCENT, LIGHT, MID, DIM, WM = _extract_adaptive_colors(px)
    else:
        # Geometric mode
        theme = themes[theme_name] if theme_name and theme_name in themes else select_theme(title, themes)
        img = Image.new('RGB', (W, H), _tuple(theme["base"]))
        draw = ImageDraw.Draw(img)
        px = img.load()
        build_geometric_background(img, draw, px, theme)

        ACCENT = _tuple(theme["accent"])
        theme_lum = sum(theme["base"]) / 3
        if theme_lum > 180:
            LIGHT = (0x1A, 0x1A, 0x28)
            MID = (0x55, 0x55, 0x66)
            DIM = (0x88, 0x88, 0x99)
        else:
            LIGHT = (0xE8, 0xE8, 0xF0)
            MID = (0x94, 0x94, 0xB8)
            DIM = (0x64, 0x64, 0x88)
        WM = _tuple(theme["watermark_color"])
        theme_name = theme["name"]

    # ── Pure image cover (title shown beside cover in feed, not on it) ──
    f9l = ImageFont.truetype(FLAT, 9)

    # Source badge (bottom-left, barely visible)
    badge_text = bg_source if photo_bg else theme_name
    bb = draw.textbbox((0, 0), badge_text, font=f9l)
    bw = bb[2] - bb[0] + 6
    draw.rectangle([18, H - 22, 20 + bw, H - 12], fill=WM)
    draw.text((21, H - 21), badge_text, fill=DIM, font=f9l)

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
    p.add_argument('--footer',
                   default=_cover_prefs.get('footers', {}).get('evening-briefing', '每晚 21:30 与你一起回顾这一天'))
    p.add_argument('--output', '-o', help='Output PNG file path.')
    p.add_argument('--mode', choices=['auto', 'geometric'],
                   default=_cover_prefs.get('cover', {}).get('default_mode', 'auto'),
                   help='Background mode: auto (local Agent image->OG->Pexels->AI->Unsplash->Brave->geometric) or geometric')
    p.add_argument('--theme', choices=list(themes.keys()), help='Force geometric theme.')
    p.add_argument('--article', help='Article HTML/text file for OG image extraction.')
    p.add_argument('--keywords', help='Comma-separated keywords for image search.')
    p.add_argument('--background-image', help='Local Agent/Codex-generated background image path.')
    p.add_argument('--image-strategy', choices=['auto', 'legacy', 'agent_first', 'factual_first'],
                   default=_cover_prefs.get('cover', {}).get('image_strategy', 'auto'),
                   help='Image source strategy. legacy ignores --background-image.')
    p.add_argument('--list-themes', action='store_true', help='List themes and exit.')

    args = p.parse_args()
    if args.list_themes:
        list_themes()
        return
    if not args.title or not args.output:
        p.error("--title and --output are required for generation")

    keywords = [k.strip() for k in args.keywords.split(',')] if args.keywords else None

    # Apply preferred_theme from preferences if not specified on CLI
    if args.mode in ('geometric', None) and not args.theme:
        preferred = _cover_prefs.get('cover', {}).get('preferred_theme')
        if preferred and preferred in themes:
            args.theme = preferred

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
        background_image=args.background_image,
        image_strategy=args.image_strategy,
    )

if __name__ == '__main__':
    main()
