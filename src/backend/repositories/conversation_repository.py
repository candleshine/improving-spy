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
        """Get a conversation by ID asynchronously.
        
        Args:
            session: The async database session to use for the query
            conversation_id: The unique identifier of the conversation to retrieve
            
        Returns:
            The Conversation object if found, None otherwise
            
        Example:
            >>> async with async_session() as session:
            ...     repo = ConversationRepository()
            ...     conversation = await repo.get(session, "some-conversation-id")
        """
        return await self.crud.get(session, id=conversation_id)
        
    async def create(self, session: AsyncSession, spy_id: str) -> str:
        """Create a new conversation asynchronously and return its ID.
        
        Args:
            session: The async database session to use for the operation
            spy_id: The ID of the spy this conversation belongs to
            
        Returns:
            The newly created conversation's ID
            
        Raises:
            sqlalchemy.exc.SQLAlchemyError: If there's an error creating the conversation
            
        Example:
            >>> async with async_session() as session:
            ...     repo = ConversationRepository()
            ...     conv_id = await repo.create(session, "spy-123")
        """
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
        """List all conversations with pagination asynchronously.
        
        Args:
            session: The async database session to use for the query
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return (for pagination)
            
        Returns:
            A list of Conversation objects
            
        Example:
            >>> async with async_session() as session:
            ...     repo = ConversationRepository()
            ...     conversations = await repo.list(session, skip=0, limit=10)
        """
        return await self.crud.get_multi(session, skip=skip, limit=limit)
    
    async def delete(self, session: AsyncSession, conversation_id: str) -> Optional[Conversation]:
        """Delete a conversation asynchronously.
        
        Args:
            session: The async database session to use for the operation
            conversation_id: The ID of the conversation to delete
            
        Returns:
            The deleted Conversation object if found, None otherwise
            
        Example:
            >>> async with async_session() as session:
            ...     repo = ConversationRepository()
            ...     deleted = await repo.delete(session, "conversation-123")
        """
        return await self.crud.delete(session, id=conversation_id)
    
    # Custom operations
    async def store_messages(
        self, 
        session: AsyncSession, 
        conversation_id: str, 
        messages: List[Union[ModelRequest, ModelResponse]]
    ) -> None:
        """Store updated message history asynchronously.
        
        Args:
            session: The async database session to use for the operation
            conversation_id: The ID of the conversation to update
            messages: List of ModelMessage objects to store
            
        Raises:
            ValueError: If the conversation is not found
            
        Example:
            >>> from pydantic_ai.messages import ModelMessage, Role
            >>> messages = [ModelMessage(role=Role.USER, content="Hello")]
            >>> async with async_session() as session:
            ...     repo = ConversationRepository()
            ...     await repo.store_messages(session, "conversation-123", messages)
        """
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
        """Retrieve message history for a conversation asynchronously.
        
        Args:
            session: The async database session to use for the query
            conversation_id: The ID of the conversation to retrieve messages for
            
        Returns:
            A list of ModelMessage objects representing the conversation history
            
        Raises:
            ValueError: If there's an error deserializing the message history
            
        Example:
            >>> async with async_session() as session:
            ...     repo = ConversationRepository()
            ...     messages = await repo.get_message_history(session, "conversation-123")
        """
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
        """Get all conversations for a specific spy asynchronously.
        
        Args:
            session: The async database session to use for the query
            spy_id: The ID of the spy to retrieve conversations for
            
        Returns:
            A list of Conversation objects belonging to the specified spy
            
        Example:
            >>> async with async_session() as session:
            ...     repo = ConversationRepository()
            ...     convos = await repo.get_by_spy_id(session, "spy-123")
        """
        query = select(Conversation).where(Conversation.spy_id == spy_id)
        result: Result = await session.execute(query)
        return list(result.scalars().all())
    
    # Synchronous versions for compatibility with existing code
    
    def get_sync(self, session: Session, conversation_id: str) -> Optional[Conversation]:
        """Synchronously get a conversation by ID.
        
        This is a synchronous version of the get() method for use in contexts
        where async/await is not available.
        
        Args:
            session: The SQLAlchemy session to use for the query
            conversation_id: The unique identifier of the conversation to retrieve
            
        Returns:
            The Conversation object if found, None otherwise
        """
        return session.query(Conversation).filter(Conversation.id == conversation_id).first()
    
    def create_sync(self, session: Session, spy_id: str) -> str:
        """Synchronously create a new conversation and return its ID.
        
        This is a synchronous version of the create() method for use in contexts
        where async/await is not available.
        
        Args:
            session: The SQLAlchemy session to use for the operation
            spy_id: The ID of the spy this conversation belongs to
            
        Returns:
            The newly created conversation's ID
            
        Note:
            This method commits the transaction within the function.
        """
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
        """Synchronously list all conversations with pagination.
        
        This is a synchronous version of the list() method for use in contexts
        where async/await is not available.
        
        Args:
            session: The SQLAlchemy session to use for the query
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return (for pagination)
            
        Returns:
            A list of Conversation objects
        """
        return session.query(Conversation).offset(skip).limit(limit).all()
    
    def delete_sync(self, session: Session, conversation_id: str) -> bool:
        """Synchronously delete a conversation.
        
        This is a synchronous version of the delete() method for use in contexts
        where async/await is not available.
        
        Args:
            session: The SQLAlchemy session to use for the operation
            conversation_id: The ID of the conversation to delete
            
        Returns:
            bool: True if the conversation was deleted, False if not found
            
        Note:
            This method commits the transaction within the function.
        """
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
        """Synchronously store updated message history.
        
        This is a synchronous version of the store_messages() method for use in 
        contexts where async/await is not available.
        
        Args:
            session: The SQLAlchemy session to use for the operation
            conversation_id: The ID of the conversation to update
            messages: List of ModelMessage objects to store
            
        Raises:
            ValueError: If the conversation is not found
            
        Note:
            This method commits the transaction within the function.
        """
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
        """Synchronously retrieve message history for a conversation.
        
        This is a synchronous version of the get_message_history() method for use in 
        contexts where async/await is not available.
        
        Args:
            session: The SQLAlchemy session to use for the query
            conversation_id: The ID of the conversation to retrieve messages for
            
        Returns:
            A list of ModelMessage objects representing the conversation history
            
        Raises:
            ValueError: If there's an error deserializing the message history
        """
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
