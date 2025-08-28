from fastcrud import FastCRUD
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..models import Spy, SpyModel, SpyCreate
import uuid
from typing import Optional, List, Dict, Any

class SpyRepository:
    def __init__(self):
        self.crud = FastCRUD(model=SpyModel)
    
    # Standard CRUD operations via FastCRUD
    async def get(self, session: AsyncSession, spy_id: str) -> Optional[Spy]:
        """Get a spy by ID asynchronously."""
        result = await self.crud.get(session, id=spy_id)
        if result:
            return Spy.from_orm(result)
        return None
        
    async def create(self, session: AsyncSession, data: Dict[str, Any]) -> Spy:
        """Create a new spy asynchronously."""
        if "id" not in data:
            data["id"] = str(uuid.uuid4())
        db_spy = await self.crud.create(session, data)
        return Spy.from_orm(db_spy)
    
    async def list(self, session: AsyncSession, skip: int = 0, limit: int = 100) -> List[Spy]:
        """List all spies with pagination asynchronously."""
        result = await self.crud.get_multi(session, skip=skip, limit=limit)
        return [Spy.from_orm(spy) for spy in result]
    
    async def update(self, session: AsyncSession, spy_id: str, data: Dict[str, Any]) -> Optional[Spy]:
        """Update a spy asynchronously."""
        result = await self.crud.update(session, id=spy_id, obj_in=data)
        if result:
            return Spy.from_orm(result)
        return None
    
    async def delete(self, session: AsyncSession, spy_id: str) -> Optional[Spy]:
        """Delete a spy asynchronously."""
        result = await self.crud.delete(session, id=spy_id)
        if result:
            return Spy.from_orm(result)
        return None
    
    # Custom operations
    async def get_by_codename(self, session: AsyncSession, codename: str) -> Optional[Spy]:
        """Get a spy by codename asynchronously."""
        query = select(SpyModel).where(SpyModel.codename == codename)
        result = await session.execute(query)
        db_spy = result.scalars().first()
        if db_spy:
            return Spy.from_orm(db_spy)
        return None
    
    async def search_by_specialty(self, session: AsyncSession, specialty: str) -> List[Spy]:
        """Search spies by specialty asynchronously."""
        query = select(SpyModel).where(SpyModel.specialty == specialty)
        result = await session.execute(query)
        return [Spy.from_orm(spy) for spy in result.scalars().all()]
    
    # Sync versions for compatibility with existing code
    def get_sync(self, session: Session, spy_id: str) -> Optional[Spy]:
        """Get a spy by ID synchronously."""
        db_spy = session.get(SpyModel, spy_id)
        if db_spy:
            return Spy.from_orm(db_spy)
        return None
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
