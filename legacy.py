#!/usr/bin/env python3
# /// script
# dependencies = [
#   "openai",
#   "requests",
# ]
# ///

"""
WhatsApp Translation Bot

Monitors a WhatsApp group and automatically translates messages between English and Portuguese.
Uses an LLM to detect language and translate, replying to messages with [ai] prefix.
"""

import sqlite3
import time
import logging
import signal
import sys
import os
import base64
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List

import requests
from openai import OpenAI

# ============================================================================
# CONFIGURATION - Edit these values directly or use environment variables
# ============================================================================

# OpenAI Configuration
OPENAI_API_KEY = "sk-G7w8Dftca4usAscQKxkZNg"  # Your OpenAI API key (or set OPENAI_API_KEY env var)
OPENAI_BASE_URL = "https://litellm.madpin.dev"  # OpenAI API base URL (or set OPENAI_BASE_URL env var)
OPENAI_MODEL = "gpt-5"  # Model to use for translation

# WhatsApp API Configuration
WHATSAPP_BASE_URL = "https://gowa.madpin.dev"
WHATSAPP_API_USER = "madpin"  # Username for WhatsApp API (or set WHATSAPP_API_USER env var)
WHATSAPP_API_PASSWORD = "Senha?gowa123"  # Password for WhatsApp API (or set WHATSAPP_API_PASSWORD env var)

# WhatsApp Chat Configuration
DEVICE_ID = "353834210235:79@s.whatsapp.net"
CHAT_JID = "5511996141038-1472907582@g.us"  # Myself
CHAT_JID = "120363419538094902@g.us"  # Dublin Gang

# Bot Behavior
POLL_INTERVAL_SECONDS = 5  # How often to check for new messages
DB_PATH = Path(__file__).parent / "translations.db"  # Database location

# ============================================================================

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global flag for graceful shutdown
should_exit = False


def signal_handler(sig, frame):
    """Handle interrupt signals for graceful shutdown."""
    global should_exit
    logger.info("Received shutdown signal. Exiting gracefully...")
    should_exit = True


