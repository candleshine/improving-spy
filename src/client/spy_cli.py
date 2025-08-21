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
from .widgets import SpySelector, ChatWindow, InputBar
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
        ("ctrl+r", "toggle_chat_mode", "Toggle Chat/Debrief"),
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
    mission_id = reactive(None)
    chat_mode = reactive("chat")  # "chat" or "debrief"
    
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
        spy_selector = SpySelector(self.spies, self.on_spy_selected)
        main_container.mount(spy_selector)
            
        # Mode selector
        mode_selector = Container(id="mode-selector")
        main_container.mount(mode_selector)
        
        # Add components to mode selector
        mode_selector.mount(Label("MODE:", classes="mode-title"))
        
        chat_mode = RadioSet(id="chat-mode")
        mode_selector.mount(chat_mode)
        
        chat_mode.mount(RadioButton("Chat", value=True))
        chat_mode.mount(RadioButton("Debrief"))
        
        # Mission ID input (hidden by default)
        mode_selector.mount(Static("Enter mission ID:", id="mission-label", classes="mode-title"))
        mission_input = InputBar(self.on_mission_submitted)
        mission_input.id = "mission-input"
        mode_selector.mount(mission_input)
        
        # Chat container (initially hidden)
        main_container.mount(Container(id="chat-container"))
        
        # Input container (initially hidden)
        input_container = Container(id="input-container")
        main_container.mount(input_container)
        message_input = InputBar(self.on_message_submitted)
        message_input.id = "message-input"
        input_container.mount(message_input)
    
    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """Handle mode selection"""
        if event.radio_set.id == "chat-mode":
            selected_index = event.value
            self.chat_mode = "chat" if selected_index == 0 else "debrief"
            
            # Show/hide mission input
            mission_label = self.query_one("#mission-label")
            mission_input = self.query_one("#mission-input")
            
            if self.chat_mode == "debrief":
                mission_label.add_class("visible")
                mission_input.add_class("visible")
            else:
                mission_label.remove_class("visible")
                mission_input.remove_class("visible")
    
    def on_spy_selected(self, spy_data: Dict[str, Any]) -> None:
        """Handle spy selection"""
        print(f"ON_SPY_SELECTED CALLED WITH SPY_DATA: {spy_data}")
        logger.debug(f"on_spy_selected called with spy_data: {spy_data}")
        
        try:
            print("SETTING SELECTED_SPY AND RESETTING CONVERSATION")
            self.selected_spy = spy_data
            self.conversation_id = None  # Reset conversation ID
            self.messages = []  # Reset message history
            logger.info(f"Spy selected: {spy_data['name']} ({spy_data['codename']})")
            
            # Create chat window
            print("ATTEMPTING TO FIND CHAT CONTAINER")
            logger.debug("Attempting to find chat container")
            chat_container = self.query_one("#chat-container")
            print(f"FOUND CHAT CONTAINER: {chat_container}")
            logger.debug(f"Found chat container: {chat_container}")
            
            print("REMOVING EXISTING CHILDREN FROM CHAT CONTAINER")
            logger.debug("Removing existing children from chat container")
            chat_container.remove_children()
            
            # Get avatar from codename
            print("CREATING CHAT WINDOW")
            logger.debug("Creating chat window")
            abbrev = "".join([word[0] for word in spy_data["codename"].split() if word])
            chat_window = ChatWindow(spy_data["name"], abbrev)
            print(f"MOUNTING CHAT WINDOW WITH SPY NAME: {spy_data['name']} AND AVATAR: {abbrev}")
            logger.debug(f"Mounting chat window with spy name: {spy_data['name']} and avatar: {abbrev}")
            chat_container.mount(chat_window)
            
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
    
    async def on_mission_submitted(self, mission_id: str) -> None:
        """Handle mission ID submission"""
        if not mission_id:
            return
            
        self.mission_id = mission_id
        
        # Create a new conversation
        try:
            response = await self.api_client.create_conversation(self.selected_spy["id"])
            self.conversation_id = response.get("conversation_id")
            
            # Connect to WebSocket
            await self.connect_websocket()
            
            # Show system message
            chat_window = self.query_one(ChatWindow)
            chat_window.add_message(f"Mission context loaded: {mission_id}", is_user=False)
            
            # Hide mission input
            mission_input = self.query_one("#mission-input")
            mission_input.remove_class("visible")
            
            # Focus message input
            self.query_one("#message-input").focus()
        except Exception as e:
            self.show_error(f"Error loading mission: {str(e)}")
    
    async def on_message_submitted(self, message: str) -> None:
        """Handle message submission"""
        if not message or not self.selected_spy:
            return
            
        # Special command to quit
        if message.lower() == ":quit":
            logger.info("Quit command received")
            self.exit()
            return
            
        # Check if we're waiting for history selection
        if hasattr(self, '_awaiting_history_selection') and self._awaiting_history_selection:
            try:
                selection = int(message.strip())
                if 1 <= selection <= len(self._history_conversations):
                    # Get the selected conversation
                    conv = self._history_conversations[selection - 1]
                    filepath = conv['filepath']
                    logger.info(f"Loading conversation from {filepath}")
                    await self._load_conversation(filepath)
                else:
                    self.show_error(f"Invalid selection: {message}")
            except ValueError:
                self.show_error(f"Please enter a number between 1 and {len(self._history_conversations)}")
            except Exception as e:
                error_msg = f"Error loading conversation: {str(e)}"
                logger.error(error_msg, exc_info=True)
                self.show_error(error_msg)
                
            # Reset flag
            self._awaiting_history_selection = False
            return
            
        # Add user message to chat
        chat_window = self.query_one(ChatWindow)
        chat_window.add_message(message, is_user=True)
        
        # Add user message to history
        self.messages.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Show typing indicator
        chat_window.show_typing()
        
        # Send message to API
        try:
            spy_id = self.selected_spy["id"]
            spy_name = self.selected_spy["name"]
            logger.info(f"Sending message to {spy_name}", 
                        mode=self.chat_mode, 
                        message_length=len(message))
            
            if self.chat_mode == "chat":
                if self.conversation_id:
                    logger.debug(f"Using existing conversation: {self.conversation_id}")
                    response = await self.api_client.chat_with_history(
                        spy_id, 
                        self.conversation_id, 
                        message
                    )
                else:
                    logger.debug("Starting new conversation")
                    response = await self.api_client.chat(spy_id, message)
                    self.conversation_id = response.get("conversation_id")
                    logger.info(f"New conversation created: {self.conversation_id}")
            else:  # debrief mode
                logger.debug(f"Debriefing mission: {self.mission_id}")
                response = await self.api_client.debrief(
                    spy_id, 
                    self.mission_id, 
                    message
                )
                self.conversation_id = response.get("conversation_id")
                
            # Hide typing indicator and add response
            chat_window.hide_typing()
            chat_window.add_message(response["response"], is_user=False)
            logger.debug(f"Received response of length {len(response['response'])}")
            
            # Add assistant response to history
            self.messages.append({
                "role": "assistant",
                "content": response["response"],
                "timestamp": datetime.now().isoformat()
            })
            
            # Connect to WebSocket if not already connected
            if not self.ws_worker or self.ws_worker.is_finished:
                await self.connect_websocket()
                
        except Exception as e:
            error_msg = f"Error sending message: {str(e)}"
            logger.error(error_msg, exc_info=True)
            chat_window.hide_typing()
            self.show_error(error_msg)
    
    async def connect_websocket(self) -> None:
        """Connect to WebSocket for real-time updates"""
        if self.ws_worker and not self.ws_worker.is_finished:
            return
            
        # Start WebSocket worker
        self.ws_worker = self.run_worker(
            self.websocket_handler(
                self.selected_spy["id"], 
                self.conversation_id
            )
        )
    
    async def websocket_handler(self, spy_id: str, conversation_id: Optional[str] = None) -> None:
        """Handle WebSocket connection and messages"""
        try:
            # Connect to WebSocket
            ws = await self.api_client.connect_websocket(spy_id, conversation_id)
            
            # Process messages
            async for message in ws:
                try:
                    data = json.loads(message)
                    message_type = data.get("type")
                    
                    if message_type == "typing":
                        # Show typing indicator
                        chat_window = self.query_one(ChatWindow)
                        chat_window.show_typing()
                    elif message_type == "response":
                        # Hide typing indicator and add response
                        chat_window = self.query_one(ChatWindow)
                        chat_window.hide_typing()
                        chat_window.add_message(data["response"], is_user=False)
                    elif message_type == "system":
                        # Show system message
                        self.show_system_message(data["content"])
                    elif message_type == "error":
                        # Show error message
                        self.show_error(data["content"])
                except Exception as e:
                    self.show_error(f"Error processing WebSocket message: {str(e)}")
                    
        except Exception as e:
            self.show_error(f"WebSocket error: {str(e)}")
    
    def show_system_message(self, message: str) -> None:
        """Show a system message"""
        chat_window = self.query_one(ChatWindow)
        system_message = Static(message, classes="system-message")
        chat_window.mount(system_message)
        chat_window.scroll_end(animate=False)
    
    def show_error(self, message: str) -> None:
        """Show an error message"""
        chat_window = self.query_one(ChatWindow)
        error_message = Static(message, classes="error-message")
        chat_window.mount(error_message)
        chat_window.scroll_end(animate=False)
    
    async def action_quit(self) -> None:
        """Quit the application"""
        logger.info("Shutting down application")
        # Close API client connections
        await self.api_client.close()
        self.exit()
        
    def action_select_focused_spy(self) -> None:
        """Select the currently focused spy"""
        print("ENTER KEY PRESSED IN MAIN APP")
        logger.debug("Enter key pressed in main app")
        
        # If we're in the spy selection phase, find the focused button
        if not self.selected_spy:
            try:
                spy_selector = self.query_one("#spy-selector")
                if hasattr(spy_selector, "action_select_focused"):
                    print("DELEGATING TO SPY SELECTOR'S ACTION_SELECT_FOCUSED")
                    logger.debug("Delegating to spy selector's action_select_focused")
                    spy_selector.action_select_focused()
                else:
                    print("SPY SELECTOR DOESN'T HAVE ACTION_SELECT_FOCUSED METHOD")
                    logger.warning("SpySelector doesn't have action_select_focused method")
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
        """Toggle between chat and debrief modes"""
        if self.chat_mode == "chat":
            self.chat_mode = "debrief"
            logger.info("Switched to debrief mode")
        else:
            self.chat_mode = "chat"
            logger.info("Switched to chat mode")
            
    def action_show_help(self) -> None:
        """Show help information"""
        help_text = """
        Spy Command Console - Keyboard Shortcuts
        
        Ctrl+Q: Quit the application
        Ctrl+S: Send the current message
        Ctrl+C: Clear the input field
        Ctrl+R: Toggle between chat and debrief modes
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
