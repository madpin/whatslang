"""Base class for all WhatsApp bots."""

import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from core.database import MessageDatabase
from core.llm_service import LLMService
from core.whatsapp_client import WhatsAppClient

logger = logging.getLogger(__name__)


class BotBase(ABC):
    """Abstract base class for WhatsApp bots."""

    # Bots must define these class attributes
    NAME = "base_bot"
    PREFIX = "[bot]"
    DESCRIPTION = ""
    SYSTEM_PROMPT = ""
    MAX_MESSAGE_LENGTH = 4095  # WhatsApp message length limit

    def __init__(
        self,
        whatsapp_client: WhatsAppClient,
        llm_service: LLMService,
        database: MessageDatabase,
        chat_jid: str,
        poll_interval: int = 5,
        bot_device_id: Optional[str] = None,
    ):
        self.whatsapp = whatsapp_client
        self.llm = llm_service
        self.db = database
        self.chat_jid = chat_jid
        self.poll_interval = poll_interval
        self.bot_device_id = bot_device_id
        self.is_first_run = True
        self.should_exit = False

    @abstractmethod
    def process_message(
        self, message: Dict[str, Any], history: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[str]:
        """
        Process a message and return the response text.

        Args:
            message: The message dict from WhatsApp API
            history: Optional list of previous messages for context

        Returns:
            The response text to send, or None to skip
        """
        pass

    def split_message(self, text: str, prefix: Optional[str] = None) -> List[str]:
        """
        Split a long message into chunks that fit within WhatsApp's message limit.

        Args:
            text: The text to split
            prefix: The prefix to add to each chunk (defaults to self.PREFIX)

        Returns:
            List of message chunks with pagination headers
        """
        if prefix is None:
            prefix = self.PREFIX

        # Calculate available space for content after prefix and pagination header
        # Format: "[prefix] 1/3 " or "[prefix] 10/10 "
        # Reserve space for worst case: "[prefix] 999/999 "
        header_overhead = len(prefix) + len(" 999/999 ")
        max_content_length = self.MAX_MESSAGE_LENGTH - header_overhead

        if len(text) <= max_content_length:
            # No splitting needed
            return [f"{prefix} {text}"]

        # Split into chunks
        chunks = []
        remaining = text

        while remaining:
            if len(remaining) <= max_content_length:
                chunks.append(remaining)
                break

            # Try to split at sentence boundary (. ! ?)
            split_pos = max_content_length
            for i in range(max_content_length - 1, max(0, max_content_length - 200), -1):
                if remaining[i] in ".!?\n":
                    split_pos = i + 1
                    break
            else:
                # Try to split at word boundary
                for i in range(max_content_length - 1, max(0, max_content_length - 100), -1):
                    if remaining[i] == " ":
                        split_pos = i + 1
                        break

            chunks.append(remaining[:split_pos].rstrip())
            remaining = remaining[split_pos:].lstrip()

        # Add pagination headers
        total_chunks = len(chunks)
        if total_chunks == 1:
            return [f"{prefix} {chunks[0]}"]

        return [f"{prefix} {i+1}/{total_chunks} {chunk}" for i, chunk in enumerate(chunks)]

    @staticmethod
    def _jid_user_part(jid: str) -> str:
        """User/phone id before @, ignoring device suffix (e.g. 123:45@s.whatsapp.net -> 123)."""
        if not jid:
            return ""
        if "@" in jid:
            jid = jid.split("@", 1)[0]
        return jid.split(":", 1)[0]

    @staticmethod
    def _is_group_chat(chat_jid: str) -> bool:
        return bool(chat_jid and chat_jid.endswith("@g.us"))

    def _forward_sender_display(self, message: Dict[str, Any]) -> str:
        """
        Human-readable label for forwarded context: saved contact name when possible,
        else API fields, else phone from JID.
        """
        if message.get("is_from_me", False):
            return "me"

        for key in (
            "push_name",
            "pushName",
            "PushName",
            "sender_name",
            "senderName",
            "SenderName",
        ):
            val = message.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()

        sender_jid = (
            message.get("sender_jid", "")
            or message.get("from", "")
            or message.get("sender", "")
        )
        if not sender_jid:
            return "unknown"

        # 1:1: chat row name is usually the contact name synced from WhatsApp
        if not self._is_group_chat(self.chat_jid):
            su, cu = self._jid_user_part(sender_jid), self._jid_user_part(self.chat_jid)
            if su and cu and su == cu:
                row = self.db.get_chat(self.chat_jid)
                if row:
                    cn = (row.get("chat_name") or "").strip()
                    placeholder = f"Chat {self.chat_jid}"
                    if cn and cn != placeholder:
                        return cn

        # Per-contact display name from WhatsApp API (works for groups and DMs)
        try:
            info = self.whatsapp.get_chat_info(sender_jid)
            if isinstance(info, dict):
                layers = [info]
                if isinstance(info.get("data"), dict):
                    layers.append(info["data"])
                for layer in layers:
                    for key in ("name", "Name", "subject", "Subject", "title", "Title"):
                        v = layer.get(key)
                        if isinstance(v, str) and v.strip():
                            return v.strip()
        except Exception as e:
            logger.debug(f"[{self.NAME}] get_chat_info for forward label failed: {e}")

        if "@" in sender_jid:
            return sender_jid.split("@")[0]
        return sender_jid

    def get_message_history(self, current_message_id: str, count: int) -> List[Dict[str, Any]]:
        """
        Retrieve message history from WhatsApp for context.

        Args:
            current_message_id: The ID of the current message being processed
            count: Number of previous messages to retrieve

        Returns:
            List of formatted history messages, excluding the current message
        """
        if count <= 0:
            return []

        try:
            # Fetch more messages than needed to account for filtering
            fetch_limit = count + 10
            messages = self.whatsapp.get_messages(self.chat_jid, limit=fetch_limit)

            if not messages:
                logger.debug(f"[{self.NAME}] No messages fetched for history")
                return []

            # Filter out current message and format history
            history = []
            for msg in messages:
                msg_id = msg.get("id")
                if msg_id == current_message_id:
                    continue

                content = msg.get("content", "")
                if not content:
                    continue

                # Check if message is from a bot (has bot prefix)
                is_bot = False
                if content.startswith("[") and "]" in content[:20]:
                    is_bot = True

                # Get sender information
                sender = msg.get("sender_jid", "") or msg.get("sender", "") or msg.get("from", "")
                is_from_me = msg.get("is_from_me", False)

                history.append(
                    {
                        "content": content,
                        "sender": sender,
                        "is_from_me": is_from_me,
                        "is_bot": is_bot,
                        "timestamp": msg.get("timestamp") or msg.get("time"),
                    }
                )

                # Stop once we have enough history messages
                if len(history) >= count:
                    break

            # Reverse to get chronological order (oldest first)
            history.reverse()

            logger.info(f"[{self.NAME}] Retrieved {len(history)} history messages for context")
            return history

        except Exception as e:
            logger.error(f"[{self.NAME}] Error fetching message history: {e}", exc_info=True)
            return []

    def should_process_message(self, message: Dict[str, Any]) -> bool:
        """
        Determine if a message should be processed by this bot.

        Default implementation:
        - Skip if no message ID
        - Skip if already processed by this bot
        - Skip if message is from a bot (including this bot)
        - Skip if message starts with any [*] prefix (from bots)
        - Skip if no content
        - Skip if message is from owner and bot is set to not answer owner messages

        Bots can override this to customize filtering logic.
        """
        message_id = message.get("id")
        if not message_id:
            return False

        # Skip if already processed by this bot
        if self.db.is_processed(message_id, self.NAME):
            return False

        # Check if message has content OR media
        msg_text = message.get("content", "")
        has_media = message.get("media_type") is not None

        # Skip if no content AND no media
        if not msg_text and not has_media:
            return False

        # Skip messages from bots (check sender)
        if self.bot_device_id:
            sender_jid = message.get("sender_jid", "") or message.get("from", "") or message.get("sender", "")
            if sender_jid and self.whatsapp.is_bot_message(sender_jid, self.bot_device_id):
                logger.debug(f"[{self.NAME}] Skipping message from bot: {sender_jid}")
                return False

        # Skip messages that start with any bot prefix [*] (only for text messages)
        if msg_text and msg_text.startswith("[") and "]" in msg_text[:20]:
            return False

        # Check if message is from owner and if bot should answer owner messages
        is_from_me = message.get("is_from_me", False)
        if is_from_me:
            # Get the answer_owner_messages setting from database
            answer_owner_messages = self.db.get_bot_answer_owner_messages(self.NAME, self.chat_jid)
            if not answer_owner_messages:
                logger.debug(
                    f"[{self.NAME}] Skipping message from owner (answer_owner_messages=False)"
                )
                return False

        return True

    def handle_message(self, message: Dict[str, Any]):
        """
        Handle a single message: process it and send reply.
        This is the main entry point for processing.
        """
        message_id = message.get("id")
        msg_text = message.get("content", "")

        logger.info(f"[{self.NAME}] Processing message: {msg_text[:50]}...")

        try:
            # Update message activity for this chat
            message_time = message.get("timestamp") or message.get("time")
            self.db.update_message_activity(self.chat_jid, message_time=message_time)

            # Check if context is enabled for this bot
            context_count = self.db.get_bot_context_message_count(self.NAME, self.chat_jid)
            history = None

            if context_count > 0:
                logger.info(f"[{self.NAME}] Fetching {context_count} context messages")
                history = self.get_message_history(message_id, context_count)

            # Let the bot process the message with optional history
            response_text = self.process_message(message, history=history)

            if not response_text:
                logger.info(f"[{self.NAME}] No response generated for message {message_id}")
                # Still mark as processed to avoid re-processing
                self.db.mark_processed(
                    message_id=message_id,
                    bot_name=self.NAME,
                    original_text=msg_text,
                    response_text="[no response]",
                    metadata="",
                )
                return

            # Determine where to send the response
            response_chat_jid = self.db.get_bot_response_chat_jid(self.NAME, self.chat_jid)
            target_chat = response_chat_jid if response_chat_jid else self.chat_jid

            # If forwarding to another chat, send the original message as context first
            if response_chat_jid:
                sender = self._forward_sender_display(message)
                fwd_text = f"[Fwd from {sender}]: {msg_text}" if msg_text else f"[Fwd from {sender}]: [media]"
                logger.info(f"[{self.NAME}] Forwarding original message to {response_chat_jid}")
                fwd_success = self.whatsapp.send_message(phone=response_chat_jid, message=fwd_text)
                if not fwd_success:
                    logger.error(
                        f"[{self.NAME}] Failed to forward original message to {response_chat_jid} "
                        f"for message {message_id}, aborting response"
                    )
                    return
                time.sleep(0.5)

            # Split message if needed and send chunks
            message_chunks = self.split_message(response_text)
            logger.info(f"[{self.NAME}] Sending response in {len(message_chunks)} chunk(s) to {target_chat}")

            success = True
            for i, chunk in enumerate(message_chunks, 1):
                logger.info(
                    f"[{self.NAME}] Sending chunk {i}/{len(message_chunks)}: {len(chunk)} chars"
                )
                reply_id = message_id if not response_chat_jid else None
                success = self.whatsapp.send_message(
                    phone=target_chat, message=chunk, reply_message_id=reply_id
                )
                if not success:
                    logger.error(f"[{self.NAME}] Failed to send chunk {i} for message {message_id}")
                    break
                time.sleep(0.5)  # Small delay between chunks

            if success:
                self.db.mark_processed(
                    message_id=message_id,
                    bot_name=self.NAME,
                    original_text=msg_text,
                    response_text=response_text[:500],
                    metadata=f"forwarded_to={response_chat_jid}" if response_chat_jid else "",
                )
                logger.info(f"[{self.NAME}] Successfully processed message {message_id}")
            else:
                logger.error(f"[{self.NAME}] Failed to send response for message {message_id}")

        except Exception as e:
            logger.error(f"[{self.NAME}] Error handling message {message_id}: {e}", exc_info=True)

    def run(self):
        """
        Main loop: poll for messages and process them.
        This method runs continuously until should_exit is set.
        """
        logger.info(f"[{self.NAME}] Starting bot for chat {self.chat_jid}")
        logger.info(f"[{self.NAME}] Polling every {self.poll_interval} seconds")

        while not self.should_exit:
            try:
                # Fetch recent messages
                messages = self.whatsapp.get_messages(self.chat_jid, limit=20)

                if not messages:
                    logger.debug(f"[{self.NAME}] No messages fetched")
                else:
                    # On first run, just mark existing messages as seen without processing
                    if self.is_first_run:
                        logger.info(
                            f"[{self.NAME}] First run: marking {len(messages)} existing messages as seen"
                        )
                        for message in messages:
                            message_id = message.get("id")
                            msg_text = message.get("content", "")
                            if message_id and not self.db.is_processed(message_id, self.NAME):
                                # Mark as processed without responding
                                self.db.mark_processed(
                                    message_id=message_id,
                                    bot_name=self.NAME,
                                    original_text=msg_text[:100] if msg_text else "[no content]",
                                    response_text="[skipped - startup]",
                                    metadata="startup",
                                )
                        self.is_first_run = False
                        logger.info(
                            f"[{self.NAME}] Initialization complete. Now monitoring for new messages..."
                        )
                    else:
                        # Process messages in chronological order (oldest first)
                        # The API likely returns newest first, so reverse
                        messages.reverse()

                        for message in messages:
                            if self.should_exit:
                                break

                            if self.should_process_message(message):
                                self.handle_message(message)
                                # Small delay between processing messages
                                time.sleep(1)

                # Wait before next poll
                time.sleep(self.poll_interval)

            except Exception as e:
                logger.error(f"[{self.NAME}] Error in main loop: {e}", exc_info=True)
                time.sleep(self.poll_interval)

        logger.info(f"[{self.NAME}] Bot stopped")

    def stop(self):
        """Signal the bot to stop gracefully."""
        logger.info(f"[{self.NAME}] Received stop signal")
        self.should_exit = True
