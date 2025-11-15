"""LLM service wrapper"""

import logging
from typing import Optional, Dict, Any
import base64

from openai import OpenAI, AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Service for LLM interactions"""
    
    def __init__(self):
        """Initialize LLM client"""
        if settings.openai_base_url:
            self.client = AsyncOpenAI(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url
            )
        else:
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        
        self.model = settings.openai_model
    
    async def translate(
        self,
        text: str,
        source_languages: list[str] = ["en", "pt"]
    ) -> Optional[Dict[str, str]]:
        """
        Detect language and translate between specified languages.
        
        Args:
            text: Text to translate
            source_languages: List of languages to detect/translate between
            
        Returns:
            Dict with 'translated_text', 'source_language', 'target_language'
            or None if translation fails
        """
        lang_str = " or ".join(source_languages)
        prompt = f"""You are a translation assistant. Your task is to:
1. Detect if the following message is in {lang_str}
2. Translate it to the other language
3. Return ONLY the translation, without any explanations or notes

Message to translate:
{text}

Respond with ONLY the translated text."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            translated_text = response.choices[0].message.content
            if not translated_text:
                return None
            
            translated_text = translated_text.strip()
            
            # Simple heuristic to determine source language
            portuguese_indicators = ['ã', 'õ', 'ç', 'á', 'é', 'í', 'ó', 'ú', 'â', 'ê', 'ô']
            is_portuguese = any(char in text.lower() for char in portuguese_indicators)
            
            source_lang = "Portuguese" if is_portuguese else "English"
            target_lang = "English" if is_portuguese else "Portuguese"
            
            return {
                "translated_text": translated_text,
                "source_language": source_lang,
                "target_language": target_lang
            }
        
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return None
    
    async def translate_image(
        self,
        image_bytes: bytes
    ) -> Optional[Dict[str, Any]]:
        """
        Extract text from image and translate.
        
        Args:
            image_bytes: Raw bytes of the image
            
        Returns:
            Dict with 'translated_text', 'source_language', 'target_language',
            or dict with 'no_text': True if no text found,
            or None if operation fails
        """
        # Detect image type by checking magic numbers
        image_type = None
        
        if image_bytes.startswith(b'\xff\xd8\xff'):
            image_type = 'jpeg'
        elif image_bytes.startswith(b'\x89PNG\r\n\x1a\n'):
            image_type = 'png'
        elif image_bytes.startswith(b'GIF87a') or image_bytes.startswith(b'GIF89a'):
            image_type = 'gif'
        elif image_bytes.startswith(b'RIFF') and b'WEBP' in image_bytes[:20]:
            image_type = 'webp'
        
        logger.info(f"Detected image type: {image_type}, size: {len(image_bytes)} bytes")
        
        # Map image type to MIME type
        mime_type_map = {
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp'
        }
        
        if not image_type or image_type not in mime_type_map:
            logger.error(f"Unsupported image type: {image_type}")
            return {"no_text": True, "error": "unsupported_format"}
        
        mime_type = mime_type_map[image_type]
        
        # Convert to base64
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        data_url = f"data:{mime_type};base64,{base64_image}"
        
        logger.info(f"Created data URL, base64 length: {len(base64_image)}")
        
        # Warn if image is very large
        if len(base64_image) > 5_000_000:
            logger.warning(f"Image is very large ({len(base64_image)} chars base64)")
        
        prompt = """You are a translation assistant. Your task is to:
1. Look at the image and identify any text in it
2. If there is NO text in the image, respond with exactly: "NO_TEXT_FOUND"
3. If there IS text, detect if it's in English or Portuguese
4. Translate the text to the other language (English → Portuguese, Portuguese → English)
5. Return ONLY the translated text, without any explanations or notes

Respond with either "NO_TEXT_FOUND" or the translated text only."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": data_url}}
                        ]
                    }
                ]
            )
            
            result = response.choices[0].message.content
            
            if not result:
                logger.warning("LLM returned empty response")
                return {"no_text": True, "error": "empty_response"}
            
            result = result.strip()
            
            logger.info(f"LLM response length: {len(result)} chars")
            
            # Check if no text was found
            if result == "NO_TEXT_FOUND":
                return {"no_text": True}
            
            # Extract original text for language detection
            extract_prompt = """Look at this image and extract ALL text you see in it.
Return ONLY the extracted text exactly as it appears, without translation or explanations."""
            
            extract_response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": extract_prompt},
                            {"type": "image_url", "image_url": {"url": data_url}}
                        ]
                    }
                ]
            )
            
            original_text = extract_response.choices[0].message.content
            if not original_text:
                original_text = result
            else:
                original_text = original_text.strip()
            
            logger.info(f"Extracted text length: {len(original_text)} chars")
            
            # Determine source language
            portuguese_indicators = ['ã', 'õ', 'ç', 'á', 'é', 'í', 'ó', 'ú', 'â', 'ê', 'ô']
            is_portuguese = any(char in original_text.lower() for char in portuguese_indicators)
            
            source_lang = "Portuguese" if is_portuguese else "English"
            target_lang = "English" if is_portuguese else "Portuguese"
            
            return {
                "translated_text": result,
                "source_language": source_lang,
                "target_language": target_lang
            }
        
        except Exception as e:
            logger.error(f"Image translation error: {e}")
            return None
    
    async def chat_completion(
        self,
        messages: list[Dict[str, str]],
        **kwargs
    ) -> Optional[str]:
        """
        Generic chat completion method.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional parameters for the API call
            
        Returns:
            Response text or None if failed
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                **kwargs
            )
            
            content = response.choices[0].message.content
            return content.strip() if content else None
        
        except Exception as e:
            logger.error(f"Chat completion error: {e}")
            return None

