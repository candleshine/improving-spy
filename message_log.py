#!/usr/bin/env python3
"""
MessageLog implementation for the Chronicle Engine frontend.
This file contains a standalone MessageLog class that can be imported into the main frontend.
"""
from textual.app import ComposeResult
from textual.containers import ScrollableContainer
from textual.widgets import Static, RichLog
import logging
import traceback
from datetime import datetime
# No need for copy module anymore

logger = logging.getLogger("spy_frontend")

# Create a special list class that can't be converted to bool
class NonBoolList(list):
    """A list subclass that can't be converted to bool by accident"""
    
    def __bool__(self):
        """Override bool conversion to raise an error"""
        logger.error("Attempted to convert message list to bool!")
        import traceback
        stack = ''.join(traceback.format_stack())
        logger.error(f"Boolean conversion stack trace: {stack}")
        # Return True instead of raising an exception to avoid breaking existing code
        # but still allow the list to be used normally
        return True

class MessageLog(Static, can_focus=False):
    """Widget to display the message log with rich formatting."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Use our special list class that can't be converted to bool
        self._messages = NonBoolList()  # Raw messages storage
        self.text_log = None           # RichLog reference
        self._composed = False         # Flag to prevent multiple widget creation
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
        if len(self._messages) > 0:
            self.update_display()
    
    def _format_message(self, msg: dict) -> str:
        """Format a message for display."""
        try:
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
            # Use our protected messages list directly
            logger.debug(f"[UI] Updating display with {len(self._messages)} messages")
            
            # Ensure we have a text log
            if self.text_log is None:
                logger.error("[UI] No text_log available for display update")
                return
                
            # Clear the log
            self.text_log.clear()
            logger.debug("[UI] Cleared RichLog content")
            
            # Format and display each message
            for i, msg in enumerate(self._messages, start=1):
                formatted = self._format_message(msg)
                if formatted:
                    logger.debug(f"[UI] Writing message {i}: {formatted[:50]}...")
                    self.text_log.write(formatted)
                    if i < len(self._messages):
                        self.text_log.write("\n")  # Newline for spacing
            
            # Refresh and scroll
            self.text_log.refresh()
            self.text_log.scroll_end(animate=False)
            logger.debug(f"[UI] Display updated with {len(self._messages)} messages")
            
        except Exception as e:
            logger.error(f"[UI] Error updating display: {e}\n{traceback.format_exc()}")
    
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
            
            # Directly append to our NonBoolList
            self._messages.append(event)
            logger.debug(f"Added message (type: {event.get('type', 'unknown')}), total messages: {len(self._messages)}")
            
            # Update the display
            self.update_display()
            
        except Exception as e:
            logger.error(f"Error adding message: {e}", exc_info=True)
            # Add error to messages
            error_msg = {
                "type": "error",
                "content": f"Error displaying message: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
            
            try:
                # Directly append to our NonBoolList
                self._messages.append(error_msg)
                self.update_display()
            except Exception as inner_e:
                logger.critical(f"Critical error handling message error: {inner_e}", exc_info=True)
    
    @property
    def messages_list(self):
        """For backwards compatibility with code that expects messages_list property"""
        return self._messages
    
    @messages_list.setter
    def messages_list(self, value):
        """For backwards compatibility with code that expects messages_list property"""
        if value is None:
            self._messages.clear()
        elif isinstance(value, list):
            # Create a new NonBoolList with the values
            self._messages.clear()
            self._messages.extend(value)
        else:
            logger.warning(f"Attempted to set messages_list to non-list: {type(value).__name__}")
            self._messages.clear()
    
    def clear_messages(self) -> None:
        """Clear all messages from the log."""
        # Clear our NonBoolList
        self._messages.clear()
        if self.text_log:
            self.text_log.clear()
            logger.debug("Cleared all messages")
            
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
