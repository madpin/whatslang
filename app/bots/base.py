"""Bot framework: declarative `BotSpec` + generic `BotRunner`.

Most bots only need a name, prefix and a couple of prompts. The runtime
handles polling, history, message dedup, owner-message gating and forwarding,
plus media (image / audio / video).
"""

from __future__ import annotations

import enum
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Optional

from app.db import Database
from app.services.llm import LLMService
from app.services.whatsapp import WhatsAppClient

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Spec / registry
# ---------------------------------------------------------------------------
class MediaMode(str, enum.Enum):
    """How the bot handles voice notes and videos.

    - IGNORE: Skip audio/video messages entirely.
    - TRANSCRIBE_AND_TRANSLATE: Transcribe with Whisper then run
      `translation_target_prompt` on the transcript. Reply contains both.
    - TRANSCRIBE_AND_REPLY: Transcribe with Whisper, then feed the transcript
      to the bot's text system prompt as if the user had typed it.
    """

    IGNORE = "ignore"
    TRANSCRIBE_AND_TRANSLATE = "transcribe_translate"
    TRANSCRIBE_AND_REPLY = "transcribe_reply"


@dataclass(frozen=True)
class BotSpec:
    """All-config bot definition.

    `text_system_prompt` is required. Set `image_prompt` to enable image
    handling; leave it None to ignore image messages. `media_mode` controls
    audio/video handling (defaults to TRANSCRIBE_AND_REPLY).
    """

    name: str
    label: str
    prefix: str
    description: str
    text_system_prompt: str
    emoji: str = "🤖"
    image_prompt: Optional[str] = None
    media_mode: MediaMode = MediaMode.TRANSCRIBE_AND_REPLY
    translation_target_prompt: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def supports_text(self) -> bool:
        return True

    @property
    def supports_image(self) -> bool:
        return bool(self.image_prompt)

    @property
    def supports_audio(self) -> bool:
        return self.media_mode is not MediaMode.IGNORE

    @property
    def supports_video(self) -> bool:
        return self.media_mode is not MediaMode.IGNORE


_REGISTRY: dict[str, BotSpec] = {}


def register(spec: BotSpec) -> BotSpec:
    """Add a bot to the global registry."""
    if spec.name in _REGISTRY:
        raise ValueError(f"Bot already registered: {spec.name}")
    _REGISTRY[spec.name] = spec
    return spec


def get_registry() -> dict[str, BotSpec]:
    return _REGISTRY


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _detect_media_type(message: dict[str, Any]) -> Optional[str]:
    """Return 'image' | 'audio' | 'video' if the message is media."""
    if mt := message.get("media_type"):
        return _normalize_media(str(mt))
    t = message.get("type")
    if t and t not in ("text", "chat", None):
        return _normalize_media(str(t))
    nested = message.get("message")
    if isinstance(nested, dict):
        if "imageMessage" in nested:
            return "image"
        if "audioMessage" in nested or "pttMessage" in nested:
            return "audio"
        if "videoMessage" in nested:
            return "video"
    mime = message.get("mimetype") or ""
    if mime.startswith("image/"):
        return "image"
    if mime.startswith("audio/"):
        return "audio"
    if mime.startswith("video/"):
        return "video"
    return None


def _normalize_media(value: str) -> Optional[str]:
    v = value.lower()
    if "image" in v:
        return "image"
    if "video" in v:
        return "video"
    if any(w in v for w in ("audio", "voice", "ptt")):
        return "audio"
    return None


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------
MAX_MESSAGE_LENGTH = 4095


