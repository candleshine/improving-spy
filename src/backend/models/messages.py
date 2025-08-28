"""Pydantic models for agent message handling.

This module defines the message models used for communication with the language model.
"""
from pydantic import BaseModel
class ChatResponse(BaseModel):
    """Structured response from the chat agent."""
    response: str
