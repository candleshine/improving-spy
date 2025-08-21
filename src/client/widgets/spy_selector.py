from textual.widgets import ListView, ListItem
from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Label, Static
from typing import List, Dict, Any, Callable


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
    """Widget for selecting a spy agent"""
    
    def __init__(self, spies: List[Dict[str, Any]], on_select: Callable[[Dict[str, Any]], None]):
        super().__init__()
        self.spies = spies
        self.on_select = on_select
        
    def compose(self) -> ComposeResult:
        yield Label("🔍 SELECT AGENT", classes="section-title")
        yield ListView(id="spy-list", classes="spy-list")
    
    def on_mount(self) -> None:
        """Add spy items to the list after the ListView is mounted"""
        spy_list = self.query_one("#spy-list")
        for spy in self.spies:
            spy_list.append(SpyListItem(spy))
        
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle spy selection"""
        spy_item = event.item
        if isinstance(spy_item, SpyListItem):
            self.on_select(spy_item.spy_data)
