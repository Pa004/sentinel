"""Git integration: locate the commit that introduced a file or violation."""

from __future__ import annotations

import re
from pathlib import Path
from subprocess import run

_SOURCE_PATH_RE = re.compile(
    r"([A-Za-z]:[\\/][^\s]*\.(?:ts|tsx|js|jsx|py|java|cs)|/[^\s]*\.(?:ts|tsx|js|jsx|py|java|cs))",
    re.IGNORECASE,
)


def is_git_repo(path: Path) -> bool:
    return find_git_root(path) is not None


def find_git_root(path: Path) -> Path | None:
    """Walk up from `path` looking for a `.git` directory or file."""
    current = path.resolve()
    if current.is_file():
        current = current.parent
    while True:
        if (current / ".git").exists():
            return current
        if current.parent == current:
            return None
        current = current.parent


def head_commit_sha(git_root: Path) -> str | None:
    """SHA of the HEAD commit in the repository."""
    proc = run(
        ["git", "-C", str(git_root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return None
    sha = proc.stdout.strip()
    return sha or None


def last_commit_sha(git_root: Path, relative_path: Path) -> str | None:
    """SHA of the most recent commit touching the file under `git_root`."""
    proc = run(
        ["git", "-C", str(git_root), "log", "-1", "--format=%H", "--", relative_path.as_posix()],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return None
    sha = proc.stdout.strip()
    return sha or None


def source_path_from_evidence(evidence: str) -> Path | None:
    """Extract the first source file path embedded in a violation evidence."""
    match = _SOURCE_PATH_RE.search(evidence)
    if match is None:
        return None
    return Path(match.group(1))
