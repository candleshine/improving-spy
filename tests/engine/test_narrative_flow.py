"""Test script for the enhanced narrative flow in the game engine.
This demonstrates how the narrative context is generated before presenting choices
and sent to the websocket layer.
"""
import asyncio
import sys
import os
import json
from pathlib import Path
from unittest.mock import AsyncMock

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

async def test_narrative_flow():
    """Test the enhanced narrative flow with the Last Oracle scenario."""
    print("\n=== Testing Enhanced Narrative Flow ===\n")
    
    # Initialize the game engine with the Last Oracle scenario
    scenario_path = Path(__file__).parent.parent.parent / "scenarios" / "last_oracle.json"
    engine = GameEngine(str(scenario_path))
    
    # Create a mock websocket
    mock_ws = MockWebSocket()
    
    # Set the initial scene
    engine.set_current_scene("temple_entrance")
    
    # Get the choices for the current scene with enhanced narrative
    choices_data = await engine.get_choices_for_current_scene(websocket=mock_ws)
    
    # Print the enhanced narrative context
    print("=== Enhanced Narrative Context ===")
    print(choices_data.get("narrative_context", "No narrative context available"))
    print("\n=== Raw Choices ===")
    print(choices_data.get("formatted_text", "No choices available"))
    
    # Verify narrative was sent to websocket
    narrative_messages = mock_ws.get_narrative_messages()
    print(f"\n=== Websocket Narrative Messages: {len(narrative_messages)} ===")
    for i, msg in enumerate(narrative_messages):
        print(f"\nMessage {i+1}:")
        print(f"Type: {msg.get('type')}")
        print(f"Scene ID: {msg.get('scene_id')}")
        print(f"Format: {msg.get('format')}")
        print(f"Content: {msg.get('text')[:100]}...")
    
    # Simulate making a choice
    print("\n=== Making a choice ===")
    # Reset the mock websocket to clear previous messages
    mock_ws = MockWebSocket()
    outcome = await engine.process_choice_selection(0, websocket=mock_ws)  # Choose the first option
    print(f"Outcome: {outcome.get('text', 'No outcome text')}")
    
    # Verify choice outcome was sent to websocket
    outcome_messages = mock_ws.get_narrative_messages()
    print(f"\n=== Websocket Outcome Messages: {len(outcome_messages)} ===")
    for i, msg in enumerate(outcome_messages):
        print(f"\nMessage {i+1}:")
        print(f"Type: {msg.get('type')}")
        print(f"Scene ID: {msg.get('scene_id') if 'scene_id' in msg else 'N/A'}")
        print(f"Is New Scene: {msg.get('is_new_scene', False)}")
        print(f"Content: {msg.get('text')[:100]}...")
    
    # Get the choices for the new scene with the previous outcome as context
    print("\n=== New Scene with Previous Outcome Context ===")
    # Reset the mock websocket again
    mock_ws = MockWebSocket()
    new_scene_choices = await engine.get_choices_for_current_scene(previous_outcome=outcome, websocket=mock_ws)
    
    # Print the enhanced narrative context for the new scene
    print("=== Enhanced Narrative Context for New Scene ===")
    print(new_scene_choices.get("narrative_context", "No narrative context available"))
    print("\n=== Raw Choices for New Scene ===")
    print(new_scene_choices.get("formatted_text", "No choices available"))
    
    # Verify narrative for new scene was sent to websocket
    new_scene_messages = mock_ws.get_narrative_messages()
    print(f"\n=== Websocket New Scene Messages: {len(new_scene_messages)} ===")
    for i, msg in enumerate(new_scene_messages):
        print(f"\nMessage {i+1}:")
        print(f"Type: {msg.get('type')}")
        print(f"Scene ID: {msg.get('scene_id')}")
        print(f"Content: {msg.get('text')[:100]}...")
    
    # Test scene description with websocket
    print("\n=== Testing Scene Description with Websocket ===")
    mock_ws = MockWebSocket()
    await engine.describe_scene("look around", websocket=mock_ws)
    
    # Verify scene description was sent to websocket
    description_messages = mock_ws.get_narrative_messages()
    print(f"\n=== Websocket Description Messages: {len(description_messages)} ===")
    for i, msg in enumerate(description_messages):
        print(f"\nMessage {i+1}:")
        print(f"Type: {msg.get('type')}")
        print(f"Scene ID: {msg.get('scene_id')}")
        print(f"Content: {msg.get('text')[:100]}...")

