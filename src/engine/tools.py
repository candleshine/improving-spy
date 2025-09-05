"""
Tools for the game engine.
"""
from pydantic import BaseModel
from pydantic_ai.tools import Tool
from typing import List, Dict, Any
import random
import logging

# Set up logging
logger = logging.getLogger("chronicle_engine")

class RollDiceInput(BaseModel):
    """Input model for the dice rolling tool."""
    sides: int = 6
    count: int = 1

def roll_dice(sides: int = 6, count: int = 1) -> List[int]:
    """
    Roll one or more dice with the specified number of sides.
    
    Args:
        sides: Number of sides on each die (default: 6)
        count: Number of dice to roll (default: 1)
        
    Returns:
        List of dice results
    """
    return [random.randint(1, sides) for _ in range(count)]

class DescribeSceneInput(BaseModel):
    """Input model for the scene description tool."""
    query: str  # Changed from id to query to better reflect its purpose

def describe_scene(query: str) -> Dict[str, Any]:
    """
    Retrieve and describe a scene based on user query.
    
    Args:
        query: The user's query about a scene (can be a scene ID or a natural language query)
        
    Returns:
        A dictionary containing scene information and an enhanced description
    """
    from .agents import GameMasterAgent
    from .scene_describer import SceneDescriber
    
    logger.info(f"describe_scene tool called with query: {query}")
    
    # Get scenario data from GameMasterAgent
    scenario_data = GameMasterAgent.scenario_data
    if not scenario_data:
        logger.error("No scenario data available in GameMasterAgent")
        return {
            "scene_id": "unknown",
            "description": "I cannot access scene information at this time.",
            "available_actions": ["explore", "talk", "leave"]
        }
    
    # Get valid scene IDs from scenario data
    scenes = scenario_data.get("scenes", {})
    valid_scene_ids = list(scenes.keys())
    logger.info(f"Valid scene IDs from scenario: {valid_scene_ids}")
    
    if not valid_scene_ids:
        logger.warning("No scenes found in scenario data")
        return {
            "scene_id": "unknown",
            "description": "No scene information is available.",
            "available_actions": ["explore", "talk", "leave"]
        }
    
    # Clean up the input - convert to lowercase and remove extra spaces
    cleaned_query = query.lower().strip()
    
    # Determine which scene we're in (current scene or specified scene)
    current_scene_id = None
    scene_data = None
    
    # Check if the query directly references a scene ID
    for scene_id in valid_scene_ids:
        if scene_id in cleaned_query or scene_id.replace('_', ' ') in cleaned_query:
            current_scene_id = scene_id
            scene_data = scenes[scene_id]
            logger.info(f"Found scene reference in query: {scene_id}")
            break
    
    # If no scene was referenced, use the current scene from context if available
    if not current_scene_id and hasattr(GameMasterAgent, 'current_scene_id'):
        current_scene_id = GameMasterAgent.current_scene_id
        if current_scene_id in scenes:
            scene_data = scenes[current_scene_id]
            logger.info(f"Using current scene from context: {current_scene_id}")
    
    # If we still don't have a scene, use the first available scene
    if not current_scene_id and valid_scene_ids:
        current_scene_id = valid_scene_ids[0]
        scene_data = scenes[current_scene_id]
        logger.info(f"Defaulting to first available scene: {current_scene_id}")
    
    # If we have a scene, generate an enhanced description
    if scene_data:
        # Initialize the scene describer
        scene_describer = SceneDescriber()
        
        # Generate an enhanced description based on the user's query
        enhanced_description = scene_describer.enhance_description_sync(
            scene_data=scene_data,
            user_input=query
        )
        
        # Return the scene information with the enhanced description
        return {
            "scene_id": current_scene_id,
            "description": enhanced_description,
            "base_narrative": scene_data.get("narrative", ""),
            "available_actions": scene_data.get("actions", ["explore", "talk", "leave"])
        }
    
    # If no valid scene could be determined
    logger.warning(f"Could not determine a valid scene for query: '{query}'")
    return {
        "scene_id": "unknown",
        "description": "I'm not sure which area you're referring to. Could you be more specific?",
        "available_actions": ["explore", "talk", "leave"]
    }

# Define the tools
dice_tool = Tool(
    roll_dice,
    name="roll_dice",
    description="Use this to resolve uncertain outcomes: combat, stealth, hacking, etc. Returns a list of integers.",
    strict=True
)

describe_scene_tool = Tool(
    describe_scene,
    name="describe_scene",
    description="Use this to get detailed information about a scene based on a natural language query like 'look around' or 'examine the statue'.",
    strict=True
)
