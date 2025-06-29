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
    
    # WhatsApp MCP Configuration
    mcp_server_url: str = Field(default="http://localhost:3334", env="MCP_SERVER_URL")
    mcp_poll_interval: int = Field(default=3, env="MCP_POLL_INTERVAL")
    
    # Bot Behavior
    bot_name: str = Field(default="AI Assistant", env="BOT_NAME")
    bot_triggers: str = Field(default="/ask,@bot,!ai,>", env="BOT_TRIGGERS")
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