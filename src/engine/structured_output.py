"""
Structured output models for the Chronicle Engine.

This module demonstrates two approaches to structured output with Pydantic AI:
1. ToolOutput with Pydantic models
2. StructuredDict with JSON schema

These are used to ensure AI responses follow a specific structure.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from pydantic_ai.output import ToolOutput
from pydantic_ai import StructuredDict

# --- ToolOutput with Pydantic Models ---

class NarrativeResponse(BaseModel):
    """Structured response for narrative text."""
    type: str = "narrative"
    text: str
    scene_id: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    format: str = "markdown"
    is_new_scene: bool = False

class NPCResponse(BaseModel):
    """Structured response for NPC dialogue."""
    type: str = "npc_speak"
    name: str
    text: str
    npc_id: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class ChoiceOutcome(BaseModel):
    """Structured response for choice outcomes."""
    type: str = "narrative"
    text: str
    success: bool
    next_scene: Optional[str] = None
    event_id: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    format: str = "markdown"

# Create ToolOutput instances for use with Pydantic AI agents
narrative_output = ToolOutput(NarrativeResponse)
npc_output = ToolOutput(NPCResponse)
choice_outcome_output = ToolOutput(ChoiceOutcome)

# --- StructuredDict with JSON Schema ---

# Schema for generating new scenarios
scenario_schema = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "description": {"type": "string"},
        "setting": {"type": "string"},
        "scenes": {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "choices": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "text": {"type": "string"},
                                "outcome": {"type": "string"},
                                "next_scene": {"type": "string"}
                            },
                            "required": ["text", "outcome"]
                        }
                    }
                },
                "required": ["name", "description", "choices"]
            }
        },
        "npcs": {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "system_prompt": {"type": "string"}
                },
                "required": ["name", "description"]
            }
        }
    },
    "required": ["title", "description", "setting", "scenes"]
}

# Create StructuredDict instance for scenario generation
scenario_generator = StructuredDict(scenario_schema)
