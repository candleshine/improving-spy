import logging
from typing import List, Dict, Any

from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import ListView, ListItem, Label, Static
from textual.message import Message

class SpySelected(Message):
    """Message sent when a spy is selected."""
    
    def __init__(self, spy_data: Dict[str, Any]) -> None:
        self.spy_data = spy_data
        super().__init__()

class SpyListItem(ListItem):
    """A list item representing a spy agent"""
    
    def __init__(self, spy_data: Dict[str, Any]):
        super().__init__()
        self.spy_data = spy_data
        # Use different variable names to avoid property conflicts
        self._spy_id = spy_data["id"]
        self._spy_name = spy_data["name"]
        self._spy_codename = spy_data["codename"]
        
    def compose(self) -> ComposeResult:
        # Create avatar from codename abbreviation (e.g., "SV" for Shadow Viper)
        abbrev = "".join([word[0] for word in self._spy_codename.split() if word])
        
        yield Container(
            Label(f"[{abbrev}]", classes="spy-avatar"),
            Label(f"{self._spy_name}", classes="spy-name"),
            id=f"spy-{self._spy_id}"
        )

class SpySelector(Static):
    """A widget for selecting a spy agent"""
    
    def __init__(self, spies: List[Dict[str, Any]], id: str = None):
        super().__init__(id=id)
        self.spies = spies
        self.selected_spy = None
        self.logger = logging.getLogger(__name__)
        self.logger.debug(f"Initialized SpySelector with ID: {self.id}")
        
    def compose(self) -> ComposeResult:
        yield Label(" SELECT AGENT", classes="section-title")
        yield ListView(id="spy-list", classes="spy-list")
    
    def on_mount(self) -> None:
        """Add spy items to the list after the ListView is mounted"""
        spy_list = self.query_one("#spy-list")
        for spy in self.spies:
            spy_list.append(SpyListItem(spy))
        
    def action_select_focused(self) -> None:
        """Handle Enter key press on the currently focused spy"""
        self.logger.debug("action_select_focused called")
        spy_list = self.query_one("#spy-list")
        if spy_list.index is not None and spy_list.index < len(self.spies):
            selected_spy = self.spies[spy_list.index]
            self.logger.debug(f"Selected spy: {selected_spy}")
            self.post_message(SpySelected(selected_spy))
            
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle mouse click on a spy"""
        self.logger.debug(f"on_list_view_selected called with item: {event.item}")
        if hasattr(event.item, 'spy_data'):
            selected_spy = event.item.spy_data
            self.logger.debug(f"Selected spy: {selected_spy}")
            self.post_message(SpySelected(selected_spy))
