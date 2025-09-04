#!/usr/bin/env python
"""
Debug test script to identify the 'bool' object has no attribute 'append' error.
"""
import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path
from textual.app import App
from textual.widgets import Static, RichLog, Button
from textual.reactive import reactive
from textual.containers import ScrollableContainer, Container

# Set up logging with file output for better debugging
log_dir = Path(".spy_console")
log_dir.mkdir(exist_ok=True)
debug_file = log_dir / "debug_test.log"

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(debug_file, mode='w')
    ]
)
logger = logging.getLogger("debug_test")

# Direct debug function for critical debugging
def debug_write(msg):
    try:
        with open(debug_file, 'a') as f:
            f.write(f"{datetime.now().isoformat()} - {msg}\n")
            f.flush()
    except Exception as e:
        print(f"Error writing to debug file: {e}")

debug_write("Debug test started")

class MessageLog(Static):
    """Simplified MessageLog widget for debugging."""
    # Using reactive for messages list - this might be part of the issue
    messages = reactive([], recompose=True)
    
    def __init__(self, *args, **kwargs):
        debug_write(f"MessageLog.__init__ START with args: {args}, kwargs: {kwargs}")
        super().__init__(*args, **kwargs)
        
        # Initialize our message storage as a protected attribute
        self._messages = []
        debug_write(f"_messages initialized as: {type(self._messages)}, id: {id(self._messages)}")
        
        # Track all attributes set on this object
        self._original_setattr = self.__class__.__setattr__
        
        # Monkey patch __setattr__ to track attribute changes
        def debug_setattr(self, name, value):
            debug_write(f"Setting attribute {name} to {type(value)}")
            if name == '_messages':
                debug_write(f"IMPORTANT: Setting _messages to {type(value)}, value: {value}")
                if not isinstance(value, list):
                    debug_write(f"WARNING: Attempting to set _messages to non-list: {type(value)}")
                    stack = ''.join(traceback.format_stack())
                    debug_write(f"Stack trace: {stack}")
                    # Force it to be a list
                    value = []
            self._original_setattr(self, name, value)
            
        self.__class__.__setattr__ = debug_setattr
        
        # Create a log widget reference
        self._log = None
        debug_write("MessageLog.__init__ COMPLETE")
    
    def compose(self):
        """Create the RichLog widget."""
        debug_write("MessageLog.compose START")
        with ScrollableContainer():
            rich_log = RichLog(highlight=True, markup=True)
            yield rich_log
            self._log = rich_log
        debug_write(f"MessageLog.compose COMPLETE, _log: {self._log}")
    
    def on_mount(self):
        """Called when widget is mounted."""
        debug_write("MessageLog.on_mount START")
        
        # Check for any watch methods
        watches = [attr for attr in dir(self) if attr.startswith('watch_')]
        debug_write(f"Found watch methods: {watches}")
        
        # Add a test message
        self.add_message({"type": "system", "content": "Test message 1"})
        
        # Add another test message after a brief delay
        self.set_timer(0.5, self.add_delayed_message)
        
        debug_write("MessageLog.on_mount COMPLETE")
    
    def add_delayed_message(self):
        """Add a delayed test message."""
        debug_write("Adding delayed test message")
        self.add_message({"type": "system", "content": "Test message 2"})
    
    def add_message(self, message):
        """Add a message to the log."""
        debug_write(f"add_message START with message: {message}")
        
        try:
            # Check current state of _messages
            debug_write(f"Before adding: _messages is {type(self._messages)}, id: {id(self._messages)}")
            
            # Verify _messages is a list
            if not isinstance(self._messages, list):
                debug_write(f"CRITICAL: _messages is not a list but {type(self._messages)}")
                self._messages = []
                debug_write(f"Reset _messages to empty list, id: {id(self._messages)}")
            
            # Make a copy of the message
            if isinstance(message, dict):
                msg_copy = dict(message)
            else:
                msg_copy = {"type": "unknown", "content": str(message)}
            
            # Try to append to _messages
            debug_write("About to append to _messages")
            try:
                self._messages.append(msg_copy)
                debug_write("Successfully appended to _messages")
            except AttributeError as ae:
                debug_write(f"AttributeError during append: {ae}")
                debug_write(f"_messages type: {type(self._messages)}, value: {self._messages}")
                # Try to recover
                self._messages = [msg_copy]
                debug_write("Reset _messages to new list with the message")
            
            # Format and display the message
            if self._log:
                # Format based on message type
                msg_type = msg_copy.get("type", "unknown")
                content = str(msg_copy.get("content", msg_copy.get("text", "")))
                formatted = f"{msg_type.upper()}: {content}\n\n"
                
                # Write to the log
                self._log.write(formatted)
                self._log.scroll_end(animate=False)
                debug_write("Successfully wrote to log")
            else:
                debug_write("No _log available to write message")
                
            # Update reactive messages list - THIS MIGHT TRIGGER THE ISSUE
            debug_write("About to update reactive messages list")
            current_messages = list(self.messages)
            current_messages.append(msg_copy)
            self.messages = current_messages
            debug_write("Successfully updated reactive messages list")
            
        except Exception as e:
            debug_write(f"Error in add_message: {e}")
            debug_write(traceback.format_exc())
    
    def watch_messages(self, old_messages, new_messages):
        """Watch for changes to the messages reactive attribute."""
        debug_write(f"watch_messages called: old_len={len(old_messages) if isinstance(old_messages, list) else 'not-list'}, new_len={len(new_messages) if isinstance(new_messages, list) else 'not-list'}")
        
        # Check _messages right after reactive update
        debug_write(f"In watch_messages: _messages is {type(self._messages)}, id: {id(self._messages)}")
        
        # THIS IS LIKELY WHERE THE ISSUE HAPPENS
        # Check if _messages has been converted to a boolean
        if isinstance(self._messages, bool):
            debug_write(f"CRITICAL: _messages has been converted to a boolean: {self._messages}")
            # Try to recover
            self._messages = []
            debug_write("Reset _messages to empty list")
        
        # Update display if needed
        self._update_display()
    
    def _update_display(self):
        """Update the display with current messages."""
        debug_write("_update_display called")
        
        try:
            # Check _messages again
            debug_write(f"In _update_display: _messages is {type(self._messages)}, id: {id(self._messages)}")
            
            # Ensure _messages is a list
            if not isinstance(self._messages, list):
                debug_write(f"CRITICAL: _messages is not a list in _update_display: {type(self._messages)}")
                self._messages = []
            
            # Update display if we have a log widget
            if self._log:
                debug_write("Updating display")
            else:
                debug_write("No _log available for display update")
                
        except Exception as e:
            debug_write(f"Error in _update_display: {e}")
            debug_write(traceback.format_exc())


class DebugApp(App):
    """Simple app for debugging."""
    
    def compose(self):
        """Create the UI."""
        yield MessageLog()


if __name__ == "__main__":
    app = DebugApp()
    app.run()
