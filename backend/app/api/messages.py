"""Message API endpoints"""

import logging
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import ProcessedMessage, Chat
from app.schemas.message import (
    MessageSendRequest,
    MessageSendResponse,
    ProcessedMessageResponse,
    ProcessedMessageListResponse,
)
from app.services import WhatsAppClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/messages", tags=["messages"])


# Dependency functions - will be injected by FastAPI
def get_whatsapp_client_dependency() -> WhatsAppClient:
    """Placeholder for WhatsAppClient dependency - overridden in main.py"""
    raise NotImplementedError("WhatsAppClient dependency not initialized")


@router.get("", response_model=ProcessedMessageListResponse)
async def list_messages(
    skip: int = 0,
    limit: int = 100,
    chat_id: str = None,
    bot_id: str = None,
    db: AsyncSession = Depends(get_db)
):
    """List processed messages"""
    # Build query
    stmt = select(ProcessedMessage)
    
    if chat_id:
        stmt = stmt.where(ProcessedMessage.chat_id == chat_id)
    if bot_id:
        stmt = stmt.where(ProcessedMessage.bot_id == bot_id)
    
    # Get total count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    count_result = await db.execute(count_stmt)
    total = count_result.scalar_one()
    
    # Get messages
    stmt = (
        stmt
        .offset(skip)
        .limit(limit)
        .order_by(ProcessedMessage.processed_at.desc())
    )
    result = await db.execute(stmt)
    messages = result.scalars().all()
    
    page = skip // limit + 1 if limit > 0 else 1
    
    return ProcessedMessageListResponse(
        messages=[ProcessedMessageResponse.model_validate(m) for m in messages],
        total=total,
        page=page,
        page_size=limit
    )


@router.post("/send", response_model=MessageSendResponse)
async def send_message(
    message_data: MessageSendRequest,
    whatsapp: Annotated[WhatsAppClient, Depends(get_whatsapp_client_dependency)] = None
):
    """Send a message immediately"""
    try:
        success = await whatsapp.send_message(
            phone=message_data.chat_jid,
            message=message_data.message,
            reply_message_id=message_data.reply_message_id
        )
        
        if success:
            logger.info(f"Message sent to {message_data.chat_jid}")
            return MessageSendResponse(
                success=True,
                message_id=None  # WhatsApp API doesn't return message ID
            )
        else:
            return MessageSendResponse(
                success=False,
                error="Failed to send message"
            )
    
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return MessageSendResponse(
            success=False,
            error=str(e)
        )

