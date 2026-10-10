import subprocess
from pathlib import Path

import pytest

from src.git_ops import GitError, commit_and_push


class FakeGit:
    """Records git invocations and returns scripted exit codes per subcommand."""

    def __init__(self, codes: dict[str, list[int]]) -> None:
        self.codes = codes
        self.calls: list[list[str]] = []

    def __call__(self, args: list[str], cwd: Path, capture_output: bool, text: bool) -> subprocess.CompletedProcess:
        self.calls.append(args[1:])
        key = " ".join(args[1:3]) if args[1] in ("diff", "pull") else args[1]
        queue = self.codes.get(key, [])
        code = queue.pop(0) if queue else 0
        return subprocess.CompletedProcess(args, code, stdout="", stderr="rejected" if code else "")


def test_nothing_staged_means_no_commit(tmp_path: Path) -> None:
    git = FakeGit({"diff --cached": [0]})
    assert commit_and_push("chore: x", tmp_path, run=git, log=lambda m: None) is False
    assert git.calls == [["add", "-A"], ["diff", "--cached", "--quiet"]]


def test_commit_and_push(tmp_path: Path) -> None:
    git = FakeGit({"diff --cached": [1]})
    assert commit_and_push("chore: x", tmp_path, run=git, log=lambda m: None) is True
    assert git.calls[2] == ["commit", "-m", "chore: x"]
    assert git.calls[3] == ["push"]


def test_rejected_push_rebases_and_retries(tmp_path: Path) -> None:
    git = FakeGit({"diff --cached": [1], "push": [1, 1, 0]})
    assert commit_and_push("chore: x", tmp_path, run=git, log=lambda m: None) is True
    assert [c[0] for c in git.calls[3:]] == ["push", "pull", "push", "pull", "push"]
    assert ["pull", "--rebase"] in git.calls


def test_gives_up_after_three_tries(tmp_path: Path) -> None:
    git = FakeGit({"diff --cached": [1], "push": [1, 1, 1]})
    with pytest.raises(GitError, match="after 3 tries"):
        commit_and_push("chore: x", tmp_path, run=git, log=lambda m: None)
    assert sum(1 for c in git.calls if c[0] == "push") == 3


def test_failed_rebase_aborts(tmp_path: Path) -> None:
    git = FakeGit({"diff --cached": [1], "push": [1], "pull --rebase": [1]})
    with pytest.raises(GitError, match="pull --rebase failed"):
        commit_and_push("chore: x", tmp_path, run=git, log=lambda m: None)
    assert git.calls[-1] == ["rebase", "--abort"]
