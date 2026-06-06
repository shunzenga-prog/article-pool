#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""
Centralised path configuration — single source of truth for every directory and file path
in the project. All scripts import from here instead of computing their own paths.

Override via config/.env:

  WORK_DIR=E:/path/to/work          # all temp/output files under one roof
  ILLUSTRATIONS_DIR=some/path       # override illustrations subdirectory
  REPORTS_DIR=some/path             # override reports subdirectory
  OUTPUT_DIR=some/path              # override general output subdirectory
  SCRAPE_OUTPUT_DIR=some/path       # override scraper output directory

Default values match the existing hardcoded paths exactly — no behaviour change unless
you set an override in .env.
"""

import os
import re
from datetime import date, datetime
from pathlib import Path

# ── Auto-detected project roots ──
SCRIPTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPTS_DIR.parent
CONFIG_DIR = PROJECT_ROOT / "config"

# ── .env loading (cached, idempotent) ──
_ENV_LOADED = False


def load_env():
    """Load config/.env into os.environ. Cached — only reads the file once.
    Uses setdefault so existing env vars are never overwritten."""
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    _ENV_LOADED = True
    env_file = CONFIG_DIR / ".env"
    if not env_file.exists():
        return
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def get_env(key: str) -> str | None:
    """Read a single value from config/.env. Returns None if not found."""
    load_env()
    return os.environ.get(key)


def get_wechat_config() -> tuple[str, str]:
    """Return (WECHAT_APPID, WECHAT_SECRET) from config/.env."""
    load_env()
    return os.environ.get("WECHAT_APPID", ""), os.environ.get("WECHAT_SECRET", "")


# ── Path resolution ──
def _resolve(raw: str | None, default: str) -> Path:
    """Resolve a path string: absolute paths kept as-is, relative resolved against
    PROJECT_ROOT, None falls back to default."""
    if raw is None:
        raw = default
    if raw is None:
        return PROJECT_ROOT / default
    p = Path(raw)
    if p.is_absolute():
        return p
    return PROJECT_ROOT / p


# ── WORK_DIR umbrella ──
load_env()

# If WORK_DIR is set, all subdirectories default to $WORK_DIR/<sub>.
# Individual *_DIR overrides still take precedence.
_WORK_DIR_RAW = os.environ.get("WORK_DIR")
_WORK_DIR = Path(_WORK_DIR_RAW) if _WORK_DIR_RAW else None

_ILLUSTRATIONS_DEFAULT = str((_WORK_DIR / "illustrations") if _WORK_DIR else PROJECT_ROOT / "test_images" / "illustrations")
_REPORTS_DEFAULT = str((_WORK_DIR / "reports") if _WORK_DIR else PROJECT_ROOT / "reports")
_OUTPUT_DEFAULT = str((_WORK_DIR / "output") if _WORK_DIR else PROJECT_ROOT / "output")

# ── Public directory paths ──
ARTICLE_ROOT = _resolve(os.environ.get("ARTICLE_ROOT"), str(PROJECT_ROOT / "文章"))
ILLUSTRATIONS_DIR = _resolve(os.environ.get("ILLUSTRATIONS_DIR"), _ILLUSTRATIONS_DEFAULT)
REPORTS_DIR = _resolve(os.environ.get("REPORTS_DIR"), _REPORTS_DEFAULT)
OUTPUT_DIR = _resolve(os.environ.get("OUTPUT_DIR"), _OUTPUT_DEFAULT)

# Scrapers keep their original default — independent of WORK_DIR unless explicitly overridden.
SCRAPE_OUTPUT_DIR = _resolve(
    os.environ.get("SCRAPE_OUTPUT_DIR"),
    os.environ.get("OUTPUT_DIR", os.path.expanduser("~/.openclaw/workspace/reports/materials")),
)

# ── Derived file paths ──
USED_IMAGES_FILE = REPORTS_DIR / "used_images.json"
USED_TOPICS_FILE = REPORTS_DIR / "used_topics.json"
PUBLISH_LOG_FILE = REPORTS_DIR / "publish_log.json"
CSDN_PUBLISH_LOG_FILE = REPORTS_DIR / "csdn_publish_log.json"
ILLUSTRATION_RULES_FILE = CONFIG_DIR / "illustration_rules.json"

# ── Ensure directories exist ──
for _d in (ILLUSTRATIONS_DIR, REPORTS_DIR, OUTPUT_DIR):
    _d.mkdir(parents=True, exist_ok=True)


def parse_article_date(value: date | datetime | str | None = None) -> date:
    """Return a date for article path generation."""
    if value is None:
        return datetime.now().date()
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    raw = str(value).strip()
    for fmt in ("%Y-%m-%d", "%Y%m%d", "%m%d"):
        try:
            parsed = datetime.strptime(raw, fmt)
            if fmt == "%m%d":
                return date(datetime.now().year, parsed.month, parsed.day)
            return parsed.date()
        except ValueError:
            pass
    raise ValueError(f"Unsupported article date: {value}")


def safe_article_title(title: str) -> str:
    """Sanitize a title for filesystem use while keeping readable Chinese text."""
    cleaned = re.sub(r'[\\/:*?"<>|]+', "", title)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned or "未命名文章"


def article_month_dir(publish_date: date | datetime | str | None = None) -> Path:
    """Return ARTICLE_ROOT/YYYY年MM月 for a publish date."""
    d = parse_article_date(publish_date)
    return ARTICLE_ROOT / f"{d.year}年{d.month:02d}月"


def article_basename(title: str, publish_date: date | datetime | str | None = None) -> str:
    """Return MMDD-safe_title for a publish date."""
    d = parse_article_date(publish_date)
    return f"{d.month:02d}{d.day:02d}-{safe_article_title(title)}"


def article_output_path(
    title: str,
    suffix: str,
    publish_date: date | datetime | str | None = None,
) -> Path:
    """Return the canonical article output path under ARTICLE_ROOT."""
    normalized_suffix = suffix if suffix.startswith(".") else f".{suffix}"
    return article_month_dir(publish_date) / f"{article_basename(title, publish_date)}{normalized_suffix}"
