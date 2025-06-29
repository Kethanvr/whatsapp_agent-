"""
WhatsApp MCP Client - Handles communication with whatsapp-mcp server
"""
import requests
import time
from typing import List, Dict, Optional, Any
from loguru import logger
from dataclasses import dataclass
from config.settings import settings

@dataclass
class ChatInfo:
    """WhatsApp chat information"""
    id: str
    name: str
    is_group: bool
    participant_count: Optional[int] = None

@dataclass
class Message:
    """WhatsApp message structure"""
    id: str
    chat_id: str
    sender: str
    text: str
    timestamp: str
    is_from_me: bool = False
    message_type: str = "text"

class WhatsAppMCPClient:
    """Client for communicating with whatsapp-mcp server"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or settings.mcp_server_url
        self.session = requests.Session()
        self._last_message_ids = {}  # Track last seen message per chat
        
    def health_check(self) -> bool:
        """Check if MCP server is running"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def get_chats(self) -> List[ChatInfo]:
        """Get all available chats"""
        try:
            response = self.session.get(f"{self.base_url}/chats")
            response.raise_for_status()
            
            chats = []
            for chat_data in response.json():
                chats.append(ChatInfo(
                    id=chat_data["id"],
                    name=chat_data.get("name", "Unknown"),
                    is_group=chat_data.get("isGroup", False),
                    participant_count=chat_data.get("participantCount")
                ))
            return chats
            
        except Exception as e:
            logger.error(f"Failed to get chats: {e}")
            return []
    
    def get_messages(self, chat_id: str, limit: int = 10) -> List[Message]:
        """Get messages from a specific chat"""
        try:
            response = self.session.get(
                f"{self.base_url}/messages/{chat_id}",
                params={"limit": limit}
            )
            response.raise_for_status()
            
            response_data = response.json()
            
            # Handle None response or empty response
            if response_data is None:
                logger.debug(f"No messages returned for chat {chat_id}")
                return []
            
            # Ensure response_data is iterable
            if not isinstance(response_data, list):
                logger.debug(f"Invalid response format for chat {chat_id}: {type(response_data)}")
                return []
            
            messages = []
            for msg_data in response_data:
                if msg_data is None:
                    continue
                    
                messages.append(Message(
                    id=msg_data.get("id", f"msg_{len(messages)}"),
                    chat_id=chat_id,
                    sender=msg_data.get("sender", "Unknown"),
                    text=msg_data.get("text", ""),
                    timestamp=msg_data.get("timestamp", ""),
                    is_from_me=msg_data.get("fromMe", False),
                    message_type=msg_data.get("type", "text")
                ))
            return messages
            
        except Exception as e:
            logger.debug(f"Failed to get messages for chat {chat_id}: {e}")
            return []
    
    def send_message(self, chat_id: str, text: str) -> bool:
        """Send a text message to a chat"""
        try:
            payload = {
                "chat_id": chat_id,
                "message": text
            }
            
            response = self.session.post(
                f"{self.base_url}/send_message",
                json=payload
            )
            response.raise_for_status()
            
            logger.info(f"Message sent to chat {chat_id}: {text[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message to chat {chat_id}: {e}")
            return False
    
    def get_new_messages(self) -> List[Message]:
        """Poll for new messages across all chats"""
        new_messages = []
        
        try:
            chats = self.get_chats()
            logger.debug(f"Polling {len(chats)} chats for new messages...")
            
            for chat in chats:
                # Skip based on chat type preferences
                if chat.is_group and not settings.enable_group_chats:
                    continue
                if not chat.is_group and not settings.enable_personal_chats:
                    continue
                
                messages = self.get_messages(chat.id, limit=3)
                
                # Skip if no messages
                if not messages:
                    continue
                
                # Filter for new messages only
                for message in messages:
                    # Skip our own messages
                    if message.is_from_me:
                        continue
                    
                    # Check if this is a new message
                    last_seen = self._last_message_ids.get(chat.id)
                    if last_seen is None or message.id != last_seen:
                        new_messages.append(message)
                        break  # Only take the most recent new message per chat
                        
                # Update last seen message ID
                if messages:
                    self._last_message_ids[chat.id] = messages[0].id
                    
        except Exception as e:
            logger.error(f"Error polling for new messages: {e}")
        
        if new_messages:
            logger.info(f"Found {len(new_messages)} new message(s)")
        
        return new_messages
    
    def is_message_triggered(self, message: Message) -> bool:
        """Check if message should trigger bot response"""
        text = message.text.lower().strip()
        
        # Check authorization if configured
        if settings.authorized_number_list:
            if message.sender not in settings.authorized_number_list:
                return False
        
        # Check for trigger patterns
        for trigger in settings.trigger_list:
            trigger = trigger.lower()
            if text.startswith(trigger):
                return True
            if trigger.startswith("@") and trigger in text:
                return True
        
        return False
    
    def extract_query_from_message(self, message: Message) -> str:
        """Extract the actual query from a triggered message"""
        text = message.text.strip()
        
        # Remove trigger prefixes
        for trigger in settings.trigger_list:
            if text.lower().startswith(trigger.lower()):
                text = text[len(trigger):].strip()
                break
        
        return text if text else message.text

# Global client instance
whatsapp_client = WhatsAppMCPClient() 