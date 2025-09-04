#!/usr/bin/env python3
"""
Minimal test for MessageLog class to identify the 'bool' object has no attribute 'append' error
"""
import logging
import sys
from textual.app import App, ComposeResult
from textual.widgets import Header

# Import our fixed MessageLog implementation
from message_log import MessageLog

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("minimal_test")

# We don't need the debug bool wrapper since it's already in message_log.py

class MinimalMessageLog(MessageLog):
    """A minimal wrapper around our fixed MessageLog implementation"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        logger.debug("Initialized MinimalMessageLog using fixed MessageLog implementation")

class MinimalApp(App):
    """Minimal app to test MessageLog"""
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield MinimalMessageLog()
    
    def on_mount(self):
        """Test adding messages"""
        logger.debug("App mounted, testing message log")
        message_log = self.query_one(MinimalMessageLog)
        
        # Try adding a message
        try:
            message_log.add_message({"type": "test", "content": "Test message"})
            logger.debug("Successfully added message")
            
            # Add a second message to verify it works
            message_log.add_message({"type": "system", "content": "System message test"})
            logger.debug("Successfully added second message")
        except Exception as e:
            logger.error(f"Error in on_mount: {e}")

if __name__ == "__main__":
    app = MinimalApp()
    try:
        app.run()
    except Exception as e:
        logger.error(f"Error running app: {e}")
        import traceback
        traceback.print_exc()
