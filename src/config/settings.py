"""Configuration management for Movidesk Automation."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional, List


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
    movidesk_agent_email: Optional[str] = Field(
        default=None, 
        description="Single agent email (legacy, use AGENTS for multi-agent)"
    )
    
    # Multi-Agent Support (v2.0)
    agents: Optional[str] = Field(
        default=None,
        description="Multiple agent emails separated by semicolon (e.g., 'email1@;email2@;email3@')"
    )
    
    @property
    def agent_emails_list(self) -> List[str]:
        """Get list of agent emails supporting both single and multi-agent modes.
        
        Returns:
            List of agent email addresses. In single-agent mode, returns list with one email.
            In multi-agent mode, returns list parsed from AGENTS variable.
        """
        # Multi-agent mode (priority)
        if self.agents:
            emails = [email.strip() for email in self.agents.split(';') if email.strip()]
            if emails:
                return emails
        
        # Fallback to single-agent mode (backward compatibility)
        if self.movidesk_agent_email:
            return [self.movidesk_agent_email]
        
        raise ValueError(
            "No agent emails configured. Set either AGENTS (multi-agent) or "
            "MOVIDESK_AGENT_EMAIL (single-agent) in .env file"
        )
    
    @property
    def is_multi_agent_mode(self) -> bool:
        """Check if running in multi-agent mode."""
        return bool(self.agents and len(self.agent_emails_list) > 1)
    
    # Groq API
    groq_api_key: str = Field(..., description="Groq API key for AI summarization")
    
    # Email Configuration
    email_enabled: bool = Field(default=True)
    email_smtp_server: str = Field(default="smtp.gmail.com")
    email_smtp_port: int = Field(default=587)
    email_from: str = Field(...)
    email_password: str = Field(...)
    email_to: str = Field(...)
    sendgrid_api_key: Optional[str] = Field(default=None, description="SendGrid API Key for email sending")
    
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
