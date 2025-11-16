"""Pydantic models for API responses."""

from typing import List, Optional
from pydantic import BaseModel


class BotStatus(BaseModel):
    """Status of a bot."""
    name: str
    chat_jid: str
    display_name: str
    status: str  # "running" or "stopped"
    prefix: str
    uptime_seconds: Optional[int] = None
    answer_owner_messages: bool = True  # Whether the bot should answer owner messages


class BotLog(BaseModel):
    """Log entry from a bot."""
    timestamp: str
    level: str
    message: str


class BotLogsResponse(BaseModel):
    """Response containing bot logs."""
    bot_name: str
    chat_jid: str
    logs: List[BotLog]


class Chat(BaseModel):
    """Chat information."""
    chat_jid: str
    chat_name: str
    is_manual: bool
    last_synced: Optional[str] = None
    added_at: str


class ChatWithBots(BaseModel):
    """Chat with bot status information."""
    chat_jid: str
    chat_name: str
    is_manual: bool
    last_synced: Optional[str] = None
    added_at: str
    bots: List[BotStatus]


class BotAssignment(BaseModel):
    """Bot-chat assignment."""
    bot_name: str
    chat_jid: str
    running: bool


class AddChatRequest(BaseModel):
    """Request to add a chat manually."""
    chat_jid: str
    chat_name: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: Optional[str] = None


class SuccessResponse(BaseModel):
    """Success response."""
    message: str

