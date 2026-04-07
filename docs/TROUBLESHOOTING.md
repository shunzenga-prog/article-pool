# 常见问题与故障排除

## 安装问题

### Q: 同步后 Skills 没有被识别？

```bash
# 确认同步成功
ls ~/.openclaw/workspace/skills/article-pipeline/

# 重启 Gateway
openclaw gateway restart

# 检查 skills 列表
openclaw skills list | grep -E "wechat|article"
```

### Q: 脚本执行权限问题？

```bash
# 赋予执行权限
chmod +x sync.sh install.sh
chmod +x scripts/*.py
```

### Q: 目录不存在？

```bash
# 创建必要的目录
mkdir -p ~/.openclaw/workspace/reports/materials
mkdir -p ~/.openclaw/workspace/reports/images
mkdir -p ~/.openclaw/workspace/templates
```

---

## 依赖问题

### Q: Playwright 安装失败？

```bash
# 安装系统依赖
sudo apt install -y libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libgbm1

# 重新安装浏览器
playwright install chromium
```

### Q: 中文字体缺失？

```bash
# Ubuntu/Debian
sudo apt install fonts-noto-cjk

# 验证
fc-list :lang=zh | head -1
```

### Q: Python 依赖安装失败？

```bash
# 使用虚拟环境
python -m venv venv
source venv/bin/activate
pip install -r scripts/requirements.txt
```

---

## API 问题

### Q: Brave Search 报错？

**错误信息**：`API key required`

**解决方案**：
1. 确认已配置 `BRAVE_API_KEY`
2. 检查 API Key 是否有效
3. 检查是否超出配额（2000次/月）

### Q: 微信公众号发布失败？

**错误信息**：`40164: invalid ip`

**解决方案**：
1. 登录 mp.weixin.qq.com
2. 进入「设置与开发」→「基本配置」→「IP白名单」
3. 添加你的服务器 IP

**错误信息**：`48001: api unauthorized`

**解决方案**：
1. `freepublish/submit` 接口需要申请权限
2. 在公众号后台申请开通（1-3工作日）
3. 或手动发布草稿

### Q: 封面生成失败？

**可能原因**：
1. Pollinations API 暂时不可用
2. 网络问题

**解决方案**：
```bash
# 测试 Pollinations API
curl "https://image.pollinations.ai/prompt/test?width=100&height=100" -o test.png
```

---

## 使用问题

### Q: 创作链路不触发？

**检查步骤**：
1. 确认 skill 已同步
2. 重启 Gateway
3. 使用正确的触发词：`创作文章`、`写公众号`

### Q: 新闻抓取失败？

**错误信息**：`browser not found`

**解决方案**：
```bash
playwright install chromium
```

### Q: 输出路径错误？

**解决方案**：
```bash
# 设置环境变量
export OUTPUT_DIR=~/.openclaw/workspace/reports/materials

# 或在脚本中动态创建目录
mkdir -p ~/.openclaw/workspace/reports/materials
```

---

## 网络问题

### Q: 无法访问 GitHub？

**解决方案**：
1. 配置代理
2. 使用国内镜像

### Q: 无法访问 Pollinations？

**解决方案**：
1. Pollinations 是免费服务，可能有延迟
2. 多尝试几次
3. 使用代理

---

## 其他问题

### Q: 如何查看日志？

```bash
# OpenClaw 日志
tail -f /tmp/openclaw/openclaw-*.log

# 手动运行脚本查看输出
python scripts/scrape-36kr-fixed.py
```

### Q: 如何调试？

```bash
# 启用详细输出
python scripts/wechat_publish.py article.md --verbose

# 测试 API 连接
python -c "
import requests
resp = requests.get('https://api.weixin.qq.com')
print(resp.status_code)
"
```

### Q: 如何更新项目？

```bash
cd article-pool
git pull
./sync.sh to
openclaw gateway restart
```

---

## 获取帮助

1. 查看 [GitHub Issues](https://github.com/shunzenga-prog/article-pool/issues)
2. 查看 [OpenClaw 文档](https://docs.openclaw.ai)
3. 提交新的 Issue