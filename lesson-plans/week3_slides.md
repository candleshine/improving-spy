---
marp: true
theme: default
author: Daniel Chen
title: "🕵️ Week 3: Building Intelligent Agents with PydanticAI"
---

# 🕵️ Week 3: Building Intelligent Agents

## With PydanticAI

### Learning Objectives

- Understand core agentic AI concepts
- Master PydanticAI for LLM interactions
- Implement tool calling and conversation management
- Build a production-ready chat agent
- Implement mission context awareness

---

## What is an Agentic AI System?

### Key Components

- **LLM Core**: Processes and generates text (using Ollama/Llama3)
- **Tools**: Mission context retrieval, conversation management
- **Memory**: Conversation history with persistence
- **Context Awareness**: Mission-specific knowledge integration

### Implementation Highlights

- **Type Safety**: Pydantic models throughout
- **Caching**: Mission context caching for performance
- **Error Handling**: Robust error handling and logging
- **Modular Design**: Separated concerns (agent, tools, repositories)

---

## Session Roadmap

### 1. PydanticAI Fundamentals

- Basic chat interactions
- System prompts and message formatting

### 2. Tool Calling

- Defining tools with Pydantic models
- Basic and advanced tool usage
- Error handling and validation

### 3. Conversation Management

- Message history
- Context windows
- Persistence

### 4. Building the Chat Agent

- Endpoint design
- Error handling
- Testing and deployment

---

## Welcome & Recap

- Review: CRUD API & managing spy profiles
- Today: Your agent goes live!
- New feature: Mission debriefs with contextual memory

---

## Core Implementation

### 1. ChatAgent Initialization

```python
class ChatAgent:
    def __init__(self, spy: Union[SpyProfile, Dict[str, Any]]):
        # Initialize with Ollama provider
        model = OpenAIModel(
            'llama3.2',
            provider=OllamaProvider(base_url='http://localhost:11434/v1'),
        )
        
        # Initialize with mission context tool
        mission_tool = Tool(
            name="get_mission_context",
            description="Retrieve mission details by ID",
            function=self._get_mission_context
        )
        
        self.ai = Agent(
            model,
            system_prompt=self._get_system_prompt(),
            tools=[mission_tool]
        )
        self._mission_cache = {}
```

---

### 2. Mission Context Tool

```python
class MissionTools:
    @staticmethod
    def get_mission_context(mission_id: str) -> Dict[str, Any]:
        """Retrieve mission context from file system."""
        mission_path = Path(f"missions/{mission_id}.txt")
        
        if not mission_path.exists():
            return {
                "mission_id": mission_id,
                "error": f"Mission not found: {mission_id}",
                "status": "error"
            }
            
        try:
            content = mission_path.read_text(encoding="utf-8")
            return {
                "mission_id": mission_id,
                "content": content,
                "status": "success"
            }
        except Exception as e:
            return {
                "mission_id": mission_id,
                "error": str(e),
                "status": "error"
            }
```

---

### 3. Conversation Management

```python
class ConversationRepository:
    def __init__(self):
        self.crud = FastCRUD(model=Conversation)
    
    async def create(self, session: AsyncSession, spy_id: str) -> str:
        """Create a new conversation."""
        conversation_id = str(uuid.uuid4())
        conversation_data = {
            "id": conversation_id,
            "spy_id": spy_id,
            "messages": "[]"
        }
        await self.crud.create(session, conversation_data)
        return conversation_id
```

response = await ai.run("What was my first message?", messages=messages)

```

---

## Install Dependencies

```bash
uv add pydantic-ai ollama
```

- Make sure Ollama is installed and at least one model pulled (e.g., llama2)

---

## 2. Tool Calling with PydanticAI

### Why Use Tools?

- Extend LLM capabilities with custom functions
- Access external data and services
- Maintain clean separation of concerns
- Enable dynamic behavior based on context

---

### A Plain tool

```python
@agent.tool_plain
def get_current_ip_address() -> str:
    """Get public IP address using ifconfig.me website"""
    command = ['curl','ifconfig.me']
    result = subprocess.run(command, capture_output=True, text=True)
    #print(result.stdout)
    return result.stdout
```

---

### Defining a Tool

```python
from pydantic import BaseModel, Field
from typing import Optional

class MissionQuery(BaseModel):
    mission_id: str = Field(..., description="ID of the mission to retrieve")

