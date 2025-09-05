"""
Main application screen for the Spy Agency CLI application.

This module contains the MainScreen class, which integrates all the widgets
and manages the application state.
"""

import asyncio
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Footer, Header, Static

from src.client.config import DEFAULT_AGENT_ID, DEFAULT_AGENT_NAME, DEFAULT_SCENARIO, SERVER_URL, WS_GAME_ENDPOINT
from src.client.logger import logger
from src.client.websocket.client import WebSocketClient
from src.client.websocket.message_handler import MessageHandler
from src.client.websocket.protocol import (
    ChatMessage,
    Message,
    MessageType,
    NarrativeMessage,
    OutgoingMessage,
    SystemMessage,
    TypingMessage,
)
from src.client.widgets.chat_window import ChatWindow
from src.client.widgets.input_bar import InputBar


class MainScreen(Screen):
    """
    Main application screen.
    
    This screen integrates all the widgets and manages the application state.
    """
    
    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
        ("ctrl+r", "reconnect", "Reconnect"),
    ]
    
    def __init__(self, *args, **kwargs):
        """
        Initialize the main screen.
        
        Args:
            *args: Additional positional arguments for the parent class
            **kwargs: Additional keyword arguments for the parent class
        """
        super().__init__(*args, **kwargs)
        self.agent_id = DEFAULT_AGENT_ID
        self.agent_name = DEFAULT_AGENT_NAME
        self.ws_client: Optional[WebSocketClient] = None
        self.message_handler: Optional[MessageHandler] = None
        self.connected = False
        self.is_exiting = False
        
    def compose(self) -> ComposeResult:
        """Define the components of the main screen."""
        # Create the header
        yield Header(show_clock=True)
        
        # Create the main container
        with Container(id="main-screen"):
            # Create the chat window
            self.chat_window = ChatWindow()
            yield self.chat_window
            
            # Create the input bar
            self.input_bar = InputBar(
                on_submit=self.on_message_submitted,
                placeholder="Type a message...",
            )
            yield self.input_bar
            
        # Create the footer
        yield Footer()
        
        # Create the status bar
        yield Static("Disconnected", id="status-bar")
        
    def on_mount(self) -> None:
        """Handle the mount event."""
        logger.info("MAIN SCREEN: Application screen mounted and initialized")
        logger.info(f"Using default agent_id={self.agent_id} and agent_name={self.agent_name}")
        
        # Connect to the WebSocket server
        logger.info("Initiating WebSocket connection on application startup")
        self.connect_to_agent(self.agent_id)
        
    def action_quit(self) -> None:
        """Quit the application."""
        logger.info("MAIN SCREEN: User initiated application shutdown")
        
        # Set the exiting flag to prevent UI updates during shutdown
        self.is_exiting = True
        logger.debug("Set is_exiting flag to prevent UI updates during shutdown")
        
        # Disconnect from the WebSocket server
        if self.ws_client:
            logger.info(f"Disconnecting WebSocket client for agent_id={self.agent_id} before shutdown")
            asyncio.create_task(self.ws_client.disconnect())
            logger.debug("WebSocket disconnect task created for clean shutdown")
        else:
            logger.debug("No active WebSocket client to disconnect during shutdown")
            
        # Exit the application
        logger.info("Exiting application")
        self.app.exit()
        
    def action_reconnect(self) -> None:
        """Reconnect to the WebSocket server."""
        logger.info("MAIN SCREEN: User initiated reconnection to WebSocket server")
        
        # Disconnect from the WebSocket server
        if self.ws_client:
            logger.info(f"Disconnecting existing WebSocket connection for agent_id={self.agent_id}")
            asyncio.create_task(self.ws_client.disconnect())
            logger.debug("Disconnect task created and running asynchronously")
        else:
            logger.warning("No active WebSocket client to disconnect")
            
        # Add a system message about reconnection
        logger.info("Adding system message about reconnection attempt")
        self.chat_window.add_system_message("Reconnecting to server...")
            
        # Connect to the WebSocket server with the default agent ID
        logger.info(f"Initiating new connection with default agent_id={DEFAULT_AGENT_ID}")
        self.connect_to_agent(DEFAULT_AGENT_ID)
        
    def on_message_submitted(self, message: str) -> None:
        """
        Handle message submission events.
        
        Args:
            message: The submitted message
        """
        logger.info(f"MAIN SCREEN: User submitted message: '{message[:30]}...' (truncated)")
        
        if not message.strip():
            logger.debug("Empty message submitted, ignoring")
            return
            
        if not self.connected:
            logger.warning("Cannot send message: WebSocket not connected")
            logger.info("Adding error message to chat window about connection status")
            self.chat_window.add_error_message(
                "Not connected to the server. Please try again later."
            )
            return
            
        # Add the message to the chat window
        logger.info("Adding user message to chat window")
        self.chat_window.add_user_message(message)
        
        # Send the message to the WebSocket server
        if self.ws_client:
            logger.info(f"Creating outgoing message for agent_id={self.agent_id}")
            outgoing_message = OutgoingMessage(
                type=MessageType.CHAT,
                payload={
                    "content": message,
                    "agent_id": self.agent_id,
                },
            )
            
            logger.info(f"MAIN SCREEN: Sending message: type={outgoing_message.type}, message_id={outgoing_message.message_id}")
            logger.debug(f"Outgoing message payload: {outgoing_message.payload}")
            
            logger.info("Creating async task to send message")
            asyncio.create_task(self.ws_client.send_message(outgoing_message))
            logger.debug("Async send task created and running")
        else:
            logger.error("WebSocket client is None despite connection status being true")
            
    def connect_to_agent(self, agent_id: str) -> None:
        """
        Connect to an agent.
        
        Args:
            agent_id: The ID of the agent to connect to
        """
        logger.info(f"MAIN SCREEN: Initiating connection to agent: {agent_id}")
        
        # Update the status bar
        status_bar = self.query_one("#status-bar", Static)
        status_bar.update("Connecting...")
        logger.debug("Updated status bar to 'Connecting...'")
        
        # Disable the input bar
        self.input_bar.disable()
        logger.debug("Disabled input bar during connection attempt")
        
        # Create the message handler
        logger.info("Creating message handler and registering message type handlers")
        self.message_handler = MessageHandler()
        
        # Register message handlers
        logger.debug("Registering CHAT message handler")
        self.message_handler.register_handler(
            MessageType.CHAT, self.handle_chat_message
        )
        
        logger.debug("Registering SYSTEM message handler")
        self.message_handler.register_handler(
            MessageType.SYSTEM, self.handle_system_message
        )
        
        logger.debug("Registering TYPING message handler")
        self.message_handler.register_handler(
            MessageType.TYPING, self.handle_typing_message
        )
        
        logger.debug("Registering ERROR message handler")
        self.message_handler.register_handler(
            MessageType.ERROR, self.handle_error_message
        )
        
        logger.debug("Registering NARRATIVE message handler")
        self.message_handler.register_handler(
            MessageType.NARRATIVE, self.handle_narrative_message
        )
        
        logger.debug("Registering FUNCTION message handler")
        self.message_handler.register_handler(
            MessageType.FUNCTION, self.handle_function_message
        )
        
        logger.debug("Registering NPC_SPEAK message handler")
        self.message_handler.register_handler(
            MessageType.NPC_SPEAK, self.handle_npc_speak_message
        )
        
        # Create the WebSocket client
        # Backend expects /ws/play?scenario=<scenario_name>
        ws_url = f"{SERVER_URL}/ws/{WS_GAME_ENDPOINT}?scenario={DEFAULT_SCENARIO}"
        logger.info(f"MAIN SCREEN: Connecting to WebSocket URL: {ws_url} with scenario: {DEFAULT_SCENARIO}")
        
        logger.info("Creating WebSocket client instance")
        self.ws_client = WebSocketClient(
            server_url=ws_url,
            agent_id=agent_id,
            on_message=self.message_handler.handle_message,
            on_connect=self.on_connect,
            on_disconnect=self.on_disconnect,
            on_error=self.on_error,
        )
        
        # Log WebSocket connection attempt
        logger.info(f"MAIN SCREEN: Starting WebSocket connection task for agent: {agent_id}")
        asyncio.create_task(self.ws_client.connect())
        logger.debug("WebSocket connection task created and running asynchronously")
        
    def on_connect(self) -> None:
        """Handle WebSocket connection events."""
        self.connected = True
        logger.info(f"MAIN SCREEN: WebSocket connected to game engine with agent_id={self.agent_id}")
        logger.info(f"Connection established successfully, ready to receive messages")
        
        # Update the status bar
        status_bar = self.query_one("#status-bar", Static)
        status_bar.update("Connected to game engine")
        logger.debug("Updated status bar to 'Connected to game engine'")
        
        # Enable the input bar
        self.input_bar.enable()
        logger.debug("Enabled input bar for user messages")
        
        # Add a system message
        logger.info("Adding system connection message to chat window")
        self.chat_window.add_system_message(
            "Connected to game engine. Type a message to begin."
        )
        
    def on_disconnect(self) -> None:
        """Handle WebSocket disconnection events."""
        self.connected = False
        logger.info(f"MAIN SCREEN: WebSocket disconnected from game engine")
        
        # Skip UI updates if the application is exiting
        if self.is_exiting:
            logger.info("Application is exiting, skipping disconnect UI updates")
            return
            
        try:
            # Update the status bar
            logger.info("Updating UI components for disconnection")
            status_bar = self.query_one("#status-bar", Static)
            status_bar.update("Disconnected")
            logger.debug("Updated status bar to 'Disconnected'")
            
            # Disable the input bar
            self.input_bar.disable()
            logger.debug("Disabled input bar due to disconnection")
            
            # Add a system message
            logger.info("Adding system disconnection message to chat window")
            self.chat_window.add_system_message(
                "Disconnected from the server. Attempting to reconnect..."
            )
        except Exception as e:
            # Log any errors during disconnect but don't crash
            logger.error(f"Error during disconnect UI update: {e}", exc_info=True)
            pass
        
    def on_error(self, error: str) -> None:
        """
        Handle WebSocket error events.
        
        Args:
            error: The error message
        """
        # Log the error
        logger.error(f"MAIN SCREEN: WebSocket error with agent {self.agent_id}: {error}")
        logger.error(f"Connection status at time of error: {self.connected}")
        
        # Add an error message to the chat window
        logger.info("Adding WebSocket error message to chat window")
        self.chat_window.add_error_message(f"Error: {error}")
        
        # Update the status bar to reflect the error state
        try:
            status_bar = self.query_one("#status-bar", Static)
            status_bar.update("Connection Error")
            logger.debug("Updated status bar to 'Connection Error'")
        except Exception as e:
            logger.error(f"Failed to update status bar: {e}")
        
    def handle_chat_message(self, message: ChatMessage) -> None:
        """
        Handle chat messages.
        
        Args:
            message: The chat message
        """
        # Log the chat message
        logger.info(f"MAIN SCREEN: Handling chat message: message_id={message.message_id}")
        logger.debug(f"Chat message payload: {message.payload}")
        
        # Add the message to the chat window
        logger.info(f"Forwarding chat message to chat window: message_id={message.message_id}")
        self.chat_window.handle_websocket_message(message)
        
    def handle_system_message(self, message: SystemMessage) -> None:
        """
        Handle system messages.
        
        Args:
            message: The system message
        """
        # Log the system message
        logger.info(f"MAIN SCREEN: Handling system message: message_id={message.message_id}")
        logger.debug(f"System message payload: {message.payload}")
        
        # Add the message to the chat window
        logger.info(f"Forwarding system message to chat window: message_id={message.message_id}")
        self.chat_window.handle_websocket_message(message)
        
    def handle_typing_message(self, message: TypingMessage) -> None:
        """
        Handle typing messages.
        
        Args:
            message: The typing message
        """
        # Log the typing message
        logger.info(f"MAIN SCREEN: Handling typing message: message_id={message.message_id}")
        logger.debug(f"Typing message payload: {message.payload}")
        
        # Add the message to the chat window
        logger.info(f"Forwarding typing message to chat window: message_id={message.message_id}")
        self.chat_window.handle_websocket_message(message)
        
    def handle_error_message(self, message: SystemMessage) -> None:
        """
        Handle error messages.
        
        Args:
            message: The error message
        """
        # Log the error message
        logger.error(f"MAIN SCREEN: Handling error message: message_id={message.message_id}")
        logger.error(f"Error message payload: {message.payload}")
        
        # Add the message to the chat window
        logger.info(f"Forwarding error message to chat window: message_id={message.message_id}")
        self.chat_window.handle_websocket_message(message)
        
    def handle_narrative_message(self, message: NarrativeMessage) -> None:
        """
        Handle narrative messages.
        
        Args:
            message: The narrative message
        """
        # Log the narrative message
        logger.info(f"MAIN SCREEN: Handling narrative message: message_id={message.message_id}")
        logger.debug(f"Narrative message payload: {message.payload}")
        
        # Add the message to the chat window
        logger.info(f"Forwarding narrative message to chat window: message_id={message.message_id}")
        self.chat_window.handle_websocket_message(message)
        
    def handle_npc_speak_message(self, message: Message) -> None:
        """
        Handle NPC speak messages.
        
        Args:
            message: The NPC speak message
        """
        # Log the NPC speak message
        logger.info(f"MAIN SCREEN: Handling NPC speak message: message_id={message.message_id}")
        logger.debug(f"NPC speak message payload: {message.payload}")
        
        # Extract NPC name and text
        npc_name = message.payload.get("name", "NPC")
        npc_text = message.payload.get("text", "")
        
        logger.info(f"NPC {npc_name} says: {npc_text[:50]}...")
        
        # Create a chat message to display in the chat window
        chat_message = ChatMessage.from_dict({
            "type": MessageType.CHAT,
            "payload": {
                "content": npc_text,
                "sender": f"[NPC] {npc_name}",
                "format": "markdown"
            },
            "message_id": message.message_id
        })
        
        # Add the message to the chat window
        logger.info(f"Forwarding NPC speak message as chat message to chat window: message_id={message.message_id}")
        self.chat_window.handle_websocket_message(chat_message)
        
    def handle_function_message(self, message: Message) -> None:
        """
        Handle function call messages from the AI agent.
        
        Args:
            message: The function message
        """
        # Log the function message
        logger.info(f"MAIN SCREEN: Handling function message: message_id={message.message_id}")
        logger.debug(f"Function message payload: {message.payload}")
        
        # Extract function name and parameters
        function_name = None
        parameters = {}
        
        if isinstance(message.payload, dict):
            function_name = message.payload.get('name')
            parameters = message.payload.get('parameters', {})
            
        logger.info(f"Function call: {function_name} with parameters: {parameters}")
        
        # Check for invalid function calls
        if function_name == "describe_scene":
            scene_id = parameters.get('id', '')
            # List of valid scene IDs - should match the list in tools.py
            valid_scene_ids = ["arrival", "safehouse", "embassy", "market", "alley", "hotel"]
            
            # Check if the scene ID is valid
            if not any(valid_id in scene_id.lower() for valid_id in valid_scene_ids):
                logger.warning(f"Invalid scene ID in function call: {scene_id}")
                system_message = f"AI attempted to describe an invalid scene: '{scene_id}'" 
                self.chat_window.add_system_message(system_message, is_error=True)
                return
        
        # Add a system message to the chat window about the function call
        params_str = ', '.join([f'{k}="{v}"' for k, v in parameters.items()])
        system_message = f"AI is calling function: {function_name}({params_str})" 
        self.chat_window.add_system_message(system_message)
