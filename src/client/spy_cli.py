#!/usr/bin/env python3
import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

import logging
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Header, Footer, Button, RadioSet, RadioButton, Label, Static
from textual.reactive import reactive
from textual.worker import Worker, get_current_worker

from .api_client import SpyAPIClient
from .widgets.spy_selector import SpySelector
from .widgets import ChatWindow, InputBar
from .history_manager import HistoryManager
from . import config as config

# Initialize logging
log_file = os.path.join(config.DATA_DIR, 'spy_cli_debug.log')
logging.basicConfig(
    level=logging.DEBUG,  # Force DEBUG level for troubleshooting
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file)
    ]
)
logger = logging.getLogger(config.APP_NAME)
logger.debug(f"Logging initialized. Log file: {log_file}")
logger.debug(f"API Base URL: {config.API_BASE_URL}")
logger.debug(f"WebSocket URL: {config.WS_BASE_URL}")


class SpyCommandConsole(App):
    """A terminal-based interface for interacting with AI-powered spy agents."""
    
    # Define keyboard bindings
    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
        ("ctrl+s", "submit_message", "Send Message"),
        ("ctrl+c", "clear_input", "Clear Input"),
        ("ctrl+h", "show_history", "History"),
        ("ctrl+o", "save_conversation", "Save"),
        ("f1", "show_help", "Help"),
    ]
    
    CSS = """
    Screen {
        background: #000000;
        color: #00ff00;
    }
    
    .section-title {
        background: #003300;
        color: #00ff00;
        padding: 1;
        text-align: center;
        width: 100%;
    }
    
    .spy-name {
        background: #003300;
        color: #00ff00;
        width: 100%;
        text-align: left;
        padding: 0 1;
    }
    
    .spy-name.selected {
        background: #00aa00;
        color: #000000;
        text-style: bold;
    }
    
    #spy-selector {
        height: auto;
        margin: 1 0;
        border: solid green;
    }
    
    .spy-list {
        height: auto;
        border: none;
    }
    
    .spy-avatar {
        background: #003300;
        color: white;
        min-width: 4;
        text-align: center;
        margin-right: 1;
    }
    
    .spy-name {
        color: #00ff00;
    }
    
    #chat-container {
        height: 1fr;
        border: solid green;
        overflow-y: auto;
    }
    
    #input-container {
        height: 3;
        margin-top: 1;
        display: none;  /* Start hidden */
    }
    
    #input-container.visible {
        display: block;  /* Show when visible class is added */
    }
    
    #message-input {
        background: #111111;
        color: white;
        border: solid green;
        min-width: 60;
    }
    
    #send-button {
        background: #003300;
        color: #00ff00;
        min-width: 10;
    }
    
    #mode-selector {
        margin: 1 0;
        border: solid green;
        padding: 1;
    }
    
    .mode-title {
        color: #00ff00;
        margin-right: 2;
    }
    
    #mission-input {
        background: #111111;
        color: white;
        border: solid green;
        display: none;
    }
    
    #mission-input.visible {
        display: block;
    }
    
    .system-message {
        color: #ffff00;
        text-align: center;
    }
    
    .error-message {
        color: #ff0000;
        text-align: center;
    }
    """
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
        ("enter", "select_focused_spy", "Select focused spy"),
    ]
    
    # Reactive attributes
    selected_spy = reactive(None)
    conversation_id = reactive(None)
    
    def __init__(self):
        super().__init__()
        self.api_client = SpyAPIClient()
        self.history_manager = HistoryManager()
        self.spies = []
        self.ws_worker = None
        self.messages = []  # Store messages for saving
        logger.info("SpyCommandConsole initialized")
    
    def compose(self) -> ComposeResult:
        """Create the UI layout"""
        yield Header(show_clock=True)
        
        # Main container
        with Container(id="main-container"):
            # Initial loading message
            yield Static("Loading spy agents...", id="loading-message")
            
        yield Footer()
    
    async def on_mount(self) -> None:
        """Load data when the app starts"""
        # Fetch spy list from API
        logger.info("Application mounted, fetching spy list")
        try:
            self.spies = await self.api_client.get_spies()
            logger.info(f"Loaded {len(self.spies)} spy agents")
            await self.setup_ui()
        except Exception as e:
            error_msg = f"Error loading spy agents: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.query_one("#loading-message").update(error_msg)
    
    async def setup_ui(self) -> None:
        """Set up the UI after loading data"""
        # Remove loading message
        self.query_one("#loading-message").remove()
        
        # Create main UI
        main_container = self.query_one("#main-container")
        
        # Spy selector
        spy_selector = SpySelector(self.spies, self.on_spy_selected, id="spy-selector")
        main_container.mount(spy_selector)
        logger.debug(f"Mounted SpySelector with ID: {spy_selector.id}")
            
        # Add a welcome message to the sidebar
        welcome = Static("\nWelcome to Spy Chat\n", classes="section-title")
        sidebar = Container(id="sidebar")
        main_container.mount(sidebar)
        sidebar.mount(welcome)
        
        # Add connection status
        self.connection_status = Static("Status: Connecting...", id="connection-status")
        sidebar.mount(self.connection_status)
        
        # Chat container (initially hidden)
        main_container.mount(Container(id="chat-container"))
        
        # Input container (initially hidden)
        input_container = Container(id="input-container")
        main_container.mount(input_container)
        message_input = InputBar(self.on_message_submitted)
        message_input.id = "message-input"
        input_container.mount(message_input)
    
    async def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """Handle radio set changes"""
        # This method is kept for compatibility but mode switching is removed
        pass
    
    async def on_spy_selected(self, spy_data: Dict[str, Any]) -> None:
        """Handle spy selection"""
        logger.debug(f"on_spy_selected called with spy: {spy_data}")
        self.selected_spy = spy_data
        logger.info(f"Selected spy: {spy_data['name']}")
        
        try:
            # Remove the spy selector if it exists
            try:
                spy_selector = self.query_one("#spy-selector")
                if spy_selector:
                    logger.debug("Removing spy selector")
                    await spy_selector.remove()
                    logger.debug("Successfully removed spy selector")
            except Exception as e:
                logger.error(f"Error removing spy selector: {e}", exc_info=True)
            
            # Get or create chat container
            try:
                chat_container = self.query_one("#chat-container")
                if not chat_container:
                    logger.debug("Chat container not found, creating one")
                    main_container = self.query_one("#main-container")
                    if not main_container:
                        raise RuntimeError("Main container not found")
                    chat_container = Container(id="chat-container")
                    main_container.mount(chat_container)
                    await self.refresh_layout()
                    logger.debug("Created and mounted chat container")
                else:
                    # Clear existing chat UI if any
                    logger.debug("Clearing existing chat UI")
                    await chat_container.remove_children()
                    await self.refresh_layout()
                    logger.debug("Cleared chat container")
                
                # Initialize chat UI
                logger.debug("Setting up chat UI")
                self.setup_chat_ui()
                
                # Connect to WebSocket in the background
                logger.debug("Starting WebSocket connection")
                self.run_worker(self.connect_websocket())
                
            except Exception as e:
                logger.error(f"Error setting up chat UI: {e}", exc_info=True)
                raise
                
        except Exception as e:
            error_msg = f"Error in on_spy_selected: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.notify(error_msg, severity="error")
            
            # Fallback UI in case of error
            try:
                logger.debug("Attempting fallback UI creation")
                chat_container = self.query_one("#chat-container")
                if not chat_container:
                    main_container = self.query_one("#main-container")
                    if main_container:
                        chat_container = Container(id="chat-container")
                        main_container.mount(chat_container)
                
                if chat_container:
                    abbrev = "".join([word[0] for word in spy_data["codename"].split() if word])
                    chat_window = ChatWindow(spy_data["name"], abbrev)
                    logger.debug(f"Mounting fallback chat window for {spy_data['name']}")
                    chat_container.mount(chat_window)
                    await self.refresh_layout()
            except Exception as fallback_error:
                logger.error(f"Error in fallback UI: {fallback_error}", exc_info=True)
                self.notify("Failed to initialize chat interface", severity="error")
            
            # Add welcome message
            welcome_msg = f"I'm {spy_data['name']}, codename {spy_data['codename']}. How can I assist you?"
            print(f"ADDING WELCOME MESSAGE: {welcome_msg}")
            logger.debug(f"Adding welcome message: {welcome_msg}")
            chat_window.add_message(welcome_msg, is_user=False)
            self.messages.append({
                "role": "system",
                "content": welcome_msg,
                "timestamp": datetime.now().isoformat()
            })
            
            # Show input container
            print("GETTING INPUT CONTAINER")
            logger.debug("Getting input container")
            input_container = self.query_one("#input-container")
            print(f"INPUT CONTAINER FOUND: {input_container}")
            logger.debug(f"Input container found: {input_container}")
            if not input_container.has_class("visible"):
                print("ADDING 'VISIBLE' CLASS TO INPUT CONTAINER")
                logger.debug("Adding 'visible' class to input container")
                input_container.add_class("visible")
            else:
                print("INPUT CONTAINER ALREADY HAS 'VISIBLE' CLASS")
                logger.debug("Input container already has 'visible' class")
            
            # Focus the message input
            print("GETTING MESSAGE INPUT")
            logger.debug("Getting message input")
            message_input = self.query_one("#message-input")
            print(f"MESSAGE INPUT FOUND: {message_input}")
            logger.debug(f"Message input found: {message_input}")
            print("FOCUSING MESSAGE INPUT")
            logger.debug("Focusing message input")
            message_input.focus()
            print("SPY SELECTION PROCESS COMPLETED SUCCESSFULLY")
            logger.debug("Spy selection process completed successfully")
                
        except Exception as e:
            print(f"ERROR IN ON_SPY_SELECTED: {str(e)}")
            import traceback
            traceback_str = traceback.format_exc()
            print(traceback_str)
            logger.error(f"Error in on_spy_selected: {str(e)}", exc_info=True)
            
        # Force the log to flush
        import sys
        sys.stdout.flush()
    
    async def on_message_submitted(self, message: str) -> None:
        """Handle sending and receiving messages"""
        if not message.strip() or not self.selected_spy:
            return
            
        spy_id = self.selected_spy["id"]
        
        # Add user message to chat
        chat_window = self.query_one(ChatWindow)
        chat_window.add_message(message, is_user=True)
        
        try:
            # Get the input widget and clear it
            input_widget = self.query_one("#message-input", InputBar)
            input_widget.value = ""
            
            # Show typing indicator
            chat_window.show_typing()
            
            # Update connection status
            status = self.query_one("#connection-status")
            status.update("Status: Sending message...")
            
            try:
                # Always use chat with conversation history
                if not self.conversation_id:
                    # Start a new conversation
                    logger.debug("Starting new conversation")
                    conv = await self.api_client.create_conversation(spy_id)
                    self.conversation_id = conv.get("conversation_id")
                    logger.info(f"New conversation created: {self.conversation_id}")
                
                # Send the message
                response = await self.api_client.chat_with_history(
                    spy_id=spy_id,
                    conversation_id=self.conversation_id,
                    message=message
                )
                
                # Process the response
                chat_window.add_message(response["response"], is_user=False)
                status.update("Status: Connected")
                
            except Exception as e:
                status.update("Status: Error (see chat)")
                raise
                
        except Exception as e:
            error_msg = f"Error sending message: {str(e)}"
            logger.error(error_msg, exc_info=True)
            chat_window.add_message(error_msg, is_user=False)
        finally:
            # Always remove typing indicator
            chat_window.hide_typing()
    
    async def action_quit(self) -> None:
        """Quit the application"""
        logger.info("Shutting down application")
        # Close API client connections
        await self.api_client.close()
        self.exit()
        
    def action_select_focused_spy(self) -> None:
        """Select the currently focused spy"""
        logger.debug("Enter key pressed in main app")
        if not self.selected_spy:
            try:
                logger.debug("No spy selected yet, looking for spy selector")
                spy_selector = self.query_one("#spy-selector")
                logger.debug(f"Found spy selector: {spy_selector}")
                
                if hasattr(spy_selector, "action_select_focused"):
                    logger.debug("Calling action_select_focused on spy selector")
                    spy_selector.action_select_focused()
                else:
                    logger.warning("SpySelector doesn't have action_select_focused method")
                    print("SPY SELECTOR DOESN'T HAVE ACTION_SELECT_FOCUSED METHOD")
                    # Log all methods available on spy_selector
                    logger.debug(f"Available methods: {[m for m in dir(spy_selector) if not m.startswith('_')]}")
            except Exception as e:
                print(f"ERROR IN ACTION_SELECT_FOCUSED_SPY: {str(e)}")
                logger.error(f"Error in action_select_focused_spy: {str(e)}", exc_info=True)
                
        # Force the log to flush
        import sys
        sys.stdout.flush()
        
    async def action_submit_message(self) -> None:
        """Submit the current message"""
        input_bar = self.query_one("#message-input")
        if input_bar and input_bar.value:
            logger.debug("Submitting message via keyboard shortcut")
            await self.on_message_submitted(input_bar.value)
            input_bar.value = ""
            
    def action_clear_input(self) -> None:
        """Clear the input field"""
        input_bar = self.query_one("#message-input")
        if input_bar:
            input_bar.value = ""
            logger.debug("Input field cleared via keyboard shortcut")
            
    def action_toggle_chat_mode(self) -> None:
        """This method is kept for key binding compatibility but does nothing"""
        logger.debug("Chat mode toggle is no longer supported")
            
    def action_show_help(self) -> None:
        """Show help information"""
        help_text = """
        Keyboard Shortcuts:
        -----------------
        Ctrl+Q: Quit the application
        Ctrl+S: Send the current message
        Ctrl+C: Clear the input field
        Ctrl+H: Show conversation history
        Ctrl+O: Save current conversation
        F1: Show this help information
        
        Type :quit to exit the application
        """
        
        chat_window = self.query_one(ChatWindow)
        if chat_window:
            chat_window.add_message(help_text, is_user=False)
            logger.debug("Help information displayed")
            
    def action_save_conversation(self) -> None:
        """Save the current conversation"""
        if not self.selected_spy or not self.conversation_id or not self.messages:
            self.show_error("No conversation to save")
            return
            
        try:
            spy_id = self.selected_spy["id"]
            filepath = self.history_manager.save_conversation(
                spy_id, 
                self.conversation_id, 
                self.messages
            )
            
            chat_window = self.query_one(ChatWindow)
            chat_window.add_message(f"Conversation saved to {os.path.basename(filepath)}", is_user=False)
            logger.info(f"Conversation saved to {filepath}")
            
        except Exception as e:
            error_msg = f"Error saving conversation: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.show_error(error_msg)
            
    async def action_show_history(self) -> None:
        """Show conversation history"""
        if not self.selected_spy:
            self.show_error("Please select a spy first")
            return
            
        try:
            spy_id = self.selected_spy["id"]
            conversations = self.history_manager.get_conversation_list(spy_id)
            
            if not conversations:
                self.show_error("No saved conversations found")
                return
                
            # Display conversation list
            chat_window = self.query_one(ChatWindow)
            chat_window.add_message("Available conversations:", is_user=False)
            
            for i, conv in enumerate(conversations[:10]):  # Show up to 10 most recent
                date_str = conv["date"].split("T")[0] if conv["date"] else "Unknown date"
                chat_window.add_message(f"{i+1}. {date_str} - {conv['message_count']} messages", is_user=False)
                
            chat_window.add_message("Type the number of the conversation to load (e.g., '1'):", is_user=False)
            
            # Store conversations for later reference
            self._history_conversations = conversations
            
            # Set a flag to handle the next message as a history selection
            self._awaiting_history_selection = True
            
        except Exception as e:
            error_msg = f"Error loading conversation history: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.show_error(error_msg)
            
    async def _load_conversation(self, filepath: str) -> None:
        """Load a conversation from disk"""
        try:
            # Load the conversation
            conversation = self.history_manager.load_conversation(filepath)
            messages = conversation.get("messages", [])
            
            if not messages:
                self.show_error("No messages found in the conversation file")
                return
                
            # Clear the current chat window
            chat_container = self.query_one("#chat-container")
            chat_container.remove_children()
            
            # Get avatar from codename
            abbrev = "".join([word[0] for word in self.selected_spy["codename"].split() if word])
            
            # Create and mount new chat window
            chat_window = ChatWindow(self.selected_spy["name"], abbrev)
            chat_container.mount(chat_window)
            
            # Add messages to the chat window
            for msg in messages:
                role = msg.get("role", "")
                content = msg.get("content", "")
                
                if role == "user":
                    chat_window.add_message(content, is_user=True)
                elif role in ["assistant", "system"]:
                    chat_window.add_message(content, is_user=False)
            
            # Set the conversation ID and messages
            self.conversation_id = conversation.get("conversation_id")
            self.messages = messages
            
            # Add a system message indicating the conversation was loaded
            load_msg = f"Loaded conversation from {os.path.basename(filepath)}"
            chat_window.add_message(load_msg, is_user=False)
            logger.info(f"Loaded conversation from {filepath}")
            
        except Exception as e:
            error_msg = f"Error loading conversation: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.show_error(error_msg)



if __name__ == "__main__":
    app = SpyCommandConsole()
    app.run()
