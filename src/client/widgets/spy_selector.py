import logging
import os
from typing import List, Dict, Any

from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import ListView, ListItem, Label, Static
from textual.message import Message

# Set up a direct debug file
DEBUG_FILE = os.path.expanduser("~/.spy_debug.log")

def debug_log(message: str):
    """Write a debug message directly to a file"""
    with open(DEBUG_FILE, "a") as f:
        f.write(f"{message}\n")

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
        self.classes = "spy-item"
        print(f"SpyListItem initialized with data: {spy_data}")
    
    def compose(self) -> ComposeResult:
        """Create the visual representation of the spy list item"""
        # Get only the codename
        codename = self.spy_data.get("codename", "Unknown")
        spy_id = self.spy_data.get("id", "unknown")
        
        debug_log(f"[SPY LIST ITEM] Composing item: codename='{codename}'")
        
        # Just show the codename
        name_label = Label(codename, classes="spy-name", id=f"name-{spy_id[:4]}")
        
        debug_log(f"[SPY LIST WIDGET] Created label: {name_label}")
        
        # Only yield the codename label
        yield name_label
            
        debug_log(f"[SPY LIST ITEM] Composition complete for {codename}")

class SpySelector(Static):
    """A widget for selecting a spy agent"""
    
    def __init__(self, spies: List[Dict[str, Any]] = None, id: str = None):
        super().__init__(id=id)
        self.logger = logging.getLogger(__name__)
        self.logger.debug(f"[SpySelector] Initializing with ID: {id}")
        
        # Initialize state
        self._spies = []
        self._pending_spies = []
        self.selected_index = 0
        self._list_view = None
        self._is_mounted = False
        
        # Store initial spies for after mount
        if spies:
            self._pending_spies = spies
    
    def compose(self) -> ComposeResult:
        """Create child widgets for the selector."""
        self.logger.debug("[SpySelector] Composing widget")
        print("\n\n[DEBUG] SpySelector.compose called")
        
        # Create title
        yield Label("SELECT AGENT (↑/↓ to navigate, Enter to select)", classes="section-title")
        
        # Create container for the list
        with Container(id="spy-list-container"):
            # Create the ListView with an ID for styling and reference
            self._list_view = ListView(id="spy-list", classes="spy-list")
            print(f"[DEBUG] Created ListView: {self._list_view}")
            yield self._list_view
            
        self.logger.debug(f"[SpySelector] Composition complete, list_view: {self._list_view}")
        print(f"[DEBUG] SpySelector.compose complete, list_view: {self._list_view}")
    
    def on_mount(self) -> None:
        """Handle widget mounting"""
        self._is_mounted = True
        self.logger.debug("[SpySelector] Widget mounted")
        
        # Apply pending spies if we have any
        if self._pending_spies:
            self.logger.debug(f"[SpySelector] Applying {len(self._pending_spies)} pending spies")
            self._spies = self._pending_spies
            self._pending_spies = []
            self._update_list_view()
    
    @property
    def spies(self) -> List[Dict[str, Any]]:
        """Get the current list of spies"""
        return self._spies
        
    @spies.setter
    def spies(self, value: List[Dict[str, Any]]) -> None:
        """Set the list of spies"""
        if not self._is_mounted:
            # Store for later if we're not mounted yet
            self.logger.debug(f"[SpySelector] Storing {len(value)} spies for after mount")
            self._pending_spies = value
            return
            
        # Otherwise update directly
        self.update_spies(value)
    
    def update_spies(self, spies: List[Dict[str, Any]]) -> None:
        """Update the list of spies"""
        if not isinstance(spies, list):
            self.logger.error(f"[SpySelector] Expected list of spies, got {type(spies)}")
            return
            
        self.logger.debug(f"[SpySelector] Updating with {len(spies)} spies")
        print(f"\n\n[DEBUG] SpySelector.update_spies called with {len(spies)} spies:")
        for spy in spies:
            print(f"Spy: {spy}")
        self._spies = spies
        
        # Update the list view
        self._update_list_view()
    
    def _update_list_view(self) -> None:
        """Update the list view with current spies"""
        # Make sure we have a valid list view reference
        if not self._list_view:
            try:
                # Try to find the ListView directly
                self._list_view = self.query_one("#spy-list", ListView)
                self.logger.debug(f"[SpySelector] Found ListView: {self._list_view}")
                debug_log(f"[SpySelector] Found ListView: {self._list_view}")
            except Exception as e:
                self.logger.error(f"[SpySelector] Cannot update: No list view available: {e}")
                debug_log(f"[SpySelector] ERROR: No list view available: {e}")
                return
            
        try:
            debug_log(f"\n\n[SPY LIST CONTENT] Updating with {len(self._spies)} spies:")
            # Log the actual spy data for debugging
            for i, spy in enumerate(self._spies):
                codename = spy.get('codename', 'Unknown')
                spy_id = spy.get('id', 'unknown')
                name = spy.get('name', '')
                debug_log(f"[SPY LIST CONTENT] Spy #{i}: codename='{codename}', id='{spy_id}', name='{name}'")
            
            # Clear existing items
            self._list_view.clear()
            debug_log("[SpySelector] Cleared existing items")
            
            # Add new items
            if not self._spies:
                self.logger.warning("[SpySelector] No spies data to display")
                # Add a placeholder item
                placeholder = ListItem(Label("No spies available", classes="spy-placeholder"))
                self._list_view.append(placeholder)
                return
                
            for i, spy in enumerate(self._spies):
                try:
                    codename = spy.get('codename', 'Unknown')
                    self.logger.debug(f"[SpySelector] Creating item for spy: {codename}")
                    item = SpyListItem(spy)
                    self._list_view.append(item)
                    self.logger.debug(f"[SpySelector] Added spy #{i}: {codename}")
                except Exception as e:
                    self.logger.error(f"[SpySelector] Error creating spy list item: {e}", exc_info=True)
            
            # Log the number of children
            self.logger.debug(f"[SpySelector] List view now has {len(self._list_view.children)} items")
            
            # Update selection
            if self._list_view.children:
                self.selected_index = 0
                self.highlight_selected()
                self.logger.debug("[SpySelector] Updated selection")
            else:
                self.logger.warning("[SpySelector] No items in list view after update")
                
        except Exception as e:
            self.logger.error(f"[SpySelector] Error updating list view: {e}", exc_info=True)
    
    def highlight_selected(self) -> None:
        """Highlight the currently selected spy in the list"""
        # Make sure we have a valid list view reference
        if not self._list_view:
            try:
                self._list_view = self.query_one("#spy-list", ListView)
                self.logger.debug(f"[SpySelector] Found ListView for highlighting: {self._list_view}")
            except Exception as e:
                self.logger.error(f"[SpySelector] Cannot highlight: No list view available: {e}")
                return
                
        if not self._list_view or not self._list_view.children:
            self.logger.debug("[SpySelector] No list view or children to highlight")
            return
            
        # Ensure the selected index is valid
        if self.selected_index < 0:
            self.selected_index = 0
        if self.selected_index >= len(self._list_view.children):
            self.selected_index = len(self._list_view.children) - 1
            
        # Remove selection from all items
        for i, item in enumerate(self._list_view.children):
            if "selected" in item.classes:
                item.remove_class("selected")
                
        # Add selection to the current item
        if self._list_view.children:
            try:
                self._list_view.children[self.selected_index].add_class("selected")
                self.logger.debug(f"[SpySelector] Selected item {self.selected_index}")
            except Exception as e:
                self.logger.error(f"[SpySelector] Error highlighting item: {e}")
    
    def _debug_widget_hierarchy(self, widget=None, level=0) -> None:
        """Log the widget hierarchy for debugging"""
        if widget is None:
            widget = self.app
        
        indent = '  ' * level
        widget_id = f' id={widget.id}' if hasattr(widget, 'id') and widget.id else ''
        widget_classes = f' classes={widget.classes}' if hasattr(widget, 'classes') and widget.classes else ''
        widget_type = widget.__class__.__name__
        
        self.logger.debug(f"{indent}{widget_type}{widget_id}{widget_classes}")
        
        if hasattr(widget, 'children'):
            for child in widget.children:
                self._debug_widget_hierarchy(child, level + 1)
    
    # This method was removed as it's a duplicate of the on_mount method above
            
    def _update_list_view_after_mount(self) -> None:
        """Update the list view after the widget has been mounted"""
        self.logger.debug("[SpySelector] Updating list view after mount")
        
        # Get the ListView directly from the children
        try:
            # Try to find the ListView in our children
            list_view = None
            for child in self.children:
                if isinstance(child, Container) and child.id == "spy-list-container":
                    for grandchild in child.children:
                        if isinstance(grandchild, ListView) and grandchild.id == "spy-list":
                            list_view = grandchild
                            break
                    break
                elif isinstance(child, ListView) and child.id == "spy-list":
                    list_view = child
                    break
            
            if list_view:
                self.logger.debug(f"[SpySelector] Found ListView after mount: {list_view}")
                self._list_view = list_view
                self._update_list_view()
            else:
                self.logger.error("[SpySelector] Could not find ListView after mount")
        except Exception as e:
            self.logger.error(f"[SpySelector] Error finding ListView after mount: {e}", exc_info=True)
        
        # Process any pending spies
        if self._pending_spies is not None:
            self.logger.debug(f"[SpySelector] Processing {len(self._pending_spies)} pending spies")
            spies = self._pending_spies
            self._pending_spies = None
            self.spies = spies
        elif self.spies:
            self.logger.debug(f"[SpySelector] Updating with {len(self.spies)} existing spies")
            self._update_list_view()
        
        # Set focus to the list for keyboard navigation
        try:
            self._list_view.focus()
            self.logger.debug("[SpySelector] Successfully focused spy list")
        except Exception as e:
            self.logger.error(f"[SpySelector] Failed to focus spy list: {e}", exc_info=True)
    
    # This method was removed as it's a duplicate of the highlight_selected method above
    
    def select_next(self) -> None:
        """Select the next spy in the list"""
        # Make sure we have a valid list view reference
        if not self._list_view:
            try:
                self._list_view = self.query_one("#spy-list", ListView)
            except Exception as e:
                self.logger.error(f"[SpySelector] Cannot select next: No list view available: {e}")
                return
                
        if not self._list_view or not self._list_view.children:
            return
            
        self.selected_index = (self.selected_index + 1) % len(self._list_view.children)
        self.highlight_selected()
        
    def select_previous(self) -> None:
        """Select the previous spy in the list"""
        # Make sure we have a valid list view reference
        if not self._list_view:
            try:
                self._list_view = self.query_one("#spy-list", ListView)
            except Exception as e:
                self.logger.error(f"[SpySelector] Cannot select previous: No list view available: {e}")
                return
                
        if not self._list_view or not self._list_view.children:
            return
            
        self.selected_index = (self.selected_index - 1) % len(self._list_view.children)
        self.highlight_selected()
        
    def select_current(self) -> None:
        """Select the currently highlighted spy"""
        # Make sure we have a valid list view reference
        if not self._list_view:
            try:
                self._list_view = self.query_one("#spy-list", ListView)
            except Exception as e:
                self.logger.error(f"[SpySelector] Cannot select current: No list view available: {e}")
                return
                
        if not self._list_view or not self._list_view.children:
            return
            
        try:
            selected_item = self._list_view.children[self.selected_index]
            if hasattr(selected_item, 'spy_data'):
                self.post_message(SpySelected(selected_item.spy_data))
                self.logger.debug(f"[SpySelector] Selected spy: {selected_item.spy_data.get('codename', 'unknown')}")
        except IndexError:
            self.logger.error(f"[SpySelector] Invalid selected_index: {self.selected_index}")
        except Exception as e:
            self.logger.error(f"[SpySelector] Error selecting current spy: {e}", exc_info=True)
    
    def on_key(self, event) -> None:
        """Handle key events for navigation"""
        # Make sure we have a valid list view reference
        if not self._list_view:
            try:
                self._list_view = self.query_one("#spy-list", ListView)
            except Exception as e:
                self.logger.error(f"[SpySelector] Cannot handle key: No list view available: {e}")
                return
                
        if event.key == "down":
            self.select_next()
            event.prevent_default()
        elif event.key == "up":
            self.select_previous()
            event.prevent_default()
        elif event.key == "enter":
            self.select_current()
            event.prevent_default()
        elif event.key == "pageup":
            if self._list_view and hasattr(self._list_view, 'page_up'):
                self._list_view.page_up()
                event.prevent_default()
        elif event.key == "pagedown":
            if self._list_view and hasattr(self._list_view, 'page_down'):
                self._list_view.page_down()
                event.prevent_default()
    
    def action_select_focused(self) -> None:
        """Handle Enter key press on the currently focused spy"""
        self.logger.debug("action_select_focused called")
        self.select_current()
    
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle mouse click on a spy"""
        try:
            self.logger.debug(f"on_list_view_selected called with item: {event.item}")
            if not self._list_view or not self._list_view.children:
                return
                
            # Find the index of the clicked item
            for i, item in enumerate(self._list_view.children):
                if item == event.item and hasattr(item, 'spy_data'):
                    self.selected_index = i
                    self.highlight_selected()
                    self.post_message(SpySelected(item.spy_data))
                    self.logger.debug(f"Selected spy via click: {item.spy_data.get('codename', 'unknown')}")
                    break
        except Exception as e:
            self.logger.error(f"Error handling list view selection: {e}", exc_info=True)
