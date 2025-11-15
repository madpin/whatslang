"""Translation bot implementation"""

import logging
from typing import Optional, List

from app.bots.base import BaseBot
from app.schemas.message import Message, Response
from app.schemas.bot import BotInfo

logger = logging.getLogger(__name__)


class TranslationBot(BaseBot):
    """Translates messages between languages"""
    
    MAX_MESSAGE_LENGTH = 4095  # WhatsApp message length limit
    
    def get_bot_info(self) -> BotInfo:
        """Return bot metadata and configuration schema"""
        return BotInfo(
            type="translation",
            name="Translation Bot",
            description="Translates messages between English and Portuguese",
            config_schema={
                "prefix": {
                    "type": "string",
                    "default": "[ai]",
                    "description": "Prefix for bot responses"
                },
                "source_languages": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": ["en", "pt"],
                    "description": "Languages to detect and translate between"
                },
                "translate_images": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether to translate text in images"
                }
            }
        )
    
    def split_message(self, text: str, prefix: str = "[ai]") -> List[str]:
        """
        Split a long message into chunks that fit within WhatsApp's message limit.
        
        Args:
            text: The text to split
            prefix: The prefix to add to each chunk
            
        Returns:
            List of message chunks with pagination headers
        """
        # Calculate available space for content after prefix and pagination header
        header_overhead = len(prefix) + len(" 999/999 ")
        max_content_length = self.MAX_MESSAGE_LENGTH - header_overhead
        
        if len(text) <= max_content_length:
            return [f"{prefix} {text}"]
        
        # Split into chunks
        chunks = []
        remaining = text
        
        while remaining:
            if len(remaining) <= max_content_length:
                chunks.append(remaining)
                break
            
            # Try to split at sentence boundary
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
    
    async def process_message(self, message: Message) -> Optional[Response]:
        """
        Process an incoming message and return translation.
        
        Args:
            message: Incoming message to process
            
        Returns:
            Response with translation, or None to skip
        """
        prefix = self.config.get("prefix", "[ai]")
        translate_images = self.config.get("translate_images", True)
        source_languages = self.config.get("source_languages", ["en", "pt"])
        
        # Skip messages that start with the bot prefix (our own messages)
        if message.content and message.content.startswith(prefix):
            return None
        
        # Handle image messages
        if message.media_type == "image" and translate_images:
            logger.info(f"Processing image message: {message.id}")
            
            # Download and decrypt the image
            image_bytes = await self.services.whatsapp.download_and_decrypt_image(
                message.id,
                message.chat_jid
            )
            
            if not image_bytes:
                logger.error(f"Failed to download/decrypt image {message.id}")
                return None
            
            # Translate text from image
            translation_result = await self.services.llm.translate_image(image_bytes)
            
            if not translation_result:
                logger.error(f"Failed to process image {message.id}")
                return None
            
            # Check if no text was found in image
            if translation_result.get("no_text"):
                # If there's a caption, we'll process it separately
                if not message.content:
                    return Response(
                        content=f"{prefix}[image] No text found in image",
                        reply_to=message.id
                    )
                # Otherwise, fall through to process caption
            else:
                # Text was found - return translation
                translated_text = translation_result["translated_text"]
                source_lang = translation_result["source_language"]
                target_lang = translation_result["target_language"]
                
                logger.info(f"Image text translated: {source_lang} → {target_lang}")
                
                # Split message if needed
                message_chunks = self.split_message(translated_text, f"{prefix}[image]")
                
                # Return first chunk as response
                # Note: For multi-chunk messages, the message processor will need
                # to handle sending subsequent chunks
                return Response(
                    content=message_chunks[0],
                    reply_to=message.id
                )
        
        # Handle text messages (including image captions)
        if message.content:
            logger.info(f"Processing text message: {message.content[:50]}...")
            
            # Translate the message
            translation_result = await self.services.llm.translate(
                message.content,
                source_languages=source_languages
            )
            
            if not translation_result:
                logger.error(f"Failed to translate message {message.id}")
                return None
            
            translated_text = translation_result["translated_text"]
            source_lang = translation_result["source_language"]
            target_lang = translation_result["target_language"]
            
            logger.info(f"Translated: {source_lang} → {target_lang}")
            
            # Split message if needed
            message_chunks = self.split_message(translated_text, prefix)
            
            # Return first chunk as response
            return Response(
                content=message_chunks[0],
                reply_to=message.id
            )
        
        return None

