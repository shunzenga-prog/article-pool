#!/usr/bin/env python3
"""
🐱 小咪的 HTML 文章发布脚本
直接上传 HTML 文件到微信公众号草稿箱（不做 Markdown 转换）

用法: python publish_html.py <HTML文件路径> [标题] [--cover <封面图路径>]
"""

import requests
import json
import os
import sys
import argparse
import re

try:
    from preferences import get_prefs as _get_prefs
    _pub_prefs = _get_prefs()
except Exception:
    _pub_prefs = {}


def load_env():
    """加载 .env 配置，唯一来源：config/.env"""
    from paths import load_env as _load
    _load()


def log_publish(title, media_id, cover_path, author):
    """记录发布到 PUBLISH_LOG_FILE"""
    from datetime import datetime
    from paths import PUBLISH_LOG_FILE as log_file

    log = []
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                log = json.load(f)
        except (json.JSONDecodeError, ValueError):
            log = []

    entry = {
        "title": title,
        "media_id": media_id,
        "cover": os.path.basename(cover_path) if cover_path else None,
        "author": author,
        "published_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "status": "draft",
    }
    log.append(entry)

    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(log, f, ensure_ascii=False, indent=2)

    print(f"📋 已记录到发布日志: {log_file}")


def get_access_token(appid, secret):
    """获取微信 access_token"""
    url = "https://api.weixin.qq.com/cgi-bin/token"
    params = {
        "grant_type": "client_credential",
        "appid": appid,
        "secret": secret,
    }
    resp = requests.get(url, params=params, timeout=15)
    data = resp.json()
    token = data.get("access_token")
    if not token:
        print(f"❌ 获取 token 失败: {data}")
    return token


def upload_thumb(access_token, image_path):
    """上传封面缩略图，返回 thumb_media_id"""
    url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={access_token}&type=thumb"

    with open(image_path, "rb") as f:
        files = {"media": (os.path.basename(image_path), f, "image/png")}
        resp = requests.post(url, files=files, timeout=30)

    data = resp.json()
    media_id = data.get("media_id")
    if not media_id:
        print(f"❌ 封面上传失败: {data}")
    return media_id


def extract_title_from_html(html):
    """从 HTML 中提取 h1 作为标题"""
    match = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.DOTALL)
    if match:
        title = re.sub(r'<[^>]+>', '', match.group(1)).strip()
        return title
    return None


def extract_digest_from_html(html, max_len=54):
    """从 HTML 正文提取摘要（前几句纯文本）"""
    # 去掉 style/script 标签
    clean = re.sub(r'<(style|script)[^>]*>.*?</\1>', '', html, flags=re.DOTALL)
    # 去掉所有 HTML 标签
    text = re.sub(r'<[^>]+>', '', clean)
    # 去掉多余空白
    text = re.sub(r'\s+', ' ', text).strip()
    if len(text) > max_len:
        text = text[:max_len] + '…'
    return text


def validate_before_publish(article_path, html_content, title):
    """Run local structural checks before touching WeChat APIs."""
    try:
        from review_html import review
    except Exception as exc:
        print(f"⚠️  无法加载 review_html.py，跳过发布前结构审阅: {exc}")
        return

    result = review(article_path, title=title)
    if result.get("passed"):
        print("✅ 发布前结构审阅通过")
        return

    print("\n❌ 发布前结构审阅未通过，已停止创建草稿。")
    for failure in result.get("failures", []):
        print(f"  - {failure}")
    print("\n请修复 HTML 后重新运行 publish_html.py。")
    sys.exit(1)


def create_draft(access_token, title, html_content, thumb_media_id, author="小咪", digest=None):
    """创建公众号草稿（直接使用 HTML，不做转换）"""
    url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={access_token}"

    if digest is None:
        digest = extract_digest_from_html(html_content)

    data = {
        "articles": [{
            "title": title,
            "content": html_content,
            "thumb_media_id": thumb_media_id,
            "author": author,
            "digest": digest,
            "need_open_comment": 0,
            "only_fans_can_comment": 0,
        }]
    }

    json_data = json.dumps(data, ensure_ascii=False).encode('utf-8')
    resp = requests.post(
        url,
        data=json_data,
        headers={'Content-Type': 'application/json; charset=utf-8'},
        timeout=30,
    )
    return resp.json()


