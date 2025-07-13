from typing import Dict, List, Optional, Tuple
import websockets
from core.state import Player
from core.logic import Action, ActionBuilder, ActionRouter, ActionResult

class Connection:
    """Manages a websocket connection and processes actions."""
    def __init__(self, websocket: websockets.WebSocketServerProtocol, 
                 player: Player):
        self.websocket = websocket
        self.action_router = None
        self.action_builder = None
        self.player: Player

    def set_action_builder(self, action_builder: ActionBuilder):
        self.action_builder = action_builder

    def set_action_router(self, action_router: ActionRouter):
        self.action_router = action_router
    
    def set_connection_manager(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
    
    async def process_message(self, message: dict, board, game) -> Optional[ActionResult]:
        """
        Process a message from the websocket connection.
        
        Args:
            message: The message received from the websocket
            board: The current game board
            game: The current game state
            NoneNone
        Returns:
            Optional[ActionResult]: The result of processing the action, or None if no valid action was found
            
        Raises:
            ValueError: If the message cannot be converted to a valid action
        """
        message['caller'] = self.player.id
        
        action = self.action_builder.build(message)
        if not action:
            raise ValueError(f"No action builder found for action type: {message['action_type']}")
        
        try:
            result = self.action_router.route(action, self.connection_manager, board, game)
            return result
        except ValueError as e:
            raise ValueError(f"Failed to build action: {str(e)}")
    
    async def send_result(self, result: ActionResult):
        """Send an action result back to the client."""
        await self.websocket.send({
            'success': result.success,
            'message': result.message,
            'follow_up_actions': [
                {'name': action.name, 'payload': action.payload}
                for action in result.follow_up_actions
            ]
        })

class ConnectionManager:
    """Manages all active connections and their associated players."""
    def __init__(self):
        self.connections: Dict[int, Connection] = {}
    
    def add_connection(self, player_id: int, connection: Connection, player: Player):
        """Add a new connection and its associated player."""
        if player_id != player.id:
            raise ValueError(f"Player ID {player_id} does not match player's ID {player.id}")
        connection.set_connection_manager(self)
        self.connections[player_id] = connection
    
    def remove_connection(self, player_id: int):
        """Remove a connection and its associated player."""
        if player_id in self.connections:
            del self.connections[player_id]
    
    def get_connection(self, player_id: int) -> Optional[Connection]:
        """Get a connection by player ID."""
        if player_id in self.connections:
            return self.connections[player_id]
        return None
    
    def get_player(self, player_id: int) -> Optional[Player]:
        """Get a player by ID."""
        if player_id in self.connections:
            return self.connections[player_id].player
        return None
    
    def get_all_players(self) -> List[Player]:
        """Get all connected players."""
        return [connection.player for connection in self.connections.values()]
    
    def get_all_connections(self) -> List[Connection]:
        """Get all active connections."""
        return list(self.connections.values()) 