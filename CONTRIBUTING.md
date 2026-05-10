# Contributing to Whatslang

Thanks for taking the time to help. This file is intentionally short — defer
to the README for architecture, and to the diff/PR for everything else.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e ".[dev]"
cd web && npm install
```

Run the backend with `make dev`, and the SPA with `make web-dev`.

## Adding a bot

1. Append a `BotSpec` to `app/bots/__init__.py`.
2. Write the `text_prompt` (and optional `image_prompt` / `audio_prompt` /
   `video_prompt`) in plain English.
3. Restart the server. The bot will appear in the dashboard catalogue.

That is the entire pipeline. The runner in `app/bots/base.py` handles
polling, history, media decoding, transcription, and message splitting.

## Quality bar

```bash
ruff format app          # auto-format Python
ruff check app           # lint
cd web && npm run typecheck
cd web && npm run build  # bundling sanity
```

PRs that run cleanly through the four commands above are easy to review.

## Commit messages

Conventional Commits, e.g. `feat: per-chat audio language override`,
`fix: avoid duplicate replies on retry`, `docs: clarify auth toggle`.

## Style notes

- Type hints in Python; explicit `from __future__ import annotations` is fine.
- Keep functions narrow; prefer pure helpers over deep classes.
- For the frontend, prefer composing the existing primitives in
  `web/src/components/ui/` rather than adding ad-hoc styles.

That's it. Open an issue if anything in the codebase is tripping you up.
