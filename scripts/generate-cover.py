#!/usr/bin/env python3
"""Smart cover image generator for WeChat articles.
Sources: Pollinations AI (free, no API key) or Unsplash (free, high quality).
Usage: python generate-cover.py <article_path> [--output <path>] [--template]
"""

import requests, re, os, sys, hashlib
from datetime import datetime
from urllib.parse import quote

COVER_TEMPLATES = {
    "news": [
        "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=900&h=500&fit=crop",
        "https://images.unsplash.com/photo-1495020689067-958852a7765e?w=900&h=500&fit=crop",
        "https://images.unsplash.com/photo-1585829365295-ab7cd400c167?w=900&h=500&fit=crop",
        "https://images.unsplash.com/photo-1559526324-593bc073d938?w=900&h=500&fit=crop",
        "https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=900&h=500&fit=crop",
        "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=900&h=500&fit=crop",
    ],
    "ai": [
        "https://images.unsplash.com/photo-1677442136019-21780ecad995?w=900&h=500&fit=crop",
        "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?w=900&h=500&fit=crop",
        "https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=900&h=500&fit=crop",
        "https://images.unsplash.com/photo-1531746790731-6c087fecd65a?w=900&h=500&fit=crop",
        "https://images.unsplash.com/photo-1518770660439-4636190af475?w=900&h=500&fit=crop",
        "https://images.unsplash.com/photo-1555255707-c07966a6a732?w=900&h=500&fit=crop",
    ],
    "gpt": [
        "https://images.unsplash.com/photo-1531746790731-6c087fecd65a?w=900&h=500&fit=crop",
        "https://images.unsplash.com/photo-1677442136019-21780ecad995?w=900&h=500&fit=crop",
        "https://images.unsplash.com/photo-1655720828018-edd2daec9349?w=900&h=500&fit=crop",
        "https://images.unsplash.com/photo-1677756119517-756a92e1c4fa?w=900&h=500&fit=crop",
        "https://images.unsplash.com/photo-1682687982501-1e58ab814714?w=900&h=500&fit=crop",
        "https://images.unsplash.com/photo-1633356122544-f134324a6cee?w=900&h=500&fit=crop",
    ],
    "coding": [
        "https://images.unsplash.com/photo-1461749280684-dccba630e2f6?w=900&h=500&fit=crop",
        "https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=900&h=500&fit=crop",
        "https://images.unsplash.com/photo-1542831371-29b0f74f9713?w=900&h=500&fit=crop",
        "https://images.unsplash.com/photo-1523800503107-5bc3ba2a6f81?w=900&h=500&fit=crop",
        "https://images.unsplash.com/photo-1515879218367-8466d910e7f7?w=900&h=500&fit=crop",
        "https://images.unsplash.com/photo-1555099962-4199c345e5dd?w=900&h=500&fit=crop",
    ],
    "business": [
        "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=900&h=500&fit=crop",
        "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=900&h=500&fit=crop",
        "https://images.unsplash.com/photo-1590283603385-17ffb3a7ce44?w=900&h=500&fit=crop",
        "https://images.unsplash.com/photo-1507679799987-c73785c6b1c2?w=900&h=500&fit=crop",
        "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=900&h=500&fit=crop",
        "https://images.unsplash.com/photo-1552664730-d307ca884978?w=900&h=500&fit=crop",
    ],
    "money": [
        "https://images.unsplash.com/photo-1579621970563-ebec7560ff3e?w=900&h=500&fit=crop",
        "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=900&h=500&fit=crop",
        "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=900&h=500&fit=crop",
        "https://images.unsplash.com/photo-1559526324-593bc073d938?w=900&h=500&fit=crop",
        "https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=900&h=500&fit=crop",
        "https://images.unsplash.com/photo-1633158829875-e5310d358f58?w=900&h=500&fit=crop",
    ],
    "innovation": [
        "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=900&h=500&fit=crop",
        "https://images.unsplash.com/photo-1518770660439-4636190af475?w=900&h=500&fit=crop",
        "https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=900&h=500&fit=crop",
        "https://images.unsplash.com/photo-1531746790731-6c087fecd65a?w=900&h=500&fit=crop",
        "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?w=900&h=500&fit=crop",
        "https://images.unsplash.com/photo-1555255707-c07966a6a732?w=900&h=500&fit=crop",
    ],
    "default": [
        "https://images.unsplash.com/photo-1504639725590-34d0984388bd?w=900&h=500&fit=crop",
        "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=900&h=500&fit=crop",
        "https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=900&h=500&fit=crop",
        "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=900&h=500&fit=crop",
        "https://images.unsplash.com/photo-1518770660439-4636190af475?w=900&h=500&fit=crop",
        "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=900&h=500&fit=crop",
    ]
}

