"""Load `config.yaml` plus secrets/runtime values from the environment."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REPOSITORY = "dheepakkaran/leetcode-daily"


def load_dotenv(path: Path) -> None:
    """Load `KEY=VALUE` lines from a local `.env` file into `os.environ`.

    Existing environment variables win. Blank lines and `#` comments are
    ignored, an optional `export ` prefix is allowed, and matching single or
    double quotes around the value are stripped.
    """
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export "):]
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
            value = value[1:-1]
        if key and key not in os.environ:
            os.environ[key] = value


@dataclass(frozen=True)
class Config:
    """All configuration for one bot run."""

    root: Path
    owner_name: str
    timezone: ZoneInfo
    morning_local_hour: int
    evening_local_hour: int
    sync_every_hours: int
    block_size: int
    language_cycle: list[str]
    difficulty_by_weekday: dict[int, str]
    core_patterns: list[str]
    acrate_ranges: dict[str, tuple[float, float]]
    problems_cache_days: int
    llm_endpoint: str
    llm_api_key_env: str
    llm_models: list[str]
    llm_temperature: float
    llm_reasoning_effort: str | None
    llm_max_output_tokens: int
    llm_max_retries_per_model: int
    milestone_solved_every: int
    milestone_streak_days: list[int]
    reaction_on_solve: str
    telegram_bot_token: str = field(default="", repr=False)
    telegram_chat_id: str = field(default="", repr=False)
    llm_api_key: str = field(default="", repr=False)
    leetcode_username: str = ""
    github_repository: str = DEFAULT_REPOSITORY

    @property
    def log_path(self) -> Path:
        return self.root / "log.csv"

    @property
    def data_dir(self) -> Path:
        return self.root / "data"

    @property
    def problems_path(self) -> Path:
        return self.data_dir / "problems.json"

    @property
    def stats_history_path(self) -> Path:
        return self.data_dir / "stats_history.json"

    @property
    def greetings_path(self) -> Path:
        return self.data_dir / "greetings.json"

    @property
    def messages_dir(self) -> Path:
        return self.data_dir / "messages"

    @property
    def readme_path(self) -> Path:
        return self.root / "README.md"


def load_config(root: Path | None = None, env: dict[str, str] | None = None) -> Config:
    """Build a `Config` from `<root>/config.yaml` and the environment.

    When `env` is None the process environment is used, after loading
    `<root>/.env` if it exists.
    """
    root = root or ROOT
    if env is None:
        load_dotenv(root / ".env")
        env = dict(os.environ)
    raw = yaml.safe_load((root / "config.yaml").read_text(encoding="utf-8"))

    schedule = raw["schedule"]
    languages = raw["languages"]
    picker = raw["picker"]
    llm = raw["llm"]
    milestones = raw["milestones"]

    return Config(
        root=root,
        owner_name=str(raw["owner_name"]),
        timezone=ZoneInfo(raw["timezone"]),
        morning_local_hour=int(schedule["morning_local_hour"]),
        evening_local_hour=int(schedule["evening_local_hour"]),
        sync_every_hours=int(schedule["sync_every_hours"]),
        block_size=int(languages["block_size"]),
        language_cycle=[str(x) for x in languages["cycle"]],
        difficulty_by_weekday={int(k): str(v) for k, v in picker["difficulty_by_weekday"].items()},
        core_patterns=[str(x) for x in picker["core_patterns"]],
        acrate_ranges={str(k): (float(v[0]), float(v[1])) for k, v in picker["acrate_ranges"].items()},
        problems_cache_days=int(picker["problems_cache_days"]),
        llm_endpoint=str(llm["endpoint"]),
        llm_api_key_env=str(llm["api_key_env"]),
        llm_models=[str(x) for x in llm["models"]],
        llm_temperature=float(llm["temperature"]),
        llm_reasoning_effort=str(llm["reasoning_effort"]) if llm.get("reasoning_effort") else None,
        llm_max_output_tokens=int(llm.get("max_output_tokens", 4000)),
        llm_max_retries_per_model=int(llm["max_retries_per_model"]),
        milestone_solved_every=int(milestones["solved_every"]),
        milestone_streak_days=[int(x) for x in milestones["streak_days"]],
        reaction_on_solve=str(raw["telegram"]["reaction_on_solve"]),
        telegram_bot_token=env.get("TELEGRAM_BOT_TOKEN", "").strip(),
        telegram_chat_id=env.get("TELEGRAM_CHAT_ID", "").strip(),
        llm_api_key=env.get(str(llm["api_key_env"]), "").strip(),
        leetcode_username=env.get("LEETCODE_USERNAME", "").strip(),
        github_repository=env.get("GITHUB_REPOSITORY", "").strip() or DEFAULT_REPOSITORY,
    )
