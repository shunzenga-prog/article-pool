# GitHub 发布指南

## 步骤 1：创建 GitHub 仓库

1. 登录 https://github.com
2. 点击右上角 "+" → "New repository"
3. 填写仓库信息：
   - Repository name: `article-pool`
   - Description: `AI 内容创作生产线 - OpenClaw 一键安装`
   - Public/Private: 选择 **Public**（开源项目）
   - ❌ 不要勾选 "Add a README file"（我们已经有了）
   - ❌ 不要勾选 "Add .gitignore"（我们已经有了）
   - License: MIT（我们已经有了）

4. 点击 "Create repository"

## 步骤 2：添加 Remote 并推送

创建仓库后，GitHub 会显示一个页面，复制你的仓库地址。

例如：`https://github.com/YOUR_USERNAME/article-pool.git`

然后执行：

```bash
cd /home/zengshun/workspace/projects/article-pool

# 添加 remote
git remote add origin https://github.com/YOUR_USERNAME/article-pool.git

# 推送到 GitHub
git push -u origin main
```

## 步骤 3：验证发布

访问你的仓库页面：

```
https://github.com/YOUR_USERNAME/article-pool
```

确认所有文件都已上传。

## 步骤 4：设置同步维护

在 workspace 中创建一个快捷脚本，方便后续同步：

```bash
# ~/.openclaw/workspace/sync-article-pool.sh
#!/bin/bash
cd /home/zengshun/workspace/projects/article-pool
./sync-from-workspace.sh
git add .
git commit -m "sync from workspace: $(date +%Y-%m-%d)"
git push
```

## 可选：配置 SSH 推送

如果你配置了 SSH key，可以切换到 SSH 地址：

```bash
git remote set-url origin git@github.com:YOUR_USERNAME/article-pool.git
```

---

*完成后，其他用户可以通过以下方式安装：*

```bash
git clone https://github.com/YOUR_USERNAME/article-pool.git
cd article-pool
./install.sh
```