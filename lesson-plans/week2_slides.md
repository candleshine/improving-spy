---
marp: true
author: Daniel Chen
email: daniel_chen@improving.com
theme: default
---

# 🕵️‍♂️ Week 2: Agent Recruitment – Create & Store Agents

## *Mission Objective*

- Create and store agents using FastAPI, Pydantic, and SQLAlchemy
- **NEW:** Use FastCRUD for rapid CRUD endpoints
- Add persistent storage to your spy agency app
- Practice CRUD operations with a real database

---

## 🚀 Why FastCRUD?

- Instantly generate CRUD endpoints for your models
- Async support out of the box
- Less code, fewer bugs, faster lessons!
- [FastCRUD on GitHub](https://github.com/benavlabs/fastcrud)

---

## 👋 Welcome & Show-and-Tell

- Check in with everyone
- Share agent profiles or Pydantic models from homework

---

## 🔄 Recap + Preview

- Recap project setup and BaseModel work
- Today’s goal: Store agents in a real database
- Preview: Building endpoints with FastAPI, Pydantic, SQLAlchemy
- **FastCRUD will make this faster!**

---

## 💡 Concept + Live Demo

### What We'll Cover

- FastAPI endpoints for agents
- Defining agent model with Pydantic
- Connecting to SQLite with SQLAlchemy ORM
- Using FastCRUD for instant CRUD
- Why SQLAlchemy makes our app database-flexible

---

### 🗄️ Why SQLite?

- Lightweight, file-based, no setup
- Perfect for local development

### 🔁 SQLAlchemy: Your Database Translator

- ORM (Object Relational Mapping) = Write Python, not SQL
- Supports: SQLite, PostgreSQL, MySQL, SQL Server, Oracle
- Switch databases by changing just the connection string!

---

### 🌐 Real-World Flexibility

| Today: `sqlite+aiosqlite:///./test.db  `
| Later: `postgresql+asyncpg://user:pass@localhost/agents_db`
---

### 🚀 FastAPI + SQLAlchemy + FastCRUD = Rapid, Portable Backend

---

### Live Demo: `/agents` Endpoint with FastCRUD

- Create `/agents` CRUD endpoints instantly
- Save agent to database
- Return agent as JSON

--- 

define the DB connection

```python
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

```

---

```python
class Base(DeclarativeBase): 
    # the magic that turns your Pydantic models into SQLAlchemy models
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
```

---

```python

# --- Dependency ---
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session

# --- Lifespan --- 
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all) # any models that inherit Base will be synchronized, created if missing
    yield

# --- FastAPI App & Router ---
app = FastAPI(lifespan=lifespan) # run the lifespan function on startup of the app

```

---

```python

agent_router = crud_router(
    session=get_session,
    model=Agent,
    create_schema=AgentCreate,
    update_schema=AgentUpdate,
    path="/agents",
    tags=["Agents"],
)

app.include_router(agent_router)
```

---

## Swagger OpenAPI UI

- FastAPI automatically generates a Swagger UI for your API
- Try it out: `http://localhost:8000/docs`

---

## 🏗️ In-Session Exercise

- Implement `/agent/codename/{codename}` GET route
- Test with curl or Postman
- Instructor available for troubleshooting

---

## 📝 **Homework: Prepare Your Agent for Action**

Complete the following tasks before next session. This will set you up for success in **Week 3: Solo Ops – Chatting with Your Agent via LLM**.

#### 1. **Enhance Your Agent Model**

Expand your database model with at least two new fields to make your agent more realistic and expressive. Examples:

- `equipment: str` (e.g., "laser watch, invisibility cloak")
- `skills: str` (e.g., "lockpicking, disguise, hacking")
- `personality: str` (e.g., "sarcastic, no-nonsense")
- `location: str` (e.g., "Cairo, Istanbul, deep underground")

> 💡 Tip: Update both your SQLAlchemy model (`Agent`) and Pydantic schemas (`AgentCreate`, `AgentUpdate`) in your code.

---

#### 2. **Test Your CRUD Endpoints**

Verify that all FastCRUD operations work:

- `POST /agents` – Create a new agent
- `GET /agents/{id}` – Retrieve a specific agent by ID
- `GET /agents` – List all agents
- (Optional) `PUT /agents/{id}` – Update an agent
- (Optional) `DELETE /agents/{id}` – Delete an agent

Use `curl`, **Postman**, or the **Swagger UI** (`http://localhost:8000/docs`) to test.

#### 3. **Install Ollama (Required for Week 3)**

Download and install [Ollama](https://ollama.com/download) for your OS (macOS, Windows, or Linux).

After installation, verify it works:

```bash
ollama --version
---

## ❓ Q&A or Demo Prep (Optional)

- Troubleshoot, review code, answer questions
