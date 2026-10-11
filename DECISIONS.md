# Decisions

One line per judgment call, with the reason.

## Environment and verification

- **Python 3.14 locally, 3.12 in Actions:** only 3.14 was installed here. `vermin` reports the code needs ≥ 3.9, so 3.12 is safe.
- **GitHub Models IDs not verified live:** `gh` isn't installed and no `GITHUB_TOKEN` was available, so §0.5 couldn't run. The config keeps the spec's IDs (`deepseek/DeepSeek-V3-0324`, `openai/gpt-4.1`, `openai/gpt-4.1-mini`). A 404/unknown model falls through to the next one, and total failure sends the `no_solution` variant.
- **No real solution sample:** acceptance item 4 is conditional on a token. The `.md` format was checked with fixture LLM output and real problem metadata in a dry run.
- **No actionlint:** it isn't installed, and downloading binaries was out of scope. `tests/test_workflows_and_repo.py` parses each workflow and asserts crons, permissions, concurrency, inputs, env and the failure step.

## LeetCode API (verified live on 2026-10-10, see `scripts/smoke_leetcode.py`)

- **Problem list field:** `paidOnly` doesn't exist on `questionList`'s `QuestionNode`. The live API uses `isPaidOnly`, and `acRate` there is a percentage.
- **`problemsetQuestionListV2`:** needs `filters: {filterCombineType: ALL}`, caps pages at 100 (so the client paginates), returns upper-case difficulty, and gives `acRate` as a 0–1 fraction (normalized ×100).
- **REST fallback:** uses `/api/problems/algorithms/` (same category as the others). It has no topic tags, so the picker drops to "any candidate" for patterns. acRate = `total_acs / total_submitted`.
- **Category:** the problem list uses `categorySlug: "algorithms"`. The empty category also returns Database/Shell/pandas/JS/Concurrency problems, which have no C++/Python/Java snippets.
- **Calendar:** the default `userCalendar` (no year) covers the current period. `userCalendar(year: Y)` is used only when the streak walk reaches Jan 1, per §14.
- **API streak ignored:** `userCalendar.streak` isn't the current streak (it returned 4 when the real current streak is 0). The bot computes the streak from `submissionCalendar`.
- **Retries:** "3 attempts (2s, 4s, 8s)" means 3 attempts total, with 2s and 4s waits between them. Only network errors, 403, 429, 5xx and non-JSON 2xx bodies are retried. GraphQL validation errors (HTTP 400 + `errors`) fail at once because retrying can't fix them.
- **Language check:** `recentSubmissionList` exposes `lang`. Sync records it as `actual_language` in `data/messages/{date}.json` rather than adding a column, so `log.csv` keeps exactly the spec's columns.

## Picker

- **Pattern coverage:** `log.csv` stores topic *names*, so each name is slugified ("Heap (Priority Queue)" → `heap-priority-queue`) to count rows per core pattern.
- **"Relax the range":** if no candidate is inside `acrate_ranges`, the range is dropped entirely rather than widened step by step.
- **Last resort:** if no unlogged, non-premium problem exists at the target difficulty, any difficulty is used, and a `PickerError` is raised only if nothing is left at all.
- **Determinism:** candidates are sorted by frontend ID before `random.Random(f"{utc_date}").choice` so the pick doesn't depend on API ordering.
- **Problem cache refresh:** the morning run refreshes `data/problems.json` whenever it's older than 7 days, even if the daily is used. A failed refresh falls back to the stale cache.

## LLM

- **Retries per model:** `max_retries_per_model: 2` means 1 try + 2 retries on 429/5xx/network errors (2s, 4s backoff). A `Retry-After` > 30s (e.g. a daily quota) skips to the next model immediately.
- **Other errors:** 401/403/413 and other non-retryable errors also skip to the next model, so the run never crashes on the LLM.
- **Output tokens:** `max_tokens: 4000`, because the GitHub Models free tier caps output at 4k tokens per request.
- **Prompt size:** statement text is truncated to 12k chars and examples to 3k chars to stay under the free-tier 8k input-token cap.
- **JSON parsing:** `json.loads(strict=False)` tolerates raw newlines inside code strings, a common model mistake. Fenced blocks and the outermost `{…}` span are tried too.
- **Minimal valid answer:** an answer is usable only if `optimal.code` is non-empty. A `brute_force` without code is treated as null.
- **No `response_format`:** not every model on the chain supports JSON mode, so the bot relies on the prompt plus parsing.

