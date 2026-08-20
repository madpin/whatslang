from __future__ import annotations

from typing import Any

from app.bots.base import BotRunner, BotSpec
from app.services.whatsapp import WhatsAppClient


class _DB:
    def __init__(self, *, answer_owner_messages: bool = True) -> None:
        self.answer_owner_messages = answer_owner_messages

    def is_processed(self, *_: Any) -> bool:
        return False

    def get_assignment(self, *_: Any) -> dict[str, Any]:
        return {
            "answer_owner_messages": int(self.answer_owner_messages),
            "context_message_count": 0,
        }


class _WhatsApp:
    @staticmethod
    def is_bot_sender(*_: Any) -> bool:
        return False

    def download_image(self, *_: Any) -> bytes:
        raise AssertionError("self-sent media should not be downloaded")


class _LLM:
    def __init__(self) -> None:
        self.last_user_text: str | None = None

    def call(self, _system_prompt: str, user_text: str) -> str:
        self.last_user_text = user_text
        return "text reply"


def _runner(*, answer_owner_messages: bool = True, llm: Any | None = None) -> BotRunner:
    spec = BotSpec(
        name="test",
        label="Test",
        prefix="[test]",
        description="",
        text_system_prompt="reply briefly",
        image_prompt="describe",
    )
    return BotRunner(
        spec,
        whatsapp=_WhatsApp(),  # type: ignore[arg-type]
        llm=llm or _LLM(),  # type: ignore[arg-type]
        db=_DB(answer_owner_messages=answer_owner_messages),  # type: ignore[arg-type]
        chat_jid="12345@g.us",
        bot_device_id="",
    )


def test_should_skip_empty_self_sent_media_even_when_owner_messages_enabled() -> None:
    runner = _runner(answer_owner_messages=True)

    assert (
        runner._should_process(
            {
                "id": "media-1",
                "media_type": "image",
                "content": "",
                "is_from_me": True,
            }
        )
        is False
    )


def test_should_still_process_self_sent_text_when_owner_messages_enabled() -> None:
    runner = _runner(answer_owner_messages=True)

    assert (
        runner._should_process(
            {
                "id": "text-1",
                "type": "text",
                "content": "hello",
                "is_from_me": True,
            }
        )
        is True
    )


def test_self_sent_text_is_not_filtered_by_matching_device_jid() -> None:
    runner = _runner(answer_owner_messages=True)
    runner.bot_device_id = "353834210235@s.whatsapp.net"
    runner.whatsapp.is_bot_sender = WhatsAppClient.is_bot_sender  # type: ignore[method-assign]

    assert (
        runner._should_process(
            {
                "id": "text-personal-1",
                "type": "text",
                "content": "hello",
                "sender_jid": "353834210235@s.whatsapp.net",
                "is_from_me": True,
            }
        )
        is True
    )


def test_self_sent_media_caption_is_handled_as_text_only() -> None:
    llm = _LLM()
    runner = _runner(answer_owner_messages=True, llm=llm)

    response = runner._produce_response(
        {
            "id": "caption-1",
            "media_type": "image",
            "content": "caption text",
            "is_from_me": True,
        },
        "caption text",
    )

    assert response == "text reply"
    assert llm.last_user_text == "caption text"
