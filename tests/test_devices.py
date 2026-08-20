"""Tests for multi-device support.

Covers:
- Config: ``DEVICES`` / ``DEVICE_ID`` resolution into a device list + default.
- ``WhatsAppGateway`` caches one client per device id and scopes each.
- ``BotRunner`` reads with the source client and *sends* with the target
  client, and only quotes the original when it stays on the same account.
- ``GET /api/devices`` and per-bot device routing via the settings endpoint.
"""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from app.bots.base import BotRunner, BotSpec
from app.config import DeviceConfig, Settings
from app.services.whatsapp import WhatsAppGateway

_PW = "test-password-12345"


# ----------------------------------------------------------------------
# Config resolution
# ----------------------------------------------------------------------
def test_legacy_device_id_becomes_default_and_is_listed() -> None:
    s = Settings(
        device_id="6281@s.whatsapp.net",
        devices=[DeviceConfig(id="sales", label="Sales")],
    )
    assert s.default_device_id == "6281@s.whatsapp.net"
    ids = [d.id for d in s.resolved_devices]
    assert ids[0] == "6281@s.whatsapp.net"  # legacy default first
    assert "sales" in ids
    assert s.device_id_set == {"6281@s.whatsapp.net", "sales"}
    assert not s.required_missing() or "DEVICE_ID" not in s.required_missing()


def test_default_falls_back_to_first_device_when_no_legacy_id() -> None:
    s = Settings(device_id="", devices=[DeviceConfig(id="a"), DeviceConfig(id="b")])
    assert s.default_device_id == "a"
    assert s.device_id_set == {"a", "b"}


def test_no_devices_at_all_is_flagged_missing() -> None:
    s = Settings(device_id="", devices=[])
    assert "DEVICE_ID" in s.required_missing()


def test_device_self_jid_resolution() -> None:
    assert DeviceConfig(id="sales").self_jid == ""  # label id → no JID
    assert DeviceConfig(id="628@s.whatsapp.net").self_jid == "628@s.whatsapp.net"
    assert DeviceConfig(id="sales", jid="628@s.whatsapp.net").self_jid == "628@s.whatsapp.net"


# ----------------------------------------------------------------------
# Gateway pool
# ----------------------------------------------------------------------
def test_gateway_caches_and_scopes_clients() -> None:
    seen: list[str] = []

    def factory(base_url: str, username: str = "", password: str = "", device_id: str = "") -> dict:
        seen.append(device_id)
        return {"base_url": base_url, "device_id": device_id}

    gw = WhatsAppGateway(
        "http://gw", "u", "p", default_device_id="A", client_factory=factory
    )
    a1 = gw.get("A")
    a2 = gw.get("A")
    b = gw.get("B")

    assert a1 is a2  # cached per device id
    assert a1["device_id"] == "A"
    assert b["device_id"] == "B"
    assert gw.default is a1  # default device
    assert gw.get("") is a1  # blank → default
    assert seen == ["A", "B"]  # only two distinct constructions


# ----------------------------------------------------------------------
# BotRunner read/send split
# ----------------------------------------------------------------------
class _RecordWA:
    def __init__(self) -> None:
        self.sent: list[tuple[str, str, Any]] = []

    def send_message(self, phone: str, message: str, reply_message_id: Any = None) -> bool:
        self.sent.append((phone, message, reply_message_id))
        return True


class _RouteDB:
    def __init__(self, assignment: dict[str, Any]) -> None:
        self._assignment = assignment
        self.processed: list[dict[str, Any]] = []

    def get_assignment(self, *_: Any) -> dict[str, Any]:
        return self._assignment

    def mark_processed(self, message_id: str, bot_name: str, **kw: Any) -> None:
        self.processed.append({"message_id": message_id, **kw})


def _spec() -> BotSpec:
    return BotSpec(
        name="x", label="X", prefix="[x]", description="", text_system_prompt="p"
    )


def _runner(*, assignment: dict[str, Any], source: str, target: str) -> tuple[BotRunner, _RecordWA, _RecordWA]:
    src, tgt = _RecordWA(), _RecordWA()
    runner = BotRunner(
        _spec(),
        whatsapp=src,  # type: ignore[arg-type]
        target_whatsapp=tgt,  # type: ignore[arg-type]
        llm=object(),  # type: ignore[arg-type]
        db=_RouteDB(assignment),  # type: ignore[arg-type]
        chat_jid="chat@s.whatsapp.net",
        bot_device_id="",
        source_device_id=source,
        target_device_id=target,
    )
    return runner, src, tgt


def test_cross_device_send_uses_target_and_does_not_quote() -> None:
    runner, src, tgt = _runner(assignment={}, source="A", target="B")
    runner._send_response({"id": "m1", "content": "hi"}, "hello")

    assert src.sent == []  # nothing goes out on the read account
    assert len(tgt.sent) == 1
    phone, message, reply_id = tgt.sent[0]
    assert phone == "chat@s.whatsapp.net"
    assert message == "[x] hello"
    assert reply_id is None  # cross-device → cannot quote the source message


