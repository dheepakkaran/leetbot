# LeetBot 🤖

**Your daily LeetCode coach on Telegram.**

A serverless GitHub Actions bot. Every morning it picks one LeetCode problem with no repeats, commits an AI-generated solution, and sends Dheepak a Telegram message with the problem, LeetCode stats and a hint. During the day it watches the public LeetCode profile and edits that message to "Solved" once an accepted submission shows up. In the evening it sends a nudge if the problem is still open.

## How it works

```mermaid
flowchart LR
    subgraph Morning["morning.yml (from 08:00 local)"]
        A[Time gate] --> B[Sync yesterday]
        B --> C[Stats + recent ACs]
        C --> D{Official daily usable?}
        D -- yes --> F[Question detail]
        D -- "premium / logged / solved" --> E[Picker: weekday difficulty,<br/>least-covered pattern]
        E --> F
        F --> G[Gemini API LLM<br/>with model fallback]
        G --> H[Write easy/medium/hard/*.md<br/>append log.csv]
        H --> I[Commit + push]
        I --> J[Send Telegram message]
        J --> K[Save data/messages/date.json<br/>commit message id]
    end
    subgraph Sync["sync.yml (hourly)"]
        S1[Pending rows in log.csv] --> S2[recentAcSubmissionList]
        S2 --> S3{slug matches and<br/>timestamp >= sent_at?}
        S3 -- yes --> S4[Mark solved in log.csv]
        S4 --> S5[Re-render from data/messages<br/>editMessageText + reaction]
        S5 --> S6[Commit + push]
    end
    subgraph Evening["evening.yml (18:00 local to reset)"]
        V1[Sync] --> V2{Still unsolved?}
        V2 -- yes --> V3[Send nudge]
    end
    K -.-> S1
```

- **`log.csv`** is the single source of truth: one row per issued problem.
- The official daily problem is used unless it's premium, already logged or already solved recently. Otherwise a deterministic picker chooses one by weekday difficulty, least-covered core pattern and acceptance rate.
- The solution language rotates in blocks of 10 days: C++, Python, Java, Java, Python, C++, then repeats.
- Edits re-render the original message from its saved context through the same renderer. Text is never patched with string surgery.

## Setup

