---
marp: true
theme: default
author: Daniel Chen
title: "🕵️ Week 3: Solo Ops – Activating the Agent"
---

# 🕵️ Week 3: Solo Ops
## Activating the Agent

Bring Your Agent to Life – LLM Integration

- Connect your spy agent to an LLM (Ollama + PydanticAI)
- Build a chat endpoint so users can converse with their agent
- Implement mission debriefs with contextual memory
- Focus: Prompt engineering, API integration, and creativity!

---

## Session Roadmap

- Welcome & Recap
- LLMs & PydanticAI Overview
- Live Demo: Prompt Engineering
- Code-Along: Agent Chat Logic
- Mission Debrief Implementation
- Message History & Context Storage
- API Endpoint: Chat with Agent
- Homework & Next Steps

---

## Welcome & Recap

- Review: CRUD API & managing spy profiles
- Today: Your agent goes live!
- New feature: Mission debriefs with contextual memory

---

## What is an LLM?

- **L**arge **L**anguage **M**odel (LLM): An AI that can generate and understand text
- Ollama: Run LLMs locally on your machine
- PydanticAI: Simple Python interface for LLMs with tool calling
- **New**: Tool calling for dynamic data access
- Context loading: Feed documents into your LLM's memory
- Message history: Store conversation context for better responses

---

## Install Dependencies

```bash
uv add pydantic-ai ollama
```

- Make sure Ollama is installed and at least one model pulled (e.g., llama2)

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
async def chat_with_tools(user_message: str, spy_id: str, conversation_id: str = None):
    """Handle a chat message that might require tool calls."""
    # Initial message to the agent
    response = await client.chat(
        spy_id=spy_id,
        message=user_message,
        conversation_id=conversation_id
    )
    
    # Check if tool calls are needed
    while response.get('tool_calls'):
        print("\n[Agent is gathering information...]")
        
        # Process each tool call
        tool_outputs = []
        for tool_call in response['tool_calls']:
            print(f"  - Calling tool: {tool_call['name']}")
            
            # Execute the tool
            result = await execute_tool(tool_call)
            tool_outputs.append({
                'tool_call_id': tool_call['id'],
                'name': tool_call['name'],
                'content': result
            })
        
        # Send tool outputs back to the agent
        response = await client.chat(
            spy_id=spy_id,
            message="Tool outputs received",
            tool_outputs=tool_outputs,
            conversation_id=conversation_id
        )
    
    # Final response from the agent
    return response

async def execute_tool(tool_call: dict) -> dict:
    """Execute a tool call and return the result."""
    tool_name = tool_call['name']
    args = tool_call['arguments']
    
    if tool_name == 'get_mission_context':
        return await MissionTools.get_mission_context(**args)
    elif tool_name == 'get_asset_status':
        return await AssetManager.get_status(**args)
    else:
        return {"error": f"Unknown tool: {tool_name}"}
```

### Example Usage
```python
# Start a conversation about a mission
response = await chat_with_tools(
    "What's the status of Operation Midnight?",
    spy_id="spy-007",
    conversation_id="conv-123"
)
print(f"\nFinal response: {response['response']}")
```

---

## Live Demo: Chat with Tool Calling

```python
class ChatAgent:
    def __init__(self, spy):
        self.spy = spy
        self.tools = {
            "get_mission_context": {
                "function": self.get_mission_context,
                "description": "Get details about a specific mission"
            }
        }

    async def chat(self, message, tool_calls=None, tool_outputs=None):
        ai = Agent('ollama:llama3.1', 
                  system_prompt=self._get_system_prompt(),
                  tools=[self.tools])
        
        if tool_calls:
            tool_outputs = [await self._handle_tool_call(tc) for tc in tool_calls]
            return await ai.chat(message, tool_calls=tool_calls, tool_outputs=tool_outputs)
        return await ai.chat(message)
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

### 1. Define Your Tools
```python
class MissionTools:
    @staticmethod
    def get_mission_context(mission_id: str) -> Dict[str, Any]:
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

## Message History & Context Storage

```python
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter

class ChatDatabase:
    def store_messages(self, conversation_id: str, messages: list[ModelMessage]):
        # Convert messages to JSON and store in database
        messages_json = ModelMessagesTypeAdapter.dump_json(messages)
        self.db.execute(
            "INSERT INTO conversations (id, messages) VALUES (?, ?)",
            (conversation_id, messages_json)
        )
        
    def get_message_history(self, conversation_id: str) -> list[ModelMessage]:
        # Retrieve and deserialize message history
        result = self.db.execute(
            "SELECT messages FROM conversations WHERE id = ?", 
            (conversation_id,)
        )
        row = result.fetchone()
        if row:
            return ModelMessagesTypeAdapter.validate_json(row[0])
        return []
```

---

## Using Message History with PydanticAI

```python
from pydantic_ai import OpenAI

async def chat_with_context(user_message, spy, conversation_id):
    # Get previous messages from database
    message_history = db.get_message_history(conversation_id)
    
    # Create AI instance with context
    ai = OpenAI(model='ollama/llama2')
    
    # Generate response using message history
    result = await ai.run(user_message, message_history=message_history)
    
    # Store updated message history
    db.store_messages(conversation_id, result.new_messages())
    
    return result.content
```

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
