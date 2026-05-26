#!/usr/bin/env python3
"""Validate repo-local Codex skill metadata without external YAML dependencies."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


FRONTMATTER_PATTERN = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
REQUIRED_KEYS = ("name", "description")
ALLOWED_KEYS = set(REQUIRED_KEYS)


def parse_frontmatter(skill_path: Path) -> dict[str, str]:
    text = skill_path.read_text(encoding="utf-8")
    match = FRONTMATTER_PATTERN.match(text)
    if not match:
        raise ValueError("missing YAML frontmatter block")

    result: dict[str, str] = {}
    for raw_line in match.group(1).splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if ":" not in line:
            raise ValueError(f"invalid frontmatter line: {raw_line}")
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        result[key] = value
    return result


def validate_skill_dir(skill_dir: Path) -> dict[str, Any]:
    skill_path = skill_dir / "SKILL.md"
    errors: list[str] = []
    warnings: list[str] = []
    metadata: dict[str, str] = {}

    if not skill_path.exists():
        return {
            "skill": skill_dir.name,
            "path": str(skill_path),
            "metadata": metadata,
            "errors": ["missing SKILL.md"],
            "warnings": warnings,
            "passed": False,
        }

    try:
        metadata = parse_frontmatter(skill_path)
    except ValueError as exc:
        errors.append(str(exc))

    missing_keys = [key for key in REQUIRED_KEYS if not metadata.get(key)]
    if missing_keys:
        errors.append(f"missing required frontmatter keys: {', '.join(missing_keys)}")

    extra_keys = sorted(set(metadata) - ALLOWED_KEYS)
    if extra_keys:
        errors.append(f"unsupported frontmatter keys: {', '.join(extra_keys)}")

    name = metadata.get("name", "")
    if name:
        if not SLUG_PATTERN.fullmatch(name):
            errors.append("name must use lowercase letters, digits, and hyphens")
        if name != skill_dir.name:
            errors.append(f"name must match folder name: {skill_dir.name}")

    description = metadata.get("description", "")
    if description and not description.startswith("Use when"):
        errors.append('description must start with "Use when"')

    line_count = len(skill_path.read_text(encoding="utf-8").splitlines())
    if line_count > 500:
        warnings.append(f"SKILL.md is {line_count} lines; consider moving detail into references")

    return {
        "skill": skill_dir.name,
        "path": str(skill_path),
        "metadata": metadata,
        "errors": errors,
        "warnings": warnings,
        "passed": not errors,
    }


def validate_skills(skills_root: Path) -> dict[str, Any]:
    skill_dirs = sorted(path for path in skills_root.iterdir() if path.is_dir())
    results = [validate_skill_dir(skill_dir) for skill_dir in skill_dirs]
    errors = [
        f"{item['skill']}: {error}"
        for item in results
        for error in item["errors"]
    ]
    warnings = [
        f"{item['skill']}: {warning}"
        for item in results
        for warning in item["warnings"]
    ]
    return {
        "skill_count": len(results),
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
        "skills": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate Article Pool skill metadata.")
    parser.add_argument("skills_root", nargs="?", default="skills", help="Path to the skills directory.")
    args = parser.parse_args()

    report = validate_skills(Path(args.skills_root))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
