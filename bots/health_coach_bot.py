"""Health coach bot: empathic-but-honest coach with kcal estimation for food images."""

import logging
from typing import Any, Dict, List, Optional

from core.bot_base import BotBase

logger = logging.getLogger(__name__)

# System prompt for text and audio: advice first, questions second; empathic, honest, kind with bad news
HEALTH_COACH_SYSTEM_PROMPT = """You are a health coach. Your style:
- Give advice first, then ask one or two short clarifying questions if helpful.
- Be empathic but honest. Do not be agreeable for the sake of it.
- When something is unhelpful or risky, say so clearly but kindly—deliver "bad news" in a sweet, supportive way, like a good coach.
- Keep responses concise and actionable. Use the same language as the user."""

# Vision prompt: health coach for every image; if food → kcal + confidence + nutrients
HEALTH_COACH_IMAGE_PROMPT = """You are a health coach. Look at this image and respond from that perspective.

If the image shows FOOD or a MEAL:
1. Estimate the approximate calories (kcal) and say how confident you are (e.g. low/medium/high or a rough percentage).
2. Add relevant nutrition info when you can: e.g. carbs, protein, fiber, and notable vitamins or minerals.
3. Give one short, practical tip (e.g. portion, balance, or swap) in a kind way.

If the image is NOT food (e.g. person, activity, product, screenshot):
- Still respond as a health coach: briefly note what you see and one relevant wellness or lifestyle point (e.g. movement, rest, hydration, habits). Be supportive and honest.

Tone: empathic and honest. Don't sugarcoat; if something is not great for health, say it gently but clearly."""


class HealthCoachBot(BotBase):
    """Health coach and kcal calculator: text, images (food analysis), and audio/video."""

    NAME = "health_coach"
    PREFIX = "[health]"

    def process_message(
        self, message: Dict[str, Any], history: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[str]:
        """
        Process a message as a health coach. Supports text, image, audio, and video.

        Args:
            message: The message dict from WhatsApp API
            history: Optional list of previous messages for context

        Returns:
            Coach response text, or None to skip
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
            return self._process_image_message(message)
        if media_type and any(x in str(media_type).lower() for x in ["audio", "voice", "ptt"]):
            return self._process_audio_message(message)
        if media_type and "video" in str(media_type).lower():
            return self._process_video_message(message)

        msg_text = message.get("content", "")
        if not msg_text:
            return None
        return self._process_text_message(msg_text, history)

    def _process_image_message(self, message: Dict[str, Any]) -> Optional[str]:
        """Analyze image as health coach; if food, estimate kcal and nutrients with confidence."""
        message_id = message.get("id")
        chat_jid = self.chat_jid
        try:
            image_bytes = self.whatsapp.download_and_decrypt_image(message_id, chat_jid)
            if not image_bytes:
                logger.error(f"[{self.NAME}] Failed to download image")
                return "I couldn’t download the image. Please try sending it again."
            result = self.llm.call_with_image(HEALTH_COACH_IMAGE_PROMPT, image_bytes)
            if not result:
                return "I couldn’t analyze the image right now. Please try again in a moment."
            return result
        except Exception as e:
            logger.error(f"[{self.NAME}] Error processing image: {e}", exc_info=True)
            return "Something went wrong while looking at the image. Please try again."

    def _process_audio_message(self, message: Dict[str, Any]) -> Optional[str]:
        """Transcribe audio then respond as health coach."""
        message_id = message.get("id")
        chat_jid = self.chat_jid
        try:
            audio_bytes = self.whatsapp.download_and_decrypt_audio(message_id, chat_jid)
            if not audio_bytes:
                logger.error(f"[{self.NAME}] Failed to download audio")
                return "I couldn’t download the voice message. Please try again."
            transcription = self.llm.transcribe_audio(audio_bytes)
            if not transcription:
                return "I couldn’t transcribe the audio. It might be unclear or in an unsupported format—please try again or send a text."
            return self._coach_response(transcription, history=None)
        except Exception as e:
            logger.error(f"[{self.NAME}] Error processing audio: {e}", exc_info=True)
            return "Something went wrong with the voice message. Please try again or send a text."

    def _process_video_message(self, message: Dict[str, Any]) -> Optional[str]:
        """Extract audio from video, transcribe, then respond as health coach."""
        message_id = message.get("id")
        chat_jid = self.chat_jid
        try:
            video_bytes = self.whatsapp.download_and_decrypt_video(message_id, chat_jid)
            if not video_bytes:
                logger.error(f"[{self.NAME}] Failed to download video")
                return "I couldn’t download the video. Please try again."
            audio_bytes = self.llm.extract_audio_from_video(video_bytes)
            if not audio_bytes:
                return "This video doesn’t seem to have an audio track, or I couldn’t extract it. Send a voice note or text if you’d like coaching."
            if len(audio_bytes) > 25 * 1024 * 1024:
                return "The video’s audio is too long for me to process. Please send a shorter clip or a voice note."
            transcription = self.llm.transcribe_audio(audio_bytes)
            if not transcription:
                return "I couldn’t transcribe the video’s audio. Try a voice note or text instead."
            return self._coach_response(transcription, history=None)
        except Exception as e:
            logger.error(f"[{self.NAME}] Error processing video: {e}", exc_info=True)
            return "Something went wrong with the video. Please try again or send a voice note or text."

    def _process_text_message(
        self, msg_text: str, history: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[str]:
        """Respond as health coach: advice first, questions second; empathic and honest."""
        return self._coach_response(msg_text, history=history)

    def _coach_response(
        self, text: str, history: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[str]:
        """Single place for coach LLM call (text or transcript)."""
        if history:
            response = self.llm.call_with_history(
                system_prompt=HEALTH_COACH_SYSTEM_PROMPT,
                current_message=text,
                history=history,
            )
        else:
            response = self.llm.call(
                HEALTH_COACH_SYSTEM_PROMPT,
                text,
            )
        return response
