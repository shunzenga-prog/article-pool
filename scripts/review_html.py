#!/usr/bin/env python3
"""
HTML 结构审阅脚本 — 扫描公众号文章 HTML，执行硬检查和软检查。

硬检查（任一失败 → 驳回）:
  H1: 外层 table 包裹全文检查
  H2: <div>/<section> 禁用标签检查
  H3: <p> 标签上的 font-size/color 样式检查
  H4: 正文首屏重复公众号系统标题检查
  H5: 新闻播报腔/AI 味表达检查
  H6: emoji/猫咪身份标识检查

软检查（失败 → 警告）:
  S1: 章节标题下划线数量
  S2: 颜色种类数量
  S3: 金句检查
  S4: 行动号召检查

用法:
  python scripts/review_html.py article.html
  python scripts/review_html.py article.html --json        # JSON 输出
  python scripts/review_html.py article.html --tutorial    # 教程模式（额外检查）
"""

import argparse
import json
import re
import sys
from pathlib import Path


def normalize_text(text: str) -> str:
    """Normalize visible text for duplicate-title comparisons."""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', '', text)
    return text.strip().lower()


def infer_title_from_path(path: Path) -> str | None:
    """Infer a likely article title from article filename, e.g. 0517-Title.html."""
    stem = path.stem
    stem = re.sub(r'_cdn$|_illustrated$', '', stem)
    match = re.match(r'^\d{4}[-_](.+)$', stem)
    if match:
        return match.group(1)
    return None


def first_visible_block_text(html: str) -> str:
    """Return text from the first visible content block after comments/meta."""
    clean = re.sub(r'^\s*(?:<!--.*?-->\s*)+', '', html, flags=re.DOTALL)
    clean = re.sub(r'^\s*<meta\b[^>]*>\s*', '', clean, flags=re.IGNORECASE)
    match = re.search(r'<(h[1-6]|p|td)\b[^>]*>(.*?)</\1>', clean, flags=re.DOTALL | re.IGNORECASE)
    if not match:
        return ""
    return re.sub(r'<[^>]+>', '', match.group(2)).strip()


