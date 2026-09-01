"""Pre-deploy validation script.

Run before deploying to ensure the project is in a deployable state.
Usage: python scripts/deploy_check.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ERRORS: list[str] = []


def run(cmd: list[str], cwd: Path | None = None, timeout: int = 120) -> bool:
    """Run a command and return True if it succeeds."""
    try:
        result = subprocess.run(
            cmd, cwd=cwd or ROOT, capture_output=True, text=True, timeout=timeout,
            shell=(sys.platform == "win32"),
        )
        if result.returncode != 0:
            print(f"  FAIL: {' '.join(cmd)}")
            if result.stderr:
                print(f"  stderr: {result.stderr[:500]}")
            return False
        return True
    except subprocess.TimeoutExpired:
        print(f"  TIMEOUT: {' '.join(cmd)}")
        return False
    except FileNotFoundError:
        print(f"  NOT FOUND: {cmd[0]}")
        return False


def check(name: str, cmd: list[str], cwd: Path | None = None, timeout: int = 120) -> None:
    """Run a check and record failures."""
    print(f"[ ] {name}")
    if run(cmd, cwd, timeout=timeout):
        print(f"[x] {name}")
    else:
        ERRORS.append(name)
        print(f"[!] {name} FAILED")


def main() -> None:
    print("=" * 60)
    print("Sentinel Pre-Deploy Checklist")
    print("=" * 60)
    print()

    # Backend checks
    print("--- Backend ---")
    check("ruff lint", ["python", "-m", "ruff", "check", "src", "tests"])
    check("ruff format", ["python", "-m", "ruff", "format", "--check", "src", "tests"])
    check("pytest", ["python", "-m", "pytest", "tests", "-q"], timeout=180)
    print()

    # Frontend checks
    frontend = ROOT / "frontend"
    print("--- Frontend ---")
    check("npm ci", ["npm", "ci"], cwd=frontend)
    check("npm run build", ["npm", "run", "build"], cwd=frontend)
    check("npm run test", ["npm", "run", "test"], cwd=frontend)
    print()

    # Security checks
    print("--- Security ---")
    env_file = ROOT / ".env"
    if env_file.exists():
        ERRORS.append(".env file exists in repo")
        print("[!] .env file exists — must not be committed")
    else:
        print("[x] No .env file in repo")
    print()

    # Summary
    print("=" * 60)
    if ERRORS:
        print(f"FAILED: {len(ERRORS)} check(s):")
        for e in ERRORS:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("ALL CHECKS PASSED — safe to deploy")
        sys.exit(0)


if __name__ == "__main__":
    main()
