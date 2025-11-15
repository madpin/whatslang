"""Chat schemas"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ChatType(str, Enum):
    """Chat type enumeration"""
    PRIVATE = "private"
    GROUP = "group"
    CHANNEL = "channel"


class ChatBase(BaseModel):
    """Base chat fields"""
    jid: str = Field(..., min_length=1, max_length=100)
    name: Optional[str] = Field(None, max_length=255)
    chat_type: Optional[ChatType] = None
    chat_metadata: Dict[str, Any] = Field(default_factory=dict)


class ChatCreate(ChatBase):
    """Schema for creating a chat"""
    pass


class ChatUpdate(BaseModel):
    """Schema for updating a chat"""
    name: Optional[str] = Field(None, max_length=255)
    chat_type: Optional[ChatType] = None
    chat_metadata: Optional[Dict[str, Any]] = None


class ChatResponse(ChatBase):
    """Schema for chat response"""
    id: str
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class ChatListResponse(BaseModel):
    """Schema for chat list response"""
    chats: list[ChatResponse]
    total: int


class ChatBotAssignmentCreate(BaseModel):
    """Schema for assigning a bot to a chat"""
    bot_id: str
    config_override: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    priority: int = 0


class ChatBotAssignmentUpdate(BaseModel):
    """Schema for updating a chat-bot assignment"""
    config_override: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None
    priority: Optional[int] = None


class ChatBotAssignmentResponse(BaseModel):
    """Schema for chat-bot assignment response"""
    id: str
    chat_id: str
    bot_id: str
    config_override: Dict[str, Any]
    enabled: bool
    priority: int
    created_at: datetime
    
    model_config = {"from_attributes": True}

