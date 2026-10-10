"""Turn the LLM's JSON into a solution Markdown file."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.languages import Language


def solution_path(difficulty: str, frontend_id: str, slug: str) -> str:
    """Repo-relative path, e.g. `medium/0042-trapping-rain-water.md`."""
    return f"{difficulty.lower()}/{frontend_id.zfill(4)}-{slug}.md"


def solution_url(repository: str, path: str) -> str:
    """GitHub URL of a solution file on main."""
    return f"https://github.com/{repository}/blob/main/{path}"


def problem_url(slug: str) -> str:
    """LeetCode problem URL."""
    return f"https://leetcode.com/problems/{slug}/"


def _code_block(fence: str, code: str) -> str:
    return f"```{fence}\n{code.strip()}\n```"


def render_solution(
    *,
    frontend_id: str,
    title: str,
    slug: str,
    difficulty: str,
    tags: list[str],
    language: Language,
    day: int,
    date: str,
    model: str,
    solution: dict[str, Any],
) -> str:
    """Render the solution Markdown (§10 template). Contains no statement text."""
    optimal = solution["optimal"]
    parts = [
        f"# {frontend_id}. {title}",
        "",
        f"**Difficulty:** {difficulty} · **Topics:** {', '.join(tags) or '—'} · "
        f"**Language:** {language.display} · **Day:** {day} · **Date:** {date}",
        "",
        f"🔗 [Open on LeetCode]({problem_url(slug)})",
        "",
        f"> AI-generated with `{model}`. Unverified. Check before trusting.",
        "",
        "## Hint",
        solution.get("hint") or "—",
        "",
    ]
    brute = solution.get("brute_force")
    if brute:
        parts += [
            "## Brute force",
            brute.get("idea") or "—",
            "",
            f"**Time:** {brute.get('time', '?')} · **Space:** {brute.get('space', '?')}",
            "",
            _code_block(language.fence, brute["code"]),
            "",
        ]
    parts += [f"## Optimal: {solution.get('pattern') or 'Optimal approach'}", optimal.get("idea") or "—", ""]
    steps = optimal.get("steps") or []
    if steps:
        parts += [f"{i}. {step}" for i, step in enumerate(steps, 1)] + [""]
    parts += [
        f"**Time:** {optimal.get('time', '?')} · **Space:** {optimal.get('space', '?')}",
        "",
        _code_block(language.fence, optimal["code"]),
        "",
        "## Edge cases",
    ]
    parts += [f"- {e}" for e in solution.get("edge_cases") or []] or ["- —"]
    parts += ["", "## Dry run (example 1)", solution.get("dry_run") or "—", ""]
    return "\n".join(parts)


def write_solution(root: Path, path: str, markdown: str) -> Path:
    """Write the Markdown to `<root>/<path>` and return the absolute path."""
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(markdown, encoding="utf-8")
    return target
