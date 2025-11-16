"""Translation bot for Portuguese-English translation."""

import logging
from typing import Dict, Any, Optional

from core.bot_base import BotBase

logger = logging.getLogger(__name__)


class TranslationBot(BotBase):
    """Bot that translates messages between Portuguese and English."""
    
    NAME = "translation"
    PREFIX = "[ai]"
    
    def process_message(self, message: Dict[str, Any]) -> Optional[str]:
        """
        Process a message by translating it between English and Portuguese.
        
        Args:
            message: The message dict from WhatsApp API
        
        Returns:
            The translated text, or None if translation fails
        """
        msg_text = message.get("content", "")
        if not msg_text:
            return None
        
        # Check if it's an image message with caption
        media_type = message.get("media_type")
        if media_type == "image":
            # For now, just translate the caption if present
            # Future: could also extract text from image
            if not msg_text:
                return None
        
        # Define the translation prompt
        prompt = f"""You are a translation assistant. Your task is to:
1. Detect if the following message is in English or Portuguese
2. Translate it to the other language (English → Portuguese, Portuguese → English)
3. Return ONLY the translation, without any explanations or notes

Message to translate:
{msg_text}

Respond with ONLY the translated text."""
        
        # Call LLM to translate
        translated_text = self.llm.call(prompt)
        
        if not translated_text:
            logger.error(f"[{self.NAME}] Failed to translate message")
            return None
        
        logger.info(f"[{self.NAME}] Translated: {msg_text[:30]}... -> {translated_text[:30]}...")
        return translated_text

