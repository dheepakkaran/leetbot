# LeetCode Daily Bot — Build Spec

You are Claude Code. Build this entire project in one pass, following this spec.

---

## 0. How to work

1. Read this whole file before writing any code.
2. Work autonomously through every section. Do not stop to ask for confirmation. Stop only if you are blocked by something that only the owner can do (secrets, account actions). In that case, finish everything else first, then list the blockers at the end.
3. When something is ambiguous, pick the simplest option that fits this spec and record it in `DECISIONS.md` (one line per decision, with the reason).
4. LeetCode's GraphQL API is **unofficial**. Before writing the client, run the live smoke queries in §7 (you have network access locally). Adapt field names to what the API actually returns. Write the working queries into `src/leetcode_queries.py`.
5. If `gh auth token` works on this machine, use that token to make one live GitHub Models call and confirm the model IDs in §10 exist. If an ID doesn't exist, pick the closest available model and record the change in `DECISIONS.md`.
6. Never commit secrets. Never commit LeetCode problem statement text. Only links, metadata and generated solutions go in the repo.
7. You are done when every item in §18 (acceptance criteria) passes. Finish by printing the owner checklist from §19.

---

## 1. What this is

A GitHub Actions bot that does four things on a schedule, with no server:

1. **Every morning:** picks a LeetCode problem (with no repeats), generates a solution with a free LLM, commits it as Markdown into `easy/`, `medium/` or `hard/`, and sends a Telegram message containing a greeting, today's problem, the owner's LeetCode stats, a hint, and the solution link.
2. **Every 2 hours:** checks the owner's public LeetCode profile for accepted submissions. When a logged problem is solved, it updates `log.csv` and **edits the original Telegram message** to show it as solved.
3. **Every evening:** if today's problem is still unsolved, sends a short nudge before LeetCode's daily reset.
4. **Always:** keeps `log.csv` as the single source of truth.

---

## 2. Owner facts

| Key | Value |
|---|---|
| Owner display name | `Dheepak` |
| GitHub repo | `dheepakkaran/leetcode-daily` (public) |
| LeetCode username | `___ka__ran___` (3 underscores, ka, 2 underscores, ran, 3 underscores). Read it from the repo **variable** `LEETCODE_USERNAME`, never hardcode it. |
| Local timezone | `America/New_York` |
| Telegram | Private chat with the owner only |
| Current LeetCode state (for test fixtures) | 67 solved (Easy 37, Medium 30, Hard 0), rank ~2,266,342, current streak 0 |

---

## 3. Stack

- Python 3.12, `requests`, `PyYAML`, `pytest`. Use stdlib `zoneinfo`, `csv`, `json`, `html`, `subprocess`.
- Don't add other dependencies unless you truly need them (record any you add in `DECISIONS.md`).
- Code style: small modules, type hints, docstrings on public functions, no global state except config.

---

## 4. Repo structure

```
leetcode-daily/
├── .github/workflows/
│   ├── morning.yml
│   ├── sync.yml
│   └── evening.yml
├── src/
│   ├── __init__.py
│   ├── config.py            # loads config.yaml + env
│   ├── leetcode_queries.py  # GraphQL query strings (verified live)
│   ├── leetcode_client.py   # HTTP + retries + typed results
│   ├── picker.py            # problem selection + dedup
│   ├── languages.py         # language rotation
│   ├── llm.py               # GitHub Models client + fallback chain
│   ├── solution_writer.py   # LLM JSON -> Markdown file
│   ├── stats.py             # streak, week progress, deltas, milestones
│   ├── messages.py          # ALL Telegram message rendering (HTML)
│   ├── telegram_client.py   # send / edit / react / reply
│   ├── log_store.py         # log.csv read/write
│   ├── git_ops.py           # commit + pull --rebase + push
│   ├── readme_progress.py   # updates README progress block
│   ├── morning.py           # entry: python -m src.morning
│   ├── sync.py              # entry: python -m src.sync
│   ├── evening.py           # entry: python -m src.evening
│   └── preview.py           # entry: python -m src.preview (sends sample variants)
├── scripts/
│   └── smoke_leetcode.py    # live check of every LeetCode query
├── data/
│   ├── problems.json        # cached problem list (auto-refreshed weekly)
│   ├── stats_history.json   # daily stats snapshots
│   ├── greetings.json       # 30 greeting lines
│   └── messages/            # {date}.json render context of each sent message
├── easy/   medium/   hard/  # solution .md files (keep a .gitkeep)
├── tests/
├── config.yaml
├── log.csv
├── DECISIONS.md
├── requirements.txt
└── README.md
```

