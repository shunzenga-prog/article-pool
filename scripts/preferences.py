"""
用户偏好加载器 - 从项目根目录 user_preferences.json 读取配置
与 DEFAULTS 深度合并，缺失文件时静默返回默认值，保证向后兼容。
"""

import json
import os
from copy import deepcopy
from pathlib import Path


DEFAULTS = {
    "author": {
        "name": "小智",
        "signature_emoji": "🐱",
    },
    "cover": {
        "default_mode": "auto",
        "preferred_theme": None,
        "title_font_size": 68,
        "subtitle_font_size": 20,
        "source_order": ["og", "pexels", "ai-gen", "unsplash", "brave"],
    },
    "article": {
        "max_daily_drafts": 3,
        "min_length": 300,
        "max_length": 5000,
        "auto_publish": False,
        "default_style": "专业流畅",
        "topic_protection_days": 7,
    },
    "writing": {
        "title_length": [20, 30],
        "font_size_px": 15,
        "line_height": 1.9,
        "max_tables": 2,
        "max_paragraph_lines": 5,
        "end_emoji": "🐱",
    },
    "colors": {
        "body_text": "#1A1A1A",
        "heading_link": "#1E88E5",
        "emphasis": "#E74C3C",
        "success": "#27AE60",
        "max_colors": 4,
    },
    "footers": {
        "morning-briefing": "扫码关注，每天早晨 8:00 准时推送",
        "evening-briefing": "每晚 21:30 与你一起回顾这一天",
        "daily-report": "关注公众号，每天获取实用编程技巧",
        "weekly-report": "每周日晚 20:00 准时更新，不见不散",
        "tech-tutorial": "每周更新实用编程教程，扫码关注不迷路",
        "news-digest": "第一时间获取重大科技事件解读",
        "monthly-summary": "每月最后一天推送月度复盘",
        "yearly-summary": "每年最后一天推送年度回顾",
    },
}


def _deep_merge(base, override):
    """递归合并 override 到 base，返回新字典。"""
    result = deepcopy(base)
    for key, val in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = _deep_merge(result[key], val)
        else:
            result[key] = deepcopy(val)
    return result


def _find_project_root():
    """向上遍历目录树查找 project root（含 CLAUDE.md 或 .claude/ 的目录）。"""
    start = Path(__file__).resolve().parent
    for d in [start] + list(start.parents):
        if (d / "CLAUDE.md").exists():
            return d
        if (d / ".claude").is_dir():
            return d
    return start.parent.parent  # fallback


def load_preferences():
    """加载用户偏好，与 DEFAULTS 深度合并。文件不存在时返回全默认值。"""
    root = _find_project_root()
    pref_file = root / "user_preferences.json"

    if not pref_file.exists():
        return deepcopy(DEFAULTS)

    try:
        with open(pref_file, "r", encoding="utf-8") as f:
            user = json.load(f)
    except (json.JSONDecodeError, IOError):
        return deepcopy(DEFAULTS)

    return _deep_merge(DEFAULTS, user)


# 模块加载时缓存一次
_prefs_cache = None


def get_prefs():
    """获取缓存的偏好（懒加载）。"""
    global _prefs_cache
    if _prefs_cache is None:
        _prefs_cache = load_preferences()
    return _prefs_cache
