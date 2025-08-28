from sqlalchemy.orm import Session
from sqlalchemy.future import select
from ..models import Spy, SpyModel
import uuid
from typing import Optional, List, Dict, Any

class SpyRepository:
    def __init__(self, db: Session):
        self.db = db
    
    # Standard CRUD operations
    def get(self, spy_id: str) -> Optional[Spy]:
        """Get a spy by ID."""
        result = self.db.get(SpyModel, spy_id)
        if result:
            return Spy.model_validate(result, from_attributes=True)
        return None
        
    def create(self, data) -> Spy:
        """Create a new spy.
        
        Args:
            data: Either a dictionary or Pydantic model containing spy data
            
        Returns:
            Spy: The created spy
        """
        # Convert Pydantic model to dict if needed
        if hasattr(data, 'model_dump'):
            data = data.model_dump()
            
        if "id" not in data:
            data["id"] = str(uuid.uuid4())
            
        spy_model = SpyModel(**data)
        self.db.add(spy_model)
        self.db.commit()
        self.db.refresh(spy_model)
        return Spy.model_validate(spy_model, from_attributes=True)
    
    def list(self, skip: int = 0, limit: int = 100) -> List[Spy]:
        """List all spies with pagination."""
        result = self.db.execute(
            select(SpyModel).offset(skip).limit(limit)
        ).scalars().all()
        return [Spy.model_validate(spy, from_attributes=True) for spy in result]
    
    def update(self, spy_id: str, data: Dict[str, Any]) -> Optional[Spy]:
        """Update a spy."""
        spy = self.db.get(SpyModel, spy_id)
        if not spy:
            return None
            
        for key, value in data.items():
            setattr(spy, key, value)
            
        self.db.commit()
        self.db.refresh(spy)
        return Spy.model_validate(spy, from_attributes=True)
    
    def delete(self, spy_id: str) -> bool:
        """Delete a spy."""
        spy = self.db.get(SpyModel, spy_id)
        if not spy:
            return False
            
        self.db.delete(spy)
        self.db.commit()
        return True
    
    # Custom operations
    def get_by_codename(self, codename: str) -> Optional[Spy]:
        """Get a spy by codename."""
        result = self.db.execute(
            select(SpyModel).where(SpyModel.codename == codename)
        ).scalars().first()
        if result:
            return Spy.model_validate(result, from_attributes=True)
        return None
    
    def search_by_specialty(self, specialty: str) -> List[Spy]:
        """Search spies by specialty."""
        result = self.db.execute(
            select(SpyModel).where(SpyModel.specialty == specialty)
        ).scalars().all()
        return [Spy.model_validate(spy, from_attributes=True) for spy in result]
        
    def list_sync(self, session: Session, skip: int = 0, limit: int = 100) -> List[Spy]:
        """List all spies with pagination (synchronous version)."""
        return session.query(Spy).offset(skip).limit(limit).all()
    
    def update_sync(self, session: Session, spy_id: str, data: Dict[str, Any]) -> Optional[Spy]:
        """Update a spy (synchronous version)."""
        spy = self.get_sync(session, spy_id)
        if not spy:
            return None
        
        for key, value in data.items():
            setattr(spy, key, value)
        
        session.commit()
        session.refresh(spy)
        return spy
    
    def delete_sync(self, session: Session, spy_id: str) -> bool:
        """Delete a spy (synchronous version)."""
        spy = self.get_sync(session, spy_id)
        if not spy:
            return False
        
        session.delete(spy)
        session.commit()
        return True
    
    def get_by_codename_sync(self, session: Session, codename: str) -> Optional[Spy]:
        """Get a spy by codename (synchronous version)."""
        return session.query(Spy).filter(Spy.codename == codename).first()
    
    def search_by_specialty_sync(self, session: Session, specialty: str) -> List[Spy]:
        """Search spies by specialty (synchronous version)."""
        return session.query(Spy).filter(Spy.specialty == specialty).all()