async def test_narrative_flow_no_websocket():
    """Test the enhanced narrative flow without websocket integration."""
    print("\n=== Testing Enhanced Narrative Flow (No Websocket) ===\n")
    
    # Initialize the game engine with the Last Oracle scenario
    scenario_path = Path(__file__).parent.parent.parent / "scenarios" / "last_oracle.json"
    engine = GameEngine(str(scenario_path))
    
    # Set the initial scene
    engine.set_current_scene("temple_entrance")
    
    # Get the choices for the current scene with enhanced narrative
    choices_data = await engine.get_choices_for_current_scene()
    
    # Print the enhanced narrative context
    print("=== Enhanced Narrative Context ===")
    print(choices_data.get("narrative_context", "No narrative context available"))
    
    # Simulate making a choice
    outcome = await engine.process_choice_selection(0)  # Choose the first option
    print(f"Outcome: {outcome.get('text', 'No outcome text')}")
    
    # Verify the outcome has the expected fields
    assert "type" in outcome, "Outcome should have a 'type' field"
    assert "text" in outcome, "Outcome should have a 'text' field"
    assert "timestamp" in outcome, "Outcome should have a 'timestamp' field"
    assert "format" in outcome, "Outcome should have a 'format' field"
    
    print("All tests passed!")

async def test_scene_info_in_narrative():
    """Test that scene information is properly included in the narrative object sent to the frontend."""
    print("\n=== Testing Scene Information in Narrative Objects ===\n")
    
    # Initialize the game engine with the Last Oracle scenario
    scenario_path = Path(__file__).parent.parent.parent / "scenarios" / "last_oracle.json"
    engine = GameEngine(str(scenario_path))
    
    # Create a mock websocket
    mock_ws = MockWebSocket()
    
    # Test different scenes to ensure scene info is consistently included
    test_scenes = ["temple_entrance", "inner_sanctum", "king_s_coronation"]
    
    for scene_id in test_scenes:
        print(f"\nTesting scene: {scene_id}")
        
        # Set the current scene
        engine.set_current_scene(scene_id)
        
        # Get the choices for the current scene with enhanced narrative
        await engine.get_choices_for_current_scene(websocket=mock_ws)
        
        # Get narrative messages sent to the websocket
        narrative_messages = mock_ws.get_narrative_messages()
        
        # There should be at least one narrative message
        assert len(narrative_messages) > 0, f"No narrative messages sent for scene {scene_id}"
        
        # Check the latest narrative message
        latest_message = narrative_messages[-1]
        
        # Verify scene information is included
        print(f"Checking narrative message for scene {scene_id}:")
        print(f"  - Has 'type': {'type' in latest_message}")
        print(f"  - Has 'scene_id': {'scene_id' in latest_message}")
        print(f"  - Has 'format': {'format' in latest_message}")
        print(f"  - Has 'timestamp': {'timestamp' in latest_message}")
        print(f"  - Has 'text': {'text' in latest_message}")
        
        # Assert that required fields are present
        assert "type" in latest_message, "Narrative message should have 'type' field"
        assert "scene_id" in latest_message, "Narrative message should have 'scene_id' field"
        assert "format" in latest_message, "Narrative message should have 'format' field"
        assert "timestamp" in latest_message, "Narrative message should have 'timestamp' field"
        assert "text" in latest_message, "Narrative message should have 'text' field"
        
        # Assert that scene_id matches the expected scene
        assert latest_message["scene_id"] == scene_id, f"Expected scene_id '{scene_id}', got '{latest_message.get('scene_id')}'"  
        
        # Reset the mock websocket for the next test
        mock_ws = MockWebSocket()
    
    # Test scene description to ensure scene info is included
    print("\nTesting scene description:")
    mock_ws = MockWebSocket()
    engine.set_current_scene("temple_entrance")
    await engine.describe_scene("look around", websocket=mock_ws)
    
    # Get narrative messages sent to the websocket
    description_messages = mock_ws.get_narrative_messages()
    
    # There should be at least one narrative message
    assert len(description_messages) > 0, "No narrative messages sent for scene description"
    
    # Check the latest description message
    latest_desc = description_messages[-1]
    
    # Verify scene information is included in description
    print("Checking scene description message:")
    print(f"  - Has 'scene_id': {'scene_id' in latest_desc}")
    assert "scene_id" in latest_desc, "Scene description should have 'scene_id' field"
    assert latest_desc["scene_id"] == "temple_entrance", f"Expected scene_id 'temple_entrance', got '{latest_desc.get('scene_id')}'"  
    
    # Test scene transition to ensure scene info is updated
    print("\nTesting scene transition:")
    mock_ws = MockWebSocket()
    engine.set_current_scene("temple_entrance")
    await engine.process_choice_selection(0, websocket=mock_ws)  # Choose the first option (Enter the temple)
    
    # Get narrative messages sent to the websocket
    transition_messages = mock_ws.get_narrative_messages()
    
    # Find the message with is_new_scene flag
    new_scene_messages = [msg for msg in transition_messages if msg.get("is_new_scene", False)]
    
    # There should be a message for the new scene
    assert len(new_scene_messages) > 0, "No new scene message sent during transition"
    
    # Check the new scene message
    new_scene_msg = new_scene_messages[0]
    
    # Verify scene information is updated in the new scene message
    print("Checking new scene message:")
    print(f"  - Has 'scene_id': {'scene_id' in new_scene_msg}")
    print(f"  - Has 'is_new_scene': {'is_new_scene' in new_scene_msg}")
    assert "scene_id" in new_scene_msg, "New scene message should have 'scene_id' field"
    assert new_scene_msg["scene_id"] == "inner_sanctum", f"Expected scene_id 'inner_sanctum', got '{new_scene_msg.get('scene_id')}'"  
    assert new_scene_msg["is_new_scene"], "New scene message should have 'is_new_scene' set to True"
    
    print("\nAll scene information tests passed!")

