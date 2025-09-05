"""
Reconnection strategies for the WebSocket client.

This module contains the logic for reconnecting to the WebSocket server
when the connection is lost.
"""

import asyncio
import random
from typing import Callable, Optional

from src.client.config import WS_RECONNECT_BASE_DELAY, WS_RECONNECT_MAX_ATTEMPTS
from src.client.logger import logger


class ReconnectionStrategy:
    """
    Base class for reconnection strategies.
    
    This class defines the interface for reconnection strategies.
    """
    
    async def next_delay(self, attempt: int) -> float:
        """
        Calculate the delay before the next reconnection attempt.
        
        Args:
            attempt: The current reconnection attempt number
            
        Returns:
            The delay in seconds before the next reconnection attempt
        """
        raise NotImplementedError
        
    def reset(self) -> None:
        """Reset the reconnection strategy."""
        pass
        
    def should_retry(self, attempt: int) -> bool:
        """
        Determine whether to retry the connection.
        
        Args:
            attempt: The current reconnection attempt number
            
        Returns:
            True if the connection should be retried, False otherwise
        """
        raise NotImplementedError


class ExponentialBackoffStrategy(ReconnectionStrategy):
    """
    Exponential backoff reconnection strategy.
    
    This strategy increases the delay exponentially with each attempt,
    with added jitter to prevent the thundering herd problem.
    """
    
    def __init__(
        self,
        base_delay: float = WS_RECONNECT_BASE_DELAY,
        max_attempts: int = WS_RECONNECT_MAX_ATTEMPTS,
        jitter: float = 0.5,
    ):
        """
        Initialize a new exponential backoff strategy.
        
        Args:
            base_delay: The base delay in seconds
            max_attempts: The maximum number of reconnection attempts
            jitter: The maximum amount of random jitter to add to the delay
        """
        self.base_delay = base_delay
        self.max_attempts = max_attempts
        self.jitter = jitter
        
    async def next_delay(self, attempt: int) -> float:
        """
        Calculate the delay before the next reconnection attempt.
        
        Args:
            attempt: The current reconnection attempt number
            
        Returns:
            The delay in seconds before the next reconnection attempt
        """
        # Calculate the delay with exponential backoff
        delay = self.base_delay * (2 ** attempt)
        
        # Add jitter to prevent the thundering herd problem
        if self.jitter > 0:
            delay += random.random() * self.jitter
            
        return delay
        
    def should_retry(self, attempt: int) -> bool:
        """
        Determine whether to retry the connection.
        
        Args:
            attempt: The current reconnection attempt number
            
        Returns:
            True if the connection should be retried, False otherwise
        """
        return attempt < self.max_attempts


async def reconnect_with_strategy(
    connect_func: Callable[[], asyncio.Future],
    strategy: ReconnectionStrategy,
    on_attempt: Optional[Callable[[int, float], None]] = None,
    on_give_up: Optional[Callable[[], None]] = None,
) -> bool:
    """
    Attempt to reconnect using the specified strategy.
    
    Args:
        connect_func: Function to call to attempt a connection
        strategy: The reconnection strategy to use
        on_attempt: Callback for when a reconnection attempt is made
        on_give_up: Callback for when all reconnection attempts have failed
        
    Returns:
        True if the reconnection was successful, False otherwise
    """
    attempt = 0
    
    while True:
        # Check if we should retry
        if not strategy.should_retry(attempt):
            logger.error("Maximum reconnection attempts reached")
            
            # Call the on_give_up callback if provided
            if on_give_up:
                on_give_up()
                
            return False
            
        # Calculate the delay
        delay = await strategy.next_delay(attempt)
        
        # Call the on_attempt callback if provided
        if on_attempt:
            on_attempt(attempt, delay)
            
        logger.info(f"Reconnecting in {delay:.1f} seconds (attempt {attempt + 1})")
        
        # Wait for the delay
        await asyncio.sleep(delay)
        
        # Attempt to reconnect
        try:
            result = await connect_func()
            
            if result:
                logger.info("Reconnection successful")
                return True
                
        except Exception as e:
            logger.error(f"Reconnection attempt failed: {e}")
            
        # Increment the attempt counter
        attempt += 1
