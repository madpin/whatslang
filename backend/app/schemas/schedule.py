"""Schedule schemas"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ScheduleType(str, Enum):
    """Schedule type enumeration"""
    ONCE = "once"
    CRON = "cron"


class ScheduleBase(BaseModel):
    """Base schedule fields"""
    message: str = Field(..., min_length=1)
    schedule_type: ScheduleType
    schedule_expression: str = Field(
        ...,
        description="ISO datetime for 'once' or cron expression for 'cron'"
    )
    timezone: str = Field(default="UTC", max_length=100)
    enabled: bool = True
    schedule_metadata: Dict[str, Any] = Field(default_factory=dict)


class ScheduleCreate(ScheduleBase):
    """Schema for creating a schedule"""
    chat_id: str


class ScheduleUpdate(BaseModel):
    """Schema for updating a schedule"""
    message: Optional[str] = Field(None, min_length=1)
    schedule_type: Optional[ScheduleType] = None
    schedule_expression: Optional[str] = None
    timezone: Optional[str] = Field(None, max_length=100)
    enabled: Optional[bool] = None
    schedule_metadata: Optional[Dict[str, Any]] = None


class ScheduleResponse(ScheduleBase):
    """Schema for schedule response"""
    id: str
    chat_id: str
    next_run_at: Optional[datetime]
    last_run_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class ScheduleListResponse(BaseModel):
    """Schema for schedule list response"""
    schedules: list[ScheduleResponse]
    total: int


class ScheduleRunResponse(BaseModel):
    """Schema for manual schedule run response"""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None

