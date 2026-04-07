#!/usr/bin/env python3
"""
🐱 智能封面图生成脚本
根据文章内容自动生成封面图

用法: python generate-cover.py <文章路径> [--output <输出路径>]

支持的封面图来源：
1. Pollinations AI（免费，无需 API）
2. Unsplash（免费，高质量图片）
3. 本地图片库（预设封面图）
"""

import requests
import re
import os
import sys
import hashlib
from urllib.parse import quote

# 封面图模板库（按主题分类）- 使用可靠的图片源
COVER_TEMPLATES = {
    "news": [
        "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=900&h=500&fit=crop",
        "https://images.unsplash.com/photo-1495020689067-958852a7765e?w=900&h=500&fit=crop",
    ],
    "ai": [
        "https://images.unsplash.com/photo-1677442136019-21780ecad995?w=900&h=500&fit=crop",
        "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?w=900&h=500&fit=crop",
    ],
    "gpt": [
        "https://images.unsplash.com/photo-1531746790731-6c087fecd65a?w=900&h=500&fit=crop",
        "https://images.unsplash.com/photo-1677442136019-21780ecad995?w=900&h=500&fit=crop",
    ],
    "coding": [
        "https://images.unsplash.com/photo-1461749280684-dccba630e2f6?w=900&h=500&fit=crop",
        "https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=900&h=500&fit=crop",
    ],
    "business": [
        "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=900&h=500&fit=crop",
        "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=900&h=500&fit=crop",
    ],
    "money": [
        "https://images.unsplash.com/photo-1579621970563-ebec7560ff3e?w=900&h=500&fit=crop",
        "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=900&h=500&fit=crop",
    ],
    "innovation": [
        "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=900&h=500&fit=crop",
        "https://images.unsplash.com/photo-1518770660439-4636190af475?w=900&h=500&fit=crop",
    ],
    "default": [
        "https://images.unsplash.com/photo-1504639725590-34d0984388bd?w=900&h=500&fit=crop",
        "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=900&h=500&fit=crop",
    ]
}

# 关键词到主题的映射
KEYWORD_TO_THEME = {
    # 新闻/日报
    "日报": "news", "新闻": "news", "热点": "news", "快讯": "news",
    
    # AI 相关
    "ai": "ai", "人工智能": "ai", "机器学习": "ai", "深度学习": "ai",
    
    # GPT 相关
    "gpt": "gpt", "chatgpt": "gpt", "openai": "gpt", "claude": "gpt",
    "llm": "gpt", "大模型": "gpt", "语言模型": "gpt",
    
    # 编程相关
    "代码": "coding", "编程": "coding", "开发": "coding", "插件": "coding",
    "api": "coding", "sdk": "coding", "开发者": "coding",
    
    # 商业相关
    "广告": "business", "商业": "business", "企业": "business", "转型": "business",
    
    # 金钱相关
    "赚钱": "money", "收入": "money", "变现": "money", "成本": "money",
    
    # 创新相关
    "创新": "innovation", "更新": "innovation", "发布": "innovation", "推出": "innovation",
}


def extract_keywords(content, max_keywords=5):
    """从文章内容提取关键词"""
    # 提取标题
    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    title = title_match.group(1) if title_match else ""
    
    # 合并标题和前 500 字
    text = title + " " + content[:500]
    
    # 提取关键词
    keywords = []
    text_lower = text.lower()
    
    for keyword, theme in KEYWORD_TO_THEME.items():
        if keyword in text_lower:
            keywords.append(keyword)
            if len(keywords) >= max_keywords:
                break
    
    return keywords


def get_theme_from_keywords(keywords):
    """根据关键词确定主题"""
    theme_counts = {}
    
    for keyword in keywords:
        if keyword in KEYWORD_TO_THEME:
            theme = KEYWORD_TO_THEME[keyword]
            theme_counts[theme] = theme_counts.get(theme, 0) + 1
    
    if theme_counts:
        return max(theme_counts, key=theme_counts.get)
    return "default"


