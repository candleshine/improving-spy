"""
History manager for saving and loading conversation history.
"""
import os
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

import logging
import src.client.config as config


class HistoryManager:
    """Manages saving and loading of conversation history."""
    
    def __init__(self):
        """Initialize the history manager."""
        self.history_dir = config.HISTORY_DIR
        os.makedirs(self.history_dir, exist_ok=True)
        logging.debug(f"History manager initialized with directory: {self.history_dir}")
    
    def save_conversation(self, spy_id: str, conversation_id: str, messages: List[Dict[str, Any]]) -> str:
        """
        Save a conversation to disk.
        
        Args:
            spy_id: The ID of the spy
            conversation_id: The ID of the conversation
            messages: List of message objects
            
        Returns:
            Path to the saved file
        """
        # Create spy-specific directory
        spy_dir = os.path.join(self.history_dir, spy_id)
        os.makedirs(spy_dir, exist_ok=True)
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{conversation_id}_{timestamp}.json"
        filepath = os.path.join(spy_dir, filename)
        
        # Prepare data to save
        data = {
            "spy_id": spy_id,
            "conversation_id": conversation_id,
            "timestamp": time.time(),
            "date": datetime.now().isoformat(),
            "messages": messages
        }
        
        # Write to file
        try:
            with open(filepath, "w") as f:
                json.dump(data, f, indent=2)
            logging.info(f"Conversation {conversation_id} saved to {filepath}")
            return filepath
        except Exception as e:
            logging.error(f"Failed to save conversation: {str(e)}", exc_info=True)
            raise
    
    def load_conversation(self, filepath: str) -> Dict[str, Any]:
        """
        Load a conversation from disk.
        
        Args:
            filepath: Path to the conversation file
            
        Returns:
            Conversation data
        """
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
            logging.info(f"Loaded conversation from {filepath}")
            return data
        except Exception as e:
            logging.error(f"Failed to load conversation: {str(e)}", exc_info=True)
            raise
    
    def get_conversation_list(self, spy_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get a list of saved conversations.
        
        Args:
            spy_id: Optional filter by spy ID
            
        Returns:
            List of conversation metadata
        """
        conversations = []
        
        try:
            # If spy_id is provided, only look in that directory
            if spy_id:
                spy_dir = os.path.join(self.history_dir, spy_id)
                if os.path.exists(spy_dir):
                    self._scan_spy_directory(spy_dir, spy_id, conversations)
            else:
                # Scan all spy directories
                for item in os.listdir(self.history_dir):
                    spy_dir = os.path.join(self.history_dir, item)
                    if os.path.isdir(spy_dir):
                        self._scan_spy_directory(spy_dir, item, conversations)
            
            # Sort by timestamp (newest first)
            conversations.sort(key=lambda x: x["timestamp"], reverse=True)
            return conversations
            
        except Exception as e:
            logging.error(f"Failed to list conversations: {str(e)}", exc_info=True)
            return []
    
    def _scan_spy_directory(self, spy_dir: str, spy_id: str, conversations: List[Dict[str, Any]]) -> None:
        """
        Scan a spy directory for conversation files.
        
        Args:
            spy_dir: Path to the spy directory
            spy_id: ID of the spy
            conversations: List to append conversation metadata to
        """
        for filename in os.listdir(spy_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(spy_dir, filename)
                try:
                    # Read basic metadata without loading the whole file
                    with open(filepath, "r") as f:
                        data = json.load(f)
                    
                    conversations.append({
                        "spy_id": spy_id,
                        "conversation_id": data.get("conversation_id", "unknown"),
                        "timestamp": data.get("timestamp", 0),
                        "date": data.get("date", ""),
                        "message_count": len(data.get("messages", [])),
                        "filepath": filepath
                    })
                except Exception as e:
                    logging.error(f"Error reading conversation file {filepath}: {str(e)}")
    
    def delete_conversation(self, filepath: str) -> bool:
        """
        Delete a conversation file.
        
        Args:
            filepath: Path to the conversation file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            os.remove(filepath)
            logging.info(f"Deleted conversation file: {filepath}")
            return True
        except Exception as e:
            logging.error(f"Failed to delete conversation: {str(e)}", exc_info=True)
            return False