def review(html_path: str, tutorial: bool = False, title: str | None = None) -> dict:
    """扫描 HTML 文件，返回结构化审阅报告。"""
    path = Path(html_path)
    if not path.exists():
        return {"passed": False, "error": f"File not found: {html_path}"}

    html = path.read_text(encoding="utf-8")
    lines = html.split("\n")

    # ── H1: 外层 table 包裹检查 ──────────────────────
    # meta 后的第一个非空、非注释内容标签如果是 <table，说明全文被包裹
    h1_fail = False
    after_meta = False
    for line in lines:
        stripped = line.strip()
        if not after_meta:
            if stripped.startswith("<meta") or stripped.startswith("<!--"):
                continue
            after_meta = True
        if not stripped or stripped.startswith("<!--"):
            continue
        if stripped.startswith("<table"):
            h1_fail = True
        break

    # ── H2: 禁用标签检查 ────────────────────────────
    div_count = len(re.findall(r'<div\b|</div>', html, re.IGNORECASE))
    section_count = len(re.findall(r'<section\b|</section>', html, re.IGNORECASE))
    h2_count = div_count + section_count

    # ── H3: <p> 上的样式检查 ────────────────────────
    # Match font-size or standalone color on <p> tags (not <pre>, <path>, etc.)
    p_style_matches = re.findall(
        r'<p[\s>][^>]*style="[^"]*(?:font-size|(?<!background-)color)\s*:', html, re.IGNORECASE
    )
    h3_count = len(p_style_matches)

    # ── H4: 正文首屏重复标题检查 ──────────────────────
    # 微信公众号会在正文外自动渲染标题；正文第一块再次写同名大标题会造成预览重复。
    comparison_title = title or infer_title_from_path(path)
    first_block_text = first_visible_block_text(html)
    h4_fail = bool(
        comparison_title
        and first_block_text
        and normalize_text(first_block_text) == normalize_text(comparison_title)
    )

    # ── H5: 新闻播报腔/AI 味表达检查 ──────────────────
    # 公众号文章允许具体日期，但避免“北京时间/当地时间/截至发稿”这类新闻口播式表达。
    broadcast_patterns = [
        r'北京时间\s*\d{1,2}\s*月\s*\d{1,2}\s*日',
        r'当地时间\s*\d{1,2}\s*月\s*\d{1,2}\s*日',
        r'截至发稿',
        r'记者了解到',
        r'据悉[，,]',
    ]
    broadcast_matches = []
    for pattern in broadcast_patterns:
        broadcast_matches.extend(re.findall(pattern, html, re.IGNORECASE))

    # ── H6: emoji/猫咪身份标识检查 ───────────────────
    emoji_pattern = re.compile(
        "["
        "\U0001F300-\U0001FAFF"
        "\U00002700-\U000027BF"
        "\U00002600-\U000026FF"
        "]",
        re.UNICODE,
    )
    emoji_matches = emoji_pattern.findall(html)
    cat_identity_matches = re.findall(r'🐱|🐈|😺|猫咪图标|小咪\s*[🐱🐈😺]', html)

    # ── S1: 章节标题下划线 ──────────────────────────
    border_bottom_count = len(re.findall(r'border-bottom', html))

    # ── S2: 颜色种类 ────────────────────────────────
    colors = set(re.findall(r'color\s*:\s*(#[0-9a-fA-F]{3,8})', html))
    bg_colors = set(re.findall(r'background-color\s*:\s*(#[0-9a-fA-F]{3,8})', html))
    all_colors = colors | bg_colors
    s2_count = len(all_colors)

    # ── S3: 金句检查 ────────────────────────────────
    # 检测: 居中加粗的独立引用段，或带有特殊样式的强调句
    golden_patterns = [
        r'text-align\s*:\s*center[^>]*>.*<strong>',  # 居中+加粗
        r'<blockquote[^>]*>',  # 引用块
    ]
    s3_found = any(re.search(p, html, re.IGNORECASE) for p in golden_patterns)

    # ── S4: 行动号召 ────────────────────────────────
    cta_keywords = ["评论区", "你怎么看", "转发", "点赞", "在看", "后台回复", "关注", "下一篇", "下期", "教程"]
    s4_found = any(kw in html for kw in cta_keywords)

    # ── 教程额外检查 ────────────────────────────────
    tutorial_checks = {}
    if tutorial:
        img_count = len(re.findall(r'<img\b', html))
        pre_count = len(re.findall(r'<pre\b', html))
        # Strip <style> and <script> blocks before counting chars (avoid CSS/JS pollution)
        clean = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        clean = re.sub(r'<script[^>]*>.*?</script>', '', clean, flags=re.DOTALL | re.IGNORECASE)
        clean = re.sub(r'<[^>]+>', '', clean)
        clean = clean.replace('\n', '').replace(' ', '')
        word_count = len(clean)
        tutorial_checks = {
            "t_img_count": img_count,
            "t_code_block_count": pre_count,
            "t_approx_chars": word_count,
            "t_img_per_1500_chars": round(img_count / max(word_count / 1500, 1), 1),
        }

    # ── 判定 ────────────────────────────────────────
    hard_failures = []
    if h1_fail:
        hard_failures.append("H1: 外层 <table> 包裹全文")
    if h2_count > 0:
        hard_failures.append(f"H2: {h2_count} 处 <div>/<section> 标签")
    if h3_count > 0:
        hard_failures.append(f"H3: {h3_count} 处 <p> 标签上有 font-size/color 样式")
    if h4_fail:
        hard_failures.append("H4: 正文首块内容重复公众号系统标题")
    if broadcast_matches:
        hard_failures.append(f"H5: 新闻播报腔/AI 味表达 {len(broadcast_matches)} 处")
    if emoji_matches or cat_identity_matches:
        hard_failures.append(f"H6: emoji/猫咪身份标识 {len(emoji_matches) + len(cat_identity_matches)} 处")

    soft_warnings = []
    if border_bottom_count < 2:
        soft_warnings.append(f"S1: border-bottom 仅 {border_bottom_count} 处（建议 ≥2）")
    if s2_count > 8:
        soft_warnings.append(f"S2: 颜色种类 {s2_count} 种（建议 ≤8）")
    if not s3_found:
        soft_warnings.append("S3: 未检测到金句")
    if not s4_found:
        soft_warnings.append("S4: 未检测到行动号召")

    passed = len(hard_failures) == 0
    if passed and soft_warnings:
        verdict = "WARNINGS"
    elif passed:
        verdict = "APPROVED"
    else:
        verdict = "REJECTED"

    return {
        "passed": passed,
        "verdict": verdict,
        "hard_checks": {
            "h1_root_tables": {"status": "FAIL" if h1_fail else "PASS", "detail": "外层table包裹" if h1_fail else "无外层table"},
            "h2_forbidden_tags": {"status": "FAIL" if h2_count > 0 else "PASS", "count": h2_count},
            "h3_style_on_p": {"status": "FAIL" if h3_count > 0 else "PASS", "count": h3_count},
            "h4_duplicate_title": {
                "status": "FAIL" if h4_fail else "PASS",
                "detail": first_block_text if h4_fail else "无重复标题",
            },
            "h5_broadcast_tone": {
                "status": "FAIL" if broadcast_matches else "PASS",
                "count": len(broadcast_matches),
                "detail": broadcast_matches[:5] if broadcast_matches else "无新闻播报腔表达",
            },
            "h6_emoji_identity": {
                "status": "FAIL" if (emoji_matches or cat_identity_matches) else "PASS",
                "count": len(emoji_matches) + len(cat_identity_matches),
                "detail": (emoji_matches + cat_identity_matches)[:5] if (emoji_matches or cat_identity_matches) else "无 emoji/猫咪身份标识",
            },
        },
        "soft_checks": {
            "s1_title_underline": {"status": "WARN" if border_bottom_count < 2 else "PASS", "count": border_bottom_count},
            "s2_color_count": {"status": "WARN" if s2_count > 8 else "PASS", "count": s2_count},
            "s3_golden_sentence": {"status": "WARN" if not s3_found else "PASS"},
            "s4_call_to_action": {"status": "WARN" if not s4_found else "PASS"},
        },
        "failures": hard_failures,
        "warnings": soft_warnings,
        "tutorial": tutorial_checks,
    }


