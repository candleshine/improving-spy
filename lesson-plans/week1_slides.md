---
marp: true
author: Daniel Chen
email: daniel_chen@improving.com
theme: default
---

# 🕵️‍♂️ Python Spy Agency: Project Overview

**Course Goal:**
Build the backend API for a chat app (UI provided) that lets users chat with a secret agent you design. Your API will connect to an Ollama-based LLM, which will craft responses in your agent's unique style.

**Week 1 Homework:**
Define your agent's personality! Decide how your agent talks, acts, and responds. The personality you create this week will shape how the LLM replies to users through your API.
---

# 🕵️ Week 1: Mission Briefing – Setup HQ

## *Mission Objective*

- Set up your Python Spy Agency development environment
- Understand project structure and tooling
- Prepare your agent profile for future missions

---

## 👋 Instructor Intro

- **Daniel Chen**
- <daniel_chen@improving.com>
- A few facts about me:
  - Principal Consultant in the Dallas Office
  - Father of 5, husband of 1, habitual dad joker
  - 20+ years of experience in software development
  - Passionate about agentic AI and how it can transform the industry

---

## 🛠️ Tools We'll Use

- Python 3.x
- Astral UV
- VS Code
- FastAPI
- Git & GitHub

---

## 🧪 Today's Feature

- Build your development HQ (project setup)
- Create your first agent profile
- See how setup fits into the final Spy Agency app

---

## 📦 Code Walkthrough

### 1. Install UV & Set Up Environment

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv init
uv add fastapi uvicorn rich
```

- Create project folder structure
- Add FastAPI, Uvicorn, SQLAlchemy

---

### 2. VS Code Setup

- Recommended extensions
  - Python or Pylance for IntelliSense
  - Ruff for linting
  
- Open project folder

---

### 3. FastAPI Hello World

```python
# src/main.py
from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def read_root():
    return {"msg": "Hello, Agent!"}
```

---

#### 🚦 Run & Test Your FastAPI App

1. **Run the server:**

   ```bash
   uv run uvicorn src.main:app --reload
   ```

   By default, this will start FastAPI on http://127.0.0.1:8000/.

---

2. **Test with HTTP request file (VS Code):**

   Open `requests.http` and click "Send Request" above the line:

   ```http
   GET http://127.0.0.1:8000/
   Accept: application/json
   ```

   You should see `{ "msg": "Hello, Agent!" }` in the response.

---

3. **Test with curl (terminal):**

   ```bash
   curl -X GET http://127.0.0.1:8000/ -H "accept: application/json"
   ```

   This should also return `{ "msg": "Hello, Agent!" }`.

### 4. Create Agent Model (starter)

```python
# src/models.py
# (Stub out your agent class for now)
from pydantic import BaseModel

class Agent(BaseModel):
    name: str
    role: str
    clearance: int
```

---

## 🧑‍💻 In-Session Exercise

- Clone or create your own repo
- Set up your environment with UV
- Define your agent profile: name, role, clearance
- Ask for help if you get stuck!

---

## 📝 Homework + Teaser

- Push your setup to GitHub
- Read Astral UV Docs
- **NEW:** Invent a Pydantic BaseModel for your agent profile (name, role, clearance, etc.)
  - We'll use this for real data validation next week!
- Optional: Write a creative backstory for your agent
- Next week: Add a database and start recruiting agents!

---

### 🧑‍💻 Bonus: Python Code Sample

Here’s a scaffold to help you get started with your agent profile using Pydantic’s BaseModel:

```python
from pydantic import BaseModel

class Agent(BaseModel):
    name: str
    role: str
    clearance: int

# Create an instance of your agent
agent = Agent(name="Jane Bond", role="Field Operative", clearance=7)
print(agent)
```

---

#### Fancy Output with Rich

For a visually appealing terminal output, try using the [Rich](https://rich.readthedocs.io/en/stable/) library:

```python
from pydantic import BaseModel
from rich.console import Console
from rich.pretty import Pretty

class Agent(BaseModel):
    name: str
    role: str
    clearance: int

agent = Agent(name="Jane Bond", role="Field Operative", clearance=7)
console = Console()
console.print(Pretty(agent.dict()))
```

- [ ] Challenge: Print your agent profile using Rich for extra style!

---

## 🧠 Final Thought

- Why setup and data models matter for all agentic systems
- Your HQ is the launchpad for all future spy missions!
