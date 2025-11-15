"""Bot implementations"""

from .base import BaseBot, BotServices
from .translation import TranslationBot

# Registry of available bot types
AVAILABLE_BOTS = {
    "translation": TranslationBot,
}

__all__ = [
    "BaseBot",
    "BotServices",
    "TranslationBot",
    "AVAILABLE_BOTS",
]
