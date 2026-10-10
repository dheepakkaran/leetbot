"""Commit + push with `pull --rebase` retries."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Callable

PUSH_TRIES = 3

Runner = Callable[..., subprocess.CompletedProcess]


class GitError(RuntimeError):
    """A git command failed in a way retries can't fix."""


def _git(run: Runner, cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    proc = run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise GitError(f"git {' '.join(args)} failed: {(proc.stderr or proc.stdout).strip()}")
    return proc


def commit_and_push(message: str, cwd: Path, run: Runner = subprocess.run, log: Callable[[str], None] = print) -> bool:
    """Stage everything, commit and push. Returns False if nothing was staged.

    On a rejected push, `git pull --rebase` and retry, up to 3 tries.
    """
    _git(run, cwd, "add", "-A")
    if _git(run, cwd, "diff", "--cached", "--quiet", check=False).returncode == 0:
        log(f"[git] nothing to commit for: {message}")
        return False
    _git(run, cwd, "commit", "-m", message)
    for attempt in range(1, PUSH_TRIES + 1):
        push = _git(run, cwd, "push", check=False)
        if push.returncode == 0:
            log(f"[git] pushed: {message}")
            return True
        log(f"[git] push rejected (try {attempt}/{PUSH_TRIES}): {push.stderr.strip()}")
        if attempt == PUSH_TRIES:
            break
        rebase = _git(run, cwd, "pull", "--rebase", check=False)
        if rebase.returncode != 0:
            _git(run, cwd, "rebase", "--abort", check=False)
            raise GitError(f"git pull --rebase failed: {rebase.stderr.strip()}")
    raise GitError(f"git push failed after {PUSH_TRIES} tries")
