# 🧠 Chat with Your Agent – Python Spy Agency

> *Build the backend API for a chat app to create and chat with AI-powered secret agents — using FastAPI, Pydantic AI, and Ollama. (UI provided by your instructor!)*

Welcome to the **Python Spy Agency**, where you'll build your own **AI spy agent** over 4 weekly sessions. The end goal: an API that powers a chat app (UI supplied) where users can talk to a secret agent you design. Your API will connect to an Ollama-based LLM, which will generate responses in your agent’s unique style.

**Week 1 Focus:**
Your first mission is to define your agent’s personality. Decide how your agent talks, acts, and responds—gruff and curt, witty and verbose, mysterious and cryptic? This personality will guide the LLM’s replies in all chats through your API.

By the end of week 1, you’ll have a well-documented agent persona that will shape all future conversations.

- Create custom agents (spies, wizards, detectives — you choose!)
- Store them in a database
- Chat with them via an LLM (using **Ollama** or OpenAI)
- Enable **multi-agent collaboration**

---

## 📚 What You'll Learn

This hands-on course walks you through building a full-stack Python app from scratch — no prior experience needed beyond basic coding knowledge.

### Weekly Themes

| Week | Theme |
| :--- | :---- |
| 1    | **Mission Briefing**: Setup your development environment with UV |
| 2    | **Agent Recruitment**: Build a backend API with FastAPI & SQLAlchemy |
| 3    | **Solo Ops**: Connect your agent to an LLM using Pydantic AI |
| 4    | **Team Extraction**: Enable multi-agent conversations |

---

## 🛠️ Tools We’ll Use

| Tool                                   | Description                                      |
| :------------------------------------- | :----------------------------------------------- |
| **Python 3.11+**                       | Language of choice                               |
| **UV**                                 | Modern Python package manager (fast, pip-compatible) |
| **FastAPI**                            | For building the backend API                     |
| **FastCRUD**                           | For rapid CRUD endpoint generation               |
| **Pydantic Models**                    | For data validation and structure                |
| **SQLAlchemy ORM**                     | To store agent profiles and chats                |
| **Pydantic AI**                        | For building agentic behavior                    |
| **Ollama**                             | Run local LLMs like Llama3 without API keys      |
| **Optional: Streamlit / HTML frontend** | For final deployment and user interface          |

---

## 🧩 Final App Overview

You’ll build a **web-based chat app** where users can:

- **Create** their own AI-powered agent (spy, wizard, detective, etc.)
- **Store** agent details in a database
- **Chat** with the agent using natural language
- **Collaborate** with multiple agents on shared missions

---

## 📁 Project Structure

```text
chat-with-agent/
├── pyproject.toml
├── README.md
├── .gitignore
├── src/
│   ├── main.py              ← Run server
│   ├── agent.py             ← Agent logic
│   ├── tools.py             ← Decoding, scanning, etc.
│   ├── database.py          ← SQLAlchemy setup
│   ├── models.py            ← Pydantic models
│   └── api/
│       ├── main.py          ← FastAPI entry point
│       └── routes.py        ← Endpoints for agents and chat
├── notes/
│   └── session_1_to_4_notes.md
└── tests/
    └── test_agent.py
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or higher
- [Ollama](https://ollama.ai/) installed and running (for local LLM support)

### 1. Install UV (if you don't have it)

`uv` is a fast, modern Python package manager. We'll use it to manage our environment and dependencies.

```bash
# Recommended installation method
curl -LsSf https://astral.sh/uv/install.sh | sh

# Alternative method via pip (if you have an existing Python)
pip install uv
```

### 2. Clone This Repo

```bash
# Use the GitHub CLI or clone manually
git clone https://github.com/your-username/chat-with-agent.git
cd chat-with-agent
```

### 3. Initialize the Project & Install Dependencies

This single command creates a virtual environment and installs all the packages listed in `pyproject.toml`.

```bash
uv sync
```

*Note: For the course, we will add dependencies week by week using `uv add <package-name>`.*

### 4. Run the Server

Open a terminal and run:

```bash
uv run uvicorn main:app --port 8000 --reload
```

This will start the FastAPI server with auto-reload enabled. The server will be available at `http://localhost:8000`.

### 5. Start the Client Application

Open a new terminal window (keep the server running) and run:

```bash
uv run run_cli.py
```

This will launch the Textual-based CLI client to interact with your spy agents.

### 6. Access API Documentation

Once the server is running, you can access the interactive API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 🧪 Weekly Milestones

Each week builds toward the final goal:

### 🧬 Week 1: Mission Briefing

- Set up your dev environment
- Learn how to use `pyproject.toml` and `uv`
- Configure VS Code and Git

### 📡 Week 2: Agent Recruitment

- Create agent profiles using **FastAPI** and **FastCRUD**
- Save them in a database using **SQLAlchemy**

### 🤖 Week 3: Solo Ops

- Hook your agent into an LLM using **Pydantic AI**
- Chat with your agent locally using **Ollama**

### 🤝 Week 4: Team Extraction

- Enable **multi-agent conversations**
- Let agents collaborate on missions
- Deploy your app so others can try it too!

---

## 🎯 Final Deliverable

By the end of the course, you’ll have built a deployable **AI chat app** that:

- Lets users create and name their own agent
- Stores agent profiles in a database
- Enables real-time chat with AI agents
- Supports **multi-agent coordination** (optional extension)

---

## 🧭 Optional Extensions

Want to go further?

- Add a **frontend** using HTML or Streamlit
- Deploy your agent as a **public service**
- Enable **TTS** (text-to-speech) for dramatic effect
- Add **memory** so agents remember past interactions

---

## 📚 Resources

- [Astral UV Docs](https://docs.astral.sh/uv/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [FastCRUD Docs](https://github.com/benavlabs/fastcrud)
- [Pydantic AI Docs](https://docs.pydantic.dev/ai/)
- [Ollama](https://ollama.ai/)
- [SQLAlchemy ORM Guide](https://docs.sqlalchemy.org/en/20/orm/quickstart.html)

---

## 💼 Want to Show Off?

Share your project!

- Post your GitHub link in developer communities
- Deploy it online and share with friends
- Add it to your portfolio as a full-stack Python project

---

## ✅ Ready to Begin?

Let’s get started — your mission begins now.

🕵️‍♂️ *Stay sharp. Stay stealthy. And above all… don't get caught.*

Let me know how I can help! 🚀