class BotRunner:
    """One bot instance running for one chat."""

    def __init__(
        self,
        spec: BotSpec,
        *,
        whatsapp: WhatsAppClient,
        llm: LLMService,
        db: Database,
        chat_jid: str,
        bot_device_id: str,
        poll_interval: int = 5,
    ):
        self.spec = spec
        self.whatsapp = whatsapp
        self.llm = llm
        self.db = db
        self.chat_jid = chat_jid
        self.bot_device_id = bot_device_id
        self.poll_interval = poll_interval

        self._exit = False
        self._first_run = True
        self._log = logging.getLogger(f"bot.{spec.name}")

    # ------------------------------------------------------------------
    # Public lifecycle
    # ------------------------------------------------------------------
    def stop(self) -> None:
        self._exit = True

    def run(self) -> None:
        self._log.info("Bot %s starting for chat %s", self.spec.name, self.chat_jid)
        while not self._exit:
            try:
                self._tick()
            except Exception as e:  # pragma: no cover - defensive
                self._log.exception("Loop error: %s", e)
            for _ in range(self.poll_interval * 4):  # responsive shutdown
                if self._exit:
                    break
                time.sleep(0.25)
        self._log.info("Bot %s stopped", self.spec.name)

    # ------------------------------------------------------------------
    # Core loop
    # ------------------------------------------------------------------
    def _tick(self) -> None:
        messages = self.whatsapp.get_messages(self.chat_jid, limit=20)
        if not messages:
            return

        if self._first_run:
            for msg in messages:
                mid = msg.get("id")
                if mid and not self.db.is_processed(mid, self.spec.name):
                    self.db.mark_processed(
                        mid, self.spec.name, original_text="(seen at startup)", metadata="startup"
                    )
            self._first_run = False
            return

        # Process oldest → newest.
        for msg in reversed(messages):
            if self._exit:
                return
            if self._should_process(msg):
                self._handle(msg)
                time.sleep(0.5)

    def _should_process(self, message: dict[str, Any]) -> bool:
        mid = message.get("id")
        if not mid or self.db.is_processed(mid, self.spec.name):
            return False
        text = message.get("content", "")
        if not text and _detect_media_type(message) is None:
            return False
        # Skip messages from bots (own device).
        sender = message.get("sender_jid") or message.get("from") or message.get("sender") or ""
        if sender and self.whatsapp.is_bot_sender(sender, self.bot_device_id):
            return False
        # Skip any message starting with a [..] bot prefix (avoid bot-on-bot loops).
        if text and text.startswith("[") and "]" in text[:20]:
            return False
        # Respect "answer owner messages" toggle.
        if message.get("is_from_me"):
            assignment = self.db.get_assignment(self.spec.name, self.chat_jid) or {}
            if not bool(assignment.get("answer_owner_messages", 1)):
                return False
        return True

    # ------------------------------------------------------------------
    # Handle one message
    # ------------------------------------------------------------------
    def _handle(self, message: dict[str, Any]) -> None:
        mid = message.get("id") or ""
        text = message.get("content", "")
        ts = message.get("timestamp") or message.get("time")
        self.db.update_message_activity(self.chat_jid, message_time=ts)

        try:
            response = self._produce_response(message, text)
        except Exception as e:  # pragma: no cover
            self._log.exception("Bot %s failed: %s", self.spec.name, e)
            return

        if not response:
            self.db.mark_processed(mid, self.spec.name, original_text=text, response_text="(no response)")
            return

        self._send_response(message, response)

    def _produce_response(self, message: dict[str, Any], text: str) -> Optional[str]:
        media = _detect_media_type(message)
        if media == "image" and self.spec.supports_image:
            return self._handle_image(message)
        if media == "audio" and self.spec.supports_audio:
            return self._handle_audio(message)
        if media == "video" and self.spec.supports_video:
            return self._handle_video(message)
        if text:
            history = self._maybe_history(message)
            return self._reply_to_text(text, history)
        return None

    # --- text -----------------------------------------------------------
    def _reply_to_text(self, text: str, history: Optional[list[dict[str, Any]]]) -> Optional[str]:
        if history:
            return self.llm.call_with_history(self.spec.text_system_prompt, text, history)
        return self.llm.call(self.spec.text_system_prompt, text)

    def _maybe_history(self, message: dict[str, Any]) -> Optional[list[dict[str, Any]]]:
        assignment = self.db.get_assignment(self.spec.name, self.chat_jid) or {}
        count = int(assignment.get("context_message_count", 0) or 0)
        if count <= 0:
            return None
        try:
            messages = self.whatsapp.get_messages(self.chat_jid, limit=count + 10)
        except Exception:
            return None
        cur_id = message.get("id")
        history: list[dict[str, Any]] = []
        for m in messages:
            if m.get("id") == cur_id:
                continue
            content = m.get("content")
            if not content:
                continue
            is_bot = bool(content.startswith("[") and "]" in content[:20])
            history.append(
                {
                    "content": content,
                    "sender": m.get("sender_jid") or m.get("from") or m.get("sender") or "",
                    "is_from_me": bool(m.get("is_from_me")),
                    "is_bot": is_bot,
                }
            )
            if len(history) >= count:
                break
        history.reverse()
        return history

    # --- image ----------------------------------------------------------
    def _handle_image(self, message: dict[str, Any]) -> Optional[str]:
        mid = message.get("id") or ""
        data = self.whatsapp.download_image(mid, self.chat_jid)
        if not data:
            return "❌ Couldn't download the image."
        result = self.llm.call_with_image(self.spec.image_prompt or "Describe this image.", data)
        return result or "❌ Couldn't analyse the image, please try again."

    # --- audio / video --------------------------------------------------
    def _handle_audio(self, message: dict[str, Any]) -> Optional[str]:
        mid = message.get("id") or ""
        data = self.whatsapp.download_audio(mid, self.chat_jid)
        if not data:
            return "❌ Couldn't download the voice message."
        return self._transcribe_and_reply(data, prefix="🎤 Transcription")

    def _handle_video(self, message: dict[str, Any]) -> Optional[str]:
        mid = message.get("id") or ""
        video = self.whatsapp.download_video(mid, self.chat_jid)
        if not video:
            return "❌ Couldn't download the video."
        if len(video) > 100 * 1024 * 1024:
            return "❌ Video is too large (over 100 MB). Please send a shorter clip."
        audio = self.llm.extract_audio_from_video(video)
        if not audio:
            return "❌ This video has no audio track, or I couldn't extract it."
        if len(audio) > 25 * 1024 * 1024:
            return "❌ The video's audio is too long for transcription. Please send a shorter clip."
        return self._transcribe_and_reply(audio, prefix="🎬 Video transcription")

    def _transcribe_and_reply(self, audio_bytes: bytes, *, prefix: str) -> Optional[str]:
        transcription = self.llm.transcribe_audio(audio_bytes)
        if not transcription:
            return "❌ Couldn't transcribe the audio. Please try again."
        if self.spec.media_mode is MediaMode.TRANSCRIBE_AND_TRANSLATE:
            target_prompt = self.spec.translation_target_prompt or self.spec.text_system_prompt
            translation = self.llm.call(target_prompt, transcription)
            if not translation:
                return f"{prefix}:\n{transcription}\n\n⚠️ Translation unavailable right now."
            return f"{prefix}:\n{transcription}\n\n🌍 Translation:\n{translation}"
        # TRANSCRIBE_AND_REPLY: feed transcript through the text prompt.
        reply = self.llm.call(self.spec.text_system_prompt, transcription)
        if not reply:
            return f"{prefix}:\n{transcription}"
        return f"{prefix}:\n{transcription}\n\n💬\n{reply}"

    # ------------------------------------------------------------------
    # Sending
    # ------------------------------------------------------------------
    def _send_response(self, message: dict[str, Any], response: str) -> None:
        mid = message.get("id") or ""
        text = message.get("content", "")
        assignment = self.db.get_assignment(self.spec.name, self.chat_jid) or {}
        forward_to = assignment.get("response_chat_jid") or None
        target = forward_to or self.chat_jid

        # Forward original context if needed.
        if forward_to:
            sender = message.get("push_name") or message.get("pushName") or "someone"
            preview = text or "[media]"
            ok = self.whatsapp.send_message(forward_to, f"[Fwd from {sender}]: {preview}")
            if not ok:
                self._log.error("Forward of original to %s failed", forward_to)
                return
            time.sleep(0.4)

        chunks = self._split_message(response)
        for i, chunk in enumerate(chunks, 1):
            reply_id = mid if not forward_to else None
            ok = self.whatsapp.send_message(target, chunk, reply_message_id=reply_id)
            if not ok:
                self._log.error("Failed to send chunk %d/%d for message %s", i, len(chunks), mid)
                return
            time.sleep(0.4)

        self.db.mark_processed(
            mid,
            self.spec.name,
            original_text=text,
            response_text=response[:500],
            metadata=f"forwarded_to={forward_to}" if forward_to else "",
        )
        self._log.info("Replied to %s (%d chunks)", mid, len(chunks))

    def _split_message(self, text: str) -> list[str]:
        prefix = self.spec.prefix
        header = f"{prefix} 999/999 "
        max_content = MAX_MESSAGE_LENGTH - len(header) - 1
        if len(text) <= max_content:
            return [f"{prefix} {text}"]

        chunks: list[str] = []
        remaining = text
        while remaining:
            if len(remaining) <= max_content:
                chunks.append(remaining)
                break
            cut = max_content
            for i in range(max_content - 1, max(0, max_content - 200), -1):
                if remaining[i] in ".!?\n":
                    cut = i + 1
                    break
            else:
                for i in range(max_content - 1, max(0, max_content - 100), -1):
                    if remaining[i] == " ":
                        cut = i + 1
                        break
            chunks.append(remaining[:cut].rstrip())
            remaining = remaining[cut:].lstrip()
        total = len(chunks)
        return [f"{prefix} {i+1}/{total} {c}" for i, c in enumerate(chunks)]
