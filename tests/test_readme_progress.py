from datetime import date
from pathlib import Path

from src.readme_progress import END, START, render_progress, update_readme
from tests.conftest import make_row


def test_empty_log_placeholder() -> None:
    block = render_progress([], 0, date(2026, 10, 13))
    assert block.startswith(START) and block.endswith(END) and "No problems issued yet" in block


def test_readme_progress_block(tmp_path: Path) -> None:
    rows = [
        make_row(1, "2026-10-10", difficulty="Easy", solved=True),
        make_row(2, "2026-10-11", difficulty="Medium", solved=True, late=True),
        make_row(3, "2026-10-12", difficulty="Hard", title="A | B"),
        make_row(4, "2026-10-13", difficulty="Medium", language="python"),
    ]
    block = render_progress(rows, 3, date(2026, 10, 13))
    assert block.startswith(START) and block.endswith(END)
    assert "**Bot days:** 4" in block and "**Solved:** 2/4 (50%)" in block
    assert "Easy 1/1 · Medium 1/2 · Hard 0/1" in block and "3 days" in block
    assert "✅ Solved late" in block and "❌ Missed" in block and "⏳ Pending" in block
    assert "A \\| B" in block and "| Python |" in block

    readme = tmp_path / "README.md"
    readme.write_text(f"# X\n\n{START}\nold\n{END}\n\nfooter\n")
    assert update_readme(readme, rows, 3, date(2026, 10, 13))
    text = readme.read_text()
    assert "old" not in text and "footer" in text and text.count(START) == 1
    assert not update_readme(readme, rows, 3, date(2026, 10, 13))  # idempotent


def test_block_appended_when_markers_missing(tmp_path: Path) -> None:
    readme = tmp_path / "README.md"
    readme.write_text("# X\n")
    assert update_readme(readme, [make_row(1, "2026-10-10")], 0, date(2026, 10, 10))
    assert readme.read_text().count(START) == 1
