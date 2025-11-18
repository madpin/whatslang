"""LLM service for making AI calls."""

import base64
import logging
from typing import Optional, Dict, Any, List

from openai import OpenAI

logger = logging.getLogger(__name__)


class LLMService:
    """Service for interacting with LLM APIs."""
    
    def __init__(self, api_key: str, model: str = "gpt-5", base_url: Optional[str] = None):
        if base_url:
            self.client = OpenAI(api_key=api_key, base_url=base_url)
        else:
            self.client = OpenAI(api_key=api_key)
        self.model = model
    
    def call(self, prompt: str, text: str = "") -> Optional[str]:
        """
        Make a simple LLM call with a prompt and optional text.
        
        Args:
            prompt: The system/instruction prompt
            text: Optional user text to include
        
        Returns:
            The LLM response text, or None if the call fails
        """
        try:
            full_prompt = f"{prompt}\n\n{text}" if text else prompt
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": full_prompt}
                ]
            )
            
            result = response.choices[0].message.content
            return result.strip() if result else None
        
        except Exception as e:
            logger.error(f"LLM call error: {e}")
            return None
    
    def call_with_history(
        self,
        system_prompt: str,
        current_message: str,
        history: List[Dict[str, Any]]
    ) -> Optional[str]:
        """
        Make an LLM call with conversation history context.
        
        Args:
            system_prompt: The system/instruction prompt
            current_message: The current message to process
            history: List of previous messages with format:
                     [{"sender": str, "content": str, "is_from_me": bool, "is_bot": bool}, ...]
        
        Returns:
            The LLM response text, or None if the call fails
        """
        try:
            # Build messages array for OpenAI API
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add history messages
            for msg in history:
                content = msg.get("content", "")
                if not content:
                    continue
                
                # Determine role based on message type
                # Bot messages and owner messages are "assistant"
                # Other user messages are "user"
                is_bot = msg.get("is_bot", False)
                is_from_me = msg.get("is_from_me", False)
                
                if is_bot or is_from_me:
                    role = "assistant"
                else:
                    role = "user"
                
                sender = msg.get("sender", "Unknown")
                # Format with sender info for context
                formatted_content = f"[{sender}]: {content}"
                
                messages.append({
                    "role": role,
                    "content": formatted_content
                })
            
            # Add current message as user message
            messages.append({
                "role": "user",
                "content": current_message
            })
            
            logger.debug(f"Calling LLM with {len(history)} history messages")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            
            result = response.choices[0].message.content
            return result.strip() if result else None
        
        except Exception as e:
            logger.error(f"LLM call with history error: {e}")
            return None
    
    def call_with_image(self, prompt: str, image_bytes: bytes) -> Optional[str]:
        """
        Make an LLM call with an image.
        
        Args:
            prompt: The instruction prompt
            image_bytes: Raw bytes of the image
        
        Returns:
            The LLM response text, or None if the call fails
        """
        # Detect image type by checking magic numbers (file signatures)
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
            logger.error(f"Unsupported or undetectable image type: {image_type}")
            return None
        
        mime_type = mime_type_map[image_type]
        
        # Convert image bytes to base64
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        data_url = f"data:{mime_type};base64,{base64_image}"
        
        logger.info(f"Created data URL with MIME type: {mime_type}")
        
        # Warn if image is very large
        if len(base64_image) > 5_000_000:
            logger.warning(f"Image is very large ({len(base64_image)} chars base64). This may cause LLM failures.")
        
        try:
            response = self.client.chat.completions.create(
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
            
            if result is None:
                logger.error("LLM returned None content")
                return None
            
            return result.strip()
        
        except Exception as e:
            logger.error(f"Image LLM call error: {e}")
            return None

