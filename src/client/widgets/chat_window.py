from textual.widgets import Static
from textual.containers import ScrollableContainer
from textual.app import ComposeResult
from rich.console import RenderableType
from rich.text import Text
from rich.panel import Panel
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.table import Table
from datetime import datetime
import re
from typing import Optional

import logging


class ChatMessage(Static):
    """A single chat message in the chat window"""
    
    def __init__(
        self, 
        message: str, 
        is_user: bool = False, 
        spy_avatar: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ):
        super().__init__()
        self.message = message
        self.is_user = is_user
        self.spy_avatar = spy_avatar
        self.timestamp = timestamp or datetime.now()
        
    def _parse_message(self, message: str) -> RenderableType:
        """Parse message content for rich formatting"""
        # Check for code blocks with syntax highlighting
        code_block_pattern = r'```(\w*)\n([\s\S]*?)```'
        code_blocks = re.findall(code_block_pattern, message)
        
        if code_blocks:
            # Process message with code blocks
            parts = []
            remaining = message
            
            for lang, code in code_blocks:
                # Split at the code block
                parts_split = remaining.split(f"```{lang}\n{code}```", 1)
                
                # Add text before code block if it exists
                if parts_split[0]:
                    parts.append(Text(parts_split[0]))
                
                # Add syntax highlighted code
                lang = lang if lang else "text"  # Default to text if no language specified
                try:
                    parts.append(Syntax(code, lang, theme="monokai", line_numbers=True))
                except Exception:
                    # Fallback if language not supported
                    parts.append(Syntax(code, "text", theme="monokai"))
                
                # Update remaining text
                if len(parts_split) > 1:
                    remaining = parts_split[1]
                else:
                    remaining = ""
            
            # Add any remaining text
            if remaining:
                parts.append(Text(remaining))
                
            # Create a table to hold all parts
            table = Table.grid(padding=(0, 0))
            table.add_column()
            for part in parts:
                table.add_row(part)
            return table
            
        # Check for inline code
        elif "`" in message:
            # Process inline code formatting
            parts = []
            segments = re.split(r'(`[^`]+`)', message)
            
            for segment in segments:
                if segment.startswith('`') and segment.endswith('`'):
                    # This is inline code
                    code = segment[1:-1]
                    parts.append(Text(code, style="bold reverse"))
                else:
                    # Regular text
                    parts.append(Text(segment))
            
            # Combine all text segments
            result = Text()
            for part in parts:
                result.append(part)
            return result
            
        # Check for markdown-style formatting
        elif any(marker in message for marker in ['**', '__', '*', '_']):
            try:
                # Try to render as markdown
                return Markdown(message)
            except Exception as e:
                logging.error(f"Error rendering markdown: {str(e)}")
                # Fallback to plain text
                return Text(message)
        else:
            # Plain text
            return Text(message)
    
    def render(self) -> RenderableType:
        time_str = self.timestamp.strftime("%H:%M")
        
        if self.is_user:
            # Right-aligned user message (white text)
            message_content = self._parse_message(self.message)
            timestamp_text = Text(f"[{time_str}]", style="dim")
            panel = Panel(
                message_content,
                title="Me",
                title_align="right",
                subtitle=timestamp_text,
                subtitle_align="right",
                border_style="white",
                padding=(0, 1)
            )
            return panel
        else:
            # Left-aligned spy message (green text)
            avatar = self.spy_avatar or "??"
            message_content = self._parse_message(self.message)
            timestamp_text = Text(f"[{time_str}]", style="dim")
            panel = Panel(
                message_content,
                title=avatar,
                title_align="left",
                subtitle=timestamp_text,
                subtitle_align="left",
                border_style="green",
                padding=(0, 1)
            )
            return panel


class TypingIndicator(Static):
    """Typing indicator for the chat window"""
    
    def __init__(self, spy_avatar: str):
        super().__init__()
        self.spy_avatar = spy_avatar
        
    def render(self) -> RenderableType:
        return Text(f"{self.spy_avatar} …typing…", style="green dim")


class ChatWindow(ScrollableContainer):
    """Widget for displaying chat messages"""
    
    def __init__(self, spy_name: str, spy_avatar: str):
        super().__init__()
        self.spy_name = spy_name
        self.spy_avatar = spy_avatar
        self.typing_indicator = None
        
    def compose(self) -> ComposeResult:
        yield Static(f"CHAT WITH {self.spy_name.upper()}", classes="section-title")
        
    def add_message(self, message: str, is_user: bool = False) -> None:
        """Add a new message to the chat window"""
        # Remove typing indicator if present
        if self.typing_indicator:
            self.typing_indicator.remove()
            self.typing_indicator = None
            
        # Add the new message
        chat_message = ChatMessage(
            message=message,
            is_user=is_user,
            spy_avatar=self.spy_avatar if not is_user else None
        )
        self.mount(chat_message)
        self.scroll_end(animate=False)
        
    def show_typing(self) -> None:
        """Show the typing indicator"""
        # Remove existing typing indicator if present
        if self.typing_indicator:
            self.typing_indicator.remove()
            
        # Add new typing indicator
        self.typing_indicator = TypingIndicator(self.spy_avatar)
        self.mount(self.typing_indicator)
        self.scroll_end(animate=False)
        
    def hide_typing(self) -> None:
        """Hide the typing indicator"""
        if self.typing_indicator:
            self.typing_indicator.remove()
            self.typing_indicator = None
            
    def clear(self) -> None:
        """Clear all messages from the chat window"""
        # Remove all child widgets except the title
        for child in self.query():
            if child != self.query_one(".section-title"):
                child.remove()
        self.typing_indicator = None
