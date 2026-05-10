"""Pydantic models exposed by the HTTP API."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


# ----- Auth -----------------------------------------------------------------
class LoginRequest(BaseModel):
    user: Optional[str] = None
    password: str


class AuthStatus(BaseModel):
    auth_required: bool
    user: Optional[str] = None


class SimpleMessage(BaseModel):
    message: str


# ----- Bot catalog ----------------------------------------------------------
class BotSupports(BaseModel):
    text: bool = True
    image: bool = False
    audio: bool = False
    video: bool = False


class BotType(BaseModel):
    name: str
    label: str
    prefix: str
    emoji: str
    description: str
    supports: BotSupports


class BotStatus(BaseModel):
    name: str
    label: str
    prefix: str
    emoji: str
    description: str
    chat_jid: str
    status: str  # "running" | "stopped"
    uptime_seconds: Optional[int] = None
    answer_owner_messages: bool = True
    context_message_count: int = 0
    response_chat_jid: Optional[str] = None
    supports: BotSupports


class BotLogEntry(BaseModel):
    timestamp: str
    level: str
    message: str


class BotLogs(BaseModel):
    bot_name: str
    chat_jid: str
    logs: list[BotLogEntry]


# ----- Chats ----------------------------------------------------------------
class Chat(BaseModel):
    chat_jid: str
    chat_name: str
    is_manual: bool = False
    is_group: bool = False
    last_synced: Optional[str] = None
    last_message_time: Optional[str] = None
    message_count: int = 0
    added_at: str


class ChatWithBots(Chat):
    bots: list[BotStatus] = Field(default_factory=list)


class ChatBrief(BaseModel):
    chat_jid: str
    chat_name: str


class Pagination(BaseModel):
    page: int
    per_page: int
    total: int
    total_pages: int


class ChatListResponse(BaseModel):
    chats: list[ChatWithBots]
    pagination: Pagination


class AddChatRequest(BaseModel):
    chat_jid: str
    chat_name: Optional[str] = None


class BulkActionRequest(BaseModel):
    chat_jids: list[str]
    action: str  # 'start_bots' | 'stop_bots' | 'delete_chats'


class BotSettingsUpdate(BaseModel):
    answer_owner_messages: Optional[bool] = None
    context_message_count: Optional[int] = None
    response_chat_jid: Optional[str] = None  # empty string clears it


# ----- System ---------------------------------------------------------------
class Health(BaseModel):
    status: str
    timestamp: str
    version: str


class Stats(BaseModel):
    total_chats: int
    running_bots: int
    available_bot_types: int
    active_chats_24h: int


class SystemInfo(BaseModel):
    version: str
    environment: str
    auth_required: bool
    whatsapp_base_url: Optional[str] = None
    openai_model: str
    openai_vision_model: str
    openai_audio_model: str
    poll_interval: int
    db_path: str


# ----- Diagnostics ----------------------------------------------------------
class GatewayDiagnostics(BaseModel):
    base_url: Optional[str] = None
    reachable: bool = False
    http_status: Optional[int] = None
    latency_ms: Optional[int] = None
    is_connected: bool = False
    is_logged_in: bool = False
    device_id: Optional[str] = None
    error: Optional[str] = None
    last_call_at: Optional[str] = None
    last_error_at: Optional[str] = None
    call_count: int = 0
    error_count: int = 0


class LlmDiagnostics(BaseModel):
    base_url: Optional[str] = None
    text_model: str
    vision_model: str
    audio_model: str
    api_key_set: bool


class DatabaseDiagnostics(BaseModel):
    path: str
    size_bytes: int
    chats: int
    assignments: int
    processed_messages: int


class BotsDiagnostics(BaseModel):
    catalog_size: int
    running: int
    poll_interval: int


class GatewayErrorEntry(BaseModel):
    timestamp: str
    where: str
    status: Optional[int] = None
    message: str


class Diagnostics(BaseModel):
    timestamp: str
    version: str
    environment: str
    gateway: GatewayDiagnostics
    llm: LlmDiagnostics
    database: DatabaseDiagnostics
    bots: BotsDiagnostics
    recent_errors: list[GatewayErrorEntry] = Field(default_factory=list)
