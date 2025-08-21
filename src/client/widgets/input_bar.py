from textual.widgets import Input, Button
from textual.containers import Horizontal
from textual.app import ComposeResult
from typing import Callable


class InputBar(Horizontal):
    """Input bar for sending messages"""
    
    def __init__(self, on_submit: Callable[[str], None]):
        super().__init__()
        self.on_submit = on_submit
        
    def compose(self) -> ComposeResult:
        yield Input(placeholder="Type your message here...", id="message-input")
        yield Button("Send", id="send-button", variant="primary")
        
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle send button press"""
        if event.button.id == "send-button":
            self._submit_message()
            
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission (Enter key)"""
        self._submit_message()
        
    def _submit_message(self) -> None:
        """Submit the current message"""
        input_widget = self.query_one("#message-input", Input)
        message = input_widget.value
        
        if message and message.strip():
            # Clear the input
            input_widget.value = ""
            
            # Call the submission callback
            self.on_submit(message.strip())
            
    def focus_input(self) -> None:
        """Focus the input field"""
        input_widget = self.query_one("#message-input", Input)
        input_widget.focus()
