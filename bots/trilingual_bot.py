"""Translation bot: English → Portuguese + Greek; any other language → English."""

import logging
from typing import Any, Dict, List, Optional

from core.bot_base import BotBase

logger = logging.getLogger(__name__)

# Shared rules for text translation (used in prompts)
_TRANSLATION_RULES = """Rules:
1. Detect the primary language of the text.
2. If the text is in English: provide BOTH a Brazilian Portuguese and a Greek translation, using exactly this format (two lines):
   🇧🇷 Portuguese: [translation]
   🇬🇷 Greek: [translation]
3. If the text is in any language other than English (including Portuguese, Greek, or mixed non-English): translate ONLY into English. Return ONLY the English text, with no labels, flags, or extra lines.
4. If the input mixes languages, use the dominant language to decide."""

_TRANSLATION_RULES_IMAGE = """   - If the text is in English: translate to BOTH Brazilian Portuguese and Greek (two lines: 🇧🇷 Portuguese: …, 🇬🇷 Greek: …).
   - If the text is in any other language: translate ONLY to English (single block labeled 🌍 English: …)."""


class TrilingualEnPtElBot(BotBase):
    """English → Portuguese + Greek; non-English → English. Same media support as TranslationBot."""

    NAME = "trilingual_en_pt_el"
    PREFIX = "[tri]"
    DESCRIPTION = "Trilingual translator: English → Portuguese + Greek, other languages → English. Supports text, images, audio, and video."
    SYSTEM_PROMPT = (
        "You are a translation assistant.\n\n" + _TRANSLATION_RULES
    )

    def process_message(
        self, message: Dict[str, Any], history: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[str]:
        """
        Translate text; supports image (vision), audio, and video like the main translation bot.

        English → Portuguese and Greek. Any other language → English.
        """
        message_id = message.get("id")

        media_type = None

        if "media_type" in message:
            media_type = message["media_type"]

        elif "type" in message and message["type"] not in ["text", "chat", None]:
            media_type = message["type"]

        elif "message" in message and isinstance(message["message"], dict):
            msg_obj = message["message"]
            if "imageMessage" in msg_obj:
                media_type = "image"
            elif "audioMessage" in msg_obj or "pttMessage" in msg_obj:
                media_type = "audio"
            elif "videoMessage" in msg_obj:
                media_type = "video"

        elif "mimetype" in message:
            mime = message["mimetype"]
            if mime.startswith("image/"):
                media_type = "image"
            elif mime.startswith("audio/"):
                media_type = "audio"
            elif mime.startswith("video/"):
                media_type = "video"

        logger.info(f"[{self.NAME}] Detected media_type='{media_type}' for message {message_id}")

        if media_type and "image" in str(media_type).lower():
            logger.info(f"[{self.NAME}] Processing image message {message_id}")
            return self._process_image_message(message)

        if media_type and any(x in str(media_type).lower() for x in ["audio", "voice", "ptt"]):
            logger.info(f"[{self.NAME}] Processing audio message {message_id}")
            return self._process_audio_message(message)

        if media_type and "video" in str(media_type).lower():
            logger.info(f"[{self.NAME}] Processing video message {message_id}")
            return self._process_video_message(message)

        msg_text = message.get("content", "")
        if not msg_text:
            return None

        logger.info(f"[{self.NAME}] Processing text message {message_id}")
        return self._process_text_message(msg_text, history)

    def _process_image_message(self, message: Dict[str, Any]) -> Optional[str]:
        message_id = message.get("id")
        chat_jid = self.chat_jid

        try:
            logger.info(f"[{self.NAME}] Downloading image from message {message_id}")
            image_bytes = self.whatsapp.download_and_decrypt_image(message_id, chat_jid)

            if not image_bytes:
                logger.error(f"[{self.NAME}] Failed to download image")
                return "❌ Sorry, I couldn't download the image."

            prompt = f"""You are a multilingual image analysis assistant. Your task is to:

1. Carefully examine the image for ANY text, writing, signs, labels, or written content
2. If you find text:
   - Extract all the text you can see
   - Apply these translation rules to that text:
{_TRANSLATION_RULES_IMAGE}
   - If the extracted text is in English, present it clearly in this format:
     📝 Original Text: [the text you found]
     🇧🇷 Portuguese: [translation]
     🇬🇷 Greek: [translation]
   - If the extracted text is NOT in English, present:
     📝 Original Text: [the text you found]
     🌍 English: [translation to English only]
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
        message_id = message.get("id")
        chat_jid = self.chat_jid

        try:
            logger.info(f"[{self.NAME}] Downloading audio from message {message_id}")
            audio_bytes = self.whatsapp.download_and_decrypt_audio(message_id, chat_jid)

            if not audio_bytes:
                logger.error(f"[{self.NAME}] Failed to download audio")
                return (
                    "❌ Sorry, I couldn't download the audio message. Please try sending it again."
                )

            logger.info(f"[{self.NAME}] Transcribing audio with Whisper API")
            transcription = self.llm.transcribe_audio(audio_bytes)

            if not transcription:
                logger.error(f"[{self.NAME}] Audio transcription failed after retries")
                return "❌ Sorry, I couldn't transcribe the audio after multiple attempts. The audio might be unclear, in an unsupported format, or there might be a temporary service issue. Please try again later."

            logger.info(f"[{self.NAME}] Transcription successful: {transcription[:50]}...")

            logger.info(f"[{self.NAME}] Translating transcription")
            translation = self._translate_text(transcription)

            if not translation:
                logger.warning(f"[{self.NAME}] Translation failed, returning transcription only")
                return f"🎤 Transcription:\n{transcription}\n\n⚠️ Translation service temporarily unavailable."

            response = f"🎤 Transcription:\n{transcription}\n\n🌍 Translation:\n{translation}"

            logger.info(f"[{self.NAME}] Audio processing complete")
            return response

        except Exception as e:
            logger.error(f"[{self.NAME}] Unexpected error processing audio: {e}", exc_info=True)
            return f"❌ An unexpected error occurred while processing the audio message. Please try again or contact support if the issue persists. (Error: {type(e).__name__})"

    def _process_video_message(self, message: Dict[str, Any]) -> Optional[str]:
        message_id = message.get("id")
        chat_jid = self.chat_jid

        try:
            logger.info(f"[{self.NAME}] Downloading video from message {message_id}")
            video_bytes = self.whatsapp.download_and_decrypt_video(message_id, chat_jid)

            if not video_bytes:
                logger.error(f"[{self.NAME}] Failed to download video")
                return "❌ Sorry, I couldn't download the video. Please try sending it again."

            video_size_mb = len(video_bytes) / (1024 * 1024)
            logger.info(f"[{self.NAME}] Video size: {video_size_mb:.2f} MB")

            if video_size_mb > 100:
                logger.warning(f"[{self.NAME}] Video is very large: {video_size_mb:.2f} MB")
                return f"❌ Video is too large ({video_size_mb:.1f} MB). Please send videos under 100 MB."

            logger.info(f"[{self.NAME}] Extracting audio from video")
            audio_bytes = self.llm.extract_audio_from_video(video_bytes)

            if not audio_bytes:
                logger.warning(f"[{self.NAME}] Video has no audio track or extraction failed")
                return "❌ This video doesn't have an audio track, or I couldn't extract it. Please make sure the video has sound."

            audio_size_mb = len(audio_bytes) / (1024 * 1024)
            logger.info(f"[{self.NAME}] Extracted audio size: {audio_size_mb:.2f} MB")

            if audio_size_mb > 25:
                logger.error(f"[{self.NAME}] Extracted audio exceeds Whisper's 25MB limit")
                return f"❌ The video's audio is too long ({audio_size_mb:.1f} MB). Whisper API supports up to 25 MB. Please send a shorter video."

            logger.info(f"[{self.NAME}] Transcribing video audio with Whisper API")
            transcription = self.llm.transcribe_audio(audio_bytes)

            if not transcription:
                logger.error(f"[{self.NAME}] Video audio transcription failed after retries")
                return "❌ Sorry, I couldn't transcribe the video's audio after multiple attempts. The audio might be unclear, in an unsupported format, or there might be a temporary service issue. Please try again later."

            logger.info(f"[{self.NAME}] Transcription successful: {transcription[:50]}...")

            logger.info(f"[{self.NAME}] Translating transcription")
            translation = self._translate_text(transcription)

            if not translation:
                logger.warning(f"[{self.NAME}] Translation failed, returning transcription only")
                return f"🎬 Video Audio Transcription:\n{transcription}\n\n⚠️ Translation service temporarily unavailable."

            response = (
                f"🎬 Video Audio Transcription:\n{transcription}\n\n🌍 Translation:\n{translation}"
            )

            logger.info(f"[{self.NAME}] Video audio processing complete")
            return response

        except Exception as e:
            logger.error(f"[{self.NAME}] Unexpected error processing video: {e}", exc_info=True)
            return f"❌ An unexpected error occurred while processing the video. Please try again or contact support if the issue persists. (Error: {type(e).__name__})"

    def _process_text_message(
        self, msg_text: str, history: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[str]:
        if history:
            system_prompt = f"""You are a translation assistant. Your task is to:
1. Consider the conversation context provided
2. Apply these rules to the current message:
{_TRANSLATION_RULES}
3. Use the conversation context to better understand references, pronouns, and implied meanings
4. Return ONLY the translation result (no explanations before or after)"""

            translated_text = self.llm.call_with_history(
                system_prompt=system_prompt, current_message=msg_text, history=history
            )
        else:
            translated_text = self._translate_text(msg_text)

        if not translated_text:
            logger.error(f"[{self.NAME}] Failed to translate message")
            return None

        logger.info(f"[{self.NAME}] Translated: {msg_text[:30]}... -> {translated_text[:30]}...")
        return translated_text

    def _translate_text(self, text: str) -> Optional[str]:
        prompt = f"""You are a translation assistant.

{_TRANSLATION_RULES}

Text to translate:
{text}

Respond with ONLY the translation result as specified above (for English: both lines with flags; for other languages: English text only)."""

        return self.llm.call(prompt)
