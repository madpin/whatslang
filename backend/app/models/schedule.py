"""Schedule model"""

from sqlalchemy import String, Boolean, ForeignKey, Enum as SQLEnum, JSON, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, Dict, Any
from datetime import datetime
import enum

from .base import Base, TimestampMixin, generate_uuid


class ScheduleType(str, enum.Enum):
    """Schedule type enumeration"""
    ONCE = "once"
    CRON = "cron"


class ScheduledMessage(Base, TimestampMixin):
    """Scheduled message model"""
    
    __tablename__ = "scheduled_messages"
    
    __table_args__ = (
        Index("ix_scheduled_messages_next_run", "next_run_at", postgresql_where="enabled = true"),
        Index("ix_scheduled_messages_chat_id", "chat_id"),
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
    
    message: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment="Message to send"
    )
    
    schedule_type: Mapped[ScheduleType] = mapped_column(
        SQLEnum(ScheduleType, name="schedule_type_enum"),
        nullable=False,
        comment="Schedule type: once or cron"
    )
    
    schedule_expression: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="ISO datetime or cron expression"
    )
    
    timezone: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="UTC",
        server_default="UTC"
    )
    
    next_run_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Next scheduled run time"
    )
    
    last_run_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last execution time"
    )
    
    enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true"
    )
    
    schedule_metadata: Mapped[Dict[str, Any]] = mapped_column(
        "metadata",  # Column name in database
        JSON,
        nullable=False,
        default=dict,
        server_default="{}"
    )
    
    # Relationships
    chat: Mapped["Chat"] = relationship(
        "Chat",
        back_populates="scheduled_messages"
    )
    
    def __repr__(self) -> str:
        return f"<ScheduledMessage(id={self.id}, chat_id={self.chat_id}, type={self.schedule_type})>"

