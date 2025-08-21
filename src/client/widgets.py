"""
Custom widgets for the Spy Command Console application.
"""
from typing import Dict, List, Any, Callable
from datetime import datetime
import logging

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, Input, Button, Label
# No reactive needed for now

# Get logger
logger = logging.getLogger("spy_cli")


class SpySelector(Vertical):
    """Widget for selecting a spy agent"""
    
    BINDINGS = [
        ("enter", "select_focused", "Select focused spy")
    ]
    
    def __init__(self, spies: List[Dict[str, Any]], on_select: Callable[[Dict[str, Any]], None]):
        super().__init__(id="spy-selector")
        self.spies = spies
        self.on_select = on_select
        self.focused_button = None
        
    def compose(self) -> ComposeResult:
        """Create the spy selector UI"""
        yield Label("SELECT SPY AGENT", classes="section-title")
        
        with Vertical(classes="spy-list"):
            for spy in self.spies:
                # Get avatar from codename
                abbrev = "".join([word[0] for word in spy["codename"].split() if word])
                
                with Horizontal(classes="spy-item"):
                    yield Label(abbrev, classes="spy-avatar")
                    yield Button(f"{spy['name']} ({spy['codename']})", 
                                id=f"spy-{spy['id']}", 
                                classes="spy-name")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events"""
        button_id = event.button.id
        print(f"BUTTON PRESSED: {button_id}")
        logger.debug(f"Button pressed: {button_id}")
        
        # Store the focused button
        self.focused_button = event.button
        
        if button_id and button_id.startswith("spy-"):
            # Add visual feedback - highlight the selected button
            for button in self.query(Button):
                if button.id.startswith("spy-"):
                    if button.id == button_id:
                        button.add_class("selected")
                    else:
                        button.remove_class("selected")
            
            spy_id = button_id[4:]  # Remove "spy-" prefix
            print(f"SPY ID EXTRACTED: {spy_id}")
            logger.debug(f"Spy ID extracted: {spy_id}")
            
            for spy in self.spies:
                print(f"CHECKING SPY: {spy.get('id', 'unknown')} - {spy.get('name', 'unknown')}")
                logger.debug(f"Checking spy: {spy.get('id', 'unknown')} - {spy.get('name', 'unknown')}")
                if spy.get("id") == spy_id:
                    print(f"FOUND MATCHING SPY: {spy.get('name', 'unknown')}")
                    logger.debug(f"Found matching spy: {spy.get('name', 'unknown')}")
                    print(f"CALLING ON_SELECT CALLBACK WITH SPY DATA: {spy}")
                    logger.debug(f"Calling on_select callback with spy data: {spy}")
                    try:
                        self.on_select(spy)
                        print("ON_SELECT CALLBACK COMPLETED SUCCESSFULLY")
                        logger.debug("on_select callback completed successfully")
                    except Exception as e:
                        print(f"ERROR IN ON_SELECT CALLBACK: {str(e)}")
                        logger.error(f"Error in on_select callback: {str(e)}")
                        import traceback
                        traceback_str = traceback.format_exc()
                        print(traceback_str)
                        logger.error(traceback_str)
                    break
            else:
                print(f"NO MATCHING SPY FOUND FOR ID: {spy_id}")
                logger.warning(f"No matching spy found for ID: {spy_id}")
        else:
            print(f"NON-SPY BUTTON PRESSED: {button_id}")
            logger.debug(f"Non-spy button pressed: {button_id}")
            
        # Force the log to flush
        import sys
        sys.stdout.flush()
        
    def on_button_focus(self, event: Button.Focused) -> None:
        """Track which button is currently focused"""
        self.focused_button = event.button
        print(f"BUTTON FOCUSED: {event.button.id}")
        logger.debug(f"Button focused: {event.button.id}")
        
    def action_select_focused(self) -> None:
        """Handle Enter key press to select the focused spy"""
        print("ENTER KEY PRESSED FOR SPY SELECTION")
        logger.debug("Enter key pressed for spy selection")
        
        if self.focused_button and self.focused_button.id and self.focused_button.id.startswith("spy-"):
            print(f"SELECTING FOCUSED SPY BUTTON: {self.focused_button.id}")
            logger.debug(f"Selecting focused spy button: {self.focused_button.id}")
            
            # Simulate a button press event
            self.focused_button.press()
        else:
            print("NO FOCUSED SPY BUTTON TO SELECT")
            logger.warning("No focused spy button to select")
            
        # Force the log to flush
        import sys
        sys.stdout.flush()


class ChatWindow(Vertical):
    """Widget for displaying chat messages"""
    
    def __init__(self, spy_name: str, spy_avatar: str):
        super().__init__(id="chat-window")
        self.spy_name = spy_name
        self.spy_avatar = spy_avatar
        self.typing_indicator = None
        
    def add_message(self, content: str, is_user: bool = False) -> None:
        """Add a message to the chat window"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if is_user:
            # User message
            with Horizontal(classes="message user-message"):
                self.mount(Label("YOU", classes="user-avatar"))
                self.mount(Static(f"{content}\n[{timestamp}]", classes="message-content"))
        else:
            # Spy message
            with Horizontal(classes="message spy-message"):
                self.mount(Label(self.spy_avatar, classes="spy-avatar"))
                self.mount(Static(f"{content}\n[{timestamp}]", classes="message-content"))
                
        # Scroll to the bottom
        self.scroll_end(animate=False)
        
    def show_typing(self) -> None:
        """Show typing indicator"""
        if self.typing_indicator is None:
            self.typing_indicator = TypingIndicator(self.spy_avatar)
            self.mount(self.typing_indicator)
            self.scroll_end(animate=False)
            
    def hide_typing(self) -> None:
        """Hide typing indicator"""
        if self.typing_indicator is not None:
            self.typing_indicator.remove()
            self.typing_indicator = None


class TypingIndicator(Horizontal):
    """Widget for showing typing indicator"""
    
    def __init__(self, spy_avatar: str):
        super().__init__(classes="typing-indicator")
        self.spy_avatar = spy_avatar
        
    def compose(self) -> ComposeResult:
        """Create the typing indicator UI"""
        yield Label(self.spy_avatar, classes="spy-avatar")
        yield Static("Typing...", classes="typing-text")


class InputBar(Input):
    """Custom input bar with callback for submission"""
    
    def __init__(self, on_submit: Callable[[str], None]):
        super().__init__()
        self.on_submit_callback = on_submit
        
    def on_key(self, event) -> None:
        """Handle key events"""
        if event.key == "enter":
            self.submit()
            
    def submit(self) -> None:
        """Submit the input value"""
        if self.value:
            self.on_submit_callback(self.value)
            self.value = ""