KEYWORD_TO_THEME = {
    "daily": "news", "news": "news", "hotspot": "news", "brief": "news",
    "ai": "ai", "artificial intelligence": "ai", "ml": "ai", "deep learning": "ai",
    "gpt": "gpt", "chatgpt": "gpt", "openai": "gpt", "claude": "gpt",
    "llm": "gpt", "gemini": "gpt", "deepseek": "gpt", "llama": "gpt",
    "code": "coding", "programming": "coding", "dev": "coding", "api": "coding",
    "python": "coding", "javascript": "coding", "open source": "coding",
    "business": "business", "enterprise": "business", "strategy": "business",
    "revenue": "business", "acquisition": "business", "ipo": "business",
    "money": "money", "funding": "money", "valuation": "money", "stock": "money",
    "investment": "money", "cost": "money",
    "innovation": "innovation", "breakthrough": "innovation", "launch": "innovation",
}

STYLE_MODIFIERS = [
    "cinematic lighting, professional",
    "minimalist design, clean composition",
    "abstract geometric, futuristic",
    "dark moody, dramatic shadows",
    "bright vibrant, high contrast",
    "soft gradient, ethereal glow",
    "tech corporate, sleek modern",
    "warm ambient, golden hour",
    "cool blue tones, cyberpunk aesthetic",
    "paper texture, editorial style",
    "glass morphism, translucent layers",
    "isometric 3D, depth of field",
]

PROMPT_TEMPLATES = [
    (["gpt", "openai"], "OpenAI GPT AI language model hologram interface"),
    (["gpt", "launch"], "new AI model launch announcement stage lights"),
    (["openai", "stock"], "stock market chart AI company valuation"),
    (["openai", "revenue"], "business revenue growth chart technology"),
    (["ai", "chip"], "AI processor chip semiconductor circuits blue glow"),
    (["ai", "funding"], "venture capital investment funding abstract money"),
    (["ai", "agent"], "AI agent network autonomous nodes connections"),
    (["ai", "search"], "AI search engine magnifying glass data streams"),
    (["ai", "robot"], "futuristic robot AI automation mechanical"),
    (["ai", "security"], "cybersecurity shield AI protection digital"),
    (["ai", "education"], "AI education learning digital transformation"),
    (["tutorial", "guide"], "step by step tutorial guide lightbulb creative"),
    (["code", "dev"], "code screen programming syntax dark theme"),
    (["api", "sdk"], "API developer interface programming connections"),
    (["stock", "crash"], "stock market crash red decline financial"),
    (["stock", "surge"], "stock market bull rally growth green"),
    (["funding", "valuation"], "startup funding venture capital investment"),
    (["acquisition"], "company merger acquisition handshake corporate deal"),
    (["revenue", "growth"], "revenue growth chart upward trend success"),
    (["cost", "price"], "cost reduction savings efficiency optimization"),
    (["google"], "Google technology campus headquarters modern"),
    (["microsoft"], "Microsoft technology software corporate modern"),
    (["nvidia"], "NVIDIA GPU chip technology green circuit board"),
    (["meta"], "Meta virtual reality metaverse technology digital"),
    (["innovation", "breakthrough"], "scientific breakthrough discovery light"),
    (["launch", "release"], "product launch reveal stage spotlight"),
    (["quantum"], "quantum computing physics particles futuristic"),
    (["geopolitics", "chip"], "geopolitics technology chess global chips"),
    (["regulation", "policy"], "government regulation policy document gavel"),
    ([], ""),
]

