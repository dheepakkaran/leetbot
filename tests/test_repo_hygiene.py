"""Repo hygiene: required files, no secrets, no hardcoded username."""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", ".venv", ".dry-run", "__pycache__", ".pytest_cache"}
TOKEN_RE = re.compile(r"ghp_[A-Za-z0-9]{20,}|gho_[A-Za-z0-9]{20,}|github_pat_\w{20,}|\b\d{8,10}:[A-Za-z0-9_-]{35}\b")


def test_required_files_exist_and_env_is_ignored() -> None:
    for name in ("README.md", "DECISIONS.md", ".env.example", ".gitignore", "config.yaml", "log.csv", "requirements.txt"):
        assert (REPO / name).is_file(), name
    assert ".env" in (REPO / ".gitignore").read_text().splitlines()
    example = (REPO / ".env.example").read_text()
    for key in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "GEMINI_API_KEY", "LEETCODE_USERNAME"):
        assert f"{key}=\n" in example  # names only, no values
    for d in ("easy", "medium", "hard"):
        assert (REPO / d / ".gitkeep").exists()


def test_username_is_not_hardcoded_in_code() -> None:
    for path in list((REPO / "src").glob("*.py")) + list((REPO / "scripts").glob("*.py")):
        assert "___ka__ran___" not in path.read_text(), path


def test_no_secrets_in_repo_files() -> None:
    for path in REPO.rglob("*"):
        rel = path.relative_to(REPO)
        if not path.is_file() or SKIP_DIRS & set(rel.parts) or path.name == ".env":
            continue
        assert not TOKEN_RE.search(path.read_text(encoding="utf-8", errors="ignore")), rel
