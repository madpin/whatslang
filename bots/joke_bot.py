"""Joke bot that responds with jokes."""

import logging
from typing import Dict, Any, Optional

from core.bot_base import BotBase

logger = logging.getLogger(__name__)


class JokeBot(BotBase):
    """Bot that responds to every message with a joke."""
    
    NAME = "joke"
    PREFIX = "[joke]"
    
    def process_message(self, message: Dict[str, Any]) -> Optional[str]:
        """
        Process a message by generating a joke response.
        
        Args:
            message: The message dict from WhatsApp API
        
        Returns:
            A joke, or None if generation fails
        """
        msg_text = message.get("content", "")
        if not msg_text:
            return None
        
        # Define the joke prompt
        prompt = """You are a funny comedian. Generate a short, funny, and appropriate joke.
The joke should be light-hearted, family-friendly, and not offensive.
Keep it under 200 characters if possible.

Respond with ONLY the joke, no explanations.
The joke should follow the language of the message."""
        
        # Call LLM to generate joke
        joke = self.llm.call(prompt)
        
        if not joke:
            logger.error(f"[{self.NAME}] Failed to generate joke")
            return None
        
        logger.info(f"[{self.NAME}] Generated joke: {joke[:50]}...")
        return joke

