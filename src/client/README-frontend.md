Excellent — thank you for the detailed feedback! Based on your answers and the provided `week3_slides.md` and `week3_lesson_plan.md`, I’ve refined the vision for your **Textual-based Spy Command Console**.

Below is the **finalized `README.md`** that reflects your exact requirements:

- ✅ Connects to backend on `http://localhost:8000`
- ✅ Uses `/api/spies` to list agents
- ✅ iMessage-style chat: left-aligned (spy), right-aligned (user), with colors
- ✅ Avatars using codename abbreviations (e.g., "SV" for Shadow Viper)
- ✅ Timestamps on every message
- ✅ Spy terminal aesthetic (green-on-black)
- ✅ Mode toggle: **Chat** vs **Debrief** (user types mission ID)
- ✅ WebSocket support for “...typing” indicators
- ✅ Natural language input (no slash commands)
- ✅ Conversation starts with mission mode selection

This README is ready for your team or students and sets a clear, professional tone for the project.

---

## 📄 `README.md` – Spy Command Console (Textual UI)

```markdown
# 🕵️ Spy Command Console  
## A Terminal-Based Agent Interface

> **"The future of espionage is in your terminal."**

A sleek, modern Textual TUI (Text User Interface) for interacting with AI-powered spy agents via your FastAPI backend.

This app lets you:
- Select from active agents
- Chat in-character using their biography and memory
- Switch between **casual chat** and **mission debrief** modes
- See real-time typing indicators via WebSocket
- View messages with avatars, timestamps, and alignment (like iMessage)

All from your terminal — no browser required.

---

## 🚀 Features

| Feature | Description |
|-------|-------------|
| 🔗 Backend Integration | Connects to FastAPI at `http://localhost:8000` |
| 👥 Spy Selection | Fetches agent list from `GET /api/spies` |
| 💬 iMessage-Style Chat | Outgoing (right), incoming (left), color-coded |
| 🎭 Mode: Chat vs Debrief | Toggle context: general chat or mission-specific recall |
| 🖼️ Avatars | Uses **codename abbreviation** (e.g., "SV", "NH") |
| ⏰ Timestamps | Each message shows time (e.g., `14:32`) |
| 🖥️ Spy Terminal Theme | Green-on-black monochrome UI |
| 🔤 Typing Indicators | WebSocket-powered "…typing" animation |
| 🗣️ Natural Input | No slash commands — just type like normal |
| 🧠 Contextual Memory | Uses conversation history and mission context |

---

## 🛠️ Tech Stack

