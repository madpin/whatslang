"""Bot API endpoints"""

import logging
from typing import List, Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Bot
from app.schemas.bot import (
    BotCreate,
    BotUpdate,
    BotResponse,
    BotListResponse,
    BotTypeInfo,
)
from app.core import BotManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/bots", tags=["bots"])


# Dependency to get BotManager - will be injected by FastAPI
def get_bot_manager_dependency() -> BotManager:
    """Placeholder for BotManager dependency - overridden in main.py"""
    raise NotImplementedError("BotManager dependency not initialized")


@router.get("/types", response_model=List[BotTypeInfo])
async def list_bot_types(
    bot_manager: Annotated[BotManager, Depends(get_bot_manager_dependency)]
):
    """List all available bot types with their configuration schemas"""
    available_types = bot_manager.get_available_bot_types()
    
    return [
        BotTypeInfo(type=bot_type, info=info)
        for bot_type, info in available_types.items()
    ]


@router.get("", response_model=BotListResponse)
async def list_bots(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List all bot instances"""
    # Get total count
    count_stmt = select(func.count(Bot.id))
    count_result = await db.execute(count_stmt)
    total = count_result.scalar_one()
    
    # Get bots
    stmt = (
        select(Bot)
        .offset(skip)
        .limit(limit)
        .order_by(Bot.created_at.desc())
    )
    result = await db.execute(stmt)
    bots = result.scalars().all()
    
    return BotListResponse(
        bots=[BotResponse.model_validate(bot) for bot in bots],
        total=total
    )


@router.post("", response_model=BotResponse, status_code=status.HTTP_201_CREATED)
async def create_bot(
    bot_data: BotCreate,
    db: AsyncSession = Depends(get_db),
    bot_manager: Annotated[BotManager, Depends(get_bot_manager_dependency)] = None
):
    """Create a new bot instance"""
    # Validate bot type
    if bot_data.type not in bot_manager.bot_registry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown bot type: {bot_data.type}"
        )
    
    # Create bot
    bot = Bot(
        type=bot_data.type,
        name=bot_data.name,
        description=bot_data.description,
        config=bot_data.config,
        enabled=bot_data.enabled
    )
    
    db.add(bot)
    await db.flush()
    await db.refresh(bot)
    
    logger.info(f"Created bot: {bot.id} ({bot.name})")
    
    return BotResponse.model_validate(bot)


@router.get("/{bot_id}", response_model=BotResponse)
async def get_bot(
    bot_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a bot by ID"""
    stmt = select(Bot).where(Bot.id == bot_id)
    result = await db.execute(stmt)
    bot = result.scalar_one_or_none()
    
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )
    
    return BotResponse.model_validate(bot)


@router.put("/{bot_id}", response_model=BotResponse)
async def update_bot(
    bot_id: str,
    bot_data: BotUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a bot"""
    stmt = select(Bot).where(Bot.id == bot_id)
    result = await db.execute(stmt)
    bot = result.scalar_one_or_none()
    
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )
    
    # Update fields
    if bot_data.name is not None:
        bot.name = bot_data.name
    if bot_data.description is not None:
        bot.description = bot_data.description
    if bot_data.config is not None:
        bot.config = bot_data.config
    if bot_data.enabled is not None:
        bot.enabled = bot_data.enabled
    
    await db.flush()
    await db.refresh(bot)
    
    logger.info(f"Updated bot: {bot.id}")
    
    return BotResponse.model_validate(bot)


@router.delete("/{bot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bot(
    bot_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a bot"""
    stmt = select(Bot).where(Bot.id == bot_id)
    result = await db.execute(stmt)
    bot = result.scalar_one_or_none()
    
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )
    
    await db.delete(bot)
    await db.flush()
    
    logger.info(f"Deleted bot: {bot_id}")

