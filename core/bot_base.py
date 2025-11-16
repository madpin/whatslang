"""Base class for all WhatsApp bots."""

import time
import logging
import signal
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pathlib import Path

from core.whatsapp_client import WhatsAppClient
from core.database import MessageDatabase
from core.llm_service import LLMService

logger = logging.getLogger(__name__)


class BotBase(ABC):
    """Abstract base class for WhatsApp bots."""
    
    # Bots must define these class attributes
    NAME = "base_bot"
    PREFIX = "[bot]"
    MAX_MESSAGE_LENGTH = 4095  # WhatsApp message length limit
    
    def __init__(
        self,
        whatsapp_client: WhatsAppClient,
        llm_service: LLMService,
        database: MessageDatabase,
        chat_jid: str,
        poll_interval: int = 5,
        bot_device_id: Optional[str] = None
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
    def process_message(self, message: Dict[str, Any]) -> Optional[str]:
        """
        Process a message and return the response text.
        
        Args:
            message: The message dict from WhatsApp API
        
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
                if remaining[i] in '.!?\n':
                    split_pos = i + 1
                    break
            else:
                # Try to split at word boundary
                for i in range(max_content_length - 1, max(0, max_content_length - 100), -1):
                    if remaining[i] == ' ':
                        split_pos = i + 1
                        break
            
            chunks.append(remaining[:split_pos].rstrip())
            remaining = remaining[split_pos:].lstrip()
        
        # Add pagination headers
        total_chunks = len(chunks)
        if total_chunks == 1:
            return [f"{prefix} {chunks[0]}"]
        
        return [f"{prefix} {i+1}/{total_chunks} {chunk}" for i, chunk in enumerate(chunks)]
    
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
        
        # Get message content
        msg_text = message.get("content", "")
        if not msg_text:
            return False
        
        # Skip messages from bots (check sender)
        if self.bot_device_id:
            sender_jid = message.get("from", "") or message.get("sender", "")
            if sender_jid and self.whatsapp.is_bot_message(sender_jid, self.bot_device_id):
                logger.debug(f"[{self.NAME}] Skipping message from bot: {sender_jid}")
                return False
        
        # Skip messages that start with any bot prefix [*]
        if msg_text.startswith("[") and "]" in msg_text[:20]:
            return False
        
        # Check if message is from owner and if bot should answer owner messages
        is_from_me = message.get("is_from_me", False)
        if is_from_me:
            # Get the answer_owner_messages setting from database
            answer_owner_messages = self.db.get_bot_answer_owner_messages(self.NAME, self.chat_jid)
            if not answer_owner_messages:
                logger.debug(f"[{self.NAME}] Skipping message from owner (answer_owner_messages=False)")
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
            
            # Let the bot process the message
            response_text = self.process_message(message)
            
            if not response_text:
                logger.info(f"[{self.NAME}] No response generated for message {message_id}")
                # Still mark as processed to avoid re-processing
                self.db.mark_processed(
                    message_id=message_id,
                    bot_name=self.NAME,
                    original_text=msg_text,
                    response_text="[no response]",
                    metadata=""
                )
                return
            
            # Split message if needed and send chunks
            message_chunks = self.split_message(response_text)
            logger.info(f"[{self.NAME}] Sending response in {len(message_chunks)} chunk(s)")
            
            success = True
            for i, chunk in enumerate(message_chunks, 1):
                logger.info(f"[{self.NAME}] Sending chunk {i}/{len(message_chunks)}: {len(chunk)} chars")
                success = self.whatsapp.send_message(
                    phone=self.chat_jid,
                    message=chunk,
                    reply_message_id=message_id
                )
                if not success:
                    logger.error(f"[{self.NAME}] Failed to send chunk {i} for message {message_id}")
                    break
                time.sleep(0.5)  # Small delay between chunks
            
            if success:
                # Mark as processed
                self.db.mark_processed(
                    message_id=message_id,
                    bot_name=self.NAME,
                    original_text=msg_text,
                    response_text=response_text[:500],  # Truncate for storage
                    metadata=""
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
                        logger.info(f"[{self.NAME}] First run: marking {len(messages)} existing messages as seen")
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
                                    metadata="startup"
                                )
                        self.is_first_run = False
                        logger.info(f"[{self.NAME}] Initialization complete. Now monitoring for new messages...")
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

