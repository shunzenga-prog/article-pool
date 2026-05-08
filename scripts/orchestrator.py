#!/usr/bin/env python3
"""
Pipeline Orchestration Engine — reads PipelinePlan JSON + Capability Registry,
recursively expands sub-pipelines, resolves dependencies, and executes tasks
with hook-based dynamic compensation.

Usage:
  python scripts/orchestrator.py plan.json
  python scripts/orchestrator.py plan.json --dry-run
  python scripts/orchestrator.py plan.json --stage S2       # execute single stage
  python scripts/orchestrator.py plan.json --from S2T3       # resume from task
"""

import json, os, sys, subprocess, time, traceback
from pathlib import Path
from datetime import datetime
from typing import Any
from collections import deque

# Fix Windows stdout encoding for emoji/special chars
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_FILE = PROJECT_ROOT / "config" / "capabilities.json"
LOG_DIR = PROJECT_ROOT / "reports"
LOG_DIR.mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════════════════════
#  Registry
# ═══════════════════════════════════════════════════════════

def load_registry() -> dict:
    if not REGISTRY_FILE.exists():
        return {"capabilities": {}}
    return json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))


# ═══════════════════════════════════════════════════════════
#  PipelinePlan loader + validator
# ═══════════════════════════════════════════════════════════

