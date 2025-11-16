"""FastAPI application entry point"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db, close_db
from app.services import LLMService, WhatsAppClient
from app.core import BotManager, MessageProcessor, MessageScheduler
from app.api import bots, chats, schedules, messages, auth

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
llm_service: LLMService = None
whatsapp_client: WhatsAppClient = None
bot_manager: BotManager = None
message_processor: MessageProcessor = None
message_scheduler: MessageScheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global llm_service, whatsapp_client, bot_manager, message_processor, message_scheduler
    
    logger.info("Starting WhatSlang application...")
    
    # Initialize database
    logger.info("Initializing database...")
    await init_db()
    
    # Initialize services
    logger.info("Initializing services...")
    llm_service = LLMService()
    whatsapp_client = WhatsAppClient()
    
    # Initialize core components
    logger.info("Initializing core components...")
    bot_manager = BotManager(llm_service, whatsapp_client)
    message_processor = MessageProcessor(bot_manager)
    message_scheduler = MessageScheduler(whatsapp_client)
    
    # Start scheduler
    logger.info("Starting scheduler...")
    await message_scheduler.start()
    
    # Start message processor
    logger.info("Starting message processor...")
    await message_processor.start()
    
    # Mark initialization complete (start processing new messages)
    message_processor.mark_initialization_complete()
    
    logger.info("Application started successfully!")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    
    # Stop message processor
    if message_processor:
        await message_processor.stop()
    
    # Stop scheduler
    if message_scheduler:
        await message_scheduler.stop()
    
    # Close database
    await close_db()
    
    logger.info("Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="WhatsApp Bot Platform with multi-bot support",
    lifespan=lifespan,
    debug=settings.debug
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency injection
def get_bot_manager() -> BotManager:
    """Get bot manager instance"""
    return bot_manager


def get_message_processor() -> MessageProcessor:
    """Get message processor instance"""
    return message_processor


def get_message_scheduler() -> MessageScheduler:
    """Get message scheduler instance"""
    return message_scheduler


def get_llm_service() -> LLMService:
    """Get LLM service instance"""
    return llm_service


def get_whatsapp_client() -> WhatsAppClient:
    """Get WhatsApp client instance"""
    return whatsapp_client


# Override default dependencies in routers
app.dependency_overrides[BotManager] = get_bot_manager
app.dependency_overrides[MessageProcessor] = get_message_processor
app.dependency_overrides[MessageScheduler] = get_message_scheduler
app.dependency_overrides[LLMService] = get_llm_service
app.dependency_overrides[WhatsAppClient] = get_whatsapp_client

# Also override the dependency functions used in API routers
from app.api.bots import get_bot_manager_dependency as bots_get_bot_manager
from app.api.chats import get_bot_manager_dependency as chats_get_bot_manager, get_whatsapp_client_dependency as chats_get_whatsapp
from app.api.messages import get_whatsapp_client_dependency as messages_get_whatsapp
from app.api.schedules import get_message_scheduler_dependency as schedules_get_scheduler

app.dependency_overrides[bots_get_bot_manager] = get_bot_manager
app.dependency_overrides[chats_get_bot_manager] = get_bot_manager
app.dependency_overrides[chats_get_whatsapp] = get_whatsapp_client
app.dependency_overrides[messages_get_whatsapp] = get_whatsapp_client
app.dependency_overrides[schedules_get_scheduler] = get_message_scheduler


# Include routers
app.include_router(auth.router)
app.include_router(bots.router)
app.include_router(chats.router)
app.include_router(schedules.router)
app.include_router(messages.router)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower()
    )

