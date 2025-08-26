from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Conversation

from .models import Base

# SQLite for simplicity
DATABASE_URL = "sqlite:///./spy_chat.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Initialize DB
def init_db():
    Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()