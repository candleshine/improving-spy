# WebSocket Client Logging Documentation

## Overview

This document outlines the comprehensive logging implementation for the Spy Agency CLI application's WebSocket client and related components. The logging system provides detailed visibility into WebSocket connection lifecycle, message handling, and UI interactions.

## Log File Location

Logs are written to: `~/.spy_console/spy_cli_debug.log`

## Logging Patterns

### Connection Lifecycle

The WebSocket connection lifecycle is fully logged with the following events:

1. **Connection Initiation**:
   ```
   INFO - MAIN SCREEN: Initiating WebSocket connection on application startup
   INFO - MAIN SCREEN: Creating WebSocket client for agent: {agent_id}
   INFO - MAIN SCREEN: Registering message handlers for WebSocket client
   INFO - MAIN SCREEN: Starting WebSocket connection task for agent: {agent_id}
   DEBUG - WebSocket connection task created and running asynchronously
   DEBUG - Connecting to ws://localhost:8000/ws/play?scenario=last_oracle with agent_id={agent_id}
   ```

2. **Connection Established**:
   ```
   INFO - Connected to WebSocket server
   DEBUG - WebSocket connection established with agent_id={agent_id}
   INFO - MAIN SCREEN: WebSocket connected to game engine with agent_id={agent_id}
   INFO - Connection established successfully, ready to receive messages
   DEBUG - Updated status bar to 'Connected to game engine'
   DEBUG - Enabled input bar for user messages
   INFO - Adding system connection message to chat window
   ```

3. **Heartbeat Mechanism**:
   ```
   DEBUG - Sent heartbeat ping
   ```

4. **Disconnection**:
   ```
   INFO - WebSocket disconnected
   DEBUG - WebSocket connection closed with code={code} and reason={reason}
   INFO - MAIN SCREEN: WebSocket disconnected from game engine
   DEBUG - Updated status bar to 'Disconnected from game engine'
   DEBUG - Disabled input bar due to disconnection
   ```

5. **Error Handling**:
   ```
   ERROR - WebSocket error: {error}
   INFO - MAIN SCREEN: WebSocket connection error: {error}
   DEBUG - Updated status bar to 'Connection error'
   ```

### Message Handling

1. **Message Receipt**:
   ```
   DEBUG - Received raw message: {message_json}
   DEBUG - Processing message of type: {message_type}
   ```

2. **Message Processing by Type**:
   ```
   DEBUG - MAIN SCREEN: Handling chat message from {sender}: {message_preview}
   DEBUG - MAIN SCREEN: Handling system message: {message_preview}
   DEBUG - MAIN SCREEN: Handling typing indicator: {is_typing}
   DEBUG - MAIN SCREEN: Handling error message: {error_message}
   ```

3. **Message Display**:
   ```
   DEBUG - Adding message to chat window: {message_preview}
   DEBUG - Updating typing indicator: {is_typing}
   ```

### User Interactions

1. **Message Sending**:
   ```
   INFO - MAIN SCREEN: User submitted message: {message_preview}
   DEBUG - Creating chat message with content: {message_preview}
   DEBUG - Sending message to WebSocket server
   DEBUG - Message sent successfully
   ```

2. **Reconnection**:
   ```
   INFO - MAIN SCREEN: User initiated reconnection
   DEBUG - Closing existing WebSocket connection if open
   INFO - MAIN SCREEN: Reconnecting to agent: {agent_id}
   ```

3. **Application Exit**:
   ```
   INFO - MAIN SCREEN: User initiated application exit
   DEBUG - Closing WebSocket connection before exit
   INFO - MAIN SCREEN: Application shutting down
   ```

## Logging Levels

- **INFO**: High-level flow information (connections, disconnections, user actions)
- **DEBUG**: Detailed operational data (message contents, UI updates, state changes)
- **ERROR**: Error conditions (connection failures, message processing errors)

## Implementation Details

Logging is implemented across the following components:

1. **WebSocketClient** (`src/client/websocket/client.py`):
   - Connection establishment and closure
   - Message receipt and parsing
   - Heartbeat mechanism
   - Error handling

2. **MainScreen** (`src/client/screens/main.py`):
   - Application lifecycle
   - WebSocket connection management
   - Message handling and routing
   - UI state updates

3. **ChatWindow** (`src/client/widgets/chat_window.py`):
   - Message display
   - UI rendering

## Debugging Tips

1. **Connection Issues**:
   - Check for connection logs with "WebSocket connected" or "WebSocket error"
   - Verify server URL and agent ID in connection logs

2. **Message Flow Problems**:
   - Follow message receipt logs ("Received raw message")
   - Trace message handling by type
   - Verify message display in chat window

3. **UI Update Issues**:
   - Check for "Updated status bar" and "Adding message to chat window" logs
   - Verify typing indicator updates

## Future Enhancements

Potential improvements to the logging system:

1. Log rotation to manage log file size
2. Structured logging for easier parsing
3. Performance metrics for WebSocket operations
4. Correlation IDs for tracking message flow
