"""
WhatsApp MCP Client - Handles communication with whatsapp-mcp server
"""
import requests
import time
from typing import List, Dict, Optional, Any, Tuple
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
        """Check if MCP server is reachable and connected to WhatsApp"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def connection_status(self) -> dict:
        """Get detailed connection status including WhatsApp connection"""
        try:
            # First try the status endpoint
            response = self.session.get(f"{self.base_url}/status")
            if response.status_code == 200:
                return response.json()
        except:
            pass
        
        # Fallback: Check if we can get chats (means WhatsApp is connected)
        try:
            response = self.session.get(f"{self.base_url}/chats", timeout=3)
            if response.status_code == 200:
                chats = response.json()
                if isinstance(chats, list):
                    # If we receive a list (even empty) from /chats endpoint, the bridge is up
                    return {
                        "connected": True,
                        "message": f"Connected – {len(chats)} chat(s) available",
                        "chat_count": len(chats)
                    }
                else:
                    # Empty response, might be disconnected
                    return {"connected": False, "message": "No chats available - WhatsApp may be disconnected"}
            else:
                return {"connected": False, "message": f"Bridge returned {response.status_code}"}
        except Exception as e:
            logger.error(f"Failed to get connection status: {e}")
            return {"connected": False, "message": str(e)}

    def get_chats(self, limit: int = 50) -> List[ChatInfo]:
        """Get all available chats with optional limit for performance"""
        try:
            # Add limit parameter to reduce data fetching
            params = {"limit": limit} if limit else {}
            response = self.session.get(f"{self.base_url}/chats", params=params)
            response.raise_for_status()
            
            chats = []
            chat_data_list = response.json()
            
            # Limit processing if too many chats
            if len(chat_data_list) > limit:
                chat_data_list = chat_data_list[:limit]
                logger.info(f"Limited chat processing to {limit} chats for performance")
            
            for chat_data in chat_data_list:
                # Better contact name resolution
                name = chat_data.get("name", "Unknown")
                chat_id = chat_data["id"]
                
                # Quick name resolution without expensive operations
                if name.isdigit() or name == chat_id.split('@')[0]:
                    # Use simplified naming for performance
                    phone_suffix = name[-4:] if len(name) >= 4 else name
                    name = f"Contact {phone_suffix}"
                
                chats.append(ChatInfo(
                    id=chat_id,
                    name=name,
                    is_group=chat_data.get("isGroup", False),
                    participant_count=chat_data.get("participantCount")
                ))
            
            logger.debug(f"Retrieved {len(chats)} chats")
            return chats
            
        except Exception as e:
            logger.error(f"Failed to get chats: {e}")
            return []
    
    def _get_better_contact_name(self, chat_id: str) -> Optional[str]:
        """Try to get a better contact name from recent messages"""
        try:
            # Get recent messages to see if we can find a better name
            messages = self.get_messages(chat_id, limit=5)
            for message in messages:
                if not message.is_from_me and message.sender:
                    # Extract potential name from sender field
                    sender = message.sender
                    if sender and not sender.isdigit() and len(sender) > 5:
                        return sender
            return None
        except:
            return None
    
    def get_recent_recipients(self, limit: int = 10) -> List[ChatInfo]:
        """Get recent message recipients for easier contact selection"""
        try:
            response = self.session.get(f"{self.base_url}/chats")
            response.raise_for_status()
            
            # Sort chats by last message time and filter for recent activity
            chat_list = response.json()
            
            # Sort by lastMessageTime (most recent first)
            sorted_chats = sorted(
                chat_list, 
                key=lambda x: x.get("lastMessageTime", ""), 
                reverse=True
            )
            
            recent_chats = []
            for chat_data in sorted_chats[:limit]:
                name = chat_data.get("name", "Unknown")
                chat_id = chat_data["id"]
                
                # Better contact name resolution
                if name.isdigit() or name == chat_id.split('@')[0]:
                    name = self._get_better_contact_name(chat_id) or f"Contact {name[-4:]}"
                
                # Add emoji indicators for contact type
                if chat_data.get("isGroup", False):
                    display_name = f"👥 {name}"
                else:
                    # Show phone number for reference
                    phone = chat_id.split('@')[0]
                    if name != phone and not name.startswith("Contact"):
                        display_name = f"👤 {name} ({phone[-4:]})"
                    else:
                        display_name = f"📞 {phone}"
                
                recent_chats.append(ChatInfo(
                    id=chat_id,
                    name=display_name,
                    is_group=chat_data.get("isGroup", False),
                    participant_count=chat_data.get("participantCount")
                ))
            
            return recent_chats
            
        except Exception as e:
            logger.error(f"Failed to get recent recipients: {e}")
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
            # Use the correct API endpoint that matches the Go bridge
            payload = {
                "recipient": chat_id,  # Go bridge expects "recipient"
                "message": text        # Go bridge expects "message"
            }
            
            # Use the /api/send endpoint (not /send_message)
            response = self.session.post(
                f"{self.base_url}/api/send",
                json=payload
            )
            response.raise_for_status()
            
            # Check response for success
            result = response.json()
            success = result.get("success", False)
            
            if success:
                logger.info(f"Message sent successfully to {chat_id}: {text[:50]}...")
                return True
            else:
                error_msg = result.get("message", "Unknown error")
                logger.error(f"Message sending failed: {error_msg}")
                return False
                logger.error(f"Failed to send message to chat {chat_id}: {e}")
                return False
            
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
    
    def find_contact_by_name(self, search_name: str) -> List[ChatInfo]:
        """Find contacts by name (fuzzy search)"""
        try:
            chats = self.get_chats()
            matches = []
            
            search_name_lower = search_name.lower().strip()
            
            for chat in chats:
                if chat.is_group:
                    continue  # Skip groups for mention-based messaging
                
                # Get better contact name
                contact_name = chat.name
                if contact_name.isdigit() or contact_name == chat.id.split('@')[0]:
                    contact_name = self._get_better_contact_name(chat.id) or f"Contact {contact_name[-4:]}"
                
                # Check for name matches (fuzzy)
                if search_name_lower in contact_name.lower():
                    phone = chat.id.split('@')[0]
                    matches.append(ChatInfo(
                        id=chat.id,
                        name=f"{contact_name} ({phone})",
                        is_group=False,
                        participant_count=None
                    ))
            
            return matches
            
        except Exception as e:
            logger.error(f"Failed to find contact by name: {e}")
            return []
    
    def parse_mention_message(self, message: str) -> Tuple[Optional[str], str]:
        """Parse message for @mentions and extract recipient and clean message"""
        import re
        
        # Look for @mentions at the beginning of the message
        mention_pattern = r'^@(\w+(?:\s+\w+)*)\s+(.*)'
        match = re.match(mention_pattern, message.strip())
        
        if match:
            mentioned_name = match.group(1).strip()
            clean_message = match.group(2).strip()
            return mentioned_name, clean_message
        
        return None, message

# Global client instance
whatsapp_client = WhatsAppMCPClient() 