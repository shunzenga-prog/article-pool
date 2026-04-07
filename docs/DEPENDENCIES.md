# 依赖说明

## Python 依赖

```txt
requests>=2.28.0      # HTTP 请求
Pillow>=9.0.0         # 图片处理（封面生成）
playwright>=1.40.0    # 浏览器自动化（新闻抓取）
```

安装：
```bash
pip install -r scripts/requirements.txt
playwright install chromium
```

---

## MCP 服务（可选）

### 小红书 MCP（可选）

如果需要自动发布到小红书，需要配置小红书 MCP 服务。

**配置方式：**

在 `~/.openclaw/openclaw.json` 中添加：

```json
{
  "mcp": {
    "servers": {
      "xiaohongshu": {
        "url": "http://localhost:18060/mcp"
      }
    }
  }
}
```

**注意：** 小红书 MCP 需要单独部署，详见相关文档。

**当前项目状态：**
- ✅ 小红书内容创作：不需要 MCP，直接使用 `xiaohongshu-writer` skill
- ⚠️ 小红书自动发布：需要 MCP 服务

---

## SDK 说明

### OpenAI Agents SDK 模式

`article-pipeline` skill 基于 OpenAI Agents SDK 的设计模式，实现多 Agent 协作。

**核心概念：**

| 概念 | 说明 | 在项目中的应用 |
|------|------|----------------|
| Agent | 独立的执行单元 | 分流官、创作官、审阅官等 |
| Handoff | Agent 间切换 | 创作官 → 审阅官 → 润色官 |
| Context Variables | 上下文传递 | platform、topic、score 等 |
| Guardrails | 输入输出验证 | 时效验证、真实性检查 |

**注意：** 这是设计模式参考，不需要安装 OpenAI SDK。OpenClaw 内置了 Agent 机制。

---

## 系统依赖

### 中文字体（封面生成）

```bash
# Ubuntu/Debian
sudo apt install fonts-noto-cjk

# macOS
# 系统自带中文字体，无需安装

# Windows
# 系统自带中文字体，无需安装
```

### Playwright 浏览器（新闻抓取）

```bash
playwright install chromium
```

---

## 完整依赖清单

| 依赖 | 用途 | 必需 | 安装方式 |
|------|------|------|----------|
| Python 3.8+ | 运行脚本 | ✅ | 系统安装 |
| requests | HTTP 请求 | ✅ | pip install |
| Pillow | 图片处理 | ✅ | pip install |
| playwright | 浏览器自动化 | ✅ | pip install + playwright install |
| 中文字体 | 封面生成 | ✅ | apt install |
| 小红书 MCP | 小红书发布 | ❌ | 可选配置 |

---

## 验证安装

```bash
# 检查 Python 依赖
python -c "import requests; import PIL; import playwright; print('✅ 依赖完整')"

# 检查字体
fc-list :lang=zh | head -1

# 检查 Playwright
playwright --version
```