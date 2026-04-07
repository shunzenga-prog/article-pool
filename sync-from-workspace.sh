#!/bin/bash

# 从 OpenClaw Workspace 同步到 Article Pool 项目
# 用于将 workspace 中的修改同步回 GitHub 项目

echo "🔄 从 Workspace 同步到 Article Pool 项目..."
echo ""

PROJECT_DIR="/home/zengshun/workspace/projects/article-pool"
WORKSPACE_DIR="$HOME/.openclaw/workspace"

# 同步 skills
echo "📦 同步 Skills..."
skills=(
    "article-pipeline"
    "wechat-writer"
    "xiaohongshu-writer"
    "ai-daily-news-get"
    "hotspot-tracker"
    "news-aggregator"
    "research-lobster"
)

for skill in "${skills[@]}"; do
    if [ -d "$WORKSPACE_DIR/skills/$skill" ]; then
        # 删除旧版本，复制新版本
        rm -rf "$PROJECT_DIR/skills/$skill"
        cp -r "$WORKSPACE_DIR/skills/$skill" "$PROJECT_DIR/skills/"
        echo "   ✅ $skill"
    fi
done

# 同步 scripts
echo "📦 同步 Scripts..."
scripts=(
    "wechat_publish.py"
    "wechat-upload-image.py"
    "generate-cover.py"
    "add-cover-text.py"
    "ai-image-gen.py"
    "fetch-news.py"
    "scrape-36kr-fixed.py"
    "scrape-aibase-v2.py"
    "scrape-news-sources.py"
)

for script in "${scripts[@]}"; do
    if [ -f "$WORKSPACE_DIR/scripts/$script" ]; then
        cp "$WORKSPACE_DIR/scripts/$script" "$PROJECT_DIR/scripts/"
        echo "   ✅ $script"
    fi
done

# 同步 templates
echo "📦 同步 Templates..."
if [ -d "$WORKSPACE_DIR/templates" ]; then
    cp -r "$WORKSPACE_DIR/templates/*" "$PROJECT_DIR/templates/" 2>/dev/null
    echo "   ✅ templates"
fi

echo ""
echo "✅ 同步完成！"
echo ""
echo "下一步："
echo "cd $PROJECT_DIR"
echo "git add ."
echo "git commit -m 'sync from workspace'"
echo "git push"