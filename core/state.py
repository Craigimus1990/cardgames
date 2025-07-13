import random

class Card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit
    
    def __str__(self):
        return f"{self.rank} of {self.suit}"
    
    def __repr__(self):
        return self.__str__()
    
    def __eq__(self, other):
        return self.rank == other.rank and self.suit == other.suit

class Deck:
    RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    SUITS = ['Hearts', 'Diamonds', 'Clubs', 'Spades']
    
    def __init__(self):
        self.collect()
    
    def collect(self):
        """Reset the deck to its initial state with all 24 cards."""
        self.cards = []
        for suit in self.SUITS:
            for rank in self.RANKS:
                self.cards.append(Card(rank, suit))
        return self
    
    def shuffle(self):
        """Shuffle the deck using the Fisher-Yates algorithm."""
        n = len(self.cards)
        for i in range(n - 1, 0, -1):
            j = random.randint(0, i)
            self.cards[i], self.cards[j] = self.cards[j], self.cards[i]
        return self
    
    def deal(self):
        """Deal the top card from the deck and remove it."""
        if not self.cards:
            raise ValueError("Cannot deal from an empty deck")
        return self.cards.pop(0)
    
    def peek(self):
        """Peek at the top card of the deck."""
        if not self.cards:
            raise ValueError("Cannot peek at an empty deck")
        return self.cards[-1]
    
    def __len__(self):
        return len(self.cards)
    
    def __str__(self):
        return str(self.cards)

class Player:
    def __init__(self, player_id: str):
        self.id = player_id
        self.hand = []
    
    def add_card(self, card):
        """Add a card to the player's hand."""
        self.hand.append(card)
    
    def remove_card(self, card):
        """Remove a card from the player's hand."""
        if card in self.hand:
            self.hand.remove(card)
            return True
        return False
    
    def __str__(self):
        return f"Player {self.id} with {len(self.hand)} cards"
    
    def __repr__(self):
        return self.__str__()

class Board:
    class Slot:
        def __init__(self, face_up: bool = False):
            self.cards = []
            self.face_up = face_up
        
        def add_card(self, card: Card):
            self.cards.append(card)
        
        def pop(self):
            return self.cards.pop()
        
        def peek(self, force: bool = False):
            if self.face_up or force:
                return self.cards[-1]
            else:
                return None

        def flip(self):
            self.face_up = not self.face_up
        
        def __len__(self):
            return len(self.cards)
        
    def __init__(self, deck: Deck):
        self.slots = {}
        self.deck = deck
        self.players = []
    
    def add_slot(self, id, slot: Slot):
        self.slots[id] = slot
    
class Game:
    def __init__(self, deck: Deck, players: list[Player]):
        self.board = Board(deck)
        self.players = players
    
    def get_player(self, player_id: str) -> Player:
        return next((player for player in self.players if player.id == player_id), None)    