"""Translation bot for Portuguese-English translation."""

import logging
from typing import Dict, Any, Optional, List

from core.bot_base import BotBase

logger = logging.getLogger(__name__)


class TranslationBot(BotBase):
    """Bot that translates messages between Portuguese and English."""
    
    NAME = "translation"
    PREFIX = "[ai]"
    
    def process_message(self, message: Dict[str, Any], history: Optional[List[Dict[str, Any]]] = None) -> Optional[str]:
        """
        Process a message by translating it between English and Portuguese.
        
        Args:
            message: The message dict from WhatsApp API
            history: Optional list of previous messages for context
        
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
        
        # If history is provided, use it for context-aware translation
        if history:
            system_prompt = """You are a translation assistant. Your task is to:
1. Consider the conversation context provided
2. Detect if the current message is in English or Portuguese
3. Translate it to the other language (English → Portuguese, Portuguese → English)
4. Use the conversation context to better understand references, pronouns, and implied meanings
5. Return ONLY the translation, without any explanations or notes"""
            
            # Call LLM with history
            translated_text = self.llm.call_with_history(
                system_prompt=system_prompt,
                current_message=msg_text,
                history=history
            )
        else:
            # No history - use simple translation
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

