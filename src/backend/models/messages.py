"""Pydantic models for agent message handling.

This module defines the message models used for communication with the language model.
"""
from enum import Enum
from typing import List, Optional, Dict, Any, Union, Literal
from pydantic import BaseModel, Field, ConfigDict


class MessageRole(str, Enum):
    """Roles that a message can have in the conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class TextContent(BaseModel):
    """Plain text content for a message part."""
    text: str = Field(..., description="The text content")
    type: Literal["text"] = Field("text", description="The type of content")


class ToolCall(BaseModel):
    """A tool call made by the assistant."""
    id: str = Field(..., description="The ID of the tool call")
    type: Literal["function"] = Field("function", description="The type of the tool call")
    function: Dict[str, Any] = Field(..., description="The function details")




class MessagePart(BaseModel):
    """Base class for message parts."""
    pass


class SystemMessage(MessagePart):
    """A system message that sets the assistant's behavior."""
    content: str = Field(..., description="The content of the system message")
    role: Literal[MessageRole.SYSTEM] = Field(MessageRole.SYSTEM, description="The role of the message")


class UserMessage(MessagePart):
    """A message from the user."""
    content: Union[str, List[Union[str, Dict[str, Any]]]] = Field(
        ...,
        description="The content of the user message"
    )
    role: Literal[MessageRole.USER] = Field(MessageRole.USER, description="The role of the message")


class AssistantMessage(MessagePart):
    """A message from the assistant."""
    content: Optional[Union[str, List[Union[str, Dict[str, Any]]]]] = Field(
        None,
        description="The content of the assistant's message"
    )
    role: Literal[MessageRole.ASSISTANT] = Field(MessageRole.ASSISTANT, description="The role of the message")
    tool_calls: Optional[List[ToolCall]] = Field(
        None,
        description="The tool calls made by the assistant"
    )


class ToolMessage(MessagePart):
    """A message containing the result of a tool call."""
    content: str = Field(..., description="The content of the tool message")
    role: Literal[MessageRole.TOOL] = Field(MessageRole.TOOL, description="The role of the message")
    tool_call_id: str = Field(..., description="The ID of the tool call this message is for")


# Union type for all possible message types
Message = Union[SystemMessage, UserMessage, AssistantMessage, ToolMessage]


class LLMResponse(BaseModel):
    """Base response model for LLM outputs."""
    content: str = Field(..., description="The main content of the response")
    model_config = ConfigDict(extra='forbid')


class ToolCallRequest(BaseModel):
    """Model for tool call requests from the LLM."""
    id: str = Field(..., description="Unique identifier for the tool call")
    name: str = Field(..., description="Name of the tool to call")
    arguments: Dict[str, Any] = Field(..., description="Arguments for the tool call")


class LLMResponseWithTools(LLMResponse):
    """LLM response that may include tool calls."""
    tool_calls: List[ToolCallRequest] = Field(
        default_factory=list,
        description="List of tool calls requested by the LLM"
    )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LLMResponseWithTools':
        """Create a response from a dictionary."""
        content = data.get('content', '')
        if not content and 'output' in data:
            content = data['output']
        
        tool_calls = []
        for call in data.get('tool_calls', []):
            tool_calls.append(ToolCallRequest(
                id=call.get('id', ''),
                name=call.get('name', ''),
                arguments=call.get('arguments', {})
            ))
            
        return cls(content=str(content), tool_calls=tool_calls)


class ToolCallResult(BaseModel):
    """Result of a tool call."""
    tool_call_id: str = Field(..., description="ID of the tool call")
    output: Any = Field(..., description="Output from the tool call")


class LLMResponseWithToolResults(LLMResponse):
    """LLM response that includes results from tool calls."""
    tool_results: List[ToolCallResult] = Field(
        default_factory=list,
        description="Results from tool calls"
    )
