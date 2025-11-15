"""Configuration management using Pydantic Settings"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application
    app_name: str = "WhatSlang"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./whatslang.db"
    database_echo: bool = False
    
    # WhatsApp API
    whatsapp_base_url: str
    whatsapp_api_user: Optional[str] = None
    whatsapp_api_password: Optional[str] = None
    
    # OpenAI/LLM
    openai_api_key: str
    openai_base_url: Optional[str] = None
    openai_model: str = "gpt-5-mini"
    
    # Bot behavior
    poll_interval_seconds: int = 5
    message_limit_per_poll: int = 20
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    
    # CORS
    cors_origins: list[str] = ["*"]
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.debug or self.reload


# Global settings instance
settings = Settings()

