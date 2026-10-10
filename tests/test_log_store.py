import os
from pathlib import Path

import pytest

from src import log_store
from src.log_store import COLUMNS, latest_row_for_date, read_log, write_log
from tests.conftest import make_row

HEADER = "day,date,frontend_id,title,slug,difficulty,tags,source,language,model,solution_path,sent_at,message_id,solved,solved_at,late,submission_id,nudge_sent"


def test_columns_in_spec_order() -> None:
    assert ",".join(COLUMNS) == HEADER


def test_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "log.csv"
    rows = [
        make_row(1, "2026-10-11", title='Commas, "quotes" & stuff', tags="Array; Hash Table", solved=True,
                 solved_at="2026-10-11T13:00:00Z", submission_id="55", late=False, nudge_sent=True),
        make_row(2, "2026-10-12", model="none", solution_path="", message_id=""),
    ]
    write_log(path, rows)
    assert path.read_text().splitlines()[0] == HEADER
    assert read_log(path) == rows
    assert read_log(path)[0].tag_list == ["Array", "Hash Table"]
    assert "true" in path.read_text() and "false" in path.read_text()
    assert latest_row_for_date(rows, "2026-10-12").day == 2
    assert latest_row_for_date(rows, "2026-10-13") is None
    assert not rows[1].has_solution and rows[0].has_solution


def test_missing_file_is_empty(tmp_path: Path) -> None:
    assert read_log(tmp_path / "nope.csv") == []


def test_atomic_write_keeps_old_file_on_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "log.csv"
    write_log(path, [make_row(1, "2026-10-11")])
    before = path.read_text()

    def boom(src, dst):  # noqa: ANN001
        raise OSError("disk full")

    monkeypatch.setattr(log_store.os, "replace", boom)
    with pytest.raises(OSError):
        write_log(path, [make_row(1, "2026-10-11"), make_row(2, "2026-10-12")])
    assert path.read_text() == before
    assert [p.name for p in tmp_path.iterdir()] == ["log.csv"]  # temp file cleaned up


def test_atomic_write_uses_rename(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = []
    real = os.replace
    monkeypatch.setattr(log_store.os, "replace", lambda a, b: calls.append((a, b)) or real(a, b))
    path = tmp_path / "log.csv"
    write_log(path, [make_row(1, "2026-10-11")])
    [(src, dst)] = calls
    assert Path(dst) == path and Path(src).parent == tmp_path and Path(src) != path
