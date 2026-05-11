"""Tests for the new diagnostics surfaces.

These cover:

- ``Database.observe_inbound`` deduplicates by ``message_id`` (so multiple
  bots watching the same chat don't inflate the counters), keeps
  ``last_seen_at`` monotonic, and exposes one row per canonical media type.
- ``LLMService`` tracks per-surface (text / vision / audio / video) calls,
  successes and errors regardless of whether the underlying API succeeded.
- ``GET /api/diagnostics`` returns the new ``llm.surfaces`` and
  ``inbound`` arrays in the right shape.
- ``BotRunner._observe`` is a best-effort write — exceptions inside the
  observation path must not stop bots from doing real work.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.bots.base import BotRunner, BotSpec, _classify_message, _ts_to_iso
from app.db import Database
from app.services.llm import LLMService

# ----------------------------------------------------------------------
# observe_inbound
# ----------------------------------------------------------------------


def test_list_inbound_returns_all_canonical_types_when_empty(tmp_path: Path) -> None:
    db = Database(tmp_path / "obs.db")
    rows = db.list_inbound_observations()
    types = {r["media_type"] for r in rows}
    assert types == set(Database.INBOUND_MEDIA_TYPES)
    assert all(r["last_seen_at"] is None for r in rows)
    assert all(r["total_count"] == 0 for r in rows)


def test_observe_inbound_dedupes_by_message_id(tmp_path: Path) -> None:
    db = Database(tmp_path / "obs.db")

    assert db.observe_inbound("MSG-1", "image", chat_jid="x@s.whatsapp.net") is True
    # Same id again — no-op (covers the "two bots watch the same chat"
    # case which previously double-counted).
    assert db.observe_inbound("MSG-1", "image", chat_jid="x@s.whatsapp.net") is False
    assert db.observe_inbound("MSG-2", "image", chat_jid="x@s.whatsapp.net") is True

    rows = {r["media_type"]: r for r in db.list_inbound_observations()}
    assert rows["image"]["total_count"] == 2
    assert rows["audio"]["total_count"] == 0


def test_observe_inbound_keeps_last_seen_monotonic(tmp_path: Path) -> None:
    """A late observation must not overwrite a fresher one."""
    db = Database(tmp_path / "obs.db")

    now = datetime(2026, 5, 10, 12, 0, 0, tzinfo=timezone.utc).isoformat()
    earlier = (
        datetime(2026, 5, 10, 12, 0, 0, tzinfo=timezone.utc) - timedelta(hours=2)
    ).isoformat()

    db.observe_inbound("M1", "audio", chat_jid="a@s.whatsapp.net", occurred_at=now)
    # An older message sneaks in afterwards — different id (so the
    # counter goes up), but the timestamp is older so last_seen_at /
    # last_chat_jid stay pointing at the fresher one.
    db.observe_inbound(
        "M2", "audio", chat_jid="b@s.whatsapp.net", occurred_at=earlier
    )

    rows = {r["media_type"]: r for r in db.list_inbound_observations()}
    audio = rows["audio"]
    assert audio["total_count"] == 2
    assert audio["last_seen_at"] == now
    assert audio["last_chat_jid"] == "a@s.whatsapp.net"


def test_observe_inbound_unknown_type_falls_back_to_other(tmp_path: Path) -> None:
    db = Database(tmp_path / "obs.db")
    db.observe_inbound("X", "weird-thing")
    rows = {r["media_type"]: r for r in db.list_inbound_observations()}
    assert rows["other"]["total_count"] == 1
    assert "weird-thing" not in rows


def test_observe_inbound_ignores_empty_message_id(tmp_path: Path) -> None:
    db = Database(tmp_path / "obs.db")
    assert db.observe_inbound("", "image") is False
    rows = {r["media_type"]: r for r in db.list_inbound_observations()}
    assert all(r["total_count"] == 0 for r in rows.values())


# ----------------------------------------------------------------------
# Bot runner observation classifier
# ----------------------------------------------------------------------


@pytest.mark.parametrize(
    "message, expected",
    [
        ({"type": "text", "content": "hello"}, "text"),
        ({"media_type": "image"}, "image"),
        ({"media_type": "voice_note"}, "audio"),
        ({"media_type": "video"}, "video"),
        ({"mimetype": "application/pdf"}, "document"),
        ({"message": {"stickerMessage": {}}}, "sticker"),
        ({"message": {"audioMessage": {}}}, "audio"),
        ({"message": {"pttMessage": {}}}, "audio"),
        ({"message": {"documentMessage": {}}}, "document"),
        ({"message": {"conversation": "hi"}}, "text"),
        ({"content": "plain text only"}, "text"),
        ({}, "other"),
    ],
)
def test_classify_message(message: dict[str, Any], expected: str) -> None:
    assert _classify_message(message) == expected


def test_ts_to_iso_handles_int_float_iso_and_garbage() -> None:
    iso = _ts_to_iso(1_700_000_000)
    assert iso is not None and iso.endswith("+00:00")
    iso2 = _ts_to_iso("1700000000")
    assert iso2 == iso  # numeric string parses identically
    assert _ts_to_iso("2025-05-10T12:00:00Z") == "2025-05-10T12:00:00+00:00"
    assert _ts_to_iso(None) is None
    assert _ts_to_iso("") is None
    # Garbage strings round-trip unchanged so the DB column still gets
    # *something* recognisable to the operator.
    assert _ts_to_iso("not-a-date") == "not-a-date"


def test_bot_runner_observe_swallows_db_failures(tmp_path: Path) -> None:
    """If the observation write throws, the bot must keep running."""

    class _BoomDB:
        def observe_inbound(self, *_: Any, **__: Any) -> bool:
            raise RuntimeError("db on fire")

    spec = BotSpec(
        name="t",
        label="T",
        prefix="[t]",
        description="",
        text_system_prompt="be brief",
    )
    runner = BotRunner(
        spec,
        whatsapp=object(),  # type: ignore[arg-type]
        llm=object(),  # type: ignore[arg-type]
        db=_BoomDB(),  # type: ignore[arg-type]
        chat_jid="x@s.whatsapp.net",
        bot_device_id="0000@s.whatsapp.net",
    )
    # Must not raise.
    runner._observe({"id": "m1", "type": "text", "content": "hi"})


# ----------------------------------------------------------------------
# LLM activity tracker
# ----------------------------------------------------------------------


class _StubChatCompletions:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.calls = 0

    def create(self, *_: Any, **__: Any) -> Any:
        self.calls += 1
        if self.fail:
            raise RuntimeError("upstream said no")
        message = SimpleNamespace(content="ok")
        choice = SimpleNamespace(message=message)
        return SimpleNamespace(choices=[choice])


class _StubAudio:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail

    @property
    def transcriptions(self) -> "_StubAudio":
        return self

    def create(self, *_: Any, **__: Any) -> Any:
        if self.fail:
            raise RuntimeError("whisper unavailable")
        return SimpleNamespace(text="transcript")


class _StubClient:
    def __init__(self, *, fail: bool = False) -> None:
        self.chat = SimpleNamespace(completions=_StubChatCompletions(fail=fail))
        self.audio = _StubAudio(fail=fail)


def _make_llm(*, fail: bool = False) -> LLMService:
    svc = LLMService.__new__(LLMService)
    svc.client = _StubClient(fail=fail)  # type: ignore[assignment]
    svc.model = "gpt-test"
    svc.vision_model = "gpt-test-vision"
    svc.audio_model = "whisper-test"
    import threading

    svc._activity_lock = threading.Lock()  # type: ignore[attr-defined]
    svc._activity = {  # type: ignore[attr-defined]
        kind: {
            "model": svc._model_for(kind),
            "call_count": 0,
            "success_count": 0,
            "error_count": 0,
            "last_call_at": None,
            "last_success_at": None,
            "last_error_at": None,
            "last_error_message": None,
            "last_latency_ms": None,
        }
        for kind in ("text", "vision", "audio", "video")
    }
    return svc


def test_llm_text_success_records_surface_activity() -> None:
    svc = _make_llm()
    out = svc.call("you are helpful", "ping")
    assert out == "ok"

    snap = {row["surface"]: row for row in svc.activity_snapshot()}
    text = snap["text"]
    assert text["call_count"] == 1
    assert text["success_count"] == 1
    assert text["error_count"] == 0
    assert text["last_success_at"] is not None
    assert text["last_error_at"] is None


def test_llm_text_failure_records_error_and_message() -> None:
    svc = _make_llm(fail=True)
    out = svc.call("be terse", "ping")
    assert out is None

    snap = {row["surface"]: row for row in svc.activity_snapshot()}
    text = snap["text"]
    assert text["call_count"] == 1
    assert text["success_count"] == 0
    assert text["error_count"] == 1
    assert text["last_error_at"] is not None
    assert text["last_error_message"] == "upstream said no"
    # And the OTHER surfaces stay at zero counts — failures don't leak.
    assert snap["audio"]["call_count"] == 0
    assert snap["vision"]["call_count"] == 0
    assert snap["video"]["call_count"] == 0


def test_llm_audio_failure_records_audio_surface() -> None:
    svc = _make_llm(fail=True)
    assert svc.transcribe_audio(b"fake-audio") is None
    snap = {row["surface"]: row for row in svc.activity_snapshot()}
    assert snap["audio"]["error_count"] >= 1
    assert snap["audio"]["last_error_at"] is not None


def test_llm_audio_too_large_records_without_calling_api() -> None:
    svc = _make_llm()
    # 26 MiB is over the 25 MiB cap, so the API is never called.
    assert svc.transcribe_audio(b"\x00" * (26 * 1024 * 1024)) is None
    snap = {row["surface"]: row for row in svc.activity_snapshot()}
    audio = snap["audio"]
    assert audio["error_count"] == 1
    assert "too large" in (audio["last_error_message"] or "")


# ----------------------------------------------------------------------
# /api/diagnostics shape
# ----------------------------------------------------------------------


def test_diagnostics_endpoint_includes_inbound_and_surfaces(
    client: TestClient,
) -> None:
    res = client.post("/api/auth/login", json={"password": "test-password-12345"})
    assert res.status_code == 200, res.text

    res = client.get("/api/diagnostics")
    assert res.status_code == 200, res.text
    body = res.json()

    assert "inbound" in body
    inbound_types = {row["media_type"] for row in body["inbound"]}
    assert inbound_types == set(Database.INBOUND_MEDIA_TYPES)

    assert "llm" in body and "surfaces" in body["llm"]
    surfaces = {row["surface"] for row in body["llm"]["surfaces"]}
    assert surfaces == {"text", "vision", "audio", "video"}
    for row in body["llm"]["surfaces"]:
        # Every surface must have the model name pre-filled even when no
        # call has happened yet — that's how the operator reads "what
        # would I be calling if a message arrived".
        assert row["model"]
        assert row["call_count"] == 0


def test_diagnostics_reflects_recorded_observation(
    client: TestClient,
    app_factory: Any,
) -> None:
    """Recording an observation through ``Database`` must surface in the
    next ``/api/diagnostics`` response."""
    res = client.post("/api/auth/login", json={"password": "test-password-12345"})
    assert res.status_code == 200, res.text

    # Reach into the live app and call observe_inbound directly.
    app = client.app
    db: Database = app.state.db  # type: ignore[attr-defined]
    db.add_chat("12345@s.whatsapp.net", "Mom")
    db.observe_inbound(
        "MSG-INBOUND-1",
        "audio",
        chat_jid="12345@s.whatsapp.net",
        sender="12345@s.whatsapp.net",
    )

    body = client.get("/api/diagnostics").json()
    audio = next(row for row in body["inbound"] if row["media_type"] == "audio")
    assert audio["total_count"] == 1
    assert audio["last_chat_jid"] == "12345@s.whatsapp.net"
    assert audio["last_chat_name"] == "Mom"
    assert audio["last_seen_at"] is not None
