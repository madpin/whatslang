"""FastAPI application for bot management."""

import json
import logging
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import yaml
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from api.bot_manager import BotManager
from api.models import (
    BotStatus, BotLogsResponse, ErrorResponse, SuccessResponse,
    Chat, ChatWithBots, BotAssignment, AssignmentUpdate, AddChatRequest
)
from core.whatsapp_client import WhatsAppClient
from core.llm_service import LLMService
from core.database import MessageDatabase

# Load environment variables from .env file
load_dotenv()

# Configure structured logging
class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
            
        return json.dumps(log_data)


def setup_logging():
    """Configure application logging."""
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    environment = os.environ.get("ENVIRONMENT", "development")
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    
    # Use JSON formatter in production, simple formatter in development
    if environment == "production":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    return root_logger


logger = setup_logging()

# Load configuration with environment variable priority
def load_config() -> Dict[str, Any]:
    """Load configuration from config.yaml with environment variable overrides."""
    config = {}
    config_path = Path(__file__).parent.parent / "config.yaml"
    
    # Try to load config.yaml if it exists (optional in production)
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f) or {}
            logger.info("Loaded configuration from config.yaml")
        except Exception as e:
            logger.warning(f"Failed to load config.yaml: {e}. Using environment variables only.")
    else:
        logger.info("No config.yaml found. Using environment variables only.")
    
    return config


config = load_config()

# Extract configuration values with environment variable overrides
whatsapp_config = config.get('whatsapp', {})
openai_config = config.get('openai', {})
bot_settings = config.get('bot_settings', {})

# Required configuration
WHATSAPP_BASE_URL = os.environ.get('WHATSAPP_BASE_URL', whatsapp_config.get('base_url'))
WHATSAPP_API_USER = os.environ.get('WHATSAPP_API_USER', whatsapp_config.get('api_user'))
WHATSAPP_API_PASSWORD = os.environ.get('WHATSAPP_API_PASSWORD', whatsapp_config.get('api_password'))
DEVICE_ID = os.environ.get('DEVICE_ID', whatsapp_config.get('device_id'))

# Legacy support: CHAT_JID is now optional and only used for backward compatibility
CHAT_JID = os.environ.get('CHAT_JID', whatsapp_config.get('chat_jid'))

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', openai_config.get('api_key'))
OPENAI_BASE_URL = os.environ.get('OPENAI_BASE_URL', openai_config.get('base_url', 'https://api.openai.com/v1'))
OPENAI_MODEL = os.environ.get('OPENAI_MODEL', openai_config.get('model', 'gpt-4'))

# Optional configuration
POLL_INTERVAL = int(os.environ.get('POLL_INTERVAL', bot_settings.get('poll_interval', 5)))
DB_PATH = Path(os.environ.get('DB_PATH', bot_settings.get('db_path', 'messages.db')))
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')

# Validate required configuration
required_vars = {
    'WHATSAPP_BASE_URL': WHATSAPP_BASE_URL,
    'WHATSAPP_API_USER': WHATSAPP_API_USER,
    'WHATSAPP_API_PASSWORD': WHATSAPP_API_PASSWORD,
    'DEVICE_ID': DEVICE_ID,
    'OPENAI_API_KEY': OPENAI_API_KEY,
}

missing_vars = [key for key, value in required_vars.items() if not value]
if missing_vars:
    error_msg = f"Missing required configuration: {', '.join(missing_vars)}"
    logger.error(error_msg)
    raise RuntimeError(error_msg)

