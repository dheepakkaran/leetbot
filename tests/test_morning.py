from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from src.log_store import read_log, write_log
from src.morning import morning_gate, read_hint, run_morning
from src.runtime import load_message_context
from src.stats import load_history
from tests.conftest import make_row, solution_json

TZ = ZoneInfo("America/New_York")


def cron_times(day: str) -> list[datetime]:
    """The morning.yml schedule: 12:17-16:17 UTC hourly."""
    y, m, d = map(int, day.split("-"))
    return [datetime(y, m, d, hour, 17, tzinfo=timezone.utc) for hour in range(12, 17)]


def runs_that_send(times: list[datetime]) -> list[int]:
    rows, passed = [], []
    for i, now in enumerate(times):
        ok, _ = morning_gate(now, TZ, 8, rows)
        if ok:
            passed.append(i)
            rows.append(make_row(1, now.date().isoformat()))  # the run that passes writes today's row
    return passed


@pytest.mark.parametrize("day, sending_cron", [("2026-07-15", 0), ("2026-01-15", 1)])  # EDT, EST
def test_exactly_one_cron_passes(day: str, sending_cron: int) -> None:
    assert runs_that_send(cron_times(day)) == [sending_cron]


@pytest.mark.parametrize("day", ["2026-07-15", "2026-01-15"])
def test_dropped_scheduled_runs_are_retried(day: str) -> None:
    times = cron_times(day)
    # GitHub drops the first two runs: the next hourly retry still sends, exactly once.
    assert runs_that_send(times[2:]) == [0]


def test_est_early_cron_is_too_early() -> None:
    ok, why = morning_gate(datetime(2026, 1, 15, 12, 17, tzinfo=timezone.utc), TZ, 8, [])
    assert not ok and "too early" in why


def test_existing_row_blocks_resend() -> None:
    now = datetime(2026, 7, 15, 13, 17, tzinfo=timezone.utc)
    ok, why = morning_gate(now, TZ, 8, [make_row(1, "2026-07-15")])
    assert not ok and "already issued" in why
    assert morning_gate(now, TZ, 8, [make_row(1, "2026-07-14")])[0]


def test_run_morning_gate_blocks_without_force(cfg, fakes, make_runtime) -> None:
    lc, _, tg = fakes
    write_log(cfg.log_path, [make_row(1, "2026-10-12")])
    rt = make_runtime(datetime(2026, 10, 12, 13, 17, tzinfo=timezone.utc))
    assert run_morning(rt) == 0
    assert tg.sent == [] and lc.calls == [] and rt.commits == []


def test_full_morning_flow(cfg, fakes, make_runtime) -> None:
    lc, llm, tg = fakes
    rt = make_runtime(datetime(2026, 10, 12, 12, 17, tzinfo=timezone.utc))  # Monday 08:17 EDT
    assert run_morning(rt) == 0

    [row] = read_log(cfg.log_path)
    assert (row.day, row.date, row.slug, row.source, row.language) == (1, "2026-10-12", "two-sum", "daily", "cpp")
    assert row.model == "gemini-3.8-flash"
    assert row.solution_path == "easy/0001-two-sum.md"
    assert row.message_id == "501" and row.sent_at == "2026-10-12T12:17:00Z"
    assert row.tags == "Array; Hash Table"
    assert rt.commits == ["chore: day 1 #1 two-sum", "chore: day 1 message id"]

    md = (cfg.root / row.solution_path).read_text()
    assert md.startswith("# 1. Two Sum\n")
    assert "SECRET-STATEMENT-TEXT" not in md  # statement never written to disk

    prompt = llm.prompts[0][1]["content"]
    assert "SECRET-STATEMENT-TEXT" in prompt and "class Solution {};" in prompt and "C++" in prompt

    [msg] = tg.sent
    lines = msg["text"].split("\n")
    assert "Day 1" in lines[0] and lines[1] == "Today: #1 Two Sum"
    assert "Solve in C++ (1/10)" in lines[2]
    assert "Yesterday" not in msg["text"]
    assert "Solved 67 · Easy 37 · Medium 30 · Hard 0" in msg["text"]
    assert [b["text"] for b in msg["buttons"][0]] == ["Open problem", "View solution"]
    assert msg["buttons"][0][1]["url"] == "https://github.com/owner/repo/blob/main/easy/0001-two-sum.md"

    ctx = load_message_context(cfg.messages_dir / "2026-10-12.json")
    assert ctx["message_id"] == 501 and ctx["variant"] == "normal"
    assert [s.total for s in load_history(cfg.stats_history_path)] == [67]
    assert "| 1 | 2026-10-12 |" in cfg.readme_path.read_text()


