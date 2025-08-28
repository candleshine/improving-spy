# 🕵️ Week 3: Teaching Guide - Building Intelligent Agents with PydanticAI

## 📚 Lesson Overview
**Duration:** 90 minutes  
**Objective:** Equip students with the skills to build intelligent agents using PydanticAI, focusing on practical implementation and best practices.

## 🎯 Learning Objectives
By the end of this lesson, students should be able to:
1. Explain the core components of agentic AI systems
2. Implement basic chat interactions using PydanticAI
3. Create and manage tools for LLM function calling
4. Handle conversation state and context effectively
5. Design production-ready chat agents

## 📖 Key Terms & Definitions

### Core Concepts
- **Agentic AI System**: An AI system that can take autonomous actions to achieve goals, often using tools and maintaining context.
- **LLM (Large Language Model)**: The core AI model that processes and generates human-like text based on input.
- **Prompt Engineering**: The practice of designing inputs to guide LLM behavior and outputs.
- **Context Window**: The amount of conversation history (tokens) an LLM can consider when generating responses.

### PydanticAI Specific
- **ModelMessage**: A structured way to represent messages in a conversation with role-based formatting.
- **Tool Calling**: The mechanism that allows LLMs to interact with external functions or APIs.
- **Conversation Management**: The process of maintaining and manipulating conversation state and history.

## 🚀 Lesson Flow

### 1. Introduction (15 min)
**Key Points to Cover:**
- What makes an AI system "agentic"?
- Real-world use cases of agentic AI
- Overview of PydanticAI's role in building these systems

**Teaching Tips:**
- Start with a live demo of a simple chat agent
- Highlight the difference between standard chatbots and agentic systems
- Use the spy theme to make it engaging

### 2. PydanticAI Fundamentals (20 min)
**Key Concepts:**
- Basic chat interactions
- System prompts and their importance
- Message formatting best practices

**Code Example:**
```python
from pydantic_ai import Agent

# Initialize the agent
agent = Agent('ollama:llama3.1', system_prompt="You are a helpful assistant.")

# Basic chat interaction
response = await agent.chat("Hello!")
print(response.content)
```

**Teaching Tips:**
- Demonstrate how system prompts influence behavior
- Show examples of good vs. bad prompts
- Have students experiment with different prompts

### 3. Tool Calling (25 min)
**Key Concepts:**
- Defining tools with Pydantic models
- Registering tools with the agent
- Handling tool responses

**Code Example:**
```python
from pydantic import BaseModel, Field

class WeatherQuery(BaseModel):
    """Get the current weather for a location."""
    location: str = Field(..., description="The city and state, e.g., San Francisco, CA")
    unit: str = Field("celsius", description="Temperature unit (celsius/fahrenheit)")

# Register the tool
agent.tools = [{"function": get_weather, "schema": WeatherQuery}]
```

**Teaching Tips:**
- Emphasize type safety with Pydantic
- Show how tools extend agent capabilities
- Demonstrate error handling in tool calls

### 4. Conversation Management (20 min)
**Key Concepts:**
- Maintaining message history
- Managing context windows
- Persisting conversations

**Code Example:**
```python
# Managing conversation history
conversation = [
    ModelMessage(role="system", content="You are a helpful assistant."),
    ModelMessage(role="user", content="What's the weather like?")
]

# Add new message
conversation.append(ModelMessage(role="user", content="In New York"))

# Get response with full context
response = await agent.chat(conversation)
```

**Teaching Tips:**
- Show how context affects responses
- Demonstrate context window limitations
- Discuss strategies for long conversations

### 5. Building the Chat Agent (10 min)
**Key Points:**
- Endpoint design considerations
- Error handling strategies
- Testing and deployment best practices

**Teaching Tips:**
- Walk through the complete flow
- Highlight common pitfalls
- Share debugging techniques

## 🎓 Assessment Activities

### In-Class Exercise (15 min)
**Activity:** Build a simple weather agent
1. Create a tool to get weather data
2. Set up a basic chat interface
3. Test different conversation flows

**Success Criteria:**
- Agent can understand and respond to weather queries
- Proper error handling is in place
- Conversation flows naturally

### Discussion Questions
1. How does tool calling enhance agent capabilities?
2. What are the limitations of current context windows?
3. How would you handle sensitive information in conversations?

## 📚 Additional Resources
- [PydanticAI Documentation](https://pydantic-ai.github.io/)
- [LLM Best Practices Guide](https://platform.openai.com/docs/guides/gpt-best-practices)
- [Conversational AI Patterns](https://martinfowler.com/articles/patterns-of-distributed-systems/conversational-patterns.html)

## 🏁 Wrap-up (5 min)
- Recap key learnings
- Preview next week's topic
- Q&A session

## 📝 Homework Assignment
Build a simple agent that can:
1. Answer questions about a specific topic
2. Use at least two custom tools
3. Maintain conversation context

**Due:** Next class session
**Submission:** GitHub repository link or code file

## 📋 Instructor Notes
- Be prepared to explain Pydantic concepts in simple terms
- Have fallback examples ready in case of API issues
- Encourage students to experiment with different system prompts
- Monitor student progress during exercises to provide timely assistance
