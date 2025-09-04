"""
Engine package for the Chronicle Engine.

This package contains the core game engine components including:
- GameEngine: Main game loop and state management
- Agents: AI agents for NPCs and game master
- Processor: Message processing utilities
"""

from .game_engine import GameEngine
from .agents import GameMasterAgent, NPCCatalog
from .processor import summarize_old_messages, filter_sensitive_messages

__all__ = [
    'GameEngine',
    'GameMasterAgent',
    'NPCCatalog',
    'summarize_old_messages',
    'filter_sensitive_messages'
]
