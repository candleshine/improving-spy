# frontend.py
"""
Chronicle Engine - Textual Frontend
A terminal-based AI RPG client using Textual and WebSockets.
Handles all structured events from the Pydantic AI backend.
"""
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Header, Input
import json
import logging
import asyncio
import websockets
from datetime import datetime
from pathlib import Path

# Import the MessageLog class from message_log.py
from message_log import MessageLog

# Debug wrapper to catch any bool conversions of list objects
original_bool = bool
def debug_bool(obj):
    """Debug wrapper for bool() to catch when it's called on list-like objects"""
    if isinstance(obj, list) or hasattr(obj, 'append'):
        logger.warning(f"WARNING: bool() called on a list-like object: {type(obj)}, id: {id(obj)}")
        import traceback
        stack = ''.join(traceback.format_stack())
        logger.warning(f"Boolean conversion stack trace: {stack}")
    return original_bool(obj)

# Replace the built-in bool function with our debug version
bool = debug_bool

# Ensure log directory exists
log_dir = Path(".spy_console")
log_dir.mkdir(exist_ok=True)

# Configure logging with both file and console output
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_dir / "spy_frontend.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create a special debug file handler for our MessageLog debugging
debug_file = log_dir / "debug_messagelog.log"
debug_handler = logging.FileHandler(debug_file, mode='w')  # 'w' to start fresh each run
debug_handler.setLevel(logging.DEBUG)
debug_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# Configure main logging
logger.addHandler(debug_handler)
logger.info("=== Starting Chronicle Engine Frontend ===")

# Create a direct file for debugging without any buffering
with open(debug_file, 'w') as f:
    f.write(f"Debug log started at {datetime.now().isoformat()}\n")


