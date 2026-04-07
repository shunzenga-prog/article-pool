# 新闻搜索策略规范

## ⚠️ 核心原则

**必须先搜索，再创作** - 不能依赖旧知识或未验证的信息

**验证时效性** - 每条新闻必须确认发布日期

**来源可靠** - 优先使用 Brave Search，避免不可靠来源

---

## 搜索时间范围（按场景）

| 场景 | 时间范围 | Brave Search 参数 | 说明 |
|------|----------|-------------------|------|
| **早报** | 前一天 | `freshness="day"` + `date_after=昨天` | 智能获取昨日新闻 |
| **晚报** | 当天 | `freshness="day"` | 智能获取今日新闻 |
| **周报** | 过去7天 | `freshness="week"` | 智能获取一周新闻 |
| **月报** | 过去30天 | `freshness="month"` | 智能获取一月新闻 |
| **指定主题创作** | 不限制 | 无时间参数 | 搜索相关内容即可 |
| **知识/技术/工具分享** | 不限制 | 无时间参数 | 搜索最新资料 |

---

## Brave Search 参数

### 时间过滤

```python
web_search(
  query="AI news",
  freshness="day",  # day/week/month
  date_after="2026-04-06",  # ISO 格式
  date_before="2026-04-07",
  count=10
)
```

### 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `freshness` | 时间范围 | "day" / "week" / "month" |
| `date_after` | 开始日期 | "2026-04-06" |
| `date_before` | 结束日期 | "2026-04-07" |
| `country` | 地区 | "US" / "CN" / "ALL" |
| `count` | 结果数量 | 10 |

---

## 搜索流程（强制）

### 1. 新闻类内容（早报/晚报/周报/月报）

```
1. 确定时间范围（如：早报 = 昨天）
2. 使用 Brave Search 搜索
3. 验证每条新闻的发布时间
4. 排除过时信息
5. 按重要性排序
6. 创作
```

### 2. 指定主题创作

```
1. 使用 Brave Search 搜索主题
2. 收集多方来源
3. 验证信息真实性
4. 结合自身知识库
5. 创作（标注来源）
```

### 3. 知识/技术/工具分享

```
1. 使用 Brave Search 搜索最新资料
2. 对比多个来源
3. 验证技术准确性
4. 结合实践经验
5. 创作
```

---

## 验证清单

创作前必须确认：

- [ ] 已使用 Brave Search 搜索
- [ ] 验证了新闻发布时间
- [ ] 新闻来源可靠（主流媒体/官方公告）
- [ ] 排除了过时信息（如：去年的旧闻）
- [ ] 多方交叉验证（重要新闻）

---

## 日期计算示例

### 早报（获取昨天新闻）

```python
from datetime import datetime, timedelta

today = datetime.now()
yesterday = today - timedelta(days=1)

web_search(
  query="AI 新闻",
  freshness="day",
  date_after=yesterday.strftime("%Y-%m-%d"),
  count=10
)
```

### 晚报（获取今天新闻）

```python
web_search(
  query="AI 新闻",
  freshness="day",
  count=10
)
```

### 周报（获取过去7天）

```python
web_search(
  query="AI 新闻",
  freshness="week",
  count=15
)
```

---

## 过时信息黑名单（示例）

**2026-04-07 更新：**

以下信息已过时，不能作为"最新新闻"：

- MiniMax M2 & Agent 开源（2025年事件，非2026年）
- GPT-4o、o3 系列（已有 GPT-5、o4）
- Peter Steinberger 加入 OpenAI（2025旧闻）
- Claude 3.5（已有 Mythos 5.0）

**验证方法：** 每次创作前必须搜索，确认新闻发布日期！

---

## 来源可靠性优先级

| 优先级 | 来源类型 | 示例 |
|--------|----------|------|
| ⭐⭐⭐⭐⭐ | 官方公告 | OpenAI Blog、Anthropic Blog |
| ⭐⭐⭐⭐ | 主流科技媒体 | 36氪、TechCrunch、The Verge |
| ⭐⭐⭐ | 传统媒体 | 纽约时报、华尔街日报 |
| ⭐⭐ | 行业媒体 | 量子位、机器之心 |
| ⭐ | 社交媒体 | Twitter/X、Reddit（需验证） |

---

## 错误案例（2026-04-07）

**错误：** 研究龙虾追踪到"MiniMax M2 & Agent 正式开源"，标注为7小时前

**原因：**
1. 没有验证新闻发布日期
2. 搜索结果混杂了旧新闻
3. 未使用 `freshness` 参数过滤

**修复：**
1. 新闻类内容必须使用 `freshness` 参数
2. 验证每条新闻的发布日期
3. 多方交叉验证

---

*创建时间：2026-04-07*  
*更新时间：2026-04-07*