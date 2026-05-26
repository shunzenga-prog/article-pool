#!/usr/bin/env python3
"""
Validate the mm-article multimodal workflow package.

The validator checks installability and legacy isolation only. It does not run
publishing or image-generation side effects.
"""

import json
import re
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _read_frontmatter(path: Path) -> dict[str, str]:
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")

    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError(f"Missing YAML frontmatter: {path}")

    end = text.find("---", 3)
    if end == -1:
        raise ValueError(f"Unclosed YAML frontmatter: {path}")

    result: dict[str, str] = {}
    for line in text[3:end].strip().splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        result[key.strip()] = value.strip().strip('"').strip("'")
    return result


def _require_existing(root: Path, relative_paths: list[str]) -> None:
    missing = [rel for rel in relative_paths if not (root / rel).exists()]
    if missing:
        raise FileNotFoundError(f"Missing protected legacy paths: {missing}")


PROCESS_LEAK_PHRASES = (
    "事实型界面图优先",
    "事实型图片优先",
    "事实型视觉",
    "不用生成图替代",
    "生成图替代",
    "裁切版",
    "视觉计划",
    "图片请求",
    "审阅通过",
    "审阅说明",
    "工作流提示词",
    "生产备注",
    "image_requests",
    "generated_images",
)


def _compact_visible_text(html_text: str) -> str:
    text = re.sub(r"<script[^>]*>.*?</script>", "", html_text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _snippet(text: str, phrase: str) -> str:
    index = text.find(phrase)
    if index < 0:
        return ""
    start = max(0, index - 32)
    end = min(len(text), index + len(phrase) + 32)
    return text[start:end].strip()


def detect_reader_visible_process_leaks(html_text: str) -> list[dict[str, str]]:
    """Find creator-only workflow notes that leaked into reader-visible output."""
    visible_text = _compact_visible_text(html_text)
    scan_text = f"{visible_text}\n{html_text}"
    leaks: list[dict[str, str]] = []
    for phrase in PROCESS_LEAK_PHRASES:
        if phrase in scan_text:
            leaks.append({"phrase": phrase, "snippet": _snippet(scan_text, phrase)})
    return leaks


def validate_article_output(article_path: Path | str) -> dict[str, Any]:
    path = Path(article_path)
    if not path.exists():
        raise FileNotFoundError(f"Missing article file: {path}")
    html_text = path.read_text(encoding="utf-8")
    leaks = detect_reader_visible_process_leaks(html_text)
    return {
        "path": str(path),
        "reader_visible_process_leaks": leaks,
        "passed": not leaks,
    }


def _collect_dataflow_errors(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    available = set(manifest.get("external_inputs", []))
    errors: list[dict[str, Any]] = []

    for task in manifest.get("semantic_tasks", []):
        inputs = task.get("inputs", [])
        missing = [name for name in inputs if name not in available]
        if missing:
            errors.append({"task": task.get("kind", ""), "missing_inputs": missing})
        available.update(task.get("outputs", []))

    return errors


def _validate_output_contract(manifest: dict[str, Any]) -> None:
    output_contract = manifest.get("output_contract")
    if not isinstance(output_contract, dict):
        raise ValueError("manifest.output_contract must be an object")
    for section in ("wechat", "reports"):
        if not isinstance(output_contract.get(section), dict):
            raise ValueError(f"manifest.output_contract.{section} must be an object")

    for field in ("article_root", "base_dir", "basename"):
        if not output_contract.get(field):
            raise ValueError(f"manifest.output_contract.{field} is required")

    wechat = output_contract["wechat"]
    required_wechat_fields = (
        "draft_html",
        "illustrated_html",
        "cdn_html",
        "cover_png",
        "cover_background",
        "visual_dir",
        "body_image_pattern",
        "screenshot_pattern",
    )
    for field in required_wechat_fields:
        if not wechat.get(field):
            raise ValueError(f"manifest.output_contract.wechat.{field} is required")

    for key in ("illustration_policy", "cover_policy"):
        if not isinstance(manifest.get(key), dict):
            raise ValueError(f"manifest.{key} must be an object")


def validate_project(root: Path | str) -> dict[str, Any]:
    root = Path(root)
    skill_path = root / "skills" / "mm-article" / "SKILL.md"
    manifest_path = root / "workflow" / "mm-article" / "manifest.json"
    plugin_path = root / ".codex-plugin" / "plugin.json"

    skill = _read_frontmatter(skill_path)
    manifest = _read_json(manifest_path)
    plugin = _read_json(plugin_path)

    if skill.get("name") != "mm-article":
        raise ValueError("mm-article skill frontmatter name must be mm-article")
    if manifest.get("skill") != "mm-article":
        raise ValueError("mm-article manifest must point to the mm-article skill")
    if plugin.get("skills") != "./skills/":
        raise ValueError("Codex plugin manifest must expose ./skills/")

    legacy_lane = manifest.get("legacy_lane", {})
    protected_skills = legacy_lane.get("protected_skills", [])
    protected_tools = legacy_lane.get("protected_tools", [])

    _require_existing(root, [f"skills/{name}/SKILL.md" for name in protected_skills])
    _require_existing(root, protected_tools)

    semantic_tasks = manifest.get("semantic_tasks", [])
    if not isinstance(semantic_tasks, list) or not semantic_tasks:
        raise ValueError("manifest.semantic_tasks must be a non-empty list")
    for task in semantic_tasks:
        if not task.get("kind") or not task.get("intent"):
            raise ValueError(f"semantic task is missing kind or intent: {task}")
        if task.get("execution") == "script_adapter":
            raise ValueError(f"semantic task cannot be a script adapter: {task['kind']}")

    production_standards = manifest.get("production_standards", [])
    if not isinstance(production_standards, list) or not production_standards:
        raise ValueError("manifest.production_standards must be a non-empty list")
    for item in production_standards:
        missing = [field for field in ("id", "gate", "failure_mode") if not item.get(field)]
        if missing:
            raise ValueError(f"production standard is missing {missing}: {item}")

    dataflow_errors = _collect_dataflow_errors(manifest)
    _validate_output_contract(manifest)

    return {
        "skill": skill,
        "manifest": {
            **manifest,
            "semantic_task_count": len(semantic_tasks),
            "production_standard_count": len(production_standards),
            "dataflow_errors": dataflow_errors,
        },
        "plugin": plugin,
        "legacy_lane": legacy_lane,
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Validate mm-article workflow assets and optional article outputs.")
    parser.add_argument("--article", action="append", default=[], help="Article HTML file to scan for mm-article leaks.")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    report = validate_project(root)
    if args.article:
        article_reports = [validate_article_output(path) for path in args.article]
        report["articles"] = article_reports
        if any(not item["passed"] for item in article_reports):
            print(json.dumps(report, ensure_ascii=False, indent=2))
            raise SystemExit(1)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
