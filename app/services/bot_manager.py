"""Bot lifecycle: per-(bot_name, chat_jid) thread, in-memory log buffers."""

from __future__ import annotations

import logging
import threading
import time
from collections import deque
from datetime import datetime, timezone
from typing import Any, Optional

from app.bots import get_spec, list_specs
from app.bots.base import BotRunner, BotSpec
from app.config import DeviceConfig
from app.db import Database
from app.services.llm import LLMService
from app.services.whatsapp import WhatsAppGateway

logger = logging.getLogger(__name__)

BotKey = tuple[str, str]  # (bot_name, chat_jid)


class _RingHandler(logging.Handler):
    """In-memory ring buffer for a specific bot's logs."""

    def __init__(self, max_logs: int = 200):
        super().__init__()
        self.records: deque[dict[str, Any]] = deque(maxlen=max_logs)

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(
            {
                "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
                "level": record.levelname,
                "message": self.format(record),
            }
        )


class BotManager:
    def __init__(
        self,
        gateway: WhatsAppGateway,
        llm: LLMService,
        db: Database,
        *,
        devices: list[DeviceConfig] | None = None,
        default_device_id: str = "",
        poll_interval: int = 5,
    ):
        self.gateway = gateway
        self.llm = llm
        self.db = db
        self.default_device_id = default_device_id or gateway.default_device_id
        self._self_jids = {d.id: d.self_jid for d in (devices or [])}
        self.poll_interval = poll_interval

        self._runners: dict[BotKey, BotRunner] = {}
        self._threads: dict[BotKey, threading.Thread] = {}
        self._handlers: dict[BotKey, _RingHandler] = {}
        self._started_at: dict[BotKey, float] = {}
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Device routing helpers
    # ------------------------------------------------------------------
    def _route_from_assignment(self, assignment: dict[str, Any]) -> tuple[str, str]:
        """Resolve (source_device_id, target_device_id) from an assignment row.

        A blank source falls back to the default device; a blank target
        falls back to the source (reply on the same account you read from).
        """
        source_id = (assignment.get("source_device_id") or "").strip() or self.default_device_id
        target_id = (assignment.get("target_device_id") or "").strip() or source_id
        return source_id, target_id

    def _route(self, bot_name: str, chat_jid: str) -> tuple[str, str]:
        return self._route_from_assignment(self.db.get_assignment(bot_name, chat_jid) or {})

    def _self_jid_for(self, device_id: str) -> str:
        return self._self_jids.get(device_id) or (device_id if "@" in device_id else "")

    # ------------------------------------------------------------------
    # Catalog / status
    # ------------------------------------------------------------------
    @property
    def specs(self) -> list[BotSpec]:
        return list_specs()

    def get_spec(self, name: str) -> Optional[BotSpec]:
        return get_spec(name)

    def is_running(self, bot_name: str, chat_jid: str) -> bool:
        return (bot_name, chat_jid) in self._runners

    def status(self, bot_name: str, chat_jid: str) -> Optional[dict[str, Any]]:
        spec = get_spec(bot_name)
        if not spec:
            return None
        key: BotKey = (bot_name, chat_jid)
        running = key in self._runners
        assignment = self.db.get_assignment(bot_name, chat_jid) or {}
        uptime = int(time.time() - self._started_at[key]) if running and key in self._started_at else None
        source_id, target_id = self._route_from_assignment(assignment)
        return {
            "name": spec.name,
            "label": spec.label,
            "prefix": spec.prefix,
            "emoji": spec.emoji,
            "description": spec.description,
            "chat_jid": chat_jid,
            "status": "running" if running else "stopped",
            "uptime_seconds": uptime,
            "answer_owner_messages": bool(assignment.get("answer_owner_messages", 1)),
            "context_message_count": int(assignment.get("context_message_count", 0) or 0),
            "response_chat_jid": assignment.get("response_chat_jid"),
            "source_device_id": source_id,
            "target_device_id": target_id,
            "supports": {
                "text": spec.supports_text,
                "image": spec.supports_image,
                "audio": spec.supports_audio,
                "video": spec.supports_video,
            },
        }

    def statuses_for_chat(self, chat_jid: str) -> list[dict[str, Any]]:
        return [s for s in (self.status(spec.name, chat_jid) for spec in self.specs) if s]

    def all_running_statuses(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for bot_name, chat_jid in list(self._runners.keys()):
            if (s := self.status(bot_name, chat_jid)):
                out.append(s)
        return out

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def start(self, bot_name: str, chat_jid: str) -> bool:
        spec = get_spec(bot_name)
        if not spec:
            logger.error("Unknown bot: %s", bot_name)
            return False
        key: BotKey = (bot_name, chat_jid)
        with self._lock:
            if key in self._runners:
                return True

            source_id, target_id = self._route(bot_name, chat_jid)
            runner = BotRunner(
                spec,
                whatsapp=self.gateway.get(source_id),
                target_whatsapp=self.gateway.get(target_id),
                llm=self.llm,
                db=self.db,
                chat_jid=chat_jid,
                bot_device_id=self._self_jid_for(source_id),
                source_device_id=source_id,
                target_device_id=target_id,
                poll_interval=self.poll_interval,
            )

            handler = _RingHandler()
            handler.setFormatter(logging.Formatter("%(asctime)s  %(levelname)s  %(message)s"))
            bot_logger = logging.getLogger(f"bot.{bot_name}")
            bot_logger.addHandler(handler)

            t = threading.Thread(target=runner.run, name=f"bot-{bot_name}-{chat_jid}", daemon=True)
            t.start()

            self._runners[key] = runner
            self._threads[key] = t
            self._handlers[key] = handler
            self._started_at[key] = time.time()

        self.db.set_running(bot_name, chat_jid, True)
        logger.info("Started %s for %s", bot_name, chat_jid)
        return True

    def stop(self, bot_name: str, chat_jid: str, *, persist: bool = True) -> bool:
        key: BotKey = (bot_name, chat_jid)
        with self._lock:
            runner = self._runners.pop(key, None)
            thread = self._threads.pop(key, None)
            handler = self._handlers.pop(key, None)
            self._started_at.pop(key, None)
        if runner is None:
            if persist:
                self.db.set_running(bot_name, chat_jid, False)
            return True

        runner.stop()
        if thread:
            thread.join(timeout=10)
        if handler:
            logging.getLogger(f"bot.{bot_name}").removeHandler(handler)
        if persist:
            self.db.set_running(bot_name, chat_jid, False)
        logger.info("Stopped %s for %s", bot_name, chat_jid)
        return True

    def stop_all(self, *, persist: bool = False) -> None:
        for bot_name, chat_jid in list(self._runners.keys()):
            self.stop(bot_name, chat_jid, persist=persist)

    def resume_running_from_db(self) -> int:
        started = 0
        for bot_name, chat_jid in self.db.list_running_pairs():
            if get_spec(bot_name) and self.start(bot_name, chat_jid):
                started += 1
        return started

    # ------------------------------------------------------------------
    # Logs
    # ------------------------------------------------------------------
    def get_logs(self, bot_name: str, chat_jid: str, *, limit: int = 100) -> list[dict[str, Any]]:
        handler = self._handlers.get((bot_name, chat_jid))
        if not handler:
            return []
        records = list(handler.records)
        records.reverse()
        return records[:limit]