1. **Telegram:**
   1. Message [@BotFather](https://t.me/BotFather), send `/newbot`, and copy the token.
   2. Open your new bot and send it `/start`.
   3. Visit `https://api.telegram.org/bot<TOKEN>/getUpdates` and copy `message.chat.id`.
2. **Gemini:** sign in at [aistudio.google.com/apikey](https://aistudio.google.com/apikey) and create a free API key (no credit card needed).
3. **GitHub repo → Settings → Secrets and variables → Actions:**
   - Secrets: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `GEMINI_API_KEY`.
   - Variables: `LEETCODE_USERNAME` = `___ka__ran___`.
4. **GitHub repo → Settings → Actions → General:** set Workflow permissions to "Read and write".
5. **Reliable timers (recommended):** GitHub's own scheduler can start runs hours late or skip them, so an outside timer presses "Run workflow" at exact times. See [Reliable timing](#reliable-timing).
6. **Locally:** run `python -m src.preview` with the env vars set, and check every variant on your phone.
7. **Actions tab:** run `morning` manually with `force=true` once. Confirm the commit, the Telegram message, and the solution link.
8. **Solve the problem on LeetCode,** then run `sync` manually. Confirm the message edits to "Solved".
9. **Done.** From here it runs daily on its own. If GitHub ever emails that scheduled workflows were disabled for inactivity, re-enable them in the Actions tab.

Solutions are written by Google's Gemini API on its free tier, called through Gemini's OpenAI-compatible endpoint. The bot makes one request a day, far below the free limits. (The original design used GitHub Models, which GitHub shut down on July 30, 2026.)

## Reliable timing

GitHub's scheduled workflows are best effort: on this repo's first day they started up to 5 hours late or not at all. The workflows keep their `schedule:` crons as a backup, but the real trigger is [cron-job.org](https://cron-job.org) (free), calling GitHub's `workflow_dispatch` API, which starts a run within seconds.

1. Create a fine-grained token at [github.com/settings/personal-access-tokens/new](https://github.com/settings/personal-access-tokens/new): only this repository, **Actions: Read and write**. Renew it before it expires.
2. On cron-job.org, create three jobs with time zone `America/New_York`:

| Job | URL | Schedule |
|---|---|---|
| morning | `https://api.github.com/repos/dheepakkaran/leetbot/actions/workflows/morning.yml/dispatches` | daily 08:07 |
| evening | `https://api.github.com/repos/dheepakkaran/leetbot/actions/workflows/evening.yml/dispatches` | daily 18:03 |
| sync | `https://api.github.com/repos/dheepakkaran/leetbot/actions/workflows/sync.yml/dispatches` | hourly at :07 |

3. Each job: method `POST`, body `{"ref":"main"}`, and headers `Accept: application/vnd.github+json`, `Authorization: Bearer <token>`, `X-GitHub-Api-Version: 2022-11-28`, `Content-Type: application/json`. A test run returns **204** on success. Only test-run `sync`; `morning` would issue a problem for real.

The time gates make duplicate triggers harmless: only the first eligible run sends, and nothing is sent after LeetCode's 00:00 UTC reset.

## Configuration

All tunables live in [`config.yaml`](config.yaml):

| Key | Meaning |
|---|---|
| `owner_name`, `timezone` | Name used in greetings; local timezone for time gates and displayed times. |
| `schedule.morning_local_hour` | Morning job sends at or after this local hour. The cron fires hourly from 12:17 to 16:17 UTC to cover DST and GitHub dropping scheduled runs; only the first eligible run sends. |
| `schedule.evening_local_hour` | Evening nudge is sent once, at or after this local hour and before LeetCode's 00:00 UTC reset (three cron tries). |
| `schedule.sync_every_hours` | Informational; the actual cadence is the cron in `sync.yml`. |
| `languages.block_size`, `languages.cycle` | Language rotation: day *n* uses `cycle[((n-1) // block_size) % len(cycle)]`. |
| `picker.difficulty_by_weekday` | Fallback picker's target difficulty per local weekday (Mon=0 … Sun=6). |
| `picker.core_patterns` | Topic tag slugs; the picker targets the one with the fewest log rows. |
| `picker.acrate_ranges` | Preferred acceptance-rate range per difficulty (relaxed if nothing fits). |
| `picker.problems_cache_days` | Max age of `data/problems.json` before it's refreshed. |
| `llm.endpoint`, `llm.models` | OpenAI-compatible chat endpoint (Gemini by default) and model IDs, tried in order. |
| `llm.api_key_env` | Name of the env var / Actions secret holding the API key (`GEMINI_API_KEY`). |
| `llm.temperature`, `llm.max_retries_per_model` | Sampling temperature; retries on 429/5xx per model. |
| `llm.reasoning_effort`, `llm.max_output_tokens` | How much Gemini thinks before answering, and the output budget for thinking plus answer. |
| `milestones.solved_every`, `milestones.streak_days` | When to add a 🎉 line (every N solved, or these streak lengths). |
| `telegram.reaction_on_solve` | Reaction added to the morning message when solved (must be an allowed Telegram reaction). |

Secrets and runtime values come from the environment only: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `GEMINI_API_KEY`, `LEETCODE_USERNAME`, `GITHUB_REPOSITORY`. Locally, copy `.env.example` to `.env`.

## Manual runs and preview

Every workflow has a **Run workflow** button with two checkboxes:

- `dry_run`: print the messages in the job log. No Telegram, no git, no file changes.
- `force`: skip time gating and idempotency checks. For `morning` this issues a new problem even if one was already sent today.

If a morning message says *"Solution unavailable today. Rerun from Actions."*, rerun `morning`. It retries the LLM for the same problem and edits the message. You don't need `force` for this.

Locally:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/smoke_leetcode.py                  # live API check
python -m src.morning --dry-run --force           # full run, prints message, no send/commit
python -m src.preview                             # sends every variant (needs Telegram env vars)
python -m src.preview --dry-run                   # prints every variant instead
pytest -q
```

`preview` sends normal, missed, Sunday, no-solution and milestone samples. It also sends one message and edits it into the solved state, then sends an evening nudge. It never touches `log.csv`, data files or git.

## Development workflow

- `main` is always deployable. Work happens on short-lived branches (`feat/…`, `fix/…`, `docs/…`, `ci/…`) using [Conventional Commits](https://www.conventionalcommits.org/).
- Open a pull request into `main`. The `ci` workflow runs `pytest -q` on Python 3.12 and must pass before merging.
- Use **Create a merge commit** when merging, then delete the branch.
- The bot's own jobs commit data (`log.csv`, `data/`, solutions, README progress) straight to `main` as `github-actions[bot]`. If you add branch protection, don't require pull requests for those pushes, or the scheduled jobs will fail.

## Repo layout

```
.github/workflows/   morning.yml · sync.yml · evening.yml · ci.yml (tests on PRs)
src/                 config, LeetCode client + queries, picker, languages, llm,
                     solution_writer, stats, messages, telegram_client, log_store,
                     git_ops, readme_progress, runtime, and the entry points
                     morning / sync / evening / preview
scripts/             smoke_leetcode.py (live check of every query)
data/                problems.json (weekly cache) · stats_history.json ·
                     greetings.json · messages/{date}.json (render contexts)
easy/ medium/ hard/  generated solutions: {id:04d}-{slug}.md
tests/               pytest suite (no network)
config.yaml · log.csv · DECISIONS.md
```

## Copyright

Problem statements belong to LeetCode. This repo stores only problem links, metadata (titles, difficulty, tags) and AI-generated solutions. The statement text is fetched at run time for the LLM prompt and is never written to disk. Solutions are AI-generated and unverified.

<!-- PROGRESS:START -->

## Progress

- **Bot days:** 3
- **Solved:** 0/3 (0%)
- **By difficulty:** Easy 0/1 · Medium 0/1 · Hard 0/1
- **Current LeetCode streak:** 0 days

| Day | Date | Problem | Difficulty | Language | Status |
|---:|---|---|---|---|---|
| 3 | 2026-10-13 | [#3727 Maximum Alternating Sum of Squares](https://leetcode.com/problems/maximum-alternating-sum-of-squares/) · [solution](medium/3727-maximum-alternating-sum-of-squares.md) | Medium | C++ | ⏳ Pending |
| 2 | 2026-10-12 | [#2897 Apply Operations on Array to Maximize Sum of Squares](https://leetcode.com/problems/apply-operations-on-array-to-maximize-sum-of-squares/) · [solution](hard/2897-apply-operations-on-array-to-maximize-sum-of-squares.md) | Hard | C++ | ❌ Missed |
| 1 | 2026-10-11 | [#2778 Sum of Squares of Special Elements](https://leetcode.com/problems/sum-of-squares-of-special-elements/) · [solution](easy/2778-sum-of-squares-of-special-elements.md) | Easy | C++ | ❌ Missed |

<!-- PROGRESS:END -->
