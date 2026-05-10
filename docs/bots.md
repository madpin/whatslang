# Writing bots

> A bot is a 7-line `BotSpec`. The runtime handles polling,
> deduplication, history, prefixes, response chunking, image OCR,
> Whisper transcription, and video → audio extraction.

This page is a *reference* (every field of `BotSpec`, every
`MediaMode`) and a *cookbook* (real prompts you can copy/paste).

---

## Table of contents

1. [The 7-line bot](#the-7-line-bot)
2. [`BotSpec` reference](#botspec-reference)
3. [The `MediaMode` enum](#the-mediamode-enum)
4. [Per-chat overrides (settings)](#per-chat-overrides-settings)
5. [Cookbook: ready-to-paste bots](#cookbook-ready-to-paste-bots)
6. [Prompt-engineering tips](#prompt-engineering-tips)
7. [Custom runners (advanced)](#custom-runners-advanced)
8. [Testing your bot](#testing-your-bot)
9. [Anti-patterns](#anti-patterns)

---

## The 7-line bot

Open `app/bots/__init__.py` and add:

```python
from app.bots.base import BotSpec, MediaMode, register

register(
    BotSpec(
        name="echo",
        label="Echo",
        prefix="[echo]",
        emoji="🔁",
        description="Repeats whatever you say, verbatim.",
        text_system_prompt=(
            "You are a polite echo. Repeat the user's text verbatim. "
            "Do not add anything."
        ),
    )
)
```

Restart the server. The bot is now in `/api/bots/types`, visible in the
dashboard, and ready to be assigned to any chat.

That's it. No threads, no polling loops, no media handling, no
deduplication, no settings UI.

---

## `BotSpec` reference

`BotSpec` is a frozen dataclass. Source:
[`app/bots/base.py`](../app/bots/base.py).

| Field | Type | Required? | Default | Purpose |
|---|---|---|---|---|
| `name` | `str` | yes | — | Unique key. Used in URLs (`/api/bots/{name}/start`) and DB (`bot_chat_assignments.bot_name`). Lowercase ASCII recommended. |
| `label` | `str` | yes | — | Human-friendly name shown in the dashboard ("EN ↔ PT Translator"). |
| `prefix` | `str` | yes | — | Tag prepended to every reply. Used to detect bot-on-bot loops — keep the `[xxx]` shape. |
| `description` | `str` | yes | — | One-paragraph description shown on the Bots page card. |
| `text_system_prompt` | `str` | yes | — | The system prompt for plain-text replies and the post-transcription LLM call. |
| `emoji` | `str` | no | `"🤖"` | Shown next to the label everywhere in the UI. |
| `image_prompt` | `str \| None` | no | `None` | If set, the bot **supports images** (vision). Sent as the user prompt with the image attachment. If `None`, image messages are ignored. |
| `media_mode` | `MediaMode` | no | `TRANSCRIBE_AND_REPLY` | How to handle audio + video. See below. |
| `translation_target_prompt` | `str \| None` | no | `None` | Used when `media_mode = TRANSCRIBE_AND_TRANSLATE`. Falls back to `text_system_prompt` if not set. |
| `metadata` | `dict[str, Any]` | no | `{}` | Free-form. Reserved for future use; ignored by the runtime today. |

Computed properties (no need to set):

| Property | Returns |
|---|---|
| `supports_text` | always `True` |
| `supports_image` | `True` iff `image_prompt is not None` |
| `supports_audio` | `True` iff `media_mode != IGNORE` |
| `supports_video` | `True` iff `media_mode != IGNORE` |

These end up in the `BotSupports` payload returned by
`/api/bots/types`, which the dashboard uses to render those little
text/image/audio/video chips.

---

## The `MediaMode` enum

```python
class MediaMode(str, Enum):
    IGNORE = "ignore"
    TRANSCRIBE_AND_TRANSLATE = "transcribe_translate"
    TRANSCRIBE_AND_REPLY = "transcribe_reply"   # default
```

| Value | Audio behaviour | Video behaviour | Reply shape |
|---|---|---|---|
| `IGNORE` | Skip. | Skip. | n/a |
| `TRANSCRIBE_AND_REPLY` | Whisper → feed transcript through `text_system_prompt`. | ffmpeg → audio → Whisper → same as audio. | `🎤 Transcription:\n<text>\n\n💬\n<reply>` |
| `TRANSCRIBE_AND_TRANSLATE` | Whisper → run `translation_target_prompt` (or `text_system_prompt` if missing) on the transcript. | Same. | `🎤 Transcription:\n<text>\n\n🌍 Translation:\n<output>` |

A few constraints worth knowing:

- **Video size cap**: 100 MB. The runner replies with a friendly error
  if the file is larger.
- **Audio length cap**: 25 MB after extraction. Same — friendly error.
- **No audio track on video**: friendly error.

---

## Per-chat overrides (settings)

Per `BotSpec`, the operator can change three things per chat:

| Field | Default | Effect |
|---|---|---|
| `answer_owner_messages` | `True` | If `False`, the bot ignores messages where `is_from_me=true`. |
| `context_message_count` | `0` | If `> 0`, the runner fetches that many previous messages and passes them as a chat history list to the LLM. The history is built from `WhatsAppClient.get_messages`. |
| `response_chat_jid` | `None` | If set, the bot forwards the original message **and** the reply to that JID instead of the source chat. |

These come from `bot_chat_assignments`. The runner reads them on every
message via `Database.get_assignment` — there's no caching, so changes
take effect on the next poll cycle.

The settings modal in the dashboard maps directly to
`PUT /api/bots/{name}/settings?chat_jid=…` (see [api.md](api.md)).

---

## Cookbook: ready-to-paste bots

Each block below is one `register(BotSpec(...))` call you can drop into
`app/bots/__init__.py`.

### 🌍 Spanish ↔ English translator (text + image OCR + audio)

```python
register(
    BotSpec(
        name="es_translator",
        label="ES ↔ EN Translator",
        prefix="[es-en]",
        emoji="🌎",
        description="Spanish ↔ English. Auto-detects direction. Handles text, OCR, voice.",
        text_system_prompt=(
            "You are a translation assistant.\n"
            "1. Detect if the text is Spanish or English.\n"
            "2. Translate to the OTHER language.\n"
            "3. Reply ONLY with the translation, no explanations."
        ),
        image_prompt=(
            "Find any text in the image.\n"
            "If text:\n"
            "  📝 Original: <verbatim>\n"
            "  🌍 Translation: <to the other of EN/ES>\n"
            "If no text:\n"
            "  📷 Contains: <one-sentence description>"
        ),
        media_mode=MediaMode.TRANSCRIBE_AND_TRANSLATE,
        translation_target_prompt=(
            "Translate the transcription to the OTHER of English/Spanish. "
            "Reply ONLY with the translation."
        ),
    )
)
```

### 📚 Summarizer (text-only, with history)

```python
register(
    BotSpec(
        name="summarizer",
        label="Summarizer",
        prefix="[sum]",
        emoji="📝",
        description="Summarizes the recent conversation in 5 bullet points.",
        text_system_prompt=(
            "You receive a conversation transcript followed by a user request.\n"
            "When the user says 'summary', 'recap' or 'resumen': produce 5 bullet "
            "points (≤120 chars each), plus a one-line action item. "
            "Otherwise: politely explain you only summarize on demand."
        ),
        media_mode=MediaMode.IGNORE,
    )
)
```

> Pair this with **Conversation context = 30** in the per-chat settings
> so it actually has something to summarise.

### 🍳 Recipe rescuer (vision-only nutrition)

```python
register(
    BotSpec(
        name="recipe_rescuer",
        label="Recipe Rescuer",
        prefix="[recipe]",
        emoji="🍳",
        description=(
            "Send a photo of what's in your fridge — get back 3 quick meal ideas "
            "with rough prep times."
        ),
        text_system_prompt=(
            "When the user asks in text without an image, ask them to send a "
            "photo of their fridge or pantry."
        ),
        image_prompt=(
            "You see a photo of food/ingredients.\n"
            "List the ingredients you can identify (max 10).\n"
            "Then propose 3 quick meal ideas: name, ingredients used, "
            "approx prep time. Match the user's language."
        ),
        media_mode=MediaMode.IGNORE,
    )
)
```

### 🤐 Confessions → admin chat (no reply in source)

```python
register(
    BotSpec(
        name="confessions",
        label="Confessions",
        prefix="[conf]",
        emoji="🤐",
        description=(
            "Listens silently in a chat and forwards every message to a moderator "
            "DM with a one-line tone analysis. Replies are sent to the moderator, "
            "not back to the chat."
        ),
        text_system_prompt=(
            "Read the user message. Reply with EXACTLY one line:\n"
            "Tone: <happy|sad|angry|neutral|joke|other> | Risk: <low|medium|high>\n"
            "Add a short note (<80 chars) only if Risk != low."
        ),
        media_mode=MediaMode.IGNORE,
    )
)
```

> Set the **Send replies to another chat** field in the per-chat
> settings to your moderator JID. The bot then forwards the original
> message + analysis to that chat instead of the source chat.

### 🏷 Voice-note titler (audio-only)

```python
register(
    BotSpec(
        name="voice_titler",
        label="Voice Titler",
        prefix="[title]",
        emoji="🏷",
        description="Listens to voice notes and replies with a snappy 5-word title.",
        text_system_prompt=(
            "You receive a transcription of a voice note. "
            "Reply with a 3-7 word title summarising it. "
            "No quotes, no punctuation at the end."
        ),
        media_mode=MediaMode.TRANSCRIBE_AND_REPLY,
    )
)
```

> Pair with `image_prompt=None` (default) so it ignores images.

---

## Prompt-engineering tips

Hard-won from the existing built-in bots:

- **Be ruthless about length.** WhatsApp on mobile loves short
  messages. Add "Reply with **only**…" or "**Maximum 3 lines.**" to
  your prompt.
- **Pin the language.** "Match the language of the user's message" is
  a great default. Otherwise the model defaults to English, which is
  often wrong on a Portuguese WhatsApp.
- **One job per bot.** A bot that translates *and* jokes is two bots.
  Keep prompts focused — your accuracy goes up and the per-chat
  settings (context, redirect) become meaningful.
- **Specify output shape.** For multimodal bots, give the model an
  exact template (`"📝 Original: ... 🌍 Translation: ..."`). Users
  tend to copy from those.
- **No greetings.** "Hi! Sure, here's…" eats characters. Add "No
  greetings, no apologies. Just answer."
- **Bot-on-bot guard.** The runner already filters messages starting
  with `[xxx]`. If you add a multi-line reply that starts with
  something else (like an emoji), other bots may try to answer it
  even if yours did. Best practice: keep your responses on one logical
  thread per chat (one bot per topic).

---

## Custom runners (advanced)

99% of bots only need a `BotSpec`. If you need bespoke logic — say,
calling another API, throttling per-user, or doing your own
deduplication — subclass `BotRunner` and override `process_message`.

```python
# app/bots/_advanced/karma.py
from typing import Any, Optional
from app.bots.base import BotRunner, BotSpec, register

KARMA = BotSpec(
    name="karma",
    label="Karma counter",
    prefix="[karma]",
    emoji="✨",
    description="Counts ++ and -- mentions per user in a chat.",
    text_system_prompt="(unused — runner overrides)",
)


class KarmaRunner(BotRunner):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.scores: dict[str, int] = {}

    def _produce_response(self, message: dict[str, Any], text: str) -> Optional[str]:
        # custom: ignore media entirely, parse "@name++"/"@name--" tokens
        import re
        delta = 0
        target = None
        m = re.search(r"@(\w+)\s*\+\+", text)
        if m:
            target, delta = m.group(1), 1
        m = re.search(r"@(\w+)\s*--", text)
        if m:
            target, delta = m.group(1), -1
        if not target or delta == 0:
            return None
        self.scores[target] = self.scores.get(target, 0) + delta
        return f"@{target} → {self.scores[target]}"


register(KARMA)

# Register the custom runner class so BotManager uses it instead of BotRunner.
# (Hook this in by extending BotManager or by giving BotSpec a runner field —
# both are small changes worth doing only if you actually need custom runners.)
```

> Today, `BotManager.start` always instantiates `BotRunner`. To wire a
> custom runner cleanly, the easiest extension is to add an optional
> `runner_factory: Callable[..., BotRunner]` to `BotSpec` and use it
> in `BotManager.start` if present. ~10 lines, all in `bot_manager.py`.

---

## Testing your bot

A quick local loop:

```bash
source .venv/bin/activate

# 1. Start backend in DEBUG so we see every gateway call.
LOG_LEVEL=DEBUG ENVIRONMENT=development python -m app

# In another shell:
# 2. Add a test chat (use a JID you own).
curl -s -X POST http://localhost:8000/api/chats \
  -H 'content-type: application/json' \
  -d '{"chat_jid":"12345@s.whatsapp.net","chat_name":"sandbox"}'

# 3. Start your new bot.
curl -s -X POST 'http://localhost:8000/api/bots/echo/start?chat_jid=12345@s.whatsapp.net'

# 4. Send yourself a message in WhatsApp. Within one poll interval,
#    Whatslang replies. Watch the logs:
curl -s 'http://localhost:8000/api/bots/echo/logs?chat_jid=12345@s.whatsapp.net' | jq
```

If you set `DASHBOARD_PASSWORD`, prepend `-b "whatslang_session=…"`
or just disable auth temporarily by leaving the password blank.

---

## Anti-patterns

- **One mega-bot that does everything.** You lose the per-chat
  settings story (context, redirect) and end up with prompt soup.
- **Letting one bot reply to another bot's reply.** It happens if
  your prefix isn't `[xxx]`-shaped. The first 20 characters must
  contain `[…]`.
- **Heavy synchronous work inside `_produce_response`.** Each tick is
  on a worker thread, so a 30-s call blocks that bot but doesn't
  block other bots — still, keep individual calls under a few seconds
  to avoid stacking.
- **Storing state on `self`.** Fine for in-process counters, but lost
  on every restart. For anything that must survive, use the database
  (`self.db.upsert_assignment(..., metadata=…)` after extending the
  schema, or make a new SQLite table).
- **Forgetting `prefix`.** Without it, the runner won't add a
  prefix, and other bots (or this same bot on the next tick) might
  try to answer your reply.