def main():
    parser = argparse.ArgumentParser(description="直接上传 HTML 到微信公众号草稿箱")
    parser.add_argument("article", help="HTML 文章文件路径")
    parser.add_argument("title", nargs="?", default=None, help="文章标题（可选，默认从 h1 提取）")
    parser.add_argument("--cover", default=None, help="封面图路径（可选）")
    default_author = _pub_prefs.get('author', {}).get('name', '小咪')
    parser.add_argument("--author", default=default_author, help=f"作者名（默认：{default_author}）")
    args = parser.parse_args()

    # 加载配置
    load_env()
    appid = os.getenv("WECHAT_APPID")
    secret = os.getenv("WECHAT_SECRET")

    if not appid or not secret or "your_" in appid.lower():
        print("\n❌ 请先配置微信公众号 API 密钥！")
        print("\n将 config/.env.example 复制为 config/.env，填入：")
        print("  WECHAT_APPID=你的AppID")
        print("  WECHAT_SECRET=你的AppSecret")
        print("\n获取方式：登录 mp.weixin.qq.com → 设置与开发 → 基本配置")
        sys.exit(1)

    # 读取文章
    if not os.path.exists(args.article):
        print(f"❌ 文件不存在: {args.article}")
        sys.exit(1)

    with open(args.article, "r", encoding="utf-8") as f:
        html_content = f.read()
    publish_article_path = args.article

    # 自动检测本地图片并上传到微信 CDN
    local_imgs = re.findall(r'<img\s[^>]*src="(?!https?://|data:)([^"]+)"', html_content)
    if local_imgs:
        print(f"\n🖼️  检测到 {len(local_imgs)} 张本地图片，正在上传到微信 CDN...")
        from replace_local_images import process_html
        process_html(args.article)
        cdn_path = args.article.replace(".html", "_cdn.html")
        if os.path.exists(cdn_path):
            with open(cdn_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            publish_article_path = cdn_path
            print(f"✅ 已替换为 CDN 版本: {cdn_path}")
        else:
            print(f"⚠️  CDN 替换未生成，使用原始文件继续")

    # 标题
    title = args.title or extract_title_from_html(html_content)
    if not title:
        print("❌ 无法提取标题，请通过命令行参数指定")
        sys.exit(1)

    print(f"\n📝 标题: {title}")
    print(f"📄 文章大小: {len(html_content)} 字符")

    validate_before_publish(publish_article_path, html_content, title)

    # 获取 token
    print("\n🔑 正在获取 access_token...")
    token = get_access_token(appid, secret)
    if not token:
        sys.exit(1)
    print("✅ Token 获取成功")

    # 上传封面图
    thumb_media_id = ""
    cover_path = args.cover

    if cover_path and os.path.exists(cover_path):
        print(f"\n🖼️ 正在上传封面图: {cover_path}")
        thumb_media_id = upload_thumb(token, cover_path)
        if thumb_media_id:
            print(f"✅ 封面图上传成功")
    else:
        print("\n⚠️ 未提供封面图，将使用默认样式")

    # 创建草稿
    print(f"\n📤 正在创建草稿...")
    result = create_draft(
        token, title, html_content,
        thumb_media_id, author=args.author
    )

    if "media_id" in result:
        print(f"\n{'='*50}")
        print(f"✅ 草稿创建成功！")
        print(f"📝 草稿 ID: {result['media_id']}")
        print(f"👉 请登录公众号后台 → 草稿箱 查看并群发")
        print(f"{'='*50}")

        # 记录发布日志
        log_publish(title, result['media_id'], cover_path, args.author)
    else:
        print(f"\n❌ 创建失败: {json.dumps(result, ensure_ascii=False, indent=2)}")
        if "errcode" in result:
            # 常见错误提示
            err_codes = {
                40001: "AppSecret 错误或 access_token 无效",
                40007: "不合法的媒体文件 id（封面图问题）",
                40014: "不合法的 access_token",
                40164: "未上传封面图（thumb_media_id 必填）",
                41001: "缺少 access_token 参数",
                42001: "access_token 超时",
                45009: "接口调用超过限制",
            }
            hint = err_codes.get(result["errcode"], "")
            if hint:
                print(f"💡 {hint}")
        sys.exit(1)


if __name__ == "__main__":
    main()
