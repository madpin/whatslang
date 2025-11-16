"""Initialize default admin user if no users exist"""

import asyncio
import logging
from sqlalchemy import select, func

from app.database import get_db, init_db
from app.models.user import User
from app.core.security import get_password_hash
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_default_user():
    """Create default admin user if no users exist"""
    await init_db()
    
    async for session in get_db():
        try:
            # Check if any users exist
            result = await session.execute(select(func.count(User.id)))
            user_count = result.scalar_one()
            
            if user_count == 0:
                logger.info("No users found, creating default admin user...")
                
                # Create default admin user
                admin_user = User(
                    email=settings.default_admin_email,
                    username="admin",
                    hashed_password=get_password_hash(settings.default_admin_password),
                    is_active=True
                )
                
                session.add(admin_user)
                await session.commit()
                
                logger.info(f"✅ Default admin user created: {settings.default_admin_email}")
                logger.info(f"   Password: {settings.default_admin_password}")
                logger.info("   ⚠️  CHANGE THIS PASSWORD IMMEDIATELY IN PRODUCTION!")
            else:
                logger.info(f"Users already exist (count: {user_count}), skipping default user creation")
        
        except Exception as e:
            logger.error(f"Error initializing default user: {e}")
            raise
        finally:
            break  # Only need one session


if __name__ == "__main__":
    asyncio.run(init_default_user())

