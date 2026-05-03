#!/usr/bin/env python3
"""
🐱 公众号图片上传工具
上传图片到微信公众号，获取 URL 用于文章插图
"""

import requests
import json
import os
import sys

from paths import load_env as _load_env
_load_env()
APPID = os.getenv("WECHAT_APPID")
SECRET = os.getenv("WECHAT_SECRET")

# 缓存 access_token
_token_cache = None

def get_access_token():
    """获取 access_token"""
    global _token_cache
    if _token_cache:
        return _token_cache
    
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APPID}&secret={SECRET}"
    resp = requests.get(url)
    data = resp.json()
    
    if "access_token" in data:
        _token_cache = data["access_token"]
        return _token_cache
    else:
        print(f"❌ 获取 token 失败：{data}")
        return None

def upload_image(image_path):
    """
    上传图片到公众号
    返回图片 URL，可直接在文章 HTML 中使用
    """
    token = get_access_token()
    if not token:
        return None
    
    if not os.path.exists(image_path):
        print(f"❌ 文件不存在：{image_path}")
        return None
    
    # 检查文件大小（2MB 限制）
    file_size = os.path.getsize(image_path)
    if file_size > 2 * 1024 * 1024:
        print(f"❌ 文件过大（{file_size/1024/1024:.2f}MB），限制 2MB")
        return None
    
    url = f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={token}"
    
    with open(image_path, "rb") as f:
        files = {"media": f}
        resp = requests.post(url, files=files)
    
    data = resp.json()
    
    if "url" in data:
        print(f"✅ 上传成功：{image_path}")
        print(f"📷 URL: {data['url']}")
        return data["url"]
    else:
        print(f"❌ 上传失败：{data}")
        return None

def upload_batch(image_paths):
    """批量上传图片"""
    results = {}
    for path in image_paths:
        url = upload_image(path)
        if url:
            results[path] = url
    return results

def main():
    if len(sys.argv) < 2:
        print("用法：python wechat-upload-image.py <图片路径> [图片路径2] ...")
        print("示例：python wechat-upload-image.py cover.png slide1.png")
        sys.exit(1)
    
    image_paths = sys.argv[1:]
    
    if len(image_paths) == 1:
        url = upload_image(image_paths[0])
        if url:
            print(f"\n复制到文章中：<img src=\"{url}\">")
    else:
        results = upload_batch(image_paths)
        print(f"\n📊 批量上传完成：{len(results)}/{len(image_paths)}")
        for path, url in results.items():
            print(f"  {path} → {url}")

if __name__ == "__main__":
    main()