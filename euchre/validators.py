from core.logic import Action, ActionValidator
from core.state import Board, Game
from core.net import ConnectionManager
from euchre.setup import Phase
from euchre.actions import Play, Discard, CallReneg, CallPickup, CallSuit, Pass

class CorrectPhase(ActionValidator):
    """Ensures actions are performed in the correct game phase."""
    def validate(self, action: Action, connection_manager: ConnectionManager, board: Board, game: Game) -> bool:
        if isinstance(action, (Play, CallReneg, TrickOver)):
            return game.phase == Phase.PLAY
        elif isinstance(action, Discard):
            return game.phase == Phase.DISCARD
        elif isinstance(action, CallPickup):
            return game.phase == Phase.PICKUP_CARD
        elif isinstance(action, CallSuit):
            return game.phase == Phase.PICK_SUIT
        elif isinstance(action, Pass):
            return game.phase in [Phase.PICKUP_CARD, Phase.PICK_SUIT]
        elif isinstance(action, TrickOver):
            return game.phase == Phase.SCORE
        elif isinstance(action, HandOver):
            return game.phase == Phase.SCORE_HAND
        elif isinstance(action, EndGame):
            return game.phase == Phase.END_GAME
        return False

class PlayersTurn(ActionValidator):
    """Ensures it is the current player's turn."""
    def validate(self, action: Action, connection_manager: ConnectionManager, board: Board, game: Game) -> bool:
        connection = connection_manager.get_connection(game.current_player.id)
        return connection is not None

class CanPass(ActionValidator):
    """Ensures the dealer can pass."""
    def validate(self, action: Action, connection_manager: ConnectionManager, board: Board, game: Game) -> bool:
        # If everyone passes, the dealer is stuck picking the suit
        return not (game.current_dealer == game.get_player(action.payload['player_id']) and game.phase == Phase.PICK_SUIT)

class BlockedOnPlayerDiscard(ActionValidator):
    """Ensures there are no players blocking on discard."""
    def validate(self, action: Action, connection_manager: ConnectionManager, board: Board, game: Game) -> bool:
        player_id = action.payload['player_id']
        return player_id in game.blocking_on_discard

class HasCard(ActionValidator):
    """Ensures the player has the card they are trying to play or discard."""
    def validate(self, action: Action, connection_manager: ConnectionManager, board: Board, game: Game) -> bool:
        if isinstance(action, (Play, Discard)):
            player = game.get_player(action.payload['player_id'])
            if player:
                return action.payload['card'] in player.hand
        return False

class ValidSuit(ActionValidator):
    """Ensures the called suit is valid and not the faceup card's suit during pickup."""
    def validate(self, action: Action, connection_manager: ConnectionManager, board: Board, game: Game) -> bool:
        if not isinstance(action, CallSuit):
            return True
            
        suit = action.payload['suit']
        if suit not in game.deck.SUITS:
            return False
            
        # During pickup phase, can't call the faceup card's suit
        if game.phase == Phase.PICKUP_CARD:
            faceup_card = board.peek()
            if faceup_card and faceup_card.suit == suit:
                return False
                
        return True
    
class TrickOver(ActionValidator):
    """Ensures the trick is over."""
    def validate(self, action: Action, connection_manager: ConnectionManager, board: Board, game: Game) -> bool:
        return all(len(slot.cards) == 0 for slot in board.slots.values())
    
class HandOver(ActionValidator):
    """Ensures the hand is over."""
    def validate(self, action: Action, connection_manager: ConnectionManager, board: Board, game: Game) -> bool:
        return game.hand_score[1] + game.hand_score[2] == 5

