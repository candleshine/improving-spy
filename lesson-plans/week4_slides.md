---
marp: true
author: Daniel Chen
email: daniel_chen@improving.com
theme: default
---

# Lesson 4: Message History, Multiple Agents & Structured Output

## Building Stateful AI Applications with Pydantic AI

<!-- note -->

---

Welcome back! In this lesson, we’ll go beyond simple AI calls and build a **stateful, interactive AI application** — a text-based RPG engine.

You’ll learn how to:

- Preserve conversation memory
- Chain agent runs
- Use structured output
- Build a real AI-powered game

All using **Pydantic AI**, **FastAPI**, and **Textual**.
<!-- end note -->

---

## Recap: What We’ve Learned

| Lesson | Topic |
|-------|-------|
| 1 | FastAPI, Pydantic `BaseModel`, REST APIs |
| 2 | SQLAlchemy, data persistence |
| 3 | Agents, Tools, `run_sync`, `run_stream` |

---

**Today:**
➡️ Message History  
➡️ Multi-Agent Coordination  
➡️ Structured Output  
➡️ Real-Time Interaction

<!-- note -->
So far, we've managed the state of the agent outside of Pydantic AI.

Today, we give them **memory**, **teamwork**, and **structure**.

This is how you build **real AI applications**, not just demos.
<!-- end note -->

---

## Accessing Messages from Agent Runs

After running an agent, you can access the full conversation.

```python
from pydantic_ai import Agent

model = OpenAIModel(OllamaProvider('gpt-4o'))
agent = Agent(model, system_prompt='Be helpful.')
result = agent.run_sync('Tell me a joke.')

print(result.all_messages())    # Full history
print(result.new_messages())    # Only new messages
```

<!-- note -->

---

`all_messages()` gives you the **complete conversation**, including the system prompt.

`new_messages()` gives you **only the latest exchange** — perfect for passing to the next run.

This is the foundation of **stateful AI apps**.
<!-- end note -->

---

## Continuing a Conversation with `message_history`

Use `message_history` to preserve context across runs.

```python
result1 = agent.run_sync('Tell me a joke.')
result2 = agent.run_sync(
    'Explain?',
    message_history=result1.new_messages()
)
```

✅ The AI remembers the joke  
✅ No need to repeat the system prompt  

<!-- note -->
This is how you make AI remember.

Pass `new_messages()` from one run into the next.

The system prompt is preserved automatically — no need to re-specify it.
<!-- end note -->

---

## Storing & Loading Message History

Save conversations to disk using `ModelMessagesTypeAdapter`.

```python
from pydantic_core import to_jsonable_python
from pydantic_ai.messages import ModelMessagesTypeAdapter

# Save
history = result.all_messages()
jsonable = to_jsonable_python(history)
with open("save.json", "w") as f:
    json.dump(jsonable, f)

# Load
with open("save.json", "r") as f:
    loaded = json.load(f)
restored = ModelMessagesTypeAdapter.validate_python(loaded)
```

<!-- note -->
Now you can **save and resume** games.

Use this with:

- File storage
- Redis
- PostgreSQL

This is how real AI apps persist memory.
<!-- end note -->

---

## Processing Message History

Trim, filter, or summarize history to save tokens.

```python
async def keep_recent(messages):
    return messages[-5:]

agent = Agent(
    'openai:gpt-4o',
    history_processors=[keep_recent]
)
```

Other ideas:

- 🔍 Filter out sensitive content
- 📝 Summarize old messages with a cheap LLM
- ⚖️ Context-aware trimming (`RunContext`)

<!-- note -->
Long conversations = expensive.

`history_processors` let you **modify the history before each call**.

This is **AI memory management** — crucial for production.
<!-- end note -->

---

## Multiple Agents: Role-Based AI Design

Use multiple agents for different roles.

```python
gm = Agent('gpt-4o', system_prompt='You are the narrator...')
guard = Agent('gpt-4o-mini', system_prompt='You are a gruff guard...')

if "talk to guard" in action:
    response = await guard.run(message_history=guard_hist)
```

**Benefits:**

- Specialized behavior
- Cost control
- Independent memory

<!-- note -->
Just like in movies, every character has their own voice.

Multiple agents let you simulate a **living world**.
<!-- end note -->

---

## Structured Output with `ToolOutput`

Force the LLM to return structured data.

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from pydantic_ai.output import ToolOutput

class NarrativeResponse(BaseModel):
    """Structured response for narrative text."""
    type: str = "narrative"
    text: str
    scene_id: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    format: str = "markdown"
    is_new_scene: bool = False

# Create ToolOutput instance for use with Pydantic AI agents
narrative_output = ToolOutput(NarrativeResponse)

# Use in an agent
SceneDescriber.agent = Agent(
    model=model,
    system_prompt=self._get_system_prompt(),
    output_type=narrative_output  # Use ToolOutput for structured responses
)
```

<!-- note -->
No more parsing JSON strings.

`ToolOutput` ensures the LLM returns valid Pydantic models.

Perfect for generating scenarios, quests, or validation.
<!-- end note -->

---

## Structured Output with `StructuredDict`

Generate valid JSON without defining a Pydantic model.

```python
from pydantic_ai import Agent, StructuredDict
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.ollama import OllamaProvider

