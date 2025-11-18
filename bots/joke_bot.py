"""Joke bot that responds with jokes."""

import logging
from typing import Dict, Any, Optional, List

from core.bot_base import BotBase

logger = logging.getLogger(__name__)


class JokeBot(BotBase):
    """Bot that responds to every message with a joke."""
    
    NAME = "joke"
    PREFIX = "[joke]"
    
    def process_message(self, message: Dict[str, Any], history: Optional[List[Dict[str, Any]]] = None) -> Optional[str]:
        """
        Process a message by generating a joke response.
        
        Args:
            message: The message dict from WhatsApp API
            history: Optional list of previous messages for context
        
        Returns:
            A joke, or None if generation fails
        """
        msg_text = message.get("content", "")
        if not msg_text:
            return None
        
        # If history is provided, use it for context-aware jokes
        if history:
            system_prompt = """You are a funny comedian. Generate a short, funny, and appropriate joke.
The joke should be light-hearted, family-friendly, and not offensive.
Keep it under 200 characters if possible.
Consider the conversation context to make the joke more relevant and contextual.
You can reference topics or themes from the conversation.

Respond with ONLY the joke, no explanations.
The joke should follow the language of the current message."""
            
            # Call LLM with history for contextual jokes
            joke = self.llm.call_with_history(
                system_prompt=system_prompt,
                current_message=msg_text,
                history=history
            )
        else:
            # No history - generate generic joke
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

