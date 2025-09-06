"""
Test script to verify client-side handling of all message types from the backend.

This script tests that all message types (NPC dialogue, clues, quests, and choices)
are properly received and processed by the client application when sent from the server.
"""

import asyncio
import json
import sys
import re
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
    """Mock WebSocket client for testing message handling."""
    
    def __init__(self):
        self.received_messages = []
        self.narrative_messages = []
        self.npc_messages = []
        self.clue_messages = []
        self.quest_messages = []
        self.choice_messages = []
        
    def on_message(self, message: Message):
        """Handle a received message."""
        self.received_messages.append(message)
        
        # Process based on message type
        if message.type == MessageType.NARRATIVE:
            self.narrative_messages.append(message)
            self._process_narrative_message(message)
        elif message.type == MessageType.NPC_SPEAK:
            self.npc_messages.append(message)
            logger.info(f"Received NPC message: {message.message_id}")
        elif message.type == MessageType.CHOICE:
            self.choice_messages.append(message)
            logger.info(f"Received choice message: {message.message_id}")
    
    def _process_narrative_message(self, message: Message):
        """Process a narrative message to extract special formats."""
        logger.info(f"Processing narrative message: {message.message_id}")
        
        # Extract text content from the message
        text = ""
        if hasattr(message, 'text') and message.text:
            text = message.text
        elif hasattr(message, 'payload') and isinstance(message.payload, dict):
            text = message.payload.get('text', '')
            if not text and 'content' in message.payload:
                text = message.payload.get('content', '')
        
        # Check for clue patterns
        clue_pattern = r"\[CLUE:[^\]]+\]"
        clue_matches = re.findall(clue_pattern, text)
        if clue_matches:
            logger.info(f"Found clue in narrative: {clue_matches}")
            for clue in clue_matches:
                self.clue_messages.append({
                    "message_id": message.message_id,
                    "clue": clue
                })
        
        # Check for quest patterns
        quest_pattern = r"\[QUEST:[^\]]+\]"
        quest_matches = re.findall(quest_pattern, text)
        if quest_matches:
            logger.info(f"Found quest in narrative: {quest_matches}")
            for quest in quest_matches:
                self.quest_messages.append({
                    "message_id": message.message_id,
                    "quest": quest
                })
    
    def get_narrative_messages(self):
        """Get all narrative messages received."""
        return self.narrative_messages
    
    def get_npc_messages(self):
        """Get all NPC messages received."""
        return self.npc_messages
    
    def get_clue_messages(self):
        """Get all clue messages extracted from narratives."""
        return self.clue_messages
    
    def get_quest_messages(self):
        """Get all quest messages extracted from narratives."""
        return self.quest_messages
    
    def get_choice_messages(self):
        """Get all choice messages received."""
        return self.choice_messages


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
    assert len(narrative_messages) == 1, "Expected 1 narrative message"
    assert narrative_messages[0].type == MessageType.NARRATIVE, "Expected message type to be NARRATIVE"
    assert narrative_messages[0].message_id == "test-narrative-1", "Expected message ID to be test-narrative-1"
    
    payload = narrative_messages[0].payload
    assert isinstance(payload, dict), "Expected payload to be a dictionary"
    assert "text" in payload, "Expected payload to contain 'text'"
    assert "scene_id" in payload, "Expected payload to contain 'scene_id'"
    assert payload["scene_id"] == "temple_entrance", "Expected scene_id to be 'temple_entrance'"
    assert payload["format"] == "markdown", "Expected format to be 'markdown'"
    
    print("✓ Narrative message handling test passed!")


@pytest.mark.asyncio
async def test_npc_dialogue_message_handling():
    """Test that NPC dialogue messages are properly handled by the client."""
    print("\n=== Testing NPC Dialogue Message Handling ===\n")
    
    # Create a mock client
    mock_client = MockWebSocketClient()
    
    # Create a sample NPC dialogue message
    npc_json = json.dumps({
        "type": "npc_speak",
        "message_id": "test-npc-1",
        "timestamp": "2025-09-05T15:05:00Z",
        "payload": {
            "name": "Oracle",
            "content": "[NPC:Oracle] In twilight's hush, where shadows weave and darkness whispers secrets to the wind, I stand vigilant, keeper of forgotten truths and harbinger of what is yet to come.",
            "scene_id": "temple_entrance"
        }
    })
    
    # Parse and process the message
    message = parse_message_from_json(npc_json)
    mock_client.on_message(message)
    
    # Verify the message was processed correctly
    npc_messages = mock_client.get_npc_messages()
    assert len(npc_messages) == 1, "Expected 1 NPC message"
    assert npc_messages[0].type == MessageType.NPC_SPEAK, "Expected message type to be NPC_SPEAK"
    assert npc_messages[0].message_id == "test-npc-1", "Expected message ID to be test-npc-1"
    
    payload = npc_messages[0].payload
    assert isinstance(payload, dict), "Expected payload to be a dictionary"
    assert "name" in payload, "Expected payload to contain 'name'"
    assert "content" in payload, "Expected payload to contain 'content'"
    assert payload["name"] == "Oracle", "Expected name to be 'Oracle'"
    assert "[NPC:Oracle]" in payload["content"], "Expected content to contain '[NPC:Oracle]'"
    
    print("✓ NPC dialogue message handling test passed!")


