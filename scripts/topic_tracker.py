#!/usr/bin/env python3
"""
选题查重辅助工具 — 管理 reports/used_topics.json

创作完成后调用 add 记录选题关键词，自动剔除超过保护期的旧记录。
创作前调用 list 查看近期选题，辅助 Agent 做语义查重判断。

用法:
    python scripts/topic_tracker.py add "标题" "关键词1,关键词2,..." "早报"
    python scripts/topic_tracker.py list
    python scripts/topic_tracker.py list --json
    python scripts/topic_tracker.py list --days 14
    python scripts/topic_tracker.py clean
"""

import json
import sys
import os
from datetime import datetime, timedelta

from paths import USED_TOPICS_FILE as DATA_FILE

# ═══════════════════════════════════════════════
#  文章类型标准化
# ═══════════════════════════════════════════════

_STANDARD_TYPES = ["教程", "深度解析", "项目推荐", "早报", "晚报", "热点快评", "通用"]

_TYPE_NORMALIZE = {
    # 教程类
    "tutorial": "教程", "AI实战教程": "教程", "技术教程": "教程",
    "实战教程": "教程", "操作指南": "教程", "手把手": "教程",
    # 深度解析类
    "深度": "深度解析", "分析": "深度解析", "观点": "深度解析",
    "观点评论": "深度解析", "深度分析": "深度解析", "opinion": "深度解析",
    # 项目推荐类
    "项目": "项目推荐", "推荐": "项目推荐", "工具推荐": "项目推荐",
    "recommendation": "项目推荐",
    # 早报类
    "morning": "早报", "morning_news": "早报", "日报": "早报",
    "新闻简报": "早报", "资讯": "早报",
    # 晚报类
    "evening": "晚报", "evening_news": "晚报",
    # 热点快评类
    "hotspot": "热点快评", "热点": "热点快评",
    # 通用类
    "general": "通用", "news": "通用", "其他": "通用",
}


def _normalize_type(raw_type: str) -> str:
    """将任意类型字符串标准化为 7 种标准类型之一"""
    t = raw_type.strip()
    if t in _STANDARD_TYPES:
        return t
    return _TYPE_NORMALIZE.get(t, "通用")


def _normalize_entries(data: dict) -> int:
    """原地标准化所有条目的类型字段，返回被修正的条目数"""
    changed = 0
    for e in data.get("entries", []):
        old = e.get("type", "通用")
        new = _normalize_type(old)
        if old != new:
            e["type"] = new
            changed += 1
    return changed


def load() -> dict:
    """加载 used_topics.json，不存在时自动创建"""
    if not DATA_FILE.exists():
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        default_data = {"protection_days": 7, "entries": []}
        save(default_data)
        return default_data
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save(data: dict):
    """保存到 used_topics.json"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_cutoff(protection_days: int) -> str:
    """计算保护期截止日期"""
    return (datetime.now() - timedelta(days=protection_days)).strftime("%Y-%m-%d")


def clean_expired(data: dict) -> dict:
    """剔除超过保护期的条目，原地修改并返回"""
    days = data.get("protection_days", 7)
    cutoff = get_cutoff(days)
    data["entries"] = [e for e in data["entries"] if e["date"] >= cutoff]
    return data


def _dedup_entries(data: dict) -> int:
    """清除完全重复的条目（同 date + 同 title），返回移除数"""
    seen = set()
    unique = []
    removed = 0
    for e in data.get("entries", []):
        key = (e.get("date", ""), e.get("title", ""))
        if key in seen:
            removed += 1
        else:
            seen.add(key)
            unique.append(e)
    data["entries"] = unique
    return removed


def cmd_add(title: str, keywords_str: str, entry_type: str):
    """添加一条新选题记录，写入前自动清理过期条目 + 去重 + 类型标准化"""
    normalized_type = _normalize_type(entry_type)

    data = load()
    data = clean_expired(data)
    _normalize_entries(data)  # 标准化已有条目
    removed = _dedup_entries(data)
    if removed:
        print(f"🧹 自动清除 {removed} 条重复记录")

    keywords = [k.strip() for k in keywords_str.split(",") if k.strip()]
    if not keywords:
        print("❌ 关键词不能为空", file=sys.stderr)
        sys.exit(1)

    today = datetime.now().strftime("%Y-%m-%d")

    # 检查同天同标题是否已存在
    for e in data.get("entries", []):
        if e.get("date") == today and e.get("title") == title:
            print(f"⚠️  今天已存在同名选题，跳过重复添加: {title}")
            return

    entry = {
        "date": today,
        "keywords": keywords,
        "title": title,
        "type": normalized_type,
    }
    data["entries"].append(entry)
    save(data)

    days = data.get("protection_days", 7)
    print(f"✅ 已添加: {title}")
    print(f"   日期: {entry['date']}  类型: {normalized_type}")
    print(f"   关键词: {', '.join(keywords)}")
    print(f"   保护期内共 {len(data['entries'])} 条记录 ({days}天)")


def cmd_list(as_json: bool = False, override_days: int = None):
    """列出保护期内的所有选题记录（只读，不修改文件）"""
    data = load()
    data = clean_expired(data)
    _normalize_entries(data)  # 标准化类型（仅内存）
    _dedup_entries(data)  # 清理重复记录（仅内存）
    # 注意：list 是只读操作，不 save()。实际清理在 cmd_add/cmd_clean 时写入。

    days = override_days if override_days else data.get("protection_days", 7)
    cutoff = get_cutoff(days)

    # 如果有 days 覆盖，按覆盖值再过滤
    entries = [e for e in data["entries"] if e["date"] >= cutoff]

    if as_json:
        print(json.dumps(entries, ensure_ascii=False, indent=2))
        return

    if not entries:
        print(f"📭 最近 {days} 天内无选题记录，可自由创作。")
        return

    print(f"📋 最近 {days} 天内选题 ({len(entries)} 条)：")
    print("─" * 65)
    for e in sorted(entries, key=lambda x: x["date"], reverse=True):
        kw = ", ".join(e["keywords"])
        print(f"  [{e['date']}] {e['title']}")
        print(f"          {kw}  |  {e['type']}")


def cmd_clean():
    """手动清理过期记录 + 去重 + 类型标准化"""
    data = load()
    before = len(data["entries"])
    data = clean_expired(data)
    _normalize_entries(data)
    _dedup_entries(data)
    after = len(data["entries"])
    save(data)
    print(f"🧹 清理: 移除 {before - after} 条过期/重复，剩 {after} 条（含类型标准化）")


def main():
    args = sys.argv[1:]

    if not args:
        print(__doc__)
        sys.exit(0)

    cmd = args[0]

    if cmd == "add":
        if len(args) < 4:
            print("用法: python topic_tracker.py add <标题> <关键词,以逗号分隔> <类型>")
            print("示例: python topic_tracker.py add 'GPT-5发布' 'OpenAI,GPT-5,大模型' '早报'")
            sys.exit(1)
        cmd_add(args[1], args[2], args[3])

    elif cmd == "list":
        as_json = "--json" in args
        override_days = None
        for i, a in enumerate(args):
            if a == "--days" and i + 1 < len(args):
                try:
                    override_days = int(args[i + 1])
                except ValueError:
                    print("❌ --days 需要整数参数", file=sys.stderr)
                    sys.exit(1)
        cmd_list(as_json=as_json, override_days=override_days)

    elif cmd == "clean":
        cmd_clean()

    else:
        print(f"❌ 未知命令: {cmd}")
        print("可用命令: add | list | clean")
        sys.exit(1)


if __name__ == "__main__":
    main()