---

## 5. `config.yaml`

```yaml
owner_name: Dheepak
timezone: America/New_York

schedule:
  morning_local_hour: 8        # send at/after 08:00 local
  evening_local_hour: 18       # nudge at 18:xx local
  sync_every_hours: 2

languages:
  block_size: 10
  cycle: [cpp, python, java, java, python, cpp]   # 60-problem cycle, then repeats

picker:
  difficulty_by_weekday:       # Monday=0 ... Sunday=6, local date
    0: Easy
    1: Medium
    2: Medium
    3: Easy
    4: Medium
    5: Hard
    6: Medium
  core_patterns:               # LeetCode topic tag slugs
    - array
    - hash-table
    - two-pointers
    - sliding-window
    - stack
    - binary-search
    - linked-list
    - tree
    - graph
    - heap-priority-queue
    - backtracking
    - dynamic-programming
    - greedy
    - trie
    - bit-manipulation
  acrate_ranges:               # prefer problems inside these acceptance ranges
    Easy: [45, 100]
    Medium: [35, 75]
    Hard: [0, 100]
  problems_cache_days: 7

llm:
  provider: github_models
  endpoint: https://models.github.ai/inference/chat/completions
  models:                      # tried in order; verify IDs (see §0.5)
    - deepseek/DeepSeek-V3-0324
    - openai/gpt-4.1
    - openai/gpt-4.1-mini
  temperature: 0.2
  max_retries_per_model: 2

milestones:
  solved_every: 50
  streak_days: [7, 30, 50, 100]

telegram:
  reaction_on_solve: "💯"      # must be in Telegram's allowed reaction set (✅ is not)
```

Read secrets and runtime values from the environment only: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `GITHUB_TOKEN`, `LEETCODE_USERNAME`, and `GITHUB_REPOSITORY` (set automatically in Actions; default to `dheepakkaran/leetcode-daily` locally).

---

## 6. Data files

### `log.csv` (single source of truth)

Columns, in this order:

```
day,date,frontend_id,title,slug,difficulty,tags,source,language,model,solution_path,sent_at,message_id,solved,solved_at,late,submission_id,nudge_sent
```

| Column | Meaning |
|---|---|
| `day` | 1-based bot day counter (= row number) |
| `date` | **UTC** date the problem was issued (YYYY-MM-DD) |
| `tags` | Topic names joined with `; ` |
| `source` | `daily` or `picker` |
| `language` | `cpp`, `python` or `java` |
| `model` | Model ID used, or `none` if generation failed |
| `sent_at` | ISO8601 UTC time the Telegram message was sent |
| `solved` | `true` / `false` |
| `solved_at` | ISO8601 UTC time of the matching accepted submission |
| `late` | `true` if solved after that problem's UTC day ended |
| `nudge_sent` | `true` / `false` |

Write it atomically: write to a temp file, then rename.

### Other data files

- **`data/stats_history.json`:** a list of daily snapshots `{date, total, easy, medium, hard, ranking, streak}`. Append one per morning run.
- **`data/messages/{date}.json`:** everything needed to re-render that morning's message: problem fields, language, day, stats snapshot, yesterday status, variant, hint, solution URL, and the message ID. Edits re-render from this file through the **same** renderer. Never edit text by string surgery.
- **`data/greetings.json`:** 30 short, varied morning lines that are not cringe (e.g. "Good morning, {name}", "Rise and grind, {name}", "Morning, {name}. One problem, that's it."). Pick by `(day - 1) % 30`.
- **`data/problems.json`:** the full problem list cache, with `fetched_at`. Refresh if older than `problems_cache_days`.

