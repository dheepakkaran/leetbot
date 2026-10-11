from datetime import datetime, timezone

from src.leetcode_client import AcSubmission, Submission
from src.log_store import read_log, write_log
from src.preview import sample_context
from src.runtime import load_message_context, save_message_context
from src.sync import match_submissions, run_sync
from tests.conftest import make_row


def ts(s: str) -> int:
    return int(datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp())


def ac(slug: str, when: str, sid: str = "777") -> AcSubmission:
    return AcSubmission(id=sid, title=slug, slug=slug, timestamp=ts(when))


def test_ac_older_than_sent_at_is_ignored() -> None:
    row = make_row(1, "2026-10-12", slug="two-sum", sent_at="2026-10-12T12:20:00Z")
    assert match_submissions([row], [ac("two-sum", "2026-03-01T10:00:00Z")]) == []
    assert match_submissions([row], [ac("two-sum", "2026-10-12T12:19:59Z")]) == []
    matches = match_submissions([row], [ac("two-sum", "2026-10-12T12:20:00Z")])
    assert len(matches) == 1


def test_earliest_qualifying_ac_wins_and_slug_must_match() -> None:
    row = make_row(1, "2026-10-12", slug="two-sum", sent_at="2026-10-12T12:20:00Z")
    acs = [
        ac("two-sum", "2026-10-12T20:00:00Z", "3"),
        ac("other", "2026-10-12T13:00:00Z", "9"),
        ac("two-sum", "2026-10-12T14:00:00Z", "2"),
    ]
    [(_, best)] = match_submissions([row], acs)
    assert best.id == "2"


def _setup(cfg, rows, *, with_ctx: bool = True) -> None:
    write_log(cfg.log_path, rows)
    if with_ctx:
        for r in rows:
            c = sample_context(cfg.github_repository)
            c.update(date=r.date, day=r.day, message_id=int(r.message_id), sent_at=r.sent_at)
            save_message_context(cfg.messages_dir / f"{r.date}.json", c)


def test_sync_marks_solved_edits_and_reacts(cfg, fakes, make_runtime) -> None:
    lc, _, tg = fakes
    _setup(cfg, [make_row(1, "2026-10-12", slug="two-sum")])
    lc.acs = [ac("two-sum", "2026-10-12T13:00:00Z", "4242")]
    lc.subs = [Submission("two-sum", ts("2026-10-12T13:00:00Z"), "Accepted", "python3")]
    rt = make_runtime(datetime(2026, 10, 12, 14, 7, tzinfo=timezone.utc))
    run_sync(rt)

    [row] = read_log(cfg.log_path)
    assert row.solved and not row.late
    assert row.solved_at == "2026-10-12T13:00:00Z"
    assert row.submission_id == "4242"
    [edit] = tg.edits
    assert edit["message_id"] == 1001
    assert "<tg-spoiler>" not in edit["text"] and "Solved at 9:00 AM · 40 min after alert" in edit["text"]
    assert tg.reactions == [(1001, "💯")]
    assert rt.commits == ["chore: sync solved #101"]
    assert load_message_context(cfg.messages_dir / "2026-10-12.json")["actual_language"] == "python3"


def test_late_solve_sets_late(cfg, fakes, make_runtime) -> None:
    lc, _, tg = fakes
    _setup(cfg, [make_row(1, "2026-10-12", slug="two-sum")])
    lc.acs = [ac("two-sum", "2026-10-13T00:30:00Z")]
    run_sync(make_runtime(datetime(2026, 10, 13, 2, 7, tzinfo=timezone.utc)))
    [row] = read_log(cfg.log_path)
    assert row.solved and row.late
    assert "Solved late · Oct 12" in tg.edits[0]["text"]  # 00:30Z Oct 13 = 8:30 PM EDT Oct 12


def test_no_change_no_commit(cfg, fakes, make_runtime) -> None:
    lc, _, tg = fakes
    _setup(cfg, [make_row(1, "2026-10-12", slug="two-sum")])
    lc.acs = [ac("two-sum", "2026-01-01T00:00:00Z")]
    rt = make_runtime(datetime(2026, 10, 12, 14, 7, tzinfo=timezone.utc))
    run_sync(rt)
    assert rt.commits == [] and tg.edits == []
    assert not read_log(cfg.log_path)[0].solved


def test_rows_without_message_id_are_skipped(cfg, fakes, make_runtime) -> None:
    lc, _, tg = fakes
    _setup(cfg, [make_row(1, "2026-10-12", slug="two-sum", message_id="")], with_ctx=False)
    lc.acs = [ac("two-sum", "2026-10-12T13:00:00Z")]
    run_sync(make_runtime(datetime(2026, 10, 12, 14, 7, tzinfo=timezone.utc)))
    assert "recent_ac" not in lc.calls and tg.edits == []


def test_dry_run_writes_nothing(cfg, fakes, make_runtime) -> None:
    lc, _, _ = fakes
    _setup(cfg, [make_row(1, "2026-10-12", slug="two-sum")])
    before = cfg.log_path.read_text()
    lc.acs = [ac("two-sum", "2026-10-12T13:00:00Z")]
    rt = make_runtime(datetime(2026, 10, 12, 14, 7, tzinfo=timezone.utc), dry_run=True)
    rows = run_sync(rt)
    assert rows[0].solved  # in-memory state is fresh
    assert cfg.log_path.read_text() == before
