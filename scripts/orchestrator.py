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

import json, os, re, sys, subprocess, time, traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
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
    """Validate PipelinePlan: schema, uniqueness, circular deps, capabilities."""
    errors = []
    caps = registry.get("capabilities", {})

    # Schema
    if not plan.get("pipeline"):
        errors.append("Missing required field: pipeline")
    if not plan.get("stages"):
        errors.append("Missing required field: stages")
        return errors

    # Collect all task ids for uniqueness + dependency graph
    task_ids = set()
    dep_graph: dict[str, set[str]] = {}

    def _collect(stage, path=""):
        stage_id = stage.get("id", "")
        if not stage_id:
            errors.append(f"{path}: Stage missing 'id'")
        if not stage.get("tasks"):
            errors.append(f"{stage_id}: Stage has no tasks")

        for task in stage.get("tasks", []):
            tid = task.get("id", "")
            cap = task.get("capability", "")
            p = f"{stage_id}/{tid}"

            if not tid:
                errors.append(f"{stage_id}: Task missing 'id'")
                continue
            if not cap:
                errors.append(f"{p}: Task missing 'capability'")
                continue

            # Uniqueness
            if tid in task_ids:
                errors.append(f"{p}: Duplicate task id '{tid}'")
            task_ids.add(tid)

            # Capability
            if cap not in caps:
                errors.append(f"{p}: Capability '{cap}' not in registry")

            # Register dependencies (resolved after full collection)
            deps = set(task.get("depends_on", []))
            dep_graph[tid] = deps

            # Sub-pipeline
            if "sub_pipeline" in task:
                for sub_stage in task["sub_pipeline"].get("stages", []):
                    _collect(sub_stage, p)

        # Stage dependencies
        for sdep in stage.get("depends_on", []):
            pass  # validated separately

    for stage in plan["stages"]:
        _collect(stage)

    # Check all dependency references
    for tid, deps in dep_graph.items():
        for dep in deps:
            if dep not in task_ids:
                errors.append(f"Task '{tid}' depends on unknown task '{dep}'")

    # Circular dependency check via DFS
    UNVISITED, VISITING, VISITED = 0, 1, 2
    state = {tid: UNVISITED for tid in task_ids}

    def _has_cycle(tid: str) -> bool:
        state[tid] = VISITING
        for dep in dep_graph.get(tid, set()):
            if state.get(dep) == VISITING:
                errors.append(f"Circular dependency: {tid} -> {dep}")
                return True
            if state.get(dep) == UNVISITED:
                if _has_cycle(dep):
                    return True
        state[tid] = VISITED
        return False

    for tid in list(task_ids):
        if state.get(tid) == UNVISITED:
            _has_cycle(tid)

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
#  Context Pipe — task-to-task data flow
# ═══════════════════════════════════════════════════════════

def resolve_references(value: Any, context: dict) -> Any:
    """Recursively resolve $TASK_ID.output.field references in any value.

    Example: "$S1T1.output.html_path" → context["S1T1"]["output"]["html_path"]
    """
    if isinstance(value, str):
        return _resolve_str(value, context)
    elif isinstance(value, dict):
        return {k: resolve_references(v, context) for k, v in value.items()}
    elif isinstance(value, list):
        return [resolve_references(v, context) for v in value]
    return value


def _resolve_str(text: str, context: dict) -> Any:
    """Resolve $refs in a string. If the entire string is a single ref, return
    the actual value (preserving type). Otherwise do string interpolation."""
    pattern = re.compile(r'\$(\w+)\.(\w+)(?:\.(\w+))?')

    # Single ref covering the whole string
    m = pattern.fullmatch(text.strip())
    if m:
        task_id = m.group(1)
        namespace = m.group(2)  # "output" or "input"
        field = m.group(3)
        if task_id in context and namespace in context[task_id]:
            data = context[task_id][namespace]
            if field and isinstance(data, dict):
                return data.get(field, text)
            return data
        return text  # unresolved — keep as-is

    # Multiple refs — string interpolation
    def replacer(m):
        task_id = m.group(1)
        namespace = m.group(2)
        field = m.group(3)
        if task_id in context and namespace in context[task_id]:
            data = context[task_id][namespace]
            if field and isinstance(data, dict):
                return str(data.get(field, m.group(0)))
            return str(data)
        return m.group(0)

    return pattern.sub(replacer, text)