def test_dry_run_force_writes_nothing(cfg, fakes, make_runtime) -> None:
    lc, _, tg = fakes
    rt = make_runtime(datetime(2026, 10, 12, 3, 0, tzinfo=timezone.utc), dry_run=True, force=True)  # 23:00 local
    before = sorted(p.relative_to(cfg.root) for p in cfg.root.rglob("*") if ".dry-run" not in p.parts)
    assert run_morning(rt) == 0
    after = sorted(p.relative_to(cfg.root) for p in cfg.root.rglob("*") if ".dry-run" not in p.parts)
    assert before == after
    assert read_log(cfg.log_path) == []
    assert len(tg.sent) == 1  # the fake records the would-be message
    assert (cfg.root / ".dry-run" / "easy" / "0001-two-sum.md").exists()


def test_llm_failure_sends_no_solution_variant(cfg, fakes, make_runtime) -> None:
    lc, llm, tg = fakes
    llm.result = None
    rt = make_runtime(datetime(2026, 10, 12, 12, 17, tzinfo=timezone.utc))
    run_morning(rt)
    [row] = read_log(cfg.log_path)
    assert row.model == "none" and row.solution_path == ""
    assert "Solution unavailable today. Rerun from Actions." in tg.sent[0]["text"]
    assert load_message_context(cfg.messages_dir / "2026-10-12.json")["variant"] == "no_solution"

    # Rerun (no --force): retries the LLM for the same row and edits the message.
    llm.result = solution_json()
    rt2 = make_runtime(datetime(2026, 10, 12, 13, 17, tzinfo=timezone.utc))
    run_morning(rt2)
    [row] = read_log(cfg.log_path)
    assert row.model != "none" and row.solution_path == "easy/0001-two-sum.md"
    [edit] = tg.edits
    assert edit["message_id"] == 501 and "View solution" in str(edit["buttons"])
    assert len(tg.sent) == 1  # no second message


def test_unsent_row_is_resumed_not_duplicated(cfg, fakes, make_runtime) -> None:
    lc, llm, tg = fakes
    md_path = cfg.root / "easy" / "0001-two-sum.md"
    md_path.parent.mkdir(parents=True)
    md_path.write_text("# 1. Two Sum\n\n## Hint\nresume hint\n\n## Optimal: X\n", encoding="utf-8")
    write_log(cfg.log_path, [make_row(1, "2026-10-12", slug="two-sum", frontend_id="1", title="Two Sum",
                                      solution_path="easy/0001-two-sum.md", message_id="", sent_at="")])
    rt = make_runtime(datetime(2026, 10, 12, 13, 17, tzinfo=timezone.utc))
    run_morning(rt)
    [row] = read_log(cfg.log_path)
    assert row.message_id == "501"
    assert llm.prompts == []  # existing solution re-used
    assert "resume hint" in tg.sent[0]["text"]


def test_picker_used_when_daily_already_logged(cfg, fakes, make_runtime) -> None:
    lc, _, tg = fakes
    write_log(cfg.log_path, [make_row(1, "2026-10-11", slug="two-sum", solved=True, solved_at="2026-10-11T13:00:00Z")])
    rt = make_runtime(datetime(2026, 10, 12, 12, 17, tzinfo=timezone.utc))  # Monday -> Easy
    run_morning(rt)
    rows = read_log(cfg.log_path)
    assert rows[1].source == "picker" and rows[1].difficulty == "Easy" and rows[1].slug != "two-sum"
    assert "✅ Yesterday: #101 solved" in tg.sent[0]["text"]
    assert (cfg.root / "data" / "problems.json").exists()


def test_read_hint() -> None:
    assert read_hint("# T\n\n## Hint\nline one\n\n## Brute force\nx") == "line one"
    assert read_hint("no hint here") == ""
