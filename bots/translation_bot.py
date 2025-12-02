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
        Supports text, image (with text extraction), audio, and video messages.
        
        Args:
            message: The message dict from WhatsApp API
            history: Optional list of previous messages for context
        
        Returns:
            The translated text, or None if translation fails
        """
        message_id = message.get("id")
        
        # Try multiple ways to detect media type (different WhatsApp APIs use different field names)
        media_type = None
        
        # Method 1: Direct media_type field
        if "media_type" in message:
            media_type = message["media_type"]
        
        # Method 2: type field
        elif "type" in message and message["type"] not in ["text", "chat", None]:
            media_type = message["type"]
        
        # Method 3: Check for nested message types (common in WhatsApp Web API)
        elif "message" in message and isinstance(message["message"], dict):
            msg_obj = message["message"]
            if "imageMessage" in msg_obj:
                media_type = "image"
            elif "audioMessage" in msg_obj or "pttMessage" in msg_obj:
                media_type = "audio"
            elif "videoMessage" in msg_obj:
                media_type = "video"
        
        # Method 4: Check mimetype
        elif "mimetype" in message:
            mime = message["mimetype"]
            if mime.startswith("image/"):
                media_type = "image"
            elif mime.startswith("audio/"):
                media_type = "audio"
            elif mime.startswith("video/"):
                media_type = "video"
        
        logger.info(f"[{self.NAME}] Detected media_type='{media_type}' for message {message_id}")
        
        # Handle IMAGE messages
        if media_type and "image" in str(media_type).lower():
            logger.info(f"[{self.NAME}] Processing image message {message_id}")
            return self._process_image_message(message)
        
        # Handle AUDIO/VOICE messages
        if media_type and any(x in str(media_type).lower() for x in ["audio", "voice", "ptt"]):
            logger.info(f"[{self.NAME}] Processing audio message {message_id}")
            return self._process_audio_message(message)
        
        # Handle VIDEO messages
        if media_type and "video" in str(media_type).lower():
            logger.info(f"[{self.NAME}] Processing video message {message_id}")
            return self._process_video_message(message)
        
        # Handle TEXT messages
        msg_text = message.get("content", "")
        if not msg_text:
            return None
        
        logger.info(f"[{self.NAME}] Processing text message {message_id}")
        return self._process_text_message(msg_text, history)
    
    def _process_image_message(self, message: Dict[str, Any]) -> Optional[str]:
        """
        Process an image message by extracting and translating any text in it.
        
        Args:
            message: The message dict from WhatsApp API
        
        Returns:
            Extracted and translated text, or error message
        """
        message_id = message.get("id")
        chat_jid = self.chat_jid
        
        try:
            # Download the image
            logger.info(f"[{self.NAME}] Downloading image from message {message_id}")
            image_bytes = self.whatsapp.download_and_decrypt_image(message_id, chat_jid)
            
            if not image_bytes:
                logger.error(f"[{self.NAME}] Failed to download image")
                return "❌ Sorry, I couldn't download the image."
            
            # Use vision AI to extract and translate text
            prompt = """You are a multilingual image analysis assistant. Your task is to:

1. Carefully examine the image for ANY text, writing, signs, labels, or written content
2. If you find text:
   - Extract all the text you can see
   - Detect if the text is in English or Portuguese
   - Translate it to the other language (English → Portuguese, Portuguese → English)
   - Present it clearly in this format:
     📝 Original Text: [the text you found]
     🌍 Translation: [the translated text]
3. If there's NO text in the image:
   - Provide a brief description of what you see in the image
   - Format: 📷 Image contains: [brief description]

