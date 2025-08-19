from fastcrud import FastCRUD
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..models import Conversation
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter
import uuid
from typing import Optional, List, Dict, Any, Union

class ConversationRepository:
    def __init__(self):
        self.crud = FastCRUD(model=Conversation)
    
    # Standard CRUD operations via FastCRUD
    async def get(self, session: AsyncSession, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation by ID asynchronously."""
        return await self.crud.get(session, id=conversation_id)
        
    async def create(self, session: AsyncSession, spy_id: str) -> str:
        """Create a new conversation asynchronously and return its ID."""
        conversation_id = str(uuid.uuid4())
        conversation_data = {
            "id": conversation_id,
            "spy_id": spy_id,
            "messages": "[]"
        }
        await self.crud.create(session, conversation_data)
        return conversation_id
    
    async def list(self, session: AsyncSession, skip: int = 0, limit: int = 100) -> List[Conversation]:
        """List all conversations with pagination asynchronously."""
        return await self.crud.get_multi(session, skip=skip, limit=limit)
    
    async def delete(self, session: AsyncSession, conversation_id: str) -> Optional[Conversation]:
        """Delete a conversation asynchronously."""
        return await self.crud.delete(session, id=conversation_id)
    
    # Custom operations
    async def store_messages(self, session: AsyncSession, conversation_id: str, messages: List[ModelMessage]):
        """Store updated message history asynchronously."""
        conversation = await self.get(session, conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        messages_json = ModelMessagesTypeAdapter.dump_json(messages)
        update_data = {"messages": messages_json}
        await self.crud.update(session, id=conversation_id, obj_in=update_data)
    
    async def get_message_history(self, session: AsyncSession, conversation_id: str) -> List[ModelMessage]:
        """Retrieve message history for a conversation asynchronously."""
        conversation = await self.get(session, conversation_id)
        if not conversation or not conversation.messages:
            return []
        
        try:
            return ModelMessagesTypeAdapter.validate_json(conversation.messages)
        except Exception as e:
            raise ValueError(f"Failed to deserialize message history: {e}")
    
    async def get_by_spy_id(self, session: AsyncSession, spy_id: str) -> List[Conversation]:
        """Get all conversations for a spy asynchronously."""
        query = select(Conversation).where(Conversation.spy_id == spy_id)
        result = await session.execute(query)
        return list(result.scalars().all())
    
    # Sync versions for compatibility with existing code
    def get_sync(self, session: Session, conversation_id: str) -> Optional[Conversation]:
        """Get a conversation by ID (synchronous version)."""
        return session.query(Conversation).filter(Conversation.id == conversation_id).first()
    
    def create_sync(self, session: Session, spy_id: str) -> str:
        """Create a new conversation and return its ID (synchronous version)."""
        conversation_id = str(uuid.uuid4())
        conversation = Conversation(
            id=conversation_id,
            spy_id=spy_id,
            messages="[]"
        )
        session.add(conversation)
        session.commit()
        return conversation_id
    
    def list_sync(self, session: Session, skip: int = 0, limit: int = 100) -> List[Conversation]:
        """List all conversations with pagination (synchronous version)."""
        return session.query(Conversation).offset(skip).limit(limit).all()
    
    def delete_sync(self, session: Session, conversation_id: str) -> bool:
        """Delete a conversation (synchronous version)."""
        conversation = self.get_sync(session, conversation_id)
        if not conversation:
            return False
        
        session.delete(conversation)
        session.commit()
        return True
    
    def store_messages_sync(self, session: Session, conversation_id: str, messages: List[ModelMessage]):
        """Store updated message history (synchronous version)."""
        conversation = self.get_sync(session, conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        messages_json = ModelMessagesTypeAdapter.dump_json(messages)
        conversation.messages = messages_json
        session.commit()
    
    def get_message_history_sync(self, session: Session, conversation_id: str) -> List[ModelMessage]:
        """Retrieve message history for a conversation (synchronous version)."""
        conversation = self.get_sync(session, conversation_id)
        if not conversation or not conversation.messages:
            return []
        
        try:
            return ModelMessagesTypeAdapter.validate_json(conversation.messages)
        except Exception as e:
            raise ValueError(f"Failed to deserialize message history: {e}")
    
    def get_by_spy_id_sync(self, session: Session, spy_id: str) -> List[Conversation]:
        """Get all conversations for a spy (synchronous version)."""
        return session.query(Conversation).filter(Conversation.spy_id == spy_id).all()
