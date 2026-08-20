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
from datetime import datetime, timezone
from typing import Any, Optional

from app.db import Database
from app.services.llm import LLMService
from app.services.whatsapp import WhatsAppClient

logger = logging.getLogger(__name__)


def _ts_to_iso(value: Any) -> Optional[str]:
    """Best-effort convert a gateway timestamp to ISO 8601 UTC.

    The WhatsApp gateway exposes timestamps in several shapes depending
    on the endpoint and version: epoch seconds (int / float / str), ISO
    strings, or RFC3339 with ``Z``. Return ``None`` on anything we can't
    parse so the caller falls back to "now" semantics.
    """
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value), tz=timezone.utc).isoformat(
                timespec="seconds"
            )
        except (OSError, OverflowError, ValueError):
            return None
    if isinstance(value, str):
        s = value.strip()
        # Pure-numeric strings → epoch seconds.
        if s.replace(".", "", 1).isdigit():
            try:
                return datetime.fromtimestamp(float(s), tz=timezone.utc).isoformat(
                    timespec="seconds"
                )
            except (OSError, OverflowError, ValueError):
                return None
        # ISO-ish strings (Z suffix is not understood by fromisoformat
        # before Python 3.11).
        try:
            return datetime.fromisoformat(s.replace("Z", "+00:00")).isoformat(
                timespec="seconds"
            )
        except ValueError:
            return s
    return None


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
    """Return ``'image' | 'audio' | 'video'`` if the message is media that
    a bot can act on. Documents / stickers / other types intentionally
    return ``None`` so the runner falls through to text handling.
    """
    return _classify_for_bot(_classify_message(message))


def _classify_message(message: dict[str, Any]) -> str:
    """Coarse-classify any inbound message into a single string type.

    Used both by the bot runner (which only acts on a subset) and by
    the diagnostics tracker (which records *every* observed message
    regardless of whether a bot would act on it).

    Possible return values: ``text``, ``image``, ``audio``, ``video``,
    ``document``, ``sticker``, ``other``.
    """
    if mt := message.get("media_type"):
        kind = _normalize_media(str(mt))
        if kind:
            return kind
    t = message.get("type")
    if isinstance(t, str):
        kind = _normalize_media(t)
        if kind:
            return kind
        if t.lower() in ("text", "chat"):
            return "text"
    nested = message.get("message")
    if isinstance(nested, dict):
        if "imageMessage" in nested:
            return "image"
        if "audioMessage" in nested or "pttMessage" in nested:
            return "audio"
        if "videoMessage" in nested:
            return "video"
        if "documentMessage" in nested:
            return "document"
        if "stickerMessage" in nested:
            return "sticker"
        if "conversation" in nested or "extendedTextMessage" in nested:
            return "text"
    mime = message.get("mimetype") or ""
    if mime.startswith("image/"):
        return "image"
    if mime.startswith("audio/"):
        return "audio"
    if mime.startswith("video/"):
        return "video"
    if mime.startswith("application/"):
        return "document"
    if message.get("content"):
        return "text"
    return "other"


def _classify_for_bot(kind: str) -> Optional[str]:
    """Reduce the diagnostic classification to the subset the bot acts on."""
    if kind in ("image", "audio", "video"):
        return kind
    return None


def _is_from_me(message: dict[str, Any]) -> bool:
    return bool(message.get("is_from_me"))


