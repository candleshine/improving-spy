"""
Tools for the game engine.
"""
from pydantic import BaseModel
from pydantic_ai.tools import Tool
from typing import List
import random

class RollDiceInput(BaseModel):
    """Input model for the dice rolling tool."""
    sides: int = 6
    count: int = 1

def roll_dice(sides: int = 6, count: int = 1) -> List[int]:
    """
    Roll one or more dice with the specified number of sides.
    
    Args:
        sides: Number of sides on each die (default: 6)
        count: Number of dice to roll (default: 1)
        
    Returns:
        List of dice results
    """
    return [random.randint(1, sides) for _ in range(count)]

dice_tool = Tool(
    roll_dice,
    name="roll_dice",
    description="Use this to resolve uncertain outcomes: combat, stealth, hacking, etc. Returns a list of integers.",
    strict=True
)
