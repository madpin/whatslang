"""Message schemas"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class Message(BaseModel):
    """Incoming message schema"""
    id: str
    chat_jid: str
    sender_jid: str
    content: Optional[str] = None
    media_type: Optional[str] = None
    media_url: Optional[str] = None
    reply_to_id: Optional[str] = None
    timestamp: datetime
    message_metadata: Dict[str, Any] = Field(default_factory=dict)


class Response(BaseModel):
    """Bot response schema"""
    content: str
    reply_to: Optional[str] = None
    media_path: Optional[str] = None


class MessageSendRequest(BaseModel):
    """Schema for sending a message"""
    chat_jid: str = Field(..., description="WhatsApp JID to send message to")
    message: str = Field(..., min_length=1, description="Message content")
    reply_message_id: Optional[str] = Field(None, description="Message ID to reply to")


class MessageSendResponse(BaseModel):
    """Schema for message send response"""
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None


class ProcessedMessageResponse(BaseModel):
    """Schema for processed message response"""
    id: str
    message_id: str
    chat_id: Optional[str]
    bot_id: Optional[str]
    content: Optional[str]
    response: Optional[str]
    message_metadata: Dict[str, Any]
    processed_at: datetime
    
    model_config = {"from_attributes": True}


class ProcessedMessageListResponse(BaseModel):
    """Schema for processed message list response"""
    messages: list[ProcessedMessageResponse]
    total: int
    page: int
    page_size: int

