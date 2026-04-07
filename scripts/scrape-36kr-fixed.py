#!/usr/bin/env python3
"""
抓取36氪科技频道 - 修复版本
"""

from playwright.sync_api import sync_playwright
import json
import re

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    print("📰 抓取36氪科技频道...")
    page.goto("https://36kr.com/information/technology/", wait_until='domcontentloaded')
    page.wait_for_timeout(5000)
    
    articles = []
    seen = set()  # 用 (url, title) 组合去重
    
    links = page.locator('a[href*="/p/"]').all()
    
    for link in links:
        try:
            href = link.get_attribute('href')
            if not href:
                continue
            
            # 构建完整URL
            if href.startswith('/'):
                url = f"https://www.36kr.com{href}"
            else:
                url = href
            
            # 获取标题
            title = link.text_content().strip()
            
            # 过滤无效标题
            if len(title) < 5:
                continue
            if title in ['核心服务', '登录', '注册']:
                continue
            
            # 去重
            key = (url, title)
            if key in seen:
                continue
            seen.add(key)
            
            articles.append({
                'title': title,
                'url': url,
                'source': '36氪'
            })
            
        except:
            continue
    
    print(f"✅ 获取 {len(articles)} 篇文章")
    
    # 输出
    print(f"\n📊 最新文章：")
    for i, article in enumerate(articles[:15], 1):
        print(f"\n{i}. {article['title']}")
        print(f"   URL: {article['url']}")
    
    # 保存
    with open('/home/zengshun/.openclaw/workspace/reports/materials/36kr-latest.json', 'w', encoding='utf-8') as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 已保存到: reports/materials/36kr-latest.json")
    
    browser.close()