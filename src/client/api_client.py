import asyncio
import json
import uuid
import os
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

import httpx
import websockets
import logging

from . import config as config


class SpyAPIClient:
    """Client for interacting with the Spy API"""
    
    def __init__(self, base_url: str = config.API_BASE_URL):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=config.API_TIMEOUT)
        self.ws = None
        self.ws_connected = False
        self.reconnect_attempts = 0
        self.ws_retry_attempts = config.WS_RECONNECT_ATTEMPTS
        self.ws_retry_delay = config.WS_RECONNECT_DELAY
        self.offline_mode = False
        self.offline_cache_dir = os.path.join(config.DATA_DIR, "offline_cache")
        os.makedirs(self.offline_cache_dir, exist_ok=True)
    
    async def get_spies(self) -> List[Dict[str, Any]]:
        """Get list of available spies"""
        try:
            logging.debug(f"Fetching spies from {self.base_url}/api/spies/")
            response = await self.client.get(f"{self.base_url}/api/spies/")
            response.raise_for_status()
            self._cache_response("spies", response.json())
            self.offline_mode = False
            return response.json()
        except httpx.HTTPError as e:
            logging.error(f"Failed to fetch spies: {str(e)}", exc_info=True)
            self.offline_mode = True
            return await self._get_cached_response("spies", [])
    
    async def get_spy(self, spy_id: str) -> Dict[str, Any]:
        """Get details for a specific spy"""
        response = await self.client.get(f"{self.base_url}/api/spies/{spy_id}")
        return response.json()
    
    async def create_conversation(self, spy_id: str) -> Dict[str, Any]:
        """Create a new conversation"""
        # Using form data instead of JSON as per OpenAPI spec
        response = await self.client.post(
            f"{self.base_url}/api/conversation",
            data={"spy_id": spy_id}
        )
        return response.json()
    
    async def chat(
        self, 
        spy_id: str, 
        message: str,
        tool_calls: Optional[List[Dict]] = None,
        tool_outputs: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Send a message in chat mode with optional tool calls.
        
        Args:
            spy_id: ID of the spy to chat with
            message: The message to send
            tool_calls: List of tool calls to process
            tool_outputs: Outputs from previous tool calls
            
        Returns:
            Dict containing the response and any tool calls
        """
        try:
            payload = {"message": message}
            if tool_calls:
                payload["tool_calls"] = tool_calls
            if tool_outputs:
                payload["tool_outputs"] = tool_outputs
                
            response = await self.client.post(
                f"{self.base_url}/api/chat/{spy_id}",
                json=payload
            )
            response.raise_for_status()
            response_data = response.json()
            self._cache_chat_response(spy_id, message, response_data)
            self.offline_mode = False
            return response_data
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logging.warning(f"API unavailable, using offline mode: {str(e)}")
            self.offline_mode = True
            return await self._generate_offline_response(spy_id, message)
    
    async def debrief(self, spy_id: str, mission_id: str, message: str) -> Dict[str, Any]:
        """
        [Deprecated] Send a message in debrief mode.
        
        Note: It's recommended to use the chat() method with tool calls instead.
        Example:
            await client.chat(
                spy_id=spy_id,
                message="What happened during the mission?",
                tool_calls=[{
                    "name": "get_mission_context",
                    "arguments": {"mission_id": mission_id}
                }]
            )
        """
        response = await self.client.post(
            f"{self.base_url}/api/debrief/{spy_id}/{mission_id}",
            json={"message": message}
        )
        return response.json()
    
    async def chat_with_history(
        self, 
        spy_id: str, 
        conversation_id: str, 
        message: str,
        tool_calls: Optional[List[Dict]] = None,
        tool_outputs: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Send a message with conversation history context and optional tool calls.
        
        Args:
            spy_id: ID of the spy to chat with
            conversation_id: ID of the conversation
            message: The message to send
            tool_calls: List of tool calls to process
            tool_outputs: Outputs from previous tool calls
            
        Returns:
            Dict containing the response and any tool calls
        """
        try:
            payload = {"message": message}
            if tool_calls:
                payload["tool_calls"] = tool_calls
            if tool_outputs:
                payload["tool_outputs"] = tool_outputs
                
            response = await self.client.post(
                f"{self.base_url}/api/chat/{spy_id}/conversation/{conversation_id}",
                json=payload
            )
            response.raise_for_status()
            response_data = response.json()
            self._cache_chat_response(spy_id, message, response_data, conversation_id)
            self.offline_mode = False
            return response_data
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logging.warning(f"API unavailable, using offline mode: {str(e)}")
            self.offline_mode = True
            return await self._generate_offline_response(spy_id, message, conversation_id)
    
    async def connect_websocket(self, spy_id: str, conversation_id: Optional[str] = None) -> websockets.WebSocketClientProtocol:
        """Connect to the WebSocket for real-time updates with auto-reconnect"""
        # Use the configured WebSocket base URL
        if conversation_id:
            ws_url = f"{config.WS_BASE_URL}/ws/chat/{spy_id}/conversation/{conversation_id}"
        else:
            ws_url = f"{config.WS_BASE_URL}/ws/chat/{spy_id}"
        
        logging.info(f"Connecting to WebSocket: {ws_url}")
        
        # Implement reconnection logic
        for attempt in range(self.ws_retry_attempts):
            try:
                if attempt > 0:
                    logging.info(f"Reconnection attempt {attempt+1}/{self.ws_retry_attempts}")
                    await asyncio.sleep(self.ws_retry_delay)
                    
                self.ws = await websockets.connect(ws_url)
                self.ws_connected = True
                self.reconnect_attempts = 0
                logging.info("WebSocket connection established")
                return self.ws
                
            except Exception as e:
                self.reconnect_attempts += 1
                logging.error(f"WebSocket connection failed (attempt {attempt+1}/{self.ws_retry_attempts}): {str(e)}")
                
        logging.error(f"Failed to connect to WebSocket after {self.ws_retry_attempts} attempts")
        self.ws_connected = False
        raise ConnectionError(f"Failed to connect to WebSocket after {self.ws_retry_attempts} attempts")
    
    async def close(self):
        """Close all connections"""
        logging.debug("Closing API client connections")
        if self.ws and not self.ws.closed:
            await self.ws.close()
            self.ws_connected = False
        await self.client.aclose()

    def _cache_response(self, cache_key: str, data: Any) -> None:
        """Cache API response for offline use"""
        try:
            cache_file = os.path.join(self.offline_cache_dir, f"{cache_key}.json")
            with open(cache_file, "w") as f:
                json.dump({
                    "timestamp": time.time(),
                    "data": data
                }, f)
            logging.debug(f"Cached response for {cache_key}")
        except Exception as e:
            logging.error(f"Failed to cache response: {str(e)}", exc_info=True)

    def _cache_chat_response(self, spy_id: str, message: str, response: Dict[str, Any], 
                           conversation_id: Optional[str] = None) -> None:
        """Cache a chat response for offline use"""
        try:
            # Create spy-specific cache directory
            spy_cache_dir = os.path.join(self.offline_cache_dir, spy_id)
            os.makedirs(spy_cache_dir, exist_ok=True)
            
            # Generate a unique ID for this chat if conversation_id is not provided
            chat_id = conversation_id or str(uuid.uuid4())
            
            # Create conversation-specific cache directory
            conv_cache_dir = os.path.join(spy_cache_dir, chat_id)
            os.makedirs(conv_cache_dir, exist_ok=True)
            
            # Save the response with timestamp
            timestamp = datetime.now().isoformat()
            filename = f"{timestamp.replace(':', '-')}.json"
            filepath = os.path.join(conv_cache_dir, filename)
            
            with open(filepath, "w") as f:
                json.dump({
                    "timestamp": timestamp,
                    "message": message,
                    "response": response
                }, f)
                
            logging.debug(f"Cached chat response for spy {spy_id}, conversation {chat_id}")
        except Exception as e:
            logging.error(f"Failed to cache chat response: {str(e)}", exc_info=True)

    async def _get_cached_response(self, cache_key: str, default: Any = None) -> Any:
        """Get a cached response"""
        try:
            cache_file = os.path.join(self.offline_cache_dir, f"{cache_key}.json")
            if os.path.exists(cache_file):
                with open(cache_file, "r") as f:
                    cached = json.load(f)
                logging.info(f"Using cached response for {cache_key}")
                return cached.get("data", default)
        except Exception as e:
            logging.error(f"Failed to read cached response: {str(e)}", exc_info=True)
        
        return default

    async def _generate_offline_response(self, spy_id: str, message: str, 
                                       conversation_id: Optional[str] = None, 
                                       mission_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate an offline response based on cached data"""
        # Notify that we're in offline mode
        offline_notice = "[OFFLINE MODE] "
        
        try:
            # Determine if this is a chat or debrief
            if mission_id:
                # This is a debrief
                response_text = f"{offline_notice}I'm operating in offline mode. Your mission debrief request has been saved and will be processed when connectivity is restored."
                return {
                    "response": response_text,
                    "conversation_id": conversation_id or str(uuid.uuid4()),
                    "offline": True
                }
            else:
                # This is a chat - try to provide a helpful response
                if "help" in message.lower() or "assist" in message.lower():
                    response_text = f"{offline_notice}I'm currently in offline mode due to connectivity issues. I can still help with basic information, but my capabilities are limited until connection is restored."
                elif "status" in message.lower() or "connection" in message.lower():
                    response_text = f"{offline_notice}The application is currently in offline mode. Your messages are being cached locally and will be synchronized when connectivity is restored."
                else:
                    response_text = f"{offline_notice}I've received your message but I'm currently operating in offline mode. Your request has been saved locally and will be processed when connectivity is restored."
                
                return {
                    "response": response_text,
                    "conversation_id": conversation_id or str(uuid.uuid4()),
                    "offline": True
                }
        except Exception as e:
            logging.error(f"Error generating offline response: {str(e)}", exc_info=True)
            return {
                "response": f"{offline_notice}Unable to process your request in offline mode. Please try again when connectivity is restored.",
                "conversation_id": conversation_id or str(uuid.uuid4()),
                "offline": True
            }
