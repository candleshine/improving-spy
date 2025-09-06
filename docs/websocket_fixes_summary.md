# WebSocket Message Handling Fixes

## Issue Summary

### Narrative Messages

The frontend WebSocket client was not properly handling `narrative` message types sent by the backend server. This caused these messages to be dropped and not displayed in the UI, leading to a discrepancy between the backend logs (which showed messages being sent) and the frontend logs (which did not show these messages being received or processed).

### System Messages

The frontend WebSocket client was receiving system messages from the backend but not properly displaying them in the UI. The issue was due to a format mismatch between the backend's system message format and what the frontend expected.

## Root Cause

### Narrative Message Issue

The root cause of the issue was that the `narrative` message type was not defined in the frontend's `MessageType` enum in `src/client/websocket/protocol.py`. As a result, when the backend sent messages with this type, they were received by the WebSocket client but could not be properly parsed and handled.

### System Message Issue

The root cause of the system message issue was a format mismatch between the backend and frontend:

- **Backend Format**: `{"type":"system","text":"Message content"}`
- **Frontend Expected Format**: `{"type":"system","payload":{"content":"Message content", "level":"info"}}`

This mismatch caused system messages to be received by the WebSocket client but not properly processed for display in the UI.

## Changes Made

### Narrative Message Support

1. **Added Message Type Definition**:
   - Added `NARRATIVE = "narrative"` to the `MessageType` enum in `protocol.py`

2. **Created Message Class**:
   - Implemented a new `NarrativeMessage` class to handle narrative messages

3. **Updated Message Factory**:
   - Modified `create_message_from_json` to handle the new message type

4. **Added Message Handler**:
   - Implemented `handle_narrative_message` in the `MainScreen` class
   - Registered the handler with the message handler system

5. **Updated Chat Window**:
   - Enhanced `handle_websocket_message` in `ChatWindow` to process narrative messages
   - Added styling and display logic for narrative messages

6. **Documentation**:
   - Created detailed documentation of the changes in `websocket_narrative_support.md`

### System Message Format Fix

1. **Enhanced Logging**:
   - Added detailed logging to `create_message_from_json` function to trace message parsing
   - Added logging to `SystemMessage.from_dict` method to debug format issues

2. **Format Adaptation**:
   - Updated `SystemMessage.from_dict` to handle both message formats:

   ```python
   # If the message has a 'text' field but no 'payload', convert it to the expected format
   if 'text' in data and 'payload' not in data:
       data['payload'] = {
           'content': data['text'],
           'level': 'info'  # Default to info level
       }
   ```

3. **Client Logging**:
   - Enhanced WebSocket client logging to inspect raw message format
   - Added detailed logging of message keys and structure for debugging

## Testing

### Narrative Message Testing

The narrative message changes were tested by running both the backend server and frontend client simultaneously. The frontend now properly receives, processes, and displays narrative messages sent by the backend.

### System Message Testing

The system message format fix was tested by:

1. Adding detailed logging to track message parsing and format conversion
2. Running the CLI application and observing system messages in the UI
3. Verifying logs show successful format conversion from backend to frontend format
4. Confirming system messages appear correctly in the chat window

## Benefits

1. **Complete Message Handling**: All message types sent by the backend are now properly handled by the frontend
2. **Improved User Experience**: Users now see narrative content and system messages that were previously missing or not displayed
3. **Better Diagnostics**: Logs now show the complete message flow from backend to frontend
4. **Consistent Protocol**: The frontend and backend now share a consistent message type definition
5. **Format Compatibility**: The system can now handle different message formats without requiring backend changes
6. **Enhanced Debugging**: Added logging makes it easier to diagnose message parsing issues

## Future Recommendations

1. **Message Type Synchronization**: Ensure that message types are kept in sync between frontend and backend
2. **Protocol Documentation**: Maintain a central document describing all supported message types and their expected formats
3. **Automated Testing**: Add tests to verify message handling for all supported types and formats
4. **Custom Styling**: Consider adding specific styling for narrative messages to distinguish them from system messages
5. **Format Standardization**: Consider standardizing message formats between frontend and backend to avoid future mismatches
6. **Schema Validation**: Implement schema validation for messages to catch format issues early
7. **Format Adapters**: Create dedicated adapters for handling different message formats from various sources
8. **Monitoring**: Add monitoring for message parsing failures to detect issues in production
