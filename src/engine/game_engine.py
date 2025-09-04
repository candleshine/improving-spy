# engine/game_engine.py
from typing import Dict, Any
import json
# Use relative imports since we're in the same package
from .agents import GameMasterAgent, NPCCatalog

# --- Game Engine Class ---
class GameEngine:
    def __init__(self, scenario_path: str):
        with open(scenario_path, 'r') as f:
            self.scenario = json.load(f)

        # Initialize NPC catalog
        self.npc_catalog = NPCCatalog()
        
        # Use the GameMasterAgent instance
        self.agent = GameMasterAgent.agent  # Access the underlying Pydantic AI Agent

        # Pre-create NPC agents
        for npc_id, config in self.scenario.get("npcs", {}).items():
            self.npc_catalog.create_npc_agent(npc_id, config)

    async def run_turn(self, user_input: str, history: list):
        result = await self.agent.run(user_input, message_history=history)
        return result.output

    def get_scene(self, scene_id: str):
        return self.scenario["scenes"].get(scene_id)