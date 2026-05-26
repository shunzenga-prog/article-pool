# mm-article Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the `mm-article` multimodal workflow entrypoint while preserving the legacy Article Pool workflow.

**Architecture:** Add a new skill, workflow manifest, Codex plugin manifest, and validator. The new semantic workflow is isolated from legacy skills and only uses old scripts as deterministic leaf tools.

**Tech Stack:** Codex skills, JSON manifest, Python unittest validator.

---

### Task 1: Validation Harness

**Files:**
- Create: `scripts/test_mm_workflow.py`
- Create: `scripts/validate_mm_workflow.py`

- [x] **Step 1: Write the failing test**

The test imports `validate_mm_workflow`, calls `validate_project(ROOT)`, and asserts that `mm-article`, the manifest, the Codex plugin skills path, and the preserved legacy lane all exist.

- [x] **Step 2: Run test to verify it fails**

Run: `python scripts/test_mm_workflow.py`

Expected: FAIL with `ModuleNotFoundError: No module named 'validate_mm_workflow'`.

- [x] **Step 3: Write the validator**

The validator reads `skills/mm-article/SKILL.md`, `workflow/mm-article/manifest.json`, and `.codex-plugin/plugin.json`, validates protected legacy paths, rejects semantic tasks with `execution: script_adapter`, and prints a JSON report.

- [x] **Step 4: Run test to verify it passes**

Run: `python scripts/test_mm_workflow.py`

Expected: PASS.

### Task 2: Multimodal Workflow Entry

**Files:**
- Create: `skills/mm-article/SKILL.md`
- Create: `workflow/mm-article/manifest.json`
- Create: `.codex-plugin/plugin.json`

- [x] **Step 1: Add the short skill entry**

Create `skills/mm-article/SKILL.md` with frontmatter name `mm-article`, a trigger description, first-load instruction for the manifest, and isolation rules for legacy skills and scripts.

- [x] **Step 2: Add the semantic manifest**

Create `workflow/mm-article/manifest.json` with host capabilities, preserved legacy lane, semantic tasks, artifact kinds, deterministic tool boundaries, and quality gates.

- [x] **Step 3: Add the Codex plugin manifest**

Create `.codex-plugin/plugin.json` with `skills: "./skills/"`, Article Pool interface metadata, and short default prompts.

- [x] **Step 4: Verify**

Run: `python scripts/test_mm_workflow.py`

Expected: PASS.
