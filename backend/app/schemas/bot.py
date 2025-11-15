"""Bot schemas"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class BotInfo(BaseModel):
    """Bot type information and configuration schema"""
    type: str
    name: str
    description: str
    config_schema: Dict[str, Any] = Field(
        default_factory=dict,
        description="JSON Schema for bot configuration"
    )
    ui_schema: Optional[Dict[str, Any]] = Field(
        default=None,
        description="UI hints for form rendering"
    )


class BotBase(BaseModel):
    """Base bot fields"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True


class BotCreate(BotBase):
    """Schema for creating a bot"""
    type: str = Field(..., min_length=1, max_length=100)


class BotUpdate(BaseModel):
    """Schema for updating a bot"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None


class BotResponse(BotBase):
    """Schema for bot response"""
    id: str
    type: str
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class BotListResponse(BaseModel):
    """Schema for bot list response"""
    bots: list[BotResponse]
    total: int


class BotTypeInfo(BaseModel):
    """Schema for available bot type information"""
    type: str
    info: BotInfo

