from fastapi import FastAPI
from typing import AsyncGenerator
from fastcrud import crud_router
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String
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