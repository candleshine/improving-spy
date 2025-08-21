# 🕵️ Spy Command Console
## A Terminal-Based Agent Interface

> **"The future of espionage is in your terminal."**

A sleek, modern Textual TUI (Text User Interface) for interacting with AI-powered spy agents via your FastAPI backend.

## 🚀 Features

- 🔗 **Backend Integration**: Connects to FastAPI at `http://localhost:8000`
- 👥 **Spy Selection**: Fetches agent list from `/api/api/spies/` (corrected endpoint)
- 💬 **iMessage-Style Chat**: Outgoing (right), incoming (left), color-coded
- 🎭 **Mode**: Chat vs Debrief with mission context
- 🖼️ **Avatars**: Uses codename abbreviation (e.g., "SV", "NH")
- ⏰ **Timestamps**: Each message shows time (e.g., `14:32`)
- 🖥️ **Spy Terminal Theme**: Green-on-black monochrome UI
- 🔤 **Typing Indicators**: WebSocket-powered "…typing" animation
- 🧠 **Conversation History**: Maintains context across messages

## 📦 Requirements

- Python 3.9+
- FastAPI backend running at `http://localhost:8000`
- Dependencies:
  ```bash
  pip install -r requirements.txt
  ```

## 🧪 Quick Start

1. **Start your FastAPI backend**:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

2. **Run the Spy Console**:
   ```bash
   python spy_cli.py
   ```

3. **Begin a conversation**:
   - Use `↑`/`↓` to select a spy
   - Press `Enter` to start
   - Choose mode: **Chat** or **Debrief**
     - In **Debrief**, type the mission ID (e.g., `paris_infiltration`)
   - Type your message and press `Enter`
   - Watch for `…typing…` indicators
   - Type `:quit` to exit

## 🔄 API Integration

The frontend uses these endpoints:

| Method | Endpoint | Purpose |
|--------|--------|--------|
| `GET` | `/api/api/spies/` | Load list of available spies |
| `POST` | `/api/chat/{spy_id}` | Send message in chat mode |
| `POST` | `/api/debrief/{spy_id}/{mission_id}` | Send message in debrief mode |
| `POST` | `/api/chat/{spy_id}/conversation/{conversation_id}` | Chat with conversation history |
| `POST` | `/api/conversation` | Start a new conversation |
| `WS` | `/ws/chat/{spy_id}` | WebSocket for real-time updates |
| `WS` | `/ws/chat/{spy_id}/conversation/{conversation_id}` | WebSocket with conversation context |

## 🧩 Architecture

```
spy_textual_frontend/
│
├── spy_cli.py            # Main Textual app
├── api_client.py         # REST + WebSocket client
├── models.py             # Pydantic models matching backend
├── widgets/
│   ├── __init__.py       # Widget imports
│   ├── spy_selector.py   # List of spies with avatars
│   ├── chat_window.py    # Scrollable chat with alignment
│   ├── input_bar.py      # Message input with send action
│   └── typing_indicator.py # Displays "...typing"
│
├── requirements.txt      # Dependencies
└── README.md             # This file
```

## 📄 Mode: Chat vs Debrief

At the start of each conversation, you choose:

- **Chat Mode**: General conversation using spy's biography only
- **Debrief Mode**: Mission-specific recall using mission context

> You will be prompted to enter the **mission ID** (e.g., `paris_infiltration`) in debrief mode.

## 🌐 WebSocket: Typing Indicators

The application connects to WebSockets for real-time updates:

1. Frontend opens WebSocket: `ws://localhost:8000/ws/chat/{spy_id}` or with conversation ID
2. Backend sends various message types:
   - `{"type": "typing", "spy_id": "1"}` - Shows typing indicator
   - `{"type": "response", ...}` - Displays spy response
   - `{"type": "system", "content": "..."}` - Shows system messages
   - `{"type": "error", "content": "..."}` - Shows error messages

This creates a **responsive, human-like interaction** with the AI agents.
