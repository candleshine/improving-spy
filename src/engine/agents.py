# engine/agents.py
"""
Agent definitions for the Chronicle Engine.
- GameMasterAgent: Central narrator and story driver
- NPCCatalog: Factory for creating NPC agents from scenario config
"""
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.ollama import OllamaProvider
from typing import Dict, Any, Optional
from datetime import datetime
from .processor import summarize_old_messages
from .tools import dice_tool, describe_scene_tool  # Import tools from the tools module




# --- Game Master Agent ---
class GameMasterAgent:
    """
    The central AI that narrates the world, advances the plot,
    and coordinates interactions.
    Uses tools and history processors for rich gameplay.
    """
    # Class-level agent instance
    agent = None
    # Class-level scenario data
    scenario_data = None
    # Current scene ID
    current_scene_id = None
    
    def __init__(self, model: str = 'qwen3:1.7b', scenario_data: Dict[str, Any] = None):
        # Store scenario data at class level
        if scenario_data:
            GameMasterAgent.scenario_data = scenario_data
            
        if GameMasterAgent.agent is None:  # Only create once
            model = OpenAIModel(
                'qwen3:1.7b',  # Using smaller qwen3:1.7b model for faster responses
                provider=OllamaProvider(base_url='http://localhost:11434/v1'),
            )
            GameMasterAgent.agent = Agent(
                model=model,
                system_prompt=self._get_system_prompt(),
                tools=[dice_tool, describe_scene_tool],
                history_processors=[summarize_old_messages]
            )

    def _get_system_prompt(self) -> str:
        # Enhanced system prompt for better storytelling
        return """
You are the Game Master of a tense, choice-driven, spy-themed RPG.
You are a master storyteller who creates immersive, cinematic experiences.

Your job is to:
- Describe scenes with rich sensory details and atmosphere
- React to player choices with meaningful consequences
- Create emotional stakes and tension
- Develop a narrative arc with rising action
- Maintain consistent tone and pacing
- Never break character or the fourth wall

Storytelling Techniques:
- Use all five senses in descriptions
- Vary sentence length for dramatic effect
- Create moments of tension and release
- Use metaphor and vivid imagery
- Foreshadow future events subtly
- Create memorable character moments

Rules:
- When an NPC speaks, format: [NPC:Name] "Dialogue"
- When a clue is found: [CLUE:Title] "Description"
- When a quest updates: [QUEST:Title] Status: unlocked/completed
- When choices appear: [CHOICE] "Option 1" / "Option 2"

Tools Usage:
- Use the describe_scene tool with natural language queries like "look around" or "examine the statue"
- The describe_scene tool now accepts any descriptive query and will enhance scene descriptions
- For dice rolls, use the roll_dice tool with appropriate sides and count parameters

Special Commands (handled by the system):
- When the player types "look" or "@LOOK", they will get a detailed scene description
- When the player types "@NPC:name message", they will interact directly with that NPC

The player shapes the story. You guide it with artful narration.
"""

    async def run(self, user_input: str, message_history=None):
        return await self.agent.run(user_input, message_history=message_history)

    def run_sync(self, user_input: str, message_history=None):
        return self.agent.run_sync(user_input, message_history=message_history)

    async def run_stream(self, user_input: str, message_history=None):
        return await self.agent.run_stream(user_input, message_history=message_history)


# --- NPC Agent Factory ---
class NPCCatalog:
    """
    Dynamically creates NPC agents from scenario configuration.
    Each NPC has its own personality, memory, and role.
    """
    # Class-level scenario data
    scenario_data = None
    
    def __init__(self, scenario_data: Dict[str, Any] = None):
        self.agents: Dict[str, Agent] = {}
        
        # Store scenario data at instance and class level
        if scenario_data:
            self.scenario_data = scenario_data
            NPCCatalog.scenario_data = scenario_data
            
        self.agent_model=OpenAIModel(
            'llama3',
            provider=OllamaProvider(base_url='http://localhost:11434/v1'),
        )

    def create_npc_agent(self, npc_id: str, config: Dict[str, Any]) -> Agent:
        """
        Create or return cached NPC agent.
        :param npc_id: Unique ID (e.g., 'handler', 'mole')
        :param config: From scenario JSON (name, system_prompt, etc.)
        """
        if npc_id in self.agents:
            return self.agents[npc_id]

        # Use local Ollama model for NPCs
        model = OpenAIModel(
            'llama3.2',  # Using llama3 model
            provider=OllamaProvider(base_url='http://localhost:11434/v1'),
        )
        
        agent = Agent(
            model=model,
            system_prompt=config.get("system_prompt", f"You are {config.get('name', npc_id)}."),
            # Optional: add tools (e.g., lie, persuade)
            history_processors=[summarize_old_messages]
        )
        self.agents[npc_id] = agent
        return agent

    def get_agent(self, npc_id: str) -> Optional[Agent]:
        return self.agents.get(npc_id)

    def clear(self):
        """For testing"""
        self.agents.clear()
        
    async def interact_with_npc(self, npc_id: str, user_input: str, message_history=None) -> Dict[str, Any]:
        """
        Interact with an NPC by sending a message and getting a response.
        
        Args:
            npc_id: The ID of the NPC to interact with
            user_input: The user's message to the NPC
            message_history: Optional message history for context
            
        Returns:
            A dictionary containing the NPC's response and metadata
        """
        # Get the NPC agent
        agent = self.get_agent(npc_id)
        if not agent:
            return {
                "type": "error",
                "text": f"NPC '{npc_id}' not found",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        try:
            # Get NPC config from scenario data
            npc_config = {}
            if self.scenario_data and "npcs" in self.scenario_data:
                npc_config = self.scenario_data["npcs"].get(npc_id, {})
                
            # Run the agent with the user input
            result = await agent.run(user_input, message_history=message_history)
            
            # Extract the response
            response = result.output if hasattr(result, 'output') else str(result)
            
            # Format the response as an NPC message
            npc_name = npc_config.get("name", npc_id)
            return {
                "type": "npc_speak",
                "name": npc_name,
                "text": response,
                "npc_id": npc_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "type": "error",
                "text": f"Error interacting with NPC '{npc_id}': {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }


# --- Global Instances ---
# These can be imported and used across the app
gm_agent = GameMasterAgent()
npc_catalog = NPCCatalog()