---

## 7. LeetCode client

- **Endpoint:** `POST https://leetcode.com/graphql`.
- **Headers:** `Content-Type: application/json`, `Referer: https://leetcode.com`, and a normal desktop browser `User-Agent`.
- **Retries:** 3 attempts with exponential backoff (2s, 4s, 8s). Raise a clear error after the last attempt.
- **First step:** write `scripts/smoke_leetcode.py` to run each query below live against `LEETCODE_USERNAME` and print trimmed results. Fix field names until all of them work.

### Queries

These are starting points; verify each one live.

1. **Daily problem:**
   ```graphql
   query { activeDailyCodingChallengeQuestion { date link question { questionFrontendId title titleSlug difficulty isPaidOnly topicTags { name slug } } } }
   ```
2. **Question detail:**
   ```graphql
   query($titleSlug: String!) { question(titleSlug: $titleSlug) { questionFrontendId title titleSlug difficulty isPaidOnly content exampleTestcases codeSnippets { langSlug code } topicTags { name slug } } }
   ```
3. **Problem list:**
   ```graphql
   query { problemsetQuestionList: questionList(categorySlug: "", limit: -1, skip: 0, filters: {}) { total: totalNum questions: data { questionFrontendId title titleSlug difficulty acRate paidOnly topicTags { slug } } } }
   ```
   If this fails, try `problemsetQuestionListV2`, then the REST endpoint `GET https://leetcode.com/api/problems/all/`. Normalize all three to the same schema.
4. **User stats:**
   ```graphql
   query($u: String!) { allQuestionsCount { difficulty count } matchedUser(username: $u) { profile { ranking } submitStatsGlobal { acSubmissionNum { difficulty count } } userCalendar { streak totalActiveDays submissionCalendar } } }
   ```
5. **Recent accepted submissions:**
   ```graphql
   query($u: String!) { recentAcSubmissionList(username: $u, limit: 20) { id title titleSlug timestamp } }
   ```
6. **Optional, language check:**
   ```graphql
   query($u: String!) { recentSubmissionList(username: $u, limit: 20) { titleSlug timestamp statusDisplay lang } }
   ```
   If this exposes `lang`, record the language actually used. If not, skip it.

### Language slugs

`cpp → cpp`, `python → python3`, `java → java`.

### Problem text

Convert the `content` HTML to plain text (stdlib `html.parser`) **only** to put it in the LLM prompt. Never write it to disk.

---

## 8. Problem selection (`picker.py`)

**Hybrid rule:**

1. Fetch the official daily problem.
2. **Use it** unless any of these are true:
   - it's premium (`isPaidOnly`),
   - its slug is already in `log.csv`,
   - its slug is in the owner's recent AC list.
3. Otherwise, **fall back to the picker**:
   - **Target difficulty:** `difficulty_by_weekday[local weekday]`.
   - **Candidates:** non-premium problems of that difficulty whose slug is not in the log and not in recent ACs.
   - **Pattern:** choose the `core_pattern` with the fewest log rows (ties broken by config order). Filter candidates by that tag. If none remain, use any core pattern. If still none, use any candidate.
   - **Acceptance rate:** prefer candidates inside `acrate_ranges`. Relax the range if that leaves none.
   - **Final pick:** deterministic, using `random.Random(f"{utc_date}")`.
4. Record `source` as `daily` or `picker`.

---

## 9. Language rotation (`languages.py`)

For bot day `n` (1-based):

```
block = ((n - 1) // block_size) % len(cycle)
lang  = cycle[block]
k     = ((n - 1) % block_size) + 1        # shown as "k/10"
```

This gives days 1–10 C++, 11–20 Python, 21–30 Java, 31–40 Java, 41–50 Python, 51–60 C++, then the cycle repeats.

