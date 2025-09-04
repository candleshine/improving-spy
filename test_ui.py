#!/usr/bin/env python3
"""
Test script for the Textual UI to verify text visibility in the RichLog widget.
"""
import sys
import logging
from textual.app import App
from textual.widgets import RichLog
from textual.containers import ScrollableContainer
from textual.reactive import reactive

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("ui_test_debug.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("ui_test")

class TestMessageLog(App):
    """Simple test app for message visibility."""
    
    TITLE = "Message Visibility Test"
    CSS = """
    RichLog {
        background: black;
        color: lime;
        height: 100%;
        width: 100%;
    }
    """
    
    messages = reactive([])
    
    def __init__(self):
        super().__init__()
        self._text_log = None
        self._formatted_messages = []
    
    def compose(self):
        """Create the UI layout."""
        logger.debug("Composing UI")
        with ScrollableContainer():
            yield RichLog(id="message_log", highlight=False, markup=True)
        logger.debug("UI composition complete")
    
    def on_mount(self):
        """Initialize the app after mounting."""
        logger.debug("App mounted")
        self._text_log = self.query_one(RichLog)
        logger.debug(f"Found RichLog: {self._text_log!r}")
        
        # Add test messages
        self.add_test_messages()
    
    def add_test_messages(self):
        """Add test messages to verify visibility."""
        logger.debug("Adding test messages")
        
        # Test different message types
        test_messages = [
            {"type": "system", "content": "SYSTEM MESSAGE: This is a test system message"},
            {"type": "user", "content": "USER MESSAGE: This is a test user message"},
            {"type": "narrative", "content": "NARRATIVE: This is a test narrative message"},
            {"type": "choice", "options": ["Option 1", "Option 2", "Option 3"]},
            {"type": "error", "content": "ERROR: This is a test error message"}
        ]
        
        # Add messages to the log
        for msg in test_messages:
            self.messages.append(msg)
            formatted = self._format_message(msg)
            if formatted:
                logger.debug(f"Writing message: {formatted[:30]}...")
                self._text_log.write(formatted)
                self._text_log.write("\n\n")  # Double newline for spacing
        
        # Force refresh and scroll to end
        self._text_log.refresh()
        self._text_log.scroll_end(animate=False)
        logger.debug("Test messages added and displayed")
    
    def _format_message(self, msg):
        """Format a message for display."""
        if not isinstance(msg, dict):
            return str(msg)
        
        msg_type = msg.get("type", "unknown")
        content = msg.get("content", msg.get("text", ""))
        
        # Simple formatting for maximum visibility
        if msg_type == 'system':
            return f"SYSTEM: {content}\n\n"
        elif msg_type == 'user':
            return f"YOU: {content}\n\n"
        elif msg_type == 'narrative':
            return f"NARRATIVE: {content}\n\n"
        elif msg_type == 'choice':
            options = msg.get('options', [])
            result = "CHOICES:\n"
            for i, option in enumerate(options, 1):
                result += f"{i}. {option}\n"
            return result + "\n"
        elif msg_type == 'error':
            return f"ERROR: {content}\n\n"
        else:
            return f"{msg_type.upper()}: {content}\n\n"

if __name__ == "__main__":
    app = TestMessageLog()
    app.run()
