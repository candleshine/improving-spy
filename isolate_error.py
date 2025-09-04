#!/usr/bin/env python3
"""
Minimal test case to isolate the 'bool' object has no attribute 'append' error.
This script creates a very simple Textual app with a MessageLog-like widget.
"""
import logging
import sys
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Static

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("isolate_error")

class SimpleLog(Static):
    """Simplified message log to isolate the issue"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Use a different name to avoid any conflicts
        self._storage = []
        logger.debug(f"Initialized SimpleLog with _storage: {type(self._storage)}")
    
    def compose(self) -> ComposeResult:
        """Nothing to compose"""
        yield Container()
    
    def add_item(self, item):
        """Add an item to the log"""
        logger.debug(f"Adding item: {item}")
        logger.debug(f"Before adding, _storage is: {type(self._storage)}")
        
        try:
            # Try to append to the storage
            self._storage.append(item)
            logger.debug(f"Successfully added item, _storage now has {len(self._storage)} items")
        except Exception as e:
            logger.error(f"Error adding item: {e}")
            logger.error(f"Type of _storage: {type(self._storage)}")
            # Try to reset the storage
            self._storage = []
            logger.debug(f"Reset _storage to empty list")
            # Try again
            try:
                self._storage.append(item)
                logger.debug(f"Successfully added item after reset")
            except Exception as e2:
                logger.error(f"Still failed after reset: {e2}")
                raise

class MinimalApp(App):
    """Minimal app to test the issue"""
    
    def compose(self) -> ComposeResult:
        self.simple_log = SimpleLog()
        yield self.simple_log
    
    def on_mount(self):
        """Test adding items"""
        logger.debug("App mounted, testing simple log")
        
        # Try adding an item
        try:
            self.simple_log.add_item("Test item 1")
            logger.debug("Successfully added first item")
            
            # Add a few more items
            self.simple_log.add_item("Test item 2")
            self.simple_log.add_item("Test item 3")
            logger.debug("Successfully added all items")
        except Exception as e:
            logger.error(f"Error in on_mount: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    app = MinimalApp()
    try:
        app.run()
    except Exception as e:
        logger.error(f"Error running app: {e}")
        import traceback
        traceback.print_exc()
