"""LLM service: text, vision and audio (Whisper) calls.

In addition to wrapping the OpenAI client, this module keeps a small
per-surface activity tracker (text / vision / audio / video) so the
diagnostics page can show "last text reply at", "last whisper call at",
counts and the most recent error message even when the application logs
get rotated or are inaccessible.
"""

from __future__ import annotations

import base64
import contextlib
import io
import logging
import os
import random
import tempfile
import threading
import time
from datetime import datetime, timezone
from typing import Any, Optional

from openai import OpenAI

logger = logging.getLogger(__name__)


# Names match the ``LLMService.activity`` keys exposed by ``snapshot``
# and rendered on the diagnostics page.
LLM_SURFACES: tuple[str, ...] = ("text", "vision", "audio", "video")


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _detect_image_mime(data: bytes) -> Optional[str]:
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"GIF87a") or data.startswith(b"GIF89a"):
        return "image/gif"
    if data.startswith(b"RIFF") and b"WEBP" in data[:20]:
        return "image/webp"
    return None


def _detect_audio_format(data: bytes) -> str:
    if data.startswith(b"ID3") or data.startswith(b"\xff\xfb") or data.startswith(b"\xff\xf3"):
        return "mp3"
    if data.startswith(b"OggS"):
        return "ogg"
    if data.startswith(b"RIFF") and b"WAVE" in data[:20]:
        return "wav"
    if data.startswith(b"\x00\x00\x00") and b"ftyp" in data[:20]:
        return "m4a"
    if data.startswith(b"\x1aE\xdf\xa3"):
        return "webm"
    return "ogg"  # WhatsApp voice notes are typically ogg/opus