class TranslationDatabase:
    """Manages SQLite database for tracking processed messages."""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize the database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processed_messages (
                message_id TEXT PRIMARY KEY,
                original_text TEXT,
                translated_text TEXT,
                source_language TEXT,
                target_language TEXT,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")
    
    def is_processed(self, message_id: str) -> bool:
        """Check if a message has already been processed."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM processed_messages WHERE message_id = ?",
            (message_id,)
        )
        result = cursor.fetchone()
        conn.close()
        return result is not None
    
    def mark_processed(
        self,
        message_id: str,
        original_text: str,
        translated_text: str,
        source_language: str,
        target_language: str
    ):
        """Mark a message as processed."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO processed_messages 
            (message_id, original_text, translated_text, source_language, target_language)
            VALUES (?, ?, ?, ?, ?)
        """, (message_id, original_text, translated_text, source_language, target_language))
        conn.commit()
        conn.close()


class WhatsAppClient:
    """Client for interacting with the WhatsApp API."""
    
    def __init__(self, base_url: str, username: Optional[str] = None, password: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        if username and password:
            self.session.auth = (username, password)
    
    def get_messages(
        self,
        chat_jid: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Fetch recent messages from a chat."""
        url = f"{self.base_url}/chat/{chat_jid}/messages"
        params = {
            "limit": limit,
            "offset": 0
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Check for success response and extract messages from results.data
            if data.get("code") == "SUCCESS" and "results" in data and "data" in data["results"]:
                return data["results"]["data"]
            else:
                logger.error(f"Unexpected response format: {data}")
                return []
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching messages: {e}")
            return []
    
    def send_message(
        self,
        phone: str,
        message: str,
        reply_message_id: Optional[str] = None
    ) -> bool:
        """Send a message to a chat, optionally replying to another message."""
        url = f"{self.base_url}/send/message"
        payload = {
            "phone": phone,
            "message": message
        }
        
        if reply_message_id:
            payload["reply_message_id"] = reply_message_id
        
        try:
            logger.debug(f"Sending message: length={len(message)}, reply_to={reply_message_id}")
            response = self.session.post(url, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Check for success response (could be code: 200 or code: "SUCCESS")
            if data.get("code") in [200, "SUCCESS"]:
                logger.info(f"Message sent successfully")
                return True
            else:
                logger.error(f"Failed to send message: {data}")
                logger.error(f"Message length was: {len(message)} chars")
                return False
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending message: {e}")
            logger.error(f"Message length was: {len(message)} chars")
            if hasattr(e.response, 'text'):
                logger.error(f"Response text: {e.response.text}")
            return False
    
    def download_and_decrypt_image(self, message_id: str, chat_jid: str) -> Optional[bytes]:
        """
        Download and decrypt WhatsApp media using the API.
        
        WhatsApp media is E2E encrypted. This method:
        1. Calls /message/{id}/download to trigger server-side decryption
        2. Gets the decrypted file path
        3. Downloads the decrypted image
        """
        try:
            # Step 1: Trigger media download/decryption on server
            download_url = f"{self.base_url}/message/{message_id}/download"
            params = {"phone": chat_jid}
            
            logger.info(f"Requesting media decryption for message {message_id}")
            response = self.session.get(download_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if data.get("code") != "SUCCESS":
                logger.error(f"Media download failed: {data.get('message')}")
                return None
            
            # Step 2: Get the decrypted file path
            file_path = data.get("results", {}).get("file_path")
            if not file_path:
                logger.error(f"No file_path in response: {data}")
                return None
            
            logger.info(f"Media decrypted to: {file_path}")
            
            # Step 3: Download the decrypted image
            image_url = f"{self.base_url}/{file_path}"
            image_response = self.session.get(image_url, timeout=30)
            image_response.raise_for_status()
            
            content_length = len(image_response.content)
            logger.info(f"Downloaded decrypted image: Size={content_length} bytes")
            
            return image_response.content
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error downloading/decrypting image: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in download_and_decrypt_image: {e}")
            return None


class TranslationService:
    """Service for translating messages using LLM."""
    
    def __init__(self, api_key: str, model: str = "gpt-5", base_url: Optional[str] = None):
        if base_url:
            self.client = OpenAI(api_key=api_key, base_url=base_url)
        else:
            self.client = OpenAI(api_key=api_key)
        self.model = model
    
    def translate(self, text: str) -> Optional[Dict[str, str]]:
        """
        Detect language and translate between English and Portuguese.
        
        Returns a dict with 'translated_text', 'source_language', and 'target_language',
        or None if translation fails.
        """
        prompt = f"""You are a translation assistant. Your task is to:
1. Detect if the following message is in English or Portuguese
2. Translate it to the other language (English → Portuguese, Portuguese → English)
3. Return ONLY the translation, without any explanations or notes

Message to translate:
{text}

Respond with ONLY the translated text."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                # max_tokens=1024,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            translated_text = response.choices[0].message.content.strip()
            
            # Simple heuristic to determine source language
            # Check if original text contains Portuguese-specific characters/words
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
    
    def translate_image(self, image_bytes: bytes) -> Optional[Dict[str, str]]:
        """
        Extract text from image and translate between English and Portuguese.
        
        Args:
            image_bytes: Raw bytes of the image
        
        Returns a dict with 'translated_text', 'source_language', and 'target_language',
        or a special dict with 'no_text': True if no text is found,
        or None if the operation fails.
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
        logger.info(f"First 20 bytes (hex): {image_bytes[:20].hex()}")
        
        # Map image type to MIME type
        mime_type_map = {
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp'
        }
        
        if not image_type or image_type not in mime_type_map:
            logger.error(f"Unsupported or undetectable image type: {image_type}")
            logger.error(f"First 50 bytes (hex): {image_bytes[:50].hex()}")
            logger.error("NOTE: The media appears to be encrypted. WhatsApp uses end-to-end encryption for media files.")
            logger.error("The go-whatsapp-web-multidevice API may not support media decryption.")
            logger.error("You may need to enable media storage or use a different API endpoint for decrypted media.")
            return {"no_text": True, "error": "encrypted_media"}
        
        mime_type = mime_type_map[image_type]
        
        # Convert image bytes to base64
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        data_url = f"data:{mime_type};base64,{base64_image}"
        
        logger.info(f"Created data URL with MIME type: {mime_type}, base64 length: {len(base64_image)}")
        
        # Warn if image is very large (> 5MB base64 ≈ 3.75MB actual)
        if len(base64_image) > 5_000_000:
            logger.warning(f"Image is very large ({len(base64_image)} chars base64). This may cause LLM failures.")
            logger.warning("Consider compressing images before sending, or the LLM may return empty responses.")
        
        prompt = """You are a translation assistant. Your task is to:
1. Look at the image and identify any text in it
2. If there is NO text in the image, respond with exactly: "NO_TEXT_FOUND"
3. If there IS text, detect if it's in English or Portuguese
4. Translate the text to the other language (English → Portuguese, Portuguese → English)
5. Return ONLY the translated text, without any explanations or notes

Respond with either "NO_TEXT_FOUND" or the translated text only."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                # max_tokens=4096,  # Increased for images with lots of text
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
            
            # Log response metadata
            logger.info(f"LLM finish_reason: {response.choices[0].finish_reason}")
            if hasattr(response, 'usage'):
                logger.info(f"LLM usage: {response.usage}")
            
            if result is None:
                logger.error("LLM returned None content")
                logger.error(f"Full response: {response}")
                return {"no_text": True, "error": "empty_response"}
            
            result = result.strip()
            
            # Log LLM response for debugging
            logger.info(f"LLM image translation response length: {len(result)} chars")
            if result:
                logger.info(f"LLM response preview: {result[:200]}...")
            else:
                logger.info(f"LLM response preview: (empty)")
            
            # Check if response is empty
            if not result:
                logger.warning("LLM returned empty response - image may be too large or complex")
                logger.warning("Try sending a smaller image or image with less text")
                return {"no_text": True, "error": "empty_response"}
            
            # Check if no text was found
            if result == "NO_TEXT_FOUND":
                return {"no_text": True}
            
            # If we got translated text, determine languages using heuristic
            # We need to ask the LLM to extract the original text to detect language
            # For simplicity, let's make another call to get the original text
            extract_prompt = """Look at this image and extract ALL text you see in it.
Return ONLY the extracted text exactly as it appears, without translation or explanations."""
            
            extract_response = self.client.chat.completions.create(
                model=self.model,
                # max_tokens=4096,  # Increased for images with lots of text
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
            if original_text is None:
                logger.error("LLM returned None content for extraction")
                original_text = result  # Use the translation as fallback
            else:
                original_text = original_text.strip()
            
            # Log extracted text for debugging
            logger.info(f"LLM extracted text length: {len(original_text)} chars")
            logger.info(f"Extracted text preview: {original_text[:200]}...")
            
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


class TranslationBot:
    """Main bot that coordinates all components."""
    
    MAX_MESSAGE_LENGTH = 4095  # WhatsApp message length limit
    
    def __init__(
        self,
        whatsapp_client: WhatsAppClient,
        translation_service: TranslationService,
        database: TranslationDatabase,
        chat_jid: str
    ):
        self.whatsapp = whatsapp_client
        self.translator = translation_service
        self.db = database
        self.chat_jid = chat_jid
        self.is_first_run = True  # Flag to handle initial startup
    
    def split_message(self, text: str, prefix: str = "[ai]") -> List[str]:
        """
        Split a long message into chunks that fit within WhatsApp's message limit.
        
        Args:
            text: The text to split
            prefix: The prefix to add to each chunk (e.g., "[ai]" or "[ai][image]")
        
        Returns:
            List of message chunks with pagination headers
        """
        # Calculate available space for content after prefix and pagination header
        # Format: "[ai] 1/3 " or "[ai][image] 10/10 "
        # Reserve space for worst case: "[prefix] 999/999 "
        header_overhead = len(prefix) + len(" 999/999 ")
        max_content_length = self.MAX_MESSAGE_LENGTH - header_overhead
        
        if len(text) <= max_content_length:
            # No splitting needed
            return [f"{prefix} {text}"]
        
        # Split into chunks
        chunks = []
        remaining = text
        
        while remaining:
            if len(remaining) <= max_content_length:
                chunks.append(remaining)
                break
            
            # Try to split at sentence boundary (. ! ?)
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
    
    def should_process_message(self, message: Dict[str, Any]) -> bool:
        """Determine if a message should be processed for translation."""
        # Get message ID first
        message_id = message.get("id")
        if not message_id:
            return False
        
        # Skip if already processed
        if self.db.is_processed(message_id):
            return False
        
        # Check if it's an image message
        media_type = message.get("media_type")
        if media_type == "image":
            # Process images that have a URL
            return bool(message.get("url"))
        
        # For text messages, check content
        msg_text = message.get("content", "")
        if not msg_text:
            return False
        
        # Skip messages that start with [ai] (bot's own translations)
        if msg_text.startswith("[ai]"):
            return False
        
        return True
    
    def process_message(self, message: Dict[str, Any]):
        """Process a single message: translate and reply."""
        message_id = message.get("id")
        media_type = message.get("media_type")
        msg_text = message.get("content", "")
        
        # Check if message has both image and text (caption)
        has_image = media_type == "image"
        has_text = bool(msg_text and not msg_text.startswith("[ai]"))
        
        # Handle image messages
        if has_image:
            logger.info(f"Processing image message: {message_id}")
            
            # Download and decrypt the image
            image_bytes = self.whatsapp.download_and_decrypt_image(message_id, self.chat_jid)
            if not image_bytes:
                logger.error(f"Failed to download/decrypt image {message_id}")
                return
            
            # Translate text from image
            translation_result = self.translator.translate_image(image_bytes)
            
            if not translation_result:
                logger.error(f"Failed to process image {message_id}")
                return
            
            # Check if no text was found in image
            if translation_result.get("no_text"):
                if not has_text:
                    # No text in image and no caption - inform user
                    message_chunks = self.split_message("No text found in image", "[ai][image]")
                    
                    for chunk in message_chunks:
                        success = self.whatsapp.send_message(
                            phone=self.chat_jid,
                            message=chunk,
                            reply_message_id=message_id
                        )
                        if not success:
                            logger.error(f"Failed to send reply for image {message_id}")
                            break
                        time.sleep(0.5)  # Small delay between chunks
                    
                    if success:
                        self.db.mark_processed(
                            message_id=message_id,
                            original_text="[image - no text]",
                            translated_text="No text found",
                            source_language="none",
                            target_language="none"
                        )
                        logger.info("Image processed - no text found")
                # If has_text, we'll process caption below, so don't return yet
            else:
                # Text was found in image - send translation (possibly in multiple chunks)
                translated_text = translation_result["translated_text"]
                source_lang = translation_result["source_language"]
                target_lang = translation_result["target_language"]
                
                message_chunks = self.split_message(translated_text, "[ai][image]")
                logger.info(f"Sending image translation in {len(message_chunks)} chunk(s)")
                logger.info(f"Total translation length: {len(translated_text)} chars")
                
                success = True
                for i, chunk in enumerate(message_chunks, 1):
                    logger.info(f"Sending chunk {i}/{len(message_chunks)}: {len(chunk)} chars - Preview: {chunk[:100]}...")
                    success = self.whatsapp.send_message(
                        phone=self.chat_jid,
                        message=chunk,
                        reply_message_id=message_id
                    )
                    if not success:
                        logger.error(f"Failed to send image translation chunk {i} for {message_id}")
                        break
                    logger.info(f"Chunk {i}/{len(message_chunks)} sent successfully")
                    time.sleep(0.5)  # Small delay between chunks
                
                if success:
                    logger.info(f"Image text translated: {source_lang} → {target_lang}")
                else:
                    logger.error(f"Failed to send image translation for {message_id}")
            
            # If there's also caption text, process it separately
            if has_text:
                logger.info(f"Processing caption text for image message: {message_id}")
                time.sleep(1)  # Small delay between image and caption
                
                caption_translation = self.translator.translate(msg_text)
                if caption_translation:
                    caption_translated_text = caption_translation["translated_text"]
                    caption_source_lang = caption_translation["source_language"]
                    caption_target_lang = caption_translation["target_language"]
                    
                    caption_chunks = self.split_message(caption_translated_text, "[ai]")
                    logger.info(f"Sending caption translation in {len(caption_chunks)} chunk(s)")
                    logger.info(f"Total caption length: {len(caption_translated_text)} chars")
                    
                    success = True
                    for i, chunk in enumerate(caption_chunks, 1):
                        logger.info(f"Sending caption chunk {i}/{len(caption_chunks)}: {len(chunk)} chars")
                        success = self.whatsapp.send_message(
                            phone=self.chat_jid,
                            message=chunk,
                            reply_message_id=message_id
                        )
                        if not success:
                            logger.error(f"Failed to send caption translation chunk {i} for {message_id}")
                            break
                        logger.info(f"Caption chunk {i}/{len(caption_chunks)} sent successfully")
                        time.sleep(0.5)  # Small delay between chunks
                    
                    if success:
                        logger.info(f"Caption translated: {caption_source_lang} → {caption_target_lang}")
                    else:
                        logger.error(f"Failed to send caption translation for {message_id}")
            
            # Mark as fully processed
            if not self.db.is_processed(message_id):
                self.db.mark_processed(
                    message_id=message_id,
                    original_text=f"[image: {message_id}] + caption: {msg_text[:50] if has_text else 'none'}",
                    translated_text="image + caption processed",
                    source_language="mixed",
                    target_language="mixed"
                )
            
            return
        
        # Handle text messages (original logic)
        msg_text = message.get("content", "")
        
        logger.info(f"Processing message: {msg_text[:50]}...")
        
        # Translate the message
        translation_result = self.translator.translate(msg_text)
        
        if not translation_result:
            logger.error(f"Failed to translate message {message_id}")
            return
        
        translated_text = translation_result["translated_text"]
        source_lang = translation_result["source_language"]
        target_lang = translation_result["target_language"]
        
        # Split message if needed and send chunks
        message_chunks = self.split_message(translated_text, "[ai]")
        logger.info(f"Sending translation in {len(message_chunks)} chunk(s)")
        logger.info(f"Total translation length: {len(translated_text)} chars")
        
        success = True
        for i, chunk in enumerate(message_chunks, 1):
            logger.info(f"Sending chunk {i}/{len(message_chunks)}: {len(chunk)} chars")
            success = self.whatsapp.send_message(
                phone=self.chat_jid,
                message=chunk,
                reply_message_id=message_id
            )
            if not success:
                logger.error(f"Failed to send translation chunk {i} for message {message_id}")
                break
            logger.info(f"Chunk {i}/{len(message_chunks)} sent successfully")
            time.sleep(0.5)  # Small delay between chunks
        
        if success:
            # Mark as processed
            self.db.mark_processed(
                message_id=message_id,
                original_text=msg_text,
                translated_text=translated_text,
                source_language=source_lang,
                target_language=target_lang
            )
            logger.info(f"Translated and replied: {source_lang} → {target_lang}")
        else:
            logger.error(f"Failed to send reply for message {message_id}")
    
    def run(self, poll_interval: int = 5):
        """Main loop: poll for messages and process them."""
        logger.info(f"Starting translation bot for chat {self.chat_jid}")
        logger.info(f"Polling every {poll_interval} seconds. Press Ctrl+C to stop.")
        
        while not should_exit:
            try:
                # Fetch recent messages
                messages = self.whatsapp.get_messages(self.chat_jid, limit=20)
                
                if not messages:
                    logger.debug("No messages fetched")
                else:
                    # On first run, just mark existing messages as seen without translating
                    if self.is_first_run:
                        logger.info(f"First run: marking {len(messages)} existing messages as seen (won't translate history)")
                        for message in messages:
                            message_id = message.get("id")
                            msg_text = message.get("content", "")
                            if message_id and msg_text and not self.db.is_processed(message_id):
                                # Mark as processed without translating
                                self.db.mark_processed(
                                    message_id=message_id,
                                    original_text=msg_text,
                                    translated_text="[skipped - startup]",
                                    source_language="unknown",
                                    target_language="unknown"
                                )
                        self.is_first_run = False
                        logger.info("Initialization complete. Now monitoring for new messages...")
                    else:
                        # Process messages in chronological order (oldest first)
                        # The API likely returns newest first, so reverse
                        messages.reverse()
                        
                        for message in messages:
                            if should_exit:
                                break
                            
                            if self.should_process_message(message):
                                self.process_message(message)
                                # Small delay between processing messages
                                time.sleep(1)
                
                # Wait before next poll
                time.sleep(poll_interval)
            
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                time.sleep(poll_interval)
        
        logger.info("Bot stopped")


def main():
    """Main entry point."""
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Get API key from environment variable or config
    api_key = os.environ.get("OPENAI_API_KEY", OPENAI_API_KEY)
    if not api_key:
        logger.error("OpenAI API key not set. Please set OPENAI_API_KEY in the script or as environment variable")
        sys.exit(1)
    
    # Get WhatsApp API credentials from environment variables or config (optional)
    whatsapp_user = os.environ.get("WHATSAPP_API_USER", WHATSAPP_API_USER) or None
    whatsapp_password = os.environ.get("WHATSAPP_API_PASSWORD", WHATSAPP_API_PASSWORD) or None
    
    # Get OpenAI configuration from environment or config
    base_url = os.environ.get("OPENAI_BASE_URL", OPENAI_BASE_URL) or None
    model = os.environ.get("OPENAI_MODEL", OPENAI_MODEL)
    
    # Initialize components
    database = TranslationDatabase(DB_PATH)
    whatsapp_client = WhatsAppClient(
        WHATSAPP_BASE_URL,
        username=whatsapp_user,
        password=whatsapp_password
    )
    translation_service = TranslationService(api_key, model=model, base_url=base_url)
    
    # Create and run bot
    bot = TranslationBot(
        whatsapp_client=whatsapp_client,
        translation_service=translation_service,
        database=database,
        chat_jid=CHAT_JID
    )
    
    bot.run(poll_interval=POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()

