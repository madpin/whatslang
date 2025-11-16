"""Configuration management using Pydantic Settings"""

import json

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AliasChoices, Field, field_validator
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
    whatsapp_base_url: str = Field(
        default="",
        validation_alias=AliasChoices("whatsapp_base_url", "WHATSAPP_BASE_URL", "whatsapp_api_url", "WHATSAPP_API_URL"),
    )
    whatsapp_api_user: Optional[str] = None
    whatsapp_api_password: Optional[str] = None
    
    # OpenAI/LLM
    openai_api_key: str = ""
    openai_base_url: Optional[str] = None
    openai_model: str = "gpt-5-mini"
    
    # Bot behavior
    poll_interval_seconds: int = 5
    message_limit_per_poll: int = 20
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    
    # Authentication / JWT
    jwt_secret_key: str = Field(
        default="change-this-secret-key-in-production",
        validation_alias=AliasChoices("jwt_secret_key", "JWT_SECRET_KEY", "secret_key", "SECRET_KEY"),
    )
    jwt_algorithm: str = "HS256"
    access_token_expire_days: int = 7
    
    # Default admin user (created on first migration)
    default_admin_email: str = Field(
        default="admin@example.com",
        validation_alias=AliasChoices("default_admin_email", "DEFAULT_ADMIN_EMAIL", "admin_email", "ADMIN_EMAIL"),
    )
    default_admin_password: str = Field(
        default="admin123",
        validation_alias=AliasChoices("default_admin_password", "DEFAULT_ADMIN_PASSWORD", "admin_password", "ADMIN_PASSWORD"),
    )
    
    # CORS
    cors_origins_raw: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("cors_origins", "CORS_ORIGINS"),
    )
    
    @field_validator("cors_origins_raw", mode="before")
    @classmethod
    def normalize_cors_input(cls, v: Union[str, list[str], None]) -> Union[str, list[str], None]:
        """Ensure CORS env inputs are consistently formatted"""
        if isinstance(v, (list, tuple)):
            return json.dumps([str(origin).strip() for origin in v if str(origin).strip()])
        return v
    
    @staticmethod
    def parse_cors_origins(v: Union[str, list[str], None]) -> list[str]:
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
    def cors_origins(self) -> list[str]:
        """CORS origins parsed from the raw env value with safe fallback"""
        parsed = self.parse_cors_origins(self.cors_origins_raw)
        return parsed if parsed else ["*"]
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.debug or self.reload


# Global settings instance
settings = Settings()

