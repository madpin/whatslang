"""Schedule API endpoints"""

import logging
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import ScheduledMessage, Chat, ScheduleType as ScheduleTypeModel, User
from app.schemas.schedule import (
    ScheduleCreate,
    ScheduleUpdate,
    ScheduleResponse,
    ScheduleListResponse,
    ScheduleRunResponse,
)
from app.core import MessageScheduler, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/schedules", tags=["schedules"])


# Dependency functions - will be injected by FastAPI
def get_message_scheduler_dependency() -> MessageScheduler:
    """Placeholder for MessageScheduler dependency - overridden in main.py"""
    raise NotImplementedError("MessageScheduler dependency not initialized")


@router.get("", response_model=ScheduleListResponse)
async def list_schedules(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all scheduled messages"""
    # Get total count
    count_stmt = select(func.count(ScheduledMessage.id))
    count_result = await db.execute(count_stmt)
    total = count_result.scalar_one()
    
    # Get schedules
    stmt = (
        select(ScheduledMessage)
        .offset(skip)
        .limit(limit)
        .order_by(ScheduledMessage.created_at.desc())
    )
    result = await db.execute(stmt)
    schedules = result.scalars().all()
    
    return ScheduleListResponse(
        schedules=[ScheduleResponse.model_validate(s) for s in schedules],
        total=total
    )


@router.post("", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    schedule_data: ScheduleCreate,
    db: AsyncSession = Depends(get_db),
    scheduler: Annotated[MessageScheduler, Depends(get_message_scheduler_dependency)] = None,
    current_user: User = Depends(get_current_user)
):
    """Create a new scheduled message"""
    # Verify chat exists
    stmt = select(Chat).where(Chat.id == schedule_data.chat_id)
    result = await db.execute(stmt)
    chat = result.scalar_one_or_none()
    
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    # Create schedule
    schedule = ScheduledMessage(
        chat_id=schedule_data.chat_id,
        message=schedule_data.message,
        schedule_type=schedule_data.schedule_type,
        schedule_expression=schedule_data.schedule_expression,
        timezone=schedule_data.timezone,
        enabled=schedule_data.enabled,
        schedule_metadata=schedule_data.schedule_metadata
    )
    
    db.add(schedule)
    await db.flush()
    await db.refresh(schedule)
    
    # Add to scheduler
    if schedule.enabled:
        await scheduler.schedule_message(
            schedule_id=schedule.id,
            chat_id=schedule.chat_id,
            message=schedule.message,
            schedule_type=schedule.schedule_type,
            schedule_expression=schedule.schedule_expression,
            timezone=schedule.timezone
        )
    
    logger.info(f"Created schedule: {schedule.id}")
    
    return ScheduleResponse.model_validate(schedule)


@router.get("/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(
    schedule_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a schedule by ID"""
    stmt = select(ScheduledMessage).where(ScheduledMessage.id == schedule_id)
    result = await db.execute(stmt)
    schedule = result.scalar_one_or_none()
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )
    
    return ScheduleResponse.model_validate(schedule)


@router.put("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: str,
    schedule_data: ScheduleUpdate,
    db: AsyncSession = Depends(get_db),
    scheduler: Annotated[MessageScheduler, Depends(get_message_scheduler_dependency)] = None,
    current_user: User = Depends(get_current_user)
):
    """Update a schedule"""
    stmt = select(ScheduledMessage).where(ScheduledMessage.id == schedule_id)
    result = await db.execute(stmt)
    schedule = result.scalar_one_or_none()
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )
    
    # Update fields
    if schedule_data.message is not None:
        schedule.message = schedule_data.message
    if schedule_data.schedule_type is not None:
        schedule.schedule_type = schedule_data.schedule_type
    if schedule_data.schedule_expression is not None:
        schedule.schedule_expression = schedule_data.schedule_expression
    if schedule_data.timezone is not None:
        schedule.timezone = schedule_data.timezone
    if schedule_data.enabled is not None:
        schedule.enabled = schedule_data.enabled
    if schedule_data.schedule_metadata is not None:
        schedule.schedule_metadata = schedule_data.schedule_metadata
    
    await db.flush()
    await db.refresh(schedule)
    
    # Update in scheduler
    await scheduler.update_schedule(schedule_id)
    
    logger.info(f"Updated schedule: {schedule_id}")
    
    return ScheduleResponse.model_validate(schedule)


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: str,
    db: AsyncSession = Depends(get_db),
    scheduler: Annotated[MessageScheduler, Depends(get_message_scheduler_dependency)] = None,
    current_user: User = Depends(get_current_user)
):
    """Delete a schedule"""
    stmt = select(ScheduledMessage).where(ScheduledMessage.id == schedule_id)
    result = await db.execute(stmt)
    schedule = result.scalar_one_or_none()
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )
    
    # Remove from scheduler
    await scheduler.remove_schedule(schedule_id)
    
    # Delete from database
    await db.delete(schedule)
    await db.flush()
    
    logger.info(f"Deleted schedule: {schedule_id}")


@router.post("/{schedule_id}/run", response_model=ScheduleRunResponse)
async def run_schedule(
    schedule_id: str,
    db: AsyncSession = Depends(get_db),
    scheduler: Annotated[MessageScheduler, Depends(get_message_scheduler_dependency)] = None,
    current_user: User = Depends(get_current_user)
):
    """Manually trigger a schedule to run immediately"""
    stmt = select(ScheduledMessage).where(ScheduledMessage.id == schedule_id)
    result = await db.execute(stmt)
    schedule = result.scalar_one_or_none()
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Schedule not found"
        )
    
    try:
        # Trigger schedule
        await scheduler.trigger_schedule(schedule_id)
        
        logger.info(f"Manually triggered schedule: {schedule_id}")
        
        return ScheduleRunResponse(
            success=True,
            message="Schedule triggered successfully"
        )
    except Exception as e:
        logger.error(f"Error triggering schedule: {e}")
        return ScheduleRunResponse(
            success=False,
            error=str(e)
        )