@pytest.mark.asyncio
async def test_clue_message_handling():
    """Test that clue messages are properly extracted from narrative messages."""
    print("\n=== Testing Clue Message Handling ===\n")
    
    # Create a mock client
    mock_client = MockWebSocketClient()
    
    # Create a sample narrative message with a clue
    narrative_with_clue_json = json.dumps({
        "type": "narrative",
        "message_id": "test-clue-1",
        "timestamp": "2025-09-05T15:10:00Z",
        "payload": {
            "text": "You rolled a 6. The raven lands on your shoulder. 'Fine. The chamberlain knows. But he won't talk unless you have the royal seal.' \n\n[CLUE:journal_entry] \"The true king's seal bears the mark of the serpent, hidden from all but the most observant eye.\"",
            "scene_id": "temple_entrance",
            "format": "markdown"
        }
    })
    
    # Parse and process the message
    message = parse_message_from_json(narrative_with_clue_json)
    mock_client.on_message(message)
    
    # Verify the clue was extracted correctly
    clue_messages = mock_client.get_clue_messages()
    assert len(clue_messages) == 1, "Expected 1 clue message"
    assert clue_messages[0]["message_id"] == "test-clue-1", "Expected message ID to be test-clue-1"
    assert "[CLUE:journal_entry]" in clue_messages[0]["clue"], "Expected clue to contain '[CLUE:journal_entry]'"
    
    print("✓ Clue message handling test passed!")


@pytest.mark.asyncio
async def test_quest_message_handling():
    """Test that quest messages are properly extracted from narrative messages."""
    print("\n=== Testing Quest Message Handling ===\n")
    
    # Create a mock client
    mock_client = MockWebSocketClient()
    
    # Create a sample narrative message with a quest update
    narrative_with_quest_json = json.dumps({
        "type": "narrative",
        "message_id": "test-quest-1",
        "timestamp": "2025-09-05T15:15:00Z",
        "payload": {
            "text": "The oracle's lips move. 'The crown... is a lie.' Then silence. \n\n[QUEST:unmask_the_false_king] Status: in_progress - Find evidence to expose the false king before the coronation.",
            "scene_id": "inner_sanctum",
            "format": "markdown"
        }
    })
    
    # Parse and process the message
    message = parse_message_from_json(narrative_with_quest_json)
    mock_client.on_message(message)
    
    # Verify the quest was extracted correctly
    quest_messages = mock_client.get_quest_messages()
    assert len(quest_messages) == 1, "Expected 1 quest message"
    assert quest_messages[0]["message_id"] == "test-quest-1", "Expected message ID to be test-quest-1"
    assert "[QUEST:unmask_the_false_king]" in quest_messages[0]["quest"], "Expected quest to contain '[QUEST:unmask_the_false_king]'"
    
    print("✓ Quest message handling test passed!")


@pytest.mark.asyncio
async def test_choice_message_handling():
    """Test that choice messages are properly handled by the client."""
    print("\n=== Testing Choice Message Handling ===\n")
    
    # Create a mock client
    mock_client = MockWebSocketClient()
    
    # Create a sample choice message
    choice_json = json.dumps({
        "type": "choice",
        "message_id": "test-choice-1",
        "timestamp": "2025-09-05T15:20:00Z",
        "payload": {
            "options": [
                {"id": 0, "text": "Enter the temple"},
                {"id": 1, "text": "Ask the raven for help"},
                {"id": 2, "text": "Return to the city"}
            ],
            "raw_text": "[CHOICE] \"1. Enter the temple\" / \"2. Ask the raven for help\" / \"3. Return to the city\"",
            "scene_id": "temple_entrance"
        }
    })
    
    # Parse and process the message
    message = parse_message_from_json(choice_json)
    mock_client.on_message(message)
    
    # Verify the message was processed correctly
    choice_messages = mock_client.get_choice_messages()
    assert len(choice_messages) == 1, "Expected 1 choice message"
    assert choice_messages[0].type == MessageType.CHOICE, "Expected message type to be CHOICE"
    assert choice_messages[0].message_id == "test-choice-1", "Expected message ID to be test-choice-1"
    
    payload = choice_messages[0].payload
    assert isinstance(payload, dict), "Expected payload to be a dictionary"
    assert "options" in payload, "Expected payload to contain 'options'"
    assert len(payload["options"]) == 3, "Expected 3 options"
    assert payload["options"][0]["text"] == "Enter the temple", "Expected first option to be 'Enter the temple'"
    assert "[CHOICE]" in payload["raw_text"], "Expected raw_text to contain '[CHOICE]'"
    
    print("✓ Choice message handling test passed!")