def generate_pollinations_url(prompt, style="modern tech"):
    """生成 Pollinations AI 图片 URL"""
    # 添加风格关键词
    full_prompt = f"{prompt}, {style}, high quality, professional, 16:9 aspect ratio"
    encoded_prompt = quote(full_prompt)
    
    return f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=900&height=500&nologo=true"


def generate_custom_cover(keywords, title):
    """根据关键词和标题生成自定义封面图 URL"""
    # 从标题提取关键概念
    title_lower = title.lower()
    
    # 根据关键词组合生成 prompt
    if any(k in title_lower for k in ["gpt", "openai", "chatgpt"]):
        prompt = "OpenAI GPT AI assistant futuristic hologram blue purple"
    elif any(k in title_lower for k in ["成本", "省钱", "价格"]):
        prompt = "cost reduction money saving business growth chart"
    elif any(k in title_lower for k in ["架构", "代理", "agent"]):
        prompt = "AI agent network architecture diagram nodes connections"
    elif any(k in title_lower for k in ["教程", "入门", "指南"]):
        prompt = "step by step tutorial guide book lightbulb idea"
    else:
        # 根据关键词组合
        keyword_str = " ".join(keywords[:3]) if keywords else "technology"
        prompt = f"{keyword_str} modern tech illustration"
    
    return generate_pollinations_url(prompt)


def get_cover_url(keywords, title, use_template=False):
    """获取封面图 URL"""
    theme = get_theme_from_keywords(keywords)
    
    # 默认使用 Pollinations AI（免费稳定）
    if not use_template:
        # 根据关键词和标题生成 Pollinations URL
        return generate_custom_cover(keywords, title)
    
    # 方案2：使用 Unsplash 模板库（可选）
    templates = COVER_TEMPLATES.get(theme, COVER_TEMPLATES["default"])
    title_hash = int(hashlib.md5(title.encode()).hexdigest(), 16) % len(templates)
    return templates[title_hash]


def download_image(url, output_path):
    """下载图片"""
    print(f"📥 下载封面图: {url[:80]}...")
    
    resp = requests.get(url, timeout=30)
    if resp.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(resp.content)
        print(f"✅ 封面图已保存: {output_path}")
        return True
    else:
        print(f"❌ 下载失败: HTTP {resp.status_code}")
        return False


def main():
    if len(sys.argv) < 2:
        print("用法: python generate-cover.py <文章路径> [--output <输出路径>] [--template]")
        print("\n选项:")
        print("  --output  指定输出路径（默认同目录 images/cover.jpg）")
        print("  --template  使用 Unsplash 模板库（默认用 Pollinations AI）")
        sys.exit(1)
    
    article_path = sys.argv[1]
    use_template = "--template" in sys.argv
    
    # 默认使用 Pollinations AI（稳定、免费）
    
    # 解析输出路径
    if "--output" in sys.argv:
        output_idx = sys.argv.index("--output") + 1
        output_path = sys.argv[output_idx] if output_idx < len(sys.argv) else None
    else:
        # 默认输出到文章同目录的 images 文件夹
        article_dir = os.path.dirname(article_path)
        images_dir = os.path.join(article_dir, "images")
        os.makedirs(images_dir, exist_ok=True)
        output_path = os.path.join(images_dir, "cover.jpg")
    
    # 读取文章
    with open(article_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 提取标题
    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    title = title_match.group(1) if title_match else "article"
    
    # 提取关键词
    keywords = extract_keywords(content)
    print(f"📝 标题: {title}")
    print(f"🔑 关键词: {keywords}")
    
    # 获取封面图 URL
    cover_url = get_cover_url(keywords, title, use_template=use_template)
    print(f"🎨 主题: {get_theme_from_keywords(keywords)}")
    print(f"📌 方案: {'Unsplash 模板库' if use_template else 'Pollinations AI'}")
    
    # 下载图片
    if download_image(cover_url, output_path):
        print(f"\n✅ 封面图生成成功！")
        print(f"📂 路径: {output_path}")
        return output_path
    else:
        # 失败时使用默认图片
        print("\n⚠️ 使用备用封面图")
        return None


if __name__ == "__main__":
    main()