# Global service instances
whatsapp_client = None
llm_service = None
database = None
bot_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown."""
    global whatsapp_client, llm_service, database, bot_manager
    
    # Startup
    logger.info("Starting WhatsApp Bot Service...")
    logger.info(f"Environment: {ENVIRONMENT}")
    logger.info(f"Database path: {DB_PATH}")
    
    try:
        # Initialize core services
        whatsapp_client = WhatsAppClient(
            base_url=WHATSAPP_BASE_URL,
            username=WHATSAPP_API_USER,
            password=WHATSAPP_API_PASSWORD
        )
        logger.info("WhatsApp client initialized")
        
        llm_service = LLMService(
            api_key=OPENAI_API_KEY,
            model=OPENAI_MODEL,
            base_url=OPENAI_BASE_URL
        )
        logger.info(f"LLM service initialized (model: {OPENAI_MODEL})")
        
        database = MessageDatabase(DB_PATH)
        logger.info("Database initialized")
        
        # Initialize bot manager
        bot_manager = BotManager(
            whatsapp_client=whatsapp_client,
            llm_service=llm_service,
            database=database,
            bot_device_id=DEVICE_ID,
            poll_interval=POLL_INTERVAL
        )
        logger.info(f"Bot manager initialized (found {len(bot_manager.bot_classes)} bots)")
        
        # If legacy CHAT_JID is provided, add it to database
        if CHAT_JID:
            logger.info(f"Legacy CHAT_JID found: {CHAT_JID}")
            database.add_chat(
                chat_jid=CHAT_JID,
                chat_name="Default Chat (from config)",
                is_manual=True
            )
        
        # Start enabled bots from database
        bot_manager.start_enabled_bots()
        
        logger.info("✅ Application startup complete")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}", exc_info=True)
        raise
    finally:
        # Shutdown
        logger.info("Shutting down WhatsApp Bot Service...")
        
        if bot_manager:
            logger.info("Stopping all running bots...")
            bot_manager.stop_all()
        
        logger.info("✅ Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="WhatsApp Bot Service",
    description="A modular WhatsApp bot service with web dashboard for managing multiple concurrent bots",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs" if ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if ENVIRONMENT != "production" else None,
)

# Configure CORS
allowed_origins = os.environ.get("ALLOWED_ORIGINS", "*")
if allowed_origins == "*":
    origins = ["*"]
else:
    origins = [origin.strip() for origin in allowed_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests."""
    start_time = datetime.now()
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration = (datetime.now() - start_time).total_seconds()
    
    # Log request
    logger.info(
        f"{request.method} {request.url.path} - Status: {response.status_code} - Duration: {duration:.3f}s",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration": duration,
        }
    )
    
    return response

# Mount static files for frontend
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path), html=True), name="static")


@app.get("/")
async def root():
    """Root endpoint - redirect to frontend dashboard."""
    return RedirectResponse(url="/static/index.html")


@app.get("/api")
async def api_info():
    """API information endpoint."""
    return {
        "service": "WhatsApp Bot Service",
        "version": "2.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "ready": "/ready",
            "bots": "/bots",
            "frontend": "/static/index.html",
            "docs": "/docs" if ENVIRONMENT != "production" else None,
        }
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint for container orchestration.
    Returns 200 if the service is running (liveness probe).
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "2.0.0",
    }


