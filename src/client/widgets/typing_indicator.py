"""
Typing indicator widget for the Spy Agency CLI application.

This module contains the TypingIndicator widget, which displays an animated
indicator when the agent is typing.
"""

import asyncio
from typing import Optional

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widgets import Static


class TypingIndicator(Static):
    """
    Widget for displaying a typing indicator.
    
    This widget shows an animated indicator when the agent is typing.
    """
    
    DEFAULT_CSS = """
    TypingIndicator {
        height: auto;
        padding: 0 1;
        color: $typing_indicator;
        opacity: 0;
        transition: opacity 300ms ease;
    }
    
    TypingIndicator.visible {
        opacity: 1;
    }
    """
    
    visible = reactive(False)
    agent_name = reactive("Agent")
    
    def __init__(
        self,
        agent_name: str = "Agent",
        *args,
        **kwargs,
    ):
        """
        Initialize a new typing indicator.
        
        Args:
            agent_name: The name of the agent
            *args: Additional positional arguments for the parent class
            **kwargs: Additional keyword arguments for the parent class
        """
        super().__init__(*args, **kwargs)
        self.agent_name = agent_name
        self._animation_task: Optional[asyncio.Task] = None
        self._dots = "..."
        self._dot_index = 0
        
    def compose(self) -> ComposeResult:
        """Define the components of the typing indicator."""
        yield Static(f"{self.agent_name} is typing", id="typing-text")
        
    def on_mount(self) -> None:
        """Handle the mount event."""
        # Hide the indicator initially
        self.visible = False
        
    def show(self) -> None:
        """Show the typing indicator."""
        self.visible = True
        
        # Start the animation if it's not already running
        if self._animation_task is None or self._animation_task.done():
            self._animation_task = asyncio.create_task(self._animate())
            
    def hide(self) -> None:
        """Hide the typing indicator."""
        self.visible = False
        
        # Stop the animation
        if self._animation_task is not None and not self._animation_task.done():
            self._animation_task.cancel()
            self._animation_task = None
            
    async def _animate(self) -> None:
        """Animate the typing indicator dots."""
        try:
            while self.visible:
                # Update the dots
                self._dot_index = (self._dot_index + 1) % 4
                dots = "." * self._dot_index if self._dot_index > 0 else "..."
                
                # Update the text
                typing_text = self.query_one("#typing-text", Static)
                typing_text.update(f"{self.agent_name} is typing{dots}")
                
                # Wait for the next frame
                await asyncio.sleep(0.5)
                
        except asyncio.CancelledError:
            # Task was cancelled, exit gracefully
            pass
            
    def watch_visible(self, visible: bool) -> None:
        """
        Watch for changes to the visible state.
        
        Args:
            visible: The new visible state
        """
        if visible:
            self.add_class("visible")
        else:
            self.remove_class("visible")
            
    def watch_agent_name(self, agent_name: str) -> None:
        """
        Watch for changes to the agent name.
        
        Args:
            agent_name: The new agent name
        """
        # Update the text
        typing_text = self.query_one("#typing-text", Static)
        typing_text.update(f"{agent_name} is typing{self._dots}")
