from src.languages import LANGUAGES
from src.llm import normalize_solution
from src.solution_writer import render_solution, solution_path, solution_url
from tests.conftest import solution_json


def render(data):
    return render_solution(
        frontend_id="1", title="Two Sum", slug="two-sum", difficulty="Easy", tags=["Array", "Hash Table"],
        language=LANGUAGES["cpp"], day=3, date="2026-10-12", model="gemini-3.8-flash", solution=normalize_solution(data),
    )


def test_paths() -> None:
    assert solution_path("Medium", "42", "trapping-rain-water") == "medium/0042-trapping-rain-water.md"
    assert solution_path("Hard", "2333", "x") == "hard/2333-x.md"
    assert solution_url("o/r", "easy/0001-two-sum.md") == "https://github.com/o/r/blob/main/easy/0001-two-sum.md"


def test_template() -> None:
    md = render(solution_json())
    expected_head = (
        "# 1. Two Sum\n\n"
        "**Difficulty:** Easy · **Topics:** Array, Hash Table · **Language:** C++ · **Day:** 3 · **Date:** 2026-10-12\n\n"
        "🔗 [Open on LeetCode](https://leetcode.com/problems/two-sum/)\n\n"
        "> AI-generated with `gemini-3.8-flash`. Unverified. Check before trusting.\n\n"
        "## Hint\nThink about what you've already seen.\n\n"
        "## Brute force\nCheck every pair.\n\n**Time:** O(n^2) · **Space:** O(1)\n\n```cpp\nclass Solution {};\n```\n\n"
        "## Optimal: Hash Map\nStore complements.\n\n1. Walk the array\n2. Look up target - x\n\n"
        "**Time:** O(n) · **Space:** O(n)\n\n```cpp\n"
    )
    assert md.startswith(expected_head)
    assert "## Edge cases\n- Duplicates\n- Negative numbers\n\n## Dry run (example 1)\nnums=[2,7,11,15]" in md


def test_brute_force_omitted_when_null() -> None:
    md = render(solution_json() | {"brute_force": None})
    assert "## Brute force" not in md
    assert "## Optimal: Hash Map" in md