- **Frontend**: [Textual](https://textual.textualize.io/) (Python TUI framework)
- **Backend**: FastAPI + Ollama + PydanticAI
- **Communication**: 
  - REST: `GET /api/spies`, `POST /api/chat`, etc.
  - WebSocket: `ws://localhost:8000/ws/chat/{conversation_id}` for typing events
- **LLM**: Runs locally via Ollama (e.g., `llama2`)
- **No browser needed** — runs in your terminal!

---

## 📦 Requirements

- Python 3.13 (as specified in .python-version)
- FastAPI backend running at `http://localhost:8000`
- Ollama with a model installed (`ollama pull llama2`)
- UV package manager (for dependency management and script execution)
- Dependencies:
  ```bash
  uv add textual httpx websockets
  ```

---

## 🧪 Quick Start

1. **Start your FastAPI backend**:
   ```bash
   # Using uvicorn directly
   uvicorn main:app --reload --port 8000
   
   # OR using UV (recommended)
   uv run -m uvicorn main:app --reload --port 8000
   ```

2. **Run the Spy Console**:
   ```bash
   # Using Python directly
   python spy_cli.py
   
   # OR using UV (recommended)
   uv run spy_cli.py
   ```

3. **Begin a conversation**:
   - Use `↑`/`↓` to select a spy
   - Press `Enter` to start
   - Choose mode: **Chat** or **Debrief**
     - In **Debrief**, type the mission ID (e.g., `paris_infiltration`)
   - Type your message and press `Enter`
   - Watch for `…typing` indicators
   - Type `:quit` to exit

---

## 🖼️ UI Layout Example

```
┌── SPY COMMAND CONSOLE ────────────────────────────┐
│ 🔍 SELECT AGENT                                  │
│                                                  │
│ ➔ [SV] Alex Rousseau                             │
│   [NH] Jordan Kane                               │
│   [GO] Mei Lin Zhao                              │
│                                                  │
│ MODE: [ Chat ● | Debrief ○ ]                     │
└──────────────────────────────────────────────────┘
┌── CHAT WITH ALEX ROUSSEAU ───────────────────────┐
│ SV  [14:30]  I don’t talk about missions. Not    │
│             unless the sky’s clear.              │
│                                                  │
│                                        Me: Hey   │
│                                       [14:32]    │
│                                                  │
│ …typing…                                         │
└──────────────────────────────────────────────────┘
│ Input: [What’s the status on Paris?]             │
```

> - **Left-aligned (green)**: Spy responses (with avatar + timestamp)  
> - **Right-aligned (white)**: Your messages  
> - **Avatars**: Codename abbreviations (e.g., `SV`)  
> - **Typing**: `…typing…` appears when spy is generating a response

---

## 🔄 API Integration

The frontend uses these endpoints:

| Method | Endpoint | Purpose |
|--------|--------|--------|
| `GET` | `/api/spies` | Load list of available spies |
| `POST` | `/api/chat/{spy_id}` | Send message in chat mode |
| `POST` | `/api/debrief/{spy_id}/{mission_id}` | Send message in debrief mode |
| `POST` | `/api/conversation` | Start a new conversation |
| `WS` | `/ws/chat/{conversation_id}` | Receive typing events |

> In **debrief mode**, you type the mission ID when prompted.  
> Example: `paris_infiltration`

---

## 🧩 Architecture

```
spy_textual_frontend/
│
├── spy_cli.py            # Main Textual app
├── api_client.py         # REST + WebSocket client
├── widgets/
│   ├── SpySelector.py    # List of spies with avatars
│   ├── ChatWindow.py     # Scrollable chat with alignment
│   ├── InputBar.py       # Message input with send action
│   └── TypingIndicator.py # Displays "...typing"
│
├── models.py             # Pydantic models matching backend
│
└── README.md
```

---

## 📄 Mode: Chat vs Debrief

At the start of each conversation, you choose:

- **Chat Mode**: General conversation using spy’s biography only
- **Debrief Mode**: Mission-specific recall using `missions/{mission_id}.txt` context

> You will be prompted to enter the **mission ID** (e.g., `paris_infiltration`) in debrief mode.

---

## 🖥️ Design: Spy Terminal Aesthetic

- **Background**: Black
- **Text**: Green (`#00ff00` or ANSI bright green)
- **User Messages**: White on dark gray
- **Avatars**: White in a green box
- **Input Bar**: Green border, blinking cursor
- **Fonts**: Monospace (Consolas, JetBrains Mono, or terminal default)

> Inspired by 1980s spy terminals — functional, secure, and immersive.

---

## 🌐 WebSocket: Typing Indicators

When you send a message:
1. Frontend opens WebSocket: `ws://localhost:8000/ws/chat/{conv_id}`
2. Backend sends `{"event": "typing", "spy_id": "1"}` when LLM starts generating
3. Frontend shows `…typing…` in the chat window
4. When response arrives, typing indicator disappears

This creates a **responsive, human-like interaction** — even though it’s AI.

---

## 🧠 Why This Matters

This isn’t just a chat app. It’s a **command console for autonomous agents**.

You’re building:
- A **real-time interface** for AI operatives
- A **context-aware system** that respects identity and memory
- A **foundation** for multi-agent ops (Week 4+)

---

## 📢 Next Steps

- I’ll provide the full Python implementation (`spy_cli.py`, `api_client.py`, etc.)
- You’ll share the **OpenAPI spec** so we can auto-generate models
- We’ll implement WebSocket typing support in both frontend and backend
- Add conversation persistence and history viewer

## 🛠️ Using UV for Development

This project uses [UV](https://github.com/astral-sh/uv), a fast Python package installer and resolver. Here's how to use it:

### Installation

```bash
# Install UV
pip install uv
```

### Package Management

```bash
# Install dependencies
uv pip install -r requirements.txt

# Add a package
uv add package_name

# Remove a package
uv remove package_name
```

### Running Scripts

```bash
# Run a Python script with UV
uv run script.py

# Run a module
uv run -m module_name

# Run the FastAPI server
uv run -m uvicorn main:app --reload --port 8000
```

Using UV provides faster dependency resolution and installation compared to standard pip, and ensures consistent environments across development machines.

---

> **Agent Status**: ONLINE  
> **Connection**: SECURE  
> **Mission**: ACTIVE  
Welcome to the future of solo ops. 🕵️‍♂️💻
```

