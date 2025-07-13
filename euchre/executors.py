from core.logic import ActionExecutor, ActionResult
from core.state import Board, Game
from core.net import ConnectionManager
from euchre.actions import AdvancePhase, HandOver, Play, Discard, CallReneg, CallPickup, CallSuit, TrickOver
from euchre.setup import EuchreGame, Phase
from typing import List, Optional

class PickUp(ActionExecutor):
    """Picks up the top card from the deck."""
    def execute(self, action: Action, connection_manager: ConnectionManager, board: Board, game: EuchreGame) -> ActionResult:
        try:
            card = game.deck.deal()
            calling_team = game.get_player(action.payload['player_id']).team_id
            dealer_connection = connection_manager.get_connection(game.current_dealer.id)
            if dealer_connection:
                dealer_connection[1].add_card(card)
                game.trump_suit = card.suit
                game.add_blocking_discard(game.current_dealer)
                game.calling_team = calling_team
                game.set_phase(Phase.DISCARD)
                return ActionResult(True, f"Dealer picked up {card}")
            return ActionResult(False, "Dealer not found")
        except ValueError as e:
            return ActionResult(False, str(e))

class Reneg(ActionExecutor):
    """Determines if the opposing team did not follow suit on a previous trick."""
    def execute(self, action: Action, connection_manager: ConnectionManager, board: Board, game: EuchreGame) -> ActionResult:
        team_id = game.get_player(action.payload['player_id']).team_id
        if (game.renegs[team_id]):
            reneg_reason = game.renegs[team_id][1]
            game.hand_score[team_id] += 5
            return ActionResult(True, f"Team {team_id} called reneg because {reneg_reason}", {}, [Broadcast(f"Team {team_id} called a reneg, which was upheld because {reneg_reason}. {team_id} wins the hand."), ScoreHand()])
        else:
            opposing_team = 1 if team_id == 2 else 2
            game.hand_score[opposing_team] += 5
            return ActionResult(False, f"Team {team_id} failed a reneg call", [Broadcast(f"Team {team_id} called a reneg, but it was not upheld. Team {opposing_team} wins the hand."), ScoreHand()])


class PlayCard(ActionExecutor):
    """Removes a card from player's hand and places it in their slot."""
    def execute(self, action: Action, connection_manager: ConnectionManager, board: Board, game: EuchreGame) -> ActionResult:
        card = action.payload['card']
        connection = connection_manager.get_connection(game.current_player.id)
        if connection and connection[1].remove_card(card):
            board.slots[connection[1].id].add_card(card)
            return ActionResult(True, f"Played {card}", [AdvanceTurn()])
        return ActionResult(False, "Card not in hand")

class NotifyCurrentPlayer(ActionExecutor):
    """Sends a message to the current player."""
    def __init__(self, override_message: Optional[str] = None):
        self.override_message = override_message

    def execute(self, action: Action, connection_manager: ConnectionManager, board: Board, game: EuchreGame) -> ActionResult:
        message = self.override_message or action.payload['message']
        connection = connection_manager.get_connection(game.current_player.id)
        if connection:
            connection[1].send_message(message)
            return ActionResult(True, f"Notified player {game.current_player.id}")
        return ActionResult(False, f"Player {game.current_player.id} not found")
    
class AdvanceDealer(ActionExecutor):
    """Advances the dealer to the next player."""
    def execute(self, action: Action, connection_manager: ConnectionManager, board: Board, game: EuchreGame) -> ActionResult:
        game.set_dealer(game.players[(game.players.index(game.current_dealer) + 1) % len(game.players)])
        return ActionResult(True, f"Dealer advanced to {game.current_dealer}")
    
class NotifyDealer(ActionExecutor):
    """Sends a message to the dealer."""
    def __init__(self, override_message: Optional[str] = None):
        self.override_message = override_message

    def execute(self, action: Action, connection_manager: ConnectionManager, board: Board, game: EuchreGame) -> ActionResult:
        message = self.override_message or action.payload['message']
        connection = connection_manager.get_connection(game.current_dealer.id)
        if connection:
            connection[1].send_message(message)
            return ActionResult(True, f"Notified dealer {game.current_dealer.id}")
        return ActionResult(False, f"Dealer {game.current_dealer.id} not found")

