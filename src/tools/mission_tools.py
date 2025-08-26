"""Tools for mission-related operations."""
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from pydantic import BaseModel, Field

# Set up logging
logger = logging.getLogger(__name__)

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
            Dict containing mission context or string if mission not found
        """
        logger.debug("Looking up mission context for mission_id: %s", mission_id)
        mission_path = Path(f"missions/{mission_id}.txt")
        
        if not mission_path.exists():
            logger.warning("Mission not found: %s", mission_id)
            return {
                "mission_id": mission_id,
                "error": f"Mission not found: {mission_id}",
                "status": "error"
            }
        
        try:
            logger.debug("Reading mission file: %s", mission_path)
            content = mission_path.read_text(encoding="utf-8")
            
            result = {
                "mission_id": mission_id,
                "content": content,
                "status": "success"
            }
            
            logger.debug("Successfully retrieved mission context for %s", mission_id)
            return result
            
        except Exception as e:
            error_msg = f"Error reading mission file: {str(e)}"
            logger.error("%s - %s: %s", error_msg, type(e).__name__, str(e))
            return {
                "mission_id": mission_id,
                "error": f"Error processing mission: {str(e)}",
                "status": "error"
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
