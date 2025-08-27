from fastcrud import FastCRUD
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..models import Spy
import uuid
from typing import Optional, List, Dict, Any

class SpyRepository:
    def __init__(self):
        self.crud = FastCRUD(model=Spy)
    
    # Standard CRUD operations via FastCRUD
    async def get(self, session: AsyncSession, spy_id: str) -> Optional[Spy]:
        """Get a spy by ID asynchronously."""
        return await self.crud.get(session, id=spy_id)
        
    async def create(self, session: AsyncSession, data: Dict[str, Any]) -> Spy:
        """Create a new spy asynchronously."""
        if "id" not in data:
            data["id"] = str(uuid.uuid4())
        return await self.crud.create(session, data)
    
    async def list(self, session: AsyncSession, skip: int = 0, limit: int = 100) -> List[Spy]:
        """List all spies with pagination asynchronously."""
        return await self.crud.get_multi(session, skip=skip, limit=limit)
    
    async def update(self, session: AsyncSession, spy_id: str, data: Dict[str, Any]) -> Optional[Spy]:
        """Update a spy asynchronously."""
        return await self.crud.update(session, id=spy_id, obj_in=data)
    
    async def delete(self, session: AsyncSession, spy_id: str) -> Optional[Spy]:
        """Delete a spy asynchronously."""
        return await self.crud.delete(session, id=spy_id)
    
    # Custom operations
    async def get_by_codename(self, session: AsyncSession, codename: str) -> Optional[Spy]:
        """Get a spy by codename asynchronously."""
        query = select(Spy).where(Spy.codename == codename)
        result = await session.execute(query)
        return result.scalars().first()
    
    async def search_by_specialty(self, session: AsyncSession, specialty: str) -> List[Spy]:
        """Search spies by specialty asynchronously."""
        query = select(Spy).where(Spy.specialty == specialty)
        result = await session.execute(query)
        return list(result.scalars().all())
    
    # Sync versions for compatibility with existing code
    def get_sync(self, session: Session, spy_id: str) -> Optional[Spy]:
        """Get a spy by ID (synchronous version)."""
        return session.query(Spy).filter(Spy.id == spy_id).first()
    
    def create_sync(self, session: Session, data: Dict[str, Any]) -> Spy:
        """Create a new spy (synchronous version)."""
        if "id" not in data:
            data["id"] = str(uuid.uuid4())
        spy = Spy(**data)
        session.add(spy)
        session.commit()
        session.refresh(spy)
        return spy
        
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
