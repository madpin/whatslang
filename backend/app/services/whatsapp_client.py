"""WhatsApp API client"""

import logging
from typing import Optional, List, Dict, Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class WhatsAppClient:
    """Client for interacting with go-whatsapp-web-multidevice API"""
    
    def __init__(self):
        """Initialize WhatsApp client"""
        self.base_url = settings.whatsapp_base_url.rstrip('/')
        self.timeout = httpx.Timeout(30.0, connect=10.0)
        
        # Setup authentication if provided
        self.auth = None
        if settings.whatsapp_api_user and settings.whatsapp_api_password:
            self.auth = (settings.whatsapp_api_user, settings.whatsapp_api_password)
    
    async def get_messages(
        self,
        chat_jid: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Fetch recent messages from a chat.
        
        Args:
            chat_jid: WhatsApp JID of the chat
            limit: Maximum number of messages to fetch
            
        Returns:
            List of message dicts
        """
        url = f"{self.base_url}/chat/{chat_jid}/messages"
        params = {
            "limit": limit,
            "offset": 0
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout, auth=self.auth) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                # Check for success response and extract messages
                if data.get("code") == "SUCCESS" and "results" in data and "data" in data["results"]:
                    return data["results"]["data"]
                else:
                    logger.error(f"Unexpected response format: {data}")
                    return []
        
        except httpx.HTTPError as e:
            logger.error(f"Error fetching messages: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching messages: {e}")
            return []
    
    async def send_message(
        self,
        phone: str,
        message: str,
        reply_message_id: Optional[str] = None
    ) -> bool:
        """
        Send a message to a chat.
        
        Args:
            phone: WhatsApp JID to send message to
            message: Message content
            reply_message_id: Optional message ID to reply to
            
        Returns:
            True if successful, False otherwise
        """
        url = f"{self.base_url}/send/message"
        payload = {
            "phone": phone,
            "message": message
        }
        
        if reply_message_id:
            payload["reply_message_id"] = reply_message_id
        
        try:
            logger.debug(f"Sending message: length={len(message)}, reply_to={reply_message_id}")
            
            async with httpx.AsyncClient(timeout=self.timeout, auth=self.auth) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                
                # Check for success response
                if data.get("code") in [200, "SUCCESS"]:
                    logger.info("Message sent successfully")
                    return True
                else:
                    logger.error(f"Failed to send message: {data}")
                    return False
        
        except httpx.HTTPError as e:
            logger.error(f"Error sending message: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response text: {e.response.text}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending message: {e}")
            return False
    
    async def download_and_decrypt_image(
        self,
        message_id: str,
        chat_jid: str
    ) -> Optional[bytes]:
        """
        Download and decrypt WhatsApp media.
        
        WhatsApp media is E2E encrypted. This method:
        1. Calls /message/{id}/download to trigger server-side decryption
        2. Gets the decrypted file path
        3. Downloads the decrypted image
        
        Args:
            message_id: WhatsApp message ID
            chat_jid: WhatsApp JID of the chat
            
        Returns:
            Decrypted image bytes or None if failed
        """
        try:
            # Step 1: Trigger media download/decryption
            download_url = f"{self.base_url}/message/{message_id}/download"
            params = {"phone": chat_jid}
            
            logger.info(f"Requesting media decryption for message {message_id}")
            
            async with httpx.AsyncClient(timeout=self.timeout, auth=self.auth) as client:
                response = await client.get(download_url, params=params)
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
                image_response = await client.get(image_url)
                image_response.raise_for_status()
                
                content_length = len(image_response.content)
                logger.info(f"Downloaded decrypted image: Size={content_length} bytes")
                
                return image_response.content
        
        except httpx.HTTPError as e:
            logger.error(f"Error downloading/decrypting image: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in download_and_decrypt_image: {e}")
            return None
    
    async def get_chat_info(self, chat_jid: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a chat.
        
        Args:
            chat_jid: WhatsApp JID of the chat
            
        Returns:
            Chat info dict or None if failed
        """
        url = f"{self.base_url}/chat/{chat_jid}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout, auth=self.auth) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                
                if data.get("code") == "SUCCESS" and "results" in data:
                    return data["results"]
                else:
                    logger.error(f"Failed to get chat info: {data}")
                    return None
        
        except httpx.HTTPError as e:
            logger.error(f"Error getting chat info: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting chat info: {e}")
            return None
    
    async def get_all_chats(self) -> List[Dict[str, Any]]:
        """
        Fetch all chats from WhatsApp.
        
        Returns:
            List of chat dicts with JID, name, type, and last message timestamp
        """
        url = f"{self.base_url}/chats"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout, auth=self.auth) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                
                # Check for success response and extract chats
                if data.get("code") == "SUCCESS" and "results" in data:
                    results = data["results"]
                    # The chats are in results.data
                    if isinstance(results, dict) and "data" in results:
                        chats = results["data"]
                        if isinstance(chats, list):
                            logger.info(f"Fetched {len(chats)} chats from WhatsApp")
                            return chats
                    logger.error(f"Unexpected chats format: {data}")
                    return []
                else:
                    logger.error(f"Failed to get chats: {data}")
                    return []
        
        except httpx.HTTPError as e:
            logger.error(f"Error fetching chats: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching chats: {e}")
            return []

