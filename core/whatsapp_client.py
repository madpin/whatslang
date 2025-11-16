"""WhatsApp API client for sending and receiving messages."""

import logging
from typing import Optional, Dict, Any, List
import time

import requests

logger = logging.getLogger(__name__)


class WhatsAppClient:
    """Client for interacting with the WhatsApp API."""
    
    def __init__(self, base_url: str, username: Optional[str] = None, password: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        if username and password:
            self.session.auth = (username, password)
    
    def health_check(self) -> bool:
        """
        Check if the WhatsApp API is responding.
        
        Returns:
            True if API is healthy, False otherwise
        """
        try:
            # Try a simple endpoint that should always work
            response = self.session.get(f"{self.base_url}/chats", timeout=5)
            return response.status_code < 500
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False
    
    def get_messages(
        self,
        chat_jid: str,
        limit: int = 20,
        max_retries: int = 2,
        retry_delay: float = 1.0,
        validate_chat: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Fetch recent messages from a chat with retry logic.
        
        Args:
            chat_jid: The JID of the chat to fetch messages from
            limit: Maximum number of messages to fetch
            max_retries: Number of times to retry on failure (default: 2)
            retry_delay: Delay in seconds between retries (default: 1.0)
            validate_chat: Whether to validate chat exists before fetching (default: False)
        
        Returns:
            List of message dictionaries, or empty list on error
        """
        # Optional: validate chat exists first
        if validate_chat:
            chat_info = self.get_chat_info(chat_jid)
            if not chat_info:
                logger.warning(f"Chat {chat_jid} not found or inaccessible, skipping message fetch")
                return []
        
        url = f"{self.base_url}/chat/{chat_jid}/messages"
        params = {
            "limit": limit,
            "offset": 0
        }
        
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    logger.info(f"Retry attempt {attempt}/{max_retries} for get_messages({chat_jid})")
                    time.sleep(retry_delay)
                
                response = self.session.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                # Check for success response and extract messages from results.data
                if data.get("code") == "SUCCESS" and "results" in data and "data" in data["results"]:
                    if attempt > 0:
                        logger.info(f"Successfully fetched messages after {attempt} retries")
                    return data["results"]["data"]
                else:
                    logger.error(f"Unexpected response format: {data}")
                    return []
            
            except requests.exceptions.HTTPError as e:
                last_error = e
                status_code = e.response.status_code if hasattr(e, 'response') and e.response else None
                
                # Log error details
                logger.error(f"HTTP error fetching messages (attempt {attempt + 1}/{max_retries + 1}): {e}")
                if hasattr(e, 'response') and e.response is not None:
                    try:
                        logger.error(f"Response status: {e.response.status_code}")
                        # Try to get response text safely
                        try:
                            resp_text = e.response.text
                            if resp_text:
                                logger.error(f"Response body: {resp_text[:500]}")
                            else:
                                logger.error("Response body is empty")
                        except Exception:
                            logger.error("Could not decode response body")
                            
                        # Try to parse as JSON for better error messages
                        try:
                            error_data = e.response.json()
                            logger.error(f"Error details: {error_data}")
                        except Exception:
                            pass  # Not JSON, already logged text above
                    except Exception as resp_err:
                        logger.debug(f"Could not log response details: {resp_err}")
                
                # Don't retry on client errors (4xx) except 429 (rate limit)
                if status_code and 400 <= status_code < 500 and status_code != 429:
                    logger.warning(f"Client error {status_code}, not retrying")
                    break
                
                # For server errors (5xx) or network issues, continue to retry
                if attempt < max_retries:
                    logger.info(f"Will retry after {retry_delay}s...")
                    continue
            
            except requests.exceptions.RequestException as e:
                last_error = e
                logger.error(f"Network error fetching messages (attempt {attempt + 1}/{max_retries + 1}): {e}")
                
                if attempt < max_retries:
                    logger.info(f"Will retry after {retry_delay}s...")
                    continue
        
        # If we get here, all retries failed
        logger.error(f"Failed to fetch messages after {max_retries + 1} attempts. Last error: {last_error}")
        return []
    
    def send_message(
        self,
        phone: str,
        message: str,
        reply_message_id: Optional[str] = None
    ) -> bool:
        """Send a message to a chat, optionally replying to another message."""
        url = f"{self.base_url}/send/message"
        payload = {
            "phone": phone,
            "message": message
        }
        
        if reply_message_id:
            payload["reply_message_id"] = reply_message_id
        
        try:
            logger.debug(f"Sending message: length={len(message)}, reply_to={reply_message_id}")
            response = self.session.post(url, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Check for success response (could be code: 200 or code: "SUCCESS")
            if data.get("code") in [200, "SUCCESS"]:
                logger.info(f"Message sent successfully")
                return True
            else:
                logger.error(f"Failed to send message: {data}")
                logger.error(f"Message length was: {len(message)} chars")
                return False
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending message: {e}")
            logger.error(f"Message length was: {len(message)} chars")
            if hasattr(e.response, 'text'):
                logger.error(f"Response text: {e.response.text}")
            return False
    
    def get_chats(self) -> List[Dict[str, Any]]:
        """Fetch available chats/groups from WhatsApp API."""
        url = f"{self.base_url}/chats"
        
        try:
            logger.info(f"Fetching chats from: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"Chats response type: {type(data)}")
            
            # Handle different response formats
            # Format 1: Direct list [{"id": "...", "name": "..."}]
            if isinstance(data, list):
                logger.info(f"Found {len(data)} chats (direct list)")
                if data:
                    logger.info(f"Sample chat data: {data[0]}")
                return data
            
            # Format 2: Wrapped in results {"code": "SUCCESS", "results": [...]}
            if isinstance(data, dict):
                logger.info(f"Response keys: {data.keys()}")
                
                if data.get("code") == "SUCCESS" and "results" in data:
                    chats = data["results"]
                    if isinstance(chats, list):
                        logger.info(f"Found {len(chats)} chats (results list)")
                        if chats:
                            logger.info(f"Sample chat data: {chats[0]}")
                        return chats
                    elif isinstance(chats, dict) and "data" in chats:
                        chats_list = chats["data"]
                        logger.info(f"Found {len(chats_list)} chats (nested data)")
                        if chats_list:
                            logger.info(f"Sample chat data: {chats_list[0]}")
                        return chats_list
            
            logger.warning(f"Unexpected response format for get_chats: {str(data)[:500]}")
            return []
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching chats: {e}")
            return []
    
    def get_groups(self) -> List[Dict[str, Any]]:
        """Fetch user's groups from WhatsApp API using /user/my/groups endpoint."""
        url = f"{self.base_url}/user/my/groups"
        
        try:
            logger.info(f"Fetching groups from: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"Groups response code: {data.get('code')}")
            logger.info(f"Groups response keys: {list(data.keys())}")
            logger.info(f"Full groups response: {str(data)[:1000]}")
            
            # Check for success response and extract groups
            if data.get("code") == "SUCCESS" and "results" in data:
                groups = data["results"]
                
                # Handle both direct list and nested data formats
                if isinstance(groups, list):
                    logger.info(f"✓ Found {len(groups)} groups (direct list)")
                    if groups:
                        logger.info(f"Sample group structure: {groups[0]}")
                        # Show sample group fields
                        sample_keys = list(groups[0].keys())
                        logger.info(f"Sample group fields: {sample_keys}")
                    return groups
                elif isinstance(groups, dict) and "data" in groups:
                    groups_list = groups["data"]
                    logger.info(f"✓ Found {len(groups_list)} groups (nested in data)")
                    if groups_list:
                        logger.info(f"Sample group structure: {groups_list[0]}")
                        sample_keys = list(groups_list[0].keys())
                        logger.info(f"Sample group fields: {sample_keys}")
                    return groups_list
                else:
                    logger.warning(f"Groups data type: {type(groups)}, Content: {groups}")
            
            logger.warning(f"Unexpected response format or unsuccessful code: {data}")
            return []
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching groups from {url}: {e}")
            return []
    
    def get_chat_info(self, chat_jid: str) -> Optional[Dict[str, Any]]:
        """Get detailed info for a specific chat."""
        url = f"{self.base_url}/chat/{chat_jid}"
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Check for success response
            if data.get("code") == "SUCCESS" and "results" in data:
                return data["results"]
            
            logger.warning(f"Unexpected response format for get_chat_info: {data}")
            return None
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching chat info for {chat_jid}: {e}")
            return None
    
    def get_group_info(self, group_jid: str) -> Optional[Dict[str, Any]]:
        """Get group information including proper group name/subject."""
        
        # Try GET requests first
        get_endpoints = [
            f"/group/{group_jid}",
            f"/group?jid={group_jid}",
            f"/chat/{group_jid}",
        ]
        
        for endpoint in get_endpoints:
            url = f"{self.base_url}{endpoint}"
            
            try:
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                logger.info(f"GET {endpoint} response: {str(data)[:300]}")
                
                # Check for success response
                if data.get("code") == "SUCCESS" and "results" in data:
                    group_info = data["results"]
                    logger.info(f"✓ Fetched group info from GET {endpoint}")
                    return group_info
                
                # Also try direct response format
                if isinstance(data, dict) and ('name' in data or 'subject' in data):
                    logger.info(f"✓ Fetched group info from GET {endpoint} (direct)")
                    return data
                    
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 405:
                    # Try POST if GET is not allowed
                    try:
                        logger.info(f"GET not allowed for {endpoint}, trying POST")
                        post_response = self.session.post(url, json={"jid": group_jid}, timeout=10)
                        post_response.raise_for_status()
                        post_data = post_response.json()
                        
                        logger.info(f"POST {endpoint} response: {str(post_data)[:300]}")
                        
                        if post_data.get("code") == "SUCCESS" and "results" in post_data:
                            logger.info(f"✓ Fetched group info from POST {endpoint}")
                            return post_data["results"]
                    except Exception as post_error:
                        logger.debug(f"POST also failed for {endpoint}: {post_error}")
                        
                logger.debug(f"Failed GET {endpoint}: {e}")
                continue
            except Exception as e:
                logger.debug(f"Error with {endpoint}: {e}")
                continue
        
        # Try the /group endpoint with POST and group JID in body
        try:
            url = f"{self.base_url}/group"
            logger.info(f"Trying POST {url} with jid in body")
            response = self.session.post(url, json={"jid": group_jid}, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"POST /group response: {str(data)[:300]}")
            
            if data.get("code") == "SUCCESS" and "results" in data:
                logger.info(f"✓ Fetched group info from POST /group")
                return data["results"]
        except Exception as e:
            logger.debug(f"POST /group failed: {e}")
        
        logger.warning(f"Could not fetch group info for {group_jid} from any endpoint")
        return None
    
    def is_bot_message(self, sender_jid: str, bot_device_id: str) -> bool:
        """Check if a message sender is a bot/system account."""
        # Check if sender matches the bot's device ID
        if sender_jid == bot_device_id:
            return True
        
        # Check if sender is a bot (typically ends with @s.whatsapp.net and matches device pattern)
        # Bot device IDs typically look like: "353834210235:79@s.whatsapp.net"
        if "@s.whatsapp.net" in sender_jid and ":" in sender_jid:
            # Extract device portion and compare with bot device ID
            sender_device = sender_jid.split("@")[0]
            bot_device = bot_device_id.split("@")[0] if "@" in bot_device_id else bot_device_id
            
            if sender_device == bot_device:
                return True
        
        return False
    
    def download_and_decrypt_image(self, message_id: str, chat_jid: str) -> Optional[bytes]:
        """
        Download and decrypt WhatsApp media using the API.
        
        WhatsApp media is E2E encrypted. This method:
        1. Calls /message/{id}/download to trigger server-side decryption
        2. Gets the decrypted file path
        3. Downloads the decrypted image
        """
        try:
            # Step 1: Trigger media download/decryption on server
            download_url = f"{self.base_url}/message/{message_id}/download"
            params = {"phone": chat_jid}
            
            logger.info(f"Requesting media decryption for message {message_id}")
            response = self.session.get(download_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if data.get("code") != "SUCCESS":
                logger.error(f"Media download failed: {data.get('message')}")
                return None
            
            # Step 2: Get the decrypted file path
            file_path = data.get("results", {}).get("file_path")
            if not file_path:
                logger.error(f"No file_path in response: {data}")
                return None
            
            logger.info(f"Media decrypted to: {file_path}")
            
            # Step 3: Download the decrypted image
            image_url = f"{self.base_url}/{file_path}"
            image_response = self.session.get(image_url, timeout=30)
            image_response.raise_for_status()
            
            content_length = len(image_response.content)
            logger.info(f"Downloaded decrypted image: Size={content_length} bytes")
            
            return image_response.content
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error downloading/decrypting image: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in download_and_decrypt_image: {e}")
            return None

