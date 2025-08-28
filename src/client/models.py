from pydantic import BaseModel
from typing import Optional, List, Union, Dict, Any


class ChatRequest(BaseModel):
    """Request model for chat endpoints"""
    message: str


class ChatResponse(BaseModel):
    """Response model for chat endpoints"""
    spy_id: str
    spy_name: str
    message: str
    response: str
    mission_id: Optional[str] = None
    conversation_id: Optional[str] = None


class SpyProfile(BaseModel):
    """Model for spy profile data"""
    id: str
    name: str
    codename: str
    biography: str
    specialty: str


class WebSocketMessage(BaseModel):
    """Base model for WebSocket messages"""
    type: str


class WebSocketResponse(WebSocketMessage):
    """Response message from WebSocket"""
    type: str = "response"
    spy_id: str
    spy_name: str
    message: str
    response: str


class WebSocketSystemMessage(WebSocketMessage):
    """System message from WebSocket"""
    type: str = "system"
    content: str


class WebSocketErrorMessage(WebSocketMessage):
    """Error message from WebSocket"""
    type: str = "error"
    content: str


class WebSocketTypingMessage(WebSocketMessage):
    """Typing indicator message from WebSocket"""
    type: str = "typing"
    spy_id: str


class ConversationCreate(BaseModel):
    """Model for creating a new conversation"""
    spy_id: str
