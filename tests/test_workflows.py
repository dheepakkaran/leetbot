"""Structure checks for the GitHub Actions workflows (YAML parse; actionlint isn't required)."""

from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent
WORKFLOW_DIR = REPO / ".github" / "workflows"
WORKFLOWS = {
    "morning": ("src.morning", ["17 12 * * *", "17 13 * * *"]),
    "sync": ("src.sync", ["7 */2 * * *"]),
    "evening": ("src.evening", ["3 22 * * *", "3 23 * * *"]),
}


def load(name: str) -> dict:
    return yaml.safe_load((WORKFLOW_DIR / f"{name}.yml").read_text())


@pytest.mark.parametrize("name", WORKFLOWS)
def test_workflow_structure(name: str) -> None:
    module, crons = WORKFLOWS[name]
    wf = load(name)
    on = wf.get("on", wf.get(True))  # PyYAML parses a bare `on` key as True
    assert [s["cron"] for s in on["schedule"]] == crons
    inputs = on["workflow_dispatch"]["inputs"]
    assert inputs["dry_run"]["type"] == "boolean" and inputs["force"]["type"] == "boolean"
    assert wf["permissions"] == {"contents": "write"}
    assert wf["concurrency"] == {"group": "leetcode-bot", "cancel-in-progress": False}

    [job] = wf["jobs"].values()
    steps = job["steps"]
    assert steps[0]["uses"].startswith("actions/checkout@")
    setup = next(s for s in steps if s.get("uses", "").startswith("actions/setup-python@"))
    assert setup["with"] == {"python-version": "3.12", "cache": "pip"}
    assert any("pip install -r requirements.txt" in s.get("run", "") for s in steps)
    git = next(s for s in steps if "git config user.name" in s.get("run", ""))
    assert "github-actions[bot]" in git["run"]
    assert "41898282+github-actions[bot]@users.noreply.github.com" in git["run"]

    run = next(s for s in steps if f"python -m {module}" in s.get("run", ""))
    env = run["env"]
    assert env["GEMINI_API_KEY"] == "${{ secrets.GEMINI_API_KEY }}"
    assert "GITHUB_TOKEN" not in env  # GitHub Models is retired; git auth comes from checkout
    assert env["TELEGRAM_BOT_TOKEN"] == "${{ secrets.TELEGRAM_BOT_TOKEN }}"
    assert env["TELEGRAM_CHAT_ID"] == "${{ secrets.TELEGRAM_CHAT_ID }}"
    assert env["LEETCODE_USERNAME"] == "${{ vars.LEETCODE_USERNAME }}"
    assert "--dry-run" in run["run"] and "--force" in run["run"]

    alert = steps[-1]
    assert alert["if"] == "failure()"
    assert "curl" in alert["run"] and "Bot error" in alert["run"] and "RUN_URL" in alert["run"]


def test_ci_runs_tests_on_pull_requests() -> None:
    wf = load("ci")
    on = wf.get("on", wf.get(True))
    assert "pull_request" in on and on["push"]["branches"] == ["main"]
    assert wf["permissions"] == {"contents": "read"}
    steps = wf["jobs"]["test"]["steps"]
    assert any(s.get("run") == "pytest -q" for s in steps)
