# 同步维护方案

Article Pool 支持与 OpenClaw workspace 双向同步，方便维护更新。

## 同步架构

```
GitHub Repository (article-pool)
        ↕️ 双向同步
OpenClaw Workspace (~/.openclaw/workspace)
```

## 从 Workspace 同步到项目

当你修改了 workspace 中的 skills/scripts，需要同步到 GitHub 项目：

```bash
#!/bin/bash
# sync-from-workspace.sh

echo "🔄 从 Workspace 同步到 Article Pool 项目..."

# 同步 skills
cp -r ~/.openclaw/workspace/skills/article-pool skills/
cp -r ~/.openclaw/workspace/skills/wechat-writer skills/
cp -r ~/.openclaw/workspace/skills/xiaohongshu-writer skills/
cp -r ~/.openclaw/workspace/skills/ai-daily-news-get skills/
cp -r ~/.openclaw/workspace/skills/hotspot-tracker skills/
cp -r ~/.openclaw/workspace/skills/news-aggregator skills/
cp -r ~/.openclaw/workspace/skills/research-lobster skills/

# 同步 scripts
cp ~/.openclaw/workspace/scripts/wechat_publish.py scripts/
cp ~/.openclaw/workspace/scripts/wechat-upload-image.py scripts/
cp ~/.openclaw/workspace/scripts/generate-cover.py scripts/
cp ~/.openclaw/workspace/scripts/add-cover-text.py scripts/
cp ~/.openclaw/workspace/scripts/ai-image-gen.py scripts/
cp ~/.openclaw/workspace/scripts/fetch-news.py scripts/
cp ~/.openclaw/workspace/scripts/scrape-36kr-fixed.py scripts/
cp ~/.openclaw/workspace/scripts/scrape-aibase-v2.py scripts/
cp ~/.openclaw/workspace/scripts/scrape-news-sources.py scripts/

# 同步 templates
cp -r ~/.openclaw/workspace/templates/* templates/

echo "✅ 同步完成！"
echo ""
echo "下一步：git add . && git commit -m 'sync from workspace' && git push"
```

## 从项目同步到 Workspace

当你从 GitHub 拉取了新版本，需要同步到 workspace：

```bash
#!/bin/bash
# sync-to-workspace.sh

echo "🔄 从 Article Pool 项目同步到 Workspace..."

# 同步 skills
cp -r skills/article-pipeline ~/.openclaw/workspace/skills/
cp -r skills/wechat-writer ~/.openclaw/workspace/skills/
cp -r skills/xiaohongshu-writer ~/.openclaw/workspace/skills/
cp -r skills/ai-daily-news-get ~/.openclaw/workspace/skills/
cp -r skills/hotspot-tracker ~/.openclaw/workspace/skills/
cp -r skills/news-aggregator ~/.openclaw/workspace/skills/
cp -r skills/research-lobster ~/.openclaw/workspace/skills/

# 同步 scripts
cp scripts/wechat_publish.py ~/.openclaw/workspace/scripts/
cp scripts/wechat-upload-image.py ~/.openclaw/workspace/scripts/
cp scripts/generate-cover.py ~/.openclaw/workspace/scripts/
cp scripts/add-cover-text.py ~/.openclaw/workspace/scripts/
cp scripts/ai-image-gen.py ~/.openclaw/workspace/scripts/
cp scripts/fetch-news.py ~/.openclaw/workspace/scripts/
cp scripts/scrape-36kr-fixed.py ~/.openclaw/workspace/scripts/
cp scripts/scrape-aibase-v2.py ~/.openclaw/workspace/scripts/
cp scripts/scrape-news-sources.py ~/.openclaw/workspace/scripts/

# 同步 templates
cp -r templates/* ~/.openclaw/workspace/templates/

echo "✅ 同步完成！"
echo ""
echo "下一步：openclaw gateway restart"
```

## 自动同步脚本

创建一个定期同步的 cron 任务：

```bash
# 每天凌晨 2 点从 workspace 同步到项目
0 2 * * * cd /home/zengshun/workspace/projects/article-pool && ./sync-from-workspace.sh && git add . && git commit -m "daily sync" && git push
```

## Git Remote 配置

项目需要配置两个 remote：

```bash
# 主 remote（GitHub）
git remote add origin https://github.com/xiaomi-ai/article-pool.git

# 可选：配置 SSH remote
git remote set-url origin git@github.com:xiaomi-ai/article-pool.git
```

## 版本管理策略

### 主分支 (main)

- 稳定版本
- 经过测试的功能

### 开发分支 (develop)

- 最新功能
- 实验性修改

### 发布流程

```
develop → 测试 → main → 发布
```

## 维护建议

1. **定期同步**：每周至少一次从 workspace 同步更新
2. **版本号管理**：每次更新更新 VERSION 文件
3. **测试验证**：同步后运行测试脚本
4. **文档更新**：同步时更新 CHANGELOG.md

---

*建议使用 Git hooks 自动化同步流程*