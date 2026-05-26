import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

import validate_skills


class SkillValidationTests(unittest.TestCase):
    def test_repo_skills_have_valid_frontmatter(self):
        report = validate_skills.validate_skills(ROOT / "skills")

        self.assertEqual(report["errors"], [])
        self.assertGreaterEqual(report["skill_count"], 10)

    def test_validator_rejects_non_slug_skill_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = Path(tmp) / "bad-name"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                "---\n"
                "name: Bad Name\n"
                "description: Use when checking invalid skill metadata.\n"
                "---\n\n"
                "# Bad\n",
                encoding="utf-8",
            )

            report = validate_skills.validate_skill_dir(skill_dir)

        self.assertFalse(report["passed"])
        self.assertIn("name must use lowercase letters, digits, and hyphens", report["errors"][0])


if __name__ == "__main__":
    unittest.main()
