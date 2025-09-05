# engine/game_engine.py
import json
import logging
# Use relative imports since we're in the same package
from .agents import GameMasterAgent, NPCCatalog
from .choice_handler import ChoiceHandler

# Set up logging
logger = logging.getLogger("chronicle_engine")

# --- Game Engine Class ---
class GameEngine:
    def __init__(self, scenario_path: str):
        with open(scenario_path, 'r') as f:
            self.scenario = json.load(f)

        # Initialize NPC catalog with scenario data
        self.npc_catalog = NPCCatalog(scenario_data=self.scenario)
        
        # Initialize GameMasterAgent with scenario data and get the agent instance
        GameMasterAgent(scenario_data=self.scenario)
        self.agent = GameMasterAgent.agent  # Access the underlying Pydantic AI Agent

        # Pre-create NPC agents
        for npc_id, config in self.scenario.get("npcs", {}).items():
            self.npc_catalog.create_npc_agent(npc_id, config)
            
        # Initialize the choice handler
        self.choice_handler = ChoiceHandler(self.scenario)

    async def run_turn(self, user_input: str, history: list):
        result = await self.agent.run(user_input, message_history=history)
        return result.output

    def get_scene(self, scene_id: str):
        """Get scene data by ID."""
        scene_data = self.scenario["scenes"].get(scene_id)
        if scene_data:
            # Update the current scene in GameMasterAgent
            from .agents import GameMasterAgent
            GameMasterAgent.current_scene_id = scene_id
        return scene_data
    
    def set_current_scene(self, scene_id: str) -> bool:
        """Set the current scene for the game."""
        if scene_id in self.scenario.get("scenes", {}):
            from .agents import GameMasterAgent
            GameMasterAgent.current_scene_id = scene_id
            return True
        return False
    
    def get_current_scene_id(self) -> str:
        """Get the current scene ID."""
        from .agents import GameMasterAgent
        return GameMasterAgent.current_scene_id
    
    async def describe_scene(self, query: str, history=None):
        """Generate an enhanced scene description based on user query."""
        from .scene_describer import SceneDescriber
        from .agents import GameMasterAgent
        
        # Get the current scene ID
        current_scene_id = GameMasterAgent.current_scene_id
        
        # If no current scene is set, try to find one in the query or use the first scene
        if not current_scene_id:
            scenes = self.scenario.get("scenes", {})
            scene_ids = list(scenes.keys())
            
            # Try to find a scene mentioned in the query
            cleaned_query = query.lower().strip()
            for scene_id in scene_ids:
                if scene_id in cleaned_query or scene_id.replace('_', ' ') in cleaned_query:
                    current_scene_id = scene_id
                    GameMasterAgent.current_scene_id = scene_id
                    break
            
            # If still no scene, use the first one
            if not current_scene_id and scene_ids:
                current_scene_id = scene_ids[0]
                GameMasterAgent.current_scene_id = current_scene_id
        
        # Get the scene data
        scene_data = self.get_scene(current_scene_id) if current_scene_id else None
        
        if not scene_data:
            return {
                "type": "narrative",
                "text": "I'm not sure which area you're in. Could you be more specific?"
            }
        
        # Create a scene describer
        scene_describer = SceneDescriber()
        
        # Generate an enhanced description
        description = await scene_describer.enhance_description(
            scene_data=scene_data,
            user_input=query
        )
        
        # Return as a narrative message
        return {
            "type": "narrative",
            "text": description,
            "scene_id": current_scene_id
        }
        
    async def interact_with_npc(self, npc_id: str, user_input: str, history=None):
        """
        Interact with an NPC directly.
        
        Args:
            npc_id: The ID of the NPC to interact with
            user_input: The user's message to the NPC
            history: Optional message history for context
            
        Returns:
            The NPC's response as a formatted event
        """
        return await self.npc_catalog.interact_with_npc(npc_id, user_input, history)
        
    def get_choices_for_current_scene(self) -> dict:
        """
        Get available choices for the current scene.
        
        Returns:
            Dictionary with choice information and formatted text
        """
        current_scene_id = self.get_current_scene_id()
        if not current_scene_id:
            return {
                "available": False,
                "message": "No current scene set."
            }
            
        choices = self.choice_handler.get_choices_for_scene(current_scene_id)
        formatted_choices = self.choice_handler.format_choices_for_display(current_scene_id)
        
        return {
            "available": len(choices) > 0,
            "choices": [choice.dict() for choice in choices],
            "formatted_text": formatted_choices,
            "scene_id": current_scene_id
        }
    
    async def process_choice_selection(self, choice_index: int) -> dict:
        """
        Process a player's choice selection.
        
        Args:
            choice_index: The index of the chosen option (0-based)
            
        Returns:
            Dictionary with the outcome information
        """
        current_scene_id = self.get_current_scene_id()
        if not current_scene_id:
            return {
                "type": "error",
                "text": "No current scene set. Cannot process choice."
            }
            
        # Process the choice
        outcome = self.choice_handler.process_choice(current_scene_id, choice_index)
        
        # Handle scene transition if needed
        if outcome.next_scene:
            self.set_current_scene(outcome.next_scene)
            
        # Return formatted response
        return {
            "type": "narrative",
            "text": outcome.message,
            "success": outcome.success,
            "next_scene": outcome.next_scene,
            "event_id": outcome.event_id
        }
        
    def add_item_to_inventory(self, item_id: str) -> bool:
        """
        Add an item to the player's inventory.
        
        Args:
            item_id: The ID of the item to add
            
        Returns:
            True if the item was added successfully
        """
        self.choice_handler.add_to_inventory(item_id)
        return True
        
    def check_inventory(self, item_id: str) -> bool:
        """
        Check if the player has a specific item.
        
        Args:
            item_id: The ID of the item to check for
            
        Returns:
            True if the player has the item
        """
        return self.choice_handler.has_item(item_id)