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
from .processor import summarize_old_messages
from .tools import dice_tool  # Import from the tools module




# --- Game Master Agent ---
class GameMasterAgent:
    """
    The central AI that narrates the world, advances the plot,
    and coordinates interactions.
    Uses tools and history processors for rich gameplay.
    """
    # Class-level agent instance
    agent = None
    
    def __init__(self, model: str = 'llama3.2'):
        if GameMasterAgent.agent is None:  # Only create once
            model = OpenAIModel(
                'llama3.2',
                provider=OllamaProvider(base_url='http://localhost:11434/v1'),
            )
            GameMasterAgent.agent = Agent(
                model=model,
                system_prompt=self._get_system_prompt(),
                tools=[dice_tool],  # Add more tools as needed
                history_processors=[summarize_old_messages]
            )

    def _get_system_prompt(self) -> str:
        return """
You are the Game Master of a tense, choice-driven, spy-themed RPG.
Your job is to:
- Describe scenes vividly
- React to player choices
- Introduce consequences
- Raise the stakes
- Keep the story moving forward
- Never break character

Rules:
- When an NPC speaks, format: [NPC:Name] "Dialogue"
- When a clue is found: [CLUE:Title] "Description"
- When a quest updates: [QUEST:Title] Status: unlocked/completed
- When choices appear: [CHOICE] "Option 1" / "Option 2"

The player shapes the story. You guide it.
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
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
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


# --- Global Instances ---
# These can be imported and used across the app
gm_agent = GameMasterAgent()
npc_catalog = NPCCatalog()