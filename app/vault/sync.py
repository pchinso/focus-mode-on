"""Best-effort git synchronization of the vault.

Git sync is optional: if the vault is not a git repository or git is
unavailable, every function degrades to a no-op so the app keeps working
against the local filesystem. This matches the spec requirement that manual
task operations keep working even when integrations are down.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def _git_available(base: Path) -> bool:
    """Return True if git exists and ``base`` is inside a work tree."""
    if shutil.which("git") is None:
        return False
    if not (base / ".git").exists():
        return False
    return True


def _run(base: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run a git command in ``base`` capturing output, never raising."""
    return subprocess.run(
        ["git", *args],
        cwd=str(base),
        capture_output=True,
        text=True,
        check=False,
    )


def pull(base: Path) -> None:
    """Pull the latest vault state if a remote is configured."""
    if not _git_available(base):
        return
    if _run(base, "remote").stdout.strip():
        _run(base, "pull", "--ff-only")


def commit(base: Path, message: str) -> bool:
    """Stage all changes and commit them.

    Args:
        base: Vault root directory.
        message: Commit message describing the mutation.

    Returns:
        True if a commit was created, False if git was unavailable or there
        was nothing to commit.
    """
    if not _git_available(base):
        return False
    _run(base, "add", "-A")
    result = _run(base, "commit", "-m", message)
    return result.returncode == 0


def push(base: Path) -> None:
    """Push commits to the default remote, if one exists."""
    if not _git_available(base):
        return
    if _run(base, "remote").stdout.strip():
        _run(base, "push")
