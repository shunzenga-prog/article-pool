#!/usr/bin/env python3
"""
Upload local images in an HTML article to WeChat CDN and replace src with CDN URLs.
Usage: python replace_local_images.py <article.html>
"""
import re
import os
import sys
import base64

# ── Import the WeChat upload function ──
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from paths import load_env
load_env()

import requests
APPID = os.getenv("WECHAT_APPID")
SECRET = os.getenv("WECHAT_SECRET")

_token_cache = None

def get_access_token():
    global _token_cache
    if _token_cache:
        return _token_cache
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APPID}&secret={SECRET}"
    resp = requests.get(url, timeout=15)
    data = resp.json()
    if "access_token" in data:
        _token_cache = data["access_token"]
        return _token_cache
    else:
        print(f"❌ Token failed: {data}")
        return None

def upload_image(image_path):
    """Upload image to WeChat CDN, return URL."""
    token = get_access_token()
    if not token:
        return None
    if not os.path.exists(image_path):
        print(f"❌ File not found: {image_path}")
        return None
    file_size = os.path.getsize(image_path)
    if file_size > 2 * 1024 * 1024:
        print(f"❌ File too large ({file_size/1024/1024:.1f}MB), limit 2MB")
        return None

    url = f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={token}"
    with open(image_path, "rb") as f:
        resp = requests.post(url, files={"media": f}, timeout=30)
    data = resp.json()
    if "url" in data:
        return data["url"]
    else:
        print(f"❌ Upload failed: {data}")
        return None

def process_html(html_path):
    """Find local/relative images in HTML and replace with WeChat CDN URLs."""
    html_dir = os.path.dirname(os.path.abspath(html_path))

    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Find all <img src="..."> that are NOT already CDN URLs and NOT data URIs
    def replace_src(match):
        src = match.group(1)
        # Skip already-uploaded CDN URLs
        if "mmbiz.qpic.cn" in src or "qpic.cn" in src:
            return match.group(0)
        # Skip data URIs
        if src.startswith("data:"):
            # Extract base64, write to temp file, upload
            header, b64data = src.split(",", 1)
            import tempfile
            ext = "png" if "png" in header else "jpg"
            with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
                tmp.write(base64.b64decode(b64data))
                tmp_path = tmp.name
            cdn_url = upload_image(tmp_path)
            os.unlink(tmp_path)
            if cdn_url:
                print(f"  ✅ data:image → {cdn_url[:60]}...")
                return f'<img src="{cdn_url}" style="max-width:100%;"'
            else:
                return match.group(0)

        # Local file path
        img_path = src
        if not os.path.isabs(img_path):
            img_path = os.path.join(html_dir, img_path)
        if os.path.exists(img_path):
            cdn_url = upload_image(img_path)
            if cdn_url:
                print(f"  ✅ {os.path.basename(img_path)} → {cdn_url[:60]}...")
                return f'<img src="{cdn_url}" style="max-width:100%;"'
        else:
            print(f"  ⚠️  Image not found: {img_path}")
        return match.group(0)

    pattern = r'<img\s[^>]*src="([^"]+)"([^>]*)>'
    updated = re.sub(pattern, replace_src, html)

    # Save
    out_path = html_path.replace(".html", "_cdn.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(updated)

    print(f"\n✅ Done. Saved to: {out_path}")
    print(f"   Use this file with publish_html.py")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python replace_local_images.py <article.html>")
        print("Uploads all local/data-URI images to WeChat CDN and replaces src.")
        sys.exit(1)
    process_html(sys.argv[1])
