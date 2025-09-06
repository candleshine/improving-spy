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
    CHOICE = "choice"


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
        timestamp: str = None,
        message_id: str = None,
        conversation_id: str = None,
        agent_id: str = None
    ):
        """
        Initialize a new message.
        
        Args:
            message_type: The type of message
            payload: The message payload
            timestamp: Optional timestamp (ISO format)
            message_id: Optional message ID
            conversation_id: Optional conversation ID
            agent_id: Optional agent ID
        """
        self.type = message_type
        self.payload = payload
        self.timestamp = timestamp or datetime.utcnow().isoformat()
        self.message_id = message_id or str(uuid.uuid4())
        self.conversation_id = conversation_id
        self.agent_id = agent_id
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the message to a dictionary."""
        result = {
            "type": self.type,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "message_id": self.message_id
        }
        
        if self.conversation_id:
            result["conversation_id"] = self.conversation_id
            
        if self.agent_id:
            result["agent_id"] = self.agent_id
            
        return result
    
    def to_json(self) -> str:
        """Convert the message to a JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create a message from a dictionary."""
        return cls(
            message_type=data.get("type", "unknown"),
            payload=data.get("payload", {}),
            timestamp=data.get("timestamp", datetime.utcnow().isoformat()),
            message_id=data.get("message_id", str(uuid.uuid4())),
            conversation_id=data.get("conversation_id"),
            agent_id=data.get("agent_id")
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        """Create a message from a JSON string."""
        return cls.from_dict(json.loads(json_str))


class ChatMessage(Message):
    """Message containing chat content."""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatMessage':
        """Create a chat message from a dictionary."""
        from src.client.logger import logger
        
        logger.debug(f"ChatMessage.from_dict called with data: {data}")
        
        try:
            if data["type"] != MessageType.CHAT:
                logger.error(f"Type mismatch in ChatMessage.from_dict: expected {MessageType.CHAT}, got {data['type']}")
                raise ValueError(f"Expected message type {MessageType.CHAT}, got {data['type']}")
            
            return super().from_dict(data)
        except KeyError as e:
            logger.error(f"KeyError in ChatMessage.from_dict: {e}")
            logger.error(f"Available keys: {data.keys()}")
            raise
        except Exception as e:
            logger.error(f"Error in ChatMessage.from_dict: {e}")
            raise


class SystemMessage(Message):
    """System message for notifications and status updates."""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SystemMessage':
        """Create a system message from a dictionary."""
        from src.client.logger import logger
        
        logger.debug(f"SystemMessage.from_dict called with data: {data}")
        
        try:
            if data["type"] != MessageType.SYSTEM:
                logger.error(f"Type mismatch in SystemMessage.from_dict: expected {MessageType.SYSTEM}, got {data['type']}")
                raise ValueError(f"Expected message type {MessageType.SYSTEM}, got {data['type']}")
            
            # Handle system message format
            # Format 1: {"type":"system","text":"System message","level":"info"}
            # Format 2: {"type":"system","payload":{"content":"System message","level":"info"}}
            
            # If the message has a 'text' field but no 'payload', convert it to the expected format
            if 'text' in data and 'payload' not in data:
                logger.info(f"Converting system message format: found 'text' field: {data['text'][:100]}")
                # Create a payload with the text content and level
                data['payload'] = {
                    'content': data['text'],
                    'level': data.get('level', 'info')
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
    """Message indicating typing status."""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TypingMessage':
        """Create a typing message from a dictionary."""
        from src.client.logger import logger
        
        logger.debug(f"TypingMessage.from_dict called with data: {data}")
        
        try:
            if data["type"] != MessageType.TYPING:
                logger.error(f"Type mismatch in TypingMessage.from_dict: expected {MessageType.TYPING}, got {data['type']}")
                raise ValueError(f"Expected message type {MessageType.TYPING}, got {data['type']}")
            
            return super().from_dict(data)
        except KeyError as e:
            logger.error(f"KeyError in TypingMessage.from_dict: {e}")
            logger.error(f"Available keys: {data.keys()}")
            raise
        except Exception as e:
            logger.error(f"Error in TypingMessage.from_dict: {e}")
            raise


class MissionMessage(Message):
    """Message containing mission information."""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MissionMessage':
        """Create a mission message from a dictionary."""
        from src.client.logger import logger
        
        logger.debug(f"MissionMessage.from_dict called with data: {data}")
        
        try:
            if data["type"] != MessageType.MISSION:
                logger.error(f"Type mismatch in MissionMessage.from_dict: expected {MessageType.MISSION}, got {data['type']}")
                raise ValueError(f"Expected message type {MessageType.MISSION}, got {data['type']}")
            
            return super().from_dict(data)
        except KeyError as e:
            logger.error(f"KeyError in MissionMessage.from_dict: {e}")
            logger.error(f"Available keys: {data.keys()}")
            raise
        except Exception as e:
            logger.error(f"Error in MissionMessage.from_dict: {e}")
            raise


class AgentsMessage(Message):
    """Message containing agent information."""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentsMessage':
        """Create an agents message from a dictionary."""
        from src.client.logger import logger
        
        logger.debug(f"AgentsMessage.from_dict called with data: {data}")
        
        try:
            if data["type"] != MessageType.AGENTS:
                logger.error(f"Type mismatch in AgentsMessage.from_dict: expected {MessageType.AGENTS}, got {data['type']}")
                raise ValueError(f"Expected message type {MessageType.AGENTS}, got {data['type']}")
            
            return super().from_dict(data)
        except KeyError as e:
            logger.error(f"KeyError in AgentsMessage.from_dict: {e}")
            logger.error(f"Available keys: {data.keys()}")
            raise
        except Exception as e:
            logger.error(f"Error in AgentsMessage.from_dict: {e}")
            raise


class StreamMessage(Message):
    """Message for streaming content."""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StreamMessage':
        """Create a stream message from a dictionary."""
        from src.client.logger import logger
        
        logger.debug(f"StreamMessage.from_dict called with data: {data}")
        
        try:
            if data["type"] != MessageType.STREAM:
                logger.error(f"Type mismatch in StreamMessage.from_dict: expected {MessageType.STREAM}, got {data['type']}")
                raise ValueError(f"Expected message type {MessageType.STREAM}, got {data['type']}")
            
            return super().from_dict(data)
        except KeyError as e:
            logger.error(f"KeyError in StreamMessage.from_dict: {e}")
            logger.error(f"Available keys: {data.keys()}")
            raise
        except Exception as e:
            logger.error(f"Error in StreamMessage.from_dict: {e}")
            raise


class ErrorMessage(Message):
    """Error message."""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ErrorMessage':
        """Create an error message from a dictionary."""
        from src.client.logger import logger
        
        logger.debug(f"ErrorMessage.from_dict called with data: {data}")
        
        try:
            if data["type"] != MessageType.ERROR:
                logger.error(f"Type mismatch in ErrorMessage.from_dict: expected {MessageType.ERROR}, got {data['type']}")
                raise ValueError(f"Expected message type {MessageType.ERROR}, got {data['type']}")
            
            # Handle error message format
            # Format 1: {"type":"error","text":"Error message"}
            # Format 2: {"type":"error","payload":{"content":"Error message"}}
            
            # If the message has a 'text' field but no 'payload', convert it to the expected format
            if 'text' in data and 'payload' not in data:
                logger.info(f"Converting error message format: found 'text' field: {data['text'][:100]}")
                # Create a payload with the text content
                data['payload'] = {
                    'content': data['text']
                }
                logger.info(f"Converted error message payload: {data['payload']}")
            
            logger.debug(f"ErrorMessage payload: {data.get('payload', {})}")
            result = super().from_dict(data)
            logger.debug("ErrorMessage created successfully")
            return result
        except KeyError as e:
            logger.error(f"KeyError in ErrorMessage.from_dict: {e}")
            logger.error(f"Available keys: {data.keys()}")
            raise
        except Exception as e:
            logger.error(f"Error in ErrorMessage.from_dict: {e}")
            raise


class AckMessage(Message):
    """Acknowledgment message."""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AckMessage':
        """Create an acknowledgment message from a dictionary."""
        from src.client.logger import logger
        
        logger.debug(f"AckMessage.from_dict called with data: {data}")
        
        try:
            if data["type"] != MessageType.ACK:
                logger.error(f"Type mismatch in AckMessage.from_dict: expected {MessageType.ACK}, got {data['type']}")
                raise ValueError(f"Expected message type {MessageType.ACK}, got {data['type']}")
            
            return super().from_dict(data)
        except KeyError as e:
            logger.error(f"KeyError in AckMessage.from_dict: {e}")
            logger.error(f"Available keys: {data.keys()}")
            raise
        except Exception as e:
            logger.error(f"Error in AckMessage.from_dict: {e}")
            raise


class NarrativeMessage(Message):
    """Narrative message for storytelling."""
    
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
            
            # If the message has a 'function' field but no 'payload', convert it to the expected format
            if 'function' in data and 'payload' not in data:
                logger.info(f"Converting function message format: found 'function' field")
                # Create a payload with the function data
                data['payload'] = {
                    'function': data['function']
                }
                logger.info(f"Converted function message payload: {data['payload']}")
            
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
            # Format 1: {"type":"npc_speak","name":"NPC Name","text":"Dialogue"}
            # Format 2: {"type":"npc_speak","payload":{"name":"NPC Name","content":"Dialogue"}}
            
            # If the message has 'name' and 'text' fields but no 'payload', convert it to the expected format
            if 'text' in data and 'payload' not in data:
                logger.info(f"Converting NPC speak message format: found 'text' field: {data['text'][:100]}")
                # Create a payload with the text content and name
                data['payload'] = {
                    'content': data['text'],
                    'name': data.get('name', 'Unknown NPC')
                }
                logger.info(f"Converted NPC speak message payload: {data['payload']}")
            
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


class ChoiceMessage(Message):
    """Message representing a set of choices for the player."""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChoiceMessage':
        """Create a ChoiceMessage from a dictionary."""
        from src.client.logger import logger
        
        logger.debug(f"ChoiceMessage.from_dict called with data: {data}")
        
        try:
            if data["type"] != MessageType.CHOICE:
                logger.error(f"Type mismatch in ChoiceMessage.from_dict: expected {MessageType.CHOICE}, got {data['type']}")
                raise ValueError(f"Expected message type {MessageType.CHOICE}, got {data['type']}")
            
            # Handle choice message format
            # Format: {"type":"choice","options":[{"text":"Option 1"},{"text":"Option 2"}],"raw_text":"Option 1 / Option 2"}
            
            # If the message has 'options' field but no 'payload', convert it to the expected format
            if 'options' in data and 'payload' not in data:
                logger.info(f"Converting choice message format: found 'options' field with {len(data['options'])} options")
                # Create a payload with the options and raw text
                data['payload'] = {
                    'options': data['options'],
                    'raw_text': data.get('raw_text', '')
                }
                logger.info(f"Converted choice message payload: {data['payload']}")
            
            logger.debug(f"ChoiceMessage payload: {data.get('payload', {})}")
            result = super().from_dict(data)
            logger.debug("ChoiceMessage created successfully")
            return result
        except KeyError as e:
            logger.error(f"KeyError in ChoiceMessage.from_dict: {e}")
            logger.error(f"Available keys: {data.keys()}")
            raise
        except Exception as e:
            logger.error(f"Error in ChoiceMessage.from_dict: {e}")
            raise


class UserMessage:
    """Message sent from the client to the server."""
    
    def __init__(
        self,
        content: str,
        agent_id: str = None,
        conversation_id: str = None,
        message_id: str = None,
        timestamp: str = None
    ):
        """
        Initialize a new user message.
        
        Args:
            content: The message content
            agent_id: Optional agent ID
            conversation_id: Optional conversation ID
            message_id: Optional message ID
            timestamp: Optional timestamp (ISO format)
        """
        self.type = MessageType.USER_MESSAGE
        self.content = content
        self.agent_id = agent_id
        self.conversation_id = conversation_id
        self.message_id = message_id or f"client-{uuid.uuid4()}"
        self.timestamp = timestamp or datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the message to a dictionary."""
        result = {
            "type": self.type,
            "payload": {
                "content": self.content
            },
            "timestamp": self.timestamp,
            "client_message_id": self.message_id
        }
        
        if self.agent_id:
            result["payload"]["agent_id"] = self.agent_id
            
        if self.conversation_id:
            result["payload"]["conversation_id"] = self.conversation_id
            
        return result
    
    def to_json(self) -> str:
        """Convert the message to a JSON string."""
        return json.dumps(self.to_dict())


def parse_message_from_json(json_str: str) -> Message:
    """
    Parse a JSON string into a Message object.
    
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
        elif message_type == MessageType.CHOICE:
            logger.debug("Creating ChoiceMessage")
            return ChoiceMessage.from_dict(data)
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