- **Display names:** C++, Python, Java.
- **Code fences:** `cpp`, `python`, `java`.

---

## 10. Solution generation

### `llm.py`

- **Request:** OpenAI-compatible chat completions to `llm.endpoint`, with `Authorization: Bearer $GITHUB_TOKEN`.
- **Fallback:** try models in config order; for each, retry up to `max_retries_per_model` times on 429/5xx with backoff. A 404 or unknown model means skip to the next model.
- **Output handling:**
  - Strip any `<think>…</think>` blocks and fenced code markers before parsing JSON.
  - If parsing fails, re-ask once with "Return ONLY valid JSON."
- **Total failure:** don't crash the morning run. Return `None`; the message then says the solution is unavailable today (see §11).

### Prompt

- **System message:** "You are an expert competitive programmer and interview coach. You write correct, idiomatic, interview-quality solutions."
- **User message must include:**
  - title, difficulty and tags,
  - the plain-text statement,
  - example test cases,
  - the **exact LeetCode code snippet for the target language** (the solution must use this signature),
  - the target language,
  - the JSON schema below,
  - these rules: the code must compile/run on LeetCode as-is; mentally verify it on the examples; if brute force is already optimal, set `brute_force` to `null`.

### JSON the model must return

```json
{
  "hint": "one short line, no spoilers of the full approach",
  "pattern": "e.g. Binary Search",
  "brute_force": {"idea": "...", "time": "O(...)", "space": "O(...)", "code": "..."} ,
  "optimal": {"idea": "...", "steps": ["...", "..."], "time": "O(...)", "space": "O(...)", "code": "..."},
  "edge_cases": ["...", "..."],
  "dry_run": "walkthrough of example 1 with concrete values"
}
```

### `solution_writer.py`

**Path:** `{difficulty_lower}/{frontend_id:04d}-{slug}.md`

**Template:**

~~~markdown
# {id}. {title}

**Difficulty:** {difficulty} · **Topics:** {tags} · **Language:** {Lang} · **Day:** {day} · **Date:** {date}

