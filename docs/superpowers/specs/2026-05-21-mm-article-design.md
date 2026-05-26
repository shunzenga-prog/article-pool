# mm-article Design

## Goal

Build a short Codex-first multimodal entrypoint for Article Pool without changing the legacy article workflow. The new entrypoint is `mm-article`.

## Architecture

`mm-article` is a semantic-first skill. It plans around topic evidence, article drafts, screenshots, generated images, visual inspection, render review, and publish results as artifacts. Legacy scripts remain deterministic leaf tools for bounded work such as HTML review, cover layout, image embedding, and publishing.

The new workflow lives in separate paths:

- `skills/mm-article/SKILL.md`
- `workflow/mm-article/manifest.json`
- `.codex-plugin/plugin.json`
- `scripts/validate_mm_workflow.py`
- `scripts/test_mm_workflow.py`

The legacy lane is explicitly preserved. The new workflow may read or call old tools, but it does not inherit old stage semantics and does not change old CLI defaults.

## Boundaries

- Old skills remain in `skills/article-pipeline`, `skills/wechat-writer`, `skills/cover-gen`, and `skills/illustration-gen`.
- Old deterministic tools remain in `scripts/review_html.py`, `scripts/gen_cover.py`, `scripts/illustration_gen.py`, and `scripts/publish_html.py`.
- Codex installation is exposed by the repo-local `.codex-plugin/plugin.json`.
- Multimodal semantics are expressed in `workflow/mm-article/manifest.json`, not by modifying legacy pipeline templates.

## Validation

`scripts/test_mm_workflow.py` verifies that the new skill, manifest, and plugin entry exist, and that protected legacy skills/tools are still present. It also verifies that semantic tasks are real semantic tasks rather than `script_adapter` stages.
