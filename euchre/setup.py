from core.logic import ActionRouter, ActionRule
from core.net import Connection, ConnectionManager
from core.state import Deck, Game, Player, Board
from enum import Enum
from typing import Dict, List, Optional, Tuple
from euchre.rules import PlayCard, Discard, CallReneg, CallPickup, CallSuit, TrickOver, HandOver

class Phase(Enum):
    """Phases of a Euchre game."""
    SETUP = "setup"
    DEAL = "deal"
    PICKUP_CARD = "pickup_card"
    PICK_SUIT = "pick_suit"
    DISCARD = "discard"
    PLAY = "play"
    SCORE_TRICK = "score_trick"
    SCORE_GAME = "score_game"
    END_GAME = "end_game"

class EuchreDeck(Deck):
    """A deck specifically for Euchre, containing only ranks 9 through Ace."""
    RANKS = ['9', '10', 'J', 'Q', 'K', 'A']
    
    def __init__(self):
        super().__init__()
    
    def collect(self):
        """Reset the deck to its initial state with all 24 cards (6 ranks × 4 suits)."""
        self.cards = []
        for suit in self.SUITS:
            for rank in self.RANKS:
                self.cards.append(self.Card(rank, suit))
        return self

class EuchreGame(Game):
    """A game of Euchre."""
    def __init__(self, deck: EuchreDeck, players: List[Player]):
        super().__init__(deck, players)
        self.phase = Phase.SETUP
        self.score: Dict[int, int] = {1: 0, 2: 0}  # Team scores
        self.hand_score: Dict[int, int] = {1: 0, 2: 0}  # Team hand scores
        self.calling_team: Optional[int] = None
        self.renegs: List[Tuple[int, str]] = []  # (team_id, reason)
        self.current_dealer: Optional[Player] = None
        self.current_player: Optional[Player] = None
        self.blocking_on_discard: List[Player] = []
        self.trump_suit: Optional[str] = None
    
    def set_phase(self, phase: Phase):
        """Set the current game phase."""
        self.phase = phase
    
    def add_score(self, team_id: int, points: int):
        """Add points to a team's score."""
        if team_id not in self.score:
            raise ValueError(f"Invalid team ID: {team_id}")
        self.score[team_id] += points
    
    def add_reneg(self, team_id: int, reason: str):
        """Record a reneg for a team."""
        self.renegs.append((team_id, reason))
    
    def clear_renegs(self):
        """Clear all recorded renegs."""
        self.renegs.clear()
    
    def set_dealer(self, player: Player):
        """Set the current dealer."""
        self.current_dealer = player
    
    def set_current_player(self, player: Player):
        """Set the current player."""
        self.current_player = player
    
    def add_blocking_discard(self, player: Player):
        """Add a player to the list of players who must discard."""
        if player not in self.blocking_on_discard:
            self.blocking_on_discard.append(player)
    
    def remove_blocking_discard(self, player: Player):
        """Remove a player from the list of players who must discard."""
        if player in self.blocking_on_discard:
            self.blocking_on_discard.remove(player)
    
    def is_blocked(self) -> bool:
        """Check if the game is blocked waiting for discards."""
        return len(self.blocking_on_discard) > 0 

class EuchreActionRouter(ActionRouter):
    """Routes actions to their corresponding rules."""
    def __init__(self):
        super().__init__()
        self.rules: Dict[str, ActionRule] = {
            "play": PlayCard(),
            "discard": Discard(),
            "call_reneg": CallReneg(),
            "call_pickup": CallPickup(),
            "call_suit": CallSuit(),
            "trick_over": TrickOver(),
        }

class EuchreSetup:
    """Manages the setup of a Euchre game."""
    def __init__(self):
        self.connection_manager = ConnectionManager()
        self.game: Optional[EuchreGame] = None
        self.action_router = EuchreActionRouter()
        self.action_builder = EuchreActionBuilder()
    
    def add_player(self, player_id: int, connection: Connection, player: Player):
        """Add a player to the setup."""
        connection.set_action_builder(self.action_builder)
        connection.set_action_router(self.action_router)
        self.connection_manager.add_connection(player_id, connection, player)
        
        # If we have 4 players, create the game
        if len(self.connection_manager.connections) == 4:
            self._create_game()
    
    def _create_game(self):
        """Create a new Euchre game with the connected players."""
        deck = EuchreDeck()
        players = self.connection_manager.get_all_players()
        self.game = EuchreGame(deck, players)
        
        # Add faceup slots for all players
        for player in players:
            self.game.board.add_slot(player.id, Board.Slot(face_up=True))

        