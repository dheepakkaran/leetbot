# LeetCode Daily Bot

A serverless GitHub Actions bot that sends one LeetCode problem a day to Telegram, commits an AI-generated solution, and tracks when it gets solved.

> Work in progress. See [SPEC.md](SPEC.md) for the design.

## Local development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -q
```
