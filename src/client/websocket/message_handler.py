"""
Message handler for processing WebSocket messages in the Spy Agency CLI application.

This module contains the logic for processing different types of messages
received from the WebSocket server and routing them to the appropriate handlers.
"""

import asyncio
from typing import Any, Callable, Dict, List, Optional, Union

from src.client.logger import logger
from src.client.websocket.protocol import (
    AckMessage,
    AgentsMessage,
    ChatMessage,
    ErrorMessage,
    Message,
    MessageType,
    MissionMessage,
    StreamMessage,
    SystemMessage,
    TypingMessage,
)


class MessageHandler:
    """
    Handler for processing WebSocket messages.
    
    This class routes messages to the appropriate handlers based on their type.
    """
    
    def __init__(self):
        """Initialize a new message handler."""
        self.handlers: Dict[MessageType, List[Callable[[Message], None]]] = {
            MessageType.CHAT: [],
            MessageType.SYSTEM: [],
            MessageType.TYPING: [],
            MessageType.MISSION: [],
            MessageType.AGENTS: [],
            MessageType.STREAM: [],
            MessageType.ERROR: [],
            MessageType.ACK: [],
            MessageType.FUNCTION: [],
            MessageType.NPC_SPEAK: [],
        }
        
    def register_handler(self, message_type: MessageType, handler: Callable[[Message], None]) -> None:
        """
        Register a handler for a specific message type.
        
        Args:
            message_type: The type of message to handle
            handler: The handler function to call when a message of this type is received
        """
        if message_type not in self.handlers:
            self.handlers[message_type] = []
            
        self.handlers[message_type].append(handler)
        
    def unregister_handler(self, message_type: MessageType, handler: Callable[[Message], None]) -> None:
        """
        Unregister a handler for a specific message type.
        
        Args:
            message_type: The type of message to handle
            handler: The handler function to remove
        """
        if message_type in self.handlers and handler in self.handlers[message_type]:
            self.handlers[message_type].remove(handler)
            
    def handle_message(self, message: Message) -> None:
        """
        Handle a message by routing it to the appropriate handlers.
        
        Args:
            message: The message to handle
        """
        if message.type not in self.handlers:
            logger.warning(f"No handlers registered for message type: {message.type}")
            return
        
        logger.info(f"PROCESSING MESSAGE: type={message.type}, message_id={message.message_id}")
        logger.debug(f"Message payload: {message.payload}")
        
        handler_count = len(self.handlers[message.type])
        logger.info(f"Found {handler_count} handler(s) for message type: {message.type}")
        
        for i, handler in enumerate(self.handlers[message.type]):
            try:
                logger.info(f"Executing handler {i+1}/{handler_count} for message type: {message.type}")
                handler(message)
                logger.info(f"Handler {i+1}/{handler_count} completed successfully")
            except Exception as e:
                logger.error(f"Error in message handler {i+1}/{handler_count}: {e}", exc_info=True)
                
    def handle_chat_message(self, message: ChatMessage) -> None:
        """
        Handle a chat message from the agent.
        
        Args:
            message: The chat message to handle
        """
        for handler in self.handlers[MessageType.CHAT]:
            try:
                handler(message)
            except Exception as e:
                logger.error(f"Error in chat message handler: {e}")
                
    def handle_system_message(self, message: SystemMessage) -> None:
        """
        Handle a system message.
        
        Args:
            message: The system message to handle
        """
        for handler in self.handlers[MessageType.SYSTEM]:
            try:
                handler(message)
            except Exception as e:
                logger.error(f"Error in system message handler: {e}")
                
    def handle_typing_message(self, message: TypingMessage) -> None:
        """
        Handle a typing indicator message.
        
        Args:
            message: The typing message to handle
        """
        for handler in self.handlers[MessageType.TYPING]:
            try:
                handler(message)
            except Exception as e:
                logger.error(f"Error in typing message handler: {e}")
                
    def handle_mission_message(self, message: MissionMessage) -> None:
        """
        Handle a mission update message.
        
        Args:
            message: The mission message to handle
        """
        for handler in self.handlers[MessageType.MISSION]:
            try:
                handler(message)
            except Exception as e:
                logger.error(f"Error in mission message handler: {e}")
                
    def handle_agents_message(self, message: AgentsMessage) -> None:
        """
        Handle an agents message.
        
        Args:
            message: The agents message to handle
        """
        for handler in self.handlers[MessageType.AGENTS]:
            try:
                handler(message)
            except Exception as e:
                logger.error(f"Error in agents message handler: {e}")
                
    def handle_stream_message(self, message: StreamMessage) -> None:
        """
        Handle a streaming message.
        
        Args:
            message: The stream message to handle
        """
        for handler in self.handlers[MessageType.STREAM]:
            try:
                handler(message)
            except Exception as e:
                logger.error(f"Error in stream message handler: {e}")
                
    def handle_error_message(self, message: ErrorMessage) -> None:
        """
        Handle an error message.
        
        Args:
            message: The error message to handle
        """
        for handler in self.handlers[MessageType.ERROR]:
            try:
                handler(message)
            except Exception as e:
                logger.error(f"Error in error message handler: {e}")
                
    def handle_ack_message(self, message: AckMessage) -> None:
        """
        Handle an acknowledgment message.
        
        Args:
            message: The acknowledgment message to handle
        """
        for handler in self.handlers[MessageType.ACK]:
            try:
                handler(message)
            except Exception as e:
                logger.error(f"Error in ack message handler: {e}")
                
    def handle_function_message(self, message: Message) -> None:
        """
        Handle a function call message from the AI agent.
        
        Args:
            message: The function message to handle
        """
        logger.info(f"Handling function message: {message.message_id}")
        logger.debug(f"Function message payload: {message.payload}")
        
        for handler in self.handlers[MessageType.FUNCTION]:
            try:
                handler(message)
            except Exception as e:
                logger.error(f"Error in function message handler: {e}")
                
    def handle_npc_speak_message(self, message: Message) -> None:
        """
        Handle a message from an NPC character.
        
        Args:
            message: The NPC speak message to handle
        """
        logger.info(f"Handling NPC speak message: {message.message_id}")
        logger.debug(f"NPC speak message payload: {message.payload}")
        
        for handler in self.handlers[MessageType.NPC_SPEAK]:
            try:
                handler(message)
            except Exception as e:
                logger.error(f"Error in NPC speak message handler: {e}")
