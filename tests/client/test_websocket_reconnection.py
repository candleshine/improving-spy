"""
Test script for WebSocket reconnection functionality.

This script tests the WebSocket client's ability to reconnect and recover sessions.
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import after path setup
from src.client.websocket.client import WebSocketClient  # noqa: E402
from src.client.websocket.protocol import Message  # noqa: E402

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("websocket_test")

# Message handler for testing
def message_handler(message: Message):
    logger.info(f"Received message: {message.type}")
    if hasattr(message, "payload"):
        logger.info(f"Message payload: {message.payload}")

# Connection handlers
def on_connect():
    logger.info("Connected to WebSocket server")

def on_disconnect():
    logger.info("Disconnected from WebSocket server")

def on_error(error_msg: str):
    logger.error(f"WebSocket error: {error_msg}")

async def test_reconnection():
    """Test the WebSocket client's reconnection functionality."""
    logger.info("Starting WebSocket reconnection test")
    
    # Create a WebSocket client
    client = WebSocketClient(
        agent_id="test_agent",
        server_url="ws://localhost:8001/ws/play?scenario=last_oracle",
        on_message=message_handler,
        on_connect=on_connect,
        on_disconnect=on_disconnect,
        on_error=on_error,
        auto_reconnect=True
    )
    
    # Connect to the server
    logger.info("Connecting to WebSocket server...")
    connected = await client.connect()
    
    if not connected:
        logger.error("Failed to connect to WebSocket server")
        return
    
    # Wait for a moment
    logger.info("Connected. Waiting for 5 seconds...")
    await asyncio.sleep(5)
    
    # Simulate a disconnection
    logger.info("Simulating disconnection...")
    await client.disconnect(clear_session=False)
    
    # Wait for a moment
    logger.info("Disconnected. Waiting for 2 seconds...")
    await asyncio.sleep(2)
    
    # Reconnect with session recovery
    logger.info("Reconnecting with session recovery...")
    reconnected = await client.reconnect()
    
    if not reconnected:
        logger.error("Failed to reconnect to WebSocket server")
        return
    
    # Wait for a moment
    logger.info("Reconnected. Waiting for 5 seconds...")
    await asyncio.sleep(5)
    
    # Disconnect and clean up
    logger.info("Test complete. Disconnecting...")
    await client.disconnect(clear_session=True)
    
    logger.info("WebSocket reconnection test completed")

if __name__ == "__main__":
    asyncio.run(test_reconnection())
