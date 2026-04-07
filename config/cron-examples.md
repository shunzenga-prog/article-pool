# Article Pool 定时任务配置示例

## 添加到 crontab

```bash
crontab -e
```

## 推荐任务

```crontab
# AI 早报 - 每天 7:00 生成
0 7 * * * cd /home/yourname/projects/article-pool && python scripts/generate_ai_daily_news.py >> logs/daily-news.log 2>&1

# 热点追踪 - 每 2 小时
0 */2 * * * cd /home/yourname/projects/article-pool && python scripts/fetch-news.py >> logs/hotspot.log 2>&1

# 自动同步 - 每小时
0 * * * * cd /home/yourname/projects/article-pool && ./sync.sh to >> logs/sync.log 2>&1

# Git 自动提交 - 每天 23:00
0 23 * * * cd /home/yourname/projects/article-pool && git add . && git commit -m "auto sync: $(date +\%Y-\%m-\%d)" && git push >> logs/git.log 2>&1
```

## 日志目录

```bash
mkdir -p /home/yourname/projects/article-pool/logs
```

## 查看日志

```bash
tail -f /home/yourname/projects/article-pool/logs/daily-news.log
```