"""Repository for managing conversation data and message history.

This module provides an interface for interacting with conversation data in the database,
including CRUD operations and message history management.
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import select

from ..models import Conversation

# Set up logging
logger = logging.getLogger(__name__)

class ConversationRepository:
    """Repository for managing conversation data and message history."""
    
    def __init__(self, db: Session):
        """Initialize the repository with a database session."""
        self.db = db
        
    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get a conversation by ID."""
        conversation = self.db.get(Conversation, conversation_id)
        if conversation:
            return {
                "id": conversation.id,
                "spy_id": conversation.spy_id,
                "title": conversation.title,
                "created_at": conversation.created_at,
                "updated_at": conversation.updated_at,
                "messages": json.loads(conversation.messages) if conversation.messages else []
            }
        return None
        
    def get_conversations_by_spy(self, spy_id: str) -> List[Dict[str, Any]]:
        """Get all conversations for a specific spy."""
        result = self.db.execute(
            select(Conversation)
            .where(Conversation.spy_id == spy_id)
        )
        conversations = result.scalars().all()
        
        return [{
            "id": conv.id,
            "spy_id": conv.spy_id,
            "message_count": len(json.loads(conv.messages)) if conv.messages else 0
        } for conv in conversations]
    
    def create_conversation(self, spy_id: str) -> Dict[str, Any]:
        """Create a new conversation."""
        conversation = Conversation(
            id=str(uuid.uuid4()),
            spy_id=spy_id,
            messages=json.dumps([])
        )
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return {
            "id": conversation.id,
            "spy_id": conversation.spy_id,
            "messages": []
        }
        
    def update_conversation(self, conversation_id: str, **updates) -> Optional[Dict[str, Any]]:
        """Update a conversation's fields."""
        conversation = self.db.get(Conversation, conversation_id)
        if not conversation:
            return None
            
        for key, value in updates.items():
            if hasattr(conversation, key):
                setattr(conversation, key, value)
                
        self.db.commit()
        self.db.refresh(conversation)
        return self.get_conversation(conversation_id)
        
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation by ID."""
        conversation = self.db.get(Conversation, conversation_id)
        if not conversation:
            return False
            
        self.db.delete(conversation)
        self.db.commit()
        return True
        
    def add_message(self, conversation_id: str, role: str, content: str, **metadata) -> Optional[Dict[str, Any]]:
        """Add a message to a conversation."""
        conversation = self.db.get(Conversation, conversation_id)
        if not conversation:
            return None
            
        messages = json.loads(conversation.messages) if conversation.messages else []
        message = {
            "role": role,
            "content": content,
            "timestamp": str(datetime.utcnow()),
            **metadata
        }
        messages.append(message)
        
        conversation.messages = json.dumps(messages)
        self.db.commit()
        self.db.refresh(conversation)
        
        return message
        
    def get_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a conversation."""
        conversation = self.db.get(Conversation, conversation_id)
        if not conversation or not conversation.messages:
            return []
            
        return json.loads(conversation.messages)
    
    def list_conversations(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """List all conversations with pagination."""
        result = self.db.execute(
            select(Conversation)
            .order_by(Conversation.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        conversations = result.scalars().all()
        
        return [{
            "id": conv.id,
            "spy_id": conv.spy_id,
            "title": conv.title,
            "created_at": conv.created_at,
            "updated_at": conv.updated_at,
            "message_count": len(json.loads(conv.messages)) if conv.messages else 0
        } for conv in conversations]
    
    def store_messages(self, conversation_id: str, messages: List[Dict[str, Any]]) -> None:
        """Store messages for a conversation."""
        conversation = self.db.get(Conversation, conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        conversation.messages = json.dumps(messages)
        self.db.commit()
    
    def get_message_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get the message history for a conversation."""
        conversation = self.db.get(Conversation, conversation_id)
        if not conversation or not conversation.messages:
            return []
            
        try:
            # Try to parse as JSON directly first
            try:
                return json.loads(conversation.messages)
            except (json.JSONDecodeError, TypeError):
                # If direct JSON parsing fails, try to handle as bytes or string
                if isinstance(conversation.messages, bytes):
                    return json.loads(conversation.messages.decode('utf-8'))
                return json.loads(str(conversation.messages))
        except Exception as e:
            logger.error(f"Error parsing messages for conversation {conversation_id}: {e}")
            return []
    
    def get_or_create_conversation(self, db: Session, spy_id: str = None, codename: str = None) -> Dict[str, Any]:
        """
        Get an existing conversation for the spy or create a new one if it doesn't exist.
        
        Args:
            db: The database session
            spy_id: The ID of the spy (either spy_id or codename must be provided)
            codename: The codename of the spy (either spy_id or codename must be provided)
            
        Returns:
            The existing or newly created conversation
            
        Raises:
            ValueError: If there's an error creating or retrieving the conversation, or if neither spy_id nor codename is provided
        """
        if not spy_id and not codename:
            raise ValueError("Either spy_id or codename must be provided")
            
        try:
            # If only codename is provided, look up the spy_id
            if codename and not spy_id:
                from .spy_repository import SpyRepository
                spy_repo = SpyRepository(db)
                spy = spy_repo.get_by_codename(codename)
                if not spy:
                    raise ValueError(f"No spy found with codename: {codename}")
                spy_id = spy.id
            
            # Check if there's an existing conversation for this spy
            existing = self.db.query(Conversation).filter(
                Conversation.spy_id == spy_id
            ).first()
            
            if existing:
                return {
                    "id": existing.id,
                    "spy_id": existing.spy_id,
                    "messages": json.loads(existing.messages) if existing.messages else [],
                    "mission_id": getattr(existing, 'mission_id', None)
                }
            
            # Create a new conversation if none exists
            new_conversation = self.create_conversation(spy_id)
            db.commit()
            return new_conversation
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error getting or creating conversation for spy {spy_id or codename}: {e}")
            raise ValueError(f"Failed to get or create conversation: {str(e)}")
    
    # Keep the old method for backward compatibility
    def get_or_create_by_spy_id(self, db: Session, spy_id: str) -> Dict[str, Any]:
        """
        [Deprecated] Use get_or_create_conversation instead.
        Get an existing conversation for the spy by ID or create a new one if it doesn't exist.
        """
        return self.get_or_create_conversation(db, spy_id=spy_id)
