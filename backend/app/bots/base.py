"""Base bot class"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from dataclasses import dataclass

from app.schemas.message import Message, Response
from app.schemas.bot import BotInfo


@dataclass
class BotServices:
    """Services available to bots"""
    llm: 'LLMService'
    whatsapp: 'WhatsAppClient'
    db: Optional[Any] = None  # AsyncSession when needed


class BaseBot(ABC):
    """Abstract base class for all bots"""
    
    def __init__(self, config: Dict[str, Any], services: BotServices):
        """
        Initialize bot with configuration and services.
        
        Args:
            config: Bot configuration (merged from global + chat-specific)
            services: Available services (LLM, WhatsApp, DB)
        """
        self.config = config
        self.services = services
    
    @abstractmethod
    async def process_message(self, message: Message) -> Optional[Response]:
        """
        Process an incoming message and return a response.
        
        Args:
            message: Incoming message to process
            
        Returns:
            Response object if bot wants to reply, None otherwise
        """
        pass
    
    @abstractmethod
    def get_bot_info(self) -> BotInfo:
        """
        Return bot metadata and configuration schema.
        
        Returns:
            BotInfo with name, description, and config schema
        """
        pass
    
    async def on_enable(self, chat_jid: str):
        """
        Called when bot is enabled for a chat.
        Override to perform initialization.
        
        Args:
            chat_jid: WhatsApp JID of the chat
        """
        pass
    
    async def on_disable(self, chat_jid: str):
        """
        Called when bot is disabled for a chat.
        Override to perform cleanup.
        
        Args:
            chat_jid: WhatsApp JID of the chat
        """
        pass

