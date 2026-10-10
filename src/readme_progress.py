"""Auto-updated progress block in README.md."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from src.languages import LANGUAGES
from src.log_store import LogRow

START = "<!-- PROGRESS:START -->"
END = "<!-- PROGRESS:END -->"
_BLOCK_RE = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)


def _status(row: LogRow, today: date) -> str:
    if row.solved:
        return "✅ Solved late" if row.late else "✅ Solved"
    return "⏳ Pending" if row.date == today.isoformat() else "❌ Missed"


def render_progress(rows: list[LogRow], streak: int, today: date) -> str:
    """Markdown for the progress block (markers included)."""
    total = len(rows)
    solved = sum(1 for r in rows if r.solved)
    rate = f"{100 * solved / total:.0f}%" if total else "—"
    lines = [START, "", "## Progress", ""]
    if not rows:
        lines += ["_No problems issued yet. The first one arrives with the next morning run._", "", END]
        return "\n".join(lines)
    lines += [
        f"- **Bot days:** {total}",
        f"- **Solved:** {solved}/{total} ({rate})",
    ]
    by_diff = []
    for diff in ("Easy", "Medium", "Hard"):
        issued = [r for r in rows if r.difficulty == diff]
        by_diff.append(f"{diff} {sum(1 for r in issued if r.solved)}/{len(issued)}")
    lines += [
        f"- **By difficulty:** {' · '.join(by_diff)}",
        f"- **Current LeetCode streak:** {streak} {'day' if streak == 1 else 'days'}",
        "",
        "| Day | Date | Problem | Difficulty | Language | Status |",
        "|---:|---|---|---|---|---|",
    ]
    for r in reversed(rows[-7:]):
        title = r.title.replace("|", "\\|")
        link = f"[#{r.frontend_id} {title}](https://leetcode.com/problems/{r.slug}/)"
        if r.solution_path:
            link += f" · [solution]({r.solution_path})"
        lang = LANGUAGES[r.language].display if r.language in LANGUAGES else r.language
        lines.append(f"| {r.day} | {r.date} | {link} | {r.difficulty} | {lang} | {_status(r, today)} |")
    lines += ["", END]
    return "\n".join(lines)


def update_readme(path: Path, rows: list[LogRow], streak: int, today: date) -> bool:
    """Replace the progress block in README.md. Returns True if the file changed."""
    text = path.read_text(encoding="utf-8")
    block = render_progress(rows, streak, today)
    if _BLOCK_RE.search(text):
        new = _BLOCK_RE.sub(lambda _: block, text, count=1)
    else:
        new = text.rstrip("\n") + "\n\n" + block + "\n"
    if new == text:
        return False
    path.write_text(new, encoding="utf-8")
    return True
