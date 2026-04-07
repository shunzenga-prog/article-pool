# 同步维护方案

## 核心原理

**OpenClaw 默认从 `~/.openclaw/workspace/skills/` 加载 skills**

所以 article-pool 需要通过 `sync.sh` 同步到 workspace：

```
article-pool/skills/  →  ~/.openclaw/workspace/skills/
article-pool/scripts/ →  ~/.openclaw/workspace/scripts/
```

## 使用方式

### 初次安装后

```bash
cd article-pool
./sync.sh to
```

### 从 GitHub 拉取更新后

```bash
git pull
./sync.sh to
```

### 修改本地 Skills 后同步回项目

```bash
./sync.sh from
git add . && git commit -m "sync" && git push
```

## 自动同步（可选）

如果想自动同步，可以添加 cron 任务：

```bash
# 每小时自动同步一次
crontab -e

# 添加这一行
0 * * * * cd /home/zengshun/workspace/projects/article-pool && ./sync.sh to >> /tmp/article-pool-sync.log 2>&1
```

## 为什么不用修改 workspace 路径？

虽然可以修改 `openclaw.json` 中的 `agents.defaults.workspace`，但这会影响：

- MEMORY.md、MAINTENANCE.md 等文件的路径
- 其他 40+ 个现有 skills 不会被加载
- 项目兼容性问题

同步方案更安全、更兼容。

---

*同步后记得重启 Gateway：`openclaw gateway restart`*