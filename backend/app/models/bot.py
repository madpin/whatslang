"""Bot model"""

from sqlalchemy import String, Boolean, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, Dict, Any

from .base import Base, TimestampMixin, generate_uuid


class Bot(Base, TimestampMixin):
    """Bot instance model"""
    
    __tablename__ = "bots"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid
    )
    
    type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Bot type (e.g., 'translation', 'search')"
    )
    
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="User-defined bot name"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        String,
        nullable=True
    )
    
    config: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        server_default="{}"
    )
    
    enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true"
    )
    
    # Relationships
    chat_assignments: Mapped[list["ChatBot"]] = relationship(
        "ChatBot",
        back_populates="bot",
        cascade="all, delete-orphan"
    )
    
    processed_messages: Mapped[list["ProcessedMessage"]] = relationship(
        "ProcessedMessage",
        back_populates="bot",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Bot(id={self.id}, type={self.type}, name={self.name})>"

