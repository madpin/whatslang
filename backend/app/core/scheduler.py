"""Message scheduler with APScheduler"""

import logging
from datetime import datetime
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from sqlalchemy import select
from pytz import timezone as pytz_timezone

from app.config import settings
from app.models import ScheduledMessage, ScheduleType, Chat
from app.services import WhatsAppClient
from app.database import get_db_context

logger = logging.getLogger(__name__)


class MessageScheduler:
    """Scheduler for sending messages at specific times"""
    
    def __init__(self, whatsapp_client: WhatsAppClient):
        """
        Initialize message scheduler.
        
        Args:
            whatsapp_client: WhatsApp client instance
        """
        self.whatsapp = whatsapp_client
        self.scheduler: Optional[AsyncIOScheduler] = None
    
    async def start(self):
        """Start the scheduler and load jobs from database"""
        if self.scheduler:
            logger.warning("Scheduler already running")
            return
        
        # Prepare database URL for APScheduler (needs sync driver)
        db_url = settings.database_url
        # APScheduler needs sync drivers, not async
        if "postgresql+asyncpg://" in db_url:
            db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
        elif "sqlite+aiosqlite://" in db_url:
            db_url = db_url.replace("sqlite+aiosqlite://", "sqlite://")
        
        # Configure job store
        jobstores = {
            'default': SQLAlchemyJobStore(url=db_url)
        }
        
        # Create scheduler
        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            timezone=pytz_timezone('UTC')
        )
        
        # Start scheduler
        self.scheduler.start()
        logger.info("Scheduler started")
        
        # Load jobs from database
        await self._load_jobs_from_db()
    
    async def stop(self):
        """Stop the scheduler"""
        if self.scheduler:
            self.scheduler.shutdown(wait=False)
            self.scheduler = None
            logger.info("Scheduler stopped")
    
    async def _load_jobs_from_db(self):
        """Load scheduled messages from database and create jobs"""
        async with get_db_context() as db:
            # Get all enabled scheduled messages
            stmt = select(ScheduledMessage).where(ScheduledMessage.enabled == True)
            result = await db.execute(stmt)
            schedules = result.scalars().all()
            
            for schedule in schedules:
                try:
                    await self._add_job(schedule)
                    logger.info(f"Loaded schedule {schedule.id} from database")
                except Exception as e:
                    logger.error(f"Error loading schedule {schedule.id}: {e}")
    
    async def _add_job(self, schedule: ScheduledMessage):
        """
        Add a job to the scheduler.
        
        Args:
            schedule: ScheduledMessage model
        """
        if not self.scheduler:
            logger.error("Scheduler not initialized")
            return
        
        # Parse schedule expression
        tz = pytz_timezone(schedule.timezone)
        
        if schedule.schedule_type == ScheduleType.ONCE:
            # One-time schedule
            run_date = datetime.fromisoformat(schedule.schedule_expression)
            trigger = DateTrigger(run_date=run_date, timezone=tz)
        elif schedule.schedule_type == ScheduleType.CRON:
            # Cron schedule
            trigger = CronTrigger.from_crontab(schedule.schedule_expression, timezone=tz)
        else:
            logger.error(f"Unknown schedule type: {schedule.schedule_type}")
            return
        
        # Get chat JID
        async with get_db_context() as db:
            stmt = select(Chat).where(Chat.id == schedule.chat_id)
            result = await db.execute(stmt)
            chat = result.scalar_one_or_none()
            
            if not chat:
                logger.error(f"Chat not found for schedule {schedule.id}")
                return
            
            chat_jid = chat.jid
        
        # Add job
        self.scheduler.add_job(
            func=send_scheduled_message,
            trigger=trigger,
            id=schedule.id,
            args=[schedule.id, chat_jid, schedule.message, self.whatsapp],
            replace_existing=True,
            name=f"Schedule {schedule.id}"
        )
        
        logger.info(f"Added job for schedule {schedule.id}")
    