class ChronicleApp(App):
    """Main Textual app for the Chronicle Engine."""
    TITLE = "Chronicle Engine - AI RPG"
    SUB_TITLE = "A text-based RPG powered by AI"
    
    CSS = """
    Screen {
        layout: vertical;
        overflow: hidden;
        padding: 0;
        margin: 0;
    }
    Header {
        height: 1;
        padding: 0 1;
    }
    #log-container {
        width: 100%;
        height: 1fr;
        padding: 0 1;
        overflow: hidden;
        border: round #00aa00;
        background: #000000; /* Black background for maximum contrast */
        color: #00ff00; /* Bright green text */
    }
    
    /* Force text visibility in RichLog */
    #log-content {
        color: #00ff00 !important;
        text-opacity: 1.0 !important;
        background: #000000 !important; /* Black background for maximum contrast */
    }
    #input-container {
        width: 100%;
        height: auto;
        padding: 1 2;
        background: $panel;
        border-top: solid $accent;
    }
    Input {
        width: 100%;
        height: 3;
        background: $surface;
        border: tall $accent;
        color: $text;
    }
    Input:focus {
        border: tall $accent-lighten-1;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("d", "toggle_developer", "Toggle Dev Mode (console log)"),
        ("x", "toggle_debug", "Toggle Debug Mode (no WebSocket)"),
    ]

    def __init__(self):
        super().__init__()
        self.websocket = None
        self.session_id = f"session_{hash(self):x}"
        self.scenario = "shadow_signal"
        self.developer_mode = False
        self.debug_mode = True  # Set to True to run without WebSocket connection
        self._composed = False
        logger.info(f"Initialized ChronicleApp with session_id: {self.session_id}")
        logger.info(f"Debug mode is {'ENABLED' if self.debug_mode else 'DISABLED'}")
        print(f"[DEBUG] Debug mode is {'ENABLED' if self.debug_mode else 'DISABLED'}")
        
        # Add initial welcome message
        self.initial_messages = [
            {"type": "system", "text": "Welcome to Chronicle Engine - Spy Console", "timestamp": datetime.now().isoformat()},
        ]

    def compose(self) -> ComposeResult:
        """Compose the main UI."""
        # Create the main layout
        yield Header()

        with Container(id="app-grid"):
            with Container(id="main-content"):
                # Message log container
                with Container(id="log-container"):
                    yield MessageLog()
                # Input container
                with Container(id="input-container"):
                    yield Input(placeholder="Type your action and press Enter...", id="user-input")

    async def on_mount(self) -> None:
        """Initialize the application when mounted."""
        # Add initial messages to the log
        message_log = self.query_one(MessageLog)
        for msg in self.initial_messages:
            message_log.add_message(msg)
                
        # Add system ready message
        message_log.add_message({
            "type": "system",
            "text": "System initialized and ready",
            "timestamp": datetime.now().isoformat()
        })
        
        # Skip WebSocket connection in debug mode
        if self.debug_mode:
            logger.info("Running in debug mode - skipping WebSocket connection")
            print("[DEBUG] Running in debug mode - skipping WebSocket connection")
            message_log.add_message({
                "type": "system",
                "text": "Running in debug mode - no WebSocket connection",
                "timestamp": datetime.now().isoformat()
            })
            # Add some test messages to verify UI display
            message_log.add_message({
                "type": "narrative",
                "text": "This is a test narrative message to verify text visibility in the UI.",
                "timestamp": datetime.now().isoformat()
            })
            message_log.add_message({
                "type": "choice",
                "options": ["Option 1: Test choice", "Option 2: Another test choice"],
                "timestamp": datetime.now().isoformat()
            })
            return
        
        # Connect to WebSocket if not in debug mode
        ws_url = f"ws://localhost:8000/ws/play?scenario={self.scenario}"
        logger.info(f"Attempting to connect to WebSocket: {ws_url}")
        
        try:
            # Connect with a reasonable timeout
            self.websocket = await asyncio.wait_for(
                websockets.connect(ws_url, ping_interval=20, ping_timeout=20),
                timeout=10.0
            )
            logger.info("WebSocket connection established successfully")
            
            # Start the message receiver
            asyncio.create_task(self.receive_messages())
            logger.debug("Started WebSocket message receiver task")
            
            # Send a test message to verify the connection
            try:
                test_msg = {"type": "ping", "text": "Frontend connected", "timestamp": datetime.now().isoformat()}
                await self.websocket.send(json.dumps(test_msg))
                logger.debug("Sent test ping message to WebSocket")
            except Exception as e:
                logger.error(f"Error sending test message: {e}", exc_info=True)
            
        except asyncio.TimeoutError:
            error_msg = "Connection timed out. Is the backend server running?"
            logger.error(error_msg)
            self.query_one(MessageLog).add_message({"type": "error", "text": error_msg})
            
        except websockets.exceptions.InvalidURI as e:
            error_msg = f"Invalid WebSocket URL: {ws_url} - {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.query_one(MessageLog).add_message({"type": "error", "text": error_msg})
            
        except ConnectionRefusedError:
            error_msg = "Connection refused. Is the backend server running on port 8000?"
            logger.error(error_msg)
            self.query_one(MessageLog).add_message({"type": "error", "text": error_msg})
            
        except Exception as e:
            error_msg = f"Failed to connect: {str(e)}. Is the backend running?"
            logger.error(error_msg, exc_info=True)
            self.query_one(MessageLog).add_message({"type": "error", "text": error_msg})

    async def receive_messages(self):
        """Listen for incoming WebSocket messages."""
        if not self.websocket or getattr(self.websocket, 'closed', True):
            logger.error("WebSocket connection not established")
            self.query_one(MessageLog).add_message({
                "type": "error",
                "content": "WebSocket connection not properly initialized. Please restart the application."
            })
            return
            
        logger.info("Starting WebSocket message receiver")
        
        try:
            while True:
                try:
                    logger.debug("Awaiting WebSocket messages...")
                    message = await self.websocket.recv()
                    
                    if not message:
                        logger.warning("Received empty message from WebSocket")
                        continue
                        
                    # Log the message (truncate if too long)
                    msg_str = str(message)
                    logger.debug(f"Received WebSocket message: {msg_str[:200]}{'...' if len(msg_str) > 200 else ''}")
                    
                    try:
                        # Parse the JSON message
                        event = json.loads(message)
                        
                        # Log the parsed event (safely handle non-dict events)
                        if isinstance(event, dict):
                            msg_type = event.get('type', 'unknown')
                            logger.debug(f"Processing WebSocket message of type: {msg_type}")
                            
                            # Special handling for error messages
                            if msg_type == 'error':
                                error_content = event.get('content', 'Unknown error')
                                logger.error(f"Server error: {error_content}")
                        
                        # Add the message to the UI
                        message_log = self.query_one(MessageLog)
                        if message_log:
                            message_log.add_message(event)
                        else:
                            logger.error("MessageLog widget not found in the UI")
                        
                    except json.JSONDecodeError as je:
                        error_msg = f"Invalid message format: {str(je)}"
                        logger.error(f"{error_msg}\nMessage: {message[:200]}...")
                        self.query_one(MessageLog).add_message({
                            "type": "error",
                            "content": error_msg
                        })
                        
                except websockets.exceptions.ConnectionClosed as ce:
                    logger.info(f"WebSocket connection closed: {ce}")
                    self.query_one(MessageLog).add_message({
                        "type": "system",
                        "content": "Disconnected from server. Please refresh to reconnect."
                    })
                    break
                    
                except asyncio.CancelledError:
                    logger.info("WebSocket listener was cancelled")
                    break
                    
                except Exception as e:
                    error_msg = f"Error processing message: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    self.query_one(MessageLog).add_message({
                        "type": "error",
                        "content": error_msg
                    })
                    # Add a small delay to prevent tight error loops
                    await asyncio.sleep(1)
                    
            logger.info("WebSocket message receiver stopped")
            
        except Exception as e:
            logger.error(f"Fatal error in WebSocket receiver: {e}", exc_info=True)
            self.query_one(MessageLog).add_message({
                "type": "error",
                "content": f"Connection error: {str(e)}"
            })

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        user_input = event.input.value.strip()
        if not user_input:
            return
            
        # Add user message to log
        message_log = self.query_one(MessageLog)
        message_log.add_message({
            "type": "user",
            "text": user_input,
            "timestamp": datetime.now().isoformat()
        })
        
        # Clear input
        event.input.value = ""
        
        # Skip WebSocket processing in debug mode
        if self.debug_mode:
            logger.info(f"[DEBUG] User input: {user_input}")
            # Echo back in debug mode
            message_log.add_message({
                "type": "system",
                "text": f"Debug echo: {user_input}",
                "timestamp": datetime.now().isoformat()
            })
            return
        
        # Process with WebSocket if connected
        try:
            if hasattr(self, 'websocket') and self.websocket:
                # Prepare message
                message = {
                    "type": "user_input",
                    "text": user_input,
                    "content": user_input,
                    "session_id": self.session_id,
                    "timestamp": datetime.now().isoformat()
                }
                logger.debug(f"Sending message to WebSocket: {message}")
                
                # Send message
                await self.websocket.send(json.dumps(message))
                logger.debug("Successfully sent message to WebSocket")
            else:
                error_msg = "WebSocket not connected. Try restarting the application."
                logger.error(error_msg)
                message_log.add_message({
                    "type": "error",
                    "text": error_msg,
                    "timestamp": datetime.now().isoformat()
                })
        except websockets.exceptions.ConnectionClosed as ce:
            error_msg = f"WebSocket connection closed while sending: {ce}"
            logger.error(error_msg)
            message_log.add_message({
                "type": "error",
                "text": "Connection lost. Please restart the application.",
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            error_msg = f"Error sending message: {str(e)}"
            logger.error(error_msg, exc_info=True)
            message_log.add_message({
                "type": "error",
                "text": f"Failed to send message: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })
        
        logger.debug("Input field cleared after submission")

    def action_toggle_developer(self) -> None:
        """Toggle developer mode (prints raw JSON to console)."""
        self.developer_mode = not self.developer_mode
        status = "enabled" if self.developer_mode else "disabled"
        logger.info(f"Developer mode {status}")
        self.query_one(MessageLog).add_message({
            "type": "system",
            "text": f"Developer mode {status}",
            "timestamp": datetime.now().isoformat()
        })
        
    def action_toggle_debug(self) -> None:
        """Toggle debug mode (runs without WebSocket connection)."""
        self.debug_mode = not self.debug_mode
        status = "enabled" if self.debug_mode else "disabled"
        logger.info(f"Debug mode {status}")
        
        message_log = self.query_one(MessageLog)
        message_log.add_message({
            "type": "system",
            "text": f"Debug mode {status}",
            "timestamp": datetime.now().isoformat()
        })
        
        # If turning debug mode off, try to connect to WebSocket
        # If turning debug mode on, disconnect from WebSocket
        if not self.debug_mode and not self.websocket:
            message_log.add_message({
                "type": "system",
                "text": "Attempting to connect to WebSocket...",
                "timestamp": datetime.now().isoformat()
            })
            # Schedule connection attempt
            asyncio.create_task(self._connect_websocket())
        elif self.debug_mode and self.websocket:
            message_log.add_message({
                "type": "system",
                "text": "Disconnecting from WebSocket...",
                "timestamp": datetime.now().isoformat()
            })
            # Schedule disconnection
            asyncio.create_task(self._disconnect_websocket())

    async def _connect_websocket(self) -> None:
        """Helper method to connect to WebSocket."""
        message_log = self.query_one(MessageLog)
        ws_url = f"ws://localhost:8000/ws/play?scenario={self.scenario}"
        logger.info(f"Attempting to connect to WebSocket: {ws_url}")
        
        try:
            # Connect with a reasonable timeout
            self.websocket = await asyncio.wait_for(
                websockets.connect(ws_url, ping_interval=20, ping_timeout=20),
                timeout=10.0
            )
            logger.info("WebSocket connection established successfully")
            message_log.add_message({
                "type": "system",
                "text": "Connected to game server",
                "timestamp": datetime.now().isoformat()
            })
            
            # Start the message receiver
            asyncio.create_task(self.receive_messages())
            logger.debug("Started WebSocket message receiver task")
            
        except (asyncio.TimeoutError, ConnectionRefusedError) as e:
            error_msg = f"Connection failed: {str(e)}. Is the backend server running?"
            logger.error(error_msg)
            message_log.add_message({"type": "error", "text": error_msg})
            # Re-enable debug mode since connection failed
            self.debug_mode = True
            message_log.add_message({
                "type": "system",
                "text": "Debug mode re-enabled due to connection failure",
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            error_msg = f"Unexpected error connecting: {str(e)}"
            logger.error(error_msg, exc_info=True)
            message_log.add_message({"type": "error", "text": error_msg})
            # Re-enable debug mode since connection failed
            self.debug_mode = True
            message_log.add_message({
                "type": "system",
                "text": "Debug mode re-enabled due to connection failure",
                "timestamp": datetime.now().isoformat()
            })
    
    async def _disconnect_websocket(self) -> None:
        """Helper method to disconnect from WebSocket."""
        if not self.websocket:
            return
            
        try:
            await self.websocket.close()
            logger.info("WebSocket connection closed")
            self.websocket = None
            self.query_one(MessageLog).add_message({
                "type": "system",
                "text": "Disconnected from game server",
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Error closing WebSocket: {e}", exc_info=True)
            self.websocket = None


if __name__ == "__main__":
    app = ChronicleApp()
    app.run()