Be thorough and extract ALL visible text, even if it's small or partially visible."""

            logger.info(f"[{self.NAME}] Calling vision AI for image analysis")
            result = self.llm.call_with_image(prompt, image_bytes)
            
            if not result:
                logger.error(f"[{self.NAME}] Vision AI call failed")
                return "❌ Sorry, I couldn't analyze the image. Please try again."
            
            logger.info(f"[{self.NAME}] Image analysis successful")
            return result
            
        except Exception as e:
            logger.error(f"[{self.NAME}] Error processing image: {e}", exc_info=True)
            return "❌ An error occurred while processing the image."
    
    def _process_audio_message(self, message: Dict[str, Any]) -> Optional[str]:
        """
        Process an audio/voice message by transcribing and translating it.
        
        Args:
            message: The message dict from WhatsApp API
        
        Returns:
            Transcription and translation, or error message
        """
        message_id = message.get("id")
        chat_jid = self.chat_jid
        
        try:
            # Download the audio
            logger.info(f"[{self.NAME}] Downloading audio from message {message_id}")
            audio_bytes = self.whatsapp.download_and_decrypt_audio(message_id, chat_jid)
            
            if not audio_bytes:
                logger.error(f"[{self.NAME}] Failed to download audio")
                return "❌ Sorry, I couldn't download the audio message."
            
            # Transcribe the audio using Whisper
            logger.info(f"[{self.NAME}] Transcribing audio with Whisper API")
            transcription = self.llm.transcribe_audio(audio_bytes)
            
            if not transcription:
                logger.error(f"[{self.NAME}] Audio transcription failed")
                return "❌ Sorry, I couldn't transcribe the audio. The audio might be unclear or in an unsupported format."
            
            logger.info(f"[{self.NAME}] Transcription successful: {transcription[:50]}...")
            
            # Translate the transcription
            logger.info(f"[{self.NAME}] Translating transcription")
            translation = self._translate_text(transcription)
            
            if not translation:
                # If translation fails, at least return the transcription
                return f"🎤 Transcription:\n{transcription}\n\n(Translation failed)"
            
            # Format the response with both transcription and translation
            response = f"🎤 Transcription:\n{transcription}\n\n🌍 Translation:\n{translation}"
            
            logger.info(f"[{self.NAME}] Audio processing complete")
            return response
            
        except Exception as e:
            logger.error(f"[{self.NAME}] Error processing audio: {e}", exc_info=True)
            return "❌ An error occurred while processing the audio message."
    
    def _process_video_message(self, message: Dict[str, Any]) -> Optional[str]:
        """
        Process a video message by extracting and transcribing its audio track.
        
        Args:
            message: The message dict from WhatsApp API
        
        Returns:
            Audio transcription and translation, or error message
        """
        message_id = message.get("id")
        chat_jid = self.chat_jid
        
        try:
            # Download the video
            logger.info(f"[{self.NAME}] Downloading video from message {message_id}")
            video_bytes = self.whatsapp.download_and_decrypt_video(message_id, chat_jid)
            
            if not video_bytes:
                logger.error(f"[{self.NAME}] Failed to download video")
                return "❌ Sorry, I couldn't download the video."
            
            # Check video size (reasonable limit for processing)
            video_size_mb = len(video_bytes) / (1024 * 1024)
            logger.info(f"[{self.NAME}] Video size: {video_size_mb:.2f} MB")
            
            if video_size_mb > 100:
                logger.warning(f"[{self.NAME}] Video is very large: {video_size_mb:.2f} MB")
                return f"❌ Video is too large ({video_size_mb:.1f} MB). Please send videos under 100 MB."
            
            # Extract audio from video
            logger.info(f"[{self.NAME}] Extracting audio from video")
            audio_bytes = self.llm.extract_audio_from_video(video_bytes)
            
            if not audio_bytes:
                logger.warning(f"[{self.NAME}] Video has no audio track or extraction failed")
                return "❌ This video doesn't have an audio track, or I couldn't extract it. Please make sure the video has sound."
            
            # Check extracted audio size (Whisper has 25MB limit)
            audio_size_mb = len(audio_bytes) / (1024 * 1024)
            logger.info(f"[{self.NAME}] Extracted audio size: {audio_size_mb:.2f} MB")
            
            if audio_size_mb > 25:
                logger.error(f"[{self.NAME}] Extracted audio exceeds Whisper's 25MB limit")
                return f"❌ The video's audio is too long ({audio_size_mb:.1f} MB). Whisper API supports up to 25 MB. Please send a shorter video."
            
            # Transcribe the audio using Whisper
            logger.info(f"[{self.NAME}] Transcribing video audio with Whisper API")
            transcription = self.llm.transcribe_audio(audio_bytes)
            
            if not transcription:
                logger.error(f"[{self.NAME}] Video audio transcription failed")
                return "❌ Sorry, I couldn't transcribe the video's audio. The audio might be unclear or in an unsupported format."
            
            logger.info(f"[{self.NAME}] Transcription successful: {transcription[:50]}...")
            
            # Translate the transcription
            logger.info(f"[{self.NAME}] Translating transcription")
            translation = self._translate_text(transcription)
            
            if not translation:
                # If translation fails, at least return the transcription
                return f"🎬 Video Audio Transcription:\n{transcription}\n\n(Translation failed)"
            
            # Format the response with both transcription and translation
            response = f"🎬 Video Audio Transcription:\n{transcription}\n\n🌍 Translation:\n{translation}"
            
            logger.info(f"[{self.NAME}] Video audio processing complete")
            return response
            
        except Exception as e:
            logger.error(f"[{self.NAME}] Error processing video: {e}", exc_info=True)
            return "❌ An error occurred while processing the video."
    
    def _process_text_message(self, msg_text: str, history: Optional[List[Dict[str, Any]]] = None) -> Optional[str]:
        """
        Process a text message by translating it.
        
        Args:
            msg_text: The message text
            history: Optional conversation history
        
        Returns:
            Translated text, or None if translation fails
        """
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
            translated_text = self._translate_text(msg_text)
        
        if not translated_text:
            logger.error(f"[{self.NAME}] Failed to translate message")
            return None
        
        logger.info(f"[{self.NAME}] Translated: {msg_text[:30]}... -> {translated_text[:30]}...")
        return translated_text
    
    def _translate_text(self, text: str) -> Optional[str]:
        """
        Translate text between English and Portuguese.
        
        Args:
            text: The text to translate
        
        Returns:
            Translated text, or None if translation fails
        """
        prompt = f"""You are a translation assistant. Your task is to:
1. Detect if the following text is in English or Portuguese
2. Translate it to the other language (English → Portuguese, Portuguese → English)
3. Return ONLY the translation, without any explanations or notes

Text to translate:
{text}

Respond with ONLY the translated text."""
        
        return self.llm.call(prompt)