# Define a schema for scenario generation
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
        }
    },
    "required": ["title", "description", "setting", "scenes"]
}
```

---

```python
# Create StructuredDict instance
scenario_generator = StructuredDict(scenario_schema)

# Use in an agent
self.agent = Agent(
    model=model,
    system_prompt=self._get_system_prompt(),
    output_type=scenario_generator  # Use StructuredDict for schema validation
)

# Get structured output
result = await self.agent.run(prompt)
scenario_data = result.output  # → dict, guaranteed to match schema
```

<!-- note -->
Use `StructuredDict` when you want schema enforcement without a full model.

Great for dynamic content like scenario generation.
<!-- end note -->

---

## Real-Time Interaction with WebSockets

Use FastAPI + Starlette for real-time events.

```python
from fastapi import WebSocket

@app.websocket("/ws/chat")
async def chat(websocket: WebSocket):
    await websocket.accept()
    while True:
        user_msg = await websocket.receive_text()
        result = await agent.run(user_msg, message_history=...)
        await websocket.send_json({"text": result.output})
```

<!-- note -->
REST is request-response.

But for **interactive AI**, we need **real-time, bidirectional flow**.

That’s where **WebSockets** come in — powered by **Starlette**.
<!-- end note -->

---

## Structured Events Over WebSockets

Send rich events to the frontend.

```python
# Backend
await websocket.send_json({
    "type": "npc_speak",
    "name": "Guard",
    "text": "Halt! Who goes there?"
})

# Frontend (Textual)
if event["type"] == "npc_speak":
    log.add(f"[red][NPC: {event['name']}] \"{event['text']}\"[/red]")
```

<!-- note -->
Don’t just send text — send **structured events**.

Your frontend can render:

- Narration
- NPC dialogue
- Clues
- Quests
- Choices

This is how you build **immersive AI experiences**.
<!-- end note -->

---

## Input Validation with a Pre-Validator Agent

Block invalid actions before they reach the GM.

```python
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.output import ToolOutput

# Define a validation model
class ValidationResult(BaseModel):
    valid: bool
    reason: str
    genre_appropriate: bool = True
```

---

```python
# Create ToolOutput for validation
validation_output = ToolOutput(ValidationResult)

# Create validator agent
validator = Agent(
    model=OpenAIModel('llama3', provider=OllamaProvider()),
    system_prompt="You validate user inputs for a spy-themed game.",
    output_type=validation_output
)
```

---

# Use in request processing

```python
async def process_user_input(user_input: str, websocket: WebSocket):
    # Validate input first
    validation = await validator.run(f"Validate this input: {user_input}")
    
    # Check if input is valid
    if not validation.output.valid:
        await websocket.send_json({
            "type": "error",
            "text": validation.output.reason
        })
        return  # Skip further processing
        
    # Continue with game master agent
    result = await gm_agent.run(user_input, message_history=history)
```

<!-- note -->
Should a spy game allow “rub my magic lamp”?

Use a **validator agent** to enforce genre, logic, and safety.

Saves tokens and improves UX.
<!-- end note -->

---

## Summary: Building Stateful AI Apps

✅ Use `message_history` to preserve context across agent runs  
✅ Store/load with `ModelMessagesTypeAdapter` for persistent conversations  
✅ Trim history with `history_processors` like `summarize_old_messages`  
✅ Use multiple agents (`GameMasterAgent`, `NPCCatalog`) for specialized roles  
✅ Use `ToolOutput` with models like `NarrativeResponse` for type-safe structured output  
✅ Use `StructuredDict` with JSON schema for dynamic content like scenario generation  
✅ Use WebSockets for real-time narrative events and choices  
✅ Send structured events with proper typing (`narrative`, `npc_speak`)  
✅ Validate user input with pre-validator agents for better UX  

You now have the tools to build **rich, interactive AI experiences** with proper state management.

<!-- note -->
Today wasn’t about games — it was about **state** and **narrative flow**.

You've learned how to:

- Give AI memory through message history
- Scale across roles with specialized agents
- Create rich narrative experiences with structured output
- Enhance storytelling with context-aware scene descriptions
- Generate immersive narrative transitions between scenes
- Use previous outcomes as context for coherent storytelling
- Stream responses for real-time interaction
- Persist conversations for long-term engagement

These are the skills you need to build AI assistants, chatbots, agents, and immersive experiences — in production.
<!-- end note -->

---

## Q&A + Resources

**Questions?**

**Resources:**

- 📘 [Pydantic AI Docs: Message History](https://ai.pydantic.dev/message-history/)
- 💡 [Pydantic AI: Structured Output](https://ai.pydantic.dev/api/output/)
- 📚 FastAPI WebSockets: [fastapi.tiangolo.com/advanced/websockets](https://fastapi.tiangolo.com/advanced/websockets/)
- 🎮 Full example: Improving Spy Engine in `src/engine/`
- 📝 Example models: `src/engine/structured_output.py`
- 🔄 Scenario generator: `src/engine/scenario_generator_agent.py`
- 🖋️ Scene describer: `src/engine/scene_describer.py`

<!-- note -->
Now open the floor for questions.

Encourage students to try:

- Saving a conversation and resuming it
- Generating a scenario with `StructuredDict`
- Adding a validator agent
- Streaming AI output

Remind them: the goal is not the game — it’s understanding how to build **AI systems that remember, interact, and scale**.
<!-- end note -->
