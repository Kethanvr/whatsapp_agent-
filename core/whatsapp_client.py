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
        self._startup_time = time.time()  # Track when bot started to ignore old messages
        
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
        """Get all available chats with PRIORITY for authorized numbers"""
        try:
            # Get ALL chats first (no limit to find authorized numbers)
            response = self.session.get(f"{self.base_url}/chats")
            response.raise_for_status()
            
            chat_data_list = response.json()
            
            # Separate authorized and other chats
            authorized_chats = []
            other_chats = []
            
            for chat_data in chat_data_list:
                chat_id = chat_data["id"]
                
                # Check if this chat belongs to an authorized number
                is_authorized_chat = False
                if settings.authorized_number_list:
                    for auth_number in settings.authorized_number_list:
                        # Normalize auth number for comparison
                        auth_normalized = auth_number.strip()
                        if auth_normalized.startswith('+'):
                            auth_normalized = auth_normalized[1:]
                        
                        # Check if chat ID contains this authorized number
                        if auth_normalized in chat_id:
                            is_authorized_chat = True
                            logger.info(f"🔒 Found AUTHORIZED chat: {chat_id}")
                            break
                
                # Better contact name resolution
                name = chat_data.get("name", "Unknown")
                if name.isdigit() or name == chat_id.split('@')[0]:
                    phone_suffix = name[-4:] if len(name) >= 4 else name
                    name = f"Contact {phone_suffix}"
                
                chat_info = ChatInfo(
                    id=chat_id,
                    name=name,
                    is_group=chat_data.get("isGroup", False),
                    participant_count=chat_data.get("participantCount")
                )
                
                if is_authorized_chat:
                    authorized_chats.append(chat_info)
                else:
                    other_chats.append(chat_info)
            
            # Combine: Authorized chats FIRST, then others (limited)
            chats = authorized_chats + other_chats[:limit-len(authorized_chats)]
            
            logger.info(f"Retrieved {len(authorized_chats)} authorized + {len(other_chats[:limit-len(authorized_chats)])} other = {len(chats)} total chats")
            if authorized_chats:
                logger.info(f"✅ Authorized chats prioritized: {[c.id for c in authorized_chats]}")
            
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
        """Send a text message to a chat with retry logic for timeout issues"""
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                # Use the correct API endpoint that matches the Go bridge
                payload = {
                    "recipient": chat_id,  # Go bridge expects "recipient"
                    "message": text        # Go bridge expects "message"
                }
                
                logger.info(f"📤 Attempt {attempt + 1}/{max_retries}: Sending to {chat_id}")
                
                # Use the /api/send endpoint with extended timeout
                response = self.session.post(
                    f"{self.base_url}/api/send",
                    json=payload,
                    timeout=30  # Extended timeout for WhatsApp delays
                )
                response.raise_for_status()
                
                # Check response for success
                result = response.json()
                success = result.get("success", False)
                
                if success:
                    logger.info(f"✅ Message sent successfully to {chat_id}: {text[:50]}...")
                    return True
                else:
                    error_msg = result.get("message", "Unknown error")
                    logger.warning(f"⚠️ Attempt {attempt + 1} failed: {error_msg}")
                    
                    # If it's a known WhatsApp issue, retry
                    if "timeout" in error_msg.lower() or "failed to send" in error_msg.lower():
                        if attempt < max_retries - 1:
                            logger.info(f"🔄 Retrying in {retry_delay} seconds...")
                            time.sleep(retry_delay)
                            continue
                    
                    logger.error(f"❌ Message sending failed: {error_msg}")
                    return False
                
            except requests.exceptions.Timeout:
                logger.warning(f"⏰ Attempt {attempt + 1} timed out")
                if attempt < max_retries - 1:
                    logger.info(f"🔄 Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    continue
                else:
                    logger.error(f"❌ All {max_retries} attempts timed out - WhatsApp bridge issue")
                    return False
                    
            except Exception as e:
                logger.warning(f"⚠️ Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"🔄 Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    continue
                else:
                    logger.error(f"❌ Failed to send message to chat {chat_id}: {e}")
                    return False
        
        return False
    
    def get_new_messages(self) -> List[Message]:
        """Poll for new messages across all chats - PRIORITIZING authorized chats"""
        new_messages = []
        startup_grace_period = 5  # Reduced to 5 seconds
        
        try:
            # Skip polling for the first few seconds to avoid processing old messages
            if time.time() - self._startup_time < startup_grace_period:
                logger.debug(f"Skipping message polling - within grace period ({startup_grace_period}s)")
                return []
            
            chats = self.get_chats()  # Now prioritizes authorized chats
            logger.debug(f"Polling {len(chats)} chats for new messages (startup: {self._startup_time})")
            
            for chat in chats:
                # Skip based on chat type preferences
                if chat.is_group and not settings.enable_group_chats:
                    continue
                if not chat.is_group and not settings.enable_personal_chats:
                    continue
                
                # Get recent messages (limit to 3 for authorized chats, 1 for others)
                is_authorized_chat = any(auth.replace('+', '').strip() in chat.id 
                                       for auth in settings.authorized_number_list)
                limit = 3 if is_authorized_chat else 1
                
                messages = self.get_messages(chat.id, limit=limit)
                
                # Skip if no messages
                if not messages:
                    continue
                
                # Get last seen message ID for this chat
                last_seen = self._last_message_ids.get(chat.id)
                
                # Find new messages (messages after last seen)
                chat_new_messages = []
                for message in messages:
                    # Skip our own messages
                    if message.is_from_me:
                        continue
                    
                    # For authorized chats, be more lenient with timestamp filtering
                    if is_authorized_chat:
                        # More lenient timestamp check for authorized numbers
                        message_age_minutes = (time.time() - self._startup_time) / 60
                        if message_age_minutes > 30:  # Only skip if very old (30+ minutes)
                            try:
                                from datetime import datetime
                                message_time = datetime.fromisoformat(message.timestamp.replace('Z', '+00:00'))
                                message_timestamp = message_time.timestamp()
                                
                                # For authorized chats, allow messages from last 10 minutes
                                if message_timestamp < (time.time() - 600):  # 10 minutes ago
                                    logger.debug(f"Skipping very old message from {message.sender}: {message.text[:30]}...")
                                    continue
                            except Exception:
                                pass  # If timestamp parsing fails, process the message
                    else:
                        # Strict timestamp check for non-authorized chats
                        try:
                            from datetime import datetime
                            message_time = datetime.fromisoformat(message.timestamp.replace('Z', '+00:00'))
                            message_timestamp = message_time.timestamp()
                            
                            if message_timestamp < self._startup_time:
                                logger.debug(f"Skipping old message from {message.sender}: {message.text[:30]}...")
                                continue
                        except Exception:
                            pass
                    
                    # If this is the first time seeing this chat
                    if last_seen is None:
                        # For authorized chats, process the message; for others, just mark as seen
                        if is_authorized_chat:
                            chat_new_messages.append(message)
                            logger.info(f"🔒 First message from AUTHORIZED chat {chat.id}: {message.text[:30]}...")
                        else:
                            logger.debug(f"First time seeing chat {chat.id}, marking as seen but not processing")
                        self._last_message_ids[chat.id] = message.id
                        continue
                    
                    # For existing chats, process all messages newer than last seen
                    if message.id != last_seen:
                        chat_new_messages.append(message)
                        if is_authorized_chat:
                            logger.info(f"🔒 New AUTHORIZED message from {message.sender}: {message.text[:30]}...")
                        else:
                            logger.debug(f"New message from {message.sender}: {message.text[:30]}...")
                    else:
                        # Found the last seen message, stop here
                        break
                
                # Add new messages from this chat
                new_messages.extend(chat_new_messages)
                        
                # Update last seen message ID to the most recent message
                if messages and not messages[0].is_from_me:
                    self._last_message_ids[chat.id] = messages[0].id
                    
        except Exception as e:
            logger.error(f"Error polling for new messages: {e}")
        
        if new_messages:
            logger.info(f"Found {len(new_messages)} NEW message(s) (prioritizing authorized chats)")
        
        return new_messages
    
    def is_message_triggered(self, message: Message) -> bool:
        """Check if message should trigger bot response - FLEXIBLE TRIGGER MATCHING"""
        text = message.text.strip()
        text_lower = text.lower()
        
        # Check if it's a group message (reduce log noise)
        is_group = "@g.us" in message.chat_id
        
        if not is_group:
            # Debug logging for personal chats
            logger.info(f"🔍 Checking FLEXIBLE trigger for: '{message.text}' from {message.sender}")
            logger.info(f"🔍 Available triggers: {settings.trigger_list}")
            
        # Check authorization if configured
        if settings.authorized_number_list:
            # Normalize phone numbers for comparison (handle +prefix and no prefix)
            sender_normalized = message.sender.strip()
            if sender_normalized.startswith('+'):
                sender_normalized = sender_normalized[1:]  # Remove + prefix
            
            # Check if sender matches any authorized number (with or without + prefix)
            is_authorized = False
            for auth_number in settings.authorized_number_list:
                auth_normalized = auth_number.strip()
                if auth_normalized.startswith('+'):
                    auth_normalized = auth_normalized[1:]  # Remove + prefix
                
                if sender_normalized == auth_normalized:
                    is_authorized = True
                    break
            
            if not is_authorized:
                if not is_group:
                    logger.info(f"❌ Message rejected: sender {message.sender} not in authorized list {settings.authorized_number_list}")
                return False
            else:
                if not is_group:
                    logger.info(f"✅ Message authorized: sender {message.sender} matches authorized list")
        
        # FLEXIBLE TRIGGER MATCHING - much more lenient
        for trigger in settings.trigger_list:
            trigger_lower = trigger.lower()
            if not is_group:
                logger.info(f"🔍 Checking trigger: '{trigger}' against text: '{text_lower}'")
            
            # FLEXIBLE MATCHING OPTIONS:
            # 1. Exact match: "!ask" == "!ask"
            if text_lower == trigger_lower:
                if not is_group:
                    logger.info(f"✅ EXACT MATCH: '{trigger}' == '{text_lower}'")
                return True
            
            # 2. Starts with trigger + space: "!ask hello" starts with "!ask "
            if text_lower.startswith(trigger_lower + " "):
                if not is_group:
                    logger.info(f"✅ START MATCH: '{text_lower}' starts with '{trigger} '")
                return True
            
            # 3. Starts with trigger: "@askme" starts with "@ask" (for @ai)
            if text_lower.startswith(trigger_lower):
                if not is_group:
                    logger.info(f"✅ PREFIX MATCH: '{text_lower}' starts with '{trigger}'")
                return True
            
            # 4. Contains trigger as word: "hey !ask me" contains "!ask"
            if f" {trigger_lower} " in text_lower or f" {trigger_lower}" == text_lower[-len(trigger_lower)-1:]:
                if not is_group:
                    logger.info(f"✅ WORD MATCH: '{text_lower}' contains '{trigger}' as word")
                return True
        
        # SPECIAL FLEXIBLE PATTERNS for common variations
        # Handle common @ask, @ai, @bot variations
        if text_lower.startswith('@'):
            for pattern in ['@ask', '@ai', '@bot']:
                if pattern in text_lower:
                    if not is_group:
                        logger.info(f"✅ @ PATTERN MATCH: '{text_lower}' contains '{pattern}'")
                    return True
        
        # Handle common !ask, !ai, !bot variations  
        if text_lower.startswith('!'):
            for pattern in ['!ask', '!ai', '!bot']:
                if pattern in text_lower:
                    if not is_group:
                        logger.info(f"✅ ! PATTERN MATCH: '{text_lower}' contains '{pattern}'")
                    return True
        
        # Handle '>' trigger anywhere in message
        if '>' in text_lower:
            if not is_group:
                logger.info(f"✅ > PATTERN MATCH: '{text_lower}' contains '>'")
            return True
        
        if not is_group:
            logger.info(f"❌ No triggers matched - ignoring message: '{text_lower}'")
        
        return False
    
    def extract_query_from_message(self, message: Message) -> str:
        """Extract the actual query from a triggered message"""
        text = message.text.strip()
        original_text = text
        
        logger.info(f"🔧 Extracting query from: '{text}'")
        
        # Remove trigger prefixes
        for trigger in settings.trigger_list:
            trigger_lower = trigger.lower()
            text_lower = text.lower()
            
            # Check if starts with trigger
            if text_lower.startswith(trigger_lower):
                # Remove the trigger and any following whitespace
                if text_lower.startswith(trigger_lower + " "):
                    text = text[len(trigger) + 1:].strip()
                else:
                    text = text[len(trigger):].strip()
                logger.info(f"🔧 Removed trigger '{trigger}', remaining: '{text}'")
                break
        
        # If no query remains after trigger removal, return original text
        if not text or text.lower() == original_text.lower():
            # For greetings and questions without triggers, return as-is
            result = original_text
        else:
            result = text
        
        logger.info(f"🔧 Final extracted query: '{result}'")
        return result
    
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