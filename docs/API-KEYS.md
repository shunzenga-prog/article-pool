# API Keys 配置说明

## Brave Search API

### 获取步骤

1. 访问 https://brave.com/search/api/
2. 注册账户（可用 Google/GitHub/Microsoft 账号登录）
3. 在 Dashboard 创建 API Key
4. 复制 API Key 到配置文件

### 配置方式

```env
BRAVE_API_KEY=BSA********************
```

### 使用限制

- **免费额度**：2000 次/月
- **付费计划**：$5/月（5000 次）或 $100/月（无限次）

### OpenClaw 配置

在 `~/.openclaw/config.json` 中配置：

```json
{
  "plugins": {
    "entries": {
      "brave": {
        "config": {
          "apiKey": "${BRAVE_API_KEY}"
        }
      }
    }
  }
}
```

---

## 微信公众号 API

### 获取步骤

1. 登录 https://mp.weixin.qq.com
2. 进入「设置与开发」→「基本配置」
3. 复制 AppID 和 AppSecret
4. 配置 IP 白名单（添加你的服务器 IP）

### 配置方式

```env
WECHAT_APPID=wx****************
WECHAT_SECRET=****************
```

### IP 白名单配置

在「设置与开发」→「基本配置」→「IP白名单」中添加：

```
# 本地开发
127.0.0.1

# 你的服务器 IP
xxx.xxx.xxx.xxx
```

### API 权限

| 接口 | 权限 | 说明 |
|------|------|------|
| /cgi-bin/token | ✅ | 获取 access_token |
| /cgi-bin/draft/add | ✅ | 创建草稿 |
| /cgi-bin/material/add_material | ✅ | 上传图片 |
| /cgi-bin/freepublish/submit | ⚠️ | 需申请开通 |

**注意**：`freepublish/submit` 接口需要单独申请权限（1-3 工作日审核）

---

## Pollinations AI（封面生成）

### 说明

Pollinations.ai 是免费的 AI 图片生成服务，无需 API Key。

### 使用方式

```python
# 直接调用 API
url = f"https://image.pollinations.ai/prompt/{prompt}?width=1200&height=675&nologo=true"
```

### 参数说明

- `prompt`：图片描述（英文）
- `width`：宽度（公众号封面推荐 1200）
- `height`：高度（公众号封面推荐 675）
- `nologo`：去除水印（true）

---

## 其他可选 API

### OpenAI/Anthropic API

如果使用 GPT/Claude 模型：

```env
OPENAI_API_KEY=sk-********************
ANTHROPIC_API_KEY=sk-ant-********************
```

### 阿里云百炼 API

如果使用国产模型（Qwen/GLM）：

```env
DASHSCOPE_API_KEY=sk-********************
```

---

## 配置文件位置

```
~/.openclaw/workspace/scripts/.env
```

## 安全提醒

1. **不要提交 .env 到 Git**
2. **不要在公开场合分享 API Key**
3. **定期更换 API Key**
4. **使用 IP 白名单限制访问**