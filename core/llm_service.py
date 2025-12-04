"""LLM service for making AI calls."""

import base64
import io
import logging
import os
import random
import tempfile
import time
from typing import Optional, Dict, Any, List

import ffmpeg
from openai import OpenAI

logger = logging.getLogger(__name__)


class LLMService:
    """Service for interacting with LLM APIs."""
    
    def __init__(
        self, 
        api_key: str, 
        model: str = "gpt-5", 
        base_url: Optional[str] = None,
        vision_model: Optional[str] = None,
        audio_model: Optional[str] = None
    ):
        if base_url:
            self.client = OpenAI(api_key=api_key, base_url=base_url)
        else:
            self.client = OpenAI(api_key=api_key)
        self.model = model
        # Use separate models for vision and audio if specified, otherwise fall back to main model
        self.vision_model = vision_model or model
        # Whisper model is always "whisper-1" unless overridden
        self.audio_model = audio_model or "whisper-1"
        
        logger.info(f"LLMService initialized - Text: {self.model}, Vision: {self.vision_model}, Audio: {self.audio_model}")
    
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
                model=self.vision_model,
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
    
    def extract_audio_from_video(self, video_bytes: bytes) -> Optional[bytes]:
        """
        Extract audio track from video file using ffmpeg.
        
        Args:
            video_bytes: Raw bytes of the video file
        
        Returns:
            Audio file bytes (mp3 format), or None if extraction fails
        """
        temp_video_path = None
        temp_audio_path = None
        
        try:
            logger.info(f"Extracting audio from video: size={len(video_bytes)} bytes")
            
            # Create temporary files
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video:
                temp_video.write(video_bytes)
                temp_video_path = temp_video.name
            
            # Create temp file for output audio
            temp_audio_fd, temp_audio_path = tempfile.mkstemp(suffix='.mp3')
            os.close(temp_audio_fd)  # Close the file descriptor, ffmpeg will write to it
            
            logger.info(f"Temporary video file: {temp_video_path}")
            logger.info(f"Temporary audio file: {temp_audio_path}")
            
            # Extract audio using ffmpeg
            try:
                (
                    ffmpeg
                    .input(temp_video_path)
                    .output(temp_audio_path, acodec='libmp3lame', ac=1, ar='16000', audio_bitrate='64k')
                    .overwrite_output()
                    .run(capture_stdout=True, capture_stderr=True, quiet=True)
                )
                logger.info("Audio extraction successful")
            except ffmpeg.Error as e:
                error_message = e.stderr.decode() if e.stderr else str(e)
                
                # Check if video has no audio stream
                if 'does not contain any stream' in error_message or 'Output file is empty' in error_message:
                    logger.warning("Video does not contain an audio stream")
                    return None
                
                logger.error(f"FFmpeg error: {error_message}")
                return None
            
            # Read extracted audio file
            if not os.path.exists(temp_audio_path) or os.path.getsize(temp_audio_path) == 0:
                logger.warning("Audio extraction resulted in empty file - video may not have audio")
                return None
            
            with open(temp_audio_path, 'rb') as audio_file:
                audio_bytes = audio_file.read()
            
            logger.info(f"Extracted audio: {len(audio_bytes)} bytes")
            return audio_bytes
            
        except Exception as e:
            logger.error(f"Error extracting audio from video: {e}", exc_info=True)
            return None
        
        finally:
            # Clean up temporary files
            if temp_video_path and os.path.exists(temp_video_path):
                try:
                    os.unlink(temp_video_path)
                    logger.debug(f"Cleaned up temp video file: {temp_video_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete temp video file: {e}")
            
            if temp_audio_path and os.path.exists(temp_audio_path):
                try:
                    os.unlink(temp_audio_path)
                    logger.debug(f"Cleaned up temp audio file: {temp_audio_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete temp audio file: {e}")
    
    def transcribe_audio(self, audio_bytes: bytes, language: Optional[str] = None) -> Optional[str]:
        """
        Transcribe audio using OpenAI's Whisper API with retry logic.
        
        Args:
            audio_bytes: Raw bytes of the audio file
            language: Optional ISO-639-1 language code (e.g., 'en', 'pt')
                     If not provided, Whisper will auto-detect
        
        Returns:
            The transcribed text, or None if transcription fails
        """
        # Detect audio format by checking magic numbers (file signatures)
        audio_format = None
        
        # Check for common audio formats
        if audio_bytes.startswith(b'ID3') or audio_bytes.startswith(b'\xff\xfb') or audio_bytes.startswith(b'\xff\xf3'):
            audio_format = 'mp3'
        elif audio_bytes.startswith(b'OggS'):
            audio_format = 'ogg'
        elif audio_bytes.startswith(b'RIFF') and b'WAVE' in audio_bytes[:20]:
            audio_format = 'wav'
        elif audio_bytes.startswith(b'\x00\x00\x00') and b'ftyp' in audio_bytes[:20]:
            audio_format = 'm4a'
        elif audio_bytes.startswith(b'\x1aE\xdf\xa3'):
            audio_format = 'webm'
        else:
            # Default to ogg (common for WhatsApp voice messages)
            audio_format = 'ogg'
            logger.warning(f"Could not detect audio format, defaulting to ogg")
        
        logger.info(f"Detected audio format: {audio_format}, size: {len(audio_bytes)} bytes")
        
        # Check file size (Whisper has a 25MB limit) - this is a permanent error, don't retry
        if len(audio_bytes) > 25 * 1024 * 1024:
            logger.error(f"Audio file too large: {len(audio_bytes)} bytes (max 25MB)")
            return None
        
        # Retry logic with exponential backoff
        max_retries = 3
        retry_delays = [2, 4, 8]  # seconds
        
        for attempt in range(max_retries):
            try:
                # Create a file-like object from the audio bytes
                # Use unique filename to prevent any client-side caching issues
                timestamp = int(time.time() * 1000)  # milliseconds
                random_suffix = random.randint(1000, 9999)
                audio_file = io.BytesIO(audio_bytes)
                audio_file.name = f"audio_{timestamp}_{random_suffix}.{audio_format}"
                
                # Ensure buffer is at the start
                audio_file.seek(0)
                
                # Call Whisper API
                if attempt == 0:
                    logger.info(f"Calling Whisper API for transcription (language: {language or 'auto-detect'})")
                else:
                    logger.info(f"Retry attempt {attempt + 1}/{max_retries} for transcription")
                
                transcription_params = {
                    "model": self.audio_model,
                    "file": audio_file,
                }
                
                if language:
                    transcription_params["language"] = language
                
                response = self.client.audio.transcriptions.create(**transcription_params)
                
                transcribed_text = response.text
                
                if not transcribed_text:
                    logger.error("Whisper returned empty transcription")
                    return None
                
                logger.info(f"Transcription successful: {len(transcribed_text)} characters")
                return transcribed_text.strip()
            
            except Exception as e:
                error_msg = str(e).lower()
                
                # Check if this is a permanent error (don't retry)
                permanent_errors = ['invalid', 'unsupported', 'format', 'codec']
                is_permanent = any(err in error_msg for err in permanent_errors)
                
                if is_permanent:
                    logger.error(f"Audio transcription failed with permanent error: {e}")
                    return None
                
                # This is potentially a transient error (API issue, timeout, rate limit)
                if attempt < max_retries - 1:
                    delay = retry_delays[attempt]
                    logger.warning(f"Audio transcription error (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    # Final attempt failed
                    logger.error(f"Audio transcription failed after {max_retries} attempts: {e}")
                    return None
        
        return None

