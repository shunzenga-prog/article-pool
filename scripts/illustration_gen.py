#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文章插图自动生成器 — Analyse article content, source images via 5-tier cascade,
upload to WeChat CDN, and embed into HTML.

Usage:
  python scripts/illustration_gen.py article.html --type 项目推荐
  python scripts/illustration_gen.py article.html --type 技术教程 --dry-run
  python scripts/illustration_gen.py article.html --type 深度解析 --no-upload
  python scripts/illustration_gen.py article.html                    # auto-detect type
"""

from __future__ import annotations

import argparse, json, os, re, sys, time, hashlib, random
import html as html_lib

# Fix Windows console encoding
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
from pathlib import Path
from datetime import datetime
from io import BytesIO
from urllib.parse import quote

try:
    from PIL import Image, ImageDraw
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# ── Paths ──
from paths import (
    CONFIG_DIR, REPORTS_DIR, ILLUSTRATIONS_DIR as OUTPUT_DIR,
    ILLUSTRATION_RULES_FILE as RULES_FILE, USED_IMAGES_FILE,
    get_wechat_config, get_env,
)

_WECHAT_APPID, _WECHAT_SECRET = get_wechat_config()
WECHAT_APPID = _WECHAT_APPID
WECHAT_SECRET = _WECHAT_SECRET
BRAVE_API_KEY = get_env("BRAVE_API_KEY") or ""

VALID_IMAGE_STRATEGIES = {"auto", "legacy", "agent_first", "factual_first"}
FACTUAL_SOURCES = {"code_screenshot", "github_screenshot", "og_image", "web_search"}
GENERATIVE_SOURCES = {"agent_generate", "ai_generate", "fallback_pattern"}


def article_image_output_path(article_path: str | Path, index: int) -> Path:
    """Return a flat image path next to the source article."""
    article = Path(article_path)
    return article.parent / f"{article.stem}-image-{index:02d}.png"


# ======================================================================
# Block 1: Configuration Loader
# ======================================================================

def load_illustration_rules() -> dict:
    """Load illustration_rules.json, merge defaults into article types."""
    if not RULES_FILE.exists():
        raise FileNotFoundError(f"配置文件不存在: {RULES_FILE}")
    with open(RULES_FILE, "r", encoding="utf-8") as f:
        rules = json.load(f)
    return rules


def detect_article_type(html: str, rules: dict) -> str | None:
    """Auto-detect article type from HTML content patterns.
    Checks types sorted by min_matches ascending (lowest threshold first)."""
    auto_rules = rules.get("auto_detect", {}).get("rules", {})
    if not auto_rules:
        return None
    # Sort by min_matches ascending — lower threshold = check first
    sorted_types = sorted(auto_rules.items(), key=lambda x: x[1].get("min_matches", 99))
    for art_type, cfg in sorted_types:
        patterns = cfg.get("patterns", [])
        min_matches = cfg.get("min_matches", 2)
        matched = sum(1 for p in patterns if p.lower() in html.lower())
        if matched >= min_matches:
            return art_type
    return None


def get_type_config(rules: dict, article_type: str) -> dict:
    """Get merged config for a specific article type."""
    defaults = rules.get("defaults", {})
    type_cfg = rules.get("article_types", {}).get(article_type)
    if not type_cfg:
        available = list(rules.get("article_types", {}).keys())
        raise ValueError(f"未知文章类型: {article_type}，可用: {available}")
    # Merge defaults
    merged = dict(defaults)
    merged.update(type_cfg)
    return merged


def normalize_image_strategy(value: str | None) -> str:
    """Normalize image strategy names to a safe default."""
    strategy = (value or "auto").strip()
    return strategy if strategy in VALID_IMAGE_STRATEGIES else "auto"


def resolve_image_strategy(cli_value: str | None, rules: dict) -> str:
    """Resolve CLI/config image strategy."""
    if cli_value:
        return normalize_image_strategy(cli_value)
    configured = rules.get("defaults", {}).get("image_strategy")
    return normalize_image_strategy(configured)


def get_ordered_source_configs(sources: dict, image_strategy: str = "auto") -> list[tuple[str, dict]]:
    """Return enabled image sources ordered for the selected strategy."""
    strategy = normalize_image_strategy(image_strategy)
    enabled = [(k, v) for k, v in sources.items() if v.get("enabled")]
    if strategy == "legacy":
        enabled = [(k, v) for k, v in enabled if k != "agent_generate"]

    def rank(item: tuple[str, dict]) -> tuple[int, int]:
        name, cfg = item
        priority = cfg.get("priority", 99)
        if strategy == "agent_first" and name == "agent_generate":
            return (-100, priority)
        if strategy == "factual_first":
            if name in FACTUAL_SOURCES:
                return (0, priority)
            if name == "agent_generate":
                return (1, priority)
            if name == "ai_generate":
                return (2, priority)
            return (3, priority)
        return (priority, 0)

    return sorted(enabled, key=rank)


def _item_label(item: dict) -> str:
    return (
        item.get("full_name")
        or item.get("name")
        or item.get("title")
        or item.get("category")
        or "technology"
    )


def _strip_html(value: str) -> str:
    text = re.sub(r"<(?:script|style)[^>]*>[\s\S]*?</(?:script|style)>", " ", value, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html_lib.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _clip_text(value: str, limit: int = 360) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip() + "…"


def _html_text_blocks(article_html: str) -> list[str]:
    blocks = []
    for m in re.finditer(r"<(?:h2|h3|p|li)[^>]*>([\s\S]*?)</(?:h2|h3|p|li)>", article_html, re.I):
        text = _strip_html(m.group(0))
        if len(text) >= 8:
            blocks.append(text)
    return blocks


def _item_paragraph_context(item: dict, article_html: str | None, label: str) -> tuple[str, str]:
    """Return nearby article text so generated art follows the paragraph, not just a keyword."""
    if item.get("html"):
        section_blocks = _html_text_blocks(str(item.get("html")))
        section_title = item.get("title") or item.get("name") or ""
        context = "。".join([str(section_title).strip(), *section_blocks[:3]]).strip("。")
        if context:
            return _clip_text(context), "section_html"

    if article_html:
        blocks = _html_text_blocks(article_html)
        label_lower = label.lower()
        for i, block in enumerate(blocks):
            if label_lower and label_lower in block.lower():
                nearby = [block]
                if len(block) < 120 and i + 1 < len(blocks):
                    nearby.append(blocks[i + 1])
                return _clip_text(" ".join(nearby)), "matched_paragraph"

    metadata = item.get("full_text") or item.get("title") or item.get("name") or item.get("category") or label
    return _clip_text(str(metadata)), "item_metadata"


def build_agent_image_requests(article_path: str, article_type: str, items: list[dict],
                               rules: dict, image_strategy: str, max_count: int,
                               article_html: str | None = None) -> list[dict]:
    """Build a portable request manifest for Agent/Codex-generated images."""
    cfg = rules.get("agent_generate", {})
    width = cfg.get("width", 670)
    height = cfg.get("height", 380)
    style = cfg.get(
        "prompt_style",
        "clean editorial technology illustration, no text, no watermark",
    )
    requests_out = []
    for idx, item in enumerate(items[:max_count]):
        label = _item_label(item)
        paragraph_context, context_source = _item_paragraph_context(item, article_html, label)
        req_id = f"image_{idx + 1:03d}"
        output_path = article_image_output_path(article_path, idx + 1)
        prompt = (
            f"为微信公众号文章生成一张配图。文章类型：{article_type}。"
            f"图片锚点：{label}。所在段落内容：{paragraph_context}。"
            f"请根据所在段落的具体信息生成画面，不要只按标题或关键词泛化发挥。"
            f"风格：{style}。画面需适合科技/互联网/编程内容，横版构图，"
            f"避免任何文字、Logo、水印。"
        )
        requests_out.append({
            "id": req_id,
            "article": article_path,
            "article_type": article_type,
            "image_strategy": normalize_image_strategy(image_strategy),
            "label": label,
            "paragraph_context": paragraph_context,
            "context_source": context_source,
            "prompt": prompt,
            "width": width,
            "height": height,
            "output_path": str(output_path),
        })
    return requests_out


def write_agent_image_requests(path: str, article_path: str, article_type: str,
                               image_strategy: str, requests_out: list[dict]) -> None:
    """Write Agent/Codex image requests for a second-stage generator."""
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": "1.0",
        "article": article_path,
        "article_type": article_type,
        "image_strategy": normalize_image_strategy(image_strategy),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "instructions": (
            "在支持图片生成的 Agent 中，逐条生成图片并保存到 output_path，"
            "然后把同一结构写成 generated_images.json，供 --use-local-images 读取。"
        ),
        "images": requests_out,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def load_agent_image_manifest(path: str | None) -> dict[str, dict]:
    """Load local generated-image manifest. Missing files are ignored."""
    if not path:
        return {}
    manifest_path = Path(path)
    if not manifest_path.exists():
        print(f"  [agent] manifest not found: {manifest_path}")
        return {}
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:
        print(f"  [agent] manifest read failed: {exc}")
        return {}

    entries = data.get("images", data) if isinstance(data, dict) else data
    if not isinstance(entries, list):
        return {}

    images: dict[str, dict] = {}
    for idx, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue
        image_id = entry.get("id") or f"image_{idx + 1:03d}"
        raw_path = entry.get("path") or entry.get("output_path") or entry.get("file")
        if not raw_path:
            continue
        image_path = Path(raw_path)
        if not image_path.is_absolute():
            image_path = manifest_path.parent / image_path
        if not image_path.exists():
            print(f"  [agent] missing generated image: {image_path}")
            continue
        fixed_entry = dict(entry)
        fixed_entry["path"] = str(image_path)
        images[image_id] = fixed_entry
    return images


# ======================================================================
# Block 2: Content Analyzer
# ======================================================================

def extract_github_repos(html: str) -> list[dict]:
    """Extract GitHub repo references from HTML content (full URLs only)."""
    pattern = r'https?://github\.com/([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+)'
    seen = set()
    repos = []
    for m in re.finditer(pattern, html):
        owner, repo = m.group(1), m.group(2)
        key = f"{owner}/{repo}"
        if key not in seen:
            seen.add(key)
            repos.append({"owner": owner, "repo": repo, "url": m.group(0), "full_name": key})
    return repos


def extract_project_names(html: str) -> list[dict]:
    """Extract project/tool names from bold text. Returns clean project names."""
    projects = []
    # Known false positives to skip
    skip_words = {"Windows", "Mac", "Linux", "macOS", "MIT", "Apache", "API",
                  "AI", "GPU", "CPU", "PNG", "JPG", "SVG", "PDF", "SSH", "HTTP",
                  "TCP", "JSON", "YAML", "CSS", "Next.js", "TypeScript",
                  "WebAssembly", "Puppeteer", "Playwright", "Chrome", "Spotlight"}
    seen = set()
    # From <b> tags — extract the first CamelCase/English project name
    for m in re.finditer(r'<b>([^<]+)</b>', html):
        full = m.group(1).strip()
        # Extract just the project name: first CamelCase word or English name before Chinese/separator
        pm = re.match(r'([A-Z][a-zA-Z0-9_]*)\s*[·\s]', full)
        if pm:
            name = pm.group(1)
        else:
            # Fallback: use first word if it contains uppercase
            words = full.split()
            name = words[0] if words else ""
        is_english_name = re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', name)
        if (name and len(name) > 2 and len(name) < 40
                and name not in skip_words
                and is_english_name
                and name.lower() not in seen):
            seen.add(name.lower())
            projects.append({"name": name, "type": "bold", "full_text": full})
    return projects


def extract_code_blocks(html: str) -> list[dict]:
    """Extract code blocks from HTML."""
    blocks = []
    for m in re.finditer(r'<pre[^>]*><code[^>]*>([\s\S]*?)</code></pre>', html):
        code = m.group(1).strip()
        # Strip HTML entities
        code = code.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
        blocks.append({"code": code, "language": "detect"})
    return blocks


def extract_sections(html: str) -> list[dict]:
    """Split article into sections by h2/h3 headings or bold section markers."""
    sections = []
    # Try h2/h3 first
    pattern = r'<(?:h2|h3)[^>]*>([^<]+)</(?:h2|h3)>'
    matches = list(re.finditer(pattern, html))
    if not matches:
        # Fallback: bold <p> section headers or <p> with font-weight:bold
        pattern = r'<(?:p|span)[^>]*font-weight\s*:\s*bold[^>]*>([^<]{3,40})</(?:p|span)>'
        matches = list(re.finditer(pattern, html))
    for i, m in enumerate(matches):
        title = m.group(1).strip()
        # Skip meta headers
        skip = {"EVENING DIGEST", "MORNING DIGEST", "扫码", "关注"}
        if title in skip:
            continue
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(html)
        section_html = html[start:end]
        sections.append({"title": title, "html": section_html, "char_count": len(section_html)})
    return sections


def extract_news_items(html: str) -> list[dict]:
    """Extract news items from numbered/sectioned article structure."""
    items = []
    # Pattern: bold title paragraph inside a table cell containing news headline
    # Match patterns like "01 OpenAI...", "OpenAI 联手高通..." in table-based layout
    title_patterns = [
        # Numbered items in tables: <p ...font-weight:bold...>01</td><td>...<p ...>title</p>
        r'<td[^>]*>\s*<p[^>]*>\s*(\d{2})\s*</p>\s*</td>\s*<td[^>]*>\s*<p[^>]*font-weight\s*:\s*bold[^>]*>([^<]+)</p>',
        # Simpler: bold text in paragraph following a number
        r'<p[^>]*font-weight\s*:\s*bold[^>]*>([^<\d][^<]{5,80})</p>',
    ]
    seen = set()
    for pattern in title_patterns:
        for m in re.finditer(pattern, html, re.DOTALL):
            if len(m.groups()) == 2:
                num, title = m.group(1), m.group(2).strip()
            else:
                title = m.group(1).strip()
            # Filter out non-news headers
            skip_kw = {"今日值得关注", "深度阅读", "值得关注", "EVENING", "MORNING",
                       "阅读约", "类别", "总结", "结尾", "互动", "推荐", "讨论"}
            if title and len(title) > 5 and not any(k in title for k in skip_kw):
                key = title[:30]
                if key not in seen:
                    seen.add(key)
                    items.append({"title": title, "type": "news_item"})
    return items


def extract_company_names(html: str, rules: dict = None) -> list[dict]:
    """Extract company/organization names from content.
    Uses configurable list from rules.json if available."""
    default_companies = [
        "OpenAI", "Google", "Meta", "Microsoft", "Apple", "Amazon", "Nvidia",
        "Intel", "高通", "联发科", "立讯精密", "AMD", "Tesla", "特斯拉",
        "华为", "DeepSeek", "Anthropic", "Claude", "AWS", "Manus",
        "迪士尼", "Netflix", "字节跳动", "腾讯", "阿里",
        "百度", "商汤", "讯飞", "智谱", "月之暗面", "百川", "零一万物",
        "Character.AI", "Perplexity", "Mistral", "Stability AI",
        "三星", "英伟达", "软银", "Oracle",
    ]
    # Merge with config-provided list if available
    config_companies = (rules or {}).get("company_names", [])
    known = list(set(default_companies + config_companies))
    found = []
    seen = set()
    for company in known:
        if company in html and company.lower() not in seen:
            seen.add(company.lower())
            found.append({"name": company, "type": "company"})
    return found


def extract_concepts(html: str) -> list[dict]:
    """Extract conceptual terms from bold/emphasized text and headings."""
    concepts = []
    seen = set()
    # Bold text + h2/h3 that describe abstract concepts (vs product names)
    concept_indicators = {"AI", "LLM", "AGI", "RAG", "Agent", "模型", "算力",
                          "开源", "闭源", "对齐", "推理", "训练", "微调",
                          "端侧", "云端", "边缘计算", "Transformer", "架构"}
    for pattern in [r'<b>([^<]+)</b>', r'<(?:h2|h3)[^>]*>([^<]+)</(?:h2|h3)>']:
        for m in re.finditer(pattern, html):
            text = m.group(1).strip()
            if len(text) > 2 and len(text) < 40 and text not in seen:
                seen.add(text)
                concepts.append({"name": text, "type": "concept"})
    return concepts


def extract_data_points(html: str) -> list[dict]:
    """Extract data mentions (numbers, percentages, amounts) as illustration targets."""
    data_patterns = [
        (r'(\d{2,4})\s*亿(?:美元|美金|元|人民币)', "投资/收入规模"),
        (r'(\d+\.?\d*)\s*%\s*(?:暴涨|涨幅|下跌|跌幅|增长)', "百分比变化"),
        (r'(\d+[,\d]*)\s*亿?\s*(?:美元|美金)\s*(?:估值|市值|资本)', "市值/估值"),
        (r'(\d+)\s*万?\s*(?:token|Token)', "技术指标"),
    ]
    points = []
    seen = set()
    for pattern, category in data_patterns:
        for m in re.finditer(pattern, html):
            raw = m.group(0).strip()
            if raw not in seen and len(raw) < 60:
                seen.add(raw)
                points.append({"name": raw, "type": "data_point", "category": category})
    return points[:5]  # Limit to 5 data points


def extract_urls_from_html(html: str) -> list[str]:
    """Extract all http/https URLs from HTML."""
    return re.findall(r'https?://[^\s<>"\']+', html)


# ======================================================================
# Block 3: Image Source Cascade (T1 → T5)
# ======================================================================

def _http_headers():
    return {"User-Agent": "Mozilla/5.0 (compatible; IllustrationGen/1.0)"}


def download_image(url: str, timeout: int = 12) -> BytesIO | None:
    """Download image from URL, return BytesIO or None."""
    if not HAS_REQUESTS:
        return None
    try:
        r = requests.get(url, timeout=timeout, headers=_http_headers())
        if r.status_code == 200 and len(r.content) > 500:
            return BytesIO(r.content)
    except Exception:
        pass
    return None


def t0_agent_generated_image(index: int, agent_images: dict[str, dict]) -> BytesIO | None:
    """Load an image generated by Codex/Agent from a local manifest."""
    if not agent_images:
        return None
    image_id = f"image_{index + 1:03d}"
    entry = agent_images.get(image_id)
    if not entry:
        values = list(agent_images.values())
        entry = values[index] if index < len(values) else None
    if not entry:
        return None
    path = entry.get("path")
    if not path:
        return None
    try:
        with open(path, "rb") as f:
            data = f.read()
        if len(data) > 500:
            print(f"  [T0] Agent-generated local image: {path}")
            return BytesIO(data)
    except Exception as exc:
        print(f"  [T0] Agent image read failed: {exc}")
    return None


def t1_github_screenshot(repo_info: dict, rules: dict) -> BytesIO | None:
    """Try to get GitHub repo screenshot via OG API and raw fallback paths."""
    cfg = rules.get("github_screenshot", {})

    # T1a: GitHub opengraph social preview
    og_url = cfg.get("og_url_template", "https://opengraph.githubassets.com/1/{owner}/{repo}")
    og_url = og_url.format(owner=repo_info["owner"], repo=repo_info["repo"])
    print(f"  [T1] GitHub OG: {og_url}")
    result = download_image(og_url, timeout=cfg.get("timeout_seconds", 15))
    if result:
        return result

    # T1b: Try common screenshot paths in repo
    fallback_paths = cfg.get("fallback_paths", [])
    branches = ["main", "master", "refs/heads/main", "refs/heads/master"]
    url_template = cfg.get("fallback_url_template",
                           "https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}")
    for branch in branches:
        for path in fallback_paths:
            fb_url = url_template.format(owner=repo_info["owner"], repo=repo_info["repo"],
                                         branch=branch, path=path)
            print(f"  [T1b] Trying: {fb_url}")
            result = download_image(fb_url, timeout=cfg.get("timeout_seconds", 15))
            if result:
                return result

    return None


def t2_og_image_from_urls(urls: list[str], max_try: int = 3) -> list[BytesIO]:
    """Extract og:image from article URLs."""
    # Filter out CDN and image URLs that won't have og:image
    cdn_hosts = ["mmbiz.qpic.cn", "qpic.cn", "mmbiz.qlogo.cn"]
    clean_urls = [u for u in urls
                  if not re.search(r'\.(jpg|jpeg|png|gif|webp|svg)(\?|$)', u, re.I)
                  and not any(h in u for h in cdn_hosts)]
    results = []
    for url in clean_urls[:max_try]:
        print(f"  [T2] Fetching OG from: {url[:80]}...")
        try:
            r = requests.get(url, timeout=8, headers=_http_headers())
            if r.status_code != 200:
                continue
            # og:image
            m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', r.text)
            if not m:
                m = re.search(r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']', r.text)
            if m:
                img_url = m.group(1)
                if img_url.startswith("//"):
                    img_url = "https:" + img_url
                elif img_url.startswith("/"):
                    from urllib.parse import urljoin
                    img_url = urljoin(url, img_url)
                img = download_image(img_url)
                if img:
                    results.append(img)
        except Exception:
            pass
    return results


def t3_web_search(query: str, rules: dict, src_cfg: dict = None) -> BytesIO | None:
    """Search for images via Brave Image Search API."""
    if not HAS_REQUESTS or not BRAVE_API_KEY:
        return None
    cfg = rules.get("web_search", {})
    count = cfg.get("results_per_search", 5)
    min_width = cfg.get("min_image_width", 500)

    # Use search_query_template from source config if available
    template = (src_cfg or {}).get("search_query_template", "")
    if template and "{name}" in template:
        full_query = template.replace("{name}", query)
    else:
        full_query = f"{query} screenshot"

    try:
        r = requests.get(
            "https://api.search.brave.com/res/v1/images/search",
            params={"q": full_query, "count": count, "safesearch": "strict"},
            headers={
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": BRAVE_API_KEY,
            },
            timeout=cfg.get("timeout_seconds", 12),
        )
        if r.status_code != 200:
            return None
        results = r.json().get("results", [])
        if not results:
            return None

        for img_data in results:
            img_url = img_data.get("properties", {}).get("url") or img_data.get("url")
            width = img_data.get("properties", {}).get("width", 0)
            if img_url and width >= min_width:
                result = download_image(img_url, timeout=10)
                if result:
                    print(f"  [T3] Brave search found: {img_url[:80]}...")
                    return result
    except Exception:
        pass
    return None


def score_ai_image(img_data: BytesIO) -> tuple:
    """Score AI-generated image quality (0-100). Checks detail, variety, flatness."""
    if not HAS_PIL:
        return 60, "no_pil"
    try:
        img = Image.open(img_data)
        w, h = img.size
        kb = len(img_data.getvalue()) / 1024
        pixel_count = w * h

        issues = []
        deductions = 0

        # 1. File size: too small = low detail / flat color wash
        expected_kb = pixel_count / 3500
        if kb < expected_kb * 0.25:
            deductions += 35
            issues.append(f"tiny({kb:.0f}KB)")
        elif kb < expected_kb * 0.45:
            deductions += 18
            issues.append(f"small({kb:.0f}KB)")

        # 2. Histogram diversity: low unique bins = near-uniform blob
        if img.mode in ("RGB", "RGBA"):
            rgb = img.convert("RGB")
            hist = rgb.histogram()  # 768 values
            active_bins = sum(1 for v in hist if v > 0)
            if active_bins < 40:
                deductions += 40
                issues.append("near_uniform")
            elif active_bins < 80:
                deductions += 20
                issues.append("low_variety")

        # 3. Std deviation of luminosity: very flat = bad, very noisy = bad
        gray = img.convert("L")
        pixels = list(gray.getdata())
        mean = sum(pixels) / len(pixels)
        std = (sum((p - mean) ** 2 for p in pixels) / len(pixels)) ** 0.5
        if std < 12:
            deductions += 30
            issues.append("too_flat")
        elif std < 20:
            deductions += 10
            issues.append("flat")

        score = max(5, 100 - deductions)
        detail = ",".join(issues) if issues else "ok"
        return score, detail
    except Exception:
        return 0, "error"


def t4_ai_generate(keywords: str, rules: dict) -> BytesIO | None:
    """Generate illustration via Pollinations.ai with quality gate + retry."""
    if not HAS_REQUESTS:
        return None
    cfg = rules.get("ai_generate", {})
    w = cfg.get("width", 670)
    h = cfg.get("height", 380)
    model = cfg.get("model", "flux")
    timeout = cfg.get("timeout_seconds", 120)
    style_mods = cfg.get("style_modifiers", ["clean UI", "tech interface"])
    quality_threshold = cfg.get("quality_threshold", 55)
    max_retries = cfg.get("max_retries", 3)

    import random as _random

    for attempt in range(max_retries):
        mod = _random.choice(style_mods)
        prompt = f"{keywords}, {mod}, professional quality, no text no watermark"
        seed_val = str(_random.randint(1, 99999))

        try:
            url = f"https://image.pollinations.ai/prompt/{quote(prompt)}"
            params = {"width": w, "height": h, "model": model, "nologo": "true", "seed": seed_val}
            print(f"  [T4] AI generate (attempt {attempt+1}/{max_retries}): {keywords[:45]}... (seed={seed_val})")
            r = requests.get(url, params=params, timeout=timeout)
            if r.status_code == 200 and len(r.content) > 1000:
                if HAS_PIL:
                    try:
                        Image.open(BytesIO(r.content)).verify()
                    except Exception:
                        continue
                q_score, q_detail = score_ai_image(BytesIO(r.content))
                print(f"  [T4] Quality: {q_score:.0f}/100 ({q_detail})")
                if q_score >= quality_threshold:
                    print(f"  [T4] Generated: {len(r.content)/1024:.0f} KB")
                    return BytesIO(r.content)
                if attempt < max_retries - 1:
                    print(f"  [T4] Below threshold {quality_threshold}, retrying...")
        except Exception:
            pass
    return None


def t5_fallback_pattern(rules: dict) -> BytesIO | None:
    """Generate abstract geometric pattern via PIL."""
    if not HAS_PIL:
        return None
    cfg = rules.get("fallback_pattern", {})
    w = cfg.get("width", 670)
    h = cfg.get("height", 380)
    themes = cfg.get("themes", [
        {"name": "ocean", "colors": ["#0a1628", "#1a3a5c", "#2e86c1", "#5dade2"]},
        {"name": "sunset", "colors": ["#1a0a14", "#5c1a3a", "#c1285e", "#e2748b"]},
    ])

    import random as _random
    theme = _random.choice(themes)
    colors = theme["colors"]

    img = Image.new("RGB", (w, h), colors[0])
    draw = ImageDraw.Draw(img)

    # Gradient background
    for y in range(h):
        ratio = y / h
        r1, g1, b1 = _hex_to_rgb(colors[0])
        r2, g2, b2 = _hex_to_rgb(colors[1])
        r = int(r1 + (r2 - r1) * ratio)
        g = int(g1 + (g2 - g1) * ratio)
        b = int(b1 + (b2 - b1) * ratio)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

    # Random geometric shapes
    for _ in range(_random.randint(3, 6)):
        shape = _random.choice(["circle", "rect", "line"])
        col = _random.choice(colors[2:])
        r, g, b = _hex_to_rgb(col)
        alpha = _random.randint(30, 80)

        if shape == "circle":
            cx = _random.randint(100, w - 100)
            cy = _random.randint(50, h - 50)
            radius = _random.randint(30, 100)
            draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius],
                         outline=(r, g, b), width=2)
        elif shape == "rect":
            x1 = _random.randint(50, w - 200)
            y1 = _random.randint(30, h - 150)
            x2 = x1 + _random.randint(60, 180)
            y2 = y1 + _random.randint(40, 120)
            draw.rectangle([x1, y1, x2, y2], outline=(r, g, b), width=2)
        else:
            x1 = _random.randint(0, w)
            y1 = _random.randint(0, h)
            x2 = x1 + _random.randint(-100, 100)
            y2 = y1 + _random.randint(-80, 80)
            draw.line([(x1, y1), (x2, y2)], fill=(r, g, b), width=2)

    # Dot grid
    for x in range(40, w, 60):
        for y in range(40, h, 60):
            draw.ellipse([x - 1, y - 1, x + 1, y + 1], fill=colors[3])

    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    print(f"  [T5] Fallback pattern generated ({len(buf.getvalue())/1024:.0f} KB)")
    return buf


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


# ======================================================================
# Block 4: Image Processing & WeChat Upload
# ======================================================================

def resize_image(img_data: BytesIO, max_width: int = 670, fmt: str = "PNG") -> BytesIO:
    """Resize image to max width, convert to target format."""
    if not HAS_PIL:
        return img_data
    try:
        img = Image.open(img_data)
        if img.width > max_width:
            ratio = max_width / img.width
            new_h = int(img.height * ratio)
            img = img.resize((max_width, new_h), Image.LANCZOS)
        # Convert to RGB if necessary
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        buf = BytesIO()
        img.save(buf, format=fmt)
        buf.seek(0)
        return buf
    except Exception:
        return None


_wechat_token_cache = None
_wechat_token_time = 0  # timestamp when token was fetched


def _get_wechat_token() -> str | None:
    global _wechat_token_cache, _wechat_token_time
    # Token expires after 7200s; refresh if older than 7000s
    if _wechat_token_cache and (time.time() - _wechat_token_time) < 7000:
        return _wechat_token_cache
    if not WECHAT_APPID or not WECHAT_SECRET:
        print("  [!] WECHAT_APPID/SECRET not configured")
        return None
    try:
        r = requests.get(
            "https://api.weixin.qq.com/cgi-bin/token",
            params={"grant_type": "client_credential", "appid": WECHAT_APPID, "secret": WECHAT_SECRET},
            timeout=10,
        )
        data = r.json()
        if "access_token" in data:
            _wechat_token_cache = data["access_token"]
            _wechat_token_time = time.time()
            return _wechat_token_cache
        else:
            print(f"  [!] Token fail: {data}")
            return None
    except Exception as e:
        print(f"  [!] Token request error: {e}")
        return None


def _compress_for_wechat(img_data: BytesIO, max_bytes: int = 2 * 1024 * 1024) -> BytesIO:
    """Auto-compress image to fit WeChat 2MB limit."""
    data = img_data.getvalue()
    if len(data) <= max_bytes:
        return img_data
    if not HAS_PIL:
        return img_data
    for quality in [85, 65, 50, 35]:
        try:
            img = Image.open(img_data)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            buf = BytesIO()
            img.save(buf, format="JPEG", quality=quality)
            buf.seek(0)
            if len(buf.getvalue()) <= max_bytes:
                print(f"  [compress] JPEG q={quality}: {len(data)/1024:.0f}KB -> {len(buf.getvalue())/1024:.0f}KB")
                return buf
        except Exception:
            pass
    return img_data


def upload_to_wechat(img_data: BytesIO, filename: str = "illustration.png") -> str | None:
    """Upload image to WeChat CDN, return URL. Auto-compresses large images."""
    token = _get_wechat_token()
    if not token:
        return None

    # Auto-compress if over 2MB
    data = img_data.getvalue()
    if len(data) > 2 * 1024 * 1024:
        img_data = _compress_for_wechat(img_data)
        data = img_data.getvalue()
        if len(data) > 2 * 1024 * 1024:
            print(f"  [!] Image still too big after compression: {len(data)/1024/1024:.1f}MB")
            return None

    try:
        r = requests.post(
            "https://api.weixin.qq.com/cgi-bin/media/uploadimg",
            params={"access_token": token},
            files={"media": (filename, data, "image/png")},
            timeout=30,
        )
        result = r.json()
        if "url" in result:
            return result["url"]
        elif result.get("errcode") == 40001:
            # Token expired, refresh and retry once
            global _wechat_token_cache, _wechat_token_time
            _wechat_token_cache = None
            _wechat_token_time = 0
            token = _get_wechat_token()
            if token:
                r = requests.post(
                    "https://api.weixin.qq.com/cgi-bin/media/uploadimg",
                    params={"access_token": token},
                    files={"media": (filename, data, "image/png")},
                    timeout=30,
                )
                result = r.json()
                if "url" in result:
                    return result["url"]
            print(f"  [!] Upload fail after token refresh: {result}")
            return None
        else:
            print(f"  [!] Upload fail: {result}")
            return None
    except Exception as e:
        print(f"  [!] Upload error: {e}")
        return None


# ======================================================================
# Block 5: HTML Embedder
# ======================================================================

def insert_images_into_html(html: str, placements: list[dict], img_template: str) -> str:
    """Insert img tags into HTML at specified positions."""
    lines = html.split("\n")
    # Sort placements by line position (insert from end to avoid offset)
    placements_sorted = sorted(placements, key=lambda p: -p["line"])

    for p in placements_sorted:
        line_num = p["line"]
        img_html = img_template.format(url=p["url"], alt=p.get("alt", "illustration"))
        if 0 <= line_num <= len(lines):
            lines.insert(line_num, img_html)

    return "\n".join(lines)


def _is_section_header_line(line: str) -> bool:
    """Detect whether a line contains a section header.
    Matches: <h2>/<h3>, or <span>/<p> with large font (17-20px) + bold (600-700).
    """
    if re.search(r"<(?:h2|h3)[^>]*>", line):
        return True
    # Match span/p with font-size 17-20px AND font-weight 600-700 or 'bold'
    if re.search(r'font-size\s*:\s*1[7-9]px[^>]*font-weight\s*:\s*(?:700|bold|600)', line):
        return True
    if re.search(r'font-size\s*:\s*20px[^>]*font-weight\s*:\s*(?:700|bold|600)', line):
        return True
    return False


def _find_section_markers(lines: list[str]) -> list[int]:
    """Find section boundary line numbers."""
    markers = []
    for i, line in enumerate(lines):
        if _is_section_header_line(line):
            markers.append(i)
    return markers


def _find_section_marker_after_line(lines: list[str], start_line: int) -> int | None:
    """Find the next section header line after start_line (for placing image before next section)."""
    for i in range(start_line + 1, len(lines)):
        if _is_section_header_line(lines[i]):
            return i
    return None


def _table_depth_before_line(lines: list[str], line_num: int) -> int:
    """Return unclosed <table> depth before inserting at line_num."""
    depth = 0
    for line in lines[:line_num]:
        depth += len(re.findall(r"<table\b", line, re.I))
        depth -= len(re.findall(r"</table>", line, re.I))
        depth = max(depth, 0)
    return depth


def _move_after_open_table(lines: list[str], line_num: int) -> int:
    """Move insertion point after the current table if line_num is inside one."""
    depth = _table_depth_before_line(lines, line_num)
    if depth <= 0:
        return line_num
    for i in range(line_num, len(lines)):
        depth += len(re.findall(r"<table\b", lines[i], re.I))
        depth -= len(re.findall(r"</table>", lines[i], re.I))
        if depth <= 0:
            return i + 1
    return line_num


def find_placement_positions(html: str, placement_strategy: str,
                             items: list[dict], image_urls: list[str]) -> list[dict]:
    """Determine image insertion line positions based on placement strategy."""
    lines = html.split("\n")
    placements = []

    if placement_strategy == "after_project_intro":
        img_idx = 0
        for item in items:
            if img_idx >= len(image_urls):
                break
            search = item.get("url") or item.get("name", "")
            if not search:
                continue
            for i, line in enumerate(lines):
                if search in line:
                    for j in range(i + 1, min(i + 10, len(lines))):
                        if "</td></tr></table>" in lines[j]:
                            placements.append({
                                "line": j + 1,
                                "url": image_urls[img_idx],
                                "alt": item.get("name", item.get("repo", "")),
                            })
                            img_idx += 1
                            break
                    break

    elif placement_strategy == "after_code_block_or_section":
        img_idx = 0
        for i, line in enumerate(lines):
            if img_idx >= len(image_urls):
                break
            if "</pre>" in line:
                placements.append({
                    "line": i + 1,
                    "url": image_urls[img_idx],
                    "alt": "code screenshot",
                })
                img_idx += 1
        for i, line in enumerate(lines):
            if img_idx >= len(image_urls):
                break
            if re.search(r"<(?:h2|h3)[^>]*>", line):
                placements.append({
                    "line": i + 1,
                    "url": image_urls[img_idx],
                    "alt": "section illustration",
                })
                img_idx += 1

    elif placement_strategy == "after_section_header":
        img_idx = 0
        for i, line in enumerate(lines):
            if img_idx >= len(image_urls):
                break
            if _is_section_header_line(line):
                # Place image after the section header (i+1 = next line)
                # but before the next section header — find a good spot in between
                next_header = _find_section_marker_after_line(lines, i)
                if next_header:
                    # Insert a few lines before next section header
                    insert_line = max(i + 2, next_header - 2)
                else:
                    insert_line = i + 2
                insert_line = _move_after_open_table(lines, insert_line)
                placements.append({
                    "line": insert_line,
                    "url": image_urls[img_idx],
                    "alt": "section illustration",
                })
                img_idx += 1

    elif placement_strategy == "before_section":
        img_idx = 0
        markers = _find_section_markers(lines)
        for marker_line in markers:
            if img_idx >= len(image_urls):
                break
            placements.append({
                "line": marker_line,
                "url": image_urls[img_idx],
                "alt": "section illustration",
            })
            img_idx += 1

    return placements


# ======================================================================
# Block 6: Orchestrator
# ======================================================================

def generate_illustrations(article_path: str, article_type: str | None = None,
                           dry_run: bool = False, no_upload: bool = False,
                           max_images: int | None = None, output_path: str | None = None,
                           image_strategy: str | None = None,
                           emit_image_requests: str | None = None,
                           use_local_images: str | None = None,
                           allow_fallback_pattern: bool = False) -> dict:
    """Main orchestrator: analyze article → source images → embed → output."""
    # Load config
    rules = load_illustration_rules()

    # Read HTML
    with open(article_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Determine article type
    if not article_type:
        article_type = detect_article_type(html, rules)
        if not article_type:
            print("ERROR: 无法自动检测文章类型，请用 --type 指定")
            print(f"  可用类型: {list(rules.get('article_types', {}).keys())}")
            sys.exit(1)
        print(f"自动检测文章类型: {article_type}")

    type_cfg = get_type_config(rules, article_type)
    image_strategy = resolve_image_strategy(image_strategy, rules)
    agent_images = load_agent_image_manifest(use_local_images)
    max_images = max_images or type_cfg.get("max_images_total", 20)
    img_template = type_cfg.get("img_table_template",
        '<table width="100%"><tr><td style="text-align:center; padding:6px 0 14px;">\n'
        '  <img src="{url}" style="max-width:100%; height:auto; display:block;" />\n'
        '</td></tr></table>')
    triggers = type_cfg.get("triggers", {})
    sources = type_cfg.get("sources", {})
    placement_strategy = type_cfg.get("placement", "after_section_header")

    print(f"\n{'='*60}")
    print(f"文章插图生成器")
    print(f"  文章: {article_path}")
    print(f"  类型: {article_type}")
    print(f"  策略: {placement_strategy}")
    print(f"  图片策略: {image_strategy}")
    print(f"  最大图片数: {max_images}")
    if agent_images:
        print(f"  本地 Agent 图片: {len(agent_images)} 张")
    print(f"{'='*60}\n")

    # ── Step 1: Content Analysis ──
    print("[1] 内容分析...")
    github_repos = extract_github_repos(html) if triggers.get("github_repo_urls") else []
    project_names = extract_project_names(html) if triggers.get("project_names") else []
    code_blocks = extract_code_blocks(html) if triggers.get("code_blocks") else []
    sections = extract_sections(html) if triggers.get("sections") else []
    news_items = extract_news_items(html) if triggers.get("news_items") else []
    company_names = extract_company_names(html, rules) if triggers.get("company_names") else []
    concepts = extract_concepts(html) if triggers.get("concepts") else []
    data_points = extract_data_points(html) if triggers.get("data_points") else []
    urls = extract_urls_from_html(html)

    print(f"  GitHub 仓库: {len(github_repos)}")
    print(f"  项目名称: {len(project_names)}")
    print(f"  代码块: {len(code_blocks)}")
    print(f"  章节: {len(sections)}")
    print(f"  新闻条目: {len(news_items)}")
    print(f"  公司名: {len(company_names)}")
    print(f"  概念术语: {len(concepts)}")
    print(f"  数据点: {len(data_points)}")
    print(f"  链接: {len(urls)}")

    # ── Step 2: Determine image needs ──
    print("\n[2] 确定需求...")
    # Pick items based on what was extracted
    if github_repos:
        items = github_repos
    elif project_names:
        items = project_names
    elif news_items:
        items = news_items
    elif sections:
        items = sections
    elif company_names:
        items = company_names
    elif concepts:
        items = concepts
    elif data_points:
        items = data_points
    else:
        items = []

    # Apply per_item limits from source configs
    enabled_sources = [v for k, v in sources.items() if v.get("enabled")]
    per_item_limit = max((s.get("per_item", 1) or 0 for s in enabled_sources), default=1)
    per_section_limit = max((s.get("per_section", 0) or 0 for s in enabled_sources), default=0)
    # If per_section is higher than per_item, prefer section-based: swap items
    if per_section_limit > per_item_limit and sections:
        items = sections
        effective_limit = per_section_limit
    else:
        effective_limit = per_item_limit

    total_needed = min(len(items) * effective_limit, max_images)
    total_needed = max(total_needed, 1) if items else 0
    print(f"  需要插图: {total_needed} 张 (per_item={per_item_limit}, per_section={per_section_limit})")

    if total_needed == 0:
        print("  未检测到需要配图的内容，跳过")
        return {"status": "skipped", "reason": "no content to illustrate"}

    agent_requests = build_agent_image_requests(
        article_path=article_path,
        article_type=article_type,
        items=items,
        rules=rules,
        image_strategy=image_strategy,
        max_count=total_needed,
        article_html=html,
    )
    if emit_image_requests:
        write_agent_image_requests(
            emit_image_requests,
            article_path,
            article_type,
            image_strategy,
            agent_requests,
        )
        print(f"  [agent] 图片生成请求: {emit_image_requests}")

    # ── Step 3: Source images via cascade ──
    print("\n[3] 获取图片...")
    sourced_images = []
    og_cache: list[BytesIO] = []  # Cache T2 results across items
    og_cache_used = 0
    if dry_run:
        print("  [DRY RUN] 跳过实际下载")

    for idx, item in enumerate(items[:max_images]):
        item_label = item.get("full_name") or item.get("name") or item.get("title", str(item))
        print(f"\n  [{idx + 1}/{total_needed}] Processing: {item_label[:80]}")

        if dry_run:
            sourced_images.append({"dry_run": True, "item": item})
            continue

        img = None
        source_used = "none"
        source_configs = get_ordered_source_configs(sources, image_strategy)

        for src_name, src_cfg in source_configs:
            if src_name == "agent_generate":
                img = t0_agent_generated_image(idx, agent_images)
                if not img:
                    print("  [T0] Agent-generated image unavailable, fallback to next source")
                    continue
            elif src_name == "github_screenshot" and github_repos and idx < len(github_repos):
                img = t1_github_screenshot(github_repos[idx], rules)
            elif src_name == "og_image" and urls:
                # Use cache if available, otherwise fetch once
                if not og_cache:
                    og_cache = t2_og_image_from_urls(urls)
                if og_cache_used < len(og_cache):
                    img = og_cache[og_cache_used]
                    og_cache_used += 1
            elif src_name == "web_search":
                query_parts = []
                if github_repos and idx < len(github_repos):
                    query_parts.append(github_repos[idx]["full_name"])
                elif project_names and idx < len(project_names):
                    query_parts.append(project_names[idx]["name"])
                elif news_items and idx < len(news_items):
                    query_parts.append(news_items[idx]["title"])
                elif company_names and idx < len(company_names):
                    query_parts.append(company_names[idx]["name"])
                elif concepts and idx < len(concepts):
                    query_parts.append(concepts[idx]["name"])
                elif data_points and idx < len(data_points):
                    query_parts.append(data_points[idx]["name"])
                query = " ".join(query_parts) if query_parts else item.get("name", item.get("title", ""))
                if query:
                    img = t3_web_search(query, rules, src_cfg)
            elif src_name == "ai_generate":
                name = item.get("full_name", item.get("name", item.get("title", "technology")))
                img = t4_ai_generate(name, rules)
            elif src_name == "fallback_pattern":
                img = t5_fallback_pattern(rules)
            elif src_name == "code_screenshot":
                # Deferred to code_image_generator.py
                print(f"  [T1] code_screenshot: skipping (use code_image_generator.py separately)")
                continue

            if img:
                source_used = src_name
                break

        if not img:
            # Ultimate fallback
            if HAS_PIL:
                img = t5_fallback_pattern(rules)
                source_used = "fallback_auto"
            else:
                print(f"  [X] Failed to get image")
                continue

        source_names_cn = {
            "agent_generate": "Agent自生成", "github_screenshot": "GitHub截图", "og_image": "OG图片",
            "web_search": "网络搜索", "ai_generate": "AI生成",
            "fallback_pattern": "几何图案", "fallback_auto": "兜底",
            "code_screenshot": "代码截图",
        }
        print(f"  [OK] Source: {source_names_cn.get(source_used, source_used)}")

        sourced_images.append({
            "data": img,
            "source": source_used,
            "item": item,
            "size_kb": len(img.getvalue()) / 1024,
        })

    if dry_run:
        return {"status": "dry_run_complete", "total_needed": total_needed, "items": items}

    # ── Step 4: Process (resize) ──
    print(f"\n[4] 处理图片 (max width={type_cfg.get('max_width_px', 670)}px)...")
    for si in sourced_images:
        resized = resize_image(si["data"], type_cfg.get("max_width_px", 670))
        if resized is not None:
            si["data"] = resized

    # ── Step 5: Upload to WeChat ──
    print(f"\n[5] 上传微信 CDN...")
    image_urls = []
    if no_upload:
        print("  [no-upload] 跳过上传")
        image_urls = ["PLACEHOLDER_URL"] * len(sourced_images)
    else:
        for si in sourced_images:
            url = upload_to_wechat(si["data"], f"illustration_{len(image_urls)+1}.png")
            if url:
                image_urls.append(url)
                si["wechat_url"] = url
                print(f"  [OK] {url[:80]}...")
            else:
                # Use placeholder
                image_urls.append("UPLOAD_FAILED")
                si["wechat_url"] = None
            time.sleep(0.5)

    # ── Step 6: Embed into HTML ──
    print(f"\n[6] 嵌入 HTML...")
    # items used for placement matching
    placement_items = (github_repos or project_names or news_items or sections
                       or company_names or concepts or data_points)
    placements = find_placement_positions(html, placement_strategy, placement_items, image_urls)
    print(f"  插入位置: {len(placements)} 处")

    new_html = insert_images_into_html(html, placements, img_template)

    # ── Step 7: Write output ──
    if output_path:
        output_file = Path(output_path)
    else:
        p = Path(article_path)
        output_file = p.parent / f"{p.stem}_illustrated{p.suffix}"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(new_html)
    print(f"  输出: {output_file}")
    print(f"  大小: {len(new_html):,} 字符 (原 {len(html):,})")

    # ── Step 8: Save summary ──
    # Save local copies
    local_paths = []
    for idx, si in enumerate(sourced_images):
        local_path = article_image_output_path(article_path, idx + 1)
        local_path.parent.mkdir(parents=True, exist_ok=True)
        with open(local_path, "wb") as f:
            f.write(si["data"].getvalue())
        local_paths.append(str(local_path))

    # Summary JSON
    summary = {
        "article": article_path,
        "output": str(output_file),
        "type": article_type,
        "total_images": len(image_urls),
        "sources_used": {},
        "images": [],
    }
    source_counts = {}
    for si in sourced_images:
        src = si["source"]
        source_counts[src] = source_counts.get(src, 0) + 1
    summary["sources_used"] = source_counts

    fallback_count = source_counts.get("fallback_pattern", 0) + source_counts.get("fallback_auto", 0)
    if fallback_count and not allow_fallback_pattern:
        print(f"\n❌ 插图门禁失败: {fallback_count} 张图片使用几何兜底。")
        print("   请提供 Agent/Codex 本地图片、真实截图/OG 图片，或显式传 --allow-fallback-pattern。")
        return {
            "status": "failed",
            "reason": "fallback_pattern_used",
            "sources_used": source_counts,
        }

    for idx, si in enumerate(sourced_images):
        summary["images"].append({
            "index": idx + 1,
            "source": si["source"],
            "item": si["item"].get("full_name") or si["item"].get("name") or si["item"].get("title", ""),
            "wechat_url": si.get("wechat_url"),
            "local_path": local_paths[idx] if idx < len(local_paths) else "",
            "size_kb": round(si["size_kb"], 1),
        })

    summary_path = REPORTS_DIR / f"illustrations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\n[Summary] Illustration report: {summary_path}")

    # Summary
    print(f"\n{'='*60}")
    print(f"完成!")
    print(f"  总插图: {len(image_urls)} 张")
    print(f"  来源: {source_counts}")
    print(f"  输出: {output_file}")
    print(f"{'='*60}")

    return summary


# ======================================================================
# Block 7: CLI
# ======================================================================

def main():
    parser = argparse.ArgumentParser(
        description="文章插图自动生成器 — 分析文章内容，自动搜索/生成配图，上传微信CDN，嵌入HTML",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python illustration_gen.py article.html --type 项目推荐
  python illustration_gen.py article.html --type 技术教程 --dry-run
  python illustration_gen.py article.html --type 深度解析 --no-upload
  python illustration_gen.py article.html --emit-image-requests reports/image_requests.json --dry-run
  python illustration_gen.py article.html --use-local-images reports/generated_images.json
  python illustration_gen.py article.html                       # 自动检测类型
        """,
    )
    parser.add_argument("article_html", help="Input HTML article file")
    parser.add_argument("--type", dest="article_type", default=None,
                        help="文章类型 (项目推荐, 技术教程, 深度解析, 早报_晚报)")
    parser.add_argument("--output", default=None, help="Output HTML path (default: *_illustrated.html)")
    parser.add_argument("--dry-run", action="store_true", help="Analyze only, do not download/upload")
    parser.add_argument("--no-upload", action="store_true", help="Skip WeChat CDN upload")
    parser.add_argument("--max-images", type=int, default=None, help="Override max_images_total")
    parser.add_argument("--image-strategy", choices=sorted(VALID_IMAGE_STRATEGIES), default=None,
                        help="Image source strategy: auto, legacy, agent_first, factual_first")
    parser.add_argument("--emit-image-requests", default=None,
                        help="Write Agent/Codex image generation request JSON")
    parser.add_argument("--use-local-images", default=None,
                        help="Read Agent/Codex generated local image manifest JSON")
    parser.add_argument("--allow-fallback-pattern", action="store_true",
                        help="Allow geometric fallback images to pass the illustration gate")

    args = parser.parse_args()

    if not os.path.exists(args.article_html):
        print(f"ERROR: 文件不存在: {args.article_html}")
        sys.exit(1)

    result = generate_illustrations(
        article_path=args.article_html,
        article_type=args.article_type,
        dry_run=args.dry_run,
        no_upload=args.no_upload,
        max_images=args.max_images,
        output_path=args.output,
        image_strategy=args.image_strategy,
        emit_image_requests=args.emit_image_requests,
        use_local_images=args.use_local_images,
        allow_fallback_pattern=args.allow_fallback_pattern,
    )

    if result.get("status") == "skipped":
        print(result.get("reason", "No content to illustrate"))
    if result.get("status") == "failed":
        sys.exit(1)


if __name__ == "__main__":
    main()
