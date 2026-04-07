---
name: AI Daily News
description: 每日AI早报 - 简洁风格，自动生成封面图并上传公众号。使用场景：(1) 生成AI早报 (2) 查看今日AI新闻 (3) 定时任务触发
---

# AI Daily News - 每日AI早报

参考36氪快讯风格，输出HTML格式，自动配图并上传公众号。

## ⚠️ 核心原则

**禁止出现内部术语** - 不要写"开头钩子"、"SCQA结构"、"爆款公式"等

**输出HTML格式** - 使用公众号排版规范的HTML模板

**时效性验证（必查！）**
- 每条新闻必须确认发布时间
- 只使用过去48小时内的信息
- 标注新闻来源日期

**过时信息黑名单（2026-04-07）：**
- GPT-4o、o3系列（已有GPT-5、o4）
- Peter Steinberger加入OpenAI（2025旧闻）
- Claude 3.5（已有Mythos 5.0）

## 输出模板（HTML格式）

```html
<h1 style="font-size:22px;font-weight:bold;color:#1A1A1A;text-align:center;margin:20px 0;">AI早报 | YYYY年M月D日</h1>

<p style="font-size:14px;color:#999;text-align:center;margin-bottom:30px;">每天5分钟，看懂AI世界</p>

<hr style="border:none;border-top:1px solid #E0E0E0;margin:30px 0;">

<h2 style="font-size:18px;font-weight:bold;color:#1A1A1A;border-left:4px solid #1E88E5;padding-left:12px;margin:35px 0 15px 0;">头条</h2>

<p style="font-size:15px;line-height:1.8;color:#1A1A1A;margin:15px 0;"><strong>[标题]</strong></p>

<p style="font-size:15px;line-height:1.8;color:#333;margin:15px 0;">[80-100字：发生了什么+关键细节+为什么重要]</p>

<hr style="border:none;border-top:1px solid #E0E0E0;margin:30px 0;">

<h2 style="font-size:18px;font-weight:bold;color:#1A1A1A;border-left:4px solid #1E88E5;padding-left:12px;margin:35px 0 15px 0;">要闻</h2>

<p style="font-size:15px;line-height:1.8;color:#1A1A1A;margin:15px 0;"><strong>1. [标题]</strong></p>
<p style="font-size:15px;line-height:1.8;color:#333;margin:15px 0;">[50-60字：核心事实+关键数据]</p>

<!-- 重复2-5条 -->

<hr style="border:none;border-top:1px solid #E0E0E0;margin:30px 0;">

<h2 style="font-size:18px;font-weight:bold;color:#1A1A1A;border-left:4px solid #1E88E5;padding-left:12px;margin:35px 0 15px 0;">简讯</h2>

<p style="font-size:15px;line-height:1.8;color:#333;margin:10px 0;">• [新闻]：[一句话30字]</p>

<!-- 重复4条 -->

<hr style="border:none;border-top:1px solid #E0E0E0;margin:30px 0;">

<h2 style="font-size:18px;font-weight:bold;color:#1A1A1A;border-left:4px solid #1E88E5;padding-left:12px;margin:35px 0 15px 0;">小咪观察</h2>

<p style="font-size:15px;line-height:1.8;color:#333;margin:15px 0;">[3-5句话口语化总结]</p>

<hr style="border:none;border-top:1px solid #E0E0E0;margin:40px 0;">

<p style="font-size:14px;color:#999;text-align:center;">🐱 小咪早报 | 每天早7点，陪你一起看懂AI</p>
```

## 工作流程

### 1. 搜索新闻
```
web_search(query="AI news latest", freshness="day", count=10)
web_search(query="AI 新闻 最新", freshness="day", count=10)
```

### 2. 筛选排序
- 头条：1条（最重要）
- 要闻：5条
- 简讯：4条

### 3. 写作要求
- 头条：发生了什么 + 为什么重要 + 有什么影响
- 要闻：核心事实 + 关键数据
- 简讯：新闻名 + 一句话
- 小咪观察：口语化总结

### 4. 生成封面图
```bash
curl -s -o reports/images/ai-daily-news-cover-YYYY-MM-DD.png \
  "https://image.pollinations.ai/prompt/Minimalist%20tech%20news%20header,%20AI%20theme,%20blue%20gradient?width=1200&height=675&nologo=true"
```

### 5. 上传图片
```
python scripts/wechat-upload-image.py reports/images/ai-daily-news-cover-YYYY-MM-DD.png
```

### 6. 发布文章
使用 wechat-article-publisher skill 上传HTML文章

### 7. 保存文件
输出到：`reports/ai-daily-news-YYYY-MM-DD.html`（HTML格式）

## 字数控制

- 总字数：800-1000字
- 头条：80-100字
- 要闻：每条50-60字
- 简讯：每条30字
- 小咪观察：100-150字