@pytest.mark.asyncio
async def test_comprehensive_message_flow():
    """Test a complete flow of messages that should trigger all message types."""
    print("\n=== Testing Comprehensive Message Flow ===\n")
    
    # Create a mock client
    mock_client = MockWebSocketClient()
    
    # Step 1: Initial narrative with scene description
    print("\nStep 1: Initial narrative with scene description")
    narrative_json = json.dumps({
        "type": "narrative",
        "message_id": "flow-narrative-1",
        "timestamp": "2025-09-05T16:00:00Z",
        "payload": {
            "text": "You stand at the entrance to the ancient temple. Stone columns rise around you, their surfaces etched with symbols of a forgotten language. A raven perches on a nearby statue, watching you with intelligent eyes.",
            "scene_id": "temple_entrance",
            "format": "markdown"
        }
    })
    message = parse_message_from_json(narrative_json)
    mock_client.on_message(message)
    
    # Step 2: NPC dialogue
    print("\nStep 2: NPC dialogue")
    npc_json = json.dumps({
        "type": "npc_speak",
        "message_id": "flow-npc-1",
        "timestamp": "2025-09-05T16:01:00Z",
        "payload": {
            "name": "Raven",
            "content": "[NPC:Raven] *Sigh* Another mortal seeking answers. What do you want?",
            "scene_id": "temple_entrance"
        }
    })
    message = parse_message_from_json(npc_json)
    mock_client.on_message(message)
    
    # Step 3: Narrative with clue
    print("\nStep 3: Narrative with clue")
    clue_json = json.dumps({
        "type": "narrative",
        "message_id": "flow-clue-1",
        "timestamp": "2025-09-05T16:02:00Z",
        "payload": {
            "text": "You rolled a 6. The raven tilts its head. 'Very well. Look beneath the statue's base. There's a hidden compartment.' \n\n[CLUE:hidden_compartment] \"A small recess contains a tarnished silver key with an unusual serpent design.\"",
            "scene_id": "temple_entrance",
            "format": "markdown"
        }
    })
    message = parse_message_from_json(clue_json)
    mock_client.on_message(message)
    
    # Step 4: Narrative with quest update
    print("\nStep 4: Narrative with quest update")
    quest_json = json.dumps({
        "type": "narrative",
        "message_id": "flow-quest-1",
        "timestamp": "2025-09-05T16:03:00Z",
        "payload": {
            "text": "As you examine the key, you notice it matches the description in the old legends. This must be the key to the inner sanctum. \n\n[QUEST:find_the_oracle] Status: in_progress - Find the oracle in the inner sanctum of the temple.",
            "scene_id": "temple_entrance",
            "format": "markdown"
        }
    })
    message = parse_message_from_json(quest_json)
    mock_client.on_message(message)
    
    # Step 5: Choice presentation
    print("\nStep 5: Choice presentation")
    choice_json = json.dumps({
        "type": "choice",
        "message_id": "flow-choice-1",
        "timestamp": "2025-09-05T16:04:00Z",
        "payload": {
            "options": [
                {"id": 0, "text": "Enter the temple using the key"},
                {"id": 1, "text": "Ask the raven more questions"},
                {"id": 2, "text": "Return to the city to gather supplies"}
            ],
            "raw_text": "[CHOICE] \"1. Enter the temple using the key\" / \"2. Ask the raven more questions\" / \"3. Return to the city to gather supplies\"",
            "scene_id": "temple_entrance"
        }
    })
    message = parse_message_from_json(choice_json)
    mock_client.on_message(message)
    
    # Verify all message types were processed correctly
    print("\nVerifying all message types were processed correctly")
    
    # Check narrative messages
    narrative_messages = mock_client.get_narrative_messages()
    assert len(narrative_messages) == 3, f"Expected 3 narrative messages, got {len(narrative_messages)}"
    
    # Check NPC messages
    npc_messages = mock_client.get_npc_messages()
    assert len(npc_messages) == 1, f"Expected 1 NPC message, got {len(npc_messages)}"
    assert npc_messages[0].payload["name"] == "Raven", "Expected NPC name to be 'Raven'"
    
    # Check clue messages
    clue_messages = mock_client.get_clue_messages()
    assert len(clue_messages) == 1, f"Expected 1 clue message, got {len(clue_messages)}"
    assert "[CLUE:hidden_compartment]" in clue_messages[0]["clue"], "Expected clue to contain '[CLUE:hidden_compartment]'"
    
    # Check quest messages
    quest_messages = mock_client.get_quest_messages()
    assert len(quest_messages) == 1, f"Expected 1 quest message, got {len(quest_messages)}"
    assert "[QUEST:find_the_oracle]" in quest_messages[0]["quest"], "Expected quest to contain '[QUEST:find_the_oracle]'"
    
    # Check choice messages
    choice_messages = mock_client.get_choice_messages()
    assert len(choice_messages) == 1, f"Expected 1 choice message, got {len(choice_messages)}"
    assert len(choice_messages[0].payload["options"]) == 3, "Expected 3 options in choice message"
    
    print("\n✓ Comprehensive message flow test passed!")


async def main():
    """Run all tests."""
    await test_narrative_message_handling()
    await test_npc_dialogue_message_handling()
    await test_clue_message_handling()
    await test_quest_message_handling()
    await test_choice_message_handling()
    await test_comprehensive_message_flow()

if __name__ == "__main__":
    asyncio.run(main())
