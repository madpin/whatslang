"""Database for tracking processed messages and managing chats/bot assignments."""

import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class MessageDatabase:
    """Manages SQLite database for tracking processed messages and bot assignments."""
    
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path) if not isinstance(db_path, Path) else db_path
        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()
    
    def init_db(self):
        """Initialize the database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Existing table for processed messages
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processed_messages (
                message_id TEXT,
                bot_name TEXT,
                original_text TEXT,
                response_text TEXT,
                metadata TEXT,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (message_id, bot_name)
            )
        """)
        
        # New table for chats
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                chat_jid TEXT PRIMARY KEY,
                chat_name TEXT,
                is_manual INTEGER DEFAULT 0,
                last_synced TIMESTAMP,
                last_message_time TIMESTAMP,
                message_count INTEGER DEFAULT 0,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Add columns if they don't exist (for existing databases)
        try:
            cursor.execute("ALTER TABLE chats ADD COLUMN last_message_time TIMESTAMP")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        try:
            cursor.execute("ALTER TABLE chats ADD COLUMN message_count INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        # Create index for faster sorting
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_chats_last_message_time 
            ON chats(last_message_time DESC)
        """)
        
        # New table for bot-chat assignments
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bot_chat_assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bot_name TEXT NOT NULL,
                chat_jid TEXT NOT NULL,
                running INTEGER DEFAULT 0,
                answer_owner_messages INTEGER DEFAULT 1,
                context_message_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chat_jid) REFERENCES chats(chat_jid) ON DELETE CASCADE,
                UNIQUE(bot_name, chat_jid)
            )
        """)
        
        # Migration: Rename 'enabled' column to 'running' if it exists
        try:
            cursor.execute("SELECT enabled FROM bot_chat_assignments LIMIT 1")
            # If we get here, 'enabled' column exists, so we need to migrate
            cursor.execute("ALTER TABLE bot_chat_assignments RENAME COLUMN enabled TO running")
            logger.info("Migrated 'enabled' column to 'running' in bot_chat_assignments table")
        except sqlite3.OperationalError:
            # Column doesn't exist or already renamed, continue
            pass
        
        # Add answer_owner_messages column if it doesn't exist (for existing databases)
        try:
            cursor.execute("ALTER TABLE bot_chat_assignments ADD COLUMN answer_owner_messages INTEGER DEFAULT 1")
            logger.info("Added 'answer_owner_messages' column to bot_chat_assignments table")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        # Add context_message_count column if it doesn't exist (for existing databases)
        try:
            cursor.execute("ALTER TABLE bot_chat_assignments ADD COLUMN context_message_count INTEGER DEFAULT 0")
            logger.info("Added 'context_message_count' column to bot_chat_assignments table")
        except sqlite3.OperationalError:
            pass  # Column already exists
        
        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")
    
    def is_processed(self, message_id: str, bot_name: str) -> bool:
        """Check if a message has already been processed by a specific bot."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM processed_messages WHERE message_id = ? AND bot_name = ?",
            (message_id, bot_name)
        )
        result = cursor.fetchone()
        conn.close()
        return result is not None
    
    def mark_processed(
        self,
        message_id: str,
        bot_name: str,
        original_text: str,
        response_text: str,
        metadata: str = ""
    ):
        """Mark a message as processed by a specific bot."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO processed_messages 
            (message_id, bot_name, original_text, response_text, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (message_id, bot_name, original_text, response_text, metadata))
        conn.commit()
        conn.close()
    
    # ===== Chat Management Methods =====
    
    def add_chat(
        self,
        chat_jid: str,
        chat_name: str,
        is_manual: bool = False
    ) -> bool:
        """Add a new chat to the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO chats (chat_jid, chat_name, is_manual, last_synced)
                VALUES (?, ?, ?, ?)
            """, (chat_jid, chat_name, 1 if is_manual else 0, datetime.utcnow().isoformat()))
            conn.commit()
            conn.close()
            logger.info(f"Added chat: {chat_jid} ({chat_name})")
            return True
        except sqlite3.IntegrityError:
            logger.warning(f"Chat already exists: {chat_jid}")
            return False
        except Exception as e:
            logger.error(f"Error adding chat: {e}", exc_info=True)
            return False
    
    def get_chat(self, chat_jid: str) -> Optional[Dict[str, Any]]:
        """Get a specific chat by JID."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM chats WHERE chat_jid = ?", (chat_jid,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def list_chats(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        sort_by: str = "last_message_time",
        order: str = "desc",
        activity_filter: Optional[str] = None,
        bot_status_filter: Optional[str] = None,
        chat_type_filter: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List all chats in the database with pagination, sorting, and filtering.
        
        Args:
            limit: Maximum number of chats to return
            offset: Number of chats to skip
            sort_by: Field to sort by (last_message_time, chat_name, message_count, added_at)
            order: Sort order (asc or desc)
            activity_filter: Filter by activity status (active, recent, idle)
            bot_status_filter: Filter by bot status (running, enabled, none)
            chat_type_filter: Filter by chat type (group, individual)
            search: Search term for chat name or JID
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Build query with filters
        # Use DISTINCT when filtering by bot status to avoid duplicates from JOIN
        if bot_status_filter:
            query = "SELECT DISTINCT chats.* FROM chats"
        else:
            query = "SELECT * FROM chats"
        
        # Bot status filter requires a JOIN
        if bot_status_filter == "running":
            query += " INNER JOIN bot_chat_assignments ON chats.chat_jid = bot_chat_assignments.chat_jid"
            query += " WHERE bot_chat_assignments.running = 1"
        elif bot_status_filter == "none":
            query += " LEFT JOIN bot_chat_assignments ON chats.chat_jid = bot_chat_assignments.chat_jid"
            query += " WHERE bot_chat_assignments.chat_jid IS NULL"
        else:
            query += " WHERE 1=1"
        
        params = []
        
        # Activity filter
        if activity_filter == "active":
            query += " AND chats.last_message_time >= datetime('now', '-1 day')"
        elif activity_filter == "recent":
            query += " AND chats.last_message_time >= datetime('now', '-7 days')"
        elif activity_filter == "idle":
            query += " AND (chats.last_message_time IS NULL OR chats.last_message_time < datetime('now', '-7 days'))"
        
        # Chat type filter
        if chat_type_filter == "group":
            query += " AND chats.chat_jid LIKE '%@g.us'"
        elif chat_type_filter == "individual":
            query += " AND chats.chat_jid NOT LIKE '%@g.us'"
        
        # Search filter
        if search:
            query += " AND (chats.chat_name LIKE ? OR chats.chat_jid LIKE ?)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term])
        
        # Sort order
        valid_sort_fields = ["last_message_time", "chat_name", "message_count", "added_at"]
        if sort_by not in valid_sort_fields:
            sort_by = "last_message_time"
        
        # Prefix sort field with table name when using JOINs
        sort_field = f"chats.{sort_by}" if bot_status_filter else sort_by
        
        # Handle NULL values in last_message_time (put them at the end)
        if sort_by == "last_message_time":
            if order.lower() == "desc":
                query += f" ORDER BY {sort_field} DESC NULLS LAST"
            else:
                query += f" ORDER BY {sort_field} ASC NULLS LAST"
        else:
            query += f" ORDER BY {sort_field} {order.upper()}"
        
        # Pagination
        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)
            if offset is not None:
                query += " OFFSET ?"
                params.append(offset)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def update_chat(
        self,
        chat_jid: str,
        chat_name: Optional[str] = None,
        last_synced: Optional[str] = None,
        last_message_time: Optional[str] = None,
        increment_message_count: bool = False
    ) -> bool:
        """Update chat information."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            updates = []
            params = []
            
            if chat_name is not None:
                updates.append("chat_name = ?")
                params.append(chat_name)
            
            if last_synced is not None:
                updates.append("last_synced = ?")
                params.append(last_synced)
            
            if last_message_time is not None:
                updates.append("last_message_time = ?")
                params.append(last_message_time)
            
            if increment_message_count:
                updates.append("message_count = message_count + 1")
            
            if not updates:
                return True
            
            params.append(chat_jid)
            query = f"UPDATE chats SET {', '.join(updates)} WHERE chat_jid = ?"
            
            cursor.execute(query, params)
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error updating chat: {e}", exc_info=True)
            return False
    
    def count_chats(
        self,
        activity_filter: Optional[str] = None,
        bot_status_filter: Optional[str] = None,
        chat_type_filter: Optional[str] = None,
        search: Optional[str] = None
    ) -> int:
        """
        Count chats with the same filters as list_chats.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Build query with filters
        # Use DISTINCT when filtering by bot status to avoid duplicates from JOIN
        if bot_status_filter:
            query = "SELECT COUNT(DISTINCT chats.chat_jid) FROM chats"
        else:
            query = "SELECT COUNT(*) FROM chats"
        
        # Bot status filter requires a JOIN
        if bot_status_filter == "running":
            query += " INNER JOIN bot_chat_assignments ON chats.chat_jid = bot_chat_assignments.chat_jid"
            query += " WHERE bot_chat_assignments.running = 1"
        elif bot_status_filter == "none":
            query += " LEFT JOIN bot_chat_assignments ON chats.chat_jid = bot_chat_assignments.chat_jid"
            query += " WHERE bot_chat_assignments.chat_jid IS NULL"
        else:
            query += " WHERE 1=1"
        
        params = []
        
        # Activity filter
        if activity_filter == "active":
            query += " AND chats.last_message_time >= datetime('now', '-1 day')"
        elif activity_filter == "recent":
            query += " AND chats.last_message_time >= datetime('now', '-7 days')"
        elif activity_filter == "idle":
            query += " AND (chats.last_message_time IS NULL OR chats.last_message_time < datetime('now', '-7 days'))"
        
        # Chat type filter
        if chat_type_filter == "group":
            query += " AND chats.chat_jid LIKE '%@g.us'"
        elif chat_type_filter == "individual":
            query += " AND chats.chat_jid NOT LIKE '%@g.us'"
        
        # Search filter
        if search:
            query += " AND (chats.chat_name LIKE ? OR chats.chat_jid LIKE ?)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term])
        
        cursor.execute(query, params)
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def update_message_activity(self, chat_jid: str, message_time: Optional[str] = None) -> bool:
        """
        Update the last_message_time for a chat and increment message count.
        Called when a message is processed for this chat.
        """
        if message_time is None:
            message_time = datetime.utcnow().isoformat()
        
        return self.update_chat(
            chat_jid=chat_jid,
            last_message_time=message_time,
            increment_message_count=True
        )
    
    def delete_chat(self, chat_jid: str) -> bool:
        """Delete a chat and its assignments."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chats WHERE chat_jid = ?", (chat_jid,))
            conn.commit()
            conn.close()
            logger.info(f"Deleted chat: {chat_jid}")
            return True
        except Exception as e:
            logger.error(f"Error deleting chat: {e}", exc_info=True)
            return False
    
    # ===== Assignment Management Methods =====
    
    def set_bot_running_state(
        self,
        bot_name: str,
        chat_jid: str,
        running: bool = True
    ) -> bool:
        """Set the running state of a bot for a specific chat."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Try to update existing assignment
            cursor.execute("""
                UPDATE bot_chat_assignments 
                SET running = ?
                WHERE bot_name = ? AND chat_jid = ?
            """, (1 if running else 0, bot_name, chat_jid))
            
            # If no rows updated, insert new assignment
            if cursor.rowcount == 0:
                cursor.execute("""
                    INSERT INTO bot_chat_assignments (bot_name, chat_jid, running)
                    VALUES (?, ?, ?)
                """, (bot_name, chat_jid, 1 if running else 0))
            
            conn.commit()
            conn.close()
            logger.info(f"Set bot running state: {bot_name} -> {chat_jid} (running={running})")
            return True
        except Exception as e:
            logger.error(f"Error setting bot running state: {e}", exc_info=True)
            return False
    
    def set_bot_answer_owner_messages(
        self,
        bot_name: str,
        chat_jid: str,
        answer_owner_messages: bool = True
    ) -> bool:
        """Set whether the bot should answer owner messages for a specific chat."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Try to update existing assignment
            cursor.execute("""
                UPDATE bot_chat_assignments 
                SET answer_owner_messages = ?
                WHERE bot_name = ? AND chat_jid = ?
            """, (1 if answer_owner_messages else 0, bot_name, chat_jid))
            
            # If no rows updated, insert new assignment
            if cursor.rowcount == 0:
                cursor.execute("""
                    INSERT INTO bot_chat_assignments (bot_name, chat_jid, answer_owner_messages)
                    VALUES (?, ?, ?)
                """, (bot_name, chat_jid, 1 if answer_owner_messages else 0))
            
            conn.commit()
            conn.close()
            logger.info(f"Set bot answer_owner_messages: {bot_name} -> {chat_jid} (answer_owner_messages={answer_owner_messages})")
            return True
        except Exception as e:
            logger.error(f"Error setting bot answer_owner_messages: {e}", exc_info=True)
            return False
    
    def get_bot_answer_owner_messages(self, bot_name: str, chat_jid: str) -> bool:
        """Get whether the bot should answer owner messages for a specific chat. Defaults to True."""
        assignment = self.get_bot_assignment(bot_name, chat_jid)
        if assignment is None:
            return True  # Default to answering owner messages
        return assignment.get('answer_owner_messages', 1) == 1
    
    def set_bot_context_message_count(
        self,
        bot_name: str,
        chat_jid: str,
        context_message_count: int
    ) -> bool:
        """Set the number of context messages to include for a bot in a specific chat."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Try to update existing assignment
            cursor.execute("""
                UPDATE bot_chat_assignments 
                SET context_message_count = ?
                WHERE bot_name = ? AND chat_jid = ?
            """, (context_message_count, bot_name, chat_jid))
            
            # If no rows updated, insert new assignment
            if cursor.rowcount == 0:
                cursor.execute("""
                    INSERT INTO bot_chat_assignments (bot_name, chat_jid, context_message_count)
                    VALUES (?, ?, ?)
                """, (bot_name, chat_jid, context_message_count))
            
            conn.commit()
            conn.close()
            logger.info(f"Set bot context_message_count: {bot_name} -> {chat_jid} (count={context_message_count})")
            return True
        except Exception as e:
            logger.error(f"Error setting bot context_message_count: {e}", exc_info=True)
            return False
    
    def get_bot_context_message_count(self, bot_name: str, chat_jid: str) -> int:
        """Get the number of context messages to include for a bot in a specific chat. Defaults to 0."""
        assignment = self.get_bot_assignment(bot_name, chat_jid)
        if assignment is None:
            return 0  # Default to no context
        return assignment.get('context_message_count', 0)
    
    def get_bot_assignment(self, bot_name: str, chat_jid: str) -> Optional[Dict[str, Any]]:
        """Get a specific bot-chat assignment."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM bot_chat_assignments 
            WHERE bot_name = ? AND chat_jid = ?
        """, (bot_name, chat_jid))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def is_bot_running_in_db(self, bot_name: str, chat_jid: str) -> bool:
        """Check if a bot is marked as running in the database for a specific chat."""
        assignment = self.get_bot_assignment(bot_name, chat_jid)
        return assignment is not None and assignment.get('running', 0) == 1
    
    def get_running_bots_for_chat(self, chat_jid: str) -> List[str]:
        """Get list of bot names that are marked as running for a specific chat."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT bot_name FROM bot_chat_assignments 
            WHERE chat_jid = ? AND running = 1
        """, (chat_jid,))
        rows = cursor.fetchall()
        conn.close()
        return [row[0] for row in rows]
    
    def get_running_chats_for_bot(self, bot_name: str) -> List[str]:
        """Get list of chat JIDs where the bot is marked as running."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT chat_jid FROM bot_chat_assignments 
            WHERE bot_name = ? AND running = 1
        """, (bot_name,))
        rows = cursor.fetchall()
        conn.close()
        return [row[0] for row in rows]
    
    def list_assignments_for_chat(self, chat_jid: str) -> List[Dict[str, Any]]:
        """List all bot assignments for a specific chat."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM bot_chat_assignments 
            WHERE chat_jid = ?
            ORDER BY bot_name
        """, (chat_jid,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def list_assignments_for_bot(self, bot_name: str) -> List[Dict[str, Any]]:
        """List all chat assignments for a specific bot."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM bot_chat_assignments 
            WHERE bot_name = ?
            ORDER BY chat_jid
        """, (bot_name,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def delete_assignment(self, bot_name: str, chat_jid: str) -> bool:
        """Delete a bot-chat assignment."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM bot_chat_assignments 
                WHERE bot_name = ? AND chat_jid = ?
            """, (bot_name, chat_jid))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error deleting assignment: {e}", exc_info=True)
            return False