def main():
    p = argparse.ArgumentParser(description="HTML 结构审阅 — 硬检查 + 软检查")
    p.add_argument("html", help="文章 HTML 文件路径")
    p.add_argument("--json", action="store_true", help="JSON 格式输出")
    p.add_argument("--tutorial", action="store_true", help="教程模式（额外检查截图覆盖率等）")
    p.add_argument("--title", default=None, help="公众号系统标题，用于检测正文首屏重复标题")
    args = p.parse_args()

    result = review(args.html, tutorial=args.tutorial, title=args.title)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"REVIEW_RESULT:")
        print(f"  passed: {result['passed']}")
        print(f"  verdict: {result['verdict']}")
        print()
        print(f"  hard_checks:")
        for k, v in result["hard_checks"].items():
            print(f"    {k}: {v['status']} — {v.get('detail', v.get('count', ''))}")
        print()
        print(f"  soft_checks:")
        for k, v in result["soft_checks"].items():
            print(f"    {k}: {v['status']} (count={v.get('count', 'N/A')})")
        if result["failures"]:
            print(f"\n  ❌ 驳回原因:")
            for f in result["failures"]:
                print(f"    - {f}")
        if result["warnings"]:
            print(f"\n  ⚠️ 警告:")
            for w in result["warnings"]:
                print(f"    - {w}")
        if result.get("tutorial"):
            t = result["tutorial"]
            print(f"\n  📖 教程统计:")
            print(f"    截图: {t['t_img_count']} 张 | 代码块: {t['t_code_block_count']} 个")
            print(f"    约 {t['t_approx_chars']} 字 | 每1500字图: {t['t_img_per_1500_chars']} 张")

    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
