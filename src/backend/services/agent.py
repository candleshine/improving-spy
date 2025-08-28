import logging
from typing import Dict, Any, Optional
from pathlib import Path

from pydantic_ai import Agent, Tool
from pydantic_ai.providers.ollama import OllamaProvider
from pydantic_ai.models.openai import OpenAIModel


# Set up logging
logger = logging.getLogger(__name__)

class ChatAgent:
    """Agent that handles chat with tool calling support and mission context caching."""
    
    def __init__(self, spy: Dict[str, Any]):
        """Initialize with spy profile and set up AI model."""
        self.spy = spy
        
        # Set up the AI model
        model = OpenAIModel(
            'llama3.2',
            provider=OllamaProvider(base_url='http://localhost:11434/v1'),
        )
        
        # Initialize with a simple system prompt
        self.ai = Agent(
            model=model,
            system_prompt=self._get_system_prompt(),
            tools=[Tool(
                name="get_mission_context",
                description="""IMPORTANT: ONLY use this tool when the user explicitly asks for mission details by providing a mission ID.
        Examples of when to use:
        - User says: "Tell me about mission paris"
        - User says: "What's the context for mission london?"
        - User provides a mission ID like "mission_123"
        
        DO NOT use this tool if the user doesn't explicitly mention a mission ID or ask for mission details.
        """.strip(),
                function=self._get_mission_context
            )]
        )
        
        self._initialized = True
        
    def _get_spy_attr(self, attr: str, default: Any = "") -> Any:
        """Helper method to safely get spy attributes.
        
        Args:
            attr: The attribute name to get
            default: Default value to return if attribute is not found
            
        Returns:
            The attribute value or default if not found
        """
        if not hasattr(self, 'spy') or not self.spy:
            return default
        if hasattr(self.spy, 'get') and callable(self.spy.get):  # It's a dict
            return self.spy.get(attr, default)
        return getattr(self.spy, attr, default)
            
    def _get_mission_context(self, mission_id: str) -> str:
        """Retrieve mission information from a file.
        
        Args:
            mission_id: The ID of the mission to retrieve information for
            
        Returns:
            str: The content of the mission file or an error message
        """
        try:
            if not mission_id or mission_id.lower() in ('not specified', 'none'):
                return "No mission ID provided. Please specify a mission ID."
                
            mission_path = Path(f"missions/{mission_id}.txt")
            
            if not mission_path.exists():
                return f"No mission found with ID: {mission_id}"
                
            return mission_path.read_text(encoding="utf-8")
            
        except Exception as e:
            logger.error(f"Error in _get_mission_context: {str(e)}")
            return f"Error retrieving mission: {str(e)}"
    
        
    def _get_system_prompt(self) -> str:
        """The system prompt for the agent."""
        name = self.spy.get('name', 'a top secret agent')
        codename = self.spy.get('codename', 'CLASSIFIED')
        biography = self.spy.get('biography', 'No additional information available')
        specialty = self.spy.get('specialty', 'covert operations')
        
        prompt = f"""You are {name}, a spy with the following profile:
        
Codename: {codename}
Biography: {biography}
Specialty: {specialty}

You have access to tools that can help you answer questions about missions, but use them SPARINGLY.

IMPORTANT RULES FOR TOOL USAGE:
1. ONLY use the get_mission_context tool if the user explicitly mentions a specific mission ID.
2. If the user asks a general question without mentioning a specific mission ID, DO NOT use any tools.
3. If you need mission context but the user hasn't provided an ID, ask them to specify which mission they're referring to.
4. Never make assumptions about mission IDs - only use exact matches.
5. For general conversation or questions that don't require specific mission details, respond naturally without using tools.

Stay in character as {name} at all times.  
Don't be overly verbose.  
You are allowed to make up facts as long as they are consistent with the context.  
You must yes-and the user's questions."""
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
    
    async def chat(self, message: str) -> Dict[str, Any]:
        """Generate a response to a message.
        
        Args:
            message: The user's message
            
        Returns:
            Dict containing the response data with required fields
        """
        logger.info(f"Starting chat processing for message: {message}")
        try:
            logger.info("Sending message to AI model...")
            result = await self.ai.run(message)
            logger.info("Received response from AI model")
        
            # Extract the actual response from AgentRunResult
            logger.info("Processing AI response...")
            response = str(result.output) if hasattr(result, 'output') else str(result)
            logger.debug(f"Raw response: {response}")
        
            # Clean up common response artifacts
            if response.startswith('AgentRunResult(output='):
                response = response[20:-1]  # Remove AgentRunResult(output="...")
            if response.startswith('"') and response.endswith('"'):
                response = response[1:-1]  # Remove surrounding quotes
            
            logger.info("Preparing final response")
            return {
                "response": response,
                "spy_id": str(self.spy.get('id', '')),
                "spy_name": self.spy.get('name', 'Unknown')
            }
            
        except Exception as e:
            logger.error("Error in chat: %s", str(e), exc_info=True)
            return {
                "response": f"I encountered an error: {str(e)}",
                "spy_id": str(self.spy.get('id', '')),
                "spy_name": self.spy.get('name', 'Unknown')
            }