def _normalize_media(value: str) -> Optional[str]:
    v = value.lower()
    if "image" in v or "photo" in v:
        return "image"
    if "video" in v:
        return "video"
    if any(w in v for w in ("audio", "voice", "ptt")):
        return "audio"
    if "document" in v or "file" in v:
        return "document"
    if "sticker" in v:
        return "sticker"
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
        target_whatsapp: Optional[WhatsAppClient] = None,
        source_device_id: str = "",
        target_device_id: str = "",
        poll_interval: int = 5,
    ):
        self.spec = spec
        # ``whatsapp`` is the *source* client — the account we read the chat
        # from. ``target_whatsapp`` is the account we send replies with; it
        # defaults to the source so single-device setups are unchanged.
        self.whatsapp = whatsapp
        self.target_whatsapp = target_whatsapp or whatsapp
        self.llm = llm
        self.db = db
        self.chat_jid = chat_jid
        self.bot_device_id = bot_device_id
        self.source_device_id = source_device_id
        self.target_device_id = target_device_id
        # Quoting a message id only works when the reply goes back through the
        # same account and chat that produced it.
        self.same_device = source_device_id == target_device_id
        self.poll_interval = poll_interval

        self._exit = False
        self._first_run = True
        self._log = logging.getLogger(f"bot.{spec.name}")

    # ------------------------------------------------------------------
    # Public lifecycle
    # ------------------------------------------------------------------
    def stop(self) -> None:
        self._exit = True

    def configure_devices(
        self,
        *,
        whatsapp: WhatsAppClient,
        target_whatsapp: WhatsAppClient,
        bot_device_id: str,
        source_device_id: str,
        target_device_id: str,
    ) -> None:
        source_changed = source_device_id != self.source_device_id
        self.whatsapp = whatsapp
        self.target_whatsapp = target_whatsapp
        self.bot_device_id = bot_device_id
        self.source_device_id = source_device_id
        self.target_device_id = target_device_id
        self.same_device = source_device_id == target_device_id
        if source_changed:
            self._first_run = True

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

        # Always record diagnostics observations — even on the first run
        # and even for messages a bot would skip. This is what powers the
        # "last image / audio / video / text observed at" panel; without
        # it, you couldn't tell whether silence is "no traffic" or "the
        # gateway / database broke".
        for msg in messages:
            self._observe(msg)

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

    def _observe(self, message: dict[str, Any]) -> None:
        """Best-effort: log every distinct message-id into ``inbound_observations``.

        Failures are swallowed — a broken DB write must never stop the
        bot from doing its real job.
        """
        mid = message.get("id")
        if not mid:
            return
        try:
            kind = _classify_message(message)
            sender = (
                message.get("sender_jid")
                or message.get("from")
                or message.get("sender")
                or message.get("push_name")
            )
            ts = _ts_to_iso(message.get("timestamp") or message.get("time"))
            self.db.observe_inbound(
                str(mid),
                media_type=kind,
                chat_jid=self.chat_jid,
                sender=str(sender) if sender else None,
                occurred_at=ts,
            )
        except Exception:  # pragma: no cover - defensive
            self._log.debug("observe_inbound failed", exc_info=True)

    def _should_process(self, message: dict[str, Any]) -> bool:
        mid = message.get("id")
        if not mid or self.db.is_processed(mid, self.spec.name):
            return False
        text = message.get("content", "")
        media = _detect_media_type(message)
        if not text and media is None:
            return False
        # Skip messages from bots (own device).
        sender = message.get("sender_jid") or message.get("from") or message.get("sender") or ""
        if (
            sender
            and not _is_from_me(message)
            and self.whatsapp.is_bot_sender(sender, self.bot_device_id)
        ):
            return False
        # Skip any message starting with a [..] bot prefix (avoid bot-on-bot loops).
        if text and text.startswith("[") and "]" in text[:20]:
            return False
        # Respect "answer owner messages" toggle.
        if _is_from_me(message):
            assignment = self.db.get_assignment(self.spec.name, self.chat_jid) or {}
            if not bool(assignment.get("answer_owner_messages", 1)):
                return False
            # GoWA can expose self-sent media rows without enough decryptable
            # metadata for /message/{id}/download. Empty owner media would
            # otherwise create a permanent gateway 500 on every fresh send.
            if media and not text:
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
        caption = (text or "").strip()
        if media and _is_from_me(message):
            if not caption:
                return None
            self._log.info(
                "Treating caption on self-sent %s message %s as text only",
                media,
                message.get("id") or "",
            )
            media = None
        if media == "image" and self.spec.supports_image:
            return self._handle_image(message, caption)
        if media == "audio" and self.spec.supports_audio:
            return self._handle_audio(message, caption)
        if media == "video" and self.spec.supports_video:
            return self._handle_video(message, caption)
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
    def _handle_image(self, message: dict[str, Any], caption: str = "") -> Optional[str]:
        mid = message.get("id") or ""
        data = self.whatsapp.download_image(mid, self.chat_jid)
        if not data:
            return "❌ Couldn't download the image."
        prompt = self.spec.image_prompt or "Describe this image."
        user_text: Optional[str] = None
        if caption:
            user_text = (
                "A caption was sent together with this image:\n"
                f'"""\n{caption}\n"""\n'
                "Treat the caption as additional source text: apply the same rules "
                "to it that you apply to text found inside the image, and include "
                "both the image text/description AND the caption (with its "
                "translation, if your role is translation) in your reply under "
                "clearly labelled sections."
            )
        result = self.llm.call_with_image(prompt, data, user_text=user_text)
        return result or "❌ Couldn't analyse the image, please try again."

    # --- audio / video --------------------------------------------------
    def _handle_audio(self, message: dict[str, Any], caption: str = "") -> Optional[str]:
        mid = message.get("id") or ""
        data = self.whatsapp.download_audio(mid, self.chat_jid)
        if not data:
            return "❌ Couldn't download the voice message."
        return self._transcribe_and_reply(data, prefix="🎤 Transcription", caption=caption)

    def _handle_video(self, message: dict[str, Any], caption: str = "") -> Optional[str]:
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
        return self._transcribe_and_reply(audio, prefix="🎬 Video transcription", caption=caption)

    def _transcribe_and_reply(
        self, audio_bytes: bytes, *, prefix: str, caption: str = ""
    ) -> Optional[str]:
        transcription = self.llm.transcribe_audio(audio_bytes)
        if not transcription:
            return "❌ Couldn't transcribe the audio. Please try again."
        if self.spec.media_mode is MediaMode.TRANSCRIBE_AND_TRANSLATE:
            target_prompt = self.spec.translation_target_prompt or self.spec.text_system_prompt
            translation = self.llm.call(target_prompt, transcription)
            if translation:
                body = f"{prefix}:\n{transcription}\n\n🌍 Translation:\n{translation}"
            else:
                body = f"{prefix}:\n{transcription}\n\n⚠️ Translation unavailable right now."
            if caption:
                cap_translation = self.llm.call(
                    self.spec.text_system_prompt, caption
                )
                if cap_translation:
                    body += (
                        f"\n\n✉️ Caption:\n{caption}\n🌍 Caption translation:\n{cap_translation}"
                    )
                else:
                    body += f"\n\n✉️ Caption:\n{caption}\n⚠️ Caption translation unavailable right now."
            return body
        # TRANSCRIBE_AND_REPLY: feed transcript (and caption) through the text prompt.
        if caption:
            combined = f"{transcription}\n\n[Caption sent with the media]: {caption}"
        else:
            combined = transcription
        reply = self.llm.call(self.spec.text_system_prompt, combined)
        head = f"{prefix}:\n{transcription}"
        if caption:
            head += f"\n\n✉️ Caption:\n{caption}"
        if not reply:
            return head
        return f"{head}\n\n💬\n{reply}"

    # ------------------------------------------------------------------
    # Sending
    # ------------------------------------------------------------------
    def _send_response(self, message: dict[str, Any], response: str) -> None:
        mid = message.get("id") or ""
        text = message.get("content", "")
        assignment = self.db.get_assignment(self.spec.name, self.chat_jid) or {}
        forward_to = assignment.get("response_chat_jid") or None
        target = forward_to or self.chat_jid

        # Forward original context if needed. Sent with the *target* account
        # (the reply device), which may differ from the one we read from.
        if forward_to:
            sender = message.get("push_name") or message.get("pushName") or "someone"
            preview = text or "[media]"
            ok = self.target_whatsapp.send_message(forward_to, f"[Fwd from {sender}]: {preview}")
            if not ok:
                self._log.error("Forward of original to %s failed", forward_to)
                return
            time.sleep(0.4)

        # A reply can only quote the original when it's going back to the same
        # chat *and* through the same account (the message id is scoped to the
        # account that observed it).
        can_quote = not forward_to and self.same_device
        chunks = self._split_message(response)
        for i, chunk in enumerate(chunks, 1):
            reply_id = mid if can_quote else None
            ok = self.target_whatsapp.send_message(target, chunk, reply_message_id=reply_id)
            if not ok:
                self._log.error("Failed to send chunk %d/%d for message %s", i, len(chunks), mid)
                return
            time.sleep(0.4)

        route = ""
        if self.source_device_id != self.target_device_id:
            route = f" via {self.source_device_id or 'default'}→{self.target_device_id or 'default'}"
        self.db.mark_processed(
            mid,
            self.spec.name,
            original_text=text,
            response_text=response[:500],
            metadata=(f"forwarded_to={forward_to}" if forward_to else "") + route,
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
