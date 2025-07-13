from core.state import Card, Deck
import websockets
import asyncio
from typing import Optional, Dict, Any

def StringToCard(card_str: str) -> Card:
    """
    Convert a string representation of a card to a Card object.
    
    Args:
        card_str: String in the format "RANK of SUIT" (e.g., "A of Hearts")
        
    Returns:
        Card object corresponding to the string representation
        
    Raises:
        ValueError: If the string format is invalid or the rank/suit is not valid
    """
    try:
        rank, _, suit = card_str.split()
        if rank not in Deck.RANKS:
            raise ValueError(f"Invalid rank: {rank}")
        if suit not in Deck.SUITS:
            raise ValueError(f"Invalid suit: {suit}")
        return Card(rank, suit)
    except ValueError as e:
        raise ValueError(f"Invalid card string format: {card_str}. Expected format: 'RANK of SUIT'") from e

async def connect_websocket(uri: str, 
                          headers: Optional[Dict[str, str]] = None,
                          timeout: float = 10.0) -> websockets.WebSocketClientProtocol:
    """
    Establish a websocket connection to a server.
    
    Args:
        uri: The websocket server URI (e.g., 'ws://localhost:8765')
        headers: Optional headers to include in the connection request
        timeout: Connection timeout in seconds
        
    Returns:
        websockets.WebSocketClientProtocol: The established websocket connection
        
    Raises:
        websockets.exceptions.InvalidStatusCode: If the server returns an invalid status code
        websockets.exceptions.InvalidMessage: If the server sends an invalid message
        asyncio.TimeoutError: If the connection times out
        ConnectionError: If the connection fails for any other reason
    """
    try:
        return await asyncio.wait_for(
            websockets.connect(uri, extra_headers=headers),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        raise asyncio.TimeoutError(f"Connection to {uri} timed out after {timeout} seconds")
    except Exception as e:
        raise ConnectionError(f"Failed to connect to {uri}: {str(e)}") 