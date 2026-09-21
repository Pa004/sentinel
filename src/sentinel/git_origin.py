"""Git integration: locate the commit that introduced a file or violation."""

from __future__ import annotations

import re
from pathlib import Path
from subprocess import run

_SOURCE_PATH_RE = re.compile(
    r"([A-Za-z]:[\\/][^\s]*\.(?:ts|tsx|js|jsx|py|java|cs)|/[^\s]*\.(?:ts|tsx|js|jsx|py|java|cs))",
    re.IGNORECASE,
)

SOURCE_SUFFIXES = (".ts", ".tsx", ".js", ".jsx", ".py", ".java", ".cs")

_RELATIVE_TOKEN_RE = re.compile(
    r"(^|[\s\"'(])((?:\.?\./)?(?:[\w.\-]+/)+[\w.\-]+\.(?:ts|tsx|js|jsx|py|java|cs))",
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
    """Extract the first source file path embedded in a violation evidence.

    Matches absolute paths first, then relative paths containing a slash
    (e.g. `presentation/App.ts`, `./domain/db.ts`). Returns a relative
    `Path` when only a relative reference exists; callers resolve it
    against the repository root.
    """
    match = _SOURCE_PATH_RE.search(evidence)
    if match is None:
        match = _RELATIVE_TOKEN_RE.search(evidence)
        if match is None:
            return None
        return Path(match.group(2))
    return Path(match.group(1).rstrip(":;,)\"'"))


def resolve_source_path(
    evidence: str,
    components: tuple[str, ...] = (),
    git_root: Path | None = None,
) -> Path | None:
    """Best-effort absolute source path for a violation.

    Tries evidence first, then `components` (which reliably carry file
    paths for every rule). Relative candidates resolve against `git_root`.
    """
    candidates: list[Path] = []
    from_evidence = source_path_from_evidence(evidence)
    if from_evidence is not None:
        candidates.append(from_evidence)
    for component in components:
        candidate = Path(component)
        if candidate.suffix.lower() in SOURCE_SUFFIXES:
            candidates.append(candidate)
    for candidate in candidates:
        if candidate.is_absolute():
            return candidate
        if git_root is not None:
            return git_root / candidate
        return candidate
    return None
