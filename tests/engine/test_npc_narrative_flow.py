"""
Test script to verify NPC interaction narrative flow via websocket.

This script tests that narrative messages from NPC interactions are properly
sent through the websocket layer.
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock
import pytest

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.engine.game_engine import GameEngine

class MockWebSocket:
    """Mock WebSocket class for testing."""
    
    def __init__(self):
        self.sent_messages = []
        self.send_json = AsyncMock(side_effect=self._store_message)
        
    async def _store_message(self, message):
        """Store the message for later inspection."""
        self.sent_messages.append(message)
        
    def get_narrative_messages(self):
        """Get all narrative messages sent to the websocket."""
        return [msg for msg in self.sent_messages if msg.get("type") == "narrative"]
    
    def get_npc_messages(self):
        """Get all NPC narrative messages sent to the websocket."""
        return [msg for msg in self.sent_messages if msg.get("type") == "narrative" and msg.get("is_npc_response")]

@pytest.mark.asyncio
async def test_npc_interaction_flow():
    """Test the NPC interaction flow with the Last Oracle scenario."""
    print("\n=== Testing NPC Interaction Flow ===\n")
    
    # Initialize the game engine with the Last Oracle scenario
    scenario_path = Path(__file__).parent.parent.parent / "scenarios" / "last_oracle.json"
    engine = GameEngine(str(scenario_path))
    
    # Set the current scene
    engine.set_current_scene("temple_entrance")
    
    # Create a mock websocket
    mock_ws = MockWebSocket()
    
    # Interact with an NPC (the Oracle)
    print("=== Interacting with the Oracle NPC ===")
    npc_response = await engine.interact_with_npc("oracle", "What do you know about the king?", websocket=mock_ws)
    
    # Print the NPC response
    print(f"NPC Response: {npc_response.get('text', 'No response text')}")
    
    # Verify NPC response was sent to websocket
    npc_messages = mock_ws.get_narrative_messages()
    print(f"\n=== Websocket NPC Messages: {len(npc_messages)} ===")
    for i, msg in enumerate(npc_messages):
        print(f"\nMessage {i+1}:")
        print(f"Type: {msg.get('type')}")
        print(f"Is NPC Response: {msg.get('is_npc_response', False)}")
        print(f"Scene ID: {msg.get('scene_id')}")
        print(f"Content: {msg.get('text')[:100]}...")
    
    # Verify that at least one NPC message was sent
    assert len(npc_messages) > 0, "No NPC messages were sent to the websocket"
    
    # Verify that the NPC message has the correct format
    npc_msg = npc_messages[0]
    assert npc_msg.get("type") == "narrative", "Message type should be 'narrative'"
    assert npc_msg.get("is_npc_response"), "Message should be marked as an NPC response"
    assert npc_msg.get("scene_id") == "temple_entrance", "Scene ID should match the current scene"
    assert npc_msg.get("text").startswith("[NPC:oracle]"), "Message should be prefixed with NPC identifier"
    
    print("\n=== Test Passed ===")

async def main():
    """Run all tests."""
    await test_npc_interaction_flow()

if __name__ == "__main__":
    asyncio.run(main())
