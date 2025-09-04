# Frontend.md

## Spy Agency Frontend Requirements

## Overview

This document outlines the requirements for the Spy Agency frontend application. The frontend is a terminal-based user interface built with Textual UI that connects to the backend via WebSockets. It provides a chat-like interface for users to interact with AI spy agents.

## Core Requirements

### WebSocket Connection

- Establish and maintain a WebSocket connection to the backend server
- Handle connection events (connect, disconnect, reconnect)
- Display connection status to the user
- Implement proper error handling for connection issues
- Support automatic reconnection with exponential backoff
- Implement ping/pong heartbeat mechanism to detect connection issues

#### WebSocket Protocol Details

- **Connection URL**: `ws://localhost:8000/ws/{agent_id}`
  - Where `{agent_id}` is the identifier of the selected spy agent
- **Connection Headers**:
  - `User-Agent`: Client identifier
- **Connection Lifecycle**:
  1. Initial connection attempt
  2. Session establishment
  3. Regular message exchange
  4. Graceful disconnection with close codes

> **Note**: No authentication is required for this POC. Authentication will be implemented in future versions.

#### WebSocket Message Format

All messages follow a standardized JSON format:

```json
{
  "type": "message_type",
  "payload": {},
  "timestamp": "2025-09-04T13:52:38-05:00",
  "message_id": "unique-message-id"
}
```

- **type**: Identifies the message category (e.g., `chat`, `system`, `typing`, etc.)
- **payload**: Contains the actual message data (structure varies by message type)
- **timestamp**: Server-generated timestamp in ISO 8601 format
- **message_id**: Unique identifier for message tracking and deduplication

### Message Display

- Create a scrollable message display area similar to a chat application
- Support different message types (user messages, agent responses, system notifications)
- Format messages appropriately based on their type
- Support markdown rendering for rich text in messages
- Implement auto-scrolling to the latest message

### User Input

- Provide an input bar at the bottom of the interface
- Submit messages to the backend when the user presses Enter
- Clear the input field after submission
- Support basic text editing functionality
- Disable input when appropriate (e.g., during connection issues)

#### Message Submission Format

When a user submits a message, the frontend sends it to the backend via WebSocket in a standardized JSON format:

```json
{
  "type": "user_message",
  "payload": {
    "content": "User's message text",
    "agent_id": "007",
    "conversation_id": "conv-123456",
    "metadata": {
      "client_timestamp": "2025-09-04T13:54:25-05:00",
      "client_info": {
        "version": "1.0.0",
        "platform": "terminal"
      }
    }
  },
  "client_message_id": "client-123456"
}
```

#### Backend Message Processing

The backend processes user input messages as follows:

1. **Message Reception**: The backend WebSocket server receives the JSON message
2. **Validation**: The message is validated against the expected schema
3. **Acknowledgment**: An acknowledgment is sent back to the client

   ```json
   {
     "type": "ack",
     "payload": {
       "client_message_id": "client-123456",
       "status": "received"
     },
     "timestamp": "2025-09-04T13:54:26-05:00",
     "message_id": "ack-123456"
   }
   ```

4. **Processing**: The message is processed by the appropriate agent
5. **Response**: The agent's response is sent back to the client

#### Command Messages

In addition to regular text messages, the frontend can send command messages to control the application flow:

```json
{
  "type": "command",
  "payload": {
    "command": "select_agent",
    "parameters": {
      "agent_id": "013"
    }
  },
  "client_message_id": "cmd-123456"
}
```

Common commands include:

- `select_agent`: Change the active agent
- `start_mission`: Begin a new mission
- `end_conversation`: Terminate the current conversation
- `request_history`: Retrieve conversation history

### Message Processing

- Parse incoming WebSocket messages from JSON format
- Handle different message types from the backend
- Format messages appropriately for display
- Prepare for future streaming support (not implemented in initial POC)

> **Note**: Message streaming will be a future feature. The initial implementation will use complete messages.

### System Notifications

- Display informational messages about the system state
- Examples include:
  - "Connected to backend"
  - "Disconnected from backend"
  - "Reconnecting..."
  - "typing..."

## Message Types

The backend sends several types of messages that the frontend needs to handle:

