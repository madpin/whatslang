"""SQLite repository.

Schema is intentionally compatible with the existing `data/messages.db` from
prior versions, so an in-place upgrade preserves chats, assignments and the
processed-message log. New columns are added idempotently via `ALTER TABLE`.
"""

from __future__ import annotations

import contextlib
import logging
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Optional

logger = logging.getLogger(__name__)


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Database:
    """Thin SQLite wrapper with WAL, helpers and per-feature methods."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        # ``mode=0o700`` keeps the data directory readable only by the
        # owning user. The DB stores excerpts of real WhatsApp messages
        # plus per-chat bot configuration — both should not be world-
        # readable on shared hosts.
        self.db_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        # Best-effort on platforms / volumes where chmod is a no-op
        # (e.g. some Docker bind-mounts on Windows hosts).
        with contextlib.suppress(OSError):
            self.db_path.parent.chmod(0o700)
        # Allow connections from worker threads (each call opens its own).
        self._lock = threading.Lock()
        self._init_schema()
        with contextlib.suppress(OSError):
            if self.db_path.exists():
                self.db_path.chmod(0o600)

    # ------------------------------------------------------------------
    # Connection helpers
    # ------------------------------------------------------------------
    @contextlib.contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path, timeout=10, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield conn
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS chats (
                    chat_jid          TEXT PRIMARY KEY,
                    chat_name         TEXT,
                    is_manual         INTEGER DEFAULT 0,
                    last_synced       TIMESTAMP,
                    last_message_time TIMESTAMP,
                    message_count     INTEGER DEFAULT 0,
                    added_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS bot_chat_assignments (
                    id                       INTEGER PRIMARY KEY AUTOINCREMENT,
                    bot_name                 TEXT NOT NULL,
                    chat_jid                 TEXT NOT NULL,
                    running                  INTEGER DEFAULT 0,
                    answer_owner_messages    INTEGER DEFAULT 1,
                    context_message_count    INTEGER DEFAULT 0,
                    response_chat_jid        TEXT,
                    created_at               TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (chat_jid) REFERENCES chats(chat_jid) ON DELETE CASCADE,
                    UNIQUE(bot_name, chat_jid)
                );

                CREATE TABLE IF NOT EXISTS processed_messages (
                    message_id    TEXT,
                    bot_name      TEXT,
                    original_text TEXT,
                    response_text TEXT,
                    metadata      TEXT,
                    processed_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (message_id, bot_name)
                );

                CREATE INDEX IF NOT EXISTS idx_chats_last_message_time
                    ON chats(last_message_time DESC);
                CREATE INDEX IF NOT EXISTS idx_assignments_chat
                    ON bot_chat_assignments(chat_jid);
                CREATE INDEX IF NOT EXISTS idx_assignments_running
                    ON bot_chat_assignments(running);
                """
            )
            # Idempotent migrations from older versions.
            for stmt in (
                "ALTER TABLE chats ADD COLUMN last_message_time TIMESTAMP",
                "ALTER TABLE chats ADD COLUMN message_count INTEGER DEFAULT 0",
                "ALTER TABLE bot_chat_assignments ADD COLUMN answer_owner_messages INTEGER DEFAULT 1",
                "ALTER TABLE bot_chat_assignments ADD COLUMN context_message_count INTEGER DEFAULT 0",
                "ALTER TABLE bot_chat_assignments ADD COLUMN response_chat_jid TEXT",
            ):
                with contextlib.suppress(sqlite3.OperationalError):
                    conn.execute(stmt)
            # Rename legacy `enabled` column if present.
            try:
                conn.execute("SELECT enabled FROM bot_chat_assignments LIMIT 1")
                conn.execute("ALTER TABLE bot_chat_assignments RENAME COLUMN enabled TO running")
                logger.info("Migrated 'enabled' column to 'running'")
            except sqlite3.OperationalError:
                pass

        logger.info("Database ready at %s", self.db_path)

    # ==================================================================
    # Processed messages
    # ==================================================================
    def is_processed(self, message_id: str, bot_name: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM processed_messages WHERE message_id=? AND bot_name=?",
                (message_id, bot_name),
            ).fetchone()
            return row is not None

    def mark_processed(
        self,
        message_id: str,
        bot_name: str,
        original_text: str = "",
        response_text: str = "",
        metadata: str = "",
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO processed_messages
                    (message_id, bot_name, original_text, response_text, metadata)
                VALUES (?, ?, ?, ?, ?)
                """,
                (message_id, bot_name, original_text[:1000], response_text[:1000], metadata),
            )

    # ==================================================================
    # Chats
    # ==================================================================
    def add_chat(self, chat_jid: str, chat_name: str, is_manual: bool = False) -> bool:
        try:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO chats (chat_jid, chat_name, is_manual, last_synced)
                    VALUES (?, ?, ?, ?)
                    """,
                    (chat_jid, chat_name, int(is_manual), _utc_iso()),
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def get_chat(self, chat_jid: str) -> Optional[dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM chats WHERE chat_jid=?", (chat_jid,)).fetchone()
            return dict(row) if row else None

    def update_chat(
        self,
        chat_jid: str,
        chat_name: Optional[str] = None,
        last_synced: Optional[str] = None,
        last_message_time: Optional[str] = None,
        increment_message_count: bool = False,
    ) -> bool:
        sets: list[str] = []
        params: list[Any] = []
        if chat_name is not None:
            sets.append("chat_name=?")
            params.append(chat_name)
        if last_synced is not None:
            sets.append("last_synced=?")
            params.append(last_synced)
        if last_message_time is not None:
            sets.append("last_message_time=?")
            params.append(last_message_time)
        if increment_message_count:
            sets.append("message_count = message_count + 1")
        if not sets:
            return True
        params.append(chat_jid)
        with self._connect() as conn:
            conn.execute(f"UPDATE chats SET {', '.join(sets)} WHERE chat_jid=?", params)
        return True

    def delete_chat(self, chat_jid: str) -> bool:
        with self._connect() as conn:
            conn.execute("DELETE FROM chats WHERE chat_jid=?", (chat_jid,))
        return True

    def list_chats(
        self,
        *,
        limit: Optional[int] = None,
        offset: int = 0,
        sort_by: str = "last_message_time",
        order: str = "desc",
        activity: Optional[str] = None,
        bot_status: Optional[str] = None,
        chat_type: Optional[str] = None,
        search: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        sql, params = self._build_chat_query(
            select="DISTINCT chats.*" if bot_status else "chats.*",
            sort_by=sort_by,
            order=order,
            activity=activity,
            bot_status=bot_status,
            chat_type=chat_type,
            search=search,
        )
        if limit is not None:
            sql += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
        with self._connect() as conn:
            return [dict(r) for r in conn.execute(sql, params).fetchall()]

    def count_chats(
        self,
        *,
        activity: Optional[str] = None,
        bot_status: Optional[str] = None,
        chat_type: Optional[str] = None,
        search: Optional[str] = None,
    ) -> int:
        select = "COUNT(DISTINCT chats.chat_jid)" if bot_status else "COUNT(*)"
        sql, params = self._build_chat_query(
            select=select,
            sort_by=None,
            order=None,
            activity=activity,
            bot_status=bot_status,
            chat_type=chat_type,
            search=search,
        )
        with self._connect() as conn:
            return int(conn.execute(sql, params).fetchone()[0])

    def _build_chat_query(
        self,
        *,
        select: str,
        sort_by: Optional[str],
        order: Optional[str],
        activity: Optional[str],
        bot_status: Optional[str],
        chat_type: Optional[str],
        search: Optional[str],
    ) -> tuple[str, list[Any]]:
        sql = f"SELECT {select} FROM chats"
        if bot_status == "running":
            sql += " INNER JOIN bot_chat_assignments a ON a.chat_jid=chats.chat_jid WHERE a.running=1"
        elif bot_status == "none":
            sql += " LEFT JOIN bot_chat_assignments a ON a.chat_jid=chats.chat_jid WHERE a.chat_jid IS NULL"
        else:
            sql += " WHERE 1=1"

        params: list[Any] = []
        if activity == "active":
            sql += " AND chats.last_message_time >= datetime('now', '-1 day')"
        elif activity == "recent":
            sql += " AND chats.last_message_time >= datetime('now', '-7 days')"
        elif activity == "idle":
            sql += (
                " AND (chats.last_message_time IS NULL"
                " OR chats.last_message_time < datetime('now', '-7 days'))"
            )
        if chat_type == "group":
            sql += " AND chats.chat_jid LIKE '%@g.us'"
        elif chat_type == "individual":
            sql += " AND chats.chat_jid NOT LIKE '%@g.us'"
        if search:
            sql += " AND (chats.chat_name LIKE ? OR chats.chat_jid LIKE ?)"
            term = f"%{search}%"
            params.extend([term, term])

        if sort_by:
            valid = {"last_message_time", "chat_name", "message_count", "added_at"}
            field = sort_by if sort_by in valid else "last_message_time"
            direction = "DESC" if (order or "desc").lower() == "desc" else "ASC"
            if field == "last_message_time":
                sql += f" ORDER BY chats.{field} {direction} NULLS LAST"
            else:
                sql += f" ORDER BY chats.{field} {direction}"
        return sql, params

    def update_message_activity(self, chat_jid: str, message_time: Optional[str] = None) -> None:
        self.update_chat(
            chat_jid,
            last_message_time=message_time or _utc_iso(),
            increment_message_count=True,
        )

    # ==================================================================
    # Bot ↔ Chat assignments
    # ==================================================================
    def get_assignment(self, bot_name: str, chat_jid: str) -> Optional[dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM bot_chat_assignments WHERE bot_name=? AND chat_jid=?",
                (bot_name, chat_jid),
            ).fetchone()
            return dict(row) if row else None

    def upsert_assignment(self, bot_name: str, chat_jid: str, **fields: Any) -> bool:
        if not fields:
            return True
        valid = {"running", "answer_owner_messages", "context_message_count", "response_chat_jid"}
        unknown = set(fields) - valid
        if unknown:
            raise ValueError(f"Unknown assignment fields: {unknown}")

        # Coerce booleans to ints for SQLite
        coerced: dict[str, Any] = {}
        for k, v in fields.items():
            if isinstance(v, bool):
                coerced[k] = int(v)
            else:
                coerced[k] = v

        with self._connect() as conn:
            sets = ", ".join(f"{k}=?" for k in coerced)
            conn.execute(
                f"UPDATE bot_chat_assignments SET {sets} WHERE bot_name=? AND chat_jid=?",
                [*coerced.values(), bot_name, chat_jid],
            )
            if conn.total_changes == 0:
                cols = ", ".join(["bot_name", "chat_jid", *coerced.keys()])
                placeholders = ", ".join(["?"] * (2 + len(coerced)))
                conn.execute(
                    f"INSERT INTO bot_chat_assignments ({cols}) VALUES ({placeholders})",
                    [bot_name, chat_jid, *coerced.values()],
                )
        return True

    def set_running(self, bot_name: str, chat_jid: str, running: bool) -> bool:
        return self.upsert_assignment(bot_name, chat_jid, running=running)

    def get_running_bots_for_chat(self, chat_jid: str) -> list[str]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT bot_name FROM bot_chat_assignments WHERE chat_jid=? AND running=1",
                (chat_jid,),
            ).fetchall()
            return [r[0] for r in rows]

    def list_assignments_for_chat(self, chat_jid: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM bot_chat_assignments WHERE chat_jid=? ORDER BY bot_name",
                (chat_jid,),
            ).fetchall()
            return [dict(r) for r in rows]

    def list_running_pairs(self) -> list[tuple[str, str]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT bot_name, chat_jid FROM bot_chat_assignments WHERE running=1"
            ).fetchall()
            return [(r[0], r[1]) for r in rows]

    def get_running_chats_for_bot(self, bot_name: str) -> list[str]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT chat_jid FROM bot_chat_assignments WHERE bot_name=? AND running=1",
                (bot_name,),
            ).fetchall()
            return [r[0] for r in rows]
