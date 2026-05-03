# -*- coding: utf-8 -*-
"""Professional cover image generator for WeChat articles.

Two modes:
  auto (default): OG → Pexels → AI-gen → Unsplash → Brave → geometric fallback
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

# Font auto-detection with fallback paths (Linux + Windows)
_CJK_CANDIDATES = [
    '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',
    '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
    '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
    '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
    '/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc',
    'C:/Windows/Fonts/msyh.ttc',
    'C:/Windows/Fonts/simhei.ttf',
]
_LAT_CANDIDATES = [
    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
    'C:/Windows/Fonts/segoeui.ttf',
    'C:/Windows/Fonts/arial.ttf',
]
_LATB_CANDIDATES = [
    '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
    'C:/Windows/Fonts/segoeuib.ttf',
    'C:/Windows/Fonts/arialbd.ttf',
]

FCJK = next((p for p in _CJK_CANDIDATES if os.path.exists(p)), _CJK_CANDIDATES[0])
FLAT = next((p for p in _LAT_CANDIDATES if os.path.exists(p)), _LAT_CANDIDATES[0])
FLATB = next((p for p in _LATB_CANDIDATES if os.path.exists(p)), _LATB_CANDIDATES[0])

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

def generate_ai_background(keywords, title, seed_text=""):
    """Generate an AI image using Pollinations.ai with prompt variation."""
    if not HAS_REQUESTS:
        return None
    try:
        topic = ' '.join(keywords[:3]) if keywords else 'technology'
        modifiers = get_random_modifier(seed_text or title)

        # Vary the base style prompt to avoid similar outputs
        style_templates = [
            "professional editorial photography, {topic}, {mods}, cinematic lighting, deep depth of field, dark atmosphere, wide angle, negative space on left, 8k photorealistic, no text no watermark",
            "abstract {topic} concept art, {mods}, dramatic composition, shallow depth of field, dark background, left side empty for text, ultra detailed, no text no watermark",
            "{mods} scene about {topic}, documentary photography style, natural lighting, rule of thirds, empty left composition, high resolution, no text no watermark",
            "minimalist {topic} illustration, {mods}, dark theme, sleek design, empty space on left, professional quality, no text no watermark",
        ]
        style = style_templates[random.randint(0, len(style_templates)-1)]
        prompt = style.format(topic=topic, mods=', '.join(modifiers[:2]))

        seed_val = str(random.randint(1, 99999))
        url = f"https://image.pollinations.ai/prompt/{quote(prompt)}"
        params = {'width': 1200, 'height': 675, 'model': 'flux', 'nologo': 'true', 'seed': seed_val}

        print(f'  ai-gen: "{topic}" + "{modifiers[0]}" (seed={seed_val})...')
        r = requests.get(url, params=params, timeout=120)
        if r.status_code == 200 and len(r.content) > 1000:
            try:
                img = Image.open(BytesIO(r.content))
                img.verify()
                print(f'  ai-gen: generated ({len(r.content)/1024:.0f} KB)')
                return BytesIO(r.content)
            except Exception:
                print(f'  ai-gen: invalid image')
                return None
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

def get_background_image(title, keywords, article_content=None):
    """Multi-tier fallback for cover backgrounds:
    Tier 1: OG images from article links
    Tier 2: Pexels API (free, 200 req/hour — needs PEXELS_API_KEY in .env)
    Tier 3: AI-generated image via Pollinations.ai (free, no key needed)
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
    h = hashlib.md5(title.encode()).digest()[0]
    names = list(themes.keys())
    return themes[names[h % len(names)]]

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
    """Apply a soft text-backdrop panel on the left side of the photo,
    keeping most of the image visible and bright. The backdrop ensures
    white text remains readable without crushing the photo."""
    W, H = img.size

    # Subtle overall vignette (very light, just to focus attention)
    for x in range(W):
        for y in range(H):
            o = px[x, y]
            # Edge darkening: only at extreme edges
            edge_factor = 1.0
            if x < 80:
                edge_factor = 0.85 + 0.15 * (x / 80)
            if x > W - 80:
                edge_factor = min(edge_factor, 0.85 + 0.15 * ((W - x) / 80))

            if edge_factor < 1.0:
                px[x, y] = (
                    int(o[0] * edge_factor),
                    int(o[1] * edge_factor),
                    int(o[2] * edge_factor),
                )

    # Left-side text backdrop: gradient from dark (left) to transparent (right)
    # This creates a readable surface for titles and body text
    for x in range(0, min(580, W)):
        for y in range(0, H):
            o = px[x, y]
            # Opacity: 60% at left edge, fading to 0% at x=580
            if x < 80:
                opacity = 0.55
            elif x < 400:
                opacity = 0.55 * (1.0 - (x - 80) / 320.0)
            elif x < 580:
                opacity = 0.55 * max(0, (580 - x) / 180.0)
            else:
                continue

            # Blend to dark charcoal
            dark_r, dark_g, dark_b = 10, 12, 20
            px[x, y] = (
                int(o[0] * (1 - opacity) + dark_r * opacity),
                int(o[1] * (1 - opacity) + dark_g * opacity),
                int(o[2] * (1 - opacity) + dark_b * opacity),
            )

    # Bottom gradient bar for footer text readability
    for y in range(H - 130, H):
        for x in range(W):
            o = px[x, y]
            ratio = (y - (H - 130)) / 130.0
            opacity = 0.15 + 0.55 * ratio  # 15% at top of bar, 70% at bottom
            dark_r, dark_g, dark_b = 8, 10, 18
            px[x, y] = (
                int(o[0] * (1 - opacity) + dark_r * opacity),
                int(o[1] * (1 - opacity) + dark_g * opacity),
                int(o[2] * (1 - opacity) + dark_b * opacity),
            )

    # Add a subtle frame border
    border_color = (40, 42, 50)
    for y in range(H):
        px[0, y] = border_color
        px[1, y] = border_color
        px[W-1, y] = border_color
        px[W-2, y] = border_color
    for x in range(W):
        px[x, 0] = border_color
        px[x, 1] = border_color
        px[x, H-1] = border_color
        px[x, H-2] = border_color


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
               "新能源", "