from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.backend.api.routes import router
from src.backend.core.database import init_db

app = FastAPI(
    title="🕵️ Spy Agent Chat API", 
    version="0.4.0",
    description="""
    # Spy Agent Chat API with WebSockets
    
    This API allows you to chat with spy agents in real-time using WebSockets.
    
    ## WebSocket Endpoints
    
    * `/ws/chat/{spy_id}` - Chat with a spy agent in real-time
    * `/ws/chat/{spy_id}/conversation/{conversation_id}` - Chat with a spy agent using conversation history
    
    ## WebSocket Usage
    
    Connect to a WebSocket endpoint and send JSON messages with the following format:
    
    ```json
    {
        "message": "Your message to the spy agent"
    }
    ```
    
    You will receive JSON responses with the following format:
    
    ```json
    {
        "type": "response",
        "spy_id": "spy-id",
        "spy_name": "Spy Name",
        "message": "Your message",
        "response": "Spy agent's response"
    }
    ```
    
    System messages have the following format:
    
    ```json
    {
        "type": "system",
        "content": "System message"
    }
    ```
    
    Error messages have the following format:
    
    ```json
    {
        "type": "error",
        "content": "Error message"
    }
    ```
    """
)

# Configure CORS for WebSocket support
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Initialize database
init_db()

# Include API routes
app.include_router(router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Spy Agent Chat API! Go to /docs for interactive API and WebSocket documentation."}