"""Tools for mission-related operations."""
from typing import Optional, Dict, Any
from pathlib import Path
from pydantic import BaseModel, Field

class MissionContextRequest(BaseModel):
    """Request model for getting mission context."""
    mission_id: str = Field(..., description="The ID of the mission to get context for")

class MissionTools:
    """Tools for mission operations."""
    
    @staticmethod
    def get_mission_context(mission_id: str) -> Dict[str, Any]:
        """
        Retrieve context about a specific mission.
        
        Args:
            mission_id: The ID of the mission to get context for
            
        Returns:
            Dict containing mission context
        """
        try:
            mission_path = Path(f"missions/{mission_id}.txt")
            if not mission_path.exists():
                return {"error": f"Mission {mission_id} not found"}
                
            content = mission_path.read_text(encoding="utf-8")
            return {
                "mission_id": mission_id,
                "content": content,
                "status": "success"
            }
        except Exception as e:
            return {"error": f"Error reading mission file: {str(e)}"}
    
    @classmethod
    def get_tools(cls):
        """Return the list of tools for the agent to use."""
        return [
            {
                "name": "get_mission_context",
                "description": "Retrieve detailed information about a mission for accurate debriefing.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "mission_id": {
                            "type": "string",
                            "description": "Unique ID of the mission to retrieve"
                        }
                    },
                    "required": ["mission_id"]
                },
                "function": cls.get_mission_context
            }
        ]
