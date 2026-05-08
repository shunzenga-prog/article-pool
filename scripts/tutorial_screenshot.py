#!/usr/bin/env python3
"""
Tutorial Screenshot Automation -- Run Python code, capture terminal output,
generate a styled terminal screenshot, and verify the output.

Usage:
  python scripts/tutorial_screenshot.py <script.py> --args "arg1 arg2" --output screenshot.png
  python scripts/tutorial_screenshot.py <script.py> --output screenshot.png --verify "expected text"
"""

import argparse, subprocess, sys, os, tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def run_script(script_path: str, args_str: str = "", timeout: int = 30) -> tuple[str, str, int]:
    """Run a Python script and capture stdout/stderr."""
    cmd = [sys.executable, script_path]
    if args_str:
        cmd.extend(args_str.split())

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=timeout,
            cwd=str(Path(script_path).parent),
            encoding="utf-8", errors="replace",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"}
        )
        return proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired:
        return "", f"TIMEOUT after {timeout}s", -1
    except Exception as e:
        return "", str(e), -1


def verify_output(stdout: str, stderr: str, verify_text: str) -> tuple[bool, str]:
    """Check if expected text appears in output."""
    combined = stdout + stderr
    if verify_text:
        if verify_text.lower() in combined.lower():
            return True, f"Verified: '{verify_text}' found in output"
        else:
            return False, f"NOT FOUND: '{verify_text}' not in output\nOutput: {combined[:300]}"
    return True, "No verification requested"


def generate_screenshot(text_content: str, output_path: str, title: str = "") -> str:
    """Generate a terminal screenshot from text content using terminal_screenshot.py."""
    # Write text to temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(text_content)
        temp_path = f.name

    try:
        ts_script = PROJECT_ROOT / "scripts" / "terminal_screenshot.py"
        cmd = [
            sys.executable, str(ts_script),
            temp_path,
            "--os", "windows",
            "--title", title or "PowerShell",
            "-o", output_path,
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60,
                             encoding="utf-8", errors="replace",
                             env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        if proc.returncode == 0 and os.path.exists(output_path):
            return output_path
        return ""
    finally:
        os.unlink(temp_path)


def main():
    p = argparse.ArgumentParser(description="Tutorial Screenshot Automation")
    p.add_argument("script", help="Python script to run")
    p.add_argument("--args", default="", help="Arguments to pass to the script")
    p.add_argument("--output", "-o", required=True, help="Output screenshot PNG path")
    p.add_argument("--verify", help="Text that must appear in output to pass verification")
    p.add_argument("--title", default="PowerShell", help="Terminal window title")
    p.add_argument("--timeout", type=int, default=30, help="Script execution timeout (s)")
    args = p.parse_args()

    if not os.path.exists(args.script):
        print(f"ERROR: Script not found: {args.script}")
        sys.exit(1)

    print(f"[Run] {args.script} {args.args}")
    stdout, stderr, exit_code = run_script(args.script, args.args, args.timeout)

    print(f"[Exit] code={exit_code}")
    if stderr and exit_code != 0:
        print(f"[Stderr] {stderr[:200]}")

    # Verify
    passed, verify_msg = verify_output(stdout, stderr, args.verify)
    print(f"[Verify] {verify_msg}")
    if not passed:
        print("WARNING: Verification failed, but generating screenshot anyway")
        print(f"[Stdout] {stdout[:500]}")

    # Generate screenshot
    text_content = stdout
    if stderr:
        text_content += f"\n\n[STDERR]\n{stderr}"

    result = generate_screenshot(text_content, args.output, args.title)
    if result:
        size_kb = os.path.getsize(result) / 1024
        print(f"[OK] Screenshot: {result} ({size_kb:.0f} KB)")
        print(f"TUTORIAL_SCREENSHOT_RESULT:")
        print(f"  output: {result}")
        print(f"  size_kb: {size_kb:.0f}")
        print(f"  exit_code: {exit_code}")
        print(f"  verified: {passed}")
    else:
        print("ERROR: Screenshot generation failed")
        print(f"[Raw output for manual use]:")
        print(text_content[:2000])
        sys.exit(1)


if __name__ == "__main__":
    main()
