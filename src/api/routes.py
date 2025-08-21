from fastapi import APIRouter, HTTPException, Depends, Form, WebSocket, WebSocketDisconnect, status
from typing import List
from sqlalchemy.orm import Session
from pydantic_ai.messages import ModelMessage

from ..models import ChatRequest, ChatResponse, SpyProfile
from ..agent import (
    chat_with_agent,
    debrief_mission,
    chat_with_context
)
from ..database import get_db
from ..repositories.spy_repository import SpyRepository
from ..repositories.conversation_repository import ConversationRepository
from ..websocket_manager import manager

# Create routers
router = APIRouter(prefix="/api", tags=["Chat"])
spy_router = APIRouter(prefix="/spies", tags=["Spies"])
ws_router = APIRouter(prefix="/ws", tags=["WebSockets"])

# Initialize repositories
spy_repository = SpyRepository()
conversation_repository = ConversationRepository()

# -------------------------------
# Endpoints
# -------------------------------

@router.post("/chat/{spy_id}", response_model=ChatResponse)
async def chat_with_spy(spy_id: str, request: ChatRequest, db: Session = Depends(get_db)):
    """Chat with a spy agent without mission context."""
    spy = spy_repository.get_sync(db, spy_id)
    if not spy:
        raise HTTPException(status_code=404, detail=f"Spy {spy_id} not found")

    # Convert spy object to dict for chat_with_agent
    spy_data = {
        "id": spy.id,
        "name": spy.name,
        "codename": spy.codename,
        "biography": spy.biography,
        "specialty": spy.specialty
    }
    response = chat_with_agent(request.message, spy_data)
    
    return ChatResponse(
        spy_id=spy_id,
        spy_name=spy.name,
        message=request.message,
        response=response
    )


@router.post("/debrief/{spy_id}/{mission_id}", response_model=ChatResponse)
async def debrief_with_spy(spy_id: str, mission_id: str, request: ChatRequest, db: Session = Depends(get_db)):
    """Debrief with a spy agent about a specific mission."""
    spy = spy_repository.get_sync(db, spy_id)
    if not spy:
        raise HTTPException(status_code=404, detail=f"Spy {spy_id} not found")
    
    # Create a conversation for this debrief if needed
    conversation_id = conversation_repository.create_sync(db, spy_id)
    
    # Get existing messages
    messages = conversation_repository.get_message_history_sync(db, conversation_id)
    
    # Generate response
    response = debrief_mission(request.message, spy_id, mission_id, db)
    
    # Store the updated conversation
    messages.append(ModelMessage(role="user", content=request.message))
    messages.append(ModelMessage(role="assistant", content=response))
    conversation_repository.store_messages_sync(db, conversation_id, messages)
    
    return ChatResponse(
        spy_id=spy_id,
        spy_name=spy.name,
        message=request.message,
        response=response
    )


@router.post("/chat/{spy_id}/conversation/{conversation_id}", response_model=ChatResponse)
async def chat_with_conversation_history(
    spy_id: str,
    conversation_id: str,
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """Chat with a spy agent using conversation history for context."""
    spy = spy_repository.get_sync(db, spy_id)
    if not spy:
        raise HTTPException(status_code=404, detail=f"Spy {spy_id} not found")
    
    # Get existing conversation
    conversation = conversation_repository.get_sync(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} not found")
    
    # Verify the conversation belongs to this spy
    if conversation.spy_id != spy_id:
        raise HTTPException(status_code=403, detail="Conversation does not belong to this spy")
    
    # Get message history
    messages = conversation_repository.get_message_history_sync(db, conversation_id)
    
    # Generate response with context
    spy_data = {
        "id": spy.id,
        "name": spy.name,
        "codename": spy.codename,
        "biography": spy.biography,
        "specialty": spy.specialty
    }
    response = chat_with_context(request.message, spy_data, messages)
    
    # Update the conversation with the new message
    messages.append(ModelMessage(role="user", content=request.message))
    messages.append(ModelMessage(role="assistant", content=response))
    conversation_repository.store_messages_sync(db, conversation_id, messages)
    
    return ChatResponse(
        spy_id=spy_id,
        spy_name=spy.name,
        message=request.message,
        response=response,
        conversation_id=conversation_id
    )


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
            
            # Convert spy object to dict for chat_with_agent
            spy_data = {
                "id": spy.id,
                "name": spy.name,
                "codename": spy.codename,
                "biography": spy.biography,
                "specialty": spy.specialty
            }
            response = chat_with_agent(user_message, spy_data)
            
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
            
            # Convert spy to dict format
            spy_data = {
                "id": spy.id,
                "name": spy.name,
                "codename": spy.codename,
                "biography": spy.biography,
                "specialty": spy.specialty
            }
            
            # Use the new chat_with_context signature
            response = chat_with_context(user_message, spy_data, messages)
            
            # Store the updated conversation
            messages.append(ModelMessage(role="user", content=user_message))
            messages.append(ModelMessage(role="assistant", content=response))
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
