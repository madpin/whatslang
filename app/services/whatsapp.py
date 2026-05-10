"""WhatsApp HTTP API client (compatible with go-whatsapp-web-multidevice).

Adds an in-memory ring buffer of the last gateway errors and a small set of
extra endpoints (status / contacts / user info / group info) used by the
diagnostics endpoint and the chat sync.
"""

from __future__ import annotations

import collections
import logging
import threading
import time
from datetime import datetime, timezone
from typing import Any, Optional

import requests

logger = logging.getLogger(__name__)


def _jid_user(jid: str) -> str:
    if not jid:
        return ""
    if "@" in jid:
        jid = jid.split("@", 1)[0]
    return jid.split(":", 1)[0]


def _first(d: dict, *keys: str, default: Any = None) -> Any:
    for k in keys:
        if k in d and d[k] not in (None, ""):
            return d[k]
    return default


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class WhatsAppClient:
    """Small wrapper around the WhatsApp REST API."""

    def __init__(
        self,
        base_url: str,
        username: str = "",
        password: str = "",
        device_id: str = "",
        error_buffer_size: int = 30,
    ):
        self.base_url = base_url.rstrip("/")
        self.device_id = device_id
        self.session = requests.Session()
        if username and password:
            self.session.auth = (username, password)
        if device_id:
            self.session.headers.setdefault("X-Device-Id", device_id)

        self._lock = threading.Lock()
        self._errors: collections.deque = collections.deque(maxlen=error_buffer_size)
        self.last_call_at: Optional[str] = None
        self.last_error_at: Optional[str] = None
        self.error_count: int = 0
        self.call_count: int = 0

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _record_error(self, where: str, err: Exception, *, status: Optional[int] = None) -> None:
        with self._lock:
            self.error_count += 1
            self.last_error_at = _now_iso()
            self._errors.append({
                "timestamp": self.last_error_at,
                "where": where,
                "status": status,
                "message": str(err)[:300],
            })

    def _record_success(self) -> None:
        with self._lock:
            self.call_count += 1
            self.last_call_at = _now_iso()

    def recent_errors(self) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._errors)

    # ------------------------------------------------------------------
    # Health / status
    # ------------------------------------------------------------------
    def health_check(self) -> bool:
        try:
            r = self.session.get(f"{self.base_url}/app/status", timeout=5)
            ok = r.status_code < 500
            self._record_success() if ok else self._record_error("/app/status", RuntimeError(f"HTTP {r.status_code}"), status=r.status_code)
            return ok
        except requests.RequestException as e:
            self._record_error("/app/status", e)
            logger.warning("WhatsApp health check failed: %s", e)
            return False

    def get_app_status(self) -> dict[str, Any]:
        """Return raw `/app/status` response with latency_ms.

        Always returns a dict; sets `reachable=false` on connection errors.
        """
        url = f"{self.base_url}/app/status"
        t0 = time.perf_counter()
        try:
            r = self.session.get(url, timeout=5)
            latency = int((time.perf_counter() - t0) * 1000)
            r.raise_for_status()
            data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
            self._record_success()
            results = data.get("results") if isinstance(data, dict) else {}
            if not isinstance(results, dict):
                results = {}
            return {
                "reachable": True,
                "http_status": r.status_code,
                "latency_ms": latency,
                "is_connected": bool(results.get("is_connected")),
                "is_logged_in": bool(results.get("is_logged_in")),
                "device_id": results.get("device_id") or self.device_id or None,
            }
        except requests.RequestException as e:
            self._record_error("/app/status", e)
            return {
                "reachable": False,
                "http_status": getattr(getattr(e, "response", None), "status_code", None),
                "latency_ms": int((time.perf_counter() - t0) * 1000),
                "is_connected": False,
                "is_logged_in": False,
                "device_id": self.device_id or None,
                "error": str(e)[:200],
            }

    # ------------------------------------------------------------------
    # Messages
    # ------------------------------------------------------------------
    def get_messages(
        self,
        chat_jid: str,
        *,
        limit: int = 20,
        max_retries: int = 2,
        retry_delay: float = 1.0,
    ) -> list[dict[str, Any]]:
        url = f"{self.base_url}/chat/{chat_jid}/messages"
        params = {"limit": limit, "offset": 0}
        last_err: Optional[Exception] = None

        for attempt in range(max_retries + 1):
            try:
                if attempt:
                    time.sleep(retry_delay)
                r = self.session.get(url, params=params, timeout=10)
                r.raise_for_status()
                data = r.json()
                if data.get("code") == "SUCCESS" and "results" in data and "data" in data["results"]:
                    self._record_success()
                    return data["results"]["data"] or []
                logger.warning("get_messages unexpected response: %s", str(data)[:200])
                self._record_success()
                return []
            except requests.HTTPError as e:
                last_err = e
                code = e.response.status_code if e.response is not None else None
                if code and 400 <= code < 500 and code != 429:
                    self._record_error(f"GET {url}", e, status=code)
                    logger.warning("get_messages client error %s, no retry", code)
                    break
            except requests.RequestException as e:
                last_err = e
        if last_err:
            self._record_error(f"GET {url}", last_err)
        logger.error("get_messages(%s) failed after %d attempts: %s", chat_jid, max_retries + 1, last_err)
        return []

    def send_message(
        self, phone: str, message: str, reply_message_id: Optional[str] = None
    ) -> bool:
        url = f"{self.base_url}/send/message"
        payload: dict[str, Any] = {"phone": phone, "message": message}
        if reply_message_id:
            payload["reply_message_id"] = reply_message_id
        try:
            r = self.session.post(url, json=payload, timeout=15)
            r.raise_for_status()
            data = r.json()
            ok = data.get("code") in (200, "SUCCESS")
            (self._record_success if ok else
             lambda: self._record_error("/send/message", RuntimeError(data.get("message", "send failed"))))()
            return ok
        except requests.RequestException as e:
            self._record_error("/send/message", e)
            logger.error("send_message error: %s (length=%d)", e, len(message))
            return False

    # ------------------------------------------------------------------
    # Chat lists
    # ------------------------------------------------------------------
    def _paginate(self, url: str, *, fetch_all: bool = True, page_limit: int = 100) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        seen: set[str] = set()
        offset = 0
        while True:
            params = {"limit": page_limit, "offset": offset} if fetch_all else None
            try:
                r = self.session.get(url, params=params, timeout=10)
                r.raise_for_status()
                data = r.json()
                self._record_success()
            except requests.RequestException as e:
                self._record_error(f"GET {url}", e)
                logger.error("Paginated GET %s failed: %s", url, e)
                break

            batch: list[dict[str, Any]] = []
            if isinstance(data, list):
                batch = data
            elif isinstance(data, dict):
                results = data.get("results")
                if isinstance(results, list):
                    batch = results
                elif isinstance(results, dict) and "data" in results:
                    batch = results["data"]
            if not batch:
                break

            added = 0
            for item in batch:
                jid = _first(item, "JID", "jid", "id", "ID")
                if jid and jid not in seen:
                    seen.add(jid)
                    out.append(item)
                    added += 1
            if not fetch_all or added == 0 or len(batch) < page_limit:
                break
            offset += page_limit
        return out

    def get_chats(self, *, fetch_all: bool = True) -> list[dict[str, Any]]:
        return self._paginate(f"{self.base_url}/chats", fetch_all=fetch_all)

    def get_groups(self, *, fetch_all: bool = True) -> list[dict[str, Any]]:
        return self._paginate(f"{self.base_url}/user/my/groups", fetch_all=fetch_all)

    def get_contacts(self, *, fetch_all: bool = True) -> list[dict[str, Any]]:
        return self._paginate(f"{self.base_url}/user/my/contacts", fetch_all=fetch_all)

    def get_chat_info(self, chat_jid: str) -> Optional[dict[str, Any]]:
        url = f"{self.base_url}/chat/{chat_jid}"
        try:
            r = self.session.get(url, timeout=10)
            r.raise_for_status()
            data = r.json()
            if data.get("code") == "SUCCESS":
                self._record_success()
                return data.get("results")
        except requests.RequestException as e:
            self._record_error(f"GET {url}", e)
            logger.debug("get_chat_info(%s) failed: %s", chat_jid, e)
        return None

    def get_group_info(self, group_jid: str) -> Optional[dict[str, Any]]:
        url = f"{self.base_url}/group/info"
        try:
            r = self.session.get(url, params={"group_id": group_jid}, timeout=10)
            r.raise_for_status()
            data = r.json()
            self._record_success()
            return data.get("results") if isinstance(data, dict) else None
        except requests.RequestException as e:
            self._record_error(f"GET {url}", e)
            logger.debug("get_group_info(%s) failed: %s", group_jid, e)
            return None

    def get_user_info(self, phone_or_jid: str) -> Optional[dict[str, Any]]:
        url = f"{self.base_url}/user/info"
        try:
            r = self.session.get(url, params={"phone": phone_or_jid}, timeout=10)
            r.raise_for_status()
            data = r.json()
            self._record_success()
            return data.get("results") if isinstance(data, dict) else None
        except requests.RequestException as e:
            self._record_error(f"GET {url}", e)
            logger.debug("get_user_info(%s) failed: %s", phone_or_jid, e)
            return None

    # ------------------------------------------------------------------
    # Media
    # ------------------------------------------------------------------
    def download_media(self, message_id: str, chat_jid: str, *, timeout: int = 30) -> Optional[bytes]:
        """Trigger server-side decryption and return the decrypted media bytes."""
        try:
            r = self.session.get(
                f"{self.base_url}/message/{message_id}/download",
                params={"phone": chat_jid},
                timeout=timeout,
            )
            r.raise_for_status()
            data = r.json()
            if data.get("code") != "SUCCESS":
                self._record_error(f"download/{message_id}", RuntimeError(data.get("message", "")))
                logger.error("Media download failed: %s", data.get("message"))
                return None
            file_path = data.get("results", {}).get("file_path")
            if not file_path:
                self._record_error(f"download/{message_id}", RuntimeError("missing file_path"))
                logger.error("Media response had no file_path: %s", data)
                return None
            r2 = self.session.get(f"{self.base_url}/{file_path}", timeout=timeout)
            r2.raise_for_status()
            self._record_success()
            return r2.content
        except requests.RequestException as e:
            self._record_error(f"download/{message_id}", e)
            logger.error("download_media error: %s", e)
            return None

    # Convenience aliases
    download_image = download_media
    download_audio = download_media

    def download_video(self, message_id: str, chat_jid: str) -> Optional[bytes]:
        return self.download_media(message_id, chat_jid, timeout=60)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def is_bot_sender(sender_jid: str, bot_device_id: str) -> bool:
        if not sender_jid or not bot_device_id:
            return False
        if sender_jid == bot_device_id:
            return True
        return _jid_user(sender_jid) == _jid_user(bot_device_id)

    @staticmethod
    def extract_friendly_name(item: dict[str, Any]) -> Optional[str]:
        """Pick the most human-friendly name from a gateway response object.

        The gateway returns slightly different shapes depending on endpoint
        and version (PascalCase vs. snake_case, ``Subject`` for groups,
        ``PushName``/``BusinessName``/``FullName`` for contacts).
        """
        for key in (
            "Name", "name",
            "Subject", "subject",
            "Title", "title",
            "PushName", "push_name",
            "FullName", "full_name",
            "BusinessName", "business_name",
            "ShortName", "short_name",
            "Notify", "notify",
            "DisplayName", "display_name",
        ):
            v = item.get(key) if isinstance(item, dict) else None
            if isinstance(v, str) and v.strip():
                return v.strip()
        return None
