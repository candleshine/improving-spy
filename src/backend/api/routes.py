import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..services.agent import ChatAgent
from ..core.database import get_db
from ..models import ChatRequest, ChatResponse, Spy, SpyCreate, SpyBase
from ..repositories.conversation_repository import ConversationRepository
from ..repositories.spy_repository import SpyRepository

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api", tags=["Chat"])

# Initialize repositories
spy_repository = SpyRepository()
conversation_repository = ConversationRepository()

# -------------------------------
# Dependencies
# -------------------------------

def get_agent(spy_id: str, db: Session = Depends(get_db)) -> ChatAgent:
    """Dependency that provides a ChatAgent instance for the spy."""
    spy = spy_repository.get_sync(db, spy_id)
    if not spy:
        raise HTTPException(status_code=404, detail=f"Spy {spy_id} not found")
    return ChatAgent(spy)

# -------------------------------
# Endpoints
# -------------------------------

# -------------------------------
# Spy CRUD Endpoints
# -------------------------------

@router.get("/spies/", response_model=List[Spy])
async def list_spies(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """List all spies with pagination"""
    return await spy_repository.list(db, skip=skip, limit=limit)

@router.post("/spies/", response_model=Spy, status_code=status.HTTP_201_CREATED)
async def create_spy(
    spy: SpyCreate,
    db: Session = Depends(get_db)
):
    """Create a new spy"""
    db_spy = await spy_repository.create(db, spy.dict())
    return db_spy

@router.get("/spies/{spy_id}", response_model=Spy)
async def get_spy(
    spy_id: str,
    db: Session = Depends(get_db)
):
    """Get a spy by ID"""
    spy = await spy_repository.get(db, spy_id)
    if not spy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Spy with ID {spy_id} not found"
        )
    return spy

@router.put("/spies/{spy_id}", response_model=Spy)
async def update_spy(
    spy_id: str,
    spy_update: Spy,
    db: Session = Depends(get_db)
):
    """Update a spy"""
    spy = await spy_repository.update(db, spy_id, spy_update.dict(exclude_unset=True))
    if not spy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Spy with ID {spy_id} not found"
        )
    return spy

@router.delete("/spies/{spy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_spy(
    spy_id: str,
    db: Session = Depends(get_db)
):
    """Delete a spy"""
    spy = await spy_repository.delete(db, spy_id)
    if not spy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Spy with ID {spy_id} not found"
        )
    return None

# -------------------------------
# Chat Endpoints
# -------------------------------

@router.post("/chat/{spy_id}", response_model=ChatResponse)
async def chat_with_spy(
    spy_id: str, 
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Chat with a spy agent.
    
    Each spy has exactly one active conversation. Messages are automatically
    added to the spy's conversation history.
    """
    try:
        # Get or create the spy's conversation
        conversation = conversation_repository.get_or_create_by_spy_id(db, spy_id)
        
        # Get the agent
        agent = get_agent(spy_id, db)
        
        # Get the response from the agent
        result = await agent.chat(
            message=request.message,
            conversation_id=str(conversation.id)
        )
        
        # Save messages to conversation history
        conversation_repository.add_message(
            db,
            conversation_id=str(conversation.id),
            role="user",
            content=request.message
        )
        
        conversation_repository.add_message(
            db,
            conversation_id=str(conversation.id),
            role="assistant",
            content=result["response"]
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
        logger.error(f"Error in chat_with_spy: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing chat request: {str(e)}"
        )