async def test_coronation_scene_narrative():
    """Test the enhanced narrative flow with the King's Coronation scene from Last Oracle scenario."""
    print("\n=== Testing Coronation Scene Narrative Flow ===\n")
    
    # Initialize the game engine with the Last Oracle scenario
    scenario_path = Path(__file__).parent.parent.parent / "scenarios" / "last_oracle.json"
    engine = GameEngine(str(scenario_path))
    
    # Create a mock websocket
    mock_ws = MockWebSocket()
    
    # Set the scene directly to the coronation scene
    engine.set_current_scene("king_s_coronation")
    
    # Get the choices for the coronation scene with enhanced narrative
    choices_data = await engine.get_choices_for_current_scene(websocket=mock_ws)
    
    # Print the enhanced narrative context
    print("=== Enhanced Narrative Context for Coronation Scene ===")
    print(choices_data.get("narrative_context", "No narrative context available"))
    print("\n=== Raw Choices for Coronation Scene ===")
    print(choices_data.get("formatted_text", "No choices available"))
    
    # Verify narrative was sent to websocket
    narrative_messages = mock_ws.get_narrative_messages()
    print(f"\n=== Websocket Narrative Messages: {len(narrative_messages)} ===")
    for i, msg in enumerate(narrative_messages):
        print(f"\nMessage {i+1}:")
        print(f"Type: {msg.get('type')}")
        print(f"Scene ID: {msg.get('scene_id')}")
        print(f"Format: {msg.get('format')}")
        print(f"Content: {msg.get('text')[:100]}...")
    
    # Test scene description for the coronation scene
    print("\n=== Testing Coronation Scene Description ===")
    mock_ws = MockWebSocket()
    await engine.describe_scene("observe the false king", websocket=mock_ws)
    
    # Verify scene description was sent to websocket
    description_messages = mock_ws.get_narrative_messages()
    print(f"\n=== Websocket Description Messages: {len(description_messages)} ===")
    for i, msg in enumerate(description_messages):
        print(f"\nMessage {i+1}:")
        print(f"Type: {msg.get('type')}")
        print(f"Scene ID: {msg.get('scene_id')}")
        print(f"Content: {msg.get('text')[:100]}...")
    
    # Verify the scene ID is correct
    assert len(narrative_messages) > 0, "No narrative messages sent for coronation scene"
    assert narrative_messages[0]["scene_id"] == "king_s_coronation", f"Expected scene_id 'king_s_coronation', got '{narrative_messages[0].get('scene_id')}'"  
    
    print("\nCoronation scene narrative flow test passed!")

if __name__ == "__main__":
    # Run all tests
    asyncio.run(test_narrative_flow())
    print("\n" + "-"*50 + "\n")
    asyncio.run(test_narrative_flow_no_websocket())
    print("\n" + "-"*50 + "\n")
    asyncio.run(test_scene_info_in_narrative())
    print("\n" + "-"*50 + "\n")
    asyncio.run(test_coronation_scene_narrative())
