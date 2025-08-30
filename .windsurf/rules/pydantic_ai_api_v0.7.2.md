---
trigger: model_decision
description: Use this rule when working with Pydantic AI functionality, implementing AI agents, creating tools and functions, or integrating with Ollama backends. Essential for maintaining consistency in AI agent behavior, tool implementation, and Pydantic model usage within the AI context.
globs:
---
# Pydantic AI API Documentation v0.7.2

## Overview
Pydantic AI is a powerful library that enables you to create AI agents using Pydantic models. It provides a structured way to define AI tools, functions, and agents with automatic validation, serialization, and type safety.

**Version**: 0.7.2  
**Release Date**: Latest stable release  
**Documentation**: [https://ai.pydantic.dev/](https://ai.pydantic.dev/)

## Core Concepts

### AI Agents
AI agents are the main building blocks that can use tools, have conversations, and perform tasks. They are defined using Pydantic models and can be configured with various backends like OpenAI, Ollama, or other LLM providers.

### Tools
Tools are functions that agents can call to perform specific tasks. They are defined using Pydantic models and can accept parameters with automatic validation.

### Functions
Functions are similar to tools but are typically used for more complex operations or when you need to define custom behavior.

## API Reference

### Core Classes

#### `Agent`
The main class for creating AI agents.

```python
from pydantic_ai import Agent

class MyAgent(Agent):
    """A custom AI agent."""
    
    # Define tools and functions here
    tools = [my_tool]
    functions = [my_function]
    
    # Configure the agent
    model = "gpt-4"  # or "ollama/llama2" for Ollama
    system_prompt = "You are a helpful AI assistant."
```

**Key Methods**:
- `run()`: Execute the agent with a given input
- `run_sync()`: Execute the agent synchronously
- `run_stream()`: Stream the agent's execution
- `iter()`: Iterate through the agent's execution steps
- `add_tool()`: Add a tool to the agent
- `add_function()`: Add a function to the agent

#### `AgentRunResult`
The result of running an agent, returned by the `run()` method.

```python
from pydantic_ai import Agent

agent = Agent('test')
result = await agent.run('Hello!')

# Access the output
print(result.output)  # The main response content

# Access conversation history
messages = result.all_messages()
if callable(messages):
    messages = messages()  # all_messages is a method

# Check for tool calls in the messages
for msg in messages:
    if hasattr(msg, 'parts'):
        for part in msg.parts:
            if hasattr(part, 'part_kind') and 'tool-call' in str(part.part_kind).lower():
                # Extract tool call information
                tool_name = getattr(part, 'tool_name', '')
                tool_call_id = getattr(part, 'tool_call_id', '')
                args = part.args_as_dict() if callable(part.args_as_dict) else {}
```

**Key Attributes**:
- `output`: The main response content from the agent
- `all_messages()`: Method that returns the conversation history
- `new_messages()`: Method that returns only new messages from this run
- `usage`: Information about token usage and costs

#### `Tool`
Base class for creating tools that agents can use.

```python
from pydantic_ai import Tool

# CORRECT - Function as first argument
tool = Tool(
    my_function,  # Function as first positional argument
    name="my_tool",
    description="Performs a specific task"
)

# INCORRECT - Function as keyword argument
tool = Tool(
    name="my_tool",
    function=my_function,  # This won't work
    description="Performs a specific task"
)
```

**Key Attributes**:
- `name`: Unique identifier for the tool
- `description`: Human-readable description of what the tool does
- `input_schema`: Pydantic model defining input parameters
- `output_schema`: Pydantic model defining output structure

#### `Function`
Base class for creating functions that agents can call.

```python
from pydantic_ai import Function

class MyFunction(Function):
    """A custom function for the agent."""
    
    name: str = "my_function"
    description: str = "Performs a complex operation"
    
    def execute(self, **kwargs) -> dict:
        """Execute the function logic."""
        # Function implementation here
        return {"result": "success", "data": kwargs}
```

### Configuration

#### Backend Configuration
Pydantic AI supports multiple backend providers:

**OpenAI**:
```python
from pydantic_ai import Agent

agent = Agent(
    model="gpt-4",
    api_key="your-openai-api-key",
    base_url="https://api.openai.com/v1"  # Optional
)
```

**Ollama**:
```python
from pydantic_ai import Agent

agent = Agent(
    model="ollama/llama2",
    base_url="http://localhost:11434"  # Ollama default
)
```

**Custom Backend**:
```python
from pydantic_ai import Agent

agent = Agent(
    model="custom-model",
    base_url="https://your-custom-endpoint.com",
    headers={"Authorization": "Bearer your-token"}
)
```

### Tool and Function Definition

#### Simple Tool Example
```python
from pydantic_ai import Tool
from pydantic import BaseModel

class CalculatorInput(BaseModel):
    operation: str
    a: float
    b: float

class CalculatorTool(Tool):
    name: str = "calculator"
    description: str = "Performs basic arithmetic operations"
    input_schema: type[BaseModel] = CalculatorInput
    
    def run(self, input_data: CalculatorInput) -> float:
        if input_data.operation == "add":
            return input_data.a + input_data.b
        elif input_data.operation == "subtract":
            return input_data.a - input_data.b
        elif input_data.operation == "multiply":
            return input_data.a * input_data.b
        elif input_data.operation == "divide":
            if input_data.b == 0:
                raise ValueError("Cannot divide by zero")
            return input_data.a / input_data.b
        else:
            raise ValueError(f"Unknown operation: {input_data.operation}")
```

#### Function with Complex Logic
```python
from pydantic_ai import Function
from pydantic import BaseModel
from typing import List, Dict, Any

class DataProcessorInput(BaseModel):
    data: List[Dict[str, Any]]
    operation: str
    filters: Dict[str, Any] = {}

class DataProcessorFunction(Function):
    name: str = "data_processor"
    description: str = "Processes data with various operations and filters"
    input_schema: type[BaseModel] = DataProcessorInput
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        input_data = DataProcessorInput(**kwargs)
        
        # Apply filters
        filtered_data = input_data.data
        for key, value in input_data.filters.items():
            filtered_data = [
                item for item in filtered_data 
                if item.get(key) == value
            ]
        
        # Apply operation
        if input_data.operation == "count":
            result = len(filtered_data)
        elif input_data.operation == "sum":
            result = sum(item.get("value", 0) for item in filtered_data)
        elif input_data.operation == "average":
            values = [item.get("value", 0) for item in filtered_data]
            result = sum(values) / len(values) if values else 0
        else:
            raise ValueError(f"Unknown operation: {input_data.operation}")
        
        return {
            "operation": input_data.operation,
            "result": result,
            "processed_items": len(filtered_data)
        }
```

### Agent Usage Patterns

#### Basic Agent Setup
```python
from pydantic_ai import Agent
from .tools import CalculatorTool, DataProcessorFunction

# Create agent with tools and functions
agent = Agent(
    model="ollama/llama2",
    system_prompt="You are a helpful AI assistant that can perform calculations and data processing.",
    tools=[CalculatorTool()],
    functions=[DataProcessorFunction()]
)

# Run the agent
response = agent.run("Calculate 15 + 27 and then process some data")
print(response)
```

#### Run-based Interaction
```python
# Execute the agent with a single prompt
response = await agent.run("Hello! Can you help me with some calculations?")

# Execute with multiple messages
messages = [
    ModelMessage(role="user", content="Hello! Can you help me with some calculations?"),
    ModelMessage(role="user", content="What's 42 divided by 6?")
]
response = await agent.run(message_history=messages)

# Stream the execution
async for step in agent.run_stream("Process this data: [{'value': 10}, {'value': 20}, {'value': 30}] with operation 'sum'?"):
    print(f"Step: {step}")
```

#### Tool and Function Registration
```python
# Add tools and functions dynamically
new_tool = MyCustomTool()
agent.add_tool(new_tool)

new_function = MyCustomFunction()
agent.add_function(new_function)
```

### Advanced Features

#### Custom Input/Output Schemas
```python
from pydantic import BaseModel, Field
from typing import Optional, List

class AdvancedInput(BaseModel):
    text: str = Field(..., description="Input text to process")
    max_length: Optional[int] = Field(None, description="Maximum output length")
    include_metadata: bool = Field(False, description="Include processing metadata")

class AdvancedOutput(BaseModel):
    processed_text: str = Field(..., description="Processed output text")
    word_count: int = Field(..., description="Number of words in output")
    processing_time: float = Field(..., description="Time taken to process in seconds")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata")

class AdvancedTool(Tool):
    name: str = "advanced_processor"
    description: str = "Advanced text processing with configurable options"
    input_schema: type[BaseModel] = AdvancedInput
    output_schema: type[BaseModel] = AdvancedOutput
    
    def run(self, input_data: AdvancedInput) -> AdvancedOutput:
        import time
        start_time = time.time()
        
        # Process the text
        processed = input_data.text.upper()
        if input_data.max_length:
            processed = processed[:input_data.max_length]
        
        processing_time = time.time() - start_time
        
        # Build output
        output = AdvancedOutput(
            processed_text=processed,
            word_count=len(processed.split()),
            processing_time=processing_time
        )
        
        if input_data.include_metadata:
            output.metadata = {
                "original_length": len(input_data.text),
                "truncated": len(processed) < len(input_data.text)
            }
        
        return output
```

#### Error Handling
```python
from pydantic_ai import Tool
from pydantic import ValidationError

class RobustTool(Tool):
    name: str = "robust_processor"
    description: str = "A tool with comprehensive error handling"
    
    def run(self, input_data: str) -> str:
        try:
            # Tool logic here
            result = self._process_input(input_data)
            return result
        except ValidationError as e:
            return f"Validation error: {e.errors()}"
        except ValueError as e:
            return f"Value error: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
    
    def _process_input(self, data: str) -> str:
        # Actual processing logic
        if not data:
            raise ValueError("Input cannot be empty")
        return f"Processed: {data}"
```

### Best Practices

#### 1. Tool and Function Design
- Keep tools focused on single, well-defined tasks
- Use descriptive names and descriptions
- Implement proper input validation
- Handle errors gracefully
- Return structured, predictable outputs

#### 2. Agent Configuration
- Use appropriate system prompts for your use case
- Choose the right model for your requirements
- Implement proper error handling and retry logic
- Monitor usage and performance

#### 3. Input/Output Schemas
- Use Pydantic models for type safety
- Provide clear field descriptions
- Use appropriate field types and constraints
- Consider optional fields for flexibility

#### 4. Error Handling
- Implement comprehensive error handling in tools
- Provide meaningful error messages
- Use appropriate HTTP status codes
- Log errors for debugging

### Migration from Previous Versions

#### Breaking Changes in v0.7.2
- Updated Pydantic dependency requirements
- Improved error handling and validation
- Enhanced backend compatibility
- Better type hints and documentation

#### Upgrade Path
1. Update your dependencies to `pydantic-ai>=0.7.2`
2. Review any deprecated method usage
3. Test your existing tools and functions
4. Update any custom backend implementations

### Examples

#### Complete Agent Example
```python
from pydantic_ai import Agent, Tool
from pydantic import BaseModel, Field
from typing import List, Dict, Any

# Define input/output schemas
class SearchInput(BaseModel):
    query: str = Field(..., description="Search query")
    max_results: int = Field(5, description="Maximum number of results")

class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str
    relevance_score: float

class SearchOutput(BaseModel):
    results: List[SearchResult]
    total_found: int
    query_time: float

# Create a search tool
class WebSearchTool(Tool):
    name: str = "web_search"
    description: str = "Search the web for information"
    input_schema: type[BaseModel] = SearchInput
    output_schema: type[BaseModel] = SearchOutput
    
    def run(self, input_data: SearchInput) -> SearchOutput:
        import time
        start_time = time.time()
        
        # Simulate web search
        # In a real implementation, you'd call a search API
        mock_results = [
            SearchResult(
                title=f"Result {i} for '{input_data.query}'",
                url=f"https://example.com/result-{i}",
                snippet=f"This is a snippet for result {i}",
                relevance_score=0.9 - (i * 0.1)
            )
            for i in range(min(input_data.max_results, 3))
        ]
        
        query_time = time.time() - start_time
        
        return SearchOutput(
            results=mock_results,
            total_found=len(mock_results),
            query_time=query_time
        )

# Create and configure the agent
agent = Agent(
    model="ollama/llama2",
    system_prompt="You are a helpful AI assistant that can search the web for information.",
    tools=[WebSearchTool()]
)

# Use the agent
response = agent.run("Search for information about Python programming")
print(response)
```

## Conclusion

Pydantic AI v0.7.2 provides a robust and flexible framework for building AI agents with structured tools and functions. The library emphasizes type safety, validation, and ease of use while supporting multiple backend providers.

Key benefits of this version include:
- Improved Pydantic integration
- Better error handling and validation
- Enhanced backend compatibility
- Comprehensive tool and function support
- Flexible configuration options

For more information and examples, visit the official documentation at [https://ai.pydantic.dev/](https://ai.pydantic.dev/).
