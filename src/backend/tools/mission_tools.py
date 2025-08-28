"""Tools for mission-related operations."""
import logging
from typing import Dict, Any
from pathlib import Path
from pydantic import BaseModel, Field

# Set up logging
logger = logging.getLogger(__name__)

class MissionContextRequest(BaseModel):
    """Request model for getting mission context."""
    mission_id: str = Field(..., description="The ID of the mission to get context for")

class MissionTools:
    """Tools for mission operations."""
    
    @classmethod
    def get_mission_context(cls, mission_id: str) -> Dict[str, Any]:
        """
        Retrieve context about a specific mission.
        
        Args:
            mission_id: The ID of the mission to get context for
            
        Returns:
            Dict containing mission context with required fields for ChatResponse
        """
        logger.debug("Looking up mission context for mission_id: %s", mission_id)
        mission_path = Path(f"missions/{mission_id}.txt")
        
        if not mission_path.exists():
            logger.info("Mission not found: %s", mission_id)
            return {
                "response": f"No mission details found for mission ID: {mission_id}",
                "spy_id": "",
                "spy_name": "",
                "message": "",
                "tool_calls": []
            }
        
        try:
            logger.debug("Reading mission file: %s", mission_path)
            content = mission_path.read_text(encoding="utf-8")
            
            result = {
                "response": content,
                "spy_id": "",
                "spy_name": "",
                "message": "",
                "tool_calls": []
            }
            
            logger.debug("Successfully retrieved mission context for %s", mission_id)
            return result
            
        except Exception as e:
            error_msg = f"Error reading mission file: {str(e)}"
            logger.error("%s - %s: %s", error_msg, type(e).__name__, str(e))
            return {
                "response": f"Error retrieving mission details: {str(e)}",
                "spy_id": "",
                "spy_name": "",
                "message": "",
                "tool_calls": []
            }
    
    @classmethod
    def get_tools(cls):
        """Return the list of tools for the agent to use."""
        return [
            {
                "name": "get_mission_context",
                "description": "Retrieve detailed information about a specific mission when the user provides a mission ID. Only use this tool when the user explicitly mentions a mission ID. If no mission ID is provided, ask the user to specify which mission they're referring to.",
                "function": cls.get_mission_context,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "mission_id": {
                            "type": "string",
                            "description": "Unique ID of the mission to retrieve"
                        }
                    },
                    "required": ["mission_id"]
                }
            }
        ]
