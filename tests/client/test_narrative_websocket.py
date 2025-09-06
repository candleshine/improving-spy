"""
Test script to verify narrative flow with the client application.

This script tests that narrative messages are properly received and processed
by the client application when sent from the server via websocket.
"""

import asyncio
import json
import sys
import os
from pathlib import Path
import pytest

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.client.websocket.protocol import (
    Message,
    MessageType,
    parse_message_from_json,
)
from src.client.logger import logger

class MockWebSocketClient:
    """Mock WebSocket client for testing narrative message handling."""
    
    def __init__(self):
        self.received_messages = []
        self.narrative_messages = []
        
    def on_message(self, message: Message):
        """Handle a received message."""
        self.received_messages.append(message)
        if message.type == MessageType.NARRATIVE:
            self.narrative_messages.append(message)
            logger.info(f"Received narrative message: {message.message_id}")
            
            # Log narrative content
            if hasattr(message, 'text') and message.text:
                logger.info(f"Narrative content: {message.text[:100]}...")
            elif hasattr(message, 'payload') and isinstance(message.payload, dict):
                text = message.payload.get('text', '')
                logger.info(f"Narrative payload content: {text[:100] if text else 'No text'}...")
                
    def get_narrative_messages(self):
        """Get all narrative messages received."""
        return self.narrative_messages

@pytest.mark.asyncio
async def test_narrative_message_handling():
    """Test that narrative messages are properly handled by the client."""
    print("\n=== Testing Narrative Message Handling ===\n")
    
    # Create a mock client
    mock_client = MockWebSocketClient()
    
    # Create a sample narrative message
    narrative_json = json.dumps({
        "type": "narrative",
        "message_id": "test-narrative-1",
        "timestamp": "2025-09-05T15:00:00Z",
        "payload": {
            "text": "You feel the cold, uneven stone beneath your fingers as you examine the ancient statue. Its features are worn by time, but you can still make out the stern expression of what appears to be a monarch, scepter in hand. There's something unsettling about the way the eyes seem to follow you.",
            "scene_id": "temple_entrance",
            "format": "markdown"
        }
    })
    
    # Parse and process the message
    message = parse_message_from_json(narrative_json)
    mock_client.on_message(message)
    
    # Verify the message was processed correctly
    narrative_messages = mock_client.get_narrative_messages()
    print(f"\n=== Narrative Messages Received: {len(narrative_messages)} ===")
    
    for i, msg in enumerate(narrative_messages):
        print(f"\nMessage {i+1}:")
        print(f"Type: {msg.type}")
        print(f"Message ID: {msg.message_id}")
        
        if hasattr(msg, 'text') and msg.text:
            print(f"Content: {msg.text[:100]}...")
        elif hasattr(msg, 'payload') and isinstance(msg.payload, dict):
            text = msg.payload.get('text', '')
            scene_id = msg.payload.get('scene_id', 'unknown')
            format_type = msg.payload.get('format', 'unknown')
            print(f"Scene ID: {scene_id}")
            print(f"Format: {format_type}")
            print(f"Content: {text[:100]}...")
    
    # Verify the message was processed correctly
    assert len(narrative_messages) == 1, "Expected 1 narrative message"
    assert narrative_messages[0].type == MessageType.NARRATIVE, "Expected message type to be NARRATIVE"
    assert narrative_messages[0].message_id == "test-narrative-1", "Expected message ID to be test-narrative-1"
    
    payload = narrative_messages[0].payload
    assert isinstance(payload, dict), "Expected payload to be a dictionary"
    assert "text" in payload, "Expected payload to contain 'text'"
    assert "scene_id" in payload, "Expected payload to contain 'scene_id'"
    assert payload["scene_id"] == "temple_entrance", "Expected scene_id to be 'temple_entrance'"
    assert payload["format"] == "markdown", "Expected format to be 'markdown'"
    
    print("\n=== Test Passed ===")
    return True

async def main():
    """Run all tests."""
    await test_narrative_message_handling()

if __name__ == "__main__":
    asyncio.run(main())
