from typing import Dict, List, Optional
from fastapi import WebSocket
import uuid


class ConnectionManager:
    """
    WebSocket connection manager to handle multiple client connections.
    Manages active connections and broadcasting messages.
    """
    def __init__(self):
        # Map of connection_id to WebSocket instance
        self.active_connections: Dict[str, WebSocket] = {}
        # Map of spy_id to list of connection_ids
        self.spy_connections: Dict[str, List[str]] = {}
        # Map of conversation_id to list of connection_ids
        self.conversation_connections: Dict[str, List[str]] = {}

    async def connect(self, websocket: WebSocket, spy_id: Optional[str] = None, 
                     conversation_id: Optional[str] = None) -> str:
        """
        Connect a new WebSocket client and register it with the appropriate spy/conversation.
        Returns the unique connection ID.
        """
        await websocket.accept()
        connection_id = str(uuid.uuid4())
        self.active_connections[connection_id] = websocket
        
        # Register with spy if provided
        if spy_id:
            if spy_id not in self.spy_connections:
                self.spy_connections[spy_id] = []
            self.spy_connections[spy_id].append(connection_id)
        
        # Register with conversation if provided
        if conversation_id:
            if conversation_id not in self.conversation_connections:
                self.conversation_connections[conversation_id] = []
            self.conversation_connections[conversation_id].append(connection_id)
            
        return connection_id

    def disconnect(self, connection_id: str):
        """
        Disconnect a WebSocket client and remove it from all registries.
        """
        if connection_id not in self.active_connections:
            return
            
        # Remove from spy connections
        for spy_id, connections in self.spy_connections.items():
            if connection_id in connections:
                self.spy_connections[spy_id].remove(connection_id)
                # Clean up empty lists
                if not self.spy_connections[spy_id]:
                    del self.spy_connections[spy_id]
                break
        
        # Remove from conversation connections
        for conv_id, connections in self.conversation_connections.items():
            if connection_id in connections:
                self.conversation_connections[conv_id].remove(connection_id)
                # Clean up empty lists
                if not self.conversation_connections[conv_id]:
                    del self.conversation_connections[conv_id]
                break
        
        # Remove from active connections
        del self.active_connections[connection_id]

    async def send_personal_message(self, message: dict, connection_id: str):
        """
        Send a message to a specific connection.
        """
        if connection_id in self.active_connections:
            await self.active_connections[connection_id].send_json(message)

    async def broadcast_to_spy(self, message: dict, spy_id: str):
        """
        Broadcast a message to all connections for a specific spy.
        """
        if spy_id in self.spy_connections:
            for connection_id in self.spy_connections[spy_id]:
                await self.send_personal_message(message, connection_id)

    async def broadcast_to_conversation(self, message: dict, conversation_id: str):
        """
        Broadcast a message to all connections for a specific conversation.
        """
        if conversation_id in self.conversation_connections:
            for connection_id in self.conversation_connections[conversation_id]:
                await self.send_personal_message(message, connection_id)

    async def broadcast(self, message: dict):
        """
        Broadcast a message to all active connections.
        """
        for connection_id in self.active_connections:
            await self.send_personal_message(message, connection_id)


# Create a global instance of the connection manager
manager = ConnectionManager()
