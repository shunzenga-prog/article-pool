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


def load() -> dict:
    """加载 used_topics.json"""
    if not DATA_FILE.exists():
        print(f"❌ {DATA_FILE} 不存在，请先创建。", file=sys.stderr)
        sys.exit(1)
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


def cmd_add(title: str, keywords_str: str, entry_type: str):
    """添加一条新选题记录，写入前自动清理过期条目"""
    data = load()
    data = clean_expired(data)

    keywords = [k.strip() for k in keywords_str.split(",") if k.strip()]
    if not keywords:
        print("❌ 关键词不能为空", file=sys.stderr)
        sys.exit(1)

    entry = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "keywords": keywords,
        "title": title,
        "type": entry_type,
    }
    data["entries"].append(entry)
    save(data)

    days = data.get("protection_days", 7)
    print(f"✅ 已添加: {title}")
    print(f"   日期: {entry['date']}  类型: {entry_type}")
    print(f"   关键词: {', '.join(keywords)}")
    print(f"   保护期内共 {len(data['entries'])} 条记录 ({days}天)")


def cmd_list(as_json: bool = False, override_days: int = None):
    """列出保护期内的所有选题记录"""
    data = load()
    data = clean_expired(data)
    save(data)  # 顺便清理过期数据

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
    """手动清理过期记录"""
    data = load()
    before = len(data["entries"])
    data = clean_expired(data)
    after = len(data["entries"])
    save(data)
    print(f"🧹 清理: 移除 {before - after} 条过期，剩 {after} 条")


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
