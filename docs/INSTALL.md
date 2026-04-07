# 安装指南

## 前置要求

1. **OpenClaw** 已安装并运行
2. **Python 3.8+** 已安装
3. **Playwright** 已安装（用于新闻抓取）
4. **必要的 API Keys**

## 安装步骤

### 1. 克隆仓库

```bash
git clone https://github.com/xiaomi-ai/article-pool.git
cd article-pool
```

### 2. 安装依赖

```bash
# Python 依赖
pip install playwright pillow requests

# Playwright 浏览器
playwright install chromium

# 中文字体（可选，用于封面生成）
sudo apt install fonts-noto-cjk
```

### 3. 安装到 OpenClaw

```bash
# 自动安装脚本
./install.sh

# 或手动安装：
# 复制 skills 到 OpenClaw workspace
cp -r skills/* ~/.openclaw/workspace/skills/

# 复制 scripts 到 OpenClaw workspace
cp -r scripts/* ~/.openclaw/workspace/scripts/

# 复制 templates 到 OpenClaw workspace
cp -r templates/* ~/.openclaw/workspace/templates/
```

### 4. 配置 API Keys

```bash
# 复制配置模板
cp config/.env.example ~/.openclaw/workspace/scripts/.env

# 编辑配置文件
nano ~/.openclaw/workspace/scripts/.env
```

填入你的 API Keys：

```env
# Brave Search API
BRAVE_API_KEY=your_brave_api_key_here

# 微信公众号 API
WECHAT_APPID=your_wechat_appid_here
WECHAT_SECRET=your_wechat_secret_here
```

### 5. 验证安装

重启 OpenClaw Gateway：

```bash
openclaw gateway restart
```

测试创作功能：

```
创作一篇测试文章
```

## 安装脚本 (install.sh)

```bash
#!/bin/bash

# Article Pool 安装脚本

echo "🐱 开始安装 Article Pool..."

# 检查 OpenClaw 是否安装
if [ ! -d ~/.openclaw ]; then
    echo "❌ OpenClaw 未安装，请先安装 OpenClaw"
    exit 1
fi

# 创建必要的目录
mkdir -p ~/.openclaw/workspace/skills
mkdir -p ~/.openclaw/workspace/scripts
mkdir -p ~/.openclaw/workspace/templates
mkdir -p ~/.openclaw/workspace/reports/materials

# 复制 skills
echo "📦 安装 Skills..."
cp -r skills/* ~/.openclaw/workspace/skills/

# 复制 scripts
echo "📦 安装 Scripts..."
cp -r scripts/* ~/.openclaw/workspace/scripts/

# 复制 templates
echo "📦 安装 Templates..."
cp -r templates/* ~/.openclaw/workspace/templates/

# 复制配置模板
if [ ! -f ~/.openclaw/workspace/scripts/.env ]; then
    echo "📝 创建配置文件模板..."
    cp config/.env.example ~/.openclaw/workspace/scripts/.env
fi

# 赋予脚本执行权限
chmod +x ~/.openclaw/workspace/scripts/*.py

echo "✅ 安装完成！"
echo ""
echo "下一步："
echo "1. 编辑 ~/.openclaw/workspace/scripts/.env 填入 API Keys"
echo "2. 运行 openclaw gateway restart"
echo "3. 测试：发送 '创作一篇测试文章'"
```

## 常见问题

### Q: Brave Search API 如何获取？

访问 https://brave.com/search/api/，注册账户后获取 API Key。

### Q: 微信公众号 API 如何获取？

登录 https://mp.weixin.qq.com，在「设置与开发」→「基本配置」获取 AppID 和 AppSecret。

### Q: 封面生成失败？

确保已安装中文字体：

```bash
sudo apt install fonts-noto-cjk
```

### Q: 新闻抓取失败？

确保 Playwright 已安装浏览器：

```bash
playwright install chromium
```

---

*更多问题请查看 [docs/API-KEYS.md](API-KEYS.md)*