🔗 [Open on LeetCode](https://leetcode.com/problems/{slug}/)

> AI-generated with `{model}`. Unverified. Check before trusting.

## Hint
{hint}

## Brute force
{idea}

**Time:** {time} · **Space:** {space}

```{fence}
{code}
```

## Optimal: {pattern}
{idea}

1. {step}
...

**Time:** {time} · **Space:** {space}

```{fence}
{code}
```

## Edge cases
- ...

## Dry run (example 1)
{dry_run}
~~~

Omit the Brute force section when `brute_force` is null.

**Solution URL:** `https://github.com/{GITHUB_REPOSITORY}/blob/main/{path}`.

---

## 11. Telegram

### `telegram_client.py`

Base URL: `https://api.telegram.org/bot{TOKEN}/`.

| Method | How to call it |
|---|---|
| `sendMessage` | `parse_mode=HTML`, `link_preview_options={"is_disabled": true}`, inline keyboard of URL buttons. Return `message_id`. |
| `editMessageText` | Same options. Treat "message is not modified" as success. |
| `setMessageReaction` | `reaction=[{"type":"emoji","emoji": config reaction}]`. Ignore failures. |
| Reply fallback | `sendMessage` with `reply_parameters={"message_id": X}`. |

**Edit fallback chain:** if `editMessageText` fails because the message can't be found or edited, send a short reply to the original message. If that also fails, send a standalone message.

### `messages.py`

Rules:
- All rendering lives here.
- Escape every dynamic string with `html.escape`.
- The message must be ≤ 4096 characters.
- **The first two lines are what shows in the phone notification**, so keep the greeting on line 1 and today's problem on line 2.

#### Morning message: base layout

```
☀️ <b>{greeting} · Day {n}</b>
Today: #{id} {title}
{difficulty} · {tags (max 3)} · Solve in {Lang} ({k}/10)

{yesterday_line}
🔥 Streak {streak} days · Week {w}/7 {bar}
<blockquote expandable>📊 <b>Your LeetCode</b>
Solved {total} · Easy {e} · Medium {m} · Hard {h}
Ranking {ranking:,} · Active days {active}</blockquote>
💡 Hint: <tg-spoiler>{hint}</tg-spoiler>
📘 Solution: <tg-spoiler>{short_url}</tg-spoiler>

{closing}
```

- **Buttons:** `[Open problem → leetcode problem URL]` `[View solution → GitHub URL]`.
- **`bar`:** 7 characters, `▰` for solved days this ISO week (Mon–Sun, UTC dates) and `▱` for the rest.
- **`yesterday_line`:** refers to the previous log row (sync has already run, see §12):
  - solved on time: `✅ Yesterday: #{id} solved`
  - solved late: `✅ Yesterday: #{id} solved late`
  - unsolved: `❌ Yesterday: #{id} not solved · streak reset`
  - day 1: no line at all.
- **Milestone line:** if total solved crossed a multiple of `solved_every`, or the streak hit a value in `streak_days`, insert `🎉 {text}` above the stats blockquote.

#### Morning message: variants

| Variant | When | Difference from base |
|---|---|---|
| `normal` | Default | Closing: `Do it asap.` |
| `missed` | Previous row unsolved | Closing: `Yesterday slipped. Today gets you back on track.` |
| `sunday` | Local weekday is Sunday | Stats blockquote becomes a week recap (below). Closing: `New week. Do it asap.` |
| `no_solution` | LLM failed | Solution line becomes `📘 Solution unavailable today. Rerun from Actions.`; only the Open problem button; hint line omitted. |

If both `missed` and `sunday` apply, use the Sunday layout with the missed yesterday line and closing.

**Sunday recap blockquote:**
```
<blockquote expandable>📊 <b>Week recap</b>
Solved {x}/7 · Easy {a} · Medium {b} · Hard {c}
Total {total} ({delta:+d}) · Ranking {arrow} {abs(rank_delta):,}
Fastest: #{id} in {duration} after alert</blockquote>
```
Deltas compare against the snapshot from 7 days earlier, or the oldest available. Arrow is `↑` when the rank number got smaller. Omit the Fastest line if nothing was solved this week.

#### Solved edit

Re-render the same morning message with `status=solved`. Differences from the original:
- A status line right after the tags line:
  - on time: `✅ <b>Solved at {local h:mm AM/PM} · {duration} after alert</b>`
  - late: `✅ <b>Solved late · {local Mon D}</b>`
- Hint and solution shown **without** spoiler tags.
- Closing: `Done. See you tomorrow.`
- Buttons: `[Your submission → https://leetcode.com/submissions/detail/{submission_id}/]` `[View solution]`.
- Stats block unchanged. It's a snapshot of that morning.

#### Evening nudge

```
⏰ <b>Still pending: #{id}</b>
{title}

{hours_left} left before LeetCode's day resets ({reset_local_time}).
🔥 Your {streak}-day streak is on the line.
```

- If the streak is 0, the last line is `Start a new streak today.`
- `reset_local_time` is 00:00 UTC converted to local time (8:00 PM EDT / 7:00 PM EST).
- Button: `[Open problem]`.

#### Failure alert

Sent by the workflow on failure:
`⚠️ Bot error: {workflow} failed. {run_url}`

---

## 12. Jobs

All three jobs share these flags: `--dry-run` (print messages, no Telegram, no git) and `--force` (skip time gating and idempotency checks).

### `src/morning.py`

1. **Time gate:** run only if local time ≥ `morning_local_hour` **and** `log.csv` has no row for today's UTC date. Otherwise exit 0 with a log line. (The workflow schedules two UTC times to handle daylight saving; this gate makes exactly one of them send.)
2. **Run sync** (same code as §12 sync) so yesterday's status is fresh.
3. Fetch user stats and recent ACs. Append a stats snapshot.
4. **Pick the problem** (§8) and fetch its details.
5. Compute day `n` and the language (§9).
6. Generate the solution (§10) and write the `.md` file.
7. Append the log row (`message_id` empty, `solved=false`).
8. Refresh the README progress block. **Commit and push** (`chore: day {n} #{id} {slug}`). The solution URL must exist before sending.
9. Compute stats (§14), choose the variant, render, and send to Telegram.
10. Save `data/messages/{date}.json`. Write `message_id` and `sent_at` to the row. Commit and push (`chore: day {n} message id`).

### `src/sync.py`

1. Load rows where `solved=false` and `message_id` is set.
2. Fetch `recentAcSubmissionList`.
3. **Match:** an AC matches a row when `titleSlug == slug` **and** `timestamp >= sent_at`. The timestamp check stops old ACs (e.g. ones from months ago) from counting.
4. For each match:
   - Set `solved=true`, `solved_at`, `submission_id`.
   - Set `late` = whether `solved_at` falls after the end of that row's UTC `date`.
   - Re-render the message from `data/messages/{date}.json` with `status=solved` and edit it (with the fallback chain from §11).
   - Add the reaction.
5. Commit and push only if something changed (`chore: sync solved #{ids}`).

### `src/evening.py`

1. **Time gate:** local hour == `evening_local_hour`, today's row exists, and `nudge_sent=false`.
2. Run sync first. If today's row is now solved, exit.
3. Send the nudge. Set `nudge_sent=true`. Commit and push.

### `src/preview.py`

Sends one sample of every variant to the owner's chat using fixture data: normal, missed, sunday, no_solution, solved edit, evening nudge, and a milestone. This lets the owner check formatting on the phone. It must not touch `log.csv` or git.

---

## 13. Workflows

Requirements common to all three:

```yaml
permissions:
  contents: write
  models: read
concurrency:
  group: leetcode-bot
  cancel-in-progress: false
```

Each workflow:
- checks out the repo,
- sets up Python 3.12 with pip cache,
- installs requirements,
- runs its module with `GITHUB_TOKEN`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` and `LEETCODE_USERNAME` in the environment (`vars.LEETCODE_USERNAME` for the username),
- has a final `if: failure()` step that `curl`s the failure alert to Telegram with the run URL,
- has `workflow_dispatch` with boolean inputs `dry_run` and `force`.

Schedules (UTC; the scripts' time gates handle daylight saving):

| Workflow | Cron |
|---|---|
| `morning.yml` | `17 12 * * *` and `17 13 * * *` |
| `sync.yml` | `7 */2 * * *` |
| `evening.yml` | `3 22 * * *` and `3 23 * * *` |

**Git identity:** `github-actions[bot]` / `41898282+github-actions[bot]@users.noreply.github.com`.

**`git_ops.commit_and_push`:**
1. `git add -A`
2. Exit if `git diff --cached --quiet` shows nothing staged.
3. Commit.
4. Push; on rejection, `git pull --rebase` and retry, up to 3 tries.

---

## 14. Stats (`stats.py`)

| Stat | How to compute it |
|---|---|
| Total and per-difficulty solved | `acSubmissionNum` (skip the `All` entry when summing; use it as the total) |
| Ranking | `profile.ranking` |
| Active days | `totalActiveDays` |
| Current streak | From `submissionCalendar` (JSON string of UTC-midnight epoch → count): consecutive UTC days with count > 0, ending today, or yesterday if today has none yet. If the streak reaches Jan 1, fetch the previous year's calendar too (`userCalendar(year: Y)`). |
| Week progress | Log rows in the current ISO week (UTC dates) with `solved=true` |
| Duration after alert | `solved_at - sent_at`, formatted `38 min`, `3 h 12 min`, or `2 days` |
| Milestones | Compare today's snapshot with the previous one |

---

## 15. README.md

Sections:
1. What this is (2–3 lines).
2. How it works: a Mermaid flowchart of morning → LLM → commit → Telegram, plus sync → edit.
3. Setup: the owner checklist from §19.
4. Configuration: `config.yaml` explained.
5. Manual runs and `preview`.
6. Repo layout.
7. Copyright note: problem statements are LeetCode's; this repo stores only links and AI-generated solutions.
8. Auto-updated progress block between `<!-- PROGRESS:START -->` and `<!-- PROGRESS:END -->`: total bot days, solved count and rate, by-difficulty counts, current streak, and a table of the last 7 days (day, date, problem link, difficulty, language, status).

---

## 16. Tests (`pytest`, no network)

Mock all HTTP.

- **picker:** respects premium, log and recent-AC dedup; weekday difficulty; least-covered pattern; deterministic per date; fallback cascade.
- **languages:** days 1, 10, 11, 21, 31, 41, 51, 60 and 61 map to the right language and k.
- **messages:**
  - every variant renders;
  - titles with `&`, `<` and `>` are escaped;
  - length ≤ 4096;
  - first line contains the greeting and day;
  - the solved edit has no `<tg-spoiler>`;
  - the evening reset time is correct for both EDT and EST dates.
- **sync:** an AC older than `sent_at` is ignored; a late solve sets `late=true`; "message is not modified" counts as success; the edit fallback chain is called in order.
- **morning time gate:** for each of EDT and EST, exactly one of the two cron times passes; an existing row for the date blocks a re-send.
- **log_store:** round-trip and atomic write.
- **stats:** streak from a fixture calendar, including the case where today has no submission yet.
- **llm:** `<think>` stripping, fenced JSON parsing, fallback to the next model on 404, `None` after all models fail.

---

## 17. Local dev

```
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/smoke_leetcode.py                  # live API check
python -m src.morning --dry-run --force           # full run, prints message, no send/commit
python -m src.preview                             # sends every variant (needs Telegram env vars)
pytest -q
```

Put a `.env.example` file in the repo with the variable names only, and add `.env` to `.gitignore`. Load `.env` locally with a tiny stdlib parser. Don't add python-dotenv.

---

## 18. Acceptance criteria

- [ ] `scripts/smoke_leetcode.py` runs live and every query returns data for `___ka__ran___`.
- [ ] `pytest -q` passes.
- [ ] `python -m src.morning --dry-run --force` prints a complete morning message using real stats (67 solved, Hard 0 at time of writing) and a real problem. Nothing is committed.
- [ ] If a GitHub token was available: one real solution `.md` was generated locally and reviewed for correct format (then deleted or kept as a sample in `DECISIONS.md`).
- [ ] All three workflows pass `actionlint` if it's available, otherwise a YAML parse check.
- [ ] No secrets and no problem statement text in any tracked file.
- [ ] `README.md`, `DECISIONS.md`, `.env.example` and `.gitignore` exist.
- [ ] Repo initialized with a clean first commit. If `gh` is authenticated, create `dheepakkaran/leetcode-daily` (public) and push; otherwise print the exact commands.

---

## 19. Owner checklist (print this at the end)

1. **Telegram:**
   1. Message @BotFather, send `/newbot`, and copy the token.
   2. Open your new bot and send it `/start`.
   3. Visit `https://api.telegram.org/bot<TOKEN>/getUpdates` and copy `message.chat.id`.
2. **GitHub repo → Settings → Secrets and variables → Actions:**
   - Secrets: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.
   - Variables: `LEETCODE_USERNAME` = `___ka__ran___`.
3. **GitHub repo → Settings → Actions → General:** set Workflow permissions to "Read and write".
4. **Locally:** run `python -m src.preview` with the env vars set, and check every variant on your phone.
5. **Actions tab:** run `morning` manually with `force=true` once. Confirm the commit, the Telegram message, and the solution link.
6. **Solve the problem on LeetCode,** then run `sync` manually. Confirm the message edits to "Solved".
7. **Done.** From here it runs daily on its own. If GitHub ever emails that scheduled workflows were disabled for inactivity, re-enable them in the Actions tab.
