"""Pydantic schemas for request/response validation"""

from .bot import (
    BotInfo,
    BotCreate,
    BotUpdate,
    BotResponse,
    BotListResponse,
    BotTypeInfo,
)
from .chat import (
    ChatType,
    ChatCreate,
    ChatUpdate,
    ChatResponse,
    ChatListResponse,
    ChatBotAssignmentCreate,
    ChatBotAssignmentUpdate,
    ChatBotAssignmentResponse,
)
from .message import (
    Message,
    Response,
    MessageSendRequest,
    MessageSendResponse,
    ProcessedMessageResponse,
    ProcessedMessageListResponse,
)
from .schedule import (
    ScheduleType,
    ScheduleCreate,
    ScheduleUpdate,
    ScheduleResponse,
    ScheduleListResponse,
    ScheduleRunResponse,
)

__all__ = [
    # Bot schemas
    "BotInfo",
    "BotCreate",
    "BotUpdate",
    "BotResponse",
    "BotListResponse",
    "BotTypeInfo",
    # Chat schemas
    "ChatType",
    "ChatCreate",
    "ChatUpdate",
    "ChatResponse",
    "ChatListResponse",
    "ChatBotAssignmentCreate",
    "ChatBotAssignmentUpdate",
    "ChatBotAssignmentResponse",
    # Message schemas
    "Message",
    "Response",
    "MessageSendRequest",
    "MessageSendResponse",
    "ProcessedMessageResponse",
    "ProcessedMessageListResponse",
    # Schedule schemas
    "ScheduleType",
    "ScheduleCreate",
    "ScheduleUpdate",
    "ScheduleResponse",
    "ScheduleListResponse",
    "ScheduleRunResponse",
]
