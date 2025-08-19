from pydantic_ai import Agent 
from fastapi import HTTPException
from pathlib import Path
from sqlalchemy.orm import Session
from .models import SpyProfile
from .repositories.spy_repository import SpyRepository

# -------------------------------
# Mission Summary Loader
# -------------------------------
def load_mission_summary(mission_id: str) -> str:
    """
    Load a mission summary from a text file.
    """
    mission_path = Path(f"missions/{mission_id}.txt")

    if not mission_path.exists():
        raise HTTPException(status_code=404, detail=f"Mission {mission_id} not found")

    try:
        return mission_path.read_text(encoding="utf-8")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading mission file: {str(e)}")


# -------------------------------
# Core Chat Function
# -------------------------------
def chat_with_agent(user_message: str, spy: SpyProfile, mission_summary: str = None) -> str:
    """
    Generate a response from the agent, optionally with mission context.
    """
    prompt = f"You are {spy.name}, a spy with the following profile:\n\n"
    prompt += f"Codename: {spy.codename}\n"
    prompt += f"Biography: {spy.biography}\n"
    prompt += f"Specialty: {spy.specialty}\n\n"

    if mission_summary:
        prompt += f"Mission Summary: {mission_summary}\n\n"
        prompt += "When asked about this mission, provide details from the mission summary.\n"
        prompt += f"Stay in character as {spy.name} who executed this mission.\n\n"

    prompt += f"User: {user_message}\n"
    prompt += f"Response as {spy.name}: "

    ai = Agent(
    'ollama:llama3.1',
    system_prompt=prompt,
)
    try:
        return ai.run(prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM call failed: {str(e)}")


# -------------------------------
# Debrief Mission Function
# -------------------------------
def debrief_mission(message: str, spy_id: str, mission_id: str, db: Session = None) -> str:
    """
    Generate a mission debrief response from a spy about a specific mission.
    """
    # Get spy from repository
    spy_repository = SpyRepository()
    spy = spy_repository.get_sync(db, spy_id)
    
    if not spy:
        raise HTTPException(status_code=404, detail=f"Spy {spy_id} not found")

    mission_summary = load_mission_summary(mission_id)
    response = chat_with_agent(message, spy, mission_summary)

    return response


# -------------------------------
# Chat with Message History
# -------------------------------
def chat_with_context(
    user_message: str,
    spy_data: dict,
    messages: list
) -> str:
    """
    Chat with an agent using conversation history for context.
    """
    # Build initial prompt
    prompt = f"You are {spy_data['name']}, a spy with the following profile:\n\n"
    prompt += f"Codename: {spy_data['codename']}\n"
    prompt += f"Biography: {spy_data['biography']}\n"
    prompt += f"Specialty: {spy_data['specialty']}\n\n"
    prompt += "Respond naturally to the user while maintaining your persona.\n"

    # Use PydanticAI with message history
    ai = Agent(
        'ollama:llama3.2',
        system_prompt=prompt,
    )
    
    try:
        # Use the message history and current user message
        result = ai.run(prompt + f"\nUser: {user_message}", message_history=messages)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM call failed: {str(e)}")