1. **Agent Messages**: Responses from the AI spy agent
   - Regular text responses
   - Markdown-formatted responses
   - Action descriptions

   ```json
   {
     "type": "chat",
     "payload": {
       "content": "I've analyzed the documents and found a potential lead.",
       "format": "markdown",
       "agent_id": "007",
       "agent_name": "James"
     },
     "timestamp": "2025-09-04T13:52:38-05:00",
     "message_id": "msg-123456"
   }
   ```

2. **System Messages**: Information about the system state
   - Connection status
   - Error messages
   - Agent status updates

   ```json
   {
     "type": "system",
     "payload": {
       "content": "Backend connection established",
       "level": "info",
       "code": "connection_established"
     },
     "timestamp": "2025-09-04T13:52:38-05:00",
     "message_id": "sys-123456"
   }
   ```

3. **Typing Indicators**: Notifications that the agent is generating a response
   - Start typing indicator
   - Stop typing indicator

   ```json
   {
     "type": "typing",
     "payload": {
       "status": "start",
       "agent_id": "007"
     },
     "timestamp": "2025-09-04T13:52:38-05:00",
     "message_id": "typ-123456"
   }
   ```

4. **Mission Updates**: Information about the current mission
   - Mission briefings
   - Objective updates
   - Mission completion notifications

   ```json
   {
     "type": "mission",
     "payload": {
       "mission_id": "m-123",
       "title": "Operation Shadow Signal",
       "status": "in_progress",
       "objectives": [
         {"id": "obj-1", "description": "Infiltrate the compound", "status": "completed"},
         {"id": "obj-2", "description": "Retrieve the documents", "status": "pending"}
       ]
     },
     "timestamp": "2025-09-04T13:52:38-05:00",
     "message_id": "mis-123456"
   }
   ```

5. **Agent Selection**: Information about available agents
   - List of available agents (for future implementation)
   - Agent selection confirmation (for future implementation)

   > **Note**: Agent selection is not implemented in the initial POC. A default agent will be used.

   ```json
   {
     "type": "agents",
     "payload": {
       "available_agents": [
         {"id": "007", "name": "James", "codename": "Bond", "specialties": ["infiltration", "combat"]},
         {"id": "013", "name": "Natasha", "codename": "Widow", "specialties": ["hacking", "intelligence"]}
       ],
       "selected_agent": "007"
     },
     "timestamp": "2025-09-04T13:52:38-05:00",
     "message_id": "agt-123456"
   }
   ```

6. **Stream Messages**: Partial responses for streaming content
   - Chunk of text to append to current message
   - Stream start/end markers

   ```json
   {
     "type": "stream",
     "payload": {
       "content": "I've analyzed",
       "message_id": "msg-123456",
       "stream_status": "continue"
     },
     "timestamp": "2025-09-04T13:52:38-05:00",
     "message_id": "str-123456"
   }
   ```

7. **Error Messages**: Detailed error information
   - Error code and description
   - Recovery suggestions

   ```json
   {
     "type": "error",
     "payload": {
       "code": "auth_failed",
       "message": "Authentication failed",
       "details": "Invalid credentials provided",
       "recovery": "Please reconnect with valid credentials"
     },
     "timestamp": "2025-09-04T13:52:38-05:00",
     "message_id": "err-123456"
   }
   ```

## Backend Communication Protocol

### Message Flow

1. **Client to Server Messages**:
   - User sends a message to the agent
   - Client sends a command (e.g., select agent, start mission)
   - Client sends heartbeat/ping
   - Client acknowledges receipt of messages

   ```json
   {
     "type": "chat",
     "payload": {
       "content": "What information do we have on the target?",
       "agent_id": "007"
     },
     "client_message_id": "client-123456"
   }
   ```

2. **Server to Client Messages**:
   - Agent responses (complete or streaming)
   - System notifications
   - Error messages
   - State updates

3. **WebSocket Events**:
   - `open`: Connection established
   - `message`: New message received
   - `error`: Connection error
   - `close`: Connection closed

### Connection Management

1. **Initial Connection**:

   ```python
   async def connect():
       uri = "ws://localhost:8000/ws"
       try:
           websocket = await websockets.connect(uri)
           # Handle successful connection
           display_system_message("Connected to backend")
       except Exception as e:
           # Handle connection error
           display_error_message(f"Connection error: {str(e)}")
   ```