def register_output(task_id: str, result: dict, context: dict):
    """Register a task's output in the shared context for downstream references."""
    output = {
        "status": result.get("status"),
        "exit_code": result.get("exit_code"),
        "stdout": result.get("stdout", "")[-500:] if result.get("stdout") else "",
    }
    # For review agent: extract passed/failures from structured output
    stdout = result.get("stdout", "")
    if "passed: true" in stdout.lower() or "passed:false" in stdout.lower():
        passed_match = re.search(r'passed:\s*(true|false)', stdout)
        if passed_match:
            output["passed"] = passed_match.group(1) == "true"
        failures = re.findall(r'H\d\s+(FAIL|PASS)', stdout)
        output["hard_checks"] = failures
    # For cover agent: extract cover_path
    cover_match = re.search(r'cover_path:\s*(\S+)', stdout)
    if cover_match:
        output["cover_path"] = cover_match.group(1)
    context.setdefault(task_id, {})
    context[task_id]["output"] = output


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
        # Build CLI args from task input — only pass keys that exist in capability params
        known_params = cap.get("params", {})
        for key, val in (task_input or {}).items():
            if key.startswith("_"):
                continue
            if key not in known_params and known_params:
                continue  # skip unknown params to avoid CLI errors
            arg_key = f"--{key.replace('_', '-')}"
            if isinstance(val, bool):
                if val:
                    parts.append(arg_key)
            elif isinstance(val, list):
                parts.append(arg_key)
                parts.append(",".join(str(v) for v in val))
            elif val is not None and not isinstance(val, dict):
                parts.append(arg_key)
                parts.append(str(val))
        return " ".join(parts)

    return None  # agent / skill


def execute_task(task: dict, registry: dict, dry_run: bool = False,
                 context: dict = None, resume_handoffs: dict = None) -> dict:
    """Execute a single task. Returns result dict.

    resume_handoffs: dict of task_id -> pre-completed result (for --resume mode)
    """
    cap_name = task.get("capability", "")
    cap = registry["capabilities"].get(cap_name, {})
    cap_type = cap.get("type", "unknown")

    # Check if this task was already completed via handoff
    if resume_handoffs and task["id"] in resume_handoffs:
        ho = resume_handoffs[task["id"]]
        ho["task_id"] = task["id"]
        ho["capability"] = cap_name
        ho["type"] = cap_type
        ho["status"] = ho.get("status", "ok")
        return ho

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
        if dry_run:
            result["status"] = "dry_run"
        else:
            # Write handoff file for AI to pick up
            handoff = {
                "task_id": task["id"],
                "capability": cap_name,
                "type": cap_type,
                "file": cap.get("file", ""),
                "description": cap.get("description", ""),
                "input": task.get("input", {}),
                "context": context,
                "status": "pending"
            }
            handoff_dir = LOG_DIR / "handoffs"
            handoff_dir.mkdir(parents=True, exist_ok=True)
            handoff_path = handoff_dir / f"{task['id']}_{cap_name}.json"
            handoff_path.write_text(json.dumps(handoff, ensure_ascii=False, indent=2), encoding="utf-8")
            result["status"] = "pending_ai"
            result["handoff_file"] = str(handoff_path)
            result["note"] = f"Handoff written: {handoff_path}"
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
                 target_stage: str = None, from_task: str = None,
                 resume_handoffs: dict = None) -> list[dict]:
    """Execute pipeline plan stage by stage.

    resume_handoffs: dict mapping task_id -> pre-completed result (from --resume)
    """
    if resume_handoffs is None:
        resume_handoffs = {}
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

            use_parallel = stage.get("parallel", False) and len(round_tasks) > 1 and not dry_run

            if use_parallel:
                def _run_parallel(task):
                    if task.get("input"):
                        task["input"] = resolve_references(task["input"], context)
                    result = execute_task(task, registry, dry_run, context, resume_handoffs)
                    result["_stage_id"] = stage_id
                    register_output(task["id"], result, context)
                    return result

                with ThreadPoolExecutor(max_workers=min(len(round_tasks), 4)) as executor:
                    futures = {executor.submit(_run_parallel, t): t for t in round_tasks}
                    for future in as_completed(futures):
                        task = futures[future]
                        result = future.result()
                        log.append(result)
                        cap_name = task.get("capability", "?")
                        status = result.get("status", "?")
                        status_str = "OK" if status in ("ok", "pending_ai") else status
                        print(f"    [{task['id']}] {cap_name} -> {status_str}")
                continue  # skip sequential loop below

            for task in round_tasks:
                cap_name = task.get("capability", "?")
                print(f"    [{task['id']}] {cap_name} ", end="", flush=True)

                if task.get("input"):
                    task["input"] = resolve_references(task["input"], context)

                result = execute_task(task, registry, dry_run, context, resume_handoffs)
                result["_stage_id"] = stage_id
                register_output(task["id"], result, context)
                log.append(result)

                status = result.get("status", "?")
                if dry_run:
                    print(f"-> {status}")
                elif status in ("ok", "pending_ai"):
                    print("OK" if status == "ok" else "-> handoff")
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
    p.add_argument("--resume", help="Load completed handoffs from directory")
    args = p.parse_args()

    # Load resume handoffs if provided
    resume_handoffs = {}
    if args.resume:
        handoff_dir = Path(args.resume)
        if handoff_dir.exists():
            for hf in handoff_dir.glob("*.json"):
                try:
                    ho = json.loads(hf.read_text(encoding="utf-8"))
                    if ho.get("status") == "completed":
                        resume_handoffs[ho["task_id"]] = ho.get("result", {})
                        ho["_resume_source"] = str(hf)
                except Exception:
                    pass
            print(f"Resume: loaded {len(resume_handoffs)} completed handoff(s)")

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
        resume_handoffs=resume_handoffs,
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
