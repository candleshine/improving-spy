"""
Chat window widget for the Spy Agency CLI application.

This module contains the ChatWindow widget, which displays messages
from the user and agent in a scrollable window.
"""

from datetime import datetime
from typing import List, Optional, Union

from rich.markdown import Markdown
from rich.text import Text
from textual.binding import Binding
from textual.containers import ScrollableContainer
from textual.reactive import reactive
from textual.widgets import Static

from src.client.config import (
    COLORS,
    MAX_MESSAGES_DISPLAYED,
    MESSAGE_TIMESTAMP_FORMAT,
    USER_PREFERENCES,
)
from src.client.logger import logger
from src.client.websocket.protocol import (
    ChatMessage,
    Message,
    MessageType,
    NarrativeMessage,
    SystemMessage,
    TypingMessage,
)


class WindowChatMessage:
    """
    Represents a message in the chat window.
    
    This class is used to store and format messages for display in the chat window.
    """
    
    def __init__(
        self,
        content: str,
        sender: str,
        timestamp: datetime,
        message_id: str,
        is_markdown: bool = False,
        is_system: bool = False,
        is_error: bool = False,
        is_choice: bool = False,
    ):
        """
        Initialize a new chat message.
        
        Args:
            content: The message content
            sender: The sender of the message (user, agent name, or "System")
            timestamp: The timestamp of the message
            message_id: The unique identifier for the message
            is_markdown: Whether the message content is formatted as Markdown
            is_system: Whether the message is a system message
            is_error: Whether the message is an error message
        """
        self.content = content
        self.sender = sender
        self.timestamp = timestamp
        self.message_id = message_id
        self.is_markdown = is_markdown
        self.is_system = is_system
        self.is_error = is_error
        self.is_choice = is_choice
        
    def format_timestamp(self) -> str:
        """Format the timestamp for display."""
        return self.timestamp.strftime(MESSAGE_TIMESTAMP_FORMAT)
        
    def get_display_text(self) -> Union[Text, Markdown]:
        """Get the formatted text for display in the chat window."""
        if self.is_markdown:
            return Markdown(self.content)
            
        text = Text(self.content)
        
        if self.is_system:
            text.stylize("italic")
            
        if self.is_error:
            text.stylize(f"bold {COLORS['accent']}")
            
        return text

    def get_formatted_message(self) -> str:
        """Get the fully formatted message for display in the chat window."""
        timestamp = self.format_timestamp()
        
        if self.is_system:
            if self.is_error:
                return f"[{timestamp}] [red]{self.content}[/red]"
            else:
                return f"[{timestamp}] [dim]{self.content}[/dim]"
        
        if self.is_choice:
            # Apply special styling for choice messages
            return f"[{timestamp}] [bold blue]CHOICES:[/bold blue]\n{self.content}"
        
        sender_color = COLORS.get(self.sender, "cyan")
        sender_display = f"[{sender_color}]{self.sender}[/{sender_color}]"
        
        if self.is_markdown:
            return f"[{timestamp}] {sender_display}:\n{self.content}"
        else:
            return f"[{timestamp}] {sender_display}: {self.content}"


