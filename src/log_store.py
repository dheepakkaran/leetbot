"""`log.csv` read/write. The log is the single source of truth."""

from __future__ import annotations

import csv
import io
import os
import tempfile
from dataclasses import dataclass, fields
from pathlib import Path

COLUMNS = [
    "day", "date", "frontend_id", "title", "slug", "difficulty", "tags", "source",
    "language", "model", "solution_path", "sent_at", "message_id", "solved",
    "solved_at", "late", "submission_id", "nudge_sent",
]
BOOL_FIELDS = {"solved", "late", "nudge_sent"}
TAG_SEPARATOR = "; "


@dataclass
class LogRow:
    """One issued problem."""

    day: int
    date: str                 # UTC date issued, YYYY-MM-DD
    frontend_id: str
    title: str
    slug: str
    difficulty: str
    tags: str                 # topic names joined with "; "
    source: str               # daily | picker
    language: str             # cpp | python | java
    model: str                # model ID, or "none"
    solution_path: str = ""
    sent_at: str = ""         # ISO8601 UTC
    message_id: str = ""
    solved: bool = False
    solved_at: str = ""       # ISO8601 UTC
    late: bool = False
    submission_id: str = ""
    nudge_sent: bool = False

    @property
    def tag_list(self) -> list[str]:
        return [t for t in self.tags.split(TAG_SEPARATOR) if t] if self.tags else []

    @property
    def has_solution(self) -> bool:
        return self.model != "none" and bool(self.solution_path)

    def to_csv(self) -> dict[str, str]:
        out: dict[str, str] = {}
        for f in fields(self):
            value = getattr(self, f.name)
            out[f.name] = ("true" if value else "false") if f.name in BOOL_FIELDS else str(value)
        return out

    @classmethod
    def from_csv(cls, d: dict[str, str]) -> "LogRow":
        kwargs: dict[str, object] = {}
        for f in fields(cls):
            raw = (d.get(f.name) or "").strip()
            if f.name in BOOL_FIELDS:
                kwargs[f.name] = raw.lower() == "true"
            elif f.name == "day":
                kwargs[f.name] = int(raw)
            else:
                kwargs[f.name] = raw
        return cls(**kwargs)  # type: ignore[arg-type]


def join_tags(names: list[str]) -> str:
    """Join topic names for the `tags` column."""
    return TAG_SEPARATOR.join(names)


def read_log(path: Path) -> list[LogRow]:
    """Read all rows; a missing file means an empty log."""
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return [LogRow.from_csv(r) for r in csv.DictReader(fh)]


def write_log(path: Path, rows: list[LogRow]) -> None:
    """Write all rows atomically: temp file in the same directory, then rename."""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=COLUMNS, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow(row.to_csv())
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".log-", suffix=".csv.tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", newline="", encoding="utf-8") as fh:
            fh.write(buf.getvalue())
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def rows_for_date(rows: list[LogRow], utc_date: str) -> list[LogRow]:
    """All rows issued on a UTC date (normally zero or one)."""
    return [r for r in rows if r.date == utc_date]


def latest_row_for_date(rows: list[LogRow], utc_date: str) -> LogRow | None:
    """The last row issued on a UTC date, if any."""
    matching = rows_for_date(rows, utc_date)
    return matching[-1] if matching else None


def logged_slugs(rows: list[LogRow]) -> set[str]:
    """Slugs that were already issued."""
    return {r.slug for r in rows}
