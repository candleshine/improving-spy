import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, Form, HTTPException, WebSocket, WebSocketDisconnect, status, Header
from sqlalchemy.orm import Session

from ..services.agent import ChatAgent
from ..core.database import get_db
from ..models import ChatRequest, ChatResponse, SpyProfile
from ..repositories.conversation_repository import ConversationRepository
from ..repositories.spy_repository import SpyRepository
from ..core.websocket_manager import manager

# Set up logging
logger = logging.getLogger(__name__)

# Create routers
router = APIRouter(prefix="/api", tags=["Chat"])
spy_router = APIRouter(prefix="/spies", tags=["Spies"])
ws_router = APIRouter(prefix="/ws", tags=["WebSockets"])

# Initialize repositories
spy_repository = SpyRepository()
conversation_repository = ConversationRepository()

# -------------------------------
# Dependencies
# -------------------------------

# Agent factory with LRU cache
def get_agent(spy_id: str, db: Session = Depends(get_db)):
    """Dependency that provides a ChatAgent instance for the spy."""
    spy = spy_repository.get_sync(db, spy_id)
    if not spy:
        raise HTTPException(status_code=404, detail=f"Spy {spy_id} not found")
        
    spy_data = {
        "id": spy.id,
        "name": spy.name,
        "codename": spy.codename,
        "biography": spy.biography,
        "specialty": spy.specialty
    }
    return ChatAgent(spy_data)

# -------------------------------
# Endpoints
# -------------------------------

