"""Bot manager for lifecycle management and monitoring across multiple chats."""

import importlib
import logging
import threading
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Type, Tuple
import sys

from core.bot_base import BotBase
from core.whatsapp_client import WhatsAppClient
from core.llm_service import LLMService
from core.database import MessageDatabase

logger = logging.getLogger(__name__)


class BotLogHandler(logging.Handler):
    """Custom log handler that stores logs in memory."""
    
    def __init__(self, bot_name: str, chat_jid: str, max_logs: int = 100):
        super().__init__()
        self.bot_name = bot_name
        self.chat_jid = chat_jid
        self.logs = deque(maxlen=max_logs)
    
    def emit(self, record):
        """Store log record."""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "message": self.format(record)
        }
        self.logs.append(log_entry)


class BotManager:
    """Manages bot lifecycle and monitoring across multiple chats."""
    
    def __init__(
        self,
        whatsapp_client: WhatsAppClient,
        llm_service: LLMService,
        database: MessageDatabase,
        bot_device_id: str,
        poll_interval: int = 5
    ):
        self.whatsapp_client = whatsapp_client
        self.llm_service = llm_service
        self.database = database
        self.bot_device_id = bot_device_id
        self.poll_interval = poll_interval
        
        # Store bot instances by (bot_name, chat_jid) tuple
        self.bots: Dict[Tuple[str, str], BotBase] = {}
        self.bot_threads: Dict[Tuple[str, str], threading.Thread] = {}
        self.bot_classes: Dict[str, Type[BotBase]] = {}
        self.bot_log_handlers: Dict[Tuple[str, str], BotLogHandler] = {}
        self.bot_start_times: Dict[Tuple[str, str], float] = {}
        
        self._discover_bots()
    
    def _discover_bots(self):
        """Discover available bot classes by scanning the bots directory."""
        bots_dir = Path(__file__).parent.parent / "bots"
        
        if not bots_dir.exists():
            logger.warning(f"Bots directory not found: {bots_dir}")
            return
        
        # Add bots directory to Python path
        bots_parent = str(bots_dir.parent)
        if bots_parent not in sys.path:
            sys.path.insert(0, bots_parent)
        
        # Scan for bot files
        for bot_file in bots_dir.glob("*_bot.py"):
            try:
                module_name = f"bots.{bot_file.stem}"
                module = importlib.import_module(module_name)
                
                # Find bot classes in the module
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and 
                        issubclass(attr, BotBase) and 
                        attr is not BotBase):
                        bot_name = attr.NAME
                        self.bot_classes[bot_name] = attr
                        logger.info(f"Discovered bot: {bot_name} ({attr.__name__})")
            
            except Exception as e:
                logger.error(f"Error loading bot from {bot_file}: {e}", exc_info=True)
        
        logger.info(f"Discovered {len(self.bot_classes)} bot(s)")
    
    def get_available_bots(self) -> List[str]:
        """Get list of available bot names."""
        return list(self.bot_classes.keys())
    
    def get_bot_status(self, bot_name: str, chat_jid: str) -> Optional[Dict]:
        """Get status of a specific bot instance for a chat."""
        if bot_name not in self.bot_classes:
            return None
        
        bot_class = self.bot_classes[bot_name]
        bot_key = (bot_name, chat_jid)
        is_running = bot_key in self.bots and bot_key in self.bot_threads
        
        # Get answer_owner_messages setting from database
        answer_owner_messages = self.database.get_bot_answer_owner_messages(bot_name, chat_jid)
        
        # Get context_message_count setting from database
        context_message_count = self.database.get_bot_context_message_count(bot_name, chat_jid)
        
        status = {
            "name": bot_name,
            "chat_jid": chat_jid,
            "display_name": bot_class.__name__,
            "status": "running" if is_running else "stopped",
            "prefix": bot_class.PREFIX,
            "uptime_seconds": None,
            "answer_owner_messages": answer_owner_messages,
            "context_message_count": context_message_count
        }
        
        if is_running and bot_key in self.bot_start_times:
            uptime = time.time() - self.bot_start_times[bot_key]
            status["uptime_seconds"] = int(uptime)
        
        return status
    
    def get_all_bot_statuses(self) -> List[Dict]:
        """Get status of all running bot instances."""
        statuses = []
        for (bot_name, chat_jid) in self.bots.keys():
            status = self.get_bot_status(bot_name, chat_jid)
            if status:
                statuses.append(status)
        return statuses
    
    def get_bot_statuses_for_chat(self, chat_jid: str) -> List[Dict]:
        """Get status of all bots (both available and running) for a specific chat."""
        statuses = []
        for bot_name in self.bot_classes.keys():
            status = self.get_bot_status(bot_name, chat_jid)
            if status:
                statuses.append(status)
        return statuses
    
    def start_bot(self, bot_name: str, chat_jid: str) -> bool:
        """Start a bot for a specific chat."""
        if bot_name not in self.bot_classes:
            logger.error(f"Bot not found: {bot_name}")
            return False
        
        bot_key = (bot_name, chat_jid)
        if bot_key in self.bots:
            logger.info(f"Bot already running: {bot_name} for chat {chat_jid}")
            return True  # Already running = success
        
        try:
            # Create bot instance
            bot_class = self.bot_classes[bot_name]
            bot = bot_class(
                whatsapp_client=self.whatsapp_client,
                llm_service=self.llm_service,
                database=self.database,
                chat_jid=chat_jid,
                poll_interval=self.poll_interval,
                bot_device_id=self.bot_device_id
            )
            
            # Set up log handler for this bot
            log_handler = BotLogHandler(bot_name, chat_jid)
            log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            
            # Add handler to root logger
            bot_logger = logging.getLogger()
            bot_logger.addHandler(log_handler)
            
            self.bot_log_handlers[bot_key] = log_handler
            
            # Start bot in a thread
            thread = threading.Thread(
                target=bot.run, 
                daemon=True, 
                name=f"Bot-{bot_name}-{chat_jid}"
            )
            thread.start()
            
            self.bots[bot_key] = bot
            self.bot_threads[bot_key] = thread
            self.bot_start_times[bot_key] = time.time()
            
            # Mark bot as running in database
            self.database.set_bot_running_state(bot_name, chat_jid, running=True)
            
            logger.info(f"Started bot: {bot_name} for chat {chat_jid}")
            return True
        
        except Exception as e:
            logger.error(f"Error starting bot {bot_name} for chat {chat_jid}: {e}", exc_info=True)
            return False
    
    def stop_bot(self, bot_name: str, chat_jid: str, update_db: bool = True) -> bool:
        """Stop a bot for a specific chat.
        
        Args:
            bot_name: Name of the bot to stop
            chat_jid: Chat JID where bot is running
            update_db: Whether to update the running state in database (default True)
        """
        bot_key = (bot_name, chat_jid)
        if bot_key not in self.bots:
            logger.info(f"Bot already stopped: {bot_name} for chat {chat_jid}")
            return True  # Already stopped = success
        
        try:
            # Signal bot to stop
            bot = self.bots[bot_key]
            bot.stop()
            
            # Wait for thread to finish (with timeout)
            thread = self.bot_threads[bot_key]
            thread.join(timeout=10)
            
            # Remove log handler
            if bot_key in self.bot_log_handlers:
                log_handler = self.bot_log_handlers[bot_key]
                bot_logger = logging.getLogger()
                bot_logger.removeHandler(log_handler)
                del self.bot_log_handlers[bot_key]
            
            # Clean up
            del self.bots[bot_key]
            del self.bot_threads[bot_key]
            if bot_key in self.bot_start_times:
                del self.bot_start_times[bot_key]
            
            # Mark bot as not running in database (only if requested)
            if update_db:
                self.database.set_bot_running_state(bot_name, chat_jid, running=False)
            
            logger.info(f"Stopped bot: {bot_name} for chat {chat_jid} (db_updated={update_db})")
            return True
        
        except Exception as e:
            logger.error(f"Error stopping bot {bot_name} for chat {chat_jid}: {e}", exc_info=True)
            return False
    
    def get_bot_logs(self, bot_name: str, chat_jid: str, limit: int = 50) -> List[Dict]:
        """Get recent logs for a bot instance."""
        bot_key = (bot_name, chat_jid)
        if bot_key not in self.bot_log_handlers:
            return []
        
        handler = self.bot_log_handlers[bot_key]
        logs = list(handler.logs)
        
        # Return most recent logs first
        logs.reverse()
        return logs[:limit]
    
    def start_running_bots(self):
        """Start all bots that were marked as running in the database."""
        chats = self.database.list_chats()
        started_count = 0
        
        for chat in chats:
            chat_jid = chat['chat_jid']
            running_bots = self.database.get_running_bots_for_chat(chat_jid)
            
            for bot_name in running_bots:
                if bot_name in self.bot_classes:
                    if self.start_bot(bot_name, chat_jid):
                        started_count += 1
                else:
                    logger.warning(f"Running bot not found: {bot_name}")
        
        logger.info(f"Started {started_count} bot instance(s) from previous session")
    
    def stop_all(self, update_db: bool = False):
        """Stop all running bots.
        
        Args:
            update_db: Whether to update the running state in database (default False).
                      Set to False during shutdown to preserve bot state for next restart.
        """
        bot_keys = list(self.bots.keys())
        for bot_name, chat_jid in bot_keys:
            self.stop_bot(bot_name, chat_jid, update_db=update_db)
