import os
from pathlib import Path

import pytest

from src.config import load_config, load_dotenv

REPO = Path(__file__).resolve().parent.parent


def test_dotenv_parser(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text('# c\nexport A_TEST_KEY="quoted value"\nB_TEST_KEY=plain\n\nEXISTING_TEST_KEY=new\n')
    monkeypatch.setenv("EXISTING_TEST_KEY", "old")
    monkeypatch.delenv("A_TEST_KEY", raising=False)
    monkeypatch.delenv("B_TEST_KEY", raising=False)
    load_dotenv(env_file)
    assert os.environ["A_TEST_KEY"] == "quoted value"
    assert os.environ["B_TEST_KEY"] == "plain"
    assert os.environ["EXISTING_TEST_KEY"] == "old"


def test_missing_dotenv_is_fine(tmp_path: Path) -> None:
    load_dotenv(tmp_path / ".env")


def test_config_loads() -> None:
    cfg = load_config(REPO, env={})
    assert cfg.owner_name == "Dheepak" and cfg.timezone.key == "America/New_York"
    assert cfg.difficulty_by_weekday[5] == "Hard" and cfg.acrate_ranges["Medium"] == (35.0, 75.0)
    assert cfg.language_cycle == ["cpp", "python", "java", "java", "python", "cpp"]
    assert cfg.github_repository == "dheepakkaran/leetcode-daily"
    assert cfg.reaction_on_solve == "💯"
    assert cfg.log_path == REPO / "log.csv"
    assert cfg.llm_endpoint == "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
    assert cfg.llm_api_key_env == "GEMINI_API_KEY" and cfg.llm_models[0] == "gemini-3.8-flash"
    assert cfg.llm_reasoning_effort == "medium" and cfg.llm_max_output_tokens == 16000


def test_secrets_come_from_env() -> None:
    cfg = load_config(REPO, env={
        "TELEGRAM_BOT_TOKEN": " SECRET-TG ", "TELEGRAM_CHAT_ID": "42", "GEMINI_API_KEY": "SECRET-GEM",
        "LEETCODE_USERNAME": "someone", "GITHUB_REPOSITORY": "me/fork",
    })
    assert (cfg.telegram_bot_token, cfg.telegram_chat_id, cfg.llm_api_key) == ("SECRET-TG", "42", "SECRET-GEM")
    assert cfg.leetcode_username == "someone" and cfg.github_repository == "me/fork"
    assert "SECRET" not in repr(cfg)  # secrets hidden from repr