class Broadcast(ActionExecutor):
    """Sends a message to all players."""
    def __init__(self, override_message: Optional[str] = None):
        self.override_message = override_message

    def execute(self, action: Action, connection_manager: ConnectionManager, board: Board, game: EuchreGame) -> ActionResult:
        message = self.override_message or action.payload['broadcast']
        if message: 
            for connection in connection_manager.get_all_connections():
                connection[1].send_message(message)
        return ActionResult(True, "Broadcast sent")

class Deal(ActionExecutor):
    """Reshuffles the deck and deals 5 cards to each player."""
    def execute(self, action: Action, connection_manager: ConnectionManager, board: Board, game: EuchreGame) -> ActionResult:
        game.deck.collect().shuffle()
        for _ in range(5):
            for connection in connection_manager.get_all_connections():
                card = game.deck.deal()
                connection[1].add_card(card)
        top_card = game.deck.peek()
        return ActionResult(True, "Dealt 5 cards to each player", [Broadcast(f"5 cards have been dealt to each player. The {top_card} is showing.")])

class Discard(ActionExecutor):
    """Removes a card from player's hand and places it in their slot."""
    def execute(self, action: Action, connection_manager: ConnectionManager, board: Board, game: EuchreGame) -> ActionResult:
        card = action.payload['card']
        show_card = 'show' in action.payload and action.payload['show']
        player_id = action.payload['player_id']
        game.remove_blocking_discard(game.get_player(player_id))
        connection = connection_manager.get_connection(player_id)
        if connection and connection[1].remove_card(card):
            if (show_card):
                board.slots[connection[1].id].add_card(card)
            game.set_phase(Phase.PLAY)
            return ActionResult(True, f"Discarded {card}")
        return ActionResult(False, "Card not in hand")

class AdvanceTurn(ActionExecutor):
    """Sets the current player to be the player to the current player's left."""
    def execute(self, action: Action, connection_manager: ConnectionManager, board: Board, game: EuchreGame) -> ActionResult:
        trick_over = game.current_dealer == game.current_player
        current_index = game.players.index(game.current_player)
        next_index = (current_index + 1) % len(game.players)
        game.set_current_player(game.players[next_index])

        if trick_over:
            if (game.phase == Phase.PICKUP_CARD):
                game.set_phase(Phase.PICK_SUIT)
                return ActionResult(True, f"Turn advanced to {game.current_player}", [Broadcast(f"{game.current_player} it is your turn to pick a suit.")])
            elif (game.phase == Phase.PICK_SUIT):
                game.set_phase(Phase.DISCARD)
                return ActionResult(True, f"{game.current_dealer} must discard a card.", [Broadcast(f"{game.current_dealer} you must discard a card.")])
            elif (game.phase == Phase.PLAY):
                game.set_phase(Phase.SCORE_TRICK)
                return ActionResult(True, f"Trick over. Scoring...", [Broadcast(f"Trick over. Scoring..."), ScoreTrick()])

class SetPlayerToDealersLeft(ActionExecutor):
    """Sets the current player to be the player to the dealer's left."""
    def execute(self, action: Action, connection_manager: ConnectionManager, board: Board, game: EuchreGame) -> ActionResult:
        current_index = game.players.index(game.current_dealer)
        next_index = (current_index + 1) % len(game.players)
        game.set_current_player(game.players[next_index])
        return ActionResult(True, f"Current player set to {game.current_player}", [Broadcast(f"{game.current_player} it is your turn to play.")])

class SetDealer(ActionExecutor):
    """Sets the dealer for the current hand."""
    def execute(self, action: Action, connection_manager: ConnectionManager, board: Board, game: EuchreGame) -> ActionResult:
        dealer = game.get_player(action.payload['dealer_id'])
        game.set_dealer(dealer)
        return ActionResult(True, f"Dealer set to {dealer}", [Broadcast(f"The dealer is now {dealer}")])