@app.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint for container orchestration.
    Returns 200 if the service is ready to accept requests (readiness probe).
    """
    try:
        # Check if core services are initialized
        if not all([whatsapp_client, llm_service, database, bot_manager]):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Core services not initialized"
            )
        
        return {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "services": {
                "whatsapp": "connected",
                "llm": "connected",
                "database": "connected",
                "bot_manager": "initialized",
            },
            "bots": {
                "available": len(bot_manager.bot_classes),
                "running": len(bot_manager.bots),
            }
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service not ready: {str(e)}"
        )


@app.get("/bots", response_model=List[BotStatus])
async def list_bots():
    """List all running bot instances."""
    try:
        statuses = bot_manager.get_all_bot_statuses()
        return statuses
    except Exception as e:
        logger.error(f"Error listing bots: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ===== Chat Management Endpoints =====

@app.get("/chats", response_model=List[ChatWithBots])
async def list_chats():
    """List all chats with their bot status."""
    try:
        chats = database.list_chats()
        result = []
        
        for chat in chats:
            chat_jid = chat['chat_jid']
            bot_statuses = bot_manager.get_bot_statuses_for_chat(chat_jid)
            
            result.append(ChatWithBots(
                chat_jid=chat['chat_jid'],
                chat_name=chat['chat_name'],
                is_manual=bool(chat['is_manual']),
                last_synced=chat.get('last_synced'),
                added_at=chat['added_at'],
                bots=bot_statuses
            ))
        
        return result
    except Exception as e:
        logger.error(f"Error listing chats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chats/sync", response_model=SuccessResponse)
async def sync_chats():
    """Sync chats from WhatsApp API."""
    try:
        # Fetch all groups with proper names from /user/my/groups
        logger.info("=" * 60)
        logger.info("STARTING CHAT SYNC")
        logger.info("=" * 60)
        logger.info("Step 1: Fetching groups from /user/my/groups")
        groups = whatsapp_client.get_groups()
        logger.info(f"✓ Retrieved {len(groups)} groups from API")
        
        # Also fetch individual chats from /chats endpoint
        logger.info("Step 2: Fetching individual chats from /chats")
        all_chats = whatsapp_client.get_chats()
        logger.info(f"✓ Retrieved {len(all_chats)} chats from API")
        
        groups_synced = 0
        chats_synced = 0
        
        # First, sync all groups (which have proper names from /user/my/groups)
        logger.info(f"Step 3: Processing {len(groups)} groups...")
        for i, group in enumerate(groups, 1):
            # Extract group JID and name
            # API returns: {"JID": "120363419538094902@g.us", "Name": "Group Name", ...}
            # Handle both uppercase and lowercase field names
            chat_jid = (
                group.get('JID') or group.get('jid') or 
                group.get('id') or group.get('ID')
            )
            chat_name = (
                group.get('Name') or group.get('name') or 
                group.get('Subject') or group.get('subject') or 
                f"Group {chat_jid}"
            )
            
            if chat_jid:
                logger.info(f"  [{i}/{len(groups)}] Group JID: {chat_jid}")
                logger.info(f"  [{i}/{len(groups)}] Group Name: {chat_name}")
                
                existing = database.get_chat(chat_jid)
                if existing:
                    database.update_chat(
                        chat_jid=chat_jid,
                        chat_name=chat_name,
                        last_synced=datetime.utcnow().isoformat()
                    )
                    logger.info(f"  [{i}/{len(groups)}] ✓ Updated group: {chat_name}")
                else:
                    database.add_chat(
                        chat_jid=chat_jid,
                        chat_name=chat_name,
                        is_manual=False
                    )
                    logger.info(f"  [{i}/{len(groups)}] ✓ Added new group: {chat_name}")
                groups_synced += 1
            else:
                logger.warning(f"  [{i}/{len(groups)}] ✗ Skipped group with no JID: {group}")
        
        # Now sync individual chats (non-groups) from /chats
        logger.info(f"Step 4: Processing {len(all_chats)} individual chats...")
        for i, chat in enumerate(all_chats, 1):
            chat_jid = chat.get('jid')
            
            # Skip if it's a group (already handled above)
            if chat_jid and '@g.us' in chat_jid:
                logger.debug(f"  [{i}/{len(all_chats)}] Skipping group (already synced): {chat_jid}")
                continue
            
            chat_name = chat.get('name') or f"Chat {chat_jid}"
            
            if chat_jid:
                logger.info(f"  [{i}/{len(all_chats)}] Chat JID: {chat_jid}")
                logger.info(f"  [{i}/{len(all_chats)}] Chat Name: {chat_name}")
                
                existing = database.get_chat(chat_jid)
                if existing:
                    database.update_chat(
                        chat_jid=chat_jid,
                        chat_name=chat_name,
                        last_synced=datetime.utcnow().isoformat()
                    )
                    logger.info(f"  [{i}/{len(all_chats)}] ✓ Updated chat: {chat_name}")
                else:
                    database.add_chat(
                        chat_jid=chat_jid,
                        chat_name=chat_name,
                        is_manual=False
                    )
                    logger.info(f"  [{i}/{len(all_chats)}] ✓ Added new chat: {chat_name}")
                chats_synced += 1
        
        logger.info("=" * 60)
        logger.info(f"SYNC COMPLETE: {groups_synced} groups, {chats_synced} individual chats")
        logger.info("=" * 60)
        
        return SuccessResponse(
            message=f"Synced {groups_synced} group(s) and {chats_synced} individual chat(s) from WhatsApp"
        )
    except Exception as e:
        logger.error(f"Error syncing chats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chats", response_model=Chat)
async def add_chat(request: AddChatRequest):
    """Manually add a chat. If no name provided, attempts to fetch from WhatsApp API."""
    try:
        chat_name = request.chat_name
        
        # If no name provided, try to fetch from WhatsApp API
        if not chat_name:
            logger.info(f"No name provided for {request.chat_jid}, attempting to fetch from WhatsApp API")
            chat_info = whatsapp_client.get_chat_info(request.chat_jid)
            
            if chat_info:
                chat_name = (
                    chat_info.get('name') or 
                    chat_info.get('subject') or 
                    chat_info.get('title') or 
                    f"Chat {request.chat_jid}"
                )
                logger.info(f"Fetched name from WhatsApp: {chat_name}")
            else:
                chat_name = f"Chat {request.chat_jid}"
                logger.warning(f"Could not fetch name from WhatsApp, using default: {chat_name}")
        
        success = database.add_chat(
            chat_jid=request.chat_jid,
            chat_name=chat_name,
            is_manual=True
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Chat already exists or failed to add")
        
        chat = database.get_chat(request.chat_jid)
        if not chat:
            raise HTTPException(status_code=500, detail="Failed to retrieve added chat")
        
        return Chat(**chat)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/chats/{chat_jid}", response_model=ChatWithBots)
async def get_chat(chat_jid: str):
    """Get a specific chat with bot status."""
    try:
        chat = database.get_chat(chat_jid)
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        
        bot_statuses = bot_manager.get_bot_statuses_for_chat(chat_jid)
        
        return ChatWithBots(
            chat_jid=chat['chat_jid'],
            chat_name=chat['chat_name'],
            is_manual=bool(chat['is_manual']),
            last_synced=chat.get('last_synced'),
            added_at=chat['added_at'],
            bots=bot_statuses
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/chats/{chat_jid}/messages")
async def get_chat_messages(chat_jid: str, limit: int = 20):
    """Get recent messages from a chat."""
    try:
        messages = whatsapp_client.get_messages(chat_jid, limit=limit)
        return {
            "code": "SUCCESS",
            "message": f"Fetched {len(messages)} messages",
            "results": {
                "chat_jid": chat_jid,
                "messages": messages,
                "count": len(messages)
            }
        }
    except Exception as e:
        logger.error(f"Error fetching messages for chat {chat_jid}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/chats/{chat_jid}", response_model=SuccessResponse)
async def delete_chat(chat_jid: str):
    """Delete a chat and stop all its bots."""
    try:
        # Stop all running bots for this chat
        for bot_name in bot_manager.get_available_bots():
            bot_key = (bot_name, chat_jid)
            if bot_key in bot_manager.bots:
                bot_manager.stop_bot(bot_name, chat_jid)
        
        # Delete from database
        success = database.delete_chat(chat_jid)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to delete chat")
        
        return SuccessResponse(message=f"Chat {chat_jid} deleted")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ===== Assignment Management Endpoints =====

@app.get("/chats/{chat_jid}/bots", response_model=List[BotStatus])
async def list_bots_for_chat(chat_jid: str):
    """List all bots with their enabled status for a specific chat."""
    try:
        statuses = bot_manager.get_bot_statuses_for_chat(chat_jid)
        return statuses
    except Exception as e:
        logger.error(f"Error listing bots for chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/chats/{chat_jid}/bots/{bot_name}", response_model=SuccessResponse)
async def update_bot_assignment(chat_jid: str, bot_name: str, update: AssignmentUpdate):
    """Enable or disable a bot for a specific chat."""
    try:
        # Check if bot exists
        if bot_name not in bot_manager.bot_classes:
            raise HTTPException(status_code=404, detail=f"Bot not found: {bot_name}")
        
        # Check if chat exists
        chat = database.get_chat(chat_jid)
        if not chat:
            raise HTTPException(status_code=404, detail=f"Chat not found: {chat_jid}")
        
        # Update assignment
        success = database.set_bot_assignment(bot_name, chat_jid, update.enabled)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to update assignment")
        
        return SuccessResponse(
            message=f"Bot {bot_name} {'enabled' if update.enabled else 'disabled'} for chat {chat_jid}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating bot assignment: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/bots/{bot_name}/chats", response_model=List[Chat])
async def list_chats_for_bot(bot_name: str):
    """List all chats with enabled status for a specific bot."""
    try:
        if bot_name not in bot_manager.bot_classes:
            raise HTTPException(status_code=404, detail=f"Bot not found: {bot_name}")
        
        enabled_chat_jids = database.get_enabled_chats_for_bot(bot_name)
        chats = []
        
        for chat_jid in enabled_chat_jids:
            chat = database.get_chat(chat_jid)
            if chat:
                chats.append(Chat(**chat))
        
        return chats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing chats for bot: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ===== Bot Control Endpoints (Updated for Multi-Chat) =====


@app.get("/bots/{bot_name}/status")
async def get_bot_status_legacy(bot_name: str, chat_jid: str):
    """Get status of a specific bot for a chat (requires chat_jid query param)."""
    try:
        status = bot_manager.get_bot_status(bot_name, chat_jid)
        if status is None:
            raise HTTPException(status_code=404, detail=f"Bot not found: {bot_name}")
        return status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting bot status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/bots/{bot_name}/start", response_model=SuccessResponse)
async def start_bot(bot_name: str, chat_jid: str):
    """Start a bot for a specific chat (requires chat_jid query param)."""
    try:
        success = bot_manager.start_bot(bot_name, chat_jid)
        if not success:
            raise HTTPException(status_code=400, detail=f"Failed to start bot: {bot_name}")
        return SuccessResponse(message=f"Bot {bot_name} started for chat {chat_jid}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting bot: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/bots/{bot_name}/stop", response_model=SuccessResponse)
async def stop_bot(bot_name: str, chat_jid: str):
    """Stop a bot for a specific chat (requires chat_jid query param)."""
    try:
        success = bot_manager.stop_bot(bot_name, chat_jid)
        if not success:
            raise HTTPException(status_code=400, detail=f"Failed to stop bot: {bot_name}")
        return SuccessResponse(message=f"Bot {bot_name} stopped for chat {chat_jid}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping bot: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/bots/{bot_name}/logs", response_model=BotLogsResponse)
async def get_bot_logs(bot_name: str, chat_jid: str, limit: int = 50):
    """Get recent logs for a bot instance (requires chat_jid query param)."""
    try:
        logs = bot_manager.get_bot_logs(bot_name, chat_jid, limit)
        return BotLogsResponse(bot_name=bot_name, chat_jid=chat_jid, logs=logs)
    except Exception as e:
        logger.error(f"Error getting bot logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    
    logger.info(f"Starting server on {host}:{port}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_config=None,  # Use our custom logging configuration
        access_log=False,  # We're handling access logs via middleware
    )