def test_same_device_send_quotes_original() -> None:
    runner, _src, tgt = _runner(assignment={}, source="A", target="A")
    runner._send_response({"id": "m1", "content": "hi"}, "hello")
    _phone, _message, reply_id = tgt.sent[0]
    assert reply_id == "m1"


def test_forward_to_other_chat_goes_through_target_device() -> None:
    runner, src, tgt = _runner(
        assignment={"response_chat_jid": "other@s.whatsapp.net"},
        source="A",
        target="B",
    )
    runner._send_response({"id": "m1", "content": "hi", "push_name": "Bob"}, "hello")

    assert src.sent == []
    # 1) forwarded original context, 2) the reply — both on the target account.
    assert len(tgt.sent) == 2
    assert tgt.sent[0][0] == "other@s.whatsapp.net"
    assert tgt.sent[0][1].startswith("[Fwd from Bob]")
    assert tgt.sent[1][0] == "other@s.whatsapp.net"
    assert tgt.sent[1][2] is None  # forwarded → no quote


# ----------------------------------------------------------------------
# API: /api/devices + per-bot routing
# ----------------------------------------------------------------------
def test_devices_endpoint_lists_default_single(client: TestClient) -> None:
    client.post("/api/auth/login", json={"password": _PW})
    body = client.get("/api/devices").json()
    assert len(body) == 1
    assert body[0]["id"] == "0000@s.whatsapp.net"
    assert body[0]["is_default"] is True


def test_devices_endpoint_lists_multiple(app_factory: Any, monkeypatch: Any) -> None:
    monkeypatch.setattr("app.main.WhatsAppClient", lambda *a, **k: None)
    monkeypatch.setattr("app.main.LLMService", lambda *a, **k: None)
    app = app_factory(DEVICES='[{"id":"sales","label":"Sales"}]')
    with TestClient(app) as c:
        c.post("/api/auth/login", json={"password": _PW})
        body = c.get("/api/devices").json()
        assert {d["id"] for d in body} == {"0000@s.whatsapp.net", "sales"}
        default = [d for d in body if d["is_default"]]
        assert len(default) == 1 and default[0]["id"] == "0000@s.whatsapp.net"


def test_bot_settings_rejects_unknown_device(client: TestClient) -> None:
    client.post("/api/auth/login", json={"password": _PW})
    client.app.state.db.add_chat("111@s.whatsapp.net", "Test")  # type: ignore[attr-defined]
    res = client.put(
        "/api/bots/translation/settings",
        params={"chat_jid": "111@s.whatsapp.net"},
        json={"source_device_id": "does-not-exist"},
    )
    assert res.status_code == 400, res.text


def test_bot_settings_stores_known_device_routing(client: TestClient) -> None:
    client.post("/api/auth/login", json={"password": _PW})
    client.app.state.db.add_chat("111@s.whatsapp.net", "Test")  # type: ignore[attr-defined]
    res = client.put(
        "/api/bots/translation/settings",
        params={"chat_jid": "111@s.whatsapp.net"},
        json={"source_device_id": "0000@s.whatsapp.net"},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["source_device_id"] == "0000@s.whatsapp.net"
    # Target defaults to the source when left unset.
    assert body["target_device_id"] == "0000@s.whatsapp.net"


def test_changing_device_route_reconfigures_running_bot(app_factory: Any, monkeypatch: Any) -> None:
    class _DeviceWA:
        def __init__(self, *_: Any, device_id: str = "", **__: Any) -> None:
            self.device_id = device_id

        def get_messages(self, *_: Any, **__: Any) -> list[dict[str, Any]]:
            return []

    monkeypatch.setattr("app.main.WhatsAppClient", _DeviceWA)
    monkeypatch.setattr("app.main.LLMService", lambda *a, **k: None)
    app = app_factory(DEVICES='[{"id":"personal","label":"Personal"}]')

    with TestClient(app) as c:
        c.post("/api/auth/login", json={"password": _PW})
        chat_jid = "111@s.whatsapp.net"
        app.state.db.add_chat(chat_jid, "Test")
        started = c.post(
            "/api/bots/translation/start", params={"chat_jid": chat_jid}
        )
        assert started.status_code == 200, started.text

        key = ("translation", chat_jid)
        original = app.state.bots._runners[key]
        assert original.whatsapp.device_id == "0000@s.whatsapp.net"
        original._first_run = False

        updated = c.put(
            "/api/bots/translation/settings",
            params={"chat_jid": chat_jid},
            json={
                "source_device_id": "personal",
                "target_device_id": "personal",
            },
        )
        assert updated.status_code == 200, updated.text

        reconfigured = app.state.bots._runners[key]
        assert reconfigured is original
        assert reconfigured.whatsapp.device_id == "personal"
        assert reconfigured.target_whatsapp.device_id == "personal"
        assert reconfigured._first_run is True
