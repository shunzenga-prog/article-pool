#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
# If WORK_DIR is set, all subdirectories default to $WORK_DIR/<sub>.
# Individual *_DIR overrides still take precedence.
_WORK_DIR_RAW = os.environ.get("WORK_DIR")
_WORK_DIR = Path(_WORK_DIR_RAW) if _WORK_DIR_RAW else None

_ILLUSTRATIONS_DEFAULT = str((_WORK_DIR / "illustrations") if _WORK_DIR else PROJECT_ROOT / "test_images" / "illustrations")
_REPORTS_DEFAULT = str((_WORK_DIR / "reports") if _WORK_DIR else PROJECT_ROOT / "reports")
_OUTPUT_DEFAULT = str((_WORK_DIR / "output") if _WORK_DIR else PROJECT_ROOT / "output")

# ── Public directory paths ──
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
ILLUSTRATION_RULES_FILE = CONFIG_DIR / "illustration_rules.json"

# ── Ensure directories exist ──
for _d in (ILLUSTRATIONS_DIR, REPORTS_DIR, OUTPUT_DIR):
    _d.mkdir(parents=True, exist_ok=True)
