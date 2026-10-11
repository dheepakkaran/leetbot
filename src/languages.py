"""Language rotation: blocks of `block_size` days cycling through `cycle`."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Language:
    key: str            # config key and log value: cpp / python / java
    display: str        # C++ / Python / Java
    fence: str          # Markdown code fence language
    leetcode_slug: str  # LeetCode codeSnippets langSlug


LANGUAGES: dict[str, Language] = {
    "cpp": Language("cpp", "C++", "cpp", "cpp"),
    "python": Language("python", "Python", "python", "python3"),
    "java": Language("java", "Java", "java", "java"),
}


def language_for_day(day: int, block_size: int, cycle: list[str]) -> tuple[Language, int]:
    """Return (language, k) for 1-based bot day `day`, where k is 1..block_size."""
    if day < 1:
        raise ValueError("day is 1-based")
    block = ((day - 1) // block_size) % len(cycle)
    k = ((day - 1) % block_size) + 1
    return LANGUAGES[cycle[block]], k


def language_by_key(key: str) -> Language:
    """Look up a language by its config/log key."""
    return LANGUAGES[key]