@router.post("/chat/{spy_id}", response_model=ChatResponse)
async def chat_with_spy(
    spy_id: str, 
    request: ChatRequest, 
    agent: ChatAgent = Depends(get_agent),
    db: Session = Depends(get_db),
    x_mission_id: Optional[str] = Header(None)
):
    """
    Unified chat endpoint for all spy interactions.
    
    Supports both regular chat and mission debriefs through tool calling.
    Uses a cached ChatAgent instance for better performance.
    """
    try:
        # Get the response from the agent
        result = await agent.chat(
            message=request.message,
            tool_calls=request.tool_calls,
            tool_outputs=request.tool_outputs
        )
        
        return ChatResponse(
            spy_id=spy_id,
            spy_name=agent.spy.name,
            message=request.message,
            response=result["response"],
            tool_calls=result.get("tool_calls", [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing chat request: {str(e)}"
        )


@router.post("/chat/{spy_id}/conversation/{conversation_id}", response_model=ChatResponse)
async def chat_with_conversation_history(
    spy_id: str,
    conversation_id: str,
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Chat with a spy agent using conversation history for context.
    
    Supports tool calling for mission context and other operations.
    """
    logger.info(f"Received chat request for spy_id={spy_id}, conversation_id={conversation_id}")
    logger.debug(f"Request message: {request.message}")
    logger.debug(f"Tool calls: {request.tool_calls}")
    logger.debug(f"Tool outputs: {request.tool_outputs}")
    
    try:
        # Get spy data
        logger.debug(f"Fetching spy data for spy_id={spy_id}")
        spy = spy_repository.get_sync(db, spy_id)
        if not spy:
            error_msg = f"Spy {spy_id} not found"
            logger.error(error_msg)
            raise HTTPException(status_code=404, detail=error_msg)
        
        # Get existing conversation
        logger.debug(f"Fetching conversation with id={conversation_id}")
        conversation = conversation_repository.get_sync(db, conversation_id)
        if not conversation:
            error_msg = f"Conversation {conversation_id} not found"
            logger.error(error_msg)
            raise HTTPException(status_code=404, detail=error_msg)
            
        # Verify the conversation belongs to this spy
        if conversation.spy_id != spy_id:
            error_msg = f"Conversation {conversation_id} does not belong to spy {spy_id}"
            logger.error(error_msg)
            raise HTTPException(status_code=403, detail=error_msg)
        
        # Prepare spy data for agent
        spy_data = {
            "id": spy.id,
            "name": spy.name,
            "codename": spy.codename,
            "biography": spy.biography,
            "specialty": spy.specialty
        }
        logger.debug("Spy data prepared for agent")
        
        # Get conversation history
        logger.debug(f"Fetching message history for conversation_id={conversation_id}")
        messages = conversation_repository.get_message_history_sync(db, conversation_id)
        logger.debug(f"Retrieved {len(messages)} previous messages")
        
        # Initialize the agent
        logger.info("Initializing ChatAgent")
        try:
            agent = ChatAgent(spy_data)
            logger.debug("ChatAgent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ChatAgent: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to initialize agent: {str(e)}")
        
        try:
            # Get the response from the agent
            logger.info("Sending message to agent")
            result = await agent.chat(
                message=request.message,
                tool_calls=request.tool_calls,
                tool_outputs=request.tool_outputs
            )
            logger.debug("Received response from agent")
            
            # Update conversation history
            logger.debug("Updating conversation history")
            # Store messages as simple dictionaries
            user_message = {"role": "user", "content": request.message}
            
            # Handle both LLMResponse and LLMResponseWithTools
            response_content = result.content
            tool_calls = []
            if hasattr(result, 'tool_calls'):
                tool_calls = [
                    {
                        "id": call.id,
                        "name": call.name,
                        "arguments": call.arguments
                    }
                    for call in result.tool_calls
                ]
            
            assistant_message = {"role": "assistant", "content": response_content}
            if tool_calls:
                assistant_message["tool_calls"] = tool_calls
                
            messages.extend([user_message, assistant_message])
            conversation_repository.store_messages_sync(db, conversation_id, messages)
            
            logger.info("Chat request processed successfully")
            return ChatResponse(
                spy_id=spy_id,
                spy_name=spy.name,
                message=request.message,
                response=response_content,
                tool_calls=tool_calls,
                conversation_id=conversation_id
            )
            
        except HTTPException as he:
            logger.error(f"HTTPException in agent.chat: {str(he.detail)}")
            raise
        except Exception as e:
            logger.error(f"Error in agent.chat: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500, 
                detail=f"Error processing chat request: {str(e)}"
            )
            
    except HTTPException as he:
        logger.error(f"HTTPException in chat_with_conversation_history: {str(he.detail)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in chat_with_conversation_history: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"An unexpected error occurred: {str(e)}"
        )
    
    # This code is unreachable due to the try/except block above
    # It's safe to remove as the functionality is already handled in the try block
    pass


@router.post("/conversation", response_model=dict)
async def create_new_conversation(
    spy_id: str = Form(...),
    db: Session = Depends(get_db)
):
    """Create a new conversation for a spy."""
    spy = spy_repository.get_sync(db, spy_id)
    if not spy:
        raise HTTPException(status_code=404, detail=f"Spy {spy_id} not found")

    conversation_id = conversation_repository.create_sync(db, spy_id)
    return {
        "spy_id": spy_id,
        "conversation_id": conversation_id
    }


# Spy routes using repository pattern
# Create
@spy_router.post("/", response_model=SpyProfile)
async def create_spy(spy: SpyProfile, db: Session = Depends(get_db)):
    """Create a new spy."""
    created_spy = spy_repository.create_sync(db, spy.model_dump())
    return created_spy

# Read all
@spy_router.get("/", response_model=List[SpyProfile])
async def list_spies(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all spies."""
    return spy_repository.list_sync(db, skip, limit)

# Read one
@spy_router.get("/{spy_id}", response_model=SpyProfile)
async def get_spy(spy_id: str, db: Session = Depends(get_db)):
    """Get a spy by ID."""
    spy = spy_repository.get_sync(db, spy_id)
    if not spy:
        raise HTTPException(status_code=404, detail=f"Spy {spy_id} not found")
    return spy

# Update
@spy_router.put("/{spy_id}", response_model=SpyProfile)
async def update_spy(spy_id: str, spy_data: SpyProfile, db: Session = Depends(get_db)):
    """Update a spy."""
    updated_spy = spy_repository.update_sync(db, spy_id, spy_data.model_dump())
    if not updated_spy:
        raise HTTPException(status_code=404, detail=f"Spy {spy_id} not found")
    return updated_spy

# Delete
@spy_router.delete("/{spy_id}", response_model=dict)
async def delete_spy(spy_id: str, db: Session = Depends(get_db)):
    """Delete a spy."""
    result = spy_repository.delete_sync(db, spy_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Spy {spy_id} not found")
    return {"message": f"Spy {spy_id} deleted successfully"}


# Include the spy router
router.include_router(spy_router)

# WebSocket endpoints
@ws_router.websocket("/chat/{spy_id}")
async def websocket_chat_endpoint(websocket: WebSocket, spy_id: str, db: Session = Depends(get_db)):
    """WebSocket endpoint for real-time chat with a spy."""
    connection_id = await manager.connect(websocket, spy_id=spy_id)
    
    try:
        # Get spy info
        spy = spy_repository.get_sync(db, spy_id)
        if not spy:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
            
        # Send welcome message
        await manager.send_personal_message(
            {
                "type": "system",
                "content": f"Connected to {spy.name} ({spy.codename})"
            },
            connection_id
        )
        
        while True:
            # Wait for messages from the client
            data = await websocket.receive_json()
            
            if "message" not in data:
                await manager.send_personal_message(
                    {"type": "error", "content": "Invalid message format"},
                    connection_id
                )
                continue
                
            # Process the message
            user_message = data["message"]
            
            # Initialize the agent with spy data
            spy_data = {
                "id": spy.id,
                "name": spy.name,
                "codename": spy.codename,
                "biography": spy.biography,
                "specialty": spy.specialty
            }
            agent = ChatAgent(spy_data)
            result = await agent.chat(message=user_message)
            response = result["response"]
            
            # Send response back
            await manager.send_personal_message(
                {
                    "type": "response",
                    "spy_id": spy_id,
                    "spy_name": spy.name,
                    "message": user_message,
                    "response": response
                },
                connection_id
            )
            
    except WebSocketDisconnect:
        manager.disconnect(connection_id)
    except Exception as e:
        # Handle any other exceptions
        try:
            await manager.send_personal_message(
                {"type": "error", "content": str(e)},
                connection_id
            )
        except Exception:
            pass
        manager.disconnect(connection_id)

@ws_router.websocket("/chat/{spy_id}/conversation/{conversation_id}")
async def websocket_conversation_endpoint(
    websocket: WebSocket, 
    spy_id: str, 
    conversation_id: str, 
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for real-time chat with conversation history."""
    connection_id = await manager.connect(
        websocket, 
        spy_id=spy_id, 
        conversation_id=conversation_id
    )
    
    try:
        # Get spy info
        spy = spy_repository.get_sync(db, spy_id)
        if not spy:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
            
        # Send welcome message
        await manager.send_personal_message(
            {
                "type": "system",
                "content": f"Connected to conversation with {spy.name}"
            },
            connection_id
        )
        
        while True:
            # Wait for messages from the client
            data = await websocket.receive_json()
            
            if "message" not in data:
                await manager.send_personal_message(
                    {"type": "error", "content": "Invalid message format"},
                    connection_id
                )
                continue
                
            # Process the message with conversation context
            user_message = data["message"]
            
            # Get message history
            messages = conversation_repository.get_message_history_sync(db, conversation_id)
            
            # Initialize the agent with spy data
            spy_data = {
                "id": spy.id,
                "name": spy.name,
                "codename": spy.codename,
                "biography": spy.biography,
                "specialty": spy.specialty
            }
            agent = ChatAgent(spy_data)
            
            # Convert messages to the format expected by the agent
            chat_messages = [
                {"role": msg.get("role", "user"), "content": msg.get("content", "")} 
                for msg in messages
            ]
            
            # Get the response from the agent
            result = await agent.chat(
                message=user_message,
                messages=chat_messages
            )
            response = result["response"]
            
            # Store the updated conversation
            messages.append({"role": "user", "content": user_message})
            messages.append({"role": "assistant", "content": response})
            conversation_repository.store_messages_sync(db, conversation_id, messages)
            
            # Send response back
            response_data = {
                "type": "response",
                "spy_id": spy_id,
                "spy_name": spy.name,
                "message": user_message,
                "response": response,
                "conversation_id": conversation_id
            }
            
            # Send to this connection and broadcast to others in the same conversation
            await manager.send_personal_message(response_data, connection_id)
            await manager.broadcast_to_conversation(response_data, conversation_id)
            
    except WebSocketDisconnect:
        manager.disconnect(connection_id)
    except Exception as e:
        # Handle any other exceptions
        try:
            await manager.send_personal_message(
                {"type": "error", "content": str(e)},
                connection_id
            )
        except Exception:
            pass
        manager.disconnect(connection_id)

# Include the WebSocket router
router.include_router(ws_router)
