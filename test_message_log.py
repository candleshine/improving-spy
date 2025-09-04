#!/usr/bin/env python3
"""
Test script for the fixed MessageLog class
"""
import logging
import sys
from datetime import datetime
from textual.app import App, ComposeResult
from textual.containers import Container, ScrollableContainer
from textual.widgets import Header, Input, Static, RichLog

# Configure logging to stdout for immediate feedback
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("test_message_log")
logger.info("=== Starting MessageLog Test ===")

class MessageLog(Static, can_focus=False):
    """Widget to display the message log with rich formatting."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Simple non-reactive storage - avoid reactive properties that can become bool
        self.messages_list = []  # Raw messages
        self.text_log = None     # RichLog reference
        self._composed = False   # Flag to prevent multiple widget creation
        logger.debug("[UI] MessageLog.__init__: initialized with empty messages list")
    
    def compose(self) -> ComposeResult:
        """Create child widgets."""
        logger.debug("[UI] MessageLog.compose called")
        
        # Only create the RichLog once
        if not self._composed:
            logger.debug("[UI] Creating RichLog widget in MessageLog.compose")
            with ScrollableContainer(id="log-container"):
                rich_log = RichLog(
                    id="log-content",
                    highlight=True,
                    markup=True,
                    classes="visible-text"
                )
                yield rich_log
                self.text_log = rich_log
                logger.debug(f"[UI] Created RichLog widget: {self.text_log!r}")
            self._composed = True
    
    def on_mount(self) -> None:
        """Called when the widget is mounted."""
        logger.debug("[UI] MessageLog mounted")
        # Update display if we have messages
        if self.messages_list:
            self.update_display()
    
    def _format_message(self, msg: dict) -> str:
        """Format a message for display."""
        try:
            if not isinstance(msg, dict):
                return str(msg)
                
            msg_type = msg.get("type", "unknown")
            content = str(msg.get("content", msg.get("text", "")))  # Fallback to text field
            
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
        except Exception as e:
            logger.error(f"[UI] Error formatting message: {e}")
            return f"ERROR: Could not format message: {str(e)}\n\n"
    
    def update_display(self) -> None:
        """Update the message display with current messages."""
        try:
            logger.debug(f"[UI] Updating display with {len(self.messages_list)} messages")
            
            # Ensure we have a text log
            if self.text_log is None:
                logger.error("[UI] No text_log available for display update")
                return
                
            # Clear the log
            self.text_log.clear()
            logger.debug("[UI] Cleared RichLog content")
            
            # Format and display each message
            for i, msg in enumerate(self.messages_list, start=1):
                formatted = self._format_message(msg)
                if formatted:
                    logger.debug(f"[UI] Writing message {i}: {formatted[:50]}...")
                    self.text_log.write(formatted)
                    if i < len(self.messages_list):
                        self.text_log.write("\n\n")  # Double newline for spacing
            
            # Refresh and scroll
            self.text_log.refresh()
            self.text_log.scroll_end(animate=False)
            logger.debug(f"[UI] Display updated with {len(self.messages_list)} messages")
            
        except Exception as e:
            logger.error(f"[UI] Error updating display: {e}")
    
    def add_message(self, event: dict) -> None:
        """Add a message to the log."""
        try:
            if not isinstance(event, dict):
                logger.warning(f"Expected dict, got {type(event).__name__}")
                event = {"type": "error", "content": f"Invalid message format: {event}"}
            
            # Ensure we have a valid message type
            if "type" not in event:
                event["type"] = "system"
                
            # Ensure we have content
            if "content" not in event:
                if "text" in event:
                    event["content"] = event["text"]
                else:
                    # Create content from other fields
                    content = ""
                    for field in ["message", "description", "output"]:
                        if field in event and event[field]:
                            content = str(event[field])
                            break
                    
                    if not content:
                        # Create content from all non-metadata fields
                        content = ", ".join(
                            f"{k}: {v}" for k, v in event.items() 
                            if k not in ["type", "timestamp"] and not k.startswith("_")
                        )
                    
                    event["content"] = content or "[No content]"
                
            # Ensure we have a timestamp
            if "timestamp" not in event:
                event["timestamp"] = datetime.now().isoformat()
            
            # Add to messages list
            self.messages_list.append(event)
            
            # Update the display
            self.update_display()
            
            msg_type = event.get("type", "unknown")
            content_preview = str(event.get("content", ""))[:100]
            logger.debug(f"Added message (type: {msg_type}): {content_preview}...")
            
        except Exception as e:
            logger.error(f"Error adding message: {e}")
            # Add error to messages
            error_msg = {
                "type": "error",
                "content": f"Error displaying message: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
            self.messages_list.append(error_msg)
            self.update_display()
    
    def clear_messages(self) -> None:
        """Clear all messages from the log."""
        self.messages_list = []
        if self.text_log:
            self.text_log.clear()
            
    def render(self) -> str:
        """Render the message log content."""
        return ""  # The actual content is in the RichLog widget
    
    DEFAULT_CSS = """
    MessageLog {
        width: 100%;
        height: 100%;
        overflow: hidden;
    }
    RichLog {
        background: #000000; /* Black background instead of transparent */
        padding: 1;
        color: #00ff00; /* Explicitly set text color to green */
        content-align: left top;
    }
    .visible-text {
        color: #00ff00 !important;
        background: #000000 !important;
        text-opacity: 1.0 !important;
    }
    """

class TestApp(App):
    """Test application for MessageLog."""
    TITLE = "MessageLog Test App"
    
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
        background: #000000;
        color: #00ff00;
    }
    #log-content {
        color: #00ff00 !important;
        text-opacity: 1.0 !important;
        background: #000000 !important;
    }
    #input-container {
        width: 100%;
        height: auto;
        padding: 1 2;
    }
    Input {
        width: 100%;
        height: 3;
    }
    """
    
    def __init__(self):
        super().__init__()
        self.message_log = None
        
    def compose(self) -> ComposeResult:
        """Compose the test UI."""
        yield Header()
        
        with Container(id="app-grid"):
            with Container(id="main-content"):
                # Message log container
                yield MessageLog()
                # Input container
                with Container(id="input-container"):
                    yield Input(placeholder="Type your test message and press Enter...", id="user-input")
    
    async def on_mount(self) -> None:
        """Initialize the application when mounted."""
        self.message_log = self.query_one(MessageLog)
        
        # Add test messages
        self.message_log.add_message({
            "type": "system",
            "text": "MessageLog Test Application Started"
        })
        
        self.message_log.add_message({
            "type": "narrative",
            "text": "This is a test narrative message to verify text visibility in the UI."
        })
        
        self.message_log.add_message({
            "type": "choice",
            "options": ["Option 1: Test choice", "Option 2: Another test choice"]
        })
        
        # Add a message with a bool value to test error handling
        try:
            self.message_log.add_message({
                "type": "test",
                "content": True  # This should be handled gracefully
            })
            logger.info("Successfully handled boolean content")
        except Exception as e:
            logger.error(f"Failed to handle boolean content: {e}")
    
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        user_input = event.input.value.strip()
        if not user_input:
            return
            
        # Add user message
        self.message_log.add_message({
            "type": "user",
            "content": user_input
        })
        
        # Echo back
        self.message_log.add_message({
            "type": "system",
            "content": f"You entered: {user_input}"
        })
        
        # Clear input
        event.input.value = ""

if __name__ == "__main__":
    app = TestApp()
    app.run()
