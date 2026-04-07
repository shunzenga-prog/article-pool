---
name: news-aggregator
description: 资讯整合Agent - 根据场景智能抓取、验证、整理新闻素材，供创作Agent使用。支持早报/晚报/周报/月报/指定主题/知识分享等多种场景。
---

# 资讯整合 Agent

为创作Agent提供验证后的新闻素材。

## ⚠️ 重要：搜索方式变更

**Brave Search 时间过滤参数不生效！**

- `date_after` 参数无效
- `freshness` 参数效果不稳定
- 必须使用直接抓取新闻源的方式

## 核心原则

1. **直接抓取新闻源** - 不依赖搜索引擎时间过滤
2. **验证时效性** - 确认每条新闻的发布日期
3. **来源可靠** - 优先官方/主流媒体
4. **场景适配** - 根据场景选择数据源

---

## 使用场景

### 场景1：早报（获取昨天新闻）

```bash
# 直接抓取36氪等科技媒体最新文章
python scripts/scrape-36kr-fixed.py > reports/materials/36kr-latest.json

# 或抓取多个源
python scripts/scrape-news-sources.py reports/materials/news-latest.json
```

### 场景2：晚报（获取今天新闻）

```bash
# 同早报，抓取最新文章即可
python scripts/scrape-36kr-fixed.py
```

### 场景3：周报（过去7天）

```python
# 方案1：抓取新闻后按日期过滤
articles = scrape_news_sources()
recent_articles = [a for a in articles if is_within_days(a, 7)]

# 方案2：RSS Feed 订阅
import feedparser
feed = feedparser.parse("https://36kr.com/feed")
```

### 场景4：月报（过去30天）

```python
# 同周报，按日期过滤
articles = scrape_news_sources()
recent_articles = [a for a in articles if is_within_days(a, 30)]
```

### 场景5：指定主题创作（不限制时间）

```python
# 使用 Brave Search 搜索主题（不过滤时间）
web_search(query="指定主题关键词", count=15)

# 验证每条内容的发布日期
for result in results:
    verify_publish_date(result.url)
```

### 场景6：知识/技术/工具分享（不限制时间）

```python
# 使用 Brave Search 搜索技术教程
web_search(query="技术关键词 教程", count=10)

# 验证内容时效性和准确性
```

---

## 工作流程

### 输入参数

```python
{
  "scene": "morning|evening|weekly|monthly|topic|knowledge",
  "topic": "可选，指定主题",
  "sources": ["36kr", "qbitai", "jiqizhixin"],  # 新闻源
  "count": 10  # 每个源的数量
}
```

### 执行步骤

```
1. 确定场景 → 选择数据源
2. 直接抓取新闻源 → 获取最新文章
3. 文章本身即最新 → 无需时间过滤
4. 去重、排序 → 按重要性排序
5. 输出素材文件
```

### 新闻源优先级

| 优先级 | 来源 | 类型 | 抓取方式 | 脚本 |
|--------|------|------|----------|------|
| ⭐⭐⭐⭐⭐ | AI Base | AI资讯 | Playwright | `scrape-aibase-v2.py` |
| ⭐⭐⭐⭐⭐ | 36氪 | 科技媒体 | Playwright | `scrape-36kr-fixed.py` |
| ⭐⭐⭐⭐ | 量子位 | AI媒体 | Playwright | 待开发 |
| ⭐⭐⭐⭐ | 机器之心 | AI媒体 | Playwright | 待开发 |
| ⭐⭐⭐ | 微软官方 | 官方公告 | web_fetch | - |
| ⭐⭐⭐ | OpenAI Blog | 官方公告 | web_fetch | - |

### 输出格式

```markdown
# 素材标题 - 日期（已验证）

## 新闻1

**时间**：X小时前（YYYY-MM-DD）
**来源**：URL
**核心内容**：摘要

## 新闻2
...

## 验证状态

✅ 搜索方式：Brave Search + freshness参数
✅ 时效性：已验证发布日期
✅ 来源：主流媒体/官方
```

---

## 验证清单

新闻类内容创作前必须确认：

- [ ] 已直接抓取新闻源（不依赖搜索引擎）
- [ ] 文章来自主流科技媒体
- [ ] 排除了过时信息（如2025年旧闻）
- [ ] 多源交叉验证（重要新闻）

主题类内容创作：

- [ ] 已使用Brave Search搜索
- [ ] 验证了内容来源可靠性
- [ ] 确认内容时效性

---

## 过时信息黑名单

**2026-04-07 更新：**

以下信息已过时：

- MiniMax M2 & Agent 开源（2025年事件）
- GPT-4o、o3系列（已有GPT-5、o4）
- Peter Steinberger加入OpenAI（2025旧闻）
- Claude 3.5（已有Mythos 5.0）

---

## 与创作Agent集成

```python
# 1. 调用资讯整合agent（直接抓取新闻源）
articles = scrape_36kr_news(count=10)

# 2. 输出素材文件
# reports/materials/36kr-latest.json

# 3. 创作agent读取素材
article_pipeline(
  source="reports/materials/36kr-latest.json"
)
```

## 可用脚本

- `scripts/scrape-aibase-v2.py` - 抓取AI Base最新文章（推荐）
- `scripts/scrape-36kr-fixed.py` - 抓取36氪最新文章
- `scripts/scrape-news-sources.py` - 抓取多个新闻源
- `scripts/verify-news-date.py` - 验证新闻发布日期

---

## 错误案例（2026-04-07）

### 案例1：Brave Search 时间过滤失效

**错误：** 设置 `date_after="2026-04-07"`，但返回2025年12月的内容

**原因：** Brave Search API 的 `date_after` 参数不生效

**验证结果：**
```python
web_search(
  query="AI news",
  date_after="2026-04-07"  # 设置了今天
)

# 返回：
# - "1 month ago" (2026年3月)
# - "January 12, 2026" (2026年1月)
# - "December 31, 2025" (2025年12月)
```

**修复：** 直接抓取新闻源，不依赖搜索引擎时间过滤

### 案例2：搜索结果把旧新闻当新新闻

**错误：** 把 "MiniMax M2开源"（2025年事件）当今天新闻

**原因：**
1. 搜索结果混杂旧新闻
2. 未验证新闻发布日期
3. 相对时间（如 "7 hours ago"）不可靠

**修复：**
1. 直接抓取新闻源（文章即最新）
2. 验证每条新闻发布日期
3. 创建过时信息黑名单

---

*创建时间：2026-04-07*
*版本：1.0*