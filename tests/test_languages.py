import pytest

from src.languages import language_for_day

CYCLE = ["cpp", "python", "java", "java", "python", "cpp"]


@pytest.mark.parametrize(
    "day, lang, k",
    [
        (1, "cpp", 1),
        (10, "cpp", 10),
        (11, "python", 1),
        (21, "java", 1),
        (31, "java", 1),
        (41, "python", 1),
        (51, "cpp", 1),
        (60, "cpp", 10),
        (61, "cpp", 1),   # cycle repeats
        (71, "python", 1),
    ],
)
def test_rotation(day: int, lang: str, k: int) -> None:
    language, got_k = language_for_day(day, 10, CYCLE)
    assert (language.key, got_k) == (lang, k)


def test_display_and_fence() -> None:
    cpp, _ = language_for_day(1, 10, CYCLE)
    py, _ = language_for_day(11, 10, CYCLE)
    java, _ = language_for_day(21, 10, CYCLE)
    assert (cpp.display, cpp.fence, cpp.leetcode_slug) == ("C++", "cpp", "cpp")
    assert (py.display, py.fence, py.leetcode_slug) == ("Python", "python", "python3")
    assert (java.display, java.fence, java.leetcode_slug) == ("Java", "java", "java")


def test_day_must_be_positive() -> None:
    with pytest.raises(ValueError):
        language_for_day(0, 10, CYCLE)
