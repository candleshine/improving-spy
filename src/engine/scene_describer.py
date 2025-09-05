"""
Scene description enhancement using AI.
"""
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.ollama import OllamaProvider
from typing import Dict, Any
import logging

# Set up logging
logger = logging.getLogger("chronicle_engine")

class SceneDescriber:
    """
    Uses a lightweight AI model to enhance scene descriptions based on user input.
    """
    # Class-level agent instance for reuse
    agent = None
    
    def __init__(self, model_name: str = 'qwen3:1.7b'):
        """
        Initialize the SceneDescriber with a lightweight model.
        
        Args:
            model_name: The name of the model to use (default: qwen3:1.7b)
        """
        if SceneDescriber.agent is None:
            logger.info(f"Initializing SceneDescriber with model: {model_name}")
            model = OpenAIModel(
                model_name,
                provider=OllamaProvider(base_url='http://localhost:11434/v1'),
            )
            
            # Create a dedicated agent for scene descriptions
            SceneDescriber.agent = Agent(
                model=model,
                system_prompt=self._get_system_prompt(),
            )
    
    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for the scene description agent.
        """
        return """
You are a descriptive scene generator for a text-based adventure game.
Your job is to enhance scene descriptions based on the base narrative and user's focus.

When given a scene narrative and a user's request (like "look around" or "examine the statue"),
provide a vivid, detailed description that expands on the base narrative.

Keep your descriptions:
- Vivid and atmospheric
- Focused on sensory details
- Relevant to the genre and setting
- Responsive to what the user is specifically looking at

Do not:
- Introduce new plot elements
- Create characters that weren't mentioned
- Contradict the base narrative

Your response should be a single paragraph of rich description.
"""
    
    async def enhance_description(self, 
                                 scene_data: Dict[str, Any], 
                                 user_input: str) -> str:
        """
        Enhance a scene description based on user input.
        
        Args:
            scene_data: The base scene data from the scenario
            user_input: What the user wants to look at or examine
            
        Returns:
            An enhanced description of the scene
        """
        if not scene_data:
            logger.warning("No scene data provided to enhance_description")
            return "I cannot see anything clearly in this area."
        
        # Extract the base narrative
        base_narrative = scene_data.get("narrative", "")
        if not base_narrative:
            logger.warning("Scene data has no narrative field")
            return "This area appears empty and nondescript."
        
        # Create a prompt for the AI
        prompt = f"""
Base Scene Description:
{base_narrative}

User wants to: {user_input}

Please provide an enhanced description focusing on what the user wants to see:
"""
        
        try:
            # Run the agent to get an enhanced description
            logger.info(f"Generating enhanced description for: {user_input}")
            result = await SceneDescriber.agent.run(prompt)
            enhanced_description = result.output if hasattr(result, 'output') else str(result)
            
            logger.info(f"Generated enhanced description: {enhanced_description[:50]}...")
            return enhanced_description
        except Exception as e:
            logger.error(f"Error generating enhanced description: {e}")
            return f"As you look around {scene_data.get('scene_id', 'the area')}, you notice {base_narrative}"
    
    def enhance_description_sync(self, 
                               scene_data: Dict[str, Any], 
                               user_input: str) -> str:
        """
        Synchronous version of enhance_description.
        """
        if not scene_data:
            logger.warning("No scene data provided to enhance_description_sync")
            return "I cannot see anything clearly in this area."
        
        # Extract the base narrative
        base_narrative = scene_data.get("narrative", "")
        if not base_narrative:
            logger.warning("Scene data has no narrative field")
            return "This area appears empty and nondescript."
        
        # Create a prompt for the AI
        prompt = f"""
Base Scene Description:
{base_narrative}

User wants to: {user_input}

Please provide an enhanced description focusing on what the user wants to see:
"""
        
        try:
            # Run the agent to get an enhanced description
            logger.info(f"Generating enhanced description for: {user_input}")
            result = SceneDescriber.agent.run_sync(prompt)
            enhanced_description = result.output if hasattr(result, 'output') else str(result)
            
            logger.info(f"Generated enhanced description: {enhanced_description[:50]}...")
            return enhanced_description
        except Exception as e:
            logger.error(f"Error generating enhanced description: {e}")
            return f"As you look around {scene_data.get('scene_id', 'the area')}, you notice {base_narrative}"
