# engine/game_engine.py
import json
import logging
from datetime import datetime
# Use relative imports since we're in the same package
from .agents import GameMasterAgent, NPCCatalog
from .choice_handler import ChoiceHandler
from .scene_describer import SceneDescriber

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
        
        # Initialize the scene describer for enhanced narrative
        self.scene_describer = SceneDescriber()

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
    
    async def describe_scene(self, query: str, history=None, websocket=None):
        """Generate an enhanced scene description based on user query."""
        from .scene_describer import SceneDescriber
        from .agents import GameMasterAgent
        import datetime
        
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
                "text": "I'm not sure which area you're in. Could you be more specific?",
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
        
        # Create a scene describer
        scene_describer = SceneDescriber()
        
        # Generate an enhanced description using ToolOutput
        description = await scene_describer.enhance_description(
            scene_data=scene_data,
            user_input=query
        )
        logger.info(f"Generated enhanced description: {description}")
        # Create the response object
        response = {
            "type": "narrative",
            "text": description,
            "scene_id": current_scene_id,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "format": "markdown"  # Better formatting for rich narrative
        }
        
        # If websocket is provided, send the narrative directly
        if websocket:
            try:
                # Log that we're sending a narrative message
                logger.info(f"Sending scene description via websocket for scene: {current_scene_id}")
                logger.debug(f"Scene description content: {description[:100]}...")
                
                # Send the message
                await websocket.send_json(response)
            except Exception as e:
                logger.error(f"Failed to send scene description via websocket: {e}")
        
        return response
        
    async def interact_with_npc(self, npc_id: str, user_input: str, history=None, websocket=None):
        """
        Interact with an NPC directly.
        
        Args:
            npc_id: The ID of the NPC to interact with
            user_input: The user's message to the NPC
            history: Optional message history for context
            websocket: Optional websocket connection to send narrative directly
            
        Returns:
            The NPC's response as a formatted event
        """
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
                    "timestamp": datetime.utcnow().isoformat() if datetime else None,
                    "format": "markdown",  # Better formatting for rich narrative
                    "is_npc_response": True  # Flag to indicate this is an NPC response
                }
                
                # Log that we're sending an NPC response
                logger.info(f"Sending NPC response via websocket for NPC: {npc_id}")
                logger.debug(f"NPC response content: {response['text'][:100]}...")
                
                # Send the message
                await websocket.send_json(narrative_message)
            except Exception as e:
                logger.error(f"Failed to send NPC response via websocket: {e}")
        
        return response
        
    async def get_choices_for_current_scene(self, previous_outcome=None, websocket=None) -> dict:
        """
        Get available choices for the current scene with enhanced narrative context.
        
        Args:
            previous_outcome: Optional outcome from a previous choice for context
            websocket: Optional websocket connection to send narrative directly
            
        Returns:
            Dictionary with choice information, formatted text, and narrative context
        """
        current_scene_id = self.get_current_scene_id()
        if not current_scene_id:
            return {
                "available": False,
                "message": "No current scene set."
            }
            
        # Get the scene data
        scene_data = self.get_scene(current_scene_id)
        if not scene_data:
            return {
                "available": False,
                "message": f"Scene data not found for {current_scene_id}"
            }
            
        # Get choices and format them
        choices = self.choice_handler.get_choices_for_scene(current_scene_id)
        formatted_choices = self.choice_handler.format_choices_for_display(current_scene_id)
        
        # Generate enhanced narrative context before choices
        narrative_context = await self.scene_describer.narrate_scene_with_choices(
            scene_data=scene_data,
            choices_text=formatted_choices,
            scene_id=current_scene_id,
            previous_outcome=previous_outcome
        )
        
        # Create the response object
        response = {
            "available": len(choices) > 0,
            "choices": [choice.dict() for choice in choices],
            "formatted_text": formatted_choices,
            "scene_id": current_scene_id,
            "narrative_context": narrative_context,
            "type": "narrative",  # Ensure type is set for websocket protocol
            "timestamp": datetime.utcnow().isoformat() if datetime else None
        }
        
        # If websocket is provided, send the narrative context directly
        if websocket and narrative_context:
            try:
                # Send as a dedicated narrative message
                narrative_message = {
                    "type": "narrative",
                    "text": narrative_context,
                    "scene_id": current_scene_id,
                    "timestamp": datetime.utcnow().isoformat() if datetime else None,
                    "format": "markdown"  # Better formatting for rich narrative
                }
                
                # Log that we're sending a narrative message
                logger.info(f"Sending narrative context via websocket for scene: {current_scene_id}")
                logger.debug(f"Narrative content: {narrative_context[:100]}...")
                
                # Send the message
                await websocket.send_json(narrative_message)
            except Exception as e:
                logger.error(f"Failed to send narrative context via websocket: {e}")
        
        return response
        
    def get_choices_for_current_scene_sync(self) -> dict:
        """
        Synchronous version of get_choices_for_current_scene without narrative enhancement.
        Used as a fallback when async isn't available.
        
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
    
    async def process_choice_selection(self, choice_index: int, websocket=None) -> dict:
        """
        Process a player's choice selection.
        
        Args:
            choice_index: The index of the chosen option (0-based)
            websocket: Optional websocket connection to send narrative directly
            
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
        result = {
            "type": "narrative",
            "text": outcome.message,
            "success": outcome.success,
            "next_scene": outcome.next_scene,
            "event_id": outcome.event_id,
            "timestamp": datetime.utcnow().isoformat() if datetime else None,
            "format": "markdown"  # Better formatting for rich narrative
        }
        
        # If websocket is provided, send the outcome narrative directly
        if websocket:
            try:
                # Log that we're sending a narrative message
                logger.info(f"Sending choice outcome via websocket: {outcome.message[:50]}...")
                
                # Send the message
                await websocket.send_json(result)
            except Exception as e:
                logger.error(f"Failed to send choice outcome via websocket: {e}")
        
        # If we've transitioned to a new scene, generate a rich narrative for the new scene
        if outcome.next_scene and websocket:
            try:
                # Get the new scene data
                new_scene_data = self.get_scene(outcome.next_scene)
                if new_scene_data:
                    # Generate an enhanced scene description
                    scene_description = await self.scene_describer.enhance_description(
                        scene_data=new_scene_data,
                        user_input="look around"
                    )
                    
                    # Send as a dedicated narrative message
                    scene_message = {
                        "type": "narrative",
                        "text": scene_description,
                        "scene_id": outcome.next_scene,
                        "timestamp": datetime.utcnow().isoformat() if datetime else None,
                        "format": "markdown",  # Better formatting for rich narrative
                        "is_new_scene": True  # Flag to indicate this is a new scene
                    }
                    
                    # Log that we're sending a new scene description
                    logger.info(f"Sending new scene description via websocket for scene: {outcome.next_scene}")
                    
                    # Send the message
                    await websocket.send_json(scene_message)
            except Exception as e:
                logger.error(f"Failed to send new scene description via websocket: {e}")
            
        return result
        
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