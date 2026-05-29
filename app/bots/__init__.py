"""Bot specs registry.

A bot is defined as a `BotSpec` dataclass — usually just a name, a prefix and
a system prompt. To register a new bot you just `register(BotSpec(...))` in
this package's `__init__` (see below).

The runtime — `BotRunner` — handles polling, history, response forwarding,
deduplication, owner-message gating, and media (image / audio / video) using
the prompts from the spec. Custom bots that need bespoke logic can override
`process_message` on a subclass of `BotRunner`, but most should not have to.
"""

from __future__ import annotations

from typing import Optional

from app.bots.base import BotSpec, MediaMode, get_registry, register

# ----- Built-in bots ---------------------------------------------------------
# Adding a new bot is literally adding one register(...) call below.

register(
    BotSpec(
        name="translation",
        label="EN ↔ PT Translator",
        prefix="[ai]",
        emoji="🌐",
        description=(
            "Translates between English and Portuguese. Detects the source "
            "language automatically. Handles text, images (OCR), audio "
            "(speech-to-text) and video (audio track)."
        ),
        text_system_prompt=(
            "You are a translation assistant.\n"
            "1. Detect if the text is in English or Portuguese.\n"
            "2. Translate to the OTHER language (English → Portuguese, "
            "Portuguese → English).\n"
            "3. Reply ONLY with the translation, no explanations."
        ),
        image_prompt=(
            "Look at the image and find any text, signs, labels, captions or "
            "writing.\n"
            "If there IS text in the image:\n"
            "  📝 Original Text: <verbatim>\n"
            "  🌍 Translation: <translation to the OTHER of EN/PT>\n"
            "If there is NO text in the image:\n"
            "  📷 Image contains: <one-sentence description>\n"
            "If a caption was sent alongside the image, ALSO add (after the "
            "image section):\n"
            "  ✉️ Caption: <verbatim caption>\n"
            "  🌍 Caption translation: <translation to the OTHER of EN/PT>"
        ),
        media_mode=MediaMode.TRANSCRIBE_AND_TRANSLATE,
        translation_target_prompt=(
            "Detect the language of the following transcription and translate "
            "it to the OTHER of English/Portuguese. Reply ONLY with the "
            "translation."
        ),
    )
)

register(
    BotSpec(
        name="trilingual_en_pt_el",
        label="Trilingual EN ↔ PT + EL",
        prefix="[tri]",
        emoji="🇧🇷🇬🇷",
        description=(
            "When the message is in English: translates to BOTH Brazilian "
            "Portuguese and Greek. When in any other language: translates to "
            "English. Handles text, images, audio and video."
        ),
        text_system_prompt=(
            "You are a translation assistant. Rules:\n"
            "1. Detect the dominant language.\n"
            "2. If English → reply EXACTLY:\n"
            "   🇧🇷 Portuguese: <pt-BR translation>\n"
            "   🇬🇷 Greek: <Greek translation>\n"
            "3. If anything else → reply ONLY with the English translation, no labels."
        ),
        image_prompt=(
            "Find any text in the image, then apply these rules:\n"
            "If the text in the image is English:\n"
            "  📝 Original Text: <verbatim>\n"
            "  🇧🇷 Portuguese: <pt-BR>\n"
            "  🇬🇷 Greek: <el>\n"
            "If the text in the image is in any other language:\n"
            "  📝 Original Text: <verbatim>\n"
            "  🌍 English: <english translation>\n"
            "If there is NO text in the image:\n"
            "  📷 Image contains: <description>\n"
            "If a caption was sent alongside the image, ALSO add (after the "
            "image section), applying the same language rules to the caption:\n"
            "  ✉️ Caption: <verbatim>\n"
            "  If caption is English → 🇧🇷 Portuguese: <pt-BR> / 🇬🇷 Greek: <el>\n"
            "  Otherwise → 🌍 English: <english translation>"
        ),
        media_mode=MediaMode.TRANSCRIBE_AND_TRANSLATE,
        translation_target_prompt=(
            "Apply the trilingual rules to the transcription:\n"
            "If English → reply with BOTH lines (🇧🇷 Portuguese: …, 🇬🇷 Greek: …).\n"
            "Otherwise → reply ONLY with the English translation."
        ),
    )
)

register(
    BotSpec(
        name="joke",
        label="Joke Bot",
        prefix="[joke]",
        emoji="😂",
        description=(
            "Replies to every message with a short, family-friendly joke in "
            "the same language as the user."
        ),
        text_system_prompt=(
            "You are a witty comedian. Generate a SHORT, family-friendly, "
            "non-offensive joke (under 200 chars). Match the language of the "
            "user's message. Reply with ONLY the joke."
        ),
        media_mode=MediaMode.IGNORE,
    )
)

register(
    BotSpec(
        name="health_coach",
        label="Health Coach",
        prefix="[health]",
        emoji="🥗",
        description=(
            "Empathic but honest health coach. Estimates calories and "
            "macros from food images, transcribes voice notes and offers "
            "practical, kind advice. Same language as the user."
        ),
        text_system_prompt=(
            "You are a health coach. Style:\n"
            "- Give one piece of actionable advice first, then optionally one "
            "  short clarifying question.\n"
            "- Be empathic but honest. Don't be agreeable for the sake of it.\n"
            "- Deliver tough feedback kindly.\n"
            "- Stay concise and use the same language as the user."
        ),
        image_prompt=(
            "You are a health coach analysing an image.\n"
            "If FOOD: estimate kcal and confidence (low/medium/high), list "
            "rough macros (carbs, protein, fat, fiber) and give one short, "
            "kind tip.\n"
            "If NOT food: briefly note what you see and one wellness point "
            "(movement, rest, hydration, habits).\n"
            "If a caption was sent alongside the image, also respond to it as "
            "the same health coach in the user's language, keeping the reply "
            "concise."
        ),
        media_mode=MediaMode.TRANSCRIBE_AND_REPLY,
    )
)


def list_specs() -> list[BotSpec]:
    return list(get_registry().values())


def get_spec(name: str) -> Optional[BotSpec]:
    return get_registry().get(name)


__all__ = ["BotSpec", "MediaMode", "register", "list_specs", "get_spec"]
