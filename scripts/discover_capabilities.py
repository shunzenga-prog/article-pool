#!/usr/bin/env python3
"""
Capability Discovery — scan agents/, skills/, scripts/ and build a unified
capability registry JSON consumed by the pipeline planner and orchestrator.

Usage:
  python scripts/discover_capabilities.py              # write config/capabilities.json
  python scripts/discover_capabilities.py --dry-run    # print to stdout only
"""

import json, os, re, ast, sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
AGENTS_DIR   = PROJECT_ROOT / "agents"
SKILLS_DIR   = PROJECT_ROOT / "skills"
SCRIPTS_DIR  = PROJECT_ROOT / "scripts"
CONFIG_DIR   = PROJECT_ROOT / "config"
OUTPUT_FILE  = CONFIG_DIR / "capabilities.json"
OVERRIDES_FILE = CONFIG_DIR / "capabilities_overrides.json"

# ── helpers ──────────────────────────────────────────────

def _parse_yaml_frontmatter(text: str) -> dict | None:
    """Parse YAML frontmatter between --- delimiters. Minimal implementation."""
    text = text.strip()
    if not text.startswith("---"):
        return None
    end = text.find("---", 3)
    if end == -1:
        return None
    block = text[3:end].strip()
    result = {}
    for line in block.split("\n"):
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            # Parse list values like [Bash, Read]
            if val.startswith("[") and val.endswith("]"):
                val = [v.strip() for v in val[1:-1].split(",") if v.strip()]
            result[key] = val
    return result


def _extract_argparse_params(source: str) -> dict:
    """Parse add_argument calls to extract parameter schema."""
    params = {}
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return params
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = None
            if isinstance(node.func, ast.Attribute):
                func = node.func.attr
            if func != "add_argument":
                continue
            # Extract arg name
            name = None
            kwargs = {}
            for kw in node.keywords:
                kwargs[kw.arg] = ast.literal_eval(kw.value) if isinstance(kw.value, ast.Constant) else str(kw.value)
            for arg in node.args:
                val = ast.literal_eval(arg) if isinstance(arg, ast.Constant) else str(arg)
                if val.startswith("--"):
                    name = val.lstrip("-")
            if not name:
                continue
            param = {}
            if "help" in kwargs:
                param["help"] = str(kwargs["help"])
            if "default" in kwargs:
                param["default"] = kwargs["default"]
            if "choices" in kwargs:
                param["choices"] = list(kwargs["choices"])
            if "type" in kwargs:
                param["type"] = str(kwargs["type"])
            if "required" in kwargs:
                param["required"] = kwargs["required"]
            params[name] = param
    return params


def _capability_key(cap_type: str, file_stem: str, frontmatter_name: str = "") -> str:
    """Generate a stable capability key. Uses frontmatter name if available."""
    if frontmatter_name:
        return frontmatter_name.replace(" ", "_").replace("-", "_")
    return f"{cap_type}.{file_stem}"


# ── scanners ─────────────────────────────────────────────

def scan_agents() -> list[dict]:
    """Scan agents/**/*.md for frontmatter-defined agents."""
    results = []
    for md_file in AGENTS_DIR.rglob("*.md"):
        if md_file.name == "README.md":
            continue
        content = md_file.read_text(encoding="utf-8")
        fm = _parse_yaml_frontmatter(content)
        if not fm or "name" not in fm:
            continue
        rel = str(md_file.relative_to(PROJECT_ROOT)).replace("\\", "/")
        results.append({
            "key": _capability_key("agent", md_file.stem, fm.get("name", "")),
            "type": "agent",
            "file": rel,
            "name": fm.get("name", md_file.stem),
            "description": fm.get("description", ""),
            "tools": fm.get("tools", []),
        })
    return results


def scan_skills() -> list[dict]:
    """Scan skills/**/SKILL.md for frontmatter-defined skills."""
    results = []
    for md_file in SKILLS_DIR.rglob("SKILL.md"):
        content = md_file.read_text(encoding="utf-8")
        fm = _parse_yaml_frontmatter(content)
        if not fm:
            continue
        rel = str(md_file.relative_to(PROJECT_ROOT)).replace("\\", "/")
        results.append({
            "key": _capability_key("skill", md_file.parent.name, fm.get("name", "")),
            "type": "skill",
            "file": rel,
            "name": fm.get("name", md_file.parent.name),
            "description": fm.get("description", ""),
        })
    return results


def scan_scripts() -> list[dict]:
    """Scan scripts/*.py for CLI tools with argparse interfaces."""
    results = []
    # Skip internal/utility modules
    skip = {"paths", "preferences", "discover_capabilities", "orchestrator",
            "rebuild_cjk_font", "replace_local_images", "__init__"}
    for py_file in sorted(SCRIPTS_DIR.glob("*.py")):
        stem = py_file.stem
        if stem in skip:
            continue
        source = py_file.read_text(encoding="utf-8")
        params = _extract_argparse_params(source)
        if not params:
            # Script has no argparse — skip unless it's well-known
            continue
        # Derive primary function from docstring
        doc = ""
        if source.strip().startswith('"""') or source.strip().startswith("'''"):
            end = source.find(source[:3], 3)
            if end > 0:
                doc = source[3:end].strip().split("\n")[0]
        # Check for constraints from overrides or heuristics
        constraints = []
        if "mode" in params and "choices" in params.get("mode", {}):
            constraints.append("has_mode_param")
        rel = str(py_file.relative_to(PROJECT_ROOT)).replace("\\", "/")
        results.append({
            "key": f"script.{stem}",
            "type": "script",
            "file": rel,
            "name": stem,
            "description": doc,
            "params": params,
            "constraints": constraints,
        })
    return results


# ── main ─────────────────────────────────────────────────

def build_registry() -> dict:
    agents = scan_agents()
    skills = scan_skills()
    scripts = scan_scripts()

    all_caps = {}
    for entry in agents + skills + scripts:
        all_caps[entry["key"]] = {k: v for k, v in entry.items() if k != "key"}

    # Merge overrides
    overrides = {}
    if OVERRIDES_FILE.exists():
        overrides = json.loads(OVERRIDES_FILE.read_text(encoding="utf-8"))
    for cap_key, patch in overrides.get("overrides", {}).items():
        if cap_key in all_caps:
            all_caps[cap_key].update(patch)
        else:
            all_caps[cap_key] = patch

    return {
        "generated_at": __import__("datetime").datetime.now().isoformat(),
        "counts": {
            "agents": len(agents),
            "skills": len(skills),
            "scripts": len(scripts),
            "total": len(all_caps),
        },
        "capabilities": all_caps,
    }


def main():
    import argparse
    p = argparse.ArgumentParser(description="Discover project capabilities")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    registry = build_registry()
    json_str = json.dumps(registry, ensure_ascii=False, indent=2)

    if args.dry_run:
        print(json_str)
    else:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        OUTPUT_FILE.write_text(json_str, encoding="utf-8")
        print(f"OK: {OUTPUT_FILE}")
        print(f"  agents: {registry['counts']['agents']}")
        print(f"  skills: {registry['counts']['skills']}")
        print(f"  scripts: {registry['counts']['scripts']}")
        print(f"  total: {registry['counts']['total']}")


if __name__ == "__main__":
    main()
