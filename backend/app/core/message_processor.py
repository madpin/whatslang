"""Message processor with polling and routing"""

import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.bot_manager import BotManager
from app.models import Chat, ProcessedMessage, ChatType
from app.schemas.message import Message
from app.database import get_db_context

logger = logging.getLogger(__name__)


class MessageProcessor:
    """Polls WhatsApp API and routes messages to bots"""
    
    def __init__(self, bot_manager: BotManager):
        """
        Initialize message processor.
        
        Args:
            bot_manager: Bot manager instance
        """
        self.bot_manager = bot_manager
        self.whatsapp = bot_manager.whatsapp_client
        self.running = False
        self.task: Optional[asyncio.Task] = None
        self.is_first_run = True  # Skip translating history on first run
    
    async def start(self):
        """Start the message processor background task"""
        if self.running:
            logger.warning("Message processor already running")
            return
        
        self.running = True
        self.task = asyncio.create_task(self._poll_loop())
        logger.info("Message processor started")
    
    async def stop(self):
        """Stop the message processor background task"""
        if not self.running:
            return
        
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        
        logger.info("Message processor stopped")
    
    async def _poll_loop(self):
        """Main polling loop"""
        logger.info(f"Starting message polling loop (interval: {settings.poll_interval_seconds}s)")
        
        while self.running:
            try:
                await self._poll_messages()
                await asyncio.sleep(settings.poll_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in polling loop: {e}", exc_info=True)
                await asyncio.sleep(settings.poll_interval_seconds)
    
    async def _poll_messages(self):
        """Poll messages from all registered chats"""
        async with get_db_context() as db:
            # Get all chats from database
            stmt = select(Chat)
            result = await db.execute(stmt)
            chats = result.scalars().all()
            
            if not chats:
                logger.debug("No chats registered yet")
                return
            
            # Poll messages for each chat
            for chat in chats:
                try:
                    await self._poll_chat_messages(chat, db)
                except Exception as e:
                    logger.error(f"Error polling chat {chat.jid}: {e}", exc_info=True)
    
    async def _poll_chat_messages(self, chat: Chat, db: AsyncSession):
        """
        Poll messages for a specific chat.
        
        Args:
            chat: Chat model
            db: Database session
        """
        # Fetch recent messages from WhatsApp API
        messages = await self.whatsapp.get_messages(
            chat.jid,
            limit=settings.message_limit_per_poll
        )
        
        if not messages:
            return
        
        # On first run, just mark existing messages as seen without processing
        if self.is_first_run:
            logger.info(f"First run: marking {len(messages)} existing messages as seen for chat {chat.jid}")
            for msg_data in messages:
                msg_id = msg_data.get("id")
                if msg_id:
                    await self._mark_as_processed(
                        message_id=msg_id,
                        chat_id=chat.id,
                        content=msg_data.get("content", ""),
                        db=db
                    )
            return
        
        # Process messages in chronological order (oldest first)
        # API likely returns newest first, so reverse
        messages.reverse()
        
        for msg_data in messages:
            try:
                await self._process_message(chat, msg_data, db)
            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
    
    async def _process_message(
        self,
        chat: Chat,
        msg_data: Dict[str, Any],
        db: AsyncSession
    ):
        """
        Process a single message.
        
        Args:
            chat: Chat model
            msg_data: Message data from WhatsApp API
            db: Database session
        """
        message_id = msg_data.get("id")
        if not message_id:
            return
        
        # Check if already processed
        if await self._is_processed(message_id, db):
            return
        
        msg_content = msg_data.get("content", "")
        
        # Skip empty messages (unless it's media)
        media_type = msg_data.get("media_type")
        if not msg_content and not media_type:
            return
        
        logger.info(f"Processing message {message_id} from chat {chat.jid}")
        
        # Convert to Message schema
        message = Message(
            id=message_id,
            chat_jid=chat.jid,
            sender_jid=msg_data.get("from", ""),
            content=msg_content or None,
            media_type=media_type,
            media_url=msg_data.get("url"),
            reply_to_id=msg_data.get("reply_to_message_id"),
            timestamp=datetime.fromisoformat(msg_data.get("timestamp", datetime.now().isoformat())),
            message_metadata=msg_data
        )
        
        # Get active bots for this chat
        bot_assignments = await self.bot_manager.get_bots_for_chat(chat.jid, db)
        
        if not bot_assignments:
            logger.debug(f"No active bots for chat {chat.jid}")
            # Mark as processed even if no bots
            await self._mark_as_processed(
                message_id=message_id,
                chat_id=chat.id,
                content=msg_content,
                db=db
            )
            return
        
        # Execute bots in priority order
        for bot_model, chat_bot, bot_instance in bot_assignments:
            try:
                logger.debug(f"Executing bot {bot_model.name} ({bot_model.type}) for message {message_id}")
                
                # Process message through bot
                response = await bot_instance.process_message(message)
                
                if response:
                    # Send response
                    success = await self.whatsapp.send_message(
                        phone=chat.jid,
                        message=response.content,
                        reply_message_id=response.reply_to or message_id
                    )
                    
                    if success:
                        logger.info(f"Bot {bot_model.name} sent response for message {message_id}")
                        
                        # Mark as processed with response
                        await self._mark_as_processed(
                            message_id=message_id,
                            chat_id=chat.id,
                            bot_id=bot_model.id,
                            content=msg_content,
                            response=response.content,
                            db=db
                        )
                    else:
                        logger.error(f"Failed to send response from bot {bot_model.name}")
                else:
                    logger.debug(f"Bot {bot_model.name} returned no response")
            
            except Exception as e:
                logger.error(f"Error executing bot {bot_model.name}: {e}", exc_info=True)
        
        # Mark as processed even if no bot responded
        if not await self._is_processed(message_id, db):
            await self._mark_as_processed(
                message_id=message_id,
                chat_id=chat.id,
                content=msg_content,
                db=db
            )
    
    async def _is_processed(self, message_id: str, db: AsyncSession) -> bool:
        """
        Check if a message has already been processed.
        
        Args:
            message_id: WhatsApp message ID
            db: Database session
            
        Returns:
            True if already processed, False otherwise
        """
        stmt = select(ProcessedMessage).where(ProcessedMessage.message_id == message_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none() is not None
    
    async def _mark_as_processed(
        self,
        message_id: str,
        chat_id: str,
        content: str = "",
        bot_id: Optional[str] = None,
        response: Optional[str] = None,
        db: AsyncSession = None
    ):
        """
        Mark a message as processed.
        
        Args:
            message_id: WhatsApp message ID
            chat_id: Chat ID
            content: Original message content
            bot_id: Optional bot ID that processed the message
            response: Optional bot response
            db: Database session
        """
        processed_msg = ProcessedMessage(
            message_id=message_id,
            chat_id=chat_id,
            bot_id=bot_id,
            content=content[:1000] if content else None,  # Truncate long content
            response=response[:1000] if response else None,
            message_metadata={}
        )
        
        db.add(processed_msg)
        await db.flush()
        
        logger.debug(f"Marked message {message_id} as processed")
    
    def mark_initialization_complete(self):
        """Mark that initialization is complete (start processing new messages)"""
        self.is_first_run = False
        logger.info("Message processor initialization complete")

