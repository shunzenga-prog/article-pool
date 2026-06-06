#!/usr/bin/env python3
"""
Validate a complete mm-article WeChat delivery.

This is the final local gate for article handoff. It combines existing HTML and
process-leak checks with deterministic artifact checks for cover images, body
illustrations, image quality, and run reports.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from PIL import Image, ImageStat

from review_html import review as review_html
from validate_mm_workflow import validate_article_output


PROJECT_ROOT = Path(__file__).resolve().parent.parent
REMOTE_IMAGE_RE = re.compile(r"^(?:https?:)?//|^data:", re.IGNORECASE)
SOURCE_CAPTURE_IMAGE_RE = re.compile(r"-source-[a-z0-9_-]+-\d{2}-compact\.(?:png|jpe?g|webp)$", re.IGNORECASE)
REJECTED_IMAGE_SOURCES = {
    "geometric",
    "fallback_pattern",
    "fallback_auto",
    "legacy_without_reason",
}
ALLOWED_IMAGE_SOURCES = {
    "agent_direct_final_cover",
    "agent_generated_local_image",
    "source_capture_artifacts",
    "authority_social_post",
    "official_screenshot",
    "official_image",
    "browser_capture",
    "terminal_capture",
    "code_capture",
    "data_chart",
    "github_screenshot",
    "og_image",
    "web_search_factual",
}


def _resolve_existing(path: Path | str, *, base: Path | None = None) -> Path:
    raw = Path(path)
    candidates = []
    if raw.is_absolute():
        candidates.append(raw)
    else:
        if base is not None:
            candidates.append(base / raw)
        candidates.append(Path.cwd() / raw)
        candidates.append(PROJECT_ROOT / raw)
    for candidate in candidates:
        if candidate.exists():
            return candidate.absolute()
    return (candidates[0] if candidates else raw).absolute()


def _base_stem(article: Path) -> str:
    stem = article.stem
    for suffix in ("_illustrated_cdn", "_illustrated", "_cdn", "_publish"):
        if stem.endswith(suffix):
            return stem[: -len(suffix)]
    return stem


def _delivery_paths(article_path: Path) -> dict[str, Path]:
    base = _base_stem(article_path)
    parent = article_path.parent
    return {
        "article": article_path,
        "illustrated_html": parent / f"{base}_illustrated{article_path.suffix}",
        "cover": parent / f"{base}.png",
    }


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _add_check(checks: list[dict[str, Any]], check_id: str, passed: bool, detail: str, **data: Any) -> None:
    item = {"id": check_id, "passed": bool(passed), "detail": detail}
    if data:
        item["data"] = data
    checks.append(item)


def _extract_img_sources(html: str) -> list[str]:
    return re.findall(r'<img\b[^>]*\bsrc=["\']([^"\']+)["\']', html, flags=re.IGNORECASE)


def _resolve_local_image(src: str, html_path: Path) -> Path | None:
    if REMOTE_IMAGE_RE.search(src):
        return None
    return _resolve_existing(src, base=html_path.parent)


def _body_image_role(path: Path) -> str:
    if SOURCE_CAPTURE_IMAGE_RE.search(path.name):
        return "source_capture"
    return "body_image"


def _image_quality(path: Path, *, role: str) -> dict[str, Any]:
    stat = path.stat()
    with Image.open(path) as image:
        width, height = image.size
        small = image.convert("RGB").resize((64, 64), Image.Resampling.LANCZOS)
        gray = small.convert("L")
        stats = ImageStat.Stat(gray)
        brightness = stats.mean[0]
        contrast = stats.stddev[0]

    if role == "cover":
        size_ok = stat.st_size >= 100 * 1024
        dimensions_ok = (width, height) == (1200, 675)
    elif role == "source_capture":
        size_ok = stat.st_size >= 10 * 1024
        dimensions_ok = width >= 480 and height >= 100
    else:
        size_ok = stat.st_size >= 30 * 1024
        dimensions_ok = width >= 600 and height >= 300

    aspect = width / max(height, 1)
    aspect_ok = True if role == "source_capture" else abs(aspect - (16 / 9)) <= 0.08
    non_blank_ok = contrast >= 4.0
    brightness_ok = 18 <= brightness <= 245
    passed = all((size_ok, dimensions_ok, aspect_ok, non_blank_ok, brightness_ok))
    checks = {
        "size": size_ok,
        "dimensions": dimensions_ok,
        "aspect": aspect_ok,
        "non_blank": non_blank_ok,
        "brightness": brightness_ok,
    }
    if role == "source_capture":
        checks["compact_dimensions"] = dimensions_ok
    return {
        "path": str(path),
        "role": role,
        "passed": passed,
        "width": width,
        "height": height,
        "size_kb": round(stat.st_size / 1024, 1),
        "brightness": round(brightness, 1),
        "contrast": round(contrast, 1),
        "checks": checks,
    }


def _manifest_image_paths(run_dir: Path | None) -> list[Path]:
    if run_dir is None:
        return []
    manifest = run_dir / "generated_images.json"
    if not manifest.exists():
        return []
    data = _read_json(manifest)
    entries = data.get("images", data) if isinstance(data, dict) else data
    paths = []
    if not isinstance(entries, list):
        return []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        kind = str(entry.get("kind") or "").lower()
        image_id = str(entry.get("id") or "").lower()
        if "cover" in kind or image_id == "cover":
            continue
        raw = entry.get("path") or entry.get("output_path") or entry.get("file")
        if raw:
            paths.append(_resolve_existing(raw, base=PROJECT_ROOT))
    return paths


def _generated_image_entries(run_dir: Path | None) -> list[dict[str, Any]]:
    if run_dir is None:
        return []
    manifest = run_dir / "generated_images.json"
    if not manifest.exists():
        return []
    data = _read_json(manifest)
    entries = data.get("images", data) if isinstance(data, dict) else data
    if not isinstance(entries, list):
        return []
    normalized = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        raw = entry.get("path") or entry.get("output_path") or entry.get("file")
        fixed = dict(entry)
        if raw:
            fixed["resolved_path"] = str(_resolve_existing(raw, base=run_dir))
        normalized.append(fixed)
    return normalized


def _entry_source(entry: dict[str, Any] | None, *, role: str, path: Path | None = None) -> str:
    if role == "source_capture":
        return "source_capture_artifacts"
    if not entry:
        return "missing_source_metadata"
    source = str(entry.get("source") or entry.get("provenance") or entry.get("origin") or "").strip()
    if source:
        return source
    if str(entry.get("kind") or "").lower() == "cover" or str(entry.get("id") or "").lower() == "cover":
        return "missing_source_metadata"
    if path and SOURCE_CAPTURE_IMAGE_RE.search(path.name):
        return "source_capture_artifacts"
    return "missing_source_metadata"


def _validate_visual_provenance(
    *,
    cover: Path,
    local_images: list[Path],
    generated_entries: list[dict[str, Any]],
) -> dict[str, Any]:
    entries_by_path = {
        Path(entry["resolved_path"]): entry
        for entry in generated_entries
        if entry.get("resolved_path")
    }
    cover_entry = next(
        (
            entry
            for entry in generated_entries
            if str(entry.get("id") or "").lower() == "cover"
            or str(entry.get("kind") or "").lower() == "cover"
            or (entry.get("resolved_path") and Path(entry["resolved_path"]) == cover)
        ),
        None,
    )

    items = []
    if cover.exists():
        source = _entry_source(cover_entry, role="cover", path=cover)
        items.append({"path": str(cover), "role": "cover", "source": source})

    for image_path in local_images:
        role = _body_image_role(image_path)
        entry = entries_by_path.get(image_path)
        source = _entry_source(entry, role=role, path=image_path)
        items.append({"path": str(image_path), "role": role, "source": source})

    failures = []
    for item in items:
        source = item["source"]
        if source in REJECTED_IMAGE_SOURCES:
            failures.append({**item, "reason": "rejected_source"})
        elif source not in ALLOWED_IMAGE_SOURCES:
            failures.append({**item, "reason": "unknown_or_missing_source"})

    return {
        "passed": not failures,
        "items": items,
        "failures": failures,
    }


def validate_delivery(
    article: Path | str,
    *,
    run_dir: Path | str | None = None,
    title: str | None = None,
    require_published: bool = False,
) -> dict[str, Any]:
    article_path = _resolve_existing(article)
    resolved_run_dir = _resolve_existing(run_dir) if run_dir else None
    paths = _delivery_paths(article_path)
    checks: list[dict[str, Any]] = []

    _add_check(checks, "article.exists", article_path.exists(), f"Article: {article_path}")

    illustrated = paths["illustrated_html"]
    cover = paths["cover"]
    _add_check(checks, "illustrated_html.exists", illustrated.exists(), f"Illustrated HTML: {illustrated}")
    _add_check(checks, "cover.exists", cover.exists(), f"Cover: {cover}")

    if illustrated.exists():
        html = illustrated.read_text(encoding="utf-8")
        img_sources = _extract_img_sources(html)
        local_images = [p for p in (_resolve_local_image(src, illustrated) for src in img_sources) if p is not None]
        local_images.extend(path for path in _manifest_image_paths(resolved_run_dir) if path.name != cover.name)
        # Keep stable order while de-duplicating.
        seen: set[Path] = set()
        local_images = [p for p in local_images if not (p in seen or seen.add(p))]
        _add_check(
            checks,
            "body_images.present",
            len(img_sources) > 0 and len(local_images) > 0,
            f"Found {len(img_sources)} img tag(s), {len(local_images)} inspectable local image(s)",
            image_sources=img_sources,
            local_images=[str(p) for p in local_images],
        )

        html_result = review_html(str(illustrated), title=title)
        _add_check(
            checks,
            "wechat_html_review.passed",
            bool(html_result.get("passed")),
            html_result.get("verdict", "UNKNOWN"),
            failures=html_result.get("failures", []),
            warnings=html_result.get("warnings", []),
        )

        leak_result = validate_article_output(illustrated)
        _add_check(
            checks,
            "process_leak.passed",
            bool(leak_result.get("passed")),
            "No reader-visible process leaks" if leak_result.get("passed") else "Reader-visible process leaks found",
            leaks=leak_result.get("reader_visible_process_leaks", []),
        )
    else:
        img_sources = []
        local_images = []
        _add_check(
            checks,
            "body_images.present",
            False,
            "Illustrated HTML is missing, so body images cannot be inspected",
            image_sources=[],
            local_images=[],
        )

    generated_entries = _generated_image_entries(resolved_run_dir)
    provenance = _validate_visual_provenance(
        cover=cover,
        local_images=local_images,
        generated_entries=generated_entries,
    )
    failed_sources = sorted({item["source"] for item in provenance["failures"]})
    _add_check(
        checks,
        "visual_provenance.passed",
        bool(provenance["passed"]),
        (
            "Visual sources accepted"
            if provenance["passed"]
            else f"Rejected or missing visual sources: {', '.join(failed_sources)}"
        ),
        provenance=provenance,
    )

    if cover.exists():
        cover_quality = _image_quality(cover, role="cover")
        _add_check(
            checks,
            "cover.quality",
            bool(cover_quality["passed"]),
            "Cover quality inspection",
            quality=cover_quality,
        )

    body_quality_reports = []
    for image_path in local_images:
        if image_path.exists():
            body_quality_reports.append(_image_quality(image_path, role=_body_image_role(image_path)))
        else:
            body_quality_reports.append({"path": str(image_path), "passed": False, "reason": "missing file"})
    if local_images:
        _add_check(
            checks,
            "body_images.quality",
            all(item.get("passed") for item in body_quality_reports),
            "Body image quality inspection",
            images=body_quality_reports,
        )

    if resolved_run_dir is not None:
        expected_reports = [
            "evidence.json",
            "title_decision.json",
            "content_prompt.md",
            "visual_plan.json",
            "image_requests.json",
            "generated_images.json",
            "review.json",
            "publish_result.json",
        ]
        missing_reports = [name for name in expected_reports if not (resolved_run_dir / name).exists()]
        _add_check(
            checks,
            "run_reports.present",
            not missing_reports,
            f"Run directory: {resolved_run_dir}",
            missing=missing_reports,
        )
        publish_path = resolved_run_dir / "publish_result.json"
        if publish_path.exists():
            publish = _read_json(publish_path)
            status = publish.get("status")
            ok_statuses = {"ready_not_published", "draft_created", "published"}
            if require_published:
                passed = status in {"draft_created", "published"} and bool(
                    publish.get("id") or publish.get("draft_id") or publish.get("media_id")
                )
            else:
                passed = status in ok_statuses
            _add_check(
                checks,
                "publish_status.ready",
                passed,
                f"Publish status: {status}",
                publish_result=publish,
            )

    failed = [check for check in checks if not check["passed"]]
    report = {
        "passed": not failed,
        "summary": {
            "total_checks": len(checks),
            "passed_checks": len(checks) - len(failed),
            "failed_checks": len(failed),
        },
        "artifacts": {
            "article": str(article_path),
            "illustrated_html": str(illustrated),
            "cover": str(cover),
            "run_dir": str(resolved_run_dir) if resolved_run_dir else None,
        },
        "checks": checks,
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate complete mm-article delivery artifacts.")
    parser.add_argument("article", help="Original or illustrated article HTML path")
    parser.add_argument("--run-dir", default=None, help="reports/mm-article/<run_id> directory")
    parser.add_argument("--title", default=None, help="WeChat system title for duplicate-title checks")
    parser.add_argument("--require-published", action="store_true", help="Require draft_created/published status")
    parser.add_argument(
        "--write-report",
        nargs="?",
        const="delivery_gate.json",
        default=None,
        help="Write JSON report to this path, or delivery_gate.json in --run-dir when no path is provided",
    )
    args = parser.parse_args()

    report = validate_delivery(
        args.article,
        run_dir=args.run_dir,
        title=args.title,
        require_published=args.require_published,
    )

    if args.write_report:
        if args.write_report == "delivery_gate.json" and args.run_dir:
            out_path = _resolve_existing(args.run_dir) / "delivery_gate.json"
        else:
            out_path = Path(args.write_report)
            if not out_path.is_absolute():
                out_path = PROJECT_ROOT / out_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        report["written_report"] = str(out_path)

    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
