"""Configuration management for Movidesk Automation."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Movidesk API
    movidesk_token: str = Field(..., description="Movidesk API token")
    movidesk_base_url: str = Field(
        default="https://api.movidesk.com/public/v1",
        description="Movidesk API base URL"
    )
    movidesk_agent_email: str = Field(..., description="Agent email for filtering tickets")
    
    # Groq API
    groq_api_key: str = Field(..., description="Groq API key for AI summarization")
    
    # Email Configuration
    email_enabled: bool = Field(default=True)
    email_smtp_server: str = Field(default="smtp.gmail.com")
    email_smtp_port: int = Field(default=587)
    email_from: str = Field(...)
    email_password: str = Field(...)
    email_to: str = Field(...)
    
    # Logging
    log_level: str = Field(default="INFO")
    
    
# Global settings instance
settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create settings instance."""
    global settings
    if settings is None:
        settings = Settings()
    return settings