class SetTrumpSuit(ActionExecutor):
    """Sets the trump suit for the current hand."""
    def execute(self, action: Action, connection_manager: ConnectionManager, board: Board, game: EuchreGame) -> ActionResult:
        suit = action.payload['suit']
        calling_team = game.get_player(action.payload['player_id']).team_id
        game.trump_suit = suit
        game.calling_team = calling_team
        game.set_phase(Phase.PLAY)
        return ActionResult(True, f"Trump suit set to {suit}", [Broadcast(f"{game.get_player(action.payload['player_id'])} called {suit} as trump.")])

class ClearBoard(ActionExecutor):
    """Clears all slots on the board."""
    def execute(self, action: Action, connection_manager: ConnectionManager, board: Board, game: EuchreGame) -> ActionResult:
        for slot in board.slots.values():
            slot.cards.clear()
        game.calling_team = None
        game.trump_suit = None
        return ActionResult(True, "Board cleared") 
    
class ScoreTrick(ActionExecutor):
    """Scores the current trick."""
    def execute(self, action: Action, connection_manager: ConnectionManager, board: Board, game: EuchreGame) -> ActionResult:
        # 1. Gather played cards from each player's slot
        played_cards = []
        starting_index = game.players.index(game.current_player)
        for i in range(len(game.players)):
            player = game.players[(starting_index + i) % len(game.players)]
            slot = board.slots.get(player.id)
            if slot and len(slot.cards) > 0:
                played_cards.append((player, slot.cards[-1]))
            else:
                return ActionResult(False, f"Player {player.id} has not played a card this trick.")
        
        starting_suit = played_cards[0][1].suit
        def card_value(card):
            # Simple rank order for Euchre (9 < 10 < J < Q < K < A)
            order = {'9': 0, '10': 1, 'J': 2, 'Q': 3, 'K': 4, 'A': 5}
            bonus = 0
            if (card.suit == starting_suit):
                bonus = 10
            elif (card.suit == game.trump_suit):
                bonus = 20
            return order.get(card.rank, -1) + bonus

        # 2. Find the player with the highest card (placeholder logic)
        winner, winning_card = max(played_cards, key=lambda pc: card_value(pc[1]))

        # 3. Add points to the winner's team
        game.hand_score[winner.team_id] += 1
        
        # 4. Check if the hand is over or if there are more tricks to play
        if (game.hand_score[1] + game.hand_score[2] >= 5):
            game.set_phase(Phase.SCORE_GAME)
            return ActionResult(True, f"Hand over. Scoring...", [Broadcast(f"Hand over. Scoring..."), ScoreHand()])
        else:
            game.set_phase(Phase.PLAY)
            game.set_current_player(winner)
            return ActionResult(True, f"{winner.team_id} wins the trick with {winning_card}.", [Broadcast(f"Team {winner.team_id} wins the trick with {winning_card}. {winner} will start the next trick."), NotifyCurrentPlayer(f"{winner} it is your turn to play.")])

    
class ScoreHand(ActionExecutor):
    """Scores the current hand."""
    def execute(self, action: Action, connection_manager: ConnectionManager, board: Board, game: EuchreGame) -> ActionResult:
        # 1. Calculate the score for each team
        points = 0
        winning_score = max(game.hand_score[1], game.hand_score[2])
        winner = 1 if game.hand_score[1] > game.hand_score[2] else 2

        if (winning_score >= 5 or winner != game.calling_team):
            points = 2
        else:
            points = 1

        game.score[winner] += points
        
        if (game.score[winner] >= 10):
            game.set_phase(Phase.END_GAME)
            return ActionResult(True, f"Team {winner} wins the game!", [Broadcast(f"Team {winner} wins the game!")])
        else:
            game.set_phase(Phase.DEAL)
            game.hand_score = {1: 0, 2: 0}
            return ActionResult(True, f"Team {winner} wins the hand!", [Broadcast(f"Team {winner} wins the hand! Score is now {game.score[1]} to {game.score[2]}."), ClearBoard(), AdvanceDealer(), Deal()])
        
        