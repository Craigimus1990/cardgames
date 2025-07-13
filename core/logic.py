from dataclasses import dataclass
from typing import Dict, List, Optional, Type
from core.state import Player, Board, Game
from core.net import ConnectionManager

@dataclass
class Action:
    """Represents a game action with a name and associated data."""
    name: str
    payload: Dict

class ActionResult:
    """Represents the result of executing an action."""
    def __init__(self, success: bool, message: str, follow_up_actions: Optional[List['ActionExecutor']] = None):
        self.success = success
        self.message = message
        self.follow_up_actions = follow_up_actions or []

class ActionValidator:
    """Base class for validating actions."""
    def validate(self, action: Action, connection_manager: ConnectionManager, board: Board, game: Game) -> bool:
        """
        Validate if an action can be performed.
        
        Args:
            action: The action to validate
            connection_manager: The connection manager containing player connections
            board: The current game board
            game: The current game state
            
        Returns:
            bool: True if the action is valid, False otherwise
        """
        raise NotImplementedError("Subclasses must implement validate()")

class ActionExecutor:
    """Base class for executing actions."""
    def execute(self, action: Action, connection_manager: ConnectionManager, board: Board, game: Game) -> ActionResult:
        """
        Execute an action.
        
        Args:
            action: The action to execute
            connection_manager: The connection manager containing player connections
            board: The current game board
            game: The current game state
            
        Returns:
            ActionResult: The result of executing the action
        """
        raise NotImplementedError("Subclasses must implement execute()")

class ActionRule:
    """Combines validators and executors to form a complete action rule."""
    def __init__(self, validators: List[ActionValidator], executor: ActionExecutor):
        self.validators = validators
        self.executor = executor
        self.success_message = ""

    def run_executors(self, action: Action, connection_manager: ConnectionManager, board: Board, game: Game, to_execute: List[ActionExecutor]):
        """
        Execute follow up actions.
        """

        results = []
        follow_up_actions = []
        for executor in to_execute:
            result = executor.execute(action, connection_manager, board, game)
            if not result.success:
                return result
            follow_up_actions.extend(result.follow_up_actions)

        if (follow_up_actions):
            return self.run_executors(action, connection_manager, board, game, follow_up_actions)

        return ActionResult(True, self.success_message or "Action executed successfully")


    def process(self, action: Action, connection_manager: ConnectionManager, board: Board, game: Game) -> ActionResult:
        """
        Process an action through all validators and executors.
        
        Args:
            action: The action to process
            connection_manager: The connection manager containing player connections
            board: The current game board
            game: The current game state
            
        Returns:
            ActionResult: The result of processing the action
        """
        # First validate the action
        for validator in self.validators:
            if not validator.validate(action, connection_manager, board, game):
                return ActionResult(False, "Action validation failed")
        
        # If validation passes, execute the action
        return self.run_executors(action, connection_manager, board, game, [self.executor])

class ActionRouter:
    """Routes actions to their corresponding rules."""
    def __init__(self):
        self.rules: Dict[str, ActionRule] = {}
    
    def register_rule(self, action_name: str, rule: ActionRule):
        """Register a rule for a specific action name."""
        self.rules[action_name] = rule
    
    def route(self, action: Action, connection_manager: ConnectionManager, board: Board, game: Game, player_action: bool = True) -> ActionResult:
        """
        Route an action to its corresponding rule.
        
        Args:
            action: The action to route
            connection_manager: The connection manager containing player connections
            board: The current game board
            game: The current game state
            
        Returns:
            ActionResult: The result of processing the action
            
        Raises:
            ValueError: If no rule is found for the action name
        """
        if action.name not in self.rules:
            raise ValueError(f"No rule found for action: {action.name}")
        
        if player_action and not is_player_action(action):
            raise ValueError(f"Action {action.name} is not allowed to be executed by a player")

        rule = self.rules[action.name]
        return rule.process(action, connection_manager, board, game)

class ActionBuilder:
    """Base class for constructing Actions from websocket messages."""
    def build(self, message: dict) -> Action:
        """
        Construct an Action from a websocket message.
        
        Args:
            message: The websocket message to convert to an Action
            player: The player who initiated the action
        Returns:
            Action: The constructed Action
            
        Raises:
            ValueError: If the message cannot be converted to a valid Action
        """
        raise NotImplementedError("Subclasses must implement build()") 