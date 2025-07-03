"""
Configuration settings for WhatsApp AI Assistant
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List
import os

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Core API Keys
    gemini_api_key: str = Field(..., env="GEMINI_API_KEY")
    
    # WhatsApp Bridge (Go) configuration – this is the REST server the agent
    # talks to for sending/receiving WhatsApp messages.  Keep the old
    # MCP_SERVER_URL env var for backward-compatibility but prefer the new
    # BRIDGE_SERVER_URL if provided.
    bridge_server_url: str = Field(
        default=os.getenv("MCP_SERVER_URL", "http://localhost:3334"),
        env="BRIDGE_SERVER_URL",
    )
    
    # Legacy – keep for backward compatibility (will be removed later).
    # If MCP_SERVER_URL env var is present we honour it; otherwise we fall back
    # to the new bridge_server_url so existing references don't break.
    mcp_server_url: str = Field(
        default_factory=lambda: os.getenv("MCP_SERVER_URL", os.getenv("BRIDGE_SERVER_URL", "http://localhost:3334")),
        env="MCP_SERVER_URL",
    )
    
    # WhatsApp MCP Configuration
    mcp_poll_interval: int = Field(default=3, env="MCP_POLL_INTERVAL")
    
    # Bot Behavior
    bot_name: str = Field(default="AI Assistant", env="BOT_NAME")
    bot_triggers: str = Field(default="!ask,@bot,@ai,>", env="BOT_TRIGGERS")
    authorized_numbers: str = Field(default="", env="AUTHORIZED_NUMBERS")
    enable_group_chats: bool = Field(default=True, env="ENABLE_GROUP_CHATS")
    enable_personal_chats: bool = Field(default=True, env="ENABLE_PERSONAL_CHATS")
    
    # Agent Settings
    max_response_length: int = Field(default=500, env="MAX_RESPONSE_LENGTH")
    agent_temperature: float = Field(default=0.7, env="AGENT_TEMPERATURE")
    agent_model: str = Field(default="gemini-pro", env="AGENT_MODEL")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    enable_console_logs: bool = Field(default=True, env="ENABLE_CONSOLE_LOGS")
    enable_file_logs: bool = Field(default=True, env="ENABLE_FILE_LOGS")
    
    # Dashboard
    dashboard_port: int = Field(default=8501, env="DASHBOARD_PORT")
    dashboard_host: str = Field(default="localhost", env="DASHBOARD_HOST")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    @property
    def trigger_list(self) -> List[str]:
        """Parse trigger string into list"""
        return [t.strip() for t in self.bot_triggers.split(",") if t.strip()]
    
    @property
    def authorized_number_list(self) -> List[str]:
        """Parse authorized numbers into list"""
        if not self.authorized_numbers:
            return []
        return [n.strip() for n in self.authorized_numbers.split(",") if n.strip()]

# Global settings instance
settings = Settings() 