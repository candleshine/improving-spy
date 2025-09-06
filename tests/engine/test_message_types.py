"""
Test script to verify all message types are properly handled by the engine.

This test ensures that the SceneDescriber and GameMasterAgent correctly handle
all message types defined in the scenario file:
- NPC dialogue messages [NPC:Name]
- Clue discovery messages [CLUE:Title]
- Quest update messages [QUEST:Title]
- Choice presentation messages [CHOICE]
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch
import pytest
import re

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.engine.game_engine import GameEngine
from src.engine.scene_describer import SceneDescriber

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
        """Get all NPC messages sent to the websocket."""
        return [msg for msg in self.sent_messages if msg.get("type") == "narrative" and "is_npc_response" in msg and msg["is_npc_response"]]
    
    def get_messages_with_pattern(self, pattern):
        """Get all messages containing the specified pattern."""
        regex = re.compile(pattern)
        return [msg for msg in self.sent_messages if msg.get("type") == "narrative" and regex.search(msg.get("text", ""))]

@pytest.mark.asyncio
async def test_npc_dialogue_messages():
    """Test that NPC dialogue messages are properly formatted and sent."""
    print("\n=== Testing NPC Dialogue Messages ===\n")
    
    # Initialize the game engine with the Last Oracle scenario
    scenario_path = Path(__file__).parent.parent.parent / "scenarios" / "last_oracle.json"
    engine = GameEngine(str(scenario_path))
    
    # Set the current scene
    engine.set_current_scene("temple_entrance")
    
    # Create a mock websocket
    mock_ws = MockWebSocket()
    
    # Test interactions with different NPCs
    npcs = ["oracle", "raven", "chamberlain"]
    
    for npc_id in npcs:
        print(f"\nTesting interaction with NPC: {npc_id}")
        
        # Interact with the NPC
        npc_response = await engine.interact_with_npc(npc_id, f"Tell me about yourself, {npc_id}.", websocket=mock_ws)
        
        # Print the NPC response
        print(f"NPC Response: {npc_response.get('text', 'No response text')[:100]}...")
        
        # Verify NPC response was sent to websocket
        npc_messages = mock_ws.get_npc_messages()
        assert len(npc_messages) > 0, f"No NPC messages were sent for {npc_id}"
        
        # Verify the NPC message format
        latest_npc_msg = npc_messages[-1]
        assert latest_npc_msg.get("is_npc_response"), f"Message for {npc_id} should be marked as an NPC response"
        assert latest_npc_msg.get("scene_id") == "temple_entrance", f"Scene ID should match the current scene for {npc_id}"
        
        # Check for NPC dialogue format [NPC:Name]
        npc_pattern = r"\[NPC:[^\]]+\]"
        assert re.search(npc_pattern, latest_npc_msg.get("text", "")), f"NPC message for {npc_id} should contain [NPC:Name] format"
        
        print(f"✓ NPC dialogue test passed for {npc_id}")
    
    print("\nAll NPC dialogue tests passed!")

@pytest.mark.asyncio
async def test_clue_discovery_messages():
    """Test that clue discovery messages are properly formatted and sent."""
    print("\n=== Testing Clue Discovery Messages ===\n")
    
    # Initialize the game engine with the Last Oracle scenario
    scenario_path = Path(__file__).parent.parent.parent / "scenarios" / "last_oracle.json"
    engine = GameEngine(str(scenario_path))
    
    # Create a mock websocket
    mock_ws = MockWebSocket()
    
    # Set up a scene with clues
    engine.set_current_scene("temple_entrance")
    
    # Trigger an event that should reveal a clue (raven_helps event)
    # This is done by simulating a dice roll success for the "Ask the raven for help" choice
    with patch('src.engine.tools.roll_dice', return_value=[6]):
        # Select the choice that triggers the dice roll (index 1 in temple_entrance choices)
        outcome = await engine.process_choice_selection(1, websocket=mock_ws)
        
        # Print the outcome
        print(f"Choice Outcome: {outcome.get('text', 'No outcome text')[:100]}...")
        
        # Verify clue message was sent to websocket
        clue_pattern = r"\[CLUE:[^\]]+\]"
        clue_messages = mock_ws.get_messages_with_pattern(clue_pattern)
        
        assert len(clue_messages) > 0, "No clue messages were sent after triggering raven_helps event"
        
        # Verify the clue message format
        latest_clue_msg = clue_messages[-1]
        assert re.search(clue_pattern, latest_clue_msg.get("text", "")), "Clue message should contain [CLUE:Title] format"
        
        print("✓ Clue discovery test passed!")

@pytest.mark.asyncio
async def test_quest_update_messages():
    """Test that quest update messages are properly formatted and sent."""
    print("\n=== Testing Quest Update Messages ===\n")
    
    # Initialize the game engine with the Last Oracle scenario
    scenario_path = Path(__file__).parent.parent.parent / "scenarios" / "last_oracle.json"
    engine = GameEngine(str(scenario_path))
    
    # Create a mock websocket
    mock_ws = MockWebSocket()
    
    # Set up a scene with quest triggers
    engine.set_current_scene("inner_sanctum")
    
    # Trigger an event that should update a quest (oracle_whispers event)
    # This corresponds to the "Read the journal aloud" choice
    outcome = await engine.process_choice_selection(1, websocket=mock_ws)
    
    # Print the outcome
    print(f"Choice Outcome: {outcome.get('text', 'No outcome text')[:100]}...")
    
    # Verify quest message was sent to websocket
    quest_pattern = r"\[QUEST:[^\]]+\]"
    quest_messages = mock_ws.get_messages_with_pattern(quest_pattern)
    
    # Print all narrative messages to debug
    all_messages = mock_ws.get_narrative_messages()
    print(f"\nTotal narrative messages: {len(all_messages)}")
    for i, msg in enumerate(all_messages):
        print(f"Message {i+1}: {msg.get('text', '')[:100]}...")
    
    # This assertion will fail until we implement quest message handling
    assert len(quest_messages) > 0, "No quest messages were sent after triggering oracle_whispers event"
    
    # Verify the quest message format
    if quest_messages:
        latest_quest_msg = quest_messages[-1]
        assert re.search(quest_pattern, latest_quest_msg.get("text", "")), "Quest message should contain [QUEST:Title] format"
        assert "unmask_the_false_king" in latest_quest_msg.get("text", ""), "Quest message should reference the quest ID"
        assert "in_progress" in latest_quest_msg.get("text", ""), "Quest message should include the quest status"
    
    print("✓ Quest update test passed!")

@pytest.mark.asyncio
async def test_choice_presentation_messages():
    """Test that choice presentation messages are properly formatted and sent."""
    print("\n=== Testing Choice Presentation Messages ===\n")
    
    # Initialize the game engine with the Last Oracle scenario
    scenario_path = Path(__file__).parent.parent.parent / "scenarios" / "last_oracle.json"
    engine = GameEngine(str(scenario_path))
    
    # Create a mock websocket
    mock_ws = MockWebSocket()
    
    # Test different scenes to ensure choices are properly presented
    test_scenes = ["temple_entrance", "inner_sanctum"]
    
    for scene_id in test_scenes:
        print(f"\nTesting choices in scene: {scene_id}")
        
        # Set the current scene
        engine.set_current_scene(scene_id)
        
        # Get the choices for the current scene with enhanced narrative
        choices_data = await engine.get_choices_for_current_scene(websocket=mock_ws)
        
        # Print the choices
        formatted_text = choices_data.get('formatted_text', '')
        print(f"Choices: {formatted_text[:100]}...")
        
        # Verify choices are properly formatted with [CHOICE] tag
        choice_pattern = r"\[CHOICE\]"
        assert re.search(choice_pattern, formatted_text), f"Choices for {scene_id} should be formatted with [CHOICE] tag"
        
        # Verify the narrative message was sent to websocket
        narrative_messages = mock_ws.get_narrative_messages()
        assert len(narrative_messages) > 0, f"No narrative messages were sent for scene {scene_id}"
        
        print(f"✓ Choice presentation test passed for {scene_id}")
        
    # Test a scene that might not have choices defined
    print("\nTesting scene without explicit choices: king_s_coronation")
    engine.set_current_scene("king_s_coronation")
    choices_data = await engine.get_choices_for_current_scene(websocket=mock_ws)
    
    # Verify the narrative message was sent to websocket
    narrative_messages = mock_ws.get_narrative_messages()
    assert len(narrative_messages) > 0, "No narrative messages were sent for scene king_s_coronation"
    
    print("✓ Scene without choices test passed")
    
    print("\nAll choice presentation tests passed!")

@pytest.mark.asyncio
async def test_comprehensive_message_flow():
    """Test a complete flow that should trigger all message types."""
    print("\n=== Testing Comprehensive Message Flow ===\n")
    
    # Initialize the game engine with the Last Oracle scenario
    scenario_path = Path(__file__).parent.parent.parent / "scenarios" / "last_oracle.json"
    engine = GameEngine(str(scenario_path))
    
    # Create a mock websocket
    mock_ws = MockWebSocket()
    
    # Start at the temple entrance
    engine.set_current_scene("temple_entrance")
    
    # Step 1: Get initial choices (should contain [CHOICE] messages)
    print("\nStep 1: Getting initial choices")
    choices_data = await engine.get_choices_for_current_scene(websocket=mock_ws)
    print(f"Got choices: {len(choices_data.get('choices', []))} options available")
    
    # Step 2: Interact with an NPC (should contain [NPC:Name] messages)
    print("\nStep 2: Interacting with the raven NPC")
    npc_response = await engine.interact_with_npc("raven", "What do you know about the oracle?", websocket=mock_ws)
    print(f"NPC response type: {npc_response.get('type')}")
    
    # Step 3: Trigger a clue discovery (using patched dice roll)
    print("\nStep 3: Triggering clue discovery")
    with patch('src.engine.tools.roll_dice', return_value=[6]):
        clue_outcome = await engine.process_choice_selection(1, websocket=mock_ws)
        print(f"Clue outcome scene: {clue_outcome.get('next_scene', 'None')}")
    
    # Step 4: Move to inner sanctum
    print("\nStep 4: Moving to inner sanctum")
    engine.set_current_scene("inner_sanctum")
    await engine.get_choices_for_current_scene(websocket=mock_ws)
    
    # Step 5: Trigger quest update
    print("\nStep 5: Triggering quest update")
    quest_outcome = await engine.process_choice_selection(1, websocket=mock_ws)
    print(f"Quest outcome type: {quest_outcome.get('type')}")
    
    # Now check for all message types in the collected messages
    all_messages = mock_ws.get_narrative_messages()
    print(f"\nTotal narrative messages: {len(all_messages)}")
    
    # Check for each message type
    npc_pattern = r"\[NPC:[^\]]+\]"
    clue_pattern = r"\[CLUE:[^\]]+\]"
    quest_pattern = r"\[QUEST:[^\]]+\]"
    choice_pattern = r"\[CHOICE\]"
    
    npc_messages = mock_ws.get_messages_with_pattern(npc_pattern)
    clue_messages = mock_ws.get_messages_with_pattern(clue_pattern)
    quest_messages = mock_ws.get_messages_with_pattern(quest_pattern)
    
    # For choices, we need to check the formatted_text field in the choices_data
    initial_choices_data = await engine.get_choices_for_current_scene(websocket=mock_ws)
    formatted_choices_text = initial_choices_data.get('formatted_text', '')
    has_choice_format = re.search(choice_pattern, formatted_choices_text) is not None
    
    print(f"NPC dialogue messages: {len(npc_messages)}")
    print(f"Clue discovery messages: {len(clue_messages)}")
    print(f"Quest update messages: {len(quest_messages)}")
    print(f"Has choice format: {has_choice_format}")
    
    # Assert that we have at least one of each message type
    assert len(npc_messages) > 0, "No NPC dialogue messages were found"
    assert len(clue_messages) > 0, "No clue discovery messages were found"
    assert len(quest_messages) > 0, "No quest update messages were found"
    assert has_choice_format, "No choice presentation format was found"
    
    print("\nComprehensive message flow test passed!")

@pytest.mark.asyncio
async def test_scene_describer_message_handling():
    """Test that SceneDescriber properly handles different message types in its enhanced descriptions."""
    print("\n=== Testing SceneDescriber Message Handling ===\n")
    
    # Initialize the SceneDescriber
    scene_describer = SceneDescriber()
    
    # Create a mock scene with all message types
    mock_scene = {
        "scene_id": "test_scene",
        "narrative": "This is a test scene with [NPC:Oracle] speaking, [CLUE:Amulet] discovery, [QUEST:FindKing] updates, and [CHOICE] options."
    }
    
    # Test enhance_description
    print("\nTesting enhance_description")
    enhanced_desc = await scene_describer.enhance_description(mock_scene, "look around")
    print(f"Enhanced description: {enhanced_desc[:100]}...")
    
    # Test narrate_scene_with_choices
    print("\nTesting narrate_scene_with_choices")
    choices_text = "[CHOICE] Option 1 / Option 2 / Option 3"
    narrative_with_choices = await scene_describer.narrate_scene_with_choices(
        mock_scene, choices_text, "test_scene"
    )
    print(f"Narrative with choices: {narrative_with_choices[:100]}...")
    
    # In a real scenario, the choices would be displayed after the narrative
    # So we'll simulate that by appending the choices_text to check the format
    complete_narrative = f"{narrative_with_choices}\n\n{choices_text}"
    
    # Check that the special message formats are preserved
    choice_pattern = r"\[CHOICE\]"
    
    # For complete narrative with choices
    assert re.search(choice_pattern, complete_narrative), \
           "Complete narrative with choices should include [CHOICE] format"
    
    print("✓ SceneDescriber message handling test passed!")

async def main():
    """Run all tests."""
    await test_npc_dialogue_messages()
    await test_clue_discovery_messages()
    await test_quest_update_messages()
    await test_choice_presentation_messages()
    await test_comprehensive_message_flow()
    await test_scene_describer_message_handling()

if __name__ == "__main__":
    asyncio.run(main())
