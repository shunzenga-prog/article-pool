#!/bin/bash

# 从 Article Pool 项目同步到 OpenClaw Workspace
# 用于将 GitHub 项目的更新应用到 workspace

echo "🔄 从 Article Pool 项目同步到 Workspace..."
echo ""

PROJECT_DIR="/home/zengshun/workspace/projects/article-pool"
WORKSPACE_DIR="$HOME/.openclaw/workspace"

# 创建必要的目录
mkdir -p "$WORKSPACE_DIR/skills"
mkdir -p "$WORKSPACE_DIR/scripts"
mkdir -p "$WORKSPACE_DIR/templates"

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
    if [ -d "$PROJECT_DIR/skills/$skill" ]; then
        # 删除旧版本，复制新版本
        rm -rf "$WORKSPACE_DIR/skills/$skill"
        cp -r "$PROJECT_DIR/skills/$skill" "$WORKSPACE_DIR/skills/"
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
    if [ -f "$PROJECT_DIR/scripts/$script" ]; then
        cp "$PROJECT_DIR/scripts/$script" "$WORKSPACE_DIR/scripts/"
        echo "   ✅ $script"
    fi
done

# 同步 templates
echo "📦 同步 Templates..."
if [ -d "$PROJECT_DIR/templates" ]; then
    cp -r "$PROJECT_DIR/templates/*" "$WORKSPACE_DIR/templates/" 2>/dev/null
    echo "   ✅ templates"
fi

# 赋予脚本执行权限
chmod +x "$WORKSPACE_DIR/scripts/*.py" 2>/dev/null

echo ""
echo "✅ 同步完成！"
echo ""
echo "下一步："
echo "openclaw gateway restart"
echo ""
echo "测试：发送「创作一篇测试文章」"