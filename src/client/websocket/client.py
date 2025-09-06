"""
WebSocket client for the Spy Agency CLI application.

This module handles the WebSocket connection to the backend server,
including connection management, reconnection, and message handling.
"""

import asyncio
import json
import random
import os
from typing import Callable, Dict, Optional
from datetime import datetime

import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

from src.client.config import (
    APP_PLATFORM,
    APP_VERSION,
    WEBSOCKET_BASE_URL,
    WS_HEARTBEAT_INTERVAL,
    WS_RECONNECT_BASE_DELAY,
    WS_RECONNECT_MAX_ATTEMPTS,
)
from src.client.logger import logger
from src.client.websocket.protocol import (
    Message,
    MessageType,
    UserMessage,
    parse_message_from_json,
)


# Session persistence file path
SESSION_DIR = os.path.expanduser("~/.spy_agency/sessions")

# Ensure session directory exists
os.makedirs(SESSION_DIR, exist_ok=True)

class WebSocketClient:
    """
    WebSocket client for communicating with the backend server.
    
    This class handles the WebSocket connection, including connection management,
    reconnection, and message handling.
    """
    
    def __init__(
        self,
        agent_id: str = None,
        server_url: str = None,
        on_message: Optional[Callable[[Message], None]] = None,
        on_connect: Optional[Callable[[], None]] = None,
        on_disconnect: Optional[Callable[[], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
        session_id: Optional[str] = None,
        auto_reconnect: bool = True,
    ):
        """
        Initialize a new WebSocket client.
        
        Args:
            agent_id: The agent ID to use for the connection
            server_url: The full WebSocket server URL (including agent_id)
            on_message: Callback for when a message is received
            on_connect: Callback for when the connection is established
            on_disconnect: Callback for when the connection is closed
            on_error: Callback for when an error occurs
            session_id: Optional session ID for reconnection
        """
        self.agent_id = agent_id
        self.on_message = on_message
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        self.on_error = on_error
        
        self.websocket = None
        self.connected = False
        self.reconnect_task = None
        self.heartbeat_task = None
        self.receive_task = None
        
        # Session management
        self.session_id = session_id
        self.last_reconnect_time = None
        self.reconnect_count = 0
        self.max_session_age = 300  # 5 minutes in seconds
        
        # Reconnection settings
        self.auto_reconnect = auto_reconnect
        self.is_reconnecting = False
        self.should_attempt_reconnect = True
        
        # Use the provided server_url or construct it from agent_id
        if server_url:
            self.connection_url = server_url
            logger.debug(f"Using provided server URL: {self.connection_url}")
        elif agent_id:
            self.connection_url = f"{WEBSOCKET_BASE_URL}/{agent_id}"
            logger.debug(f"Using constructed URL from agent_id: {self.connection_url}")
        else:
            raise ValueError("Either server_url or agent_id must be provided")
        
        self.pending_messages: Dict[str, asyncio.Future] = {}
        self.conversation_id: Optional[str] = None
        
        # Try to load saved session data
        self._load_session()
        
    def _get_session_file_path(self) -> str:
        """Get the path to the session file for this agent"""
        if not self.agent_id:
            return None
        return os.path.join(SESSION_DIR, f"{self.agent_id}.json")
    
    def _save_session(self) -> None:
        """Save the current session data to a file"""
        if not self.agent_id:
            return
            
        try:
            session_data = {
                "agent_id": self.agent_id,
                "conversation_id": self.conversation_id,
                "session_id": self.session_id,
                "last_updated": datetime.utcnow().isoformat(),
            }
            
            file_path = self._get_session_file_path()
            with open(file_path, "w") as f:
                json.dump(session_data, f)
                
            logger.debug(f"Saved session data to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save session data: {e}")
    
    def _load_session(self) -> None:
        """Load session data from a file if it exists"""
        if not self.agent_id:
            return
            
        file_path = self._get_session_file_path()
        if not file_path or not os.path.exists(file_path):
            return
            
        try:
            with open(file_path, "r") as f:
                session_data = json.load(f)
                
            # Check if the session is still valid (not too old)
            last_updated = datetime.fromisoformat(session_data.get("last_updated", ""))
            now = datetime.utcnow()
            age_seconds = (now - last_updated).total_seconds()
            
            if age_seconds > self.max_session_age:
                logger.info(f"Saved session is too old ({age_seconds:.1f} seconds), not loading")
                # Clear the outdated session data
                self.clear_session_data()
                return
                
            # Load the session data
            if not self.conversation_id and "conversation_id" in session_data:
                self.conversation_id = session_data["conversation_id"]
                logger.info(f"Loaded conversation_id from saved session: {self.conversation_id}")
                
            if not self.session_id and "session_id" in session_data:
                self.session_id = session_data["session_id"]
                logger.info(f"Loaded session_id from saved session: {self.session_id}")
                
            logger.debug(f"Loaded session data from {file_path}")
        except Exception as e:
            logger.error(f"Failed to load session data: {e}")
            
    def clear_session_data(self) -> None:
        """Clear all session data and remove the session file"""
        # Reset session variables
        self.session_id = None
        self.conversation_id = None
        self.reconnect_count = 0
        self.last_reconnect_time = None
        
        # Remove the session file if it exists
        file_path = self._get_session_file_path()
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Removed session file: {file_path}")
            except Exception as e:
                logger.error(f"Failed to remove session file: {e}")
                
        logger.info("Session data cleared")
        
    async def connect(self) -> bool:
        """
        Connect to the WebSocket server.
        
        Returns:
            True if the connection was successful, False otherwise
        """
        # Prepare connection URL with session information if available
        connection_url = self.connection_url
        
        # Add session_id as query parameter if available and not already in URL
        if self.session_id and "session_id=" not in connection_url:
            separator = "&" if "?" in connection_url else "?"
            connection_url = f"{connection_url}{separator}session_id={self.session_id}"
            logger.info(f"Added session_id to connection URL: {self.session_id}")
            
        # Add conversation_id as query parameter if available and not already in URL
        if self.conversation_id and "conversation_id=" not in connection_url:
            separator = "&" if "?" in connection_url else "?"
            connection_url = f"{connection_url}{separator}conversation_id={self.conversation_id}"
            logger.info(f"Added conversation_id to connection URL: {self.conversation_id}")
            
        logger.debug(f"Connecting to {connection_url} with agent_id={self.agent_id}")
        
        try:
            # For websockets 15.0.1, we need to use the correct parameters
            # The extra_headers parameter is not supported directly
            # Instead, we need to create a ClientOptions object
            
            # Set up connection parameters compatible with websockets 15.0.1
            self.websocket = await websockets.connect(
                connection_url,
                ping_interval=None,  # Disable automatic pings, we'll handle this ourselves
                close_timeout=5,     # Set a reasonable timeout for closing the connection
            )
            
            self.connected = True
            logger.info("Connected to WebSocket server")
            logger.debug(f"WebSocket connection established with agent_id={self.agent_id}")
            
            # Start the heartbeat and receive tasks
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            self.receive_task = asyncio.create_task(self._receive_loop())
            
            # Check if this is a reconnection with a recovered session
            is_reconnection = self.reconnect_count > 0
            is_session_recovery = is_reconnection and (self.session_id is not None or self.conversation_id is not None)
            
            # Send session recovery notification if applicable
            if is_session_recovery:
                # Create a system message to notify the user about session recovery
                recovery_message = {
                    "type": MessageType.SYSTEM,
                    "payload": {
                        "content": f"Session recovered successfully. Reconnected to previous conversation.",
                        "level": "info",
                        "is_recovery": True,
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    "message_id": f"recovery-{uuid.uuid4()}"
                }
                
                # Simulate receiving this message to notify the user
                if self.on_message:
                    logger.info("Sending session recovery notification to user")
                    self.on_message(Message.from_dict(recovery_message))
            
            # Call the on_connect callback if provided
            if self.on_connect:
                self.on_connect()
                
            return True
            
        except ConnectionRefusedError:
            error_msg = f"Connection refused to {self.connection_url}. Is the server running?"
            logger.error(error_msg)
            
            # Call the on_error callback if provided
            if self.on_error:
                self.on_error(error_msg)
                
            return False
        except websockets.exceptions.InvalidStatusCode as e:
            error_msg = f"Invalid status code from {self.connection_url}: {e}"
            logger.error(error_msg)
            
            # Call the on_error callback if provided
            if self.on_error:
                self.on_error(error_msg)
                
            return False
        except (WebSocketException, ConnectionError) as e:
            error_msg = f"Failed to connect to WebSocket server at {self.connection_url}: {e}"
            logger.error(error_msg)
            
            # Call the on_error callback if provided
            if self.on_error:
                self.on_error(error_msg)
                
            return False
        except asyncio.TimeoutError:
            error_msg = f"Connection timeout to {self.connection_url}"
            logger.error(error_msg)
            
            # Call the on_error callback if provided
            if self.on_error:
                self.on_error(error_msg)
                
            return False
        except Exception as e:
            error_msg = f"Unexpected error connecting to WebSocket server at {self.connection_url}: {e}"
            logger.error(error_msg, exc_info=True)
            
            # Call the on_error callback if provided
            if self.on_error:
                self.on_error(error_msg)
                
            return False
    
    def stop_reconnection(self) -> None:
        """Stop any automatic reconnection attempts."""
        self.should_attempt_reconnect = False
        logger.info("Automatic reconnection has been disabled")
        
        # Cancel any ongoing reconnection task
        if self.reconnect_task and not self.reconnect_task.done():
            self.reconnect_task.cancel()
            logger.info("Cancelled ongoing reconnection task")
    
    def enable_reconnection(self) -> None:
        """Enable automatic reconnection attempts."""
        self.should_attempt_reconnect = True
        logger.info("Automatic reconnection has been enabled")
    
    async def disconnect(self, clear_session: bool = False) -> None:
        """Disconnect from the WebSocket server.
        
        Args:
            clear_session: If True, clear all session data. If False, preserve session data for reconnection.
        """
        if not self.connected and not self.websocket:
            if clear_session:
                self.clear_session_data()
            return
            
        logger.info(f"Disconnecting from WebSocket server (clear_session={clear_session})")
        
        # Save session data before disconnecting (if not clearing)
        if not clear_session:
            self._save_session()
        
        # Cancel the heartbeat and receive tasks
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            
        if self.receive_task:
            self.receive_task.cancel()
            
        # Close the WebSocket connection
        try:
            await self.websocket.close()
        except WebSocketException as e:
            logger.error(f"Error closing WebSocket connection: {e}")
            
        self.connected = False
        self.websocket = None
        
        # Clear session data if requested
        if clear_session:
            self.clear_session_data()
        
        # Call the on_disconnect callback if provided
        if self.on_disconnect:
            self.on_disconnect()
    
    async def reconnect(self, attempt: int = 0) -> bool:
        """
        Attempt to reconnect to the WebSocket server.
        
        Args:
            attempt: The current reconnection attempt number
            
        Returns:
            True if the reconnection was successful, False otherwise
        """
        # Check if reconnection is allowed
        if not self.should_attempt_reconnect:
            logger.info("Reconnection is disabled, not attempting to reconnect")
            return False
            
        # Check if we're already in the process of reconnecting
        if self.is_reconnecting:
            logger.info("Already attempting to reconnect, not starting another reconnection")
            return False
            
        # Check if we've reached the maximum number of attempts
        if attempt >= WS_RECONNECT_MAX_ATTEMPTS:
            logger.error("Maximum reconnection attempts reached")
            self.is_reconnecting = False
            return False
            
        try:
            # Set reconnection state
            self.is_reconnecting = True
            
            # Update reconnection tracking
            self.reconnect_count += 1
            self.last_reconnect_time = datetime.utcnow()
            
            # Save session data before reconnecting
            self._save_session()
            
            # Calculate the delay with exponential backoff and jitter
            delay = (WS_RECONNECT_BASE_DELAY * (2 ** attempt)) + (random.random() * 0.5)
            
            logger.info(f"Reconnecting in {delay:.1f} seconds (attempt {attempt + 1}/{WS_RECONNECT_MAX_ATTEMPTS})")
            logger.info(f"Using session_id: {self.session_id}, conversation_id: {self.conversation_id}")
            
            # Wait for the delay
            await asyncio.sleep(delay)
            
            # Check if reconnection was cancelled during the delay
            if not self.should_attempt_reconnect:
                logger.info("Reconnection was cancelled during delay")
                self.is_reconnecting = False
                return False
            
            # Construct URL with session information if available
            reconnect_url = self.connection_url
            if self.session_id:
                # Add session_id as a query parameter for reconnection
                if '?' in reconnect_url:
                    reconnect_url += f"&session_id={self.session_id}"
                else:
                    reconnect_url += f"?session_id={self.session_id}"
                logger.info(f"Reconnecting with session_id: {self.session_id}")
            
            # Store original URL
            original_url = self.connection_url
            
            # Use the reconnect URL temporarily
            self.connection_url = reconnect_url
            
            # Attempt to reconnect
            success = await self.connect()
            
            # Restore original URL
            self.connection_url = original_url
            
            if success:
                logger.info(f"Reconnection successful (attempt {attempt + 1})")
                # Save updated session data after successful reconnection
                self._save_session()
                self.is_reconnecting = False
                return True
            else:
                # If the reconnection failed, try again
                logger.warning(f"Reconnection failed (attempt {attempt + 1})")
                return await self.reconnect(attempt + 1)
                
        except asyncio.CancelledError:
            logger.info("Reconnection task was cancelled")
            self.is_reconnecting = False
            raise
        except Exception as e:
            logger.error(f"Error during reconnection: {e}", exc_info=True)
            self.is_reconnecting = False
            return False
    
    async def send_message(self, message: Message) -> None:
        """
        Send a message to the WebSocket server.
        
        Args:
            message: The message to send
        """
        if not self.connected or not self.websocket:
            logger.error("Cannot send message: not connected to WebSocket server")
            return
            
        try:
            # Ensure proper JSON serialization
            message_json = message.to_json()
            await self.websocket.send(message_json)
            
            # Log the message details for debugging
            logger.debug(f"Sent message: {message.to_dict()}")
            logger.debug(f"Outgoing message type: {message.type}, agent_id: {self.agent_id}, conversation_id: {self.conversation_id}")
            
            # Verify the message was sent as valid JSON
            try:
                # This is just a validation check, not actually needed for sending
                json.loads(message_json)
            except json.JSONDecodeError:
                logger.warning(f"Warning: Sent message is not valid JSON: {message_json}")
                # Continue anyway since the message was already sent
        except WebSocketException as e:
            logger.error(f"Error sending message: {e}")
            if self.on_error:
                self.on_error(str(e))
    
    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeat messages to keep the connection alive."""
        while self.connected and self.websocket:
            try:
                # Send a ping to keep the connection alive
                await self.websocket.ping()
                # logger.debug("Sent heartbeat ping")
                
                # Wait for the heartbeat interval
                await asyncio.sleep(WS_HEARTBEAT_INTERVAL)
                
            except asyncio.CancelledError:
                # Task was cancelled, exit gracefully
                logger.debug("Heartbeat loop cancelled")
                break
                
            except WebSocketException as e:
                logger.error(f"Heartbeat error: {e}")
                
                # Attempt to reconnect if auto_reconnect is enabled
                if self.auto_reconnect and self.should_attempt_reconnect:
                    logger.info("Auto-reconnect is enabled, attempting to reconnect after heartbeat error...")
                    self.reconnect_task = asyncio.create_task(self.reconnect())
                else:
                    logger.info("Auto-reconnect is disabled or reconnection was stopped")
                break
    
    async def _receive_loop(self) -> None:
        """Receive and process messages from the WebSocket server."""
        while self.connected and self.websocket:
            try:
                # Receive a message with timeout
                try:
                    # Add a reasonable timeout for receiving messages
                    message_json = await asyncio.wait_for(self.websocket.recv(), timeout=30)
                    logger.debug(f"Received raw message: {message_json}")
                    
                    # Add more detailed logging for message inspection
                    try:
                        raw_data = json.loads(message_json)
                        logger.info(f"Raw message keys: {list(raw_data.keys())}")
                        if 'type' in raw_data:
                            logger.info(f"Raw message type: '{raw_data['type']}'")
                        else:
                            logger.warning("No 'type' field found in raw message")
                            
                        # Log payload structure if present
                        if 'payload' in raw_data:
                            logger.info(f"Payload keys: {list(raw_data['payload'].keys()) if isinstance(raw_data['payload'], dict) else 'Not a dict'}")
                        elif 'text' in raw_data:
                            logger.info(f"Message has 'text' field instead of 'payload': {raw_data['text'][:50]}...")
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse raw message for inspection: {e}")
                    except Exception as e:
                        logger.error(f"Error inspecting raw message: {e}")
                        
                    # Parse the message
                    try:
                        message = parse_message_from_json(message_json)
                        
                        # Extract and save session information
                        if message.type == MessageType.CHAT and "conversation_id" in message.payload:
                            self.conversation_id = message.payload["conversation_id"]
                            logger.info(f"Updated conversation_id: {self.conversation_id}")
                            self._save_session()
                            
                        # Check for session_id in system messages
                        if message.type == MessageType.SYSTEM and isinstance(message.payload, dict):
                            if "session_id" in message.payload:
                                self.session_id = message.payload["session_id"]
                                logger.info(f"Updated session_id from system message: {self.session_id}")
                                self._save_session()
                        
                        # Also check for session_id and scene_id in narrative messages
                        if message.type == MessageType.NARRATIVE and isinstance(message.payload, dict):
                            if "session_id" in message.payload:
                                self.session_id = message.payload["session_id"]
                                logger.info(f"Updated session_id from narrative: {self.session_id}")
                                self._save_session()
                            
                            # Log scene information if available
                            if "scene_id" in message.payload:
                                scene_id = message.payload['scene_id']
                                logger.info(f"Narrative message for scene: {scene_id}")
                                # Extract additional scene information if available
                                if isinstance(message.payload, dict):
                                    scene_info = message.payload.get('scene_info', {})
                                    if scene_info:
                                        logger.info(f"Scene info: {scene_info}")
                        
                        # Log detailed message information
                        logger.info(f"RECEIVED MESSAGE: type={message.type}, message_id={message.message_id}")
                        
                        logger.debug(f"Message payload: {message.payload}")
                        
                        # Call the on_message callback if provided
                        if self.on_message:
                            self.on_message(message)
                        else:
                            logger.warning(f"No message handler registered for message: type={message.type}, message_id={message.message_id}")
                            
                    except json.JSONDecodeError as e:
                        logger.error(f"Error parsing message: {e}")
                        continue
                except asyncio.TimeoutError:
                    # Just log and continue if we timeout waiting for a message
                    logger.debug("No message received within timeout period, continuing...")
                    continue
                        
            except asyncio.CancelledError:
                # Task was cancelled, exit gracefully
                break
                
            except ConnectionClosed as e:
                logger.error(f"WebSocket connection closed: {e}")
                
                # Call the on_disconnect callback if provided
                if self.on_disconnect:
                    self.on_disconnect()
                
                # Attempt to reconnect if auto_reconnect is enabled
                if self.auto_reconnect and self.should_attempt_reconnect:
                    logger.info("Auto-reconnect is enabled, attempting to reconnect...")
                    self.reconnect_task = asyncio.create_task(self.reconnect())
                else:
                    logger.info("Auto-reconnect is disabled or reconnection was stopped")
                break
                
            except WebSocketException as e:
                logger.error(f"WebSocket error: {e}")
                
                # Call the on_error callback if provided
                if self.on_error:
                    self.on_error(str(e))
                
                # Attempt to reconnect if auto_reconnect is enabled
                if self.auto_reconnect and self.should_attempt_reconnect:
                    logger.info("Auto-reconnect is enabled, attempting to reconnect after error...")
                    self.reconnect_task = asyncio.create_task(self.reconnect())
                else:
                    logger.info("Auto-reconnect is disabled or reconnection was stopped")
                break
