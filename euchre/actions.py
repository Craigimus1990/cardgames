from core.logic import Action, ActionBuilder
from core.state import Card

def is_player_action(action: Action) -> bool:
    return action.action_type in ["play", "discard", "call_reneg", "call_pickup", "call_suit"]

# Player actions
class Play(Action):
    """Action representing a player's intention to play a card."""
    def __init__(self, card: Card, player_id: int):
        super().__init__("play", {"card": card, "player_id": player_id})

class Discard(Action):
    """Action representing a player's intention to discard a card."""
    def __init__(self, card: Card, player_id: int):
        super().__init__("discard", {"card": card, "player_id": player_id})

class CallReneg(Action):
    """Action representing a player's accusation of the opposing team not following suit."""
    def __init__(self, trick_number: int, team_id: int):
        super().__init__("call_reneg", {
            "trick_number": trick_number,
            "team_id": team_id
        })

class CallPickup(Action):
    """Action representing a player's request for the dealer to pick up the top card."""
    def __init__(self):
        super().__init__("call_pickup", {})

class Pass(Action):
    """Action representing a player's decision to pass."""
    def __init__(self):
        super().__init__("pass", {})

class CallSuit(Action):
    """Action representing a player's declaration of a trump suit."""
    def __init__(self, suit: str):
        super().__init__("call_suit", {"suit": suit}) 

class EndGame(Action):
    """Action used to end the game."""
    def __init__(self):
        super().__init__("end_game", {})

class StartGame(Action):
    """Action used to start the game."""
    def __init__(self):
        super().__init__("start_game", {})


class EuchreActionBuilder(ActionBuilder):
    """Action builder for Euchre actions."""
    def __init__(self):
        super().__init__()
    
    def build(self, message: dict) -> Action:
        action_type = message.get('action_type')
        if not action_type:
            raise ValueError("Message missing required 'action_type' field")
        
        if action_type == "play":
            return Play(message['card'], message['player_id'])
        elif action_type == "discard":
            return Discard(message['card'], message['player_id'])
        elif action_type == "call_reneg":
            return CallReneg(message['trick_number'], message['team_id'])
        elif action_type == "call_pickup":
            return CallPickup()
        elif action_type == "pass":
            return Pass()
        elif action_type == "call_suit":
            return CallSuit(message['suit'])
        elif action_type == "end_game":
            return EndGame()
        elif action_type == "start_game":
            return StartGame()
        else:
            return None