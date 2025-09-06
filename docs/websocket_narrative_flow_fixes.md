# Narrative Flow WebSocket Integration Fixes

## Issue Summary

The enhanced narrative flow in the GameEngine was not properly reaching the frontend client via the WebSocket layer. While the backend was generating rich narrative descriptions and attempting to send them through the WebSocket connection, these messages were not being properly received and processed by the client.

## Root Causes

1. **Missing WebSocket Parameter**: In `main.py`, the GameEngine methods were being called without passing the WebSocket parameter, preventing narrative messages from being sent to the client.

2. **Missing Message Handler**: In the client's `MessageHandler` class, there was no handler registered for the `MessageType.NARRATIVE` message type, causing narrative messages to be dropped.

## Changes Made

### Backend Fixes

1. **WebSocket Parameter Propagation**: Updated `main.py` to pass the WebSocket parameter to GameEngine methods:

   ```python
   # Before
   scene_response = await engine.describe_scene(scene_query, history)
   choice_response = await engine.process_choice_selection(choice_index)
   scene_desc = await engine.describe_scene("look around", history)
   npc_response = await engine.interact_with_npc(npc_id, npc_message, history)

   # After
   scene_response = await engine.describe_scene(scene_query, history, websocket)
   choice_response = await engine.process_choice_selection(choice_index, websocket)
   scene_desc = await engine.describe_scene("look around", history, websocket)
   npc_response = await engine.interact_with_npc(npc_id, npc_message, history, websocket)
   ```

2. **Enhanced NPC Interaction**: Updated the `interact_with_npc` method in GameEngine to support websocket communication:

   ```python
   async def interact_with_npc(self, npc_id: str, user_input: str, history=None, websocket=None):
       # Get the NPC response
       response = await self.npc_catalog.interact_with_npc(npc_id, user_input, history)
       
       # If websocket is provided, send the NPC response as a narrative message
       if websocket and response:
           try:
               # Create a narrative message from the NPC response
               narrative_message = {
                   "type": "narrative",
                   "text": f"[NPC:{npc_id}] {response['text']}",
                   "scene_id": self.get_current_scene_id(),
                   "timestamp": datetime.utcnow().isoformat(),
                   "format": "markdown",
                   "is_npc_response": True  # Flag to indicate this is an NPC response
               }
               
               # Send the message
               await websocket.send_json(narrative_message)
           except Exception as e:
               logger.error(f"Failed to send NPC response via websocket: {e}")
       
       return response
   ```

3. **Verified GameEngine Implementation**: Confirmed that the GameEngine's methods (`describe_scene`, `process_choice_selection`, `get_choices_for_current_scene`, `interact_with_npc`) properly send narrative messages to the WebSocket when provided.

### Frontend Fixes

1. **Added Message Handler**: Updated the `MessageHandler` class in `src/client/websocket/message_handler.py` to register a handler for narrative messages:

   ```python
   self.handlers: Dict[MessageType, List[Callable[[Message], None]]] = {
       # Existing handlers...
       MessageType.NARRATIVE: [],  # Added handler for narrative messages
   }
   ```

2. **Enhanced Logging**: Added detailed logging in the WebSocket client to verify narrative messages are being received and processed correctly:

   ```python
   # Enhanced logging for narrative messages
   if message.type == MessageType.NARRATIVE:
       logger.info(f"NARRATIVE MESSAGE RECEIVED: id={message.message_id}")
       if hasattr(message, 'text') and message.text:
           logger.info(f"Narrative content (first 100 chars): {message.text[:100]}...")
       elif hasattr(message, 'payload') and isinstance(message.payload, dict):
           text = message.payload.get('text', '')
           scene_id = message.payload.get('scene_id', 'unknown')
           format_type = message.payload.get('format', 'unknown')
           logger.info(f"Narrative payload - scene: {scene_id}, format: {format_type}")
           logger.info(f"Narrative content (first 100 chars): {text[:100] if text else 'No text'}...")
   ```

3. **Fixed Client Code Issues**: Corrected indentation and syntax errors in the WebSocket client code that were causing runtime errors.

## Testing

1. **Unit Tests**: Created a dedicated test script (`test_narrative_websocket.py`) to verify that narrative messages are properly processed by the client application.

2. **Integration Tests**: Ran the existing `test_narrative_flow.py` to verify that the GameEngine correctly sends narrative messages to the WebSocket layer.

3. **Logging Verification**: Added enhanced logging throughout the WebSocket message flow to verify that narrative messages are being properly sent, received, and processed.

## Results

- The narrative flow now correctly reaches the frontend client via the WebSocket layer.
- Rich, immersive narrative descriptions are properly displayed to the user during gameplay.
- The WebSocket client correctly processes and displays narrative messages with the appropriate styling.
- Logging provides visibility into the entire message flow, making it easier to diagnose any future issues.

## Future Recommendations

1. **Consistent Message Handling**: Ensure all message types are consistently registered in the MessageHandler.
2. **Automated Testing**: Add more comprehensive tests for WebSocket message handling.
3. **Error Handling**: Improve error handling for WebSocket message processing to prevent silent failures.
4. **Message Format Standardization**: Consider standardizing message formats between frontend and backend.
5. **Monitoring**: Add monitoring for WebSocket message flow to detect issues in production.
