#!/usr/bin/env python3
"""
🐱 新闻内容抓取脚本
使用 Playwright 抓取网页内容
"""

from playwright.sync_api import sync_playwright
import sys
import os

def fetch_news(url, output_path):
    """
    抓取新闻内容
    
    Args:
        url: 新闻 URL
        output_path: 输出文件路径
    """
    print(f"📰 抓取新闻: {url}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # 设置超时
        page.set_default_timeout(30000)
        
        try:
            page.goto(url, wait_until='domcontentloaded')
            
            # 提取标题
            title = page.locator('h1').first.text_content() if page.locator('h1').count() > 0 else ""
            
            # 提取正文内容（尝试多种选择器）
            content = ""
            
            # 尝试常见的内容选择器
            selectors = [
                'article',
                '.article-content',
                '.content',
                '.news-content',
                '.post-content',
                'div[class*="content"]',
                'main',
            ]
            
            for selector in selectors:
                if page.locator(selector).count() > 0:
                    content = page.locator(selector).first.inner_text()
                    if len(content) > 200:  # 找到足够长的内容就停止
                        break
            
            if not content:
                # 如果没有找到，提取所有段落
                paragraphs = page.locator('p').all_text_contents()
                content = '\n\n'.join(paragraphs)
            
            # 保存为 Markdown
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(f"# {title}\n\n")
                f.write(f"**来源**: {url}\n\n")
                f.write(content)
            
            print(f"✅ 已保存: {output_path}")
            print(f"📝 标题: {title}")
            print(f"📏 内容长度: {len(content)} 字")
            
            return title, content
            
        except Exception as e:
            print(f"❌ 抓取失败: {e}")
            return None, None
        
        finally:
            browser.close()

def main():
    if len(sys.argv) < 3:
        print("用法: python fetch-news.py <URL> <输出路径>")
        print("示例: python fetch-news.py https://example.com/news reports/news.md")
        sys.exit(1)
    
    url = sys.argv[1]
    output_path = sys.argv[2]
    
    fetch_news(url, output_path)

if __name__ == "__main__":
    main()