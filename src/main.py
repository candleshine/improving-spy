from fastapi import FastAPI, Depends, HTTPException
from typing import AsyncGenerator
from fastcrud import crud_router
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, select
# --- Database Setup ---
DATABASE_URL = "sqlite+aiosqlite:///./test.db"
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

# --- SQLAlchemy Model ---
class Agent(Base):
    __tablename__ = "agents"
    id = Column(Integer, primary_key=True)
    codename = Column(String, nullable=False)
    specialty = Column(String)

# --- Pydantic Schemas ---
class AgentCreate(BaseModel):
    codename: str
    specialty: str

class AgentUpdate(BaseModel):
    codename: str
    specialty: str

# --- Dependency ---
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session

# --- Lifespan ---
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

# --- FastAPI App & Router ---
app = FastAPI(lifespan=lifespan)

agent_router = crud_router(
    session=get_session,
    model=Agent,
    create_schema=AgentCreate,
    update_schema=AgentUpdate,
    path="/agents",
    tags=["Agents"],
)

app.include_router(agent_router)

@app.get("/agents/codename/{codename}", tags=["Agents"])
async def get_agent_by_codename(codename: str, session: AsyncSession = Depends(get_session)):
    """Get an agent by their codename"""
    # Create a select query filtered by codename
    query = select(Agent).where(Agent.codename == codename)
    
    # Execute the query
    result = await session.execute(query)
    
    # Get the first result (or None if no results)
    agent = result.scalars().first()
    
    # If no agent was found, raise a 404 error
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent with codename '{codename}' not found")
    
    # Return the agent
    return agent