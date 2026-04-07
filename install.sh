#!/bin/bash

# Article Pool 安装脚本
# 用于将项目安装到 OpenClaw workspace

echo "🐱 开始安装 Article Pool..."
echo ""

# 检查 OpenClaw 是否安装
if [ ! -d ~/.openclaw ]; then
    echo "❌ OpenClaw 未安装，请先安装 OpenClaw"
    echo "   安装指南：https://docs.openclaw.ai"
    exit 1
fi

echo "✅ OpenClaw 已安装"

# 创建必要的目录
echo "📁 创建目录..."
mkdir -p ~/.openclaw/workspace/skills
mkdir -p ~/.openclaw/workspace/scripts
mkdir -p ~/.openclaw/workspace/templates
mkdir -p ~/.openclaw/workspace/reports/materials
mkdir -p ~/.openclaw/workspace/reports/images

# 复制 skills
echo "📦 安装 Skills..."
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
    if [ -d "skills/$skill" ]; then
        cp -r "skills/$skill" ~/.openclaw/workspace/skills/
        echo "   ✅ $skill"
    fi
done

# 复制 scripts
echo "📦 安装 Scripts..."
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
    if [ -f "scripts/$script" ]; then
        cp "scripts/$script" ~/.openclaw/workspace/scripts/
        echo "   ✅ $script"
    fi
done

# 复制 templates
echo "📦 安装 Templates..."
if [ -d "templates" ]; then
    cp -r templates/* ~/.openclaw/workspace/templates/
    echo "   ✅ templates"
fi

# 复制配置模板
if [ ! -f ~/.openclaw/workspace/scripts/.env ]; then
    echo "📝 创建配置文件模板..."
    cp config/.env.example ~/.openclaw/workspace/scripts/.env
    echo "   ✅ .env 模板已创建"
fi

# 赋予脚本执行权限
echo "🔧 设置执行权限..."
chmod +x ~/.openclaw/workspace/scripts/*.py 2>/dev/null

echo ""
echo "✅ 安装完成！"
echo ""
echo "======================================"
echo "下一步："
echo ""
echo "1. 编辑配置文件："
echo "   nano ~/.openclaw/workspace/scripts/.env"
echo "   填入你的 API Keys（Brave Search、微信公众号等）"
echo ""
echo "2. 重启 OpenClaw Gateway："
echo "   openclaw gateway restart"
echo ""
echo "3. 测试创作功能："
echo "   发送「创作一篇测试文章」"
echo ""
echo "======================================"
echo ""
echo "🐱 小咪祝你创作愉快！"