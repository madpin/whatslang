"""Message model"""

from sqlalchemy import String, ForeignKey, JSON, DateTime, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, Dict, Any
from datetime import datetime

from .base import Base, generate_uuid


class ProcessedMessage(Base):
    """Tracks processed messages for deduplication"""
    
    __tablename__ = "processed_messages"
    
    __table_args__ = (
        Index("ix_processed_messages_message_id", "message_id"),
        Index("ix_processed_messages_chat_bot", "chat_id", "bot_id"),
        Index("ix_processed_messages_processed_at", "processed_at"),
    )
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid
    )
    
    message_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        comment="WhatsApp message ID"
    )
    
    chat_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("chats.id", ondelete="CASCADE"),
        nullable=True
    )
    
    bot_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("bots.id", ondelete="CASCADE"),
        nullable=True
    )
    
    content: Mapped[Optional[str]] = mapped_column(
        String,
        nullable=True,
        comment="Original message content"
    )
    
    response: Mapped[Optional[str]] = mapped_column(
        String,
        nullable=True,
        comment="Bot response"
    )
    
    message_metadata: Mapped[Dict[str, Any]] = mapped_column(
        "metadata",  # Column name in database
        JSON,
        nullable=False,
        default=dict,
        server_default="{}"
    )
    
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    chat: Mapped[Optional["Chat"]] = relationship(
        "Chat",
        back_populates="processed_messages"
    )
    
    bot: Mapped[Optional["Bot"]] = relationship(
        "Bot",
        back_populates="processed_messages"
    )
    
    def __repr__(self) -> str:
        return f"<ProcessedMessage(id={self.id}, message_id={self.message_id})>"