async def send_scheduled_message(
    schedule_id: str,
    chat_jid: str,
    message: str,
    whatsapp_client: WhatsAppClient
):
    """
    Execute scheduled message send.

    Args:
        schedule_id: Schedule ID
        chat_jid: WhatsApp JID
        message: Message to send
        whatsapp_client: WhatsApp client instance
    """
    logger.info(f"Executing scheduled message {schedule_id} to {chat_jid}")

    try:
        # Send message
        success = await whatsapp_client.send_message(
            phone=chat_jid,
            message=message
        )

        if success:
            logger.info(f"Scheduled message {schedule_id} sent successfully")
        else:
            logger.error(f"Failed to send scheduled message {schedule_id}")

        # Update last_run_at in database
        async with get_db_context() as db:
            stmt = select(ScheduledMessage).where(ScheduledMessage.id == schedule_id)
            result = await db.execute(stmt)
            schedule = result.scalar_one_or_none()

            if schedule:
                schedule.last_run_at = datetime.utcnow()

                # If it's a one-time schedule, disable it
                if schedule.schedule_type == ScheduleType.ONCE:
                    schedule.enabled = False
                    logger.info(f"Disabled one-time schedule {schedule_id}")

                await db.flush()

    except Exception as e:
        logger.error(f"Error executing scheduled message {schedule_id}: {e}", exc_info=True)
    
    async def schedule_message(
        self,
        schedule_id: str,
        chat_id: str,
        message: str,
        schedule_type: ScheduleType,
        schedule_expression: str,
        timezone: str = "UTC"
    ):
        """
        Schedule a new message.
        
        Args:
            schedule_id: Schedule ID (from database)
            chat_id: Chat ID
            message: Message to send
            schedule_type: Type of schedule (once or cron)
            schedule_expression: ISO datetime or cron expression
            timezone: Timezone for the schedule
        """
        # Get schedule from database
        async with get_db_context() as db:
            stmt = select(ScheduledMessage).where(ScheduledMessage.id == schedule_id)
            result = await db.execute(stmt)
            schedule = result.scalar_one_or_none()
            
            if not schedule:
                logger.error(f"Schedule not found: {schedule_id}")
                return
            
            # Add job to scheduler
            await self._add_job(schedule)
    
    async def update_schedule(self, schedule_id: str):
        """
        Update an existing schedule.
        
        Args:
            schedule_id: Schedule ID
        """
        # Remove old job
        if self.scheduler and self.scheduler.get_job(schedule_id):
            self.scheduler.remove_job(schedule_id)
        
        # Get updated schedule from database
        async with get_db_context() as db:
            stmt = select(ScheduledMessage).where(ScheduledMessage.id == schedule_id)
            result = await db.execute(stmt)
            schedule = result.scalar_one_or_none()
            
            if not schedule:
                logger.error(f"Schedule not found: {schedule_id}")
                return
            
            # Add updated job
            if schedule.enabled:
                await self._add_job(schedule)
    
    async def remove_schedule(self, schedule_id: str):
        """
        Remove a schedule.
        
        Args:
            schedule_id: Schedule ID
        """
        if self.scheduler and self.scheduler.get_job(schedule_id):
            self.scheduler.remove_job(schedule_id)
            logger.info(f"Removed schedule {schedule_id}")
    
    async def trigger_schedule(self, schedule_id: str):
        """
        Manually trigger a schedule to run immediately.
        
        Args:
            schedule_id: Schedule ID
        """
        async with get_db_context() as db:
            stmt = select(ScheduledMessage).where(ScheduledMessage.id == schedule_id)
            result = await db.execute(stmt)
            schedule = result.scalar_one_or_none()
            
            if not schedule:
                logger.error(f"Schedule not found: {schedule_id}")
                return
            
            # Get chat JID
            stmt = select(Chat).where(Chat.id == schedule.chat_id)
            result = await db.execute(stmt)
            chat = result.scalar_one_or_none()
            
            if not chat:
                logger.error(f"Chat not found for schedule {schedule_id}")
                return
            
            # Execute immediately
            await send_scheduled_message(schedule_id, chat.jid, schedule.message, self.whatsapp)

