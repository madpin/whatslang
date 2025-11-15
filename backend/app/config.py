"""Configuration management using Pydantic Settings"""

import json

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import Optional, Union


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
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, list[str], None]) -> list[str]:
        """Parse CORS origins from comma-separated string or list"""
        if v is None:
            return []
        
        if isinstance(v, list):
            return [origin.strip() for origin in v if isinstance(origin, str) and origin.strip()]
        
        if isinstance(v, str):
            cleaned = v.strip()
            if not cleaned:
                return []
            
            # Attempt to parse JSON arrays first (e.g. '["https://a.com"]')
            if cleaned.startswith("[") and cleaned.endswith("]"):
                try:
                    parsed = json.loads(cleaned)
                    if isinstance(parsed, list):
                        return [str(origin).strip() for origin in parsed if str(origin).strip()]
                except json.JSONDecodeError:
                    pass
            
            normalized = cleaned.replace("\n", ",").replace(";", ",")
            return [origin.strip() for origin in normalized.split(",") if origin.strip()]
        
        raise ValueError("cors_origins must be provided as a string or list of strings")
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.debug or self.reload


# Global settings instance
settings = Settings()