## Messages

- **"Short URL":** the solution line shows the repo path (e.g. `medium/2333-….md`) as link text pointing to the full GitHub URL, which keeps the line short on a phone.
- **Escaping:** text nodes use `html.escape(s, quote=False)`. Telegram only needs `<`, `>` and `&` escaped, so apostrophes stay readable. Attributes (`href`) use `quote=True`.
- **Length:** if the message would exceed 4096 chars, the hint is truncated progressively (400 → 200 → 80 chars) and the title is capped at 200.
- **Week bar:** positional, Mon..Sun. `▰` marks a weekday whose row is solved. `Week {w}/7` counts solved rows in the ISO week.
- **Sunday recap window:** the 7 UTC dates before today (last Sunday … Saturday). This matches the "snapshot from 7 days earlier" used for the deltas. Ranking unchanged shows `→ 0`.
- **Milestones:** shown only when a previous snapshot exists, so the very first run doesn't celebrate crossing 50. Each milestone gets its own `🎉` line.
- **Pluralization:** "1 day" / "N days". Durations under a minute show as "1 min".
- **Edit fallback:** the reply step sends a short "✅ #id title / status" reply. If replying also fails (original deleted), the full solved message is sent standalone because that's more useful than the short text.
- **Snapshot fields:** the streak/week line, like the stats block, is part of the morning snapshot, so the solved edit doesn't change it.
- **`render_failure_alert`:** exists for consistency and tests. The workflows send the same text with `curl`, as §11 requires.

## Jobs

- **Shared plumbing:** added `src/runtime.py` (CLI flags, client construction, dry-run messenger, message-context files, greetings) so the three entry points stay small. This is the only module beyond §4.
- **Dry-run:** writes nothing tracked (no log, data, README or git). A generated solution goes to the git-ignored `.dry-run/` so it can be reviewed. LeetCode and the LLM are still called for real.
- **Repair on rerun:** if today's row exists but its message was never sent, or it has no solution (`model=none`), the next morning run fixes that row instead of issuing another problem, with or without `--force`. This makes "Rerun from Actions" true, and in EDT the second cron retries automatically.
- **Same-date rows:** `--force` with a healthy row for today issues a new row (new day) as the spec says. Its render context is saved as `data/messages/{date}-day{n}.json`, so it doesn't overwrite the first one.
- **Missing context:** if sync finds no saved context for a solved row, it replies to the original message (falling back to standalone) instead of editing, since it can't re-render.
- **README streak:** the progress block's "current streak" is the LeetCode streak from the latest stats snapshot. Sync also refreshes the block when something changed, using that snapshot.
- **`late` before solving:** unsolved rows store `late=false`.
- **Git identity:** set in each workflow with `git config` before running the job. Local non-dry runs use the developer's own identity.
- **CI workflow:** added `.github/workflows/ci.yml` (beyond §13) to run `pytest -q` on every pull request and on pushes to `main`. Pushes that only touch bot data (`log.csv`, `data/`, solutions) are skipped.
- **Dry-run messenger location:** `Messenger` and `DryRunMessenger` live in `telegram_client.py`, next to the real client, so `preview` doesn't depend on the job runtime.
- **Action versions:** `actions/checkout@v5` and `actions/setup-python@v6` (current majors).
- **Workflow inputs:** passed through `env:` instead of being interpolated into the shell script, to avoid script injection.

## Dependencies

- **Runtime:** `requests`, `PyYAML`, `pytest` only. `pyflakes` and `vermin` were used locally for checks and are not project dependencies.
- **`SPEC.md` is tracked:** it's the design doc this repo was built from. Tracking it also stops a local non-dry run's `git add -A` from sweeping it into a bot commit.
