#!/usr/bin/env python3
"""
抓取 AI Base 新闻 - 最新AI资讯
"""

from playwright.sync_api import sync_playwright
import json
import os
import re
import sys

# 获取输出目录（支持环境变量或默认值）
OUTPUT_DIR = os.environ.get('OUTPUT_DIR', os.path.expanduser('~/.openclaw/workspace/reports/materials'))

def scrape_aibase():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print("📰 抓取 AI Base 新闻...")
        page.goto("https://www.aibase.com/zh/news", wait_until='domcontentloaded')
        page.wait_for_timeout(5000)
        
        articles = []
        seen = set()
        
        # 获取新闻链接
        links = page.locator('a[href*="/news/"]').all()
        
        for link in links:
            try:
                href = link.get_attribute('href')
                if not href:
                    continue
                
                # 构建完整URL
                if href.startswith('/'):
                    url = f"https://www.aibase.com{href}"
                else:
                    url = href
                
                # 提取文章ID
                match = re.search(r'/news/(\d+)', url)
                if not match:
                    continue
                
                article_id = match.group(1)
                
                # 去重
                if article_id in seen:
                    continue
                seen.add(article_id)
                
                # 获取完整文本
                text = link.text_content().strip()
                
                # 解析格式: "1 小时前.AIbase标题内容摘要..."
                parts = text.split('.AIbase')
                if len(parts) >= 2:
                    time_str = parts[0].strip()  # "1 小时前"
                    content = parts[1].strip()    # "标题内容摘要..."
                    
                    # 提取标题（第一句）
                    title_end = content.find('。')
                    if title_end > 0 and title_end < 80:
                        title = content[:title_end]
                    else:
                        # 找不到句号，取前50字符
                        title = content[:50]
                else:
                    # 格式不符，直接用文本
                    time_str = ""
                    title = text[:50]
                
                # 过滤无效标题
                if len(title) < 10:
                    continue
                
                articles.append({
                    'title': title,
                    'url': url,
                    'time': time_str,
                    'source': 'AI Base'
                })
                
            except:
                continue
        
        print(f"✅ 获取 {len(articles)} 篇文章")
        
        browser.close()
        return articles

if __name__ == "__main__":
    articles = scrape_aibase()
    
    # 输出到 stdout（方便管道处理）
    if '--stdout' in sys.argv:
        print(json.dumps(articles, ensure_ascii=False, indent=2))
    else:
        # 创建输出目录
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        print(f"\n📊 AI Base 最新新闻：")
        for i, article in enumerate(articles[:15], 1):
            print(f"\n{i}. [{article['time']}] {article['title']}")
            print(f"   URL: {article['url']}")
        
        # 保存到文件
        output_path = os.path.join(OUTPUT_DIR, 'aibase-latest.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 已保存到: {output_path}")