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
- PydanticAI: Simple Python interface for LLMs
- Context loading: Feed documents into your LLM's memory
- Message history: Store conversation context for better responses

---

## Install Dependencies

```bash
uv add pydantic-ai ollama
```

- Make sure Ollama is installed and at least one model pulled (e.g., llama2)

---

## Context Engineering

- Combine the spy's biography, mission data, and user message to create a prompt
- Example:

```text
You are [spy name]. [biography]
Mission Summary: [mission_details]
User: [message]
```

---

## Live Demo: Chat Function

```python
from pydantic_ai import OpenAI

def chat_with_agent(user_message, spy, mission_summary=None):
    if mission_summary:
        prompt = f"You are {spy.name}. {spy.biography}\nMission Summary: {mission_summary}\nUser: {user_message}"
    else:
        prompt = f"You are {spy.name}. {spy.biography}\nUser: {user_message}"
    ai = OpenAI(model='ollama/llama2')
    return ai(prompt)
```

- Test with different agent personalities and mission contexts!

---

## Mission Debrief Implementation

```python
def load_mission_summary(mission_id):
    # Load mission summary from text file or database
    with open(f"missions/{mission_id}.txt", "r") as f:
        return f.read()

def debrief_mission(spy_id, mission_id, user_message):
    spy = get_spy_by_id(spy_id)
    mission_summary = load_mission_summary(mission_id)
    return chat_with_agent(user_message, spy, mission_summary)
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
