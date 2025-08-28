"""
Main screen for the Spy CLI application.
"""
import asyncio
from typing import Dict, Any

from textual.screen import Screen
from textual.containers import Container, Vertical
from textual.widgets import Header, Footer, Label
from textual.reactive import reactive

from ..api_client import SpyAPIClient
from ..widgets.spy_selector import SpySelector, SpyListItem, SpySelected
from ..widgets.chat_window import ChatWindow
from ..widgets.input_bar import InputBar
from ..history_manager import HistoryManager

class MainScreen(Screen):
    """Main application screen with chat interface and spy selection."""
    
    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
        ("ctrl+s", "submit_message", "Send Message"),
        ("ctrl+c", "clear_input", "Clear Input"),
        ("ctrl+h", "show_history", "History"),
        ("ctrl+o", "save_conversation", "Save"),
        ("f1", "show_help", "Help"),
    ]
    
    active_spy = reactive(None)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_client = SpyAPIClient()
        self.history_manager = HistoryManager()
        self.messages = []
        self.spies = []
    
    def compose(self):
        """Create child widgets for the app."""
        yield Header()
        
        with Container(id="app-grid"):
            with Vertical(id="left-panel"):
                yield Label("Available Spies", classes="section-title")
                # Initialize with empty spies list
                yield SpySelector(
                    id="spy-selector",
                    spies=[]  # Will be populated in on_mount
                )
            
            with Vertical(id="right-panel"):
                # Create a container for the chat window with an ID
                with Container(id="chat-window"):
                    # Initialize with default values that can be updated later
                    self.chat_component = ChatWindow(
                        spy_name="Agent",
                        spy_avatar="👤"
                    )
                    yield self.chat_component
                yield InputBar(on_submit=self._on_message_submit)
        
        yield Footer()
    
    async def on_mount(self) -> None:
        """Initialize the screen after mounting."""
        await self.load_spies()
    
    async def load_spies(self) -> None:
        """Load available spies from the API."""
        try:
            self.spies = await self.api_client.get_spies()
            selector = self.query_one(SpySelector)
            # Update the spies list in the selector
            selector.spies = self.spies
            # Clear and repopulate the list
            spy_list = selector.query_one("#spy-list")
            spy_list.clear()
            for spy in self.spies:
                spy_list.append(SpyListItem(spy))
        except Exception as e:
            self.notify(f"Failed to load spies: {str(e)}", severity="error")
            
    async def _on_spy_selected(self, spy_data: Dict[str, Any]) -> None:
        """Handle spy selection.
        
        Args:
            spy_data: Dictionary containing spy information
        """
        if hasattr(spy_data, 'spy_data'):
            spy_data = spy_data.spy_data
            
        self.active_spy = spy_data
        self.chat_component.spy_name = spy_data.get('name', 'Agent')
        self.chat_component.spy_avatar = spy_data.get('avatar', '👤')
        self.chat_component.clear()
        
        input_field = self.query_one("#message-input")
        if input_field:
            input_field.focus()
            
        spy_name = spy_data.get('name', 'Unknown')
        self.notify(f"Selected {spy_name}", title="Spy Selected")
        
    async def _on_message_submit(self, message: str) -> None:
        """Handle message submission from the input bar.
        
        Args:
            message: The message text to send
        """
        if not message.strip():
            return
            
        if not self.active_spy:
            self.notify("Please select a spy first", severity="warning")
            return
            
        # Add user message to chat
        self.chat_component.add_message(message, is_user=True)
        
        try:
            # Show typing indicator
            self.chat_component.show_typing()
            
            # Ensure we have a spy ID
            spy_id = self.active_spy.get('id')
            if not spy_id:
                raise ValueError("No spy ID found in active spy data")
            
            # Log the request
            print(f"Sending message to spy {spy_id}: {message}")
            
            # Send message via HTTP
            response = await self.api_client.chat(
                spy_id=spy_id,
                message=message
            )
            
            # Log the response
            print(f"Received response: {response}")
            
            if not isinstance(response, dict):
                raise ValueError(f"Unexpected response format: {response}")
                
            if 'response' in response:
                # Add the response to chat
                self.chat_component.add_message(response['response'], is_user=False)
                
                # Save to history
                await self.history_manager.save_message(
                    spy_id=spy_id,
                    message=message,
                    response=response['response']
                )
            else:
                error_msg = "No response content received from server"
                if 'detail' in response:
                    error_msg = f"Server error: {response['detail']}"
                self.notify(error_msg, severity="error")
                self.chat_component.add_message(error_msg, is_user=False)
                
        except Exception as e:
            error_msg = f"Error sending message: {str(e)}"
            print(error_msg)  # Log to console for debugging
            self.notify(error_msg, severity="error")
            self.chat_component.add_message(error_msg, is_user=False)
            
        finally:
            # Always hide the typing indicator
            self.chat_component.hide_typing()
        
    async def on_spy_selector_spy_selected(self, event: SpySelected) -> None:
        """Handle the SpySelected event from the SpySelector.
        
        Args:
            event: The SpySelected event containing spy data
        """
        await self._on_spy_selected(event.spy_data)
    
    async def on_input_submitted(self, event) -> None:
        """Handle message submission."""
        if not self.active_spy:
            self.notify("Please select a spy first", severity="warning")
            return
            
        message = event.value.strip()
        if not message:
            return
            
        # Add user message to chat
        self.chat_component.add_message(message, is_user=True)
        
        # Get response from spy
        try:
            # Show typing indicator
            self.chat_component.show_typing()
            
            # Simulate network delay
            await asyncio.sleep(1)
            
            # Get response from API
            response = await self.api_client.chat(
                spy_id=self.active_spy['id'],
                message=message
            )
            
            # Add response to chat
            if 'response' in response:
                self.chat_component.add_message(response['response'], is_user=False)
            else:
                error_msg = "No response content received from server"
                if 'detail' in response:
                    error_msg = f"Server error: {response['detail']}"
                self.notify(error_msg, severity="error")
                self.chat_component.add_message(error_msg, is_user=False)
            
        except Exception as e:
            self.notify(f"Error: {str(e)}", severity="error")
            
        finally:
            # Make sure to hide typing indicator in case of errors
            self.chat_component.hide_typing()
    
    def action_quit(self) -> None:
        """Handle quit action."""
        self.app.exit()
    
    def action_clear_input(self) -> None:
        """Clear the input field."""
        self.query_one("#input-bar", InputBar).clear()
    
    def action_show_help(self) -> None:
        """Show help message."""
        help_text = """\
        Available Commands:
        - Ctrl+S: Send message
        - Ctrl+C: Clear input
        - Ctrl+H: Show history
        - Ctrl+O: Save conversation
        - F1: Show this help
        - Ctrl+Q: Quit
        """
        self.notify(help_text, title="Help", timeout=10)
        
    async def on_unmount(self) -> None:
        """Clean up resources when the screen is unmounted."""
        pass
