#!/usr/bin/env python3
"""
直接抓取科技媒体最新文章
不依赖搜索引擎的时间过滤
"""

from playwright.sync_api import sync_playwright
import json
import sys
from datetime import datetime

def scrape_36kr_tech(count=10):
    """抓取36氪科技频道最新文章"""
    articles = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_default_timeout(20000)
        
        try:
            print("📰 抓取36氪科技频道...")
            page.goto("https://36kr.com/information/technology/", wait_until='domcontentloaded')
            page.wait_for_timeout(2000)  # 等待加载
            
            # 查找文章列表
            items = page.locator('.information-flow-list .information-item').all()[:count]
            
            for item in items:
                try:
                    title_elem = item.locator('.article-item-title a, .title-wrapper a').first
                    title = title_elem.text_content().strip()
                    url = title_elem.get_attribute('href')
                    
                    if url and not url.startswith('http'):
                        url = f"https://36kr.com{url}"
                    
                    # 尝试获取时间
                    time_elem = item.locator('.time, .date').first
                    date_str = time_elem.text_content().strip() if time_elem.count() > 0 else ""
                    
                    articles.append({
                        'title': title,
                        'url': url,
                        'date': date_str,
                        'source': '36氪'
                    })
                    
                except Exception as e:
                    print(f"  ⚠️ 解析文章失败: {e}")
                    continue
            
            print(f"  ✅ 获取 {len(articles)} 篇文章")
            
        except Exception as e:
            print(f"  ❌ 抓取失败: {e}")
        
        finally:
            browser.close()
    
    return articles

def scrape_qbitai(count=10):
    """抓取量子位最新文章"""
    articles = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_default_timeout(20000)
        
        try:
            print("📰 抓取量子位...")
            page.goto("https://www.qbitai.com/", wait_until='domcontentloaded')
            page.wait_for_timeout(2000)
            
            # 查找文章
            items = page.locator('article, .post, .article-item').all()[:count]
            
            for item in items:
                try:
                    title_elem = item.locator('a').first
                    title = title_elem.text_content().strip()
                    url = title_elem.get_attribute('href')
                    
                    articles.append({
                        'title': title,
                        'url': url,
                        'date': '',
                        'source': '量子位'
                    })
                    
                except:
                    continue
            
            print(f"  ✅ 获取 {len(articles)} 篇文章")
            
        except Exception as e:
            print(f"  ❌ 抓取失败: {e}")
        
        finally:
            browser.close()
    
    return articles

def scrape_jiqizhixin(count=10):
    """抓取机器之心最新文章"""
    articles = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_default_timeout(20000)
        
        try:
            print("📰 抓取机器之心...")
            page.goto("https://www.jiqizhixin.com/", wait_until='domcontentloaded')
            page.wait_for_timeout(2000)
            
            items = page.locator('.article-item, article, .post').all()[:count]
            
            for item in items:
                try:
                    title_elem = item.locator('a').first
                    title = title_elem.text_content().strip()
                    url = title_elem.get_attribute('href')
                    
                    if url and not url.startswith('http'):
                        url = f"https://www.jiqizhixin.com{url}"
                    
                    articles.append({
                        'title': title,
                        'url': url,
                        'date': '',
                        'source': '机器之心'
                    })
                    
                except:
                    continue
            
            print(f"  ✅ 获取 {len(articles)} 篇文章")
            
        except Exception as e:
            print(f"  ❌ 抓取失败: {e}")
        
        finally:
            browser.close()
    
    return articles

def main():
    print("=" * 50)
    print("直接抓取科技媒体最新文章")
    print("=" * 50)
    
    all_articles = []
    
    # 抓取多个源
    all_articles.extend(scrape_36kr_tech(count=10))
    all_articles.extend(scrape_qbitai(count=5))
    all_articles.extend(scrape_jiqizhixin(count=5))
    
    print(f"\n📊 总计获取 {len(all_articles)} 篇文章")
    
    # 输出
    if len(sys.argv) > 1:
        output_path = sys.argv[1]
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_articles, f, ensure_ascii=False, indent=2)
        print(f"✅ 已保存到: {output_path}")
    else:
        # 打印
        for i, article in enumerate(all_articles[:10], 1):
            print(f"\n{i}. {article['title'][:50]}...")
            print(f"   来源: {article['source']}")
            print(f"   URL: {article['url']}")
    
    return all_articles

if __name__ == "__main__":
    main()