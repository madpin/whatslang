"""Bot manager for lifecycle and registration"""

import logging
from typing import Optional, Dict, Any, List, Type
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bots import BaseBot, BotServices, AVAILABLE_BOTS
from app.models import Bot, ChatBot
from app.services import LLMService, WhatsAppClient
from app.schemas.bot import BotInfo

logger = logging.getLogger(__name__)


class BotManager:
    """Manages bot lifecycle and registration"""
    
    def __init__(self, llm_service: LLMService, whatsapp_client: WhatsAppClient):
        """
        Initialize bot manager.
        
        Args:
            llm_service: LLM service instance
            whatsapp_client: WhatsApp client instance
        """
        self.llm_service = llm_service
        self.whatsapp_client = whatsapp_client
        self.bot_registry = AVAILABLE_BOTS.copy()
    
    def register_bot(self, bot_type: str, bot_class: Type[BaseBot]):
        """
        Register a new bot type.
        
        Args:
            bot_type: Unique identifier for the bot type
            bot_class: Bot class (subclass of BaseBot)
        """
        if not issubclass(bot_class, BaseBot):
            raise ValueError(f"Bot class must be a subclass of BaseBot")
        
        self.bot_registry[bot_type] = bot_class
        logger.info(f"Registered bot type: {bot_type}")
    
    def get_available_bot_types(self) -> Dict[str, BotInfo]:
        """
        Get information about all available bot types.
        
        Returns:
            Dict mapping bot type to BotInfo
        """
        result = {}
        services = BotServices(
            llm=self.llm_service,
            whatsapp=self.whatsapp_client
        )
        
        for bot_type, bot_class in self.bot_registry.items():
            try:
                # Instantiate with empty config to get info
                bot_instance = bot_class(config={}, services=services)
                result[bot_type] = bot_instance.get_bot_info()
            except Exception as e:
                logger.error(f"Error getting info for bot type {bot_type}: {e}")
        
        return result
    
    def get_bot_instance(
        self,
        bot_type: str,
        config: Dict[str, Any],
        db: Optional[AsyncSession] = None
    ) -> Optional[BaseBot]:
        """
        Create a bot instance with the given configuration.
        
        Args:
            bot_type: Type of bot to create
            config: Bot configuration
            db: Optional database session
            
        Returns:
            Bot instance or None if type not found
        """
        bot_class = self.bot_registry.get(bot_type)
        if not bot_class:
            logger.error(f"Unknown bot type: {bot_type}")
            return None
        
        services = BotServices(
            llm=self.llm_service,
            whatsapp=self.whatsapp_client,
            db=db
        )
        
        try:
            return bot_class(config=config, services=services)
        except Exception as e:
            logger.error(f"Error creating bot instance for type {bot_type}: {e}")
            return None
    
    async def get_bots_for_chat(
        self,
        chat_jid: str,
        db: AsyncSession
    ) -> List[tuple[Bot, ChatBot, BaseBot]]:
        """
        Get all active bots for a chat, ordered by priority.
        
        Args:
            chat_jid: WhatsApp JID of the chat
            db: Database session
            
        Returns:
            List of tuples (Bot model, ChatBot assignment, Bot instance)
        """
        from app.models import Chat
        
        # Get chat by JID
        stmt = select(Chat).where(Chat.jid == chat_jid)
        result = await db.execute(stmt)
        chat = result.scalar_one_or_none()
        
        if not chat:
            logger.debug(f"Chat not found: {chat_jid}")
            return []
        
        # Get active bot assignments for this chat, ordered by priority
        stmt = (
            select(Bot, ChatBot)
            .join(ChatBot, Bot.id == ChatBot.bot_id)
            .where(ChatBot.chat_id == chat.id)
            .where(ChatBot.enabled == True)
            .where(Bot.enabled == True)
            .order_by(ChatBot.priority.asc())
        )
        
        result = await db.execute(stmt)
        assignments = result.all()
        
        bot_instances = []
        for bot_model, chat_bot in assignments:
            # Merge bot config with chat-specific overrides
            merged_config = {**bot_model.config, **chat_bot.config_override}
            
            # Create bot instance
            bot_instance = self.get_bot_instance(
                bot_type=bot_model.type,
                config=merged_config,
                db=db
            )
            
            if bot_instance:
                bot_instances.append((bot_model, chat_bot, bot_instance))
            else:
                logger.warning(f"Failed to create instance for bot {bot_model.id} ({bot_model.type})")
        
        return bot_instances
    
    async def enable_bot_for_chat(
        self,
        bot_id: str,
        chat_jid: str,
        db: AsyncSession
    ):
        """
        Enable a bot for a chat (call on_enable).
        
        Args:
            bot_id: Bot ID
            chat_jid: WhatsApp JID
            db: Database session
        """
        # Get bot
        stmt = select(Bot).where(Bot.id == bot_id)
        result = await db.execute(stmt)
        bot = result.scalar_one_or_none()
        
        if not bot:
            logger.error(f"Bot not found: {bot_id}")
            return
        
        # Create bot instance
        bot_instance = self.get_bot_instance(
            bot_type=bot.type,
            config=bot.config,
            db=db
        )
        
        if bot_instance:
            try:
                await bot_instance.on_enable(chat_jid)
                logger.info(f"Bot {bot_id} enabled for chat {chat_jid}")
            except Exception as e:
                logger.error(f"Error calling on_enable for bot {bot_id}: {e}")
    
    async def disable_bot_for_chat(
        self,
        bot_id: str,
        chat_jid: str,
        db: AsyncSession
    ):
        """
        Disable a bot for a chat (call on_disable).
        
        Args:
            bot_id: Bot ID
            chat_jid: WhatsApp JID
            db: Database session
        """
        # Get bot
        stmt = select(Bot).where(Bot.id == bot_id)
        result = await db.execute(stmt)
        bot = result.scalar_one_or_none()
        
        if not bot:
            logger.error(f"Bot not found: {bot_id}")
            return
        
        # Create bot instance
        bot_instance = self.get_bot_instance(
            bot_type=bot.type,
            config=bot.config,
            db=db
        )
        
        if bot_instance:
            try:
                await bot_instance.on_disable(chat_jid)
                logger.info(f"Bot {bot_id} disabled for chat {chat_jid}")
            except Exception as e:
                logger.error(f"Error calling on_disable for bot {bot_id}: {e}")

