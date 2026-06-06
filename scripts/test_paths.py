import importlib
import os
import sys
import unittest
from datetime import date
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
CONFIG_ENV = ROOT / "config" / ".env"
sys.path.insert(0, str(SCRIPTS))


class PathsConfigTests(unittest.TestCase):
    def setUp(self):
        self._env_backup = CONFIG_ENV.read_text(encoding="utf-8") if CONFIG_ENV.exists() else None
        self._os_env_backup = {
            key: os.environ.get(key)
            for key in (
                "ARTICLE_ROOT",
                "WORK_DIR",
                "ILLUSTRATIONS_DIR",
                "REPORTS_DIR",
                "OUTPUT_DIR",
                "SCRAPE_OUTPUT_DIR",
            )
        }
        for key in self._os_env_backup:
            os.environ.pop(key, None)

    def tearDown(self):
        if self._env_backup is None:
            if CONFIG_ENV.exists():
                CONFIG_ENV.unlink()
        else:
            CONFIG_ENV.write_text(self._env_backup, encoding="utf-8")
        for key, value in self._os_env_backup.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        sys.modules.pop("paths", None)

    def test_config_env_controls_article_root_before_constants_are_built(self):
        CONFIG_ENV.write_text(
            "ARTICLE_ROOT=/Users/mulin/workspace/公众号/文章\n"
            "REPORTS_DIR=reports\n"
            "OUTPUT_DIR=output\n",
            encoding="utf-8",
        )

        paths = importlib.import_module("paths")

        self.assertEqual(paths.ARTICLE_ROOT, Path("/Users/mulin/workspace/公众号/文章"))

    def test_article_output_path_uses_month_directory_and_mmdd_basename(self):
        CONFIG_ENV.write_text(
            "ARTICLE_ROOT=/Users/mulin/workspace/公众号/文章\n",
            encoding="utf-8",
        )
        paths = importlib.import_module("paths")

        output = paths.article_output_path(
            "claude code最新实践指南",
            suffix=".html",
            publish_date=date(2026, 6, 5),
        )

        self.assertEqual(
            output,
            Path("/Users/mulin/workspace/公众号/文章/2026年06月/0605-claude code最新实践指南.html"),
        )


if __name__ == "__main__":
    unittest.main()
