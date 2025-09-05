"""
Input bar widget for the Spy Agency CLI application.

This module contains the InputBar widget, which allows the user to enter
messages to send to the agent.
"""

from typing import Callable, Optional

from textual.binding import Binding
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widgets import Button, Input

from src.client.logger import logger


class InputBar(Horizontal):
    """
    Widget for user input.
    
    This widget provides an input field for the user to enter messages
    and a send button to submit them.
    """
    
    DEFAULT_CSS = """
    InputBar {
        height: 3;
        dock: bottom;
        padding: 0 1;
        background: $background;
        border-top: solid $primary;
    }
    
    InputBar Input {
        width: 1fr;
        margin-right: 1;
    }
    
    InputBar Button {
        width: 10;
    }
    
    .disabled {
        opacity: 0.5;
    }
    """
    
    BINDINGS = [
        Binding("ctrl+enter", "submit", "Submit"),
    ]
    
    enabled = reactive(True)
    
    def __init__(
        self,
        on_submit: Optional[Callable[[str], None]] = None,
        placeholder: str = "Type a message...",
        *args,
        **kwargs,
    ):
        """
        Initialize a new input bar.
        
        Args:
            on_submit: Callback for when a message is submitted
            placeholder: Placeholder text for the input field
            *args: Additional positional arguments for the parent class
            **kwargs: Additional keyword arguments for the parent class
        """
        super().__init__(*args, **kwargs)
        self.on_submit = on_submit
        self.placeholder = placeholder
        
    def compose(self):
        """Define the components of the input bar."""
        self.input = Input(placeholder=self.placeholder)
        self.send_button = Button("Send", variant="primary")
        
        yield self.input
        yield self.send_button
        
    def on_mount(self):
        """Handle the mount event."""
        # Focus the input field
        self.input.focus()
        
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        Handle button press events.
        
        Args:
            event: The button press event
        """
        if event.button == self.send_button:
            self.submit_message()
            
    def on_input_submitted(self) -> None:
        """Handle input submission events."""
        self.submit_message()
        
    def action_submit(self) -> None:
        """Submit the current message."""
        self.submit_message()
        
    def submit_message(self) -> None:
        """Submit the current message."""
        if not self.enabled:
            return
            
        message = self.input.value.strip()
        
        if not message:
            return
            
        logger.debug(f"Submitting message: {message}")
        
        # Call the on_submit callback if provided
        if self.on_submit:
            self.on_submit(message)
            
        # Clear the input field
        self.input.value = ""
        
        # Focus the input field
        self.input.focus()
        
    def enable(self) -> None:
        """Enable the input bar."""
        self.enabled = True
        self.input.disabled = False
        self.send_button.disabled = False
        self.input.focus()
        self.remove_class("disabled")
        
    def disable(self) -> None:
        """Disable the input bar."""
        self.enabled = False
        self.input.disabled = True
        self.send_button.disabled = True
        self.add_class("disabled")
        
    def watch_enabled(self, enabled: bool) -> None:
        """
        Watch for changes to the enabled state.
        
        Args:
            enabled: The new enabled state
        """
        if enabled:
            self.enable()
        else:
            self.disable()
