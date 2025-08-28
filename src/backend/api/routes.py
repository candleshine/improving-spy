import logging
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..services.agent import ChatAgent
from ..core.database import get_db
from ..models import ChatRequest, ChatResponse, Spy, SpyCreate
from ..repositories.conversation_repository import ConversationRepository
from ..repositories.spy_repository import SpyRepository

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api", tags=["Chat"])

# Initialize repositories

def is_valid_uuid(val):
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False

# Dependency that provides a ChatAgent instance for the spy.
def get_agent(spy_identifier: str, db: Session = Depends(get_db)) -> ChatAgent:
    """Dependency that provides a ChatAgent instance for the spy.
    
    Args:
        spy_identifier: Either a spy's UUID or codename
    """
    repo = SpyRepository(db)
    
    # First try to get by ID (UUID)
    if is_valid_uuid(spy_identifier):
        spy = repo.get(spy_identifier)
    else:
        # If not a valid UUID, try to find by codename
        spy = repo.get_by_codename(spy_identifier)
    
    if not spy:
        raise HTTPException(status_code=404, detail=f"Spy not found: {spy_identifier}")
    
    # Convert SQLAlchemy model to dict to avoid passing the session
    spy_dict = {
        'id': str(spy.id),  # Ensure id is a string as expected by Pydantic
        'name': spy.name,
        'codename': spy.codename,
        'biography': spy.biography,
        'specialty': spy.specialty
    }
    
    return ChatAgent(spy_dict)

# -------------------------------
# Endpoints
# -------------------------------

# -------------------------------
# Spy CRUD Endpoints
# -------------------------------

@router.get("/spies/", response_model=List[Spy])
def list_spies(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """List all spies with pagination"""
    repo = SpyRepository(db)
    return repo.list(skip=skip, limit=limit)

@router.post("/spies/", response_model=Spy, status_code=status.HTTP_201_CREATED)
def create_spy(
    spy: SpyCreate,
    db: Session = Depends(get_db)
):
    """Create a new spy"""
    repo = SpyRepository(db)
    db_spy = repo.create(spy.model_dump())
    return db_spy

@router.get("/spies/{spy_id}", response_model=Spy)
def get_spy(
    spy_id: str,
    db: Session = Depends(get_db)
):
    """Get a spy by ID"""
    repo = SpyRepository(db)
    spy = repo.get(spy_id)
    if not spy:
        raise HTTPException(status_code=404, detail="Spy not found")
    return spy

@router.get("/spies/codename/{codename}", response_model=Spy)
def get_spy_by_codename(
    codename: str,
    db: Session = Depends(get_db)
):
    """Get a spy by codename"""
    repo = SpyRepository(db)
    spy = repo.get_by_codename(codename)
    if not spy:
        raise HTTPException(status_code=404, detail=f"Spy with codename '{codename}' not found")
    return spy

@router.put("/spies/{spy_id}", response_model=Spy)
def update_spy(
    spy_id: str,
    spy_update: Spy,
    db: Session = Depends(get_db)
):
    """Update a spy"""
    repo = SpyRepository(db)
    db_spy = repo.update(spy_id, spy_update.dict())
    if not db_spy:
        raise HTTPException(status_code=404, detail="Spy not found")
    return db_spy

@router.delete("/spies/{spy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_spy(
    spy_id: str,
    db: Session = Depends(get_db)
):
    """Delete a spy"""
    repo = SpyRepository(db)
    if not repo.delete(spy_id):
        raise HTTPException(status_code=404, detail="Spy not found")
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
    logger.info(f"Received chat request for spy_id: {spy_id}")
    try:
        # Initialize conversation repository
        logger.info("Initializing conversation repository...")
        conversation_repository = ConversationRepository(db)
        logger.info("Conversation repository initialized")

        try:
            # Get the agent
            logger.info(f"Getting agent for spy_id: {spy_id}")
            agent = get_agent(spy_id, db)
            logger.info("Agent initialized successfully")
            
            # Get the response from the agent
            logger.info("Sending message to agent...")
            result = await agent.chat(message=request.message)
            logger.info("Received response from agent")
            
            # Return a simple response with the agent's reply
            response = {
                "spy_id": result.get("spy_id", ""),
                "spy_name": result.get("spy_name", "Unknown"),
                "message": request.message,
                "response": result.get("response", ""),
                "tool_calls": result.get("tool_calls", [])
            }
            logger.info("Sending response back to client")
            return response
            
        except HTTPException as he:
            logger.error(f"HTTP Exception in chat processing: {str(he)}")
            raise
        except Exception as e:
            logger.error(f"Error in chat processing: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Error processing chat: {str(e)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat_with_spy: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing chat request: {str(e)}"
        )
