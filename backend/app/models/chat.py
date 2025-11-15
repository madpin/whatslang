"""Chat model"""

from sqlalchemy import String, Enum as SQLEnum, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, Dict, Any
import enum

from .base import Base, TimestampMixin, generate_uuid


class ChatType(str, enum.Enum):
    """Chat type enumeration"""
    PRIVATE = "private"
    GROUP = "group"
    CHANNEL = "channel"


class Chat(Base, TimestampMixin):
    """WhatsApp chat model"""
    
    __tablename__ = "chats"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid
    )
    
    jid: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        comment="WhatsApp JID (unique identifier)"
    )
    
    name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Chat name (group name or contact name)"
    )
    
    chat_type: Mapped[ChatType] = mapped_column(
        SQLEnum(ChatType, name="chat_type_enum"),
        nullable=True,
        comment="Type of chat"
    )
    
    chat_metadata: Mapped[Dict[str, Any]] = mapped_column(
        "metadata",  # Column name in database
        JSON,
        nullable=False,
        default=dict,
        server_default="{}"
    )
    
    # Relationships
    bot_assignments: Mapped[list["ChatBot"]] = relationship(
        "ChatBot",
        back_populates="chat",
        cascade="all, delete-orphan"
    )
    
    processed_messages: Mapped[list["ProcessedMessage"]] = relationship(
        "ProcessedMessage",
        back_populates="chat",
        cascade="all, delete-orphan"
    )
    
    scheduled_messages: Mapped[list["ScheduledMessage"]] = relationship(
        "ScheduledMessage",
        back_populates="chat",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Chat(id={self.id}, jid={self.jid}, name={self.name})>"

