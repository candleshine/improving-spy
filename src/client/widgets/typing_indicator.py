from textual.widgets import Static
from rich.text import Text
from rich.console import RenderableType


class TypingIndicator(Static):
    """Standalone typing indicator widget"""
    
    def __init__(self, spy_avatar: str):
        super().__init__()
        self.spy_avatar = spy_avatar
        self.visible = False
        
    def render(self) -> RenderableType:
        if not self.visible:
            return Text("")
        return Text(f"{self.spy_avatar} …typing…", style="green dim")
    
    def show(self) -> None:
        """Show the typing indicator"""
        self.visible = True
        self.refresh()
        
    def hide(self) -> None:
        """Hide the typing indicator"""
        self.visible = False
        self.refresh()