async def get_mission_context(mission_id: str) -> dict:
    """Fetch mission details by ID."""
    mission_path = Path(f"missions/{mission_id}.txt")
    if not mission_path.exists():
        return {"error": f"Mission {mission_id} not found"}
    return {"content": mission_path.read_text(encoding="utf-8")}
```

### Registering Tools with the Agent

```python
from pydantic_ai import Agent, Tool

# Create tools with type safety
tools = [
    Tool(
        name="get_mission_context",
        description="Get details about a specific mission",
        function=get_mission_context,
        parameters=MissionQuery,
    )
]

# Initialize agent with tools
agent = Agent(
    'ollama/llama2',
    system_prompt="You are a helpful AI assistant.",
    tools=tools
)
```

---

## From Static Prompts to Dynamic Tools

### Old Way: Static Context

```python
prompt = f"""You are {spy.name}. {spy.biography}
Mission Summary: {mission_details}
User: {message}"""
```

### New Way: Dynamic Tool Calling

```python
# Agent can now fetch mission details on demand
response = await agent.chat(
    message="What happened in the Paris mission?",
    tool_calls=[{
        "name": "get_mission_context",
        "arguments": {"mission_id": "paris"}
    }]
)
```

---

## Using the New System

### Basic Chat Example

```python
# Simple chat with no tool calls
response = await client.chat(
    spy_id="spy-123",
    message="Hello, how are you?"
)
print(f"{response['spy_name']}: {response['response']}")
```

---

### Tool Calling in Action

```python
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
```

---

```
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
```

---

### Example Usage

```python
# Start a conversation about a mission
response = await chat_with_tools(
    "What's the status of mission id paris?",
    spy_id="spy-007",
    conversation_id="conv-123"
)
print(f"\nFinal response: {response['response']}")
```

---

## Live Demo: Chat with Tool Calling

```python
class ChatAgent:
    """Agent that handles chat with tool calling support."""
    
    def __init__(self, spy: Union[SpyProfile, Dict[str, Any]]):
        """Initialize with spy profile."""
        if isinstance(spy, dict):
            self.spy = SpyProfile(**spy)
        else:
            self.spy = spy
            
        # Initialize tools from MissionTools
        self.tools = MissionTools.get_tools()
        
    def _get_system_prompt(self) -> str:
        """Generate the system prompt for the agent."""
        return f"""You are {self.spy.name}, a spy with the following profile:
        
Codename: {self.spy.codename}
Biography: {self.spy.biography}
Specialty: {self.spy.specialty}

You have access to tools that can help you answer questions about missions. 
When asked about a mission, use the get_mission_context tool to retrieve information.
Stay in character as {self.spy.name} at all times."""

    async def chat(
        self, 
        message: str, 
        tool_calls: Optional[List[Dict]] = None,
        tool_outputs: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Generate a response to a message, handling tool calls if needed."""
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
```

- The agent now fetches mission details on-demand

---

## Unified Chat with Tool Calling

### Before: Separate Endpoints

- `/chat/{spy_id}` - General chat
- `/debrief/{spy_id}/{mission_id}` - Mission-specific chat

### After: Single Endpoint

- `/chat/{spy_id}` - Handles both modes
- Uses tool calling for mission context
- More flexible and maintainable

### Tool Implementation

```python
class MissionTools:
    @staticmethod
    def get_mission_context(mission_id: str) -> Dict[str, Any]:
        mission_path = Path(f"missions/{mission_id}.txt")
        if not mission_path.exists():
            return {"error": f"Mission {mission_id} not found"}
        content = mission_path.read_text(encoding="utf-8")
        return {"mission_id": mission_id, "content": content}
```

### 1. Tool Definition with Pydantic

```python
from pydantic import BaseModel, Field

class MissionContextRequest(BaseModel):
    """Request model for getting mission context."""
    mission_id: str = Field(..., description="The ID of the mission to get context for")

class MissionTools:
    @staticmethod
    def get_mission_context(mission_id: str) -> Dict[str, Any]:
        """Retrieve mission context with caching."""
        if mission_id in self._mission_cache:
            return self._mission_cache[mission_id]
            
        result = MissionTools.get_mission_context(mission_id)
        if result.get('status') == 'success':
            self._mission_cache[mission_id] = result
        return result
        """Fetch mission details by ID.
        
        Args:
            mission_id: Unique identifier for the mission
            
        Returns:
            Dict containing mission details or error message
        """
        try:
            mission_path = Path(f"missions/{mission_id}.txt")
            if not mission_path.exists():
                return {
                    "status": "error",
                    "message": f"Mission {mission_id} not found",
                    "suggestions": [
                        "Check the mission ID",
                        "Verify mission files exist"
                    ]
                }
            return {
                "status": "success",
                "mission_id": mission_id,
                "content": mission_path.read_text(encoding="utf-8")
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to load mission: {str(e)}"
            }
```

### 2. Create the Agent

```python
class ChatAgent:
    def __init__(self, spy: Dict[str, Any]):
        """Initialize the chat agent with spy profile and tools.
        
        Args:
            spy: Dictionary containing spy profile information
        """
        self.spy = spy
        self.tools = {
            "get_mission_context": {
                "function": MissionTools.get_mission_context,
                "description": "Get details about a specific mission",
                "parameters": {
                    "mission_id": {
                        "type": "string",
                        "description": "ID of the mission to retrieve"
                    }
                }
            },
            # Example of adding a new tool
            "get_asset_status": {
                "function": self._get_asset_status,
                "description": "Check status of a field asset",
                "parameters": {
                    "asset_id": {"type": "string"},
                    "location": {"type": "string", "required": False}
                }
            }
        }
```

---

## This is not RAG

- **R**elational **A**nalysis **G**eneration (RAG):
- tokenizes the documents and stores them in a vector database
- we are using the text as the context for the LLM

---

## 3. Managing Conversations

### Message History

```python
from pydantic_ai.messages import ModelMessage
from typing import List, Optional

class ConversationManager:
    def __init__(self, max_history: int = 10):
        self.max_history = max_history
        self.history: dict[str, List[ModelMessage]] = {}
    
    def add_message(self, conversation_id: str, message: ModelMessage):
        """Add a message to the conversation history."""
        if conversation_id not in self.history:
            self.history[conversation_id] = []
        
        # Add new message
        self.history[conversation_id].append(message)
        
        # Enforce max history
        if len(self.history[conversation_id]) > self.max_history * 2:  # Account for both user and assistant
            self.history[conversation_id] = self.history[conversation_id][-self.max_history * 2:]
    
    def get_messages(self, conversation_id: str) -> List[ModelMessage]:
        """Retrieve conversation history."""
        return self.history.get(conversation_id, [])

# Usage:
manager = ConversationManager()
manager.add_message("conv1", ModelMessage(role="user", content="Hello!"))
```

### Context Windows

- Keep conversation history manageable
- Use rolling window for long conversations
- Consider token limits for your model

### Exercise: Implement Message Persistence

1. Extend `ConversationManager` to save messages to disk
2. Add methods to load/save conversations
3. Implement cleanup for old conversations

---

## 4. Building the Chat Agent

### Complete Chat Endpoint

```python
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()
conversation_manager = ConversationManager()

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

@app.post("/chat/{spy_id}")
async def chat(
    spy_id: str,
    request: ChatRequest,
    conversation_manager: ConversationManager = Depends(get_conversation_manager)
):
    # 1. Get or create conversation
    conversation_id = request.conversation_id or str(uuid.uuid4())
    
    # 2. Get message history
    messages = conversation_manager.get_messages(conversation_id)
    
    # 3. Get or create agent
    agent = get_or_create_agent(spy_id)
    
    try:
        # 4. Generate response
        response = await agent.chat(
            request.message,
            messages=messages
        )
        
        # 5. Update conversation history
        conversation_manager.add_message(
            conversation_id,
            ModelMessage(role="user", content=request.message)
        )
        conversation_manager.add_message(
            conversation_id,
            ModelMessage(role="assistant", content=response["response"])
        )
        
        return {
            "response": response["response"],
            "conversation_id": conversation_id,
            "tool_calls": response.get("tool_calls", [])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Error Handling

- Handle rate limiting
- Validate input
- Manage conversation state
- Log errors appropriately

---

## Build the Chat Endpoint

- `POST /api/chat/{spy_id}`
- `POST /api/debrief/{spy_id}/{mission_id}`
- `POST /api/chat/{spy_id}/conversation/{conversation_id}`
- Retrieve spy, mission data, and conversation history
- Call chat logic, return LLM response
- Try it in `/docs` or with curl/Postman

---

## Homework & Next Steps

- Test chat endpoint with different agents and biographies
- Create mission summary documents and test debriefings
- Implement conversation history storage and retrieval
- Experiment with prompt templates
- Teaser: Next week – multi-agent missions!

---

# Questions?

**Debug LLM setup, ask about agent logic, or share your creative prompts!**
