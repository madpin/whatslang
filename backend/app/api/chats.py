"""Chat API endpoints"""

import logging
from typing import List, Annotated
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Chat, ChatBot, Bot, ChatType as ChatTypeModel
from app.schemas.chat import (
    ChatCreate,
    ChatUpdate,
    ChatResponse,
    ChatListResponse,
    ChatBotAssignmentCreate,
    ChatBotAssignmentUpdate,
    ChatBotAssignmentResponse,
)
from app.core import BotManager
from app.services import WhatsAppClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chats", tags=["chats"])


# Dependency functions - will be injected by FastAPI
def get_bot_manager_dependency() -> BotManager:
    """Placeholder for BotManager dependency - overridden in main.py"""
    raise NotImplementedError("BotManager dependency not initialized")


def get_whatsapp_client_dependency() -> WhatsAppClient:
    """Placeholder for WhatsAppClient dependency - overridden in main.py"""
    raise NotImplementedError("WhatsAppClient dependency not initialized")


@router.get("", response_model=ChatListResponse)
async def list_chats(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """List all chats"""
    # Get total count
    count_stmt = select(func.count(Chat.id))
    count_result = await db.execute(count_stmt)
    total = count_result.scalar_one()
    
    # Get chats
    stmt = (
        select(Chat)
        .offset(skip)
        .limit(limit)
        .order_by(Chat.last_message_at.desc().nulls_last(), Chat.created_at.desc())
    )
    result = await db.execute(stmt)
    chats = result.scalars().all()
    
    return ChatListResponse(
        chats=[ChatResponse.model_validate(chat) for chat in chats],
        total=total
    )


@router.post("", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
async def create_chat(
    chat_data: ChatCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new chat"""
    # Check if chat already exists
    stmt = select(Chat).where(Chat.jid == chat_data.jid)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chat with this JID already exists"
        )
    
    # Create chat
    chat = Chat(
        jid=chat_data.jid,
        name=chat_data.name,
        chat_type=chat_data.chat_type,
        chat_metadata=chat_data.chat_metadata
    )
    
    db.add(chat)
    await db.flush()
    await db.refresh(chat)
    
    logger.info(f"Created chat: {chat.id} ({chat.jid})")
    
    return ChatResponse.model_validate(chat)


@router.get("/{chat_id}", response_model=ChatResponse)
async def get_chat(
    chat_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a chat by ID"""
    stmt = select(Chat).where(Chat.id == chat_id)
    result = await db.execute(stmt)
    chat = result.scalar_one_or_none()
    
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    return ChatResponse.model_validate(chat)


@router.put("/{chat_id}", response_model=ChatResponse)
async def update_chat(
    chat_id: str,
    chat_data: ChatUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a chat"""
    stmt = select(Chat).where(Chat.id == chat_id)
    result = await db.execute(stmt)
    chat = result.scalar_one_or_none()
    
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    # Update fields
    if chat_data.name is not None:
        chat.name = chat_data.name
    if chat_data.chat_type is not None:
        chat.chat_type = chat_data.chat_type
    if chat_data.chat_metadata is not None:
        chat.chat_metadata = chat_data.chat_metadata
    
    await db.flush()
    await db.refresh(chat)
    
    logger.info(f"Updated chat: {chat.id}")
    
    return ChatResponse.model_validate(chat)


@router.post("/{chat_id}/sync", response_model=ChatResponse)
async def sync_chat(
    chat_id: str,
    db: AsyncSession = Depends(get_db),
    whatsapp: Annotated[WhatsAppClient, Depends(get_whatsapp_client_dependency)] = None
):
    """Sync chat information from WhatsApp"""
    stmt = select(Chat).where(Chat.id == chat_id)
    result = await db.execute(stmt)
    chat = result.scalar_one_or_none()
    
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    # Get chat info from WhatsApp API
    chat_info = await whatsapp.get_chat_info(chat.jid)
    
    if chat_info:
        # Update chat with info from WhatsApp
        if "name" in chat_info:
            chat.name = chat_info["name"]
        
        chat.chat_metadata = {**chat.chat_metadata, **chat_info}
        
        await db.flush()
        await db.refresh(chat)
        
        logger.info(f"Synced chat: {chat.id}")
    
    return ChatResponse.model_validate(chat)


@router.post("/sync-all")
async def sync_all_chats(
    db: AsyncSession = Depends(get_db),
    whatsapp: Annotated[WhatsAppClient, Depends(get_whatsapp_client_dependency)] = None
):
    """Sync all chats from WhatsApp"""
    # Fetch all chats from WhatsApp
    whatsapp_chats = await whatsapp.get_all_chats()
    
    created_count = 0
    updated_count = 0
    
    for wa_chat in whatsapp_chats:
        jid = wa_chat.get("jid")
        if not jid:
            continue
        
        name = wa_chat.get("name", "")
        
        # Determine chat type
        chat_type = ChatTypeModel.GROUP if jid.endswith("@g.us") else ChatTypeModel.PRIVATE
        
        # Extract last message timestamp if available
        last_message_at = None
        if "last_message_time" in wa_chat:
            try:
                # Parse ISO 8601 timestamp (e.g., "2025-11-15T20:09:10Z")
                time_str = wa_chat["last_message_time"]
                # Remove 'Z' and parse as UTC
                if time_str.endswith('Z'):
                    time_str = time_str[:-1] + '+00:00'
                dt = datetime.fromisoformat(time_str)
                # Remove timezone info to match database column (TIMESTAMP WITHOUT TIME ZONE)
                last_message_at = dt.replace(tzinfo=None)
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to parse last message time for {jid}: {e}")
        
        # Check if chat exists
        stmt = select(Chat).where(Chat.jid == jid)
        result = await db.execute(stmt)
        existing_chat = result.scalar_one_or_none()
        
        if existing_chat:
            # Update existing chat
            existing_chat.name = name
            if last_message_at:
                existing_chat.last_message_at = last_message_at
            existing_chat.chat_metadata = {**existing_chat.chat_metadata, **wa_chat}
            updated_count += 1
        else:
            # Create new chat
            new_chat = Chat(
                jid=jid,
                name=name,
                chat_type=chat_type,
                chat_metadata=wa_chat,
                last_message_at=last_message_at
            )
            db.add(new_chat)
            created_count += 1
    
    await db.flush()
    
    logger.info(f"Synced chats: {created_count} created, {updated_count} updated")
    
    return {
        "message": "Chats synced successfully",
        "created": created_count,
        "updated": updated_count,
        "total": created_count + updated_count
    }


# Bot assignment endpoints

@router.get("/{chat_id}/bots", response_model=List[ChatBotAssignmentResponse])
async def list_chat_bots(
    chat_id: str,
    db: AsyncSession = Depends(get_db)
):
    """List all bots assigned to a chat"""
    # Verify chat exists
    stmt = select(Chat).where(Chat.id == chat_id)
    result = await db.execute(stmt)
    chat = result.scalar_one_or_none()
    
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    # Get bot assignments
    stmt = (
        select(ChatBot)
        .where(ChatBot.chat_id == chat_id)
        .order_by(ChatBot.priority.asc())
    )
    result = await db.execute(stmt)
    assignments = result.scalars().all()
    
    return [ChatBotAssignmentResponse.model_validate(a) for a in assignments]


@router.post("/{chat_id}/bots", response_model=ChatBotAssignmentResponse, status_code=status.HTTP_201_CREATED)
async def assign_bot_to_chat(
    chat_id: str,
    assignment_data: ChatBotAssignmentCreate,
    db: AsyncSession = Depends(get_db),
    bot_manager: Annotated[BotManager, Depends(get_bot_manager_dependency)] = None
):
    """Assign a bot to a chat"""
    # Verify chat exists
    stmt = select(Chat).where(Chat.id == chat_id)
    result = await db.execute(stmt)
    chat = result.scalar_one_or_none()
    
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    # Verify bot exists
    stmt = select(Bot).where(Bot.id == assignment_data.bot_id)
    result = await db.execute(stmt)
    bot = result.scalar_one_or_none()
    
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot not found"
        )
    
    # Check if assignment already exists
    stmt = select(ChatBot).where(
        ChatBot.chat_id == chat_id,
        ChatBot.bot_id == assignment_data.bot_id
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bot already assigned to this chat"
        )
    
    # Create assignment
    assignment = ChatBot(
        chat_id=chat_id,
        bot_id=assignment_data.bot_id,
        config_override=assignment_data.config_override,
        enabled=assignment_data.enabled,
        priority=assignment_data.priority
    )
    
    db.add(assignment)
    await db.flush()
    await db.refresh(assignment)
    
    # Call on_enable
    await bot_manager.enable_bot_for_chat(assignment_data.bot_id, chat.jid, db)
    
    logger.info(f"Assigned bot {assignment_data.bot_id} to chat {chat_id}")
    
    return ChatBotAssignmentResponse.model_validate(assignment)


@router.put("/{chat_id}/bots/{bot_id}", response_model=ChatBotAssignmentResponse)
async def update_chat_bot_assignment(
    chat_id: str,
    bot_id: str,
    assignment_data: ChatBotAssignmentUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a bot assignment for a chat"""
    stmt = select(ChatBot).where(
        ChatBot.chat_id == chat_id,
        ChatBot.bot_id == bot_id
    )
    result = await db.execute(stmt)
    assignment = result.scalar_one_or_none()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot assignment not found"
        )
    
    # Update fields
    if assignment_data.config_override is not None:
        assignment.config_override = assignment_data.config_override
    if assignment_data.enabled is not None:
        assignment.enabled = assignment_data.enabled
    if assignment_data.priority is not None:
        assignment.priority = assignment_data.priority
    
    await db.flush()
    await db.refresh(assignment)
    
    logger.info(f"Updated bot assignment: bot {bot_id} in chat {chat_id}")
    
    return ChatBotAssignmentResponse.model_validate(assignment)


@router.delete("/{chat_id}/bots/{bot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_bot_from_chat(
    chat_id: str,
    bot_id: str,
    db: AsyncSession = Depends(get_db),
    bot_manager: Annotated[BotManager, Depends(get_bot_manager_dependency)] = None
):
    """Remove a bot from a chat"""
    # Get chat
    stmt = select(Chat).where(Chat.id == chat_id)
    result = await db.execute(stmt)
    chat = result.scalar_one_or_none()
    
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    # Get assignment
    stmt = select(ChatBot).where(
        ChatBot.chat_id == chat_id,
        ChatBot.bot_id == bot_id
    )
    result = await db.execute(stmt)
    assignment = result.scalar_one_or_none()
    
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bot assignment not found"
        )
    
    # Call on_disable
    await bot_manager.disable_bot_for_chat(bot_id, chat.jid, db)
    
    # Delete assignment
    await db.delete(assignment)
    await db.flush()
    
    logger.info(f"Removed bot {bot_id} from chat {chat_id}")