2. **Reconnection Strategy**:
   - Implement exponential backoff
   - Maximum retry attempts
   - Jitter to prevent thundering herd problem

   ```python
   async def reconnect(attempt: int = 0):
       max_attempts = 5
       if attempt >= max_attempts:
           # Give up after max attempts
           display_error_message("Failed to reconnect after multiple attempts")
           return None
           
       wait_time = (2 ** attempt) + (random.random() * 0.5)
       display_system_message(f"Reconnecting in {wait_time:.1f} seconds...")
       await asyncio.sleep(wait_time)
       try:
           return await connect()
       except Exception:
           return await reconnect(attempt + 1)
   ```

3. **Heartbeat Mechanism**:
   - Send ping every 30 seconds
   - Expect pong response within 10 seconds
   - Reconnect if pong not received

   > **Note**: During connection loss, the input bar will be disabled. No offline functionality is provided in this POC.

### Message Processing Pipeline

1. **Receive Message**:
   - Parse JSON payload
   - Validate message structure
   - Extract message type and content

2. **Message Routing**:
   - Route to appropriate handler based on message type
   - Update UI components as needed
   - Messages are persisted/summarized on the backend

3. **Error Handling**:
   - Handle malformed messages
   - Handle unexpected message types
   - Log errors for debugging
   - Display relevant error messages to the user
   - Show specific connection status information
   - Write detailed logs to `.spy_console/spy_cli_debug.log`

## Technical Implementation

### Textual UI Framework

The frontend will be built using the [Textual UI framework](https://textual.textualize.io/), a modern TUI (Text User Interface) framework for Python. Textual provides:

- Rich text rendering
- Layout management
- Event handling
- Styling with CSS-like syntax
- Widget system

Refer to the [Textual documentation](https://textual.textualize.io/guide/) for detailed implementation guidance.

### Code Structure

The frontend code should be modular and well-organized:

```python
src/client/
├── app.py                # Main application entry point
├── spy_cli.py            # CLI interface
├── api_client.py         # Backend API client
├── config.py             # Configuration
├── logger.py             # Logging configuration
├── websocket/            # WebSocket communication
│   ├── client.py         # WebSocket client implementation
│   ├── message_handler.py # Message processing logic
│   ├── reconnection.py   # Reconnection strategies
│   └── protocol.py       # Message protocol definitions (with i18n hooks)
├── widgets/              # UI components
│   ├── chat_window.py    # Message display
│   ├── input_bar.py      # User input
│   ├── status_bar.py     # Connection status display
│   └── typing_indicator.py # Typing indicator
└── screens/              # Application screens
    └── main.py           # Main application screen
```

### Design Principles

1. **Simplicity**: Keep the code simple and focused on core functionality
2. **Modularity**: Use a component-based approach with clear separation of concerns
3. **Readability**: Write clean, well-documented code
4. **Error Handling**: Implement robust error handling throughout
5. **Responsiveness**: Ensure the UI remains responsive during network operations

## User Experience

- The interface should be intuitive and easy to use
- Messages should be clearly distinguishable by type
- System status should be visible at all times
- Error messages should be informative and actionable
- The application should provide feedback for user actions

## Development Guidelines

- Follow Python best practices and PEP 8 style guidelines
- Document all classes and functions with docstrings
- Use type hints for better code clarity
- Write unit tests for all components
- Use async/await for WebSocket communication
- Implement proper logging throughout the application
- Configure logging to write to `.spy_console/spy_cli_debug.log`
- Include different log levels (DEBUG, INFO, WARNING, ERROR)
- Use the real server for testing (no mock server required)
- Design for local deployment only
- Include hooks for future internationalization (English-only for initial version)

> **Note**: This is a POC (Proof of Concept) application, not intended for production use. The focus should be on demonstrating core functionality rather than production-level robustness.

## Resources

- [Textual Documentation](https://textual.textualize.io/)
- [Textual GitHub Repository](https://github.com/Textualize/textual)
- [WebSockets in Python](https://websockets.readthedocs.io/en/stable/)
- [Rich Text Formatting](https://rich.readthedocs.io/en/latest/)
- [Asyncio Documentation](https://docs.python.org/3/library/asyncio.html)