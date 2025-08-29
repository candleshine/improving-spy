from sqlalchemy import Column, String, Text, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

# SQLAlchemy ORM Base
Base = declarative_base()
__all__ = ['Spy', 'SpyBase', 'SpyCreate', 'SpyModel', 'Conversation', 'SpyProfile', 'ToolCall', 'ToolCallResponse', 'ChatRequest', 'ChatResponse']

# Database Model: Spy (SQLAlchemy)
class SpyModel(Base):
    __tablename__ = "spies"
    __table_args__ = (
        UniqueConstraint('codename', name='uq_spies_codename'),
    )

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    codename = Column(String, nullable=False, unique=True)
    biography = Column(Text, nullable=False)
    specialty = Column(String, nullable=False)

# Database Model: Conversation
class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True)
    spy_id = Column(String, nullable=False)
    messages = Column(Text, nullable=False)  # JSON-serialized message history
    mission_id = Column(String, nullable=True)

# Pydantic Models (for API)
class SpyBase(BaseModel):
    """Base Pydantic model for Spy with common fields"""
    name: str
    codename: str
    biography: str
    specialty: str

class SpyCreate(SpyBase):
    """Pydantic model for creating a new spy"""
    pass

class Spy(SpyBase):
    """Pydantic model for Spy responses"""
    id: str

    class Config:
        from_attributes = True

class SpyProfile(BaseModel):
    id: str
    name: str
    codename: str
    biography: str
    specialty: str

# Tool-related Models
class ToolCall(BaseModel):
    """A tool call requested by the model."""
    id: str = Field(..., description="Unique identifier for the tool call")
    name: str = Field(..., description="Name of the tool to call")
    arguments: Dict[str, Any] = Field(..., description="Arguments for the tool call")

class ToolCallResponse(BaseModel):
    """Response from a tool call."""
    tool_call_id: str = Field(..., description="ID of the tool call being responded to")
    name: str = Field(..., description="Name of the tool that was called")
    content: Dict[str, Any] = Field(..., description="Result of the tool call")

# Request/Response Models
class ChatRequest(BaseModel):
    """Request model for chat endpoints."""
    message: str = Field(..., description="The user's message")
    tool_calls: Optional[List[ToolCall]] = Field(
        None, 
        description="Tool calls to process before generating a response"
    )
    tool_outputs: Optional[List[ToolCallResponse]] = Field(
        None,
        description="Outputs from previous tool calls"
    )

class ChatResponse(BaseModel):
    """Response model for chat endpoints."""
    spy_id: str = Field(..., description="ID of the spy being talked to")
    spy_name: str = Field(..., description="Name of the spy being talked to")
    message: str = Field(..., description="The user's message")
    response: str = Field(..., description="The spy's response")
    tool_calls: Optional[List[ToolCall]] = Field(
        None,
        description="Tool calls requested by the model"
    )
    mission_id: Optional[str] = Field(
        None,
        description="[Deprecated] Mission ID for debriefing"
    )
    conversation_id: Optional[str] = Field(
        None,
        description="ID of the conversation, if applicable"
    )