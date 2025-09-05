"""
WebSocket protocol definitions for the Spy Agency CLI application.

This module defines the message formats and protocol constants used for
communication between the client and server.
"""

import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional


class MessageType(str, Enum):
    """Enum for different types of messages in the WebSocket protocol."""
    CHAT = "chat"
    SYSTEM = "system"
    TYPING = "typing"
    MISSION = "mission"
    AGENTS = "agents"
    STREAM = "stream"
    ERROR = "error"
    COMMAND = "command"
    USER_MESSAGE = "user_message"
    ACK = "ack"
    NARRATIVE = "narrative"
    FUNCTION = "function"
    NPC_SPEAK = "npc_speak"


class SystemMessageLevel(str, Enum):
    """Enum for system message severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    DEBUG = "debug"


class TypingStatus(str, Enum):
    """Enum for typing indicator status."""
    START = "start"
    STOP = "stop"


class StreamStatus(str, Enum):
    """Enum for streaming message status."""
    START = "start"
    CONTINUE = "continue"
    END = "end"


class Message:
    """Base class for all WebSocket messages."""
    
    def __init__(
        self,
        message_type: MessageType,
        payload: Dict[str, Any],
        message_id: Optional[str] = None,
        timestamp: Optional[str] = None,
        client_message_id: Optional[str] = None,
    ):
        """
        Initialize a new message.
        
        Args:
            message_type: The type of message
            payload: The message payload
            message_id: Unique identifier for the message (server-generated)
            timestamp: ISO 8601 formatted timestamp (server-generated)
            client_message_id: Client-generated message ID for tracking
        """
        self.type = message_type
        self.payload = payload
        self.message_id = message_id
        self.timestamp = timestamp or datetime.now().isoformat()
        self.client_message_id = client_message_id or f"client-{uuid.uuid4()}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the message to a dictionary for JSON serialization."""
        result = {
            "type": self.type,
            "payload": self.payload,
        }
        
        if self.message_id:
            result["message_id"] = self.message_id
            
        if self.timestamp:
            result["timestamp"] = self.timestamp
            
        if self.client_message_id:
            result["client_message_id"] = self.client_message_id
            
        return result
    
    def to_json(self) -> str:
        """Convert the message to a JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create a message from a dictionary."""
        return cls(
            message_type=data["type"],
            payload=data["payload"],
            message_id=data.get("message_id"),
            timestamp=data.get("timestamp"),
            client_message_id=data.get("client_message_id"),
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        """Create a message from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)


class OutgoingMessage(Message):
    """Generic message sent from the client to the server."""
    
    def __init__(
        self,
        type: MessageType,
        payload: Dict[str, Any],
        client_message_id: Optional[str] = None,
    ):
        """
        Initialize a new outgoing message.
        
        Args:
            type: The type of message
            payload: The message payload
            client_message_id: Client-generated message ID for tracking
        """
        super().__init__(
            message_type=type,
            payload=payload,
            client_message_id=client_message_id,
        )


class UserMessage(Message):
    """Message sent from the user to the agent."""
    
    def __init__(
        self,
        content: str,
        agent_id: str,
        conversation_id: Optional[str] = None,
        client_message_id: Optional[str] = None,
    ):
        """
        Initialize a new user message.
        
        Args:
            content: The message content
            agent_id: The ID of the agent to send the message to
            conversation_id: The ID of the conversation
            client_message_id: Client-generated message ID for tracking
        """
        payload = {
            "content": content,
            "agent_id": agent_id,
            "metadata": {
                "client_timestamp": datetime.now().isoformat(),
                "client_info": {
                    "version": "1.0.0",
                    "platform": "terminal"
                }
            }
        }
        
        if conversation_id:
            payload["conversation_id"] = conversation_id
            
        super().__init__(
            message_type=MessageType.USER_MESSAGE,
            payload=payload,
            client_message_id=client_message_id,
        )


class CommandMessage(Message):
    """Command message sent from the client to the server."""
    
    def __init__(
        self,
        command: str,
        parameters: Dict[str, Any],
        client_message_id: Optional[str] = None,
    ):
        """
        Initialize a new command message.
        
        Args:
            command: The command to execute
            parameters: Parameters for the command
            client_message_id: Client-generated message ID for tracking
        """
        payload = {
            "command": command,
            "parameters": parameters,
        }
        
        super().__init__(
            message_type=MessageType.COMMAND,
            payload=payload,
            client_message_id=client_message_id,
        )


class ChatMessage(Message):
    """Chat message received from the agent."""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatMessage':
        """Create a chat message from a dictionary."""
        if data["type"] != MessageType.CHAT:
            raise ValueError(f"Expected message type {MessageType.CHAT}, got {data['type']}")
        
        return super().from_dict(data)


class SystemMessage(Message):
    """System message for notifications about the system state."""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SystemMessage':
        """Create a system message from a dictionary."""
        from src.client.logger import logger
        
        logger.debug(f"SystemMessage.from_dict called with data: {data}")
        
        try:
            if data["type"] != MessageType.SYSTEM:
                logger.error(f"Type mismatch in SystemMessage.from_dict: expected {MessageType.SYSTEM}, got {data['type']}")
                raise ValueError(f"Expected message type {MessageType.SYSTEM}, got {data['type']}")
            
            # Handle different system message formats
            # Format 1: {"type":"system","text":"Message content"}
            # Format 2: {"type":"system","payload":{"content":"Message content", "level":"info"}}
            
            # If the message has a 'text' field but no 'payload', convert it to the expected format
            if 'text' in data and 'payload' not in data:
                logger.info(f"Converting system message format: found 'text' field: {data['text'][:100]}")
                # Create a payload with the text content
                data['payload'] = {
                    'content': data['text'],
                    'level': 'info'  # Default to info level
                }
                logger.info(f"Converted system message payload: {data['payload']}")
            
            logger.debug(f"SystemMessage payload: {data.get('payload', {})}")
            result = super().from_dict(data)
            logger.debug("SystemMessage created successfully")
            return result
        except KeyError as e:
            logger.error(f"KeyError in SystemMessage.from_dict: {e}")
            logger.error(f"Available keys: {data.keys()}")
            raise
        except Exception as e:
            logger.error(f"Error in SystemMessage.from_dict: {e}")
            raise


class TypingMessage(Message):
    """Typing indicator message."""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TypingMessage':
        """Create a typing message from a dictionary."""
        if data["type"] != MessageType.TYPING:
            raise ValueError(f"Expected message type {MessageType.TYPING}, got {data['type']}")
        
        return super().from_dict(data)


class MissionMessage(Message):
    """Mission update message."""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MissionMessage':
        """Create a mission message from a dictionary."""
        if data["type"] != MessageType.MISSION:
            raise ValueError(f"Expected message type {MessageType.MISSION}, got {data['type']}")
        
        return super().from_dict(data)


class AgentsMessage(Message):
    """Message containing information about available agents."""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentsMessage':
        """Create an agents message from a dictionary."""
        if data["type"] != MessageType.AGENTS:
            raise ValueError(f"Expected message type {MessageType.AGENTS}, got {data['type']}")
        
        return super().from_dict(data)


class StreamMessage(Message):
    """Streaming message for partial responses."""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StreamMessage':
        """Create a stream message from a dictionary."""
        if data["type"] != MessageType.STREAM:
            raise ValueError(f"Expected message type {MessageType.STREAM}, got {data['type']}")
        
        return super().from_dict(data)


class ErrorMessage(Message):
    """Error message from the server."""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ErrorMessage':
        """Create an error message from a dictionary."""
        if data["type"] != MessageType.ERROR:
            raise ValueError(f"Expected message type {MessageType.ERROR}, got {data['type']}")
        
        return super().from_dict(data)


class AckMessage(Message):
    """Acknowledgment message from the server."""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AckMessage':
        """Create an acknowledgment message from a dictionary."""
        if data["type"] != MessageType.ACK:
            raise ValueError(f"Expected message type {MessageType.ACK}, got {data['type']}")
        
        return super().from_dict(data)


class NarrativeMessage(Message):
    """Narrative message containing story content."""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NarrativeMessage':
        """Create a narrative message from a dictionary."""
        from src.client.logger import logger
        
        logger.debug(f"NarrativeMessage.from_dict called with data: {data}")
        
        try:
            if data["type"] != MessageType.NARRATIVE:
                logger.error(f"Type mismatch in NarrativeMessage.from_dict: expected {MessageType.NARRATIVE}, got {data['type']}")
                raise ValueError(f"Expected message type {MessageType.NARRATIVE}, got {data['type']}")
            
            # Handle different narrative message formats
            # Format 1: {"type":"narrative","text":"Narrative content"}
            # Format 2: {"type":"narrative","payload":{"content":"Narrative content", "format":"markdown"}}
            
            # If the message has a 'text' field but no 'payload', convert it to the expected format
            if 'text' in data and 'payload' not in data:
                logger.info(f"Converting narrative message format: found 'text' field: {data['text'][:100]}")
                # Create a payload with the text content
                data['payload'] = {
                    'content': data['text'],
                    'format': 'markdown'  # Default to markdown for better formatting
                }
                logger.info(f"Converted narrative message payload: {data['payload']}")
            
            logger.debug(f"NarrativeMessage payload: {data.get('payload', {})}")
            result = super().from_dict(data)
            logger.debug("NarrativeMessage created successfully")
            return result
        except KeyError as e:
            logger.error(f"KeyError in NarrativeMessage.from_dict: {e}")
            logger.error(f"Available keys: {data.keys()}")
            raise
        except Exception as e:
            logger.error(f"Error in NarrativeMessage.from_dict: {e}")
            raise


class FunctionMessage(Message):
    """Function call message from the AI agent."""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FunctionMessage':
        """Create a function message from a dictionary."""
        from src.client.logger import logger
        
        logger.debug(f"FunctionMessage.from_dict called with data: {data}")
        
        try:
            if data["type"] != MessageType.FUNCTION:
                logger.error(f"Type mismatch in FunctionMessage.from_dict: expected {MessageType.FUNCTION}, got {data['type']}")
                raise ValueError(f"Expected message type {MessageType.FUNCTION}, got {data['type']}")
            
            # Handle function message format
            # Format: {"type":"function","function":{"name":"function_name","parameters":{"param1":"value1"}}}
            # or: {"type":"function","payload":{"name":"function_name","parameters":{"param1":"value1"}}}
            
            # If the message has a 'function' field but no 'payload', convert it to the expected format
            if 'function' in data and 'payload' not in data:
                logger.info(f"Converting function message format: found 'function' field")
                # Create a payload with the function content
                data['payload'] = data['function']
                logger.info(f"Converted function message payload: {data['payload']}")
            
            # If the message has a 'content' field that contains a JSON string with function data
            if 'content' in data and isinstance(data['content'], str) and 'payload' not in data:
                try:
                    # Try to parse the content as JSON
                    content_data = json.loads(data['content'])
                    if isinstance(content_data, dict) and 'function' in content_data:
                        logger.info(f"Found function data in content field: {content_data['function']}")
                        data['payload'] = content_data['function']
                        logger.info(f"Extracted function payload: {data['payload']}")
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse content as JSON: {data['content'][:100]}")
            
            logger.debug(f"FunctionMessage payload: {data.get('payload', {})}")
            result = super().from_dict(data)
            logger.debug("FunctionMessage created successfully")
            return result
        except KeyError as e:
            logger.error(f"KeyError in FunctionMessage.from_dict: {e}")
            logger.error(f"Available keys: {data.keys()}")
            raise
        except Exception as e:
            logger.error(f"Error in FunctionMessage.from_dict: {e}")
            raise


class NPCSpeakMessage(Message):
    """Message from an NPC character."""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NPCSpeakMessage':
        """Create an NPC speak message from a dictionary."""
        from src.client.logger import logger
        
        logger.debug(f"NPCSpeakMessage.from_dict called with data: {data}")
        
        try:
            if data["type"] != MessageType.NPC_SPEAK:
                logger.error(f"Type mismatch in NPCSpeakMessage.from_dict: expected {MessageType.NPC_SPEAK}, got {data['type']}")
                raise ValueError(f"Expected message type {MessageType.NPC_SPEAK}, got {data['type']}")
            
            # Handle NPC message format
            # Format: {"type":"npc_speak","name":"NPC Name","text":"NPC dialogue"}
            
            # If the message has direct fields but no 'payload', convert it to the expected format
            if 'name' in data and 'text' in data and 'payload' not in data:
                logger.info(f"Converting NPC message format: found direct fields")
                # Create a payload with the NPC content
                data['payload'] = {
                    'name': data['name'],
                    'text': data['text'],
                    'npc_id': data.get('npc_id', data['name'].lower()),
                    'format': 'markdown'  # Default to markdown for better formatting
                }
                logger.info(f"Converted NPC message payload: {data['payload']}")
            
            logger.debug(f"NPCSpeakMessage payload: {data.get('payload', {})}")
            result = super().from_dict(data)
            logger.debug("NPCSpeakMessage created successfully")
            return result
        except KeyError as e:
            logger.error(f"KeyError in NPCSpeakMessage.from_dict: {e}")
            logger.error(f"Available keys: {data.keys()}")
            raise
        except Exception as e:
            logger.error(f"Error in NPCSpeakMessage.from_dict: {e}")
            raise


def create_message_from_json(json_str: str) -> Message:
    """
    Create the appropriate message subclass from a JSON string.
    
    Args:
        json_str: JSON string representing a message
        
    Returns:
        An instance of the appropriate Message subclass
    """
    from src.client.logger import logger
    
    logger.debug(f"Parsing message JSON: {json_str[:200]}{'...' if len(json_str) > 200 else ''}")
    
    try:
        data = json.loads(json_str)
        logger.debug(f"JSON parsed successfully: {data.keys()}")
        
        message_type = data.get("type")
        logger.info(f"Message type detected: '{message_type}'")
        
        if not message_type:
            logger.warning(f"No message type found in data: {data}")
            return Message.from_dict(data)
        
        # Handle format conversion for narrative messages that use 'text' instead of 'payload.content'
        if message_type == MessageType.NARRATIVE and 'text' in data and 'payload' not in data:
            logger.info(f"Converting narrative message format: found 'text' field: {data['text'][:100]}")
            # Create a payload with the text content
            data['payload'] = {
                'content': data['text'],
                'format': 'markdown'  # Default to markdown for better formatting
            }
            logger.info(f"Converted narrative message payload: {data['payload']}")
        
        if message_type == MessageType.CHAT:
            logger.debug("Creating ChatMessage")
            return ChatMessage.from_dict(data)
        elif message_type == MessageType.SYSTEM:
            logger.debug("Creating SystemMessage")
            return SystemMessage.from_dict(data)
        elif message_type == MessageType.TYPING:
            logger.debug("Creating TypingMessage")
            return TypingMessage.from_dict(data)
        elif message_type == MessageType.MISSION:
            logger.debug("Creating MissionMessage")
            return MissionMessage.from_dict(data)
        elif message_type == MessageType.AGENTS:
            logger.debug("Creating AgentsMessage")
            return AgentsMessage.from_dict(data)
        elif message_type == MessageType.STREAM:
            logger.debug("Creating StreamMessage")
            return StreamMessage.from_dict(data)
        elif message_type == MessageType.ERROR:
            logger.debug("Creating ErrorMessage")
            return ErrorMessage.from_dict(data)
        elif message_type == MessageType.ACK:
            logger.debug("Creating AckMessage")
            return AckMessage.from_dict(data)
        elif message_type == MessageType.NARRATIVE:
            logger.debug("Creating NarrativeMessage")
            return NarrativeMessage.from_dict(data)
        elif message_type == MessageType.FUNCTION:
            logger.debug("Creating FunctionMessage")
            return FunctionMessage.from_dict(data)
        elif message_type == MessageType.NPC_SPEAK:
            logger.debug("Creating NPCSpeakMessage")
            return NPCSpeakMessage.from_dict(data)
        else:
            logger.warning(f"Unknown message type: '{message_type}', creating generic Message")
            return Message.from_dict(data)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}")
        logger.error(f"Raw message: {json_str}")
        raise
    except Exception as e:
        logger.error(f"Error creating message from JSON: {e}")
        logger.error(f"Raw message: {json_str}")
        raise
