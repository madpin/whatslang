"""ChatBot association model"""

from sqlalchemy import String, Boolean, JSON, Integer, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Dict, Any

from .base import Base, TimestampMixin, generate_uuid


class ChatBot(Base, TimestampMixin):
    """Association between chats and bots"""
    
    __tablename__ = "chat_bots"
    
    __table_args__ = (
        UniqueConstraint("chat_id", "bot_id", name="uq_chat_bot"),
        Index("ix_chat_bots_chat_id", "chat_id"),
        Index("ix_chat_bots_bot_id", "bot_id"),
    )
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid
    )
    
    chat_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("chats.id", ondelete="CASCADE"),
        nullable=False
    )
    
    bot_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("bots.id", ondelete="CASCADE"),
        nullable=False
    )
    
    config_override: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
        comment="Per-chat configuration overrides"
    )
    
    enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true"
    )
    
    priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
        comment="Execution order (lower = earlier)"
    )
    
    # Relationships
    chat: Mapped["Chat"] = relationship(
        "Chat",
        back_populates="bot_assignments"
    )
    
    bot: Mapped["Bot"] = relationship(
        "Bot",
        back_populates="chat_assignments"
    )
    
    def __repr__(self) -> str:
        return f"<ChatBot(id={self.id}, chat_id={self.chat_id}, bot_id={self.bot_id}, priority={self.priority})>"