class LLMService:
    """Wraps OpenAI/LiteLLM for chat, vision, and audio."""

    def __init__(
        self,
        api_key: str,
        *,
        model: str = "gpt-4o-mini",
        base_url: Optional[str] = None,
        vision_model: Optional[str] = None,
        audio_model: str = "whisper-1",
    ):
        self.client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
        self.model = model
        self.vision_model = vision_model or model
        self.audio_model = audio_model

        # Per-surface activity tracker. ``last_*_at`` is set on every
        # *attempt* (so we know we tried), ``last_success_at`` only on a
        # success, and ``last_error_at`` only on a failure. The
        # diagnostics page colour-codes by staleness of those.
        self._activity_lock = threading.Lock()
        self._activity: dict[str, dict[str, Any]] = {
            kind: {
                "model": self._model_for(kind),
                "call_count": 0,
                "success_count": 0,
                "error_count": 0,
                "last_call_at": None,
                "last_success_at": None,
                "last_error_at": None,
                "last_error_message": None,
                "last_latency_ms": None,
            }
            for kind in LLM_SURFACES
        }

        logger.info(
            "LLMService ready (text=%s, vision=%s, audio=%s)",
            self.model,
            self.vision_model,
            self.audio_model,
        )

    # ------------------------------------------------------------------
    # Tracking helpers
    # ------------------------------------------------------------------
    def _model_for(self, surface: str) -> Optional[str]:
        if surface == "text":
            return self.model
        if surface == "vision":
            return self.vision_model
        if surface == "audio":
            return self.audio_model
        if surface == "video":
            # Video extraction goes through ffmpeg locally and then
            # whisper for the transcription. The "model" the operator
            # cares about for the video surface is whisper.
            return self.audio_model
        return None

    def _record_call(
        self,
        surface: str,
        *,
        success: bool,
        latency_ms: int,
        error: Optional[BaseException] = None,
    ) -> None:
        if surface not in LLM_SURFACES:
            return
        ts = _utc_iso()
        with self._activity_lock:
            row = self._activity[surface]
            row["call_count"] += 1
            row["last_call_at"] = ts
            row["last_latency_ms"] = latency_ms
            if success:
                row["success_count"] += 1
                row["last_success_at"] = ts
            else:
                row["error_count"] += 1
                row["last_error_at"] = ts
                if error is not None:
                    row["last_error_message"] = str(error)[:200]

    def activity_snapshot(self) -> list[dict[str, Any]]:
        """Return per-surface activity rows, in canonical order."""
        with self._activity_lock:
            return [
                {"surface": kind, **dict(self._activity[kind])}
                for kind in LLM_SURFACES
            ]

    # ------------------------------------------------------------------
    # Text
    # ------------------------------------------------------------------
    def call(self, system_prompt: str, user_text: str = "") -> Optional[str]:
        t0 = time.perf_counter()
        try:
            messages = [{"role": "system", "content": system_prompt}]
            if user_text:
                messages.append({"role": "user", "content": user_text})
            r = self.client.chat.completions.create(model=self.model, messages=messages)
            content = r.choices[0].message.content
            self._record_call(
                "text", success=True, latency_ms=int((time.perf_counter() - t0) * 1000)
            )
            return content.strip() if content else None
        except Exception as e:
            self._record_call(
                "text",
                success=False,
                latency_ms=int((time.perf_counter() - t0) * 1000),
                error=e,
            )
            logger.error("LLM text call failed: %s", e)
            return None

    def call_with_history(
        self,
        system_prompt: str,
        current_message: str,
        history: list[dict[str, Any]],
    ) -> Optional[str]:
        t0 = time.perf_counter()
        try:
            messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
            for msg in history:
                content = msg.get("content")
                if not content:
                    continue
                role = "assistant" if (msg.get("is_bot") or msg.get("is_from_me")) else "user"
                sender = msg.get("sender") or "user"
                messages.append({"role": role, "content": f"[{sender}]: {content}"})
            messages.append({"role": "user", "content": current_message})
            r = self.client.chat.completions.create(model=self.model, messages=messages)
            content = r.choices[0].message.content
            self._record_call(
                "text", success=True, latency_ms=int((time.perf_counter() - t0) * 1000)
            )
            return content.strip() if content else None
        except Exception as e:
            self._record_call(
                "text",
                success=False,
                latency_ms=int((time.perf_counter() - t0) * 1000),
                error=e,
            )
            logger.error("LLM history call failed: %s", e)
            return None

    # ------------------------------------------------------------------
    # Vision
    # ------------------------------------------------------------------
    def call_with_image(self, prompt: str, image_bytes: bytes) -> Optional[str]:
        mime = _detect_image_mime(image_bytes)
        if not mime:
            self._record_call(
                "vision",
                success=False,
                latency_ms=0,
                error=RuntimeError("unsupported image format"),
            )
            logger.error("Unsupported image format")
            return None
        data_url = f"data:{mime};base64,{base64.b64encode(image_bytes).decode()}"
        t0 = time.perf_counter()
        try:
            r = self.client.chat.completions.create(
                model=self.vision_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": data_url}},
                        ],
                    }
                ],
            )
            content = r.choices[0].message.content
            self._record_call(
                "vision",
                success=True,
                latency_ms=int((time.perf_counter() - t0) * 1000),
            )
            return content.strip() if content else None
        except Exception as e:
            self._record_call(
                "vision",
                success=False,
                latency_ms=int((time.perf_counter() - t0) * 1000),
                error=e,
            )
            logger.error("LLM vision call failed: %s", e)
            return None

    # ------------------------------------------------------------------
    # Audio
    # ------------------------------------------------------------------
    def transcribe_audio(self, audio_bytes: bytes, language: Optional[str] = None) -> Optional[str]:
        if len(audio_bytes) > 25 * 1024 * 1024:
            self._record_call(
                "audio",
                success=False,
                latency_ms=0,
                error=RuntimeError(f"audio too large: {len(audio_bytes)} bytes"),
            )
            logger.error("Audio too large for Whisper API: %d bytes", len(audio_bytes))
            return None
        fmt = _detect_audio_format(audio_bytes)
        delays = [2, 4, 8]
        last_err: Optional[BaseException] = None
        t0 = time.perf_counter()
        for attempt in range(3):
            try:
                buf = io.BytesIO(audio_bytes)
                buf.name = f"audio_{int(time.time()*1000)}_{random.randint(1000, 9999)}.{fmt}"
                params: dict[str, Any] = {"model": self.audio_model, "file": buf}
                if language:
                    params["language"] = language
                r = self.client.audio.transcriptions.create(**params)
                text = (r.text or "").strip()
                self._record_call(
                    "audio",
                    success=True,
                    latency_ms=int((time.perf_counter() - t0) * 1000),
                )
                return text or None
            except Exception as e:
                last_err = e
                msg = str(e).lower()
                if any(k in msg for k in ("invalid", "unsupported", "format", "codec")):
                    logger.error("Whisper permanent error: %s", e)
                    break
                if attempt < 2:
                    time.sleep(delays[attempt])
                else:
                    logger.error("Whisper failed after retries: %s", e)
        self._record_call(
            "audio",
            success=False,
            latency_ms=int((time.perf_counter() - t0) * 1000),
            error=last_err,
        )
        return None

    def extract_audio_from_video(self, video_bytes: bytes) -> Optional[bytes]:
        """Extract a 16kHz mono mp3 audio track from a video using ffmpeg."""
        t0 = time.perf_counter()
        try:
            import ffmpeg  # type: ignore[import-untyped]
        except ImportError as e:
            self._record_call("video", success=False, latency_ms=0, error=e)
            logger.error("ffmpeg-python not installed; cannot process video")
            return None

        vid_path = aud_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                tmp.write(video_bytes)
                vid_path = tmp.name
            fd, aud_path = tempfile.mkstemp(suffix=".mp3")
            os.close(fd)
            try:
                (
                    ffmpeg.input(vid_path)
                    .output(
                        aud_path,
                        acodec="libmp3lame",
                        ac=1,
                        ar="16000",
                        audio_bitrate="64k",
                    )
                    .overwrite_output()
                    .run(capture_stdout=True, capture_stderr=True, quiet=True)
                )
            except ffmpeg.Error as e:
                msg = e.stderr.decode("utf-8", errors="ignore") if e.stderr else str(e)
                if "does not contain any stream" in msg or "Output file is empty" in msg:
                    logger.warning("Video has no audio stream")
                else:
                    logger.error("ffmpeg failed: %s", msg)
                self._record_call(
                    "video",
                    success=False,
                    latency_ms=int((time.perf_counter() - t0) * 1000),
                    error=RuntimeError(msg[:200]),
                )
                return None
            if not os.path.exists(aud_path) or os.path.getsize(aud_path) == 0:
                self._record_call(
                    "video",
                    success=False,
                    latency_ms=int((time.perf_counter() - t0) * 1000),
                    error=RuntimeError("ffmpeg produced empty audio"),
                )
                return None
            with open(aud_path, "rb") as f:
                data = f.read()
            self._record_call(
                "video",
                success=True,
                latency_ms=int((time.perf_counter() - t0) * 1000),
            )
            return data
        finally:
            for p in (vid_path, aud_path):
                if p and os.path.exists(p):
                    with contextlib.suppress(OSError):
                        os.unlink(p)
