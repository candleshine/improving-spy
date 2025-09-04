# tools/scenario_generator.py
"""
Standalone utility to generate scenario files using Ollama and structured output.
Supports command-line configuration for title, genre, and custom guidance.
"""
import json
import os
import argparse
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.output import ToolOutput
from pydantic_core import to_jsonable_python

# --- Configuration ---
SCENARIOS_DIR = "scenarios"
os.makedirs(SCENARIOS_DIR, exist_ok=True)


# --- Pydantic Models for Structured Output ---
class NPCModel(BaseModel):
    name: str = Field(..., description="Full name of the NPC")
    role: str = Field(..., description="Role in the story")
    personality: str = Field(..., description="Personality traits")
    system_prompt: str = Field(..., description="AI instructions for this NPC")


class ClueModel(BaseModel):
    description: str = Field(..., description="What the player discovers")
    location: str = Field(..., description="Scene ID where it appears")


class QuestModel(BaseModel):
    status: str = Field(..., description="unlocked, hidden, in_progress, completed, failed")
    description: str = Field(..., description="Player's goal")


class ChoiceModel(BaseModel):
    text: str = Field(..., description="Player choice text")
    next_scene: Optional[str] = Field(None, description="ID of next scene")
    tool: Optional[str] = Field(None, description="Tool to use, e.g., roll_dice")
    item: Optional[str] = Field(None, description="Required item")
    success: Optional[str] = Field(None, description="Event ID on success")
    fail: Optional[str] = Field(None, description="Event ID on failure")
    trigger: Optional[str] = Field(None, description="Event ID to trigger")


class EventModel(BaseModel):
    narrative: Optional[str] = Field(None, description="What happens")
    trigger_quest: Optional[str] = Field(None, description="Quest to update")
    status: Optional[str] = Field(None, description="New quest status")
    clue: Optional[str] = Field(None, description="Clue revealed")


class SceneModel(BaseModel):
    narrative: str = Field(..., description="The story text for this scene")


class ScenarioModel(BaseModel):
    title: str = Field(..., description="Compelling title")
    genre: str = Field(..., description="e.g., Spy, Sci-Fi, Fantasy")
    summary: str = Field(..., description="One-paragraph story summary")
    system_prompt: str = Field(..., description="Game Master's core instruction")
    scenes: Dict[str, SceneModel]
    npcs: Dict[str, NPCModel]
    clues: Dict[str, ClueModel]
    quests: Dict[str, QuestModel]
    choices: Dict[str, List[ChoiceModel]]
    events: Dict[str, EventModel]


# --- CLI Setup ---
def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a structured RPG scenario using Ollama and Pydantic AI"
    )
    parser.add_argument("--title", type=str, default="", help="Title of the scenario (optional)")
    parser.add_argument("--genre", type=str, default="", help="Genre: Spy, Sci-Fi, Fantasy, etc. (optional, default: Spy)")
    parser.add_argument("--guidance", type=str, default="", help="Custom guidance for the scenario (e.g., 'a double agent plot') (optional)")
    return parser.parse_args()


# --- Ollama Agent with Structured Output ---
def create_agent() -> Agent:
    return Agent(
        model='ollama:llama3.1',  # Use any Ollama model: llama3.1, mixtral, phi3, etc.
        output_type=ToolOutput(ScenarioModel, name="generate_scenario"),
        # Optional: add tools, history_processors
    )


# --- Save to File ---
def save_scenario(scenario_data: dict, filename: str):
    filepath = Path(SCENARIOS_DIR) / f"{filename}.json"
    safe_data = to_jsonable_python(scenario_data)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(safe_data, f, indent=2, ensure_ascii=False)
    print(f"✅ Scenario saved to {filepath}")


# --- Main ---
def main():
    args = parse_args()

    # Get user inputs
    title = args.title or input("Enter title (e.g., Operation: Shadow Signal) [optional]: ").strip()
    genre = args.genre or input("Enter genre (e.g., Spy, Sci-Fi, Fantasy) [optional, default: Spy]: ").strip()
    guidance = args.guidance or input("Enter scenario guidance (e.g., 'a mole in the agency') [optional]: ").strip()

    # Set defaults if not provided
    if not title:
        title = "Untitled Scenario"
    if not genre:
        genre = "Spy"
    if not guidance:
        guidance = "a tense, choice-driven narrative with moral dilemmas"

    print(f"\n🧠 Generating scenario...")
    print(f"   Title: {title}")
    print(f"   Genre: {genre}")
    print(f"   Theme: {guidance}\n")

    # Create agent
    agent = create_agent()

    # Build prompt dynamically based on provided inputs
    prompt_parts = []
    
    if genre:
        prompt_parts.append(f"Create a {genre}-themed RPG scenario")
    else:
        prompt_parts.append("Create an RPG scenario")
        
    if title and title != "Untitled Scenario":
        prompt_parts.append(f"titled \"{title}\"")
        
    if guidance and guidance != "a tense, choice-driven narrative with moral dilemmas":
        prompt_parts.append(f"that centers on: {guidance}")
    
    # Join the parts with proper punctuation
    prompt = ". ".join(part.strip() for part in prompt_parts if part.strip()) + "."
    
    # Add the rest of the prompt
    prompt += """

A great scenario includes:
- A **strong opening scene** that sets tone and urgency
- At least **3 narrative scenes** with escalating stakes
- **Meaningful choices** that branch the story (e.g., trust vs. betray, fight vs. flee)
- At least **2 NPCs** with distinct personalities, motivations, and dialogue styles
- **1 major twist or revelation** (e.g., a double agent, hidden identity, false memory)
- **1 key clue** that advances the plot when discovered
- **1 active quest** that evolves (e.g., unlocked → in_progress → completed/failed)
- **Moral ambiguity** — no choice should be obviously "right"
- A **satisfying ending** that reflects player decisions

Structure the output exactly as specified in the JSON schema. Include:
- In `choices`: `next_scene`, `tool` (like `roll_dice`), or `item` requirements
- In `events`: consequences like `trigger_quest`, `clue`, or `narrative` updates
- In `npcs`: unique `system_prompt` for each to guide AI behavior

Focus on **atmosphere, tension, and player impact**. This is not a linear story — it's a living world.
Output only the structured data — no explanations.
"""

    try:
        result = agent.run_sync(prompt)
        scenario_model: ScenarioModel = result.output  # ✅ Guaranteed to be valid
        scenario_dict = scenario_model.model_dump()

        # Generate safe filename
        filename = "".join(c for c in title if c.isalnum() or c in " -_").replace(" ", "_").lower()
        filename = filename[:50] or "scenario"

        # Save
        print(f"✅ Generated scenario: '{scenario_model.title}'")
        print(f"📝 Summary: {scenario_model.summary[:100]}...")
        save_scenario(scenario_dict, filename)

        print(f"\n🎮 You can now play it with: ?scenario={filename}")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("Tip: Make sure Ollama is running: `ollama serve`")
        print("Available models: `ollama list`")


if __name__ == "__main__":
    main()