class ChatWindow(ScrollableContainer):
    """
    Widget for displaying chat messages.
    
    This widget displays messages from the user and agent in a scrollable window.
    """
    
    DEFAULT_CSS = """
    ChatWindow {
        height: 90%;
        border: solid $primary;
        padding: 1;
        background: $background;
    }
    
    ChatWindow > Static {
        margin-bottom: 1;
    }
    
    .user-message {
        color: $secondary;
        margin-right: 2;
    }

    .agent-message {
        color: $primary;
    }

    .system-message {
        color: $success;
        text-style: italic;
    }
    
    .error-message {
        color: $accent;
        text-style: bold;
    }
    
    .narrative-message {
        color: $warning;
        text-style: italic bold;
        border-left: thick $warning;
        padding-left: 1;
    }
    
    .timestamp {
        color: $foreground 50%;
        text-style: dim;
    }
    """
    
    BINDINGS = [
        Binding("ctrl+home", "scroll_home", "Scroll to top"),
        Binding("ctrl+end", "scroll_end", "Scroll to bottom"),
        Binding("page_up", "page_up", "Page up"),
        Binding("page_down", "page_down", "Page down"),
    ]
    
    messages = reactive(list)
    typing_indicator_visible = reactive(False)
    
    def __init__(
        self,
        *args,
        **kwargs,
    ):
        """
        Initialize a new chat window.
        
        Args:
            *args: Additional positional arguments for the parent class
            **kwargs: Additional keyword arguments for the parent class
        """
        super().__init__(*args, **kwargs)
        self.messages: List[WindowChatMessage] = []
        self.typing_indicator_visible = False
        
    def on_mount(self) -> None:
        """Handle the mount event."""
        # Add a welcome message
        self.add_system_message(
            "Connected. Type a message to begin."
        )
        
    def add_message(self, message: WindowChatMessage) -> None:
        """
        Add a message to the chat window.
        
        Args:
            message: The message to add
        """
        self.messages.append(message)
        
        # Limit the number of messages displayed
        if len(self.messages) > MAX_MESSAGES_DISPLAYED:
            self.messages = self.messages[-MAX_MESSAGES_DISPLAYED:]
            
        self._update_display()
        
    def add_user_message(self, content: str) -> None:
        """
        Add a user message to the chat window.
        
        Args:
            content: The message content
        """
        message = WindowChatMessage(
            content=content,
            sender="You",
            timestamp=datetime.now(),
            message_id=f"user-{len(self.messages)}",
        )
        
        self.add_message(message)
        
        
    def add_system_message(self, content: str, is_error: bool = False) -> None:
        """
        Add a system message to the chat window.
        
        Args:
            content: The message content
            is_error: Whether the message is an error message
        """
        message = WindowChatMessage(
            content=content,
            sender="System",
            timestamp=datetime.now(),
            message_id=f"system-{len(self.messages)}",
            is_system=True,
            is_error=is_error,
        )
        
        self.add_message(message)
        
    def add_error_message(self, content: str) -> None:
        """
        Add an error message to the chat window.
        
        Args:
            content: The message content
        """
        self.add_system_message(content, is_error=True)
        
    def show_typing_indicator(self) -> None:
        """Show the typing indicator."""
        self.typing_indicator_visible = True
        self._update_display()
        
    def hide_typing_indicator(self) -> None:
        """Hide the typing indicator."""
        self.typing_indicator_visible = False
        self._update_display()
        
    def clear(self) -> None:
        """Clear all messages from the chat window."""
        self.messages = []
        self._update_display()
        
    def _update_display(self) -> None:
        """Update the display with the current messages."""
        # Check if the widget is mounted before attempting to update the display
        if not self.is_mounted:
            return
            
        # Remove all existing widgets
        self.remove_children()
        
        # Add each message as a Static widget
        for message in self.messages:
            # Create the message widget
            message_widget = Static()
            
            # Set the appropriate CSS class
            if message.is_system and message.sender == "Narrative":
                message_widget.add_class("narrative-message")
            elif message.is_system:
                message_widget.add_class("system-message")
            elif message.is_error:
                message_widget.add_class("error-message")
            elif message.sender == "You":
                message_widget.add_class("user-message")
            else:
                message_widget.add_class("agent-message")
                
            # Format the message
            sender_prefix = f"{message.sender}: " if not message.is_system else ""
            timestamp_suffix = f" [{message.format_timestamp()}]" if USER_PREFERENCES["show_timestamps"] else ""
            
            # Set the message content
            if message.is_markdown:
                # For markdown content, we can't concatenate with Text objects
                # Instead, create a formatted string and use Markdown directly
                formatted_content = f"{sender_prefix}{message.content}{timestamp_suffix}"
                message_widget.update(Markdown(formatted_content))
            else:
                # For text content, we can concatenate Text objects
                message_widget.update(
                    Text(f"{sender_prefix}", style="bold") + 
                    message.get_display_text() +
                    Text(timestamp_suffix, style="dim")
                )
                
            # Add the message widget to the container
            try:
                self.mount(message_widget)
            except Exception:
                # If mounting fails, just skip it
                pass
            
        # Add the typing indicator if visible
        if self.typing_indicator_visible:
            typing_widget = Static("Agent is typing...", classes="typing-indicator")
            try:
                self.mount(typing_widget)
            except Exception:
                # If mounting fails, just skip it
                pass
            
        # Scroll to the bottom
        try:
            self.scroll_end()
        except Exception:
            # If scrolling fails, just skip it
            pass
        
    def action_scroll_home(self) -> None:
        """Scroll to the top of the chat window."""
        self.scroll_home(animate=False)
        
    def action_scroll_end(self) -> None:
        """Scroll to the bottom of the chat window."""
        self.scroll_end(animate=False)
        
    def action_page_up(self) -> None:
        """Scroll up one page."""
        self.scroll_up(animate=False)
        
    def action_page_down(self) -> None:
        """Scroll down one page."""
        self.scroll_down(animate=False)
        
    def handle_websocket_message(self, message: Union[ChatMessage, SystemMessage, TypingMessage, NarrativeMessage, Message]) -> None:
        """
        Handle a message from the WebSocket connection.
        
        Args:
            message: The message to handle
        """
        logger.info(f"DISPLAYING MESSAGE: type={message.type}, message_id={message.message_id}")
        
        if message.type == MessageType.CHAT:
            content = message.payload.get("content", "")
            sender = message.payload.get("sender", "Agent")
            is_markdown = message.payload.get("format", "text") == "markdown"
            
            logger.info(f"Processing chat message: sender={sender}, is_markdown={is_markdown}")
            logger.debug(f"Chat message content: {content[:100]}{'...' if len(content) > 100 else ''}")
            
            message_obj = WindowChatMessage(
                content=content,
                sender=sender,
                timestamp=datetime.now(),
                message_id=message.message_id or f"agent-{len(self.messages)}",
                is_markdown=is_markdown,
            )
            
            logger.info(f"Adding chat message to display: message_id={message_obj.message_id}")
            self.add_message(message_obj)
            
        elif message.type == MessageType.SYSTEM:
            content = message.payload.get("content", "")
            level = message.payload.get("level", "info")
            
            logger.info(f"Processing system message: level={level}")
            logger.debug(f"System message content: {content}")
            
            if level == "error":
                logger.info("Adding system error message to display")
                self.add_error_message(content)
            else:
                logger.info("Adding system info message to display")
                self.add_system_message(content)
                
        elif message.type == MessageType.NARRATIVE:
            # Extract content from either payload.content or text field
            content = ""
            if hasattr(message, "payload") and isinstance(message.payload, dict):
                content = message.payload.get("content", "")
                if not content and "text" in message.payload:
                    content = message.payload.get("text", "")
            elif hasattr(message, "text"):
                content = message.text
                
            # Check for malformed JSON in content (like embedded JSON responses)
            if content and (content.startswith("</think>") or "\"type\":\"response\"" in content):
                logger.info("Detected malformed JSON in narrative message, cleaning up")
                
                # Remove any </think> tags
                if "</think>" in content:
                    content = content.split("</think>", 1)[1].strip()
                
                # Try to extract the actual message content from embedded JSON
                try:
                    import json
                    import re
                    
                    # Find JSON-like structure in the content
                    json_match = re.search(r'\{.*\}', content)
                    if json_match:
                        json_str = json_match.group(0)
                        json_data = json.loads(json_str)
                        
                        # Extract the actual content from the embedded JSON
                        if isinstance(json_data, dict):
                            if "payload" in json_data and isinstance(json_data["payload"], dict):
                                if "content" in json_data["payload"]:
                                    content = json_data["payload"]["content"]
                                    logger.info(f"Extracted content from embedded JSON: {content[:50]}...")
                except Exception as e:
                    logger.error(f"Error parsing embedded JSON in narrative message: {e}")
                    # Keep the original content if parsing fails
                
            # Default to markdown for narrative messages for better formatting
            is_markdown = True
            if hasattr(message, "payload") and isinstance(message.payload, dict):
                is_markdown = message.payload.get("format", "markdown") == "markdown"
            
            logger.info(f"Processing narrative message: is_markdown={is_markdown}")
            logger.debug(f"Narrative message content: {content[:100]}{'...' if len(content) > 100 else ''}")
            
            message_obj = WindowChatMessage(
                content=content,
                sender="Narrative",
                timestamp=datetime.now(),
                message_id=message.message_id or f"narrative-{len(self.messages)}",
                is_markdown=is_markdown,
                is_system=True,  # Format as a system message for styling
            )
            
            logger.info(f"Adding narrative message to display: message_id={message_obj.message_id}")
            self.add_message(message_obj)
                
        elif message.type == MessageType.TYPING:
            status = message.payload.get("status")
            logger.info(f"Processing typing indicator: status={status}")
            
            if status == "start":
                logger.info("Showing typing indicator")
                self.show_typing_indicator()
            elif status == "stop":
                logger.info("Hiding typing indicator")
                self.hide_typing_indicator()
                
        elif message.type == MessageType.ERROR:
            content = message.payload.get("message", "An error occurred")
            logger.info("Processing error message")
            logger.debug(f"Error message content: {content}")
            logger.info("Adding error message to display")
            self.add_error_message(content)
            
        elif message.type == MessageType.CHOICE:
            options = message.payload.get("options", [])
            raw_text = message.payload.get("raw_text", "")
            
            logger.info(f"Processing choice message with {len(options)} options")
            logger.debug(f"Choice options: {options}")
            
            # Format the choices as a markdown list with numbers
            choice_text = "**Choose an option:**\n\n"
            for i, option in enumerate(options, 1):
                option_text = option.get("text", f"Option {i}")
                choice_text += f"{i}. {option_text}\n"
            
            # Add a hint about how to select options
            choice_text += "\n*Type the number to select an option*"
            
            message_obj = WindowChatMessage(
                content=choice_text,
                sender="Choices",
                timestamp=datetime.now(),
                message_id=message.message_id or f"choice-{len(self.messages)}",
                is_markdown=True,
                is_choice=True,  # Mark as a choice message for special styling
            )
            
            logger.info(f"Adding choice message to display: message_id={message_obj.message_id}")
            self.add_message(message_obj)