STYLE_SEEDS = [
    "futuristic technology digital art",
    "modern tech corporate professional",
    "abstract data visualization infographic",
    "minimal clean concept illustration",
    "dark theme cyberpunk neon glow",
    "bright vibrant gradient modern design",
]

def extract_keywords(content, max_keywords=8):
    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    title = title_match.group(1) if title_match else ""
    text = (title + " " + content[:2000]).lower()
    scored = []
    for keyword in KEYWORD_TO_THEME:
        count = text.count(keyword)
        if count > 0:
            scored.append((keyword, count))
    scored.sort(key=lambda x: -x[1])
    return [k for k, _ in scored[:max_keywords]]

def get_theme_from_keywords(keywords):
    counts = {}
    for kw in keywords:
        if kw in KEYWORD_TO_THEME:
            t = KEYWORD_TO_THEME[kw]
            counts[t] = counts.get(t, 0) + 1
    return max(counts, key=counts.get) if counts else "default"

def generate_pollinations_url(prompt, seed=None):
    url = f"https://image.pollinations.ai/prompt/{quote(prompt)}?width=900&height=500&nologo=true"
    if seed:
        url += f"&seed={seed}"
    return url

def generate_custom_cover(keywords, title, date_seed=0):
    title_lower = title.lower()
    kw_lower = [k.lower() for k in keywords]
    matched = None
    for tkeys, prompt in PROMPT_TEMPLATES:
        if not tkeys:
            continue
        if all(tk in title_lower or any(tk in kw for kw in kw_lower) for tk in tkeys):
            matched = prompt
            break
    if not matched:
        kws = keywords[:4] if keywords else ["technology"]
        base = " ".join(kws)
        si = date_seed % len(STYLE_SEEDS)
        matched = f"{base} {STYLE_SEEDS[si]}"
    style = STYLE_MODIFIERS[date_seed % len(STYLE_MODIFIERS)]
    full_prompt = f"{matched}, {style}, 16:9 aspect ratio"
    return generate_pollinations_url(full_prompt, seed=date_seed)

def get_cover_url(keywords, title, use_template=False, date_seed=0):
    theme = get_theme_from_keywords(keywords)
    if not use_template:
        return generate_custom_cover(keywords, title, date_seed)
    templates = COVER_TEMPLATES.get(theme, COVER_TEMPLATES["default"])
    th = int(hashlib.md5(title.encode()).hexdigest(), 16)
    return templates[(th + date_seed) % len(templates)]

def download_image(url, output_path):
    print(f"Downloading: {url[:80]}...")
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(resp.content)
            print(f"Saved: {output_path}")
            return True
        print(f"Failed: HTTP {resp.status_code}")
        return False
    except Exception as e:
        print(f"Failed: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python generate-cover.py <article_path> [--output <path>] [--template]")
        sys.exit(1)
    article_path = sys.argv[1]
    use_template = "--template" in sys.argv
    if "--output" in sys.argv:
        oi = sys.argv.index("--output") + 1
        output_path = sys.argv[oi] if oi < len(sys.argv) else None
    else:
        ad = os.path.dirname(article_path)
        idir = os.path.join(ad, "images")
        os.makedirs(idir, exist_ok=True)
        output_path = os.path.join(idir, "cover.jpg")
    with open(article_path, "r", encoding="utf-8") as f:
        content = f.read()
    tm = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    title = tm.group(1) if tm else "article"
    keywords = extract_keywords(content)
    date_seed = int(datetime.now().strftime("%Y%m%d"))
    print(f"Title: {title}")
    print(f"Keywords: {keywords}")
    print(f"Theme: {get_theme_from_keywords(keywords)}")
    print(f"Source: {'Unsplash' if use_template else 'Pollinations AI'}")
    print(f"Seed: {date_seed}")
    cover_url = get_cover_url(keywords, title, use_template=use_template, date_seed=date_seed)
    if download_image(cover_url, output_path):
        print(f"\nOK! Path: {output_path}")
        return output_path
    print("\nFallback needed")
    return None

if __name__ == "__main__":
    main()
