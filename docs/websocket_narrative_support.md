# WebSocket Narrative Message Support

## Overview

This document describes the implementation of support for the `narrative` message type in the frontend WebSocket client. The backend was already sending messages with the `narrative` type, but the frontend was not properly handling them, causing them to be dropped and not displayed in the UI.

## Implementation Details

### 1. Protocol Definition

Added the `NARRATIVE` message type to the `MessageType` enum in `src/client/websocket/protocol.py`:

```python
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
    NARRATIVE = "narrative"  # Added support for narrative messages
```

### 2. Message Class

Created a new `NarrativeMessage` class in `src/client/websocket/protocol.py` to handle narrative messages:

```python
class NarrativeMessage(Message):
    """Narrative message containing story content."""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NarrativeMessage':
        """Create a narrative message from a dictionary."""
        if data["type"] != MessageType.NARRATIVE:
            raise ValueError(f"Expected message type {MessageType.NARRATIVE}, got {data['type']}")
        
        return super().from_dict(data)
```

### 3. Message Factory

Updated the `create_message_from_json` function to handle narrative messages:

```python
def create_message_from_json(json_str: str) -> Message:
    # ...existing code...
    elif message_type == MessageType.NARRATIVE:
        return NarrativeMessage.from_dict(data)
    # ...existing code...
```

### 4. Message Handler Registration

Added a handler for narrative messages in the `MainScreen` class:

```python
# Register message handlers
# ...existing handlers...
logger.debug("Registering NARRATIVE message handler")
self.message_handler.register_handler(
    MessageType.NARRATIVE, self.handle_narrative_message
)
```

### 5. Message Handler Implementation

Implemented the `handle_narrative_message` method in the `MainScreen` class:

```python
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
```

### 6. Chat Window Message Handling

Updated the `handle_websocket_message` method in the `ChatWindow` class to handle narrative messages:

```python
def handle_websocket_message(self, message: Union[ChatMessage, SystemMessage, TypingMessage, NarrativeMessage]) -> None:
    # ...existing code...
    elif message.type == MessageType.NARRATIVE:
        content = message.payload.get("content", "")
        is_markdown = message.payload.get("format", "text") == "markdown"
        
        logger.info(f"Processing narrative message: is_markdown={is_markdown}")
        logger.debug(f"Narrative message content: {content[:100]}{'...' if len(content) > 100 else ''}")
        
        message_obj = WindowChatMessage(
            content=content,
            sender="Narrative",
            timestamp=datetime.now(),
            message_id=message.message_id or f"narrative-{len(self.messages)}",
            is_markdown=is_markdown,
            is_system=True,  # Format as a system message for styling
        )
        
        logger.info(f"Adding narrative message to display: message_id={message_obj.message_id}")
        self.add_message(message_obj)
    # ...existing code...
```

## Usage

Narrative messages are now properly handled by the frontend WebSocket client. When the backend sends a message with the type `narrative`, it will be displayed in the chat window with the sender "Narrative" and styled as a system message.

## Testing

To test the narrative message support:

1. Start the backend server: `uv run python main.py`
2. Start the frontend client: `uv run python src/client/spy_cli.py`
3. Observe that narrative messages from the backend are now properly displayed in the frontend UI

## Future Improvements

- Add specific styling for narrative messages to distinguish them from system messages
- Support additional payload fields specific to narrative messages
- Add unit tests for narrative message handling
