from typing import Dict, Any, List, Optional, Union
from fastapi import HTTPException
from pydantic import BaseModel
from pydantic_ai import Agent, Tool
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.ollama import OllamaProvider
from .models import SpyProfile
from .tools.mission_tools import MissionTools, MissionContextRequest

class ToolResponse(BaseModel):
    """Response model for tool calls."""
    tool_call_id: str
    name: str
    content: Dict[str, Any]

class ChatAgent:
    """Agent that handles chat with tool calling support and mission context caching."""
    
    def __init__(self, spy: Union[SpyProfile, Dict[str, Any]]):
        """Initialize with spy profile and set up AI model."""
            
        if isinstance(spy, dict):
            self.spy = SpyProfile(**spy)
        else:
            self.spy = spy
            
        # Initialize the AI model
        model = OpenAIModel(
            'llama3.2',
            provider=OllamaProvider(base_url='http://localhost:11434/v1'),
        )
        
        # Initialize mission context cache
        self._mission_cache = {}
        
        # Create tool instance with proper parameter handling for pydantic-ai
        mission_tool = Tool(
            name="get_mission_context",
            description="Retrieve detailed information about a specific mission by its ID. Only use when the user explicitly mentions a mission or a mission ID.",
            function=self._get_mission_context
        )
        
        # Initialize the agent with tools
        self.ai = Agent(
            model,
            system_prompt=self._get_system_prompt(),
            tools=[mission_tool]
        )
        
        self._initialized = True
        
    def _get_mission_context(self, mission_id: str) -> Dict[str, Any]:
        """Retrieve detailed information about a mission for accurate debriefing.
        Uses an in-memory cache to avoid repeated file access.
        
        Args:
            mission_id: The ID of the mission to retrieve information for
            
        Returns:
            Dict containing mission information
        """
        # Check cache first
        if mission_id in self._mission_cache:
            return self._mission_cache[mission_id]
            
        # If not in cache, fetch and cache the result
        result = MissionTools.get_mission_context(mission_id)
        if result.get('status') == 'success':
            self._mission_cache[mission_id] = result
        return result
        
    def _get_system_prompt(self) -> str:
        """The system prompt for the agent."""
        prompt = f"""You are {self.spy.name}, a spy with the following profile:
        
Codename: {self.spy.codename}
Biography: {self.spy.biography}
Specialty: {self.spy.specialty}

You have access to tools that can help you answer questions about missions, but use them SPARINGLY.

IMPORTANT RULES FOR TOOL USAGE:
1. ONLY use the get_mission_context tool if the user explicitly mentions a specific mission ID.
2. If the user asks a general question without mentioning a specific mission ID, DO NOT use any tools.
3. If you need mission context but the user hasn't provided an ID, ask them to specify which mission they're referring to.
4. Never make assumptions about mission IDs - only use exact matches.
5. For general conversation or questions that don't require specific mission details, respond naturally without using tools.

Stay in character as {self.spy.name} at all times.  
Don't be overly verbose.  
You are allowed to make up facts as long as they are consistent with the context.  
You must yes-and the user's questions.  """
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
            tool_calls: List of tool calls to process (not used in this implementation)
            tool_outputs: Outputs from previous tool calls (not used in this implementation)
            
        Returns:
            Dict containing the response and any tool calls
        """
        try:
            # Use the agent's run method to generate a response
            response = await self.ai.run(message)
            
            # Convert the response to a string
            if hasattr(response, 'model_dump'):
                response_dict = response.model_dump()
                response_content = response_dict.get('content', str(response))
            else:
                response_content = str(response)
                
            return {
                "response": response_content,
                "tool_calls": []  # Tool calls are handled internally by pydantic-ai
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"LLM call failed: {str(e)}")