def load_plan(plan_path: str) -> dict:
    with open(plan_path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_plan(plan: dict, registry: dict) -> list[str]:
    """Check every task capability exists in registry. Returns errors."""
    errors = []
    caps = registry.get("capabilities", {})

    def _check_stage(stage, path=""):
        for task in stage.get("tasks", []):
            cap = task.get("capability", "")
            p = f"{path}/{task['id']}"
            if cap and cap not in caps:
                errors.append(f"{p}: capability '{cap}' not found in registry")
            if "sub_pipeline" in task:
                for sub_stage in task["sub_pipeline"].get("stages", []):
                    _check_stage(sub_stage, p)

    for stage in plan.get("stages", []):
        for task in stage.get("tasks", []):
            cap = task.get("capability", "")
            p = f"{stage['id']}/{task['id']}"
            if cap and cap not in caps:
                errors.append(f"{p}: capability '{cap}' not found in registry")
            if "sub_pipeline" in task:
                for sub_stage in task["sub_pipeline"].get("stages", []):
                    _check_stage(sub_stage, p)
    return errors


# ═══════════════════════════════════════════════════════════
#  Topological sort + parallel detection
# ═══════════════════════════════════════════════════════════

def flatten_tasks(stages: list[dict]) -> list[dict]:
    """Flatten all tasks across stages with stage metadata attached."""
    flat = []
    for stage in stages:
        for task in stage.get("tasks", []):
            task["_stage_id"] = stage["id"]
            task["_stage_parallel"] = stage.get("parallel", False)
            task["_stage_hooks"] = stage.get("hooks", {})
            flat.append(task)
    return flat


def build_execution_order(tasks: list[dict]) -> list[list[dict]]:
    """Group tasks into execution rounds respecting dependencies.

    Round 0: tasks with no unresolved dependencies
    Round 1: tasks whose deps were all in Round 0
    ...

    Tasks within the same round can run in parallel (if their stage allows).
    """
    task_ids = {t["id"] for t in tasks}
    rounds = []
    done = set()

    remaining = list(tasks)
    while remaining:
        round_tasks = []
        next_remaining = []
        for task in remaining:
            deps = [d for d in task.get("depends_on", []) if d in task_ids]
            if all(d in done for d in deps):
                round_tasks.append(task)
                done.add(task["id"])
            else:
                next_remaining.append(task)
        if not round_tasks:
            # Circular dependency or unresolvable — push all remaining
            round_tasks = next_remaining
            for t in round_tasks:
                done.add(t["id"])
            next_remaining = []
        rounds.append(round_tasks)
        remaining = next_remaining

    return rounds


# ═══════════════════════════════════════════════════════════
#  Task Executor
# ═══════════════════════════════════════════════════════════

def resolve_command(capability: str, registry: dict, task_input: dict) -> str | None:
    """Resolve a capability into an executable command.

    Returns None for 'agent'/'skill' types (require AI handoff).
    Returns a shell command string for 'script' types.
    """
    cap = registry["capabilities"].get(capability)
    if not cap:
        return None

    if cap["type"] == "script":
        script_path = PROJECT_ROOT / cap["file"]
        parts = [sys.executable, str(script_path)]
        # Build CLI args from task input dict
        for key, val in (task_input or {}).items():
            if key.startswith("_"):
                continue
            arg_key = f"--{key.replace('_', '-')}"
            if isinstance(val, bool):
                if val:
                    parts.append(arg_key)
            elif isinstance(val, list):
                parts.append(arg_key)
                parts.append(",".join(str(v) for v in val))
            elif val is not None:
                parts.append(arg_key)
                parts.append(str(val))
        return " ".join(parts)

    return None  # agent / skill


def execute_task(task: dict, registry: dict, dry_run: bool = False,
                 context: dict = None) -> dict:
    """Execute a single task. Returns result dict."""
    cap_name = task.get("capability", "")
    cap = registry["capabilities"].get(cap_name, {})
    cap_type = cap.get("type", "unknown")

    result = {
        "task_id": task["id"],
        "capability": cap_name,
        "type": cap_type,
        "started_at": datetime.now().isoformat(),
        "status": "unknown",
    }

    cmd = resolve_command(cap_name, registry, task.get("input", {}))

    if cap_type == "script" and cmd:
        if dry_run:
            result["status"] = "dry_run"
            result["command"] = cmd
        else:
            try:
                proc = subprocess.run(
                    cmd, shell=True, capture_output=True, text=True,
                    timeout=300, cwd=str(PROJECT_ROOT),
                    encoding="utf-8", errors="replace",
                    env={**os.environ, "PYTHONIOENCODING": "utf-8"}
                )
                result["exit_code"] = proc.returncode
                result["stdout"] = proc.stdout[-2000:]
                result["stderr"] = proc.stderr[-1000:]
                result["status"] = "ok" if proc.returncode == 0 else "failed"
            except subprocess.TimeoutExpired:
                result["status"] = "timeout"
                result["error"] = "Command timed out after 300s"
            except Exception as e:
                result["status"] = "error"
                result["error"] = str(e)
    elif cap_type in ("agent", "skill"):
        result["status"] = "requires_ai" if not dry_run else "dry_run"
        result["note"] = f"AI handoff needed for {cap_type}: {cap.get('file','')}"
    else:
        result["status"] = "skipped" if dry_run else "unsupported"
        result["error"] = f"Unsupported capability type: {cap_type}"

    result["finished_at"] = datetime.now().isoformat()
    return result


# ═══════════════════════════════════════════════════════════
#  Hook Executor
# ═══════════════════════════════════════════════════════════

def execute_hooks(hooks: dict, hook_type: str, context: dict) -> dict | None:
    """Execute hooks of given type. Returns action dict or None."""
    hook_cfg = hooks.get(hook_type, {})
    if not hook_cfg:
        return None

    if hook_type == "on_failure":
        retry = hook_cfg.get("retry", 0)
        fallback = hook_cfg.get("fallback", "escalate")
        return {"action": "retry" if retry > 0 else fallback, "retries_left": retry}

    if hook_type == "on_stage_entry":
        required = hook_cfg.get("require_inputs", [])
        missing = [r for r in required if r not in context]
        if missing:
            return {"action": "block", "reason": f"Missing inputs: {missing}"}
        return {"action": "proceed"}

    if hook_type == "on_stage_complete":
        gate = hook_cfg.get("gate", "")
        if gate:
            return {"action": "check_gate", "condition": gate}
        return {"action": "proceed"}

    return None


# ═══════════════════════════════════════════════════════════
#  Main Orchestrator
# ═══════════════════════════════════════════════════════════

def run_pipeline(plan: dict, registry: dict, dry_run: bool = False,
                 target_stage: str = None, from_task: str = None) -> list[dict]:
    """Execute pipeline plan stage by stage."""
    stages = plan.get("stages", [])
    log = []
    context = plan.get("context", {})

    # Filter stages
    if target_stage:
        stages = [s for s in stages if s["id"] == target_stage]
    if from_task:
        # Find the stage containing the task, and all subsequent stages
        found = False
        filtered = []
        for stage in stages:
            task_ids = [t["id"] for t in stage.get("tasks", [])]
            if from_task in task_ids:
                found = True
                # Start from this task within this stage
                stage["tasks"] = [t for t in stage["tasks"] if t["id"] == from_task or
                                  any(d == from_task for d in t.get("depends_on", []))]
            if found:
                filtered.append(stage)
        stages = filtered

    stage_results = {}  # track per-stage status

    for stage in stages:
        stage_id = stage["id"]
        print(f"\n{'='*50}")
        print(f"Stage {stage_id}: {stage.get('name','')}")
        print(f"{'='*50}")

        # Check stage-level depends_on
        should_skip = False
        stage_deps = stage.get("depends_on", [])
        for dep_id in stage_deps:
            if dep_id in stage_results and stage_results[dep_id] != "ok":
                print(f"  [SKIP] Stage depends on {dep_id} (status: {stage_results[dep_id]})")
                log.append({"stage": stage_id, "status": "skipped", "reason": f"depends_on {dep_id} not ok"})
                stage_results[stage_id] = "skipped"
                should_skip = True
        if should_skip:
            continue

        # Hook: on_stage_entry
        entry_result = execute_hooks(stage.get("hooks", {}), "on_stage_entry", context)
        if entry_result and entry_result.get("action") == "block":
            print(f"  [HOOK] Stage blocked: {entry_result['reason']}")
            log.append({"stage": stage_id, "status": "blocked", "reason": entry_result["reason"]})
            stage_results[stage_id] = "blocked"
            continue

        tasks = stage.get("tasks", [])

        # Handle sub_pipelines recursively
        for task in tasks:
            if "sub_pipeline" in task:
                print(f"  [{task['id']}] Sub-pipeline: {task['sub_pipeline'].get('description','')}")
                sub_log = run_pipeline(task["sub_pipeline"], registry, dry_run)
                log.append({
                    "task_id": task["id"],
                    "type": "sub_pipeline",
                    "sub_log": sub_log,
                    "status": "ok" if all(s.get("status") == "ok" for s in sub_log) else "partial",
                })

        # Filter out sub_pipeline tasks (already handled)
        executable_tasks = [t for t in tasks if "sub_pipeline" not in t]

        if not executable_tasks:
            continue

        rounds = build_execution_order(executable_tasks)

        for round_idx, round_tasks in enumerate(rounds):
            print(f"\n  Round {round_idx + 1}: {len(round_tasks)} task(s)")

            for task in round_tasks:
                cap_name = task.get("capability", "?")
                print(f"    [{task['id']}] {cap_name} ", end="", flush=True)

                result = execute_task(task, registry, dry_run, context)
                result["_stage_id"] = stage_id
                log.append(result)

                status = result.get("status", "?")
                if dry_run:
                    print(f"-> {status}")
                elif status == "ok":
                    print("OK")
                elif status == "failed":
                    print(f"FAIL (exit {result.get('exit_code','?')})")
                    # Hook: on_failure
                    hook_result = execute_hooks(task.get("hooks", {}) or
                                                stage.get("hooks", {}),
                                                "on_failure", {**context, "task": task})
                    if hook_result:
                        action = hook_result.get("action", "")
                        retries = hook_result.get("retries_left", 0)
                        if action == "retry" and retries > 0:
                            print(f"      [HOOK] Retrying ({retries} left)...")
                            task["hooks"] = task.get("hooks", {})
                            task["hooks"]["on_failure"] = {"retry": retries - 1, "fallback": "skip"}
                            retry_result = execute_task(task, registry, dry_run, context)
                            log.append(retry_result)
                        elif action == "skip":
                            print(f"      [HOOK] Skipping (fallback)")
                        else:
                            print(f"      [HOOK] Escalating: {action}")
                else:
                    print(f"→ {status}")

        # Hook: on_stage_complete
        execute_hooks(stage.get("hooks", {}), "on_stage_complete", context)

        # Track stage result for downstream depends_on
        stage_has_failures = any(
            e.get("status") in ("failed", "error", "timeout")
            for e in log if e.get("_stage_id") == stage_id
        )
        stage_results[stage_id] = "failed" if stage_has_failures else "ok"

    return log


# ═══════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════

def main():
    import argparse
    p = argparse.ArgumentParser(description="Pipeline Orchestration Engine")
    p.add_argument("plan", help="PipelinePlan JSON file")
    p.add_argument("--dry-run", action="store_true", help="Preview only, no execution")
    p.add_argument("--stage", help="Execute only this stage")
    p.add_argument("--from", dest="from_task", help="Resume from this task")
    args = p.parse_args()

    registry = load_registry()
    plan = load_plan(args.plan)

    # Validate
    errors = validate_plan(plan, registry)
    if errors:
        print("Validation errors:")
        for e in errors:
            print(f"  FAIL {e}")
        if not args.dry_run:
            sys.exit(1)

    print(f"Pipeline: {plan.get('pipeline','?')}")
    print(f"Description: {plan.get('description','')}")
    print(f"Stages: {len(plan.get('stages',[]))}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}\n")

    log = run_pipeline(
        plan, registry,
        dry_run=args.dry_run,
        target_stage=args.stage,
        from_task=args.from_task,
    )

    # Write execution log
    log_path = LOG_DIR / f"execution_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    log_path.write_text(json.dumps({
        "pipeline": plan.get("pipeline"),
        "executed_at": datetime.now().isoformat(),
        "dry_run": args.dry_run,
        "log": log,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nLog: {log_path}")

    # Summary
    ok = sum(1 for e in log if e.get("status") == "ok")
    fail = sum(1 for e in log if e.get("status") in ("failed", "error", "timeout"))
    dry = sum(1 for e in log if e.get("status") == "dry_run")
    ai = sum(1 for e in log if e.get("status") == "requires_ai")
    print(f"Summary: {ok} ok, {fail} failed, {ai} ai-handoff, {dry} dry-run")


if __name__ == "__main__":
    main()
