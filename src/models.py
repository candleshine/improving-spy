from sqlalchemy import Column, String, Text
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from typing import Optional

# SQLAlchemy ORM Base
Base = declarative_base()

# Database Model: Spy
class Spy(Base):
    __tablename__ = "spies"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    codename = Column(String, nullable=False)
    biography = Column(Text, nullable=False)
    specialty = Column(String, nullable=False)

# Database Model: Conversation
class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True)
    spy_id = Column(String, nullable=False)
    messages = Column(Text, nullable=False)  # JSON-serialized message history

# Pydantic Models (for API)
class SpyProfile(BaseModel):
    id: str
    name: str
    codename: str
    biography: str
    specialty: str

# Request/Response Models
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    spy_id: str
    spy_name: str
    message: str
    response: str
    mission_id: Optional[str] = None
    conversation_id: Optional[str] = None