from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel
from pydantic_ai import Agent 
from fastapi import HTTPException
from pathlib import Path
from sqlalchemy.orm import Session
from .models import SpyProfile
from .repositories.spy_repository import SpyRepository
from .tools.mission_tools import MissionTools

class ToolResponse(BaseModel):
    """Response model for tool calls."""
    tool_call_id: str
    name: str
    content: Dict[str, Any]

class ChatAgent:
    """Agent that handles chat with tool calling support."""
    
    def __init__(self, spy: Union[SpyProfile, Dict[str, Any]]):
        """Initialize with spy profile."""
        if isinstance(spy, dict):
            self.spy = SpyProfile(**spy)
        else:
            self.spy = spy
            
        # Initialize tools
        self.tools = MissionTools.get_tools()
        
    def _get_system_prompt(self) -> str:
        """Generate the system prompt for the agent."""
        prompt = f"""You are {self.spy.name}, a spy with the following profile:
        
Codename: {self.spy.codename}
Biography: {self.spy.biography}
Specialty: {self.spy.specialty}

You have access to tools that can help you answer questions about missions. 
When asked about a mission, use the get_mission_context tool to retrieve information.
Stay in character as {self.spy.name} at all times."""
        return prompt
    
    def _get_tool_by_name(self, name: str) -> Optional[Dict]:
        """Get a tool by its name."""
        return next((t for t in self.tools if t["name"] == name), None)
    
    async def _handle_tool_call(self, tool_call: Dict) -> Dict:
        """Handle a single tool call."""
        tool = self._get_tool_by_name(tool_call["name"])
        if not tool:
            return {
                "tool_call_id": tool_call.get("id", ""),
                "error": f"Tool {tool_call['name']} not found"
            }
            
        try:
            result = tool["function"](**tool_call["arguments"])
            return {
                "tool_call_id": tool_call.get("id", ""),
                "name": tool_call["name"],
                "content": result
            }
        except Exception as e:
            return {
                "tool_call_id": tool_call.get("id", ""),
                "error": f"Error executing {tool_call['name']}: {str(e)}"
            }
    
    async def chat(
        self, 
        message: str, 
        tool_calls: Optional[List[Dict]] = None,
        tool_outputs: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Generate a response to a message, handling tool calls if needed.
        
        Args:
            message: The user's message
            tool_calls: List of tool calls to process
            tool_outputs: Outputs from previous tool calls
            
        Returns:
            Dict containing the response and any tool calls
        """
        # Initialize the agent with tools
        ai = Agent(
            'ollama:llama3.1',
            system_prompt=self._get_system_prompt(),
            tools=[{"name": t["name"], "description": t["description"], 
                  "parameters": t["parameters"]} for t in self.tools]
        )
        
        try:
            # If we have tool calls, handle them first
            if tool_calls:
                tool_outputs = []
                for tool_call in tool_calls:
                    output = await self._handle_tool_call(tool_call)
                    tool_outputs.append(output)
                
                # Get the next response with tool outputs
                response = await ai.chat(
                    message,
                    tool_calls=tool_calls,
                    tool_outputs=tool_outputs
                )
            else:
                # Regular chat response
                response = await ai.chat(message)
                
            return {"response": response, "tool_calls": getattr(response, 'tool_calls', [])}
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"LLM call failed: {str(e)}")

# -------------------------------
# Helper Functions
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
# Chat with Message History
# -------------------------------
async def chat_with_context(
    user_message: str,
    spy_data: dict,
    messages: list,
    tool_calls: Optional[List[Dict]] = None,
    tool_outputs: Optional[List[Dict]] = None
) -> Dict[str, Any]:
    """
    Chat with an agent using conversation history for context.
    
    Args:
        user_message: The user's message
        spy_data: Spy profile data
        messages: List of previous messages in the conversation
        tool_calls: List of tool calls to process
        tool_outputs: Outputs from previous tool calls
        
    Returns:
        Dict containing the response and any tool calls
    """
    agent = ChatAgent(spy_data)
    return await agent.chat(user_message, tool_calls, tool_outputs)

# -------------------------------
# Backward Compatibility
# -------------------------------

def chat_with_agent(user_message: str, spy: Union[SpyProfile, Dict[str, Any]], mission_summary: str = None) -> str:
    """Legacy function for backward compatibility."""
    agent = ChatAgent(spy)
    response = agent.chat(user_message)
    return response["response"]

def debrief_mission(message: str, spy_id: str, mission_id: str, db: Session = None) -> str:
    """Legacy function for backward compatibility."""
    # Get spy from repository
    spy_repository = SpyRepository()
    spy = spy_repository.get_sync(db, spy_id)
    
    if not spy:
        raise HTTPException(status_code=404, detail=f"Spy {spy_id} not found")

    mission_summary = load_mission_summary(mission_id)
    response = chat_with_agent(message, spy, mission_summary)
    return response
