from core.logic import ActionRule
from euchre.validators import *
from euchre.executors import * 

class Deal(ActionRule):
    """Rule for dealing cards at the start of a hand."""
    def __init__(self):
        super().__init__(
            validators=[CorrectPhase()],
            executor=Deal()
        ) 


class PickupCard(ActionRule):
    """Rule for picking up the top card."""
    def __init__(self):
        super().__init__(
            validators=[CorrectPhase(), PlayersTurn()],
            executor=PickupCard()
        )


class Pass(ActionRule):
    """Rule for passing the top card."""
    def __init__(self):
        super().__init__(
            validators=[CorrectPhase(), PlayersTurn(), CanPass()],
            executor=Pass()
        )


class Discard(ActionRule):
    """Rule for discarding a card."""
    def __init__(self):
        super().__init__(
            validators=[CorrectPhase(), HasCard(), BlockedOnPlayerDiscard()],
            executor=Discard()
        )


class CallSuit(ActionRule):
    """Rule for calling a suit."""
    def __init__(self):
        super().__init__(
            validators=[CorrectPhase(), PlayersTurn(), ValidSuit()],
            executor=CallSuit()
        )


class PlayCard(ActionRule):
    """Rule for playing a card."""
    def __init__(self):
        super().__init__(
            validators=[CorrectPhase(), PlayersTurn(), HasCard()],
            executor=PlayCard()
        )

class TrickOver(ActionRule):
    """Rule for ending a trick."""
    def __init__(self):
        super().__init__(
            validators=[CorrectPhase(), TrickOver()],
            executor=ScoreTrick()
        )