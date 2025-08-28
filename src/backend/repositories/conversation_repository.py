"""Repository for managing conversation data and message history.

This module provides both asynchronous and synchronous interfaces for interacting
with conversation data in the database, including CRUD operations and message history management.
"""

from __future__ import annotations
import json
import logging
import uuid
from typing import List, Optional, TypeVar, Union

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select, Result
from pydantic_ai.messages import ModelRequest, ModelResponse, ModelMessagesTypeAdapter
from fastcrud import FastCRUD

from ..models import Conversation

# Set up logging
logger = logging.getLogger(__name__)

_T = TypeVar('_T', bound='ConversationRepository')

class ConversationRepository:
    """Repository for managing conversation data and message history.
    
    Provides both asynchronous and synchronous interfaces for interacting with
    conversation data in the database.
    
    Attributes:
        crud: FastCRUD instance for basic CRUD operations on Conversation model
    """
    
    def __init__(self: _T) -> None:
        """Initialize a new ConversationRepository instance.
        
        Creates a FastCRUD instance for the Conversation model.
        """
        self.crud: FastCRUD = FastCRUD(model=Conversation)
    
    # Standard CRUD operations via FastCRUD
    async def get(self, session: AsyncSession, conversation_id: str) -> Optional[Conversation]:
        return await self.crud.get(session, id=conversation_id)
        
    async def create(self, session: AsyncSession, spy_id: str) -> str:
        conversation_id = str(uuid.uuid4())
        conversation_data = {
            "id": conversation_id,
            "spy_id": spy_id,
            "messages": "[]"
        }
        await self.crud.create(session, conversation_data)
        return conversation_id
    
    async def list(
        self, 
        session: AsyncSession, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Conversation]:
        """List all conversations with pagination asynchronously."""
        return await self.crud.get_multi(session, skip=skip, limit=limit)
        
    async def delete(self, session: AsyncSession, conversation_id: str) -> Optional[Conversation]:
        """Delete a conversation asynchronously."""
        return await self.crud.delete(session, id=conversation_id)
    
    # Custom operations
    async def store_messages(
        self, 
        session: AsyncSession, 
        conversation_id: str, 
        messages: List[Union[ModelRequest, ModelResponse]]
    ) -> None:
        conversation = await self.get(session, conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        messages_json = ModelMessagesTypeAdapter.dump_json(messages)
        update_data = {"messages": messages_json}
        await self.crud.update(session, id=conversation_id, obj_in=update_data)
    
    async def get_message_history(
        self, 
        session: AsyncSession, 
        conversation_id: str
    ) -> List[Union[ModelRequest, ModelResponse]]:
        conversation = await self.get(session, conversation_id)
        if not conversation or not conversation.messages:
            return []
        
        try:
            import json
            messages_data = json.loads(conversation.messages)
            
            # If it's already a list of ModelMessage objects
            if isinstance(messages_data, list) and all(
                isinstance(msg, dict) and 'role' in msg and 'content' in msg 
                for msg in messages_data
            ):
                model_messages = []
                for msg in messages_data:
                    role = str(msg['role']).lower()
                    content = msg['content']
                    # Create the appropriate message type based on role
                    if role == 'user':
                        model_messages.append(ModelRequest(parts=[content]))
                    else:
                        model_messages.append(ModelResponse(parts=[content]))
                return model_messages
            
            # If it's a single message
            if isinstance(messages_data, dict) and 'role' in messages_data and 'content' in messages_data:
                role = str(messages_data['role']).lower()
                content = messages_data['content']
                if role == 'user':
                    return [ModelRequest(parts=[content])]
                else:
                    return [ModelResponse(parts=[content])]
                
            # Try to validate as a serialized ModelMessage list as a last resort
            try:
                return ModelMessagesTypeAdapter.validate_json(conversation.messages)
            except Exception:
                pass
                
            # If we get here, the format is unexpected
            raise ValueError(f"Unexpected message format: {conversation.messages[:100]}...")
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in message history: {e}")
        except Exception as e:
            raise ValueError(f"Failed to deserialize message history: {e}")
    
    async def get_by_spy_id(
        self, 
        session: AsyncSession, 
        spy_id: str
    ) -> List[Conversation]:
        query = select(Conversation).where(Conversation.spy_id == spy_id)
        result: Result = await session.execute(query)
        return list(result.scalars().all())
    
    # Synchronous versions for compatibility with existing code
    
    def get_sync(self, session: Session, conversation_id: str) -> Optional[Conversation]:
        return session.query(Conversation).filter(Conversation.id == conversation_id).first()
    
    def create_sync(self, session: Session, spy_id: str) -> str:
        conversation_id = str(uuid.uuid4())
        conversation = Conversation(
            id=conversation_id,
            spy_id=spy_id,
            messages="[]"
        )
        session.add(conversation)
        session.commit()
        return conversation_id
    
    def list_sync(
        self, 
        session: Session, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Conversation]:
        return session.query(Conversation).offset(skip).limit(limit).all()
    
    def delete_sync(self, session: Session, conversation_id: str) -> bool:
        conversation = self.get_sync(session, conversation_id)
        if not conversation:
            return False
        
        session.delete(conversation)
        session.commit()
        return True
    
    def store_messages_sync(
        self, 
        session: Session, 
        conversation_id: str, 
        messages: List[Union[ModelRequest, ModelResponse]]
    ) -> None:
        conversation = self.get_sync(session, conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        messages_json = ModelMessagesTypeAdapter.dump_json(messages)
        conversation.messages = messages_json
        session.commit()
    
    def get_message_history_sync(
        self, 
        session: Session, 
        conversation_id: str
    ) -> List[Union[ModelRequest, ModelResponse]]:
        conversation = self.get_sync(session, conversation_id)
        if not conversation or not conversation.messages:
            return []
            
        try:
            # First try to use the ModelMessagesTypeAdapter
            try:
                return ModelMessagesTypeAdapter.validate_json(conversation.messages)
            except Exception:
                pass
                
            # If that fails, try to parse as JSON directly
            try:
                messages_data = json.loads(conversation.messages)
            except (json.JSONDecodeError, TypeError):
                # If direct JSON parsing fails, try to handle as bytes or string
                if isinstance(conversation.messages, bytes):
                    messages_data = json.loads(conversation.messages.decode('utf-8'))
                else:
                    try:
                        messages_data = json.loads(str(conversation.messages))
                    except json.JSONDecodeError:
                        # If it's still not valid JSON, try to extract JSON-like content
                        import re
                        json_match = re.search(r'\[\s*\{.*\}\s*\]', str(conversation.messages), re.DOTALL)
                        if json_match:
                            messages_data = json.loads(json_match.group(0))
                        else:
                            raise
            
            # If it's a list of messages
            if isinstance(messages_data, list):
                model_messages = []
                for msg in messages_data:
                    if isinstance(msg, str):
                        # Handle case where message is a simple string
                        model_messages.append(ModelResponse(parts=[msg]))
                        continue
                        
                    if not isinstance(msg, dict):
                        continue
                        
                    # Handle different message formats
                    if 'parts' in msg:
                        # New format with 'parts' array
                        parts = msg.get('parts', [])
                        if not parts:
                            continue
                            
                        if msg.get('kind') == 'request' or msg.get('role') == 'user':
                            model_messages.append(ModelRequest(parts=parts))
                        else:
                            model_messages.append(ModelResponse(parts=parts))
                    elif 'role' in msg and 'content' in msg:
                        # Old format with 'role' and 'content'
                        role = str(msg['role']).lower()
                        content = msg['content']
                        if role == 'user':
                            model_messages.append(ModelRequest(parts=[content]))
                        else:
                            model_messages.append(ModelResponse(parts=[content]))
                
                if model_messages:
                    return model_messages
            
            # If it's a single message
            if isinstance(messages_data, dict):
                if 'parts' in messages_data:
                    parts = messages_data.get('parts', [])
                    if messages_data.get('kind') == 'request' or messages_data.get('role') == 'user':
                        return [ModelRequest(parts=parts)]
                    return [ModelResponse(parts=parts)]
                elif 'role' in messages_data and 'content' in messages_data:
                    role = str(messages_data['role']).lower()
                    content = messages_data['content']
                    if role == 'user':
                        return [ModelRequest(parts=[content])]
                    return [ModelResponse(parts=[content])]
            
            # If we get here, try to handle as a simple string
            if isinstance(conversation.messages, (str, bytes)):
                try:
                    msg_str = conversation.messages.decode('utf-8') if isinstance(conversation.messages, bytes) else str(conversation.messages)
                    return [ModelResponse(parts=[msg_str])]
                except Exception:
                    pass
                
            # If we still can't parse it, return an empty list to avoid breaking the conversation
            logger.warning(f"Could not parse message history: {str(conversation.messages)[:200]}...")
            return []
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in message history: {e}")
            return []
        except Exception as e:
            logger.error(f"Error deserializing message history: {e}", exc_info=True)
            return []

    async def get_or_create_by_spy_id(
        self,
        session: AsyncSession,
        spy_id: str
    ) -> Conversation:
        """
        Get an existing conversation for the spy or create a new one if it doesn't exist.
        
        Args:
            session: The database session
            spy_id: The ID of the spy
            
        Returns:
            The existing or newly created conversation
            
        Raises:
            ValueError: If there's an error creating or retrieving the conversation
        """
        try:
            # Try to get an existing conversation
            existing = await self.get_by_spy_id(session, spy_id)
            if existing:
                # Return the most recent conversation
                return existing[0]
                
            # If no conversation exists, create a new one
            conversation_id = await self.create(session, spy_id)
            conversation = await self.get(session, conversation_id)
            if not conversation:
                raise ValueError("Failed to create new conversation")
            return conversation
            
        except Exception as e:
            logger.error(f"Error in get_or_create_by_spy_id: {str(e)}")
            raise ValueError(f"Failed to get or create conversation: {str(e)}")