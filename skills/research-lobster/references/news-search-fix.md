# 新闻搜索流程修复方案

## 问题诊断

### 问题1：Brave Search 参数不生效

**现象：**
- 设置 `date_after="2026-04-07"`，但返回2025年12月的内容
- 设置 `freshness="day"`，但混入多周/多月前的内容

**原因：**
- Brave Search API 可能不支持 `date_after` 参数
- `freshness` 参数行为不符合预期

### 问题2：搜索结果时间不可靠

**现象：**
- "7 hours ago" 这样的相对时间不准确
- 需要访问实际页面验证发布日期

## 解决方案

### 方案1：搜索后验证（推荐）

```python
# 1. 搜索（不过滤时间）
web_search(query="AI 新闻", count=20)

# 2. 验证每条新闻的发布日期
for result in results:
    actual_date = verify_publish_date(result.url)
    if actual_date >= target_date:
        keep(result)
    else:
        discard(result)
```

### 方案2：直接访问新闻源

```python
# 直接抓取目标网站
sources = [
    "https://36kr.com/information/technology/",
    "https://www.jiqizhixin.com/",
    "https://www.qbitai.com/",
]

for source in sources:
    articles = scrape_latest_articles(source, count=5)
    # 文章本身就是最新的
```

### 方案3：使用 RSS Feed

```python
# 订阅科技媒体的 RSS
rss_feeds = [
    "https://36kr.com/feed",
    "https://www.qbitai.com/feed",
]

for feed in rss_feeds:
    articles = parse_rss(feed, since=yesterday)
```

## 推荐流程

**新闻类内容：**

1. **直接访问新闻源**（方案2）
   - 抓取36氪、机器之心、量子位等科技媒体的最新文章
   - 文章本身就是最新的，无需验证

2. **或使用RSS Feed**（方案3）
   - 更高效，直接获取结构化数据

**指定主题创作：**

1. **搜索 + 验证**（方案1）
   - 先搜索相关主题
   - 再验证每条内容的发布日期

## 实现示例

### 抓取36氪最新AI文章

```python
from playwright.sync_api import sync_playwright

def scrape_36kr_ai_news(count=10):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://36kr.com/information/technology/")
        
        articles = []
        items = page.locator('.article-item').all()[:count]
        
        for item in items:
            title = item.locator('a').text_content()
            url = item.locator('a').get_attribute('href')
            date = item.locator('.time').text_content()
            
            articles.append({
                'title': title,
                'url': f"https://36kr.com{url}",
                'date': date
            })
        
        browser.close()
        return articles
```

## 下一步行动

1. ✅ 创建直接抓取新闻源的脚本
2. ✅ 实现 RSS Feed 解析
3. ✅ 更新 news-aggregator skill
4. ✅ 测试验证

---

*创建时间：2026-04-07*
*问题类型：搜索API参数不生效*