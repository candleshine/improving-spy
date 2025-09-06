"""
Choice handling system for the Chronicle Engine.
Processes player choices and their outcomes based on scenario data.
"""
import logging
import random
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

# Set up logging
logger = logging.getLogger("chronicle_engine")

class Choice(BaseModel):
    """Model representing a player choice option."""
    text: str
    next_scene: Optional[str] = None
    tool: Optional[str] = None
    sides: Optional[int] = None
    threshold: Optional[int] = None
    success: Optional[str] = None
    fail: Optional[str] = None
    item: Optional[str] = None
    
class ChoiceOutcome(BaseModel):
    """Model representing the outcome of a choice."""
    success: bool
    next_scene: Optional[str] = None
    event_id: Optional[str] = None
    message: str
    roll_result: Optional[int] = None
    
class ChoiceHandler:
    """
    Handles processing of player choices and their outcomes.
    """
    def __init__(self, scenario_data: Dict[str, Any]):
        """
        Initialize the choice handler with scenario data.
        
        Args:
            scenario_data: The complete scenario data
        """
        self.scenario_data = scenario_data
        self.choices = scenario_data.get("choices", {})
        self.events = scenario_data.get("events", {})
        self.player_inventory = set()  # Track items the player has
        
    def get_choices_for_scene(self, scene_id: str) -> List[Choice]:
        """
        Get available choices for a specific scene.
        
        Args:
            scene_id: The ID of the current scene
            
        Returns:
            List of Choice objects for the scene
        """
        scene_choices = self.choices.get(scene_id, [])
        return [Choice(**choice) for choice in scene_choices]
    
    def format_choices_for_display(self, scene_id: str) -> str:
        """
        Format choices for display to the player.
        
        Args:
            scene_id: The ID of the current scene
            
        Returns:
            Formatted string of choices
        """
        choices = self.get_choices_for_scene(scene_id)
        if not choices:
            return ""
            
        choice_texts = [f"{i+1}. {choice.text}" for i, choice in enumerate(choices)]
        return "[CHOICE] " + " / ".join(f'"{text}"' for text in choice_texts)
    
    def process_choice(self, scene_id: str, choice_index: int) -> ChoiceOutcome:
        """
        Process a player's choice and determine the outcome.
        
        Args:
            scene_id: The current scene ID
            choice_index: The index of the chosen option (0-based)
            
        Returns:
            ChoiceOutcome with the result of the choice
        """
        choices = self.get_choices_for_scene(scene_id)
        
        if not choices or choice_index < 0 or choice_index >= len(choices):
            return ChoiceOutcome(
                success=False,
                message="Invalid choice.",
                next_scene=None
            )
            
        choice = choices[choice_index]
        
        # Simple scene transition
        if choice.next_scene and not choice.tool:
            message = f"You chose to {choice.text.lower()}."
            
            # Check if this scene transition is to an event that might trigger a quest
            event = self.events.get(choice.next_scene, {})
            if event:
                # Use the event narrative if available
                if "narrative" in event:
                    message = event.get("narrative")
                
                # Check for clues in the event
                clue_id = event.get("clue")
                if clue_id:
                    clue = self.scenario_data.get("clues", {}).get(clue_id, {})
                    if clue:
                        message += f"\n\n[CLUE:{clue_id}] \"{clue.get('description', '')}\""
                
                # Check for quest updates in the event
                quest_id = event.get("trigger_quest")
                quest_status = event.get("status")
                if quest_id and quest_status:
                    quest = self.scenario_data.get("quests", {}).get(quest_id, {})
                    if quest:
                        message += f"\n\n[QUEST:{quest_id}] Status: {quest_status} - {quest.get('description', '')}"
            
            return ChoiceOutcome(
                success=True,
                next_scene=choice.next_scene,
                message=message,
                event_id=choice.next_scene if choice.next_scene in self.events else None
            )
            
        # Tool-based choice
        if choice.tool:
            return self._process_tool_choice(choice)
            
        # Default fallback
        return ChoiceOutcome(
            success=True,
            message=f"You chose to {choice.text.lower()}.",
            next_scene=None
        )
    
    def _process_tool_choice(self, choice: Choice) -> ChoiceOutcome:
        """
        Process a choice that involves a tool.
        
        Args:
            choice: The Choice object
            
        Returns:
            ChoiceOutcome with the result
        """
        if choice.tool == "roll_dice":
            return self._process_dice_roll(choice)
        elif choice.tool == "check_inventory":
            return self._process_inventory_check(choice)
        else:
            return ChoiceOutcome(
                success=False,
                message=f"Unknown tool: {choice.tool}",
                next_scene=None
            )
    
    def _process_dice_roll(self, choice: Choice) -> ChoiceOutcome:
        """Process a dice roll choice."""
        sides = choice.sides or 6
        roll_result = random.randint(1, sides)
        threshold = choice.threshold or sides // 2
        
        success = roll_result >= threshold
        event_id = choice.success if success else choice.fail
        
        # Get event details
        event = self.events.get(event_id, {})
        message = event.get("narrative", "")
        
        if not message:
            message = f"You rolled a {roll_result}. " + ("Success!" if success else "Failure.")
        else:
            message = f"You rolled a {roll_result}. {message}"
            
        # Check if this event gives a clue
        clue_id = event.get("clue")
        if clue_id:
            clue = self.scenario_data.get("clues", {}).get(clue_id, {})
            if clue:
                message += f"\n\n[CLUE:{clue_id}] \"{clue.get('description', '')}\""
        
        # Check if this event triggers or updates a quest
        quest_id = event.get("trigger_quest")
        quest_status = event.get("status")
        if quest_id and quest_status:
            quest = self.scenario_data.get("quests", {}).get(quest_id, {})
            if quest:
                message += f"\n\n[QUEST:{quest_id}] Status: {quest_status} - {quest.get('description', '')}"
        
        return ChoiceOutcome(
            success=success,
            next_scene=event.get("next_scene"),
            event_id=event_id,
            message=message,
            roll_result=roll_result
        )
    
    def _process_inventory_check(self, choice: Choice) -> ChoiceOutcome:
        """Process an inventory check choice."""
        required_item = choice.item
        has_item = required_item in self.player_inventory
        
        event_id = choice.success if has_item else choice.fail
        event = self.events.get(event_id, {})
        message = event.get("narrative", "")
        
        if not message:
            if has_item:
                message = f"You use the {required_item}."
            else:
                message = f"You don't have the {required_item}."
        
        # Check if this event gives a clue
        clue_id = event.get("clue")
        if clue_id:
            clue = self.scenario_data.get("clues", {}).get(clue_id, {})
            if clue:
                message += f"\n\n[CLUE:{clue_id}] \"{clue.get('description', '')}\""
        
        # Check if this event triggers or updates a quest
        quest_id = event.get("trigger_quest")
        quest_status = event.get("status")
        if quest_id and quest_status:
            quest = self.scenario_data.get("quests", {}).get(quest_id, {})
            if quest:
                message += f"\n\n[QUEST:{quest_id}] Status: {quest_status} - {quest.get('description', '')}"
        
        return ChoiceOutcome(
            success=has_item,
            next_scene=event.get("next_scene"),
            event_id=event_id,
            message=message
        )
    
    def add_to_inventory(self, item_id: str) -> None:
        """Add an item to the player's inventory."""
        self.player_inventory.add(item_id)
        logger.info(f"Added {item_id} to player inventory")
    
    def remove_from_inventory(self, item_id: str) -> bool:
        """Remove an item from the player's inventory."""
        if item_id in self.player_inventory:
            self.player_inventory.remove(item_id)
            logger.info(f"Removed {item_id} from player inventory")
            return True
        return False
    
    def has_item(self, item_id: str) -> bool:
        """Check if the player has a specific item."""
        return item_id in self.player_inventory
