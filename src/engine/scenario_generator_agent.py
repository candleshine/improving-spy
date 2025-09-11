"""
Scenario Generator Agent for the Chronicle Engine.

This module demonstrates using StructuredDict for generating structured
scenario data with Pydantic AI.
"""
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.ollama import OllamaProvider
from .structured_output import scenario_generator
import logging

# Set up logging
logger = logging.getLogger("chronicle_engine")

class ScenarioGeneratorAgent:
    """
    Agent that generates complete spy scenarios using StructuredDict.
    
    This demonstrates how to use StructuredDict to ensure the AI returns
    valid JSON that matches a specific schema without defining Pydantic models.
    """
    
    def __init__(self, model_name: str = 'qwen3:1.7b'):
        """Initialize the scenario generator agent with specified model."""
        model = OpenAIModel(
            model_name,
            provider=OllamaProvider(base_url='http://localhost:11434/v1'),
        )
        
        # Create an agent with StructuredDict as output_type
        self.agent = Agent(
            model=model,
            system_prompt=self._get_system_prompt(),
            output_type=scenario_generator  # Use the StructuredDict instance
        )
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for scenario generation."""
        return """
        You are a master spy scenario creator. Your job is to create immersive, 
        detailed spy missions with branching paths and interesting characters.
        
        Create a complete scenario with:
        - An engaging title and description
        - A vivid setting in an international location
        - Multiple interconnected scenes with choices
        - NPCs with distinct personalities and roles
        
        Each scene should have:
        - A descriptive name
        - Rich environmental details
        - 2-4 meaningful choices that affect the story
        
        Each NPC should have:
        - A name and description
        - A system prompt that defines their personality and knowledge
        
        Focus on creating a coherent narrative with rising tension, 
        opportunities for both stealth and action, and meaningful consequences.
        """
    
    async def generate_scenario(self, prompt: str) -> dict:
        """
        Generate a complete scenario based on the user's prompt.
        
        Args:
            prompt: User's request for a specific type of scenario
            
        Returns:
            A dictionary containing the complete scenario data,
            guaranteed to match the schema defined in structured_output.py
        """
        try:
            logger.info(f"Generating scenario based on prompt: {prompt[:50]}...")
            result = await self.agent.run(prompt)
            
            # result.output is guaranteed to match the schema
            scenario_data = result.output
            logger.info(f"Successfully generated scenario: {scenario_data.get('title', 'Untitled')}")
            
            return scenario_data
        except Exception as e:
            logger.error(f"Error generating scenario: {e}")
            # Return a minimal valid scenario as fallback
            return {
                "title": "Error Scenario",
                "description": f"Failed to generate scenario: {str(e)}",
                "setting": "Error State",
                "scenes": {
                    "start": {
                        "name": "Error Scene",
                        "description": "Something went wrong with scenario generation.",
                        "choices": [
                            {
                                "text": "Try again",
                                "outcome": "Let's try generating a scenario again."
                            }
                        ]
                    }
                }
            }
