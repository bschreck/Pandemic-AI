from enum import Enum
from dataclasses import dataclass
import random


class Character(Enum):
    DUKE = 1
    ASSASSIN = 2
    CAPTAIN = 3
    AMBASSADOR = 4
    CONTESSA = 5

class CoupPlayer:
    def __init__(self, idx):
        self.idx = idx
        self.cards = []
        self.tokens = []
        
    def get_action(self, state):
        action, other_player_idx = input(f"Player {self.idx}: what action do you want to do? (income, foreign_aid, coup, tax, assassinate, steal, exchange)"), input(f"Player {self.idx}: who do you want to do it to? (0-{len(state.players)-1})")
        other_player_idx = int(other_player_idx)
        return action, other_player_idx

    def announce(self, state, player_idx, action):
        pass

    def maybe_challenge(self, state, player_idx):
        challenge = input(f"Player {self.idx}: do you want to challenge? (y/n)")
        return challenge == 'y'

    def maybe_counter(self, state, player_idx, action):
        counter = input(f"Player {self.idx}: do you want to countej? (y/n)")
        return counter == 'y'
    
    def remove_influence(self):
        if len(self.cards) > 1:
            print(f"Current cards:", self.cards)
            card_to_pop = input(f"Player {self.idx}: choose a card to remove (0 or 1)")
            self.cards = [c for i, c in enumerate(self.cards) if i != int(card_to_pop)]
        else:
            self.cards.pop()

@dataclass
class CoupState:
    players: list[CoupPlayer]
    deck: list[Character]

class Coup:
    def __init__(self, nplayers, ncards_per_character=3):
        self.nplayers = nplayers
        self.state = CoupState([c for c in Character] * ncards_per_character, [CoupPlayer(player_idx) for player_idx in range(nplayers)])
        self.shuffle_deck()
        self.deal()
        for player_idx in range(self.nplayers):
            self.add_coins_to_player(player_idx, 2)
        self.general_actions = {method.__name__: method for method in [self.income, self.foreign_aid, self.coup]}
        self.character_actions = {method.__name__: method for method in [self.tax, self.assassinate, self.steal, self.exchange]}
        self.available_counteractions_by_target = {'assassinate': [Character.CONTESSA], 'steal': [Character.AMBASSADOR, Character.CAPTAIN]}
        self.available_counteractions_by_anyone = {'foreign_aid': [Character.DUKE]}
        self.available_character_actions = {'tax': Character.DUKE, 'steal': Character.CAPTAIN, 'assassinate': Character.ASSASSIN, 'exchange': Character.AMBASSADOR}
        
    def shuffle_deck(self):
        random.shuffle(self.state.deck)
    
    def add_cards(self, player_idx, cards):
        self.state.players[player_idx].cards.extend(cards)

    def remove_cards(self, player_idx, ncards, interactive=True):
        cur_cards = self.state.players[player_idx].cards
        print("Current cards: ", cur_cards)
        card_idx = input(f"choose {ncards} card{'s' if ncards > 1 else ''} to remove (0 or 1)")
        self.state.players[player_idx].cards = [c for i, c in enumerate(cur_cards) if i != card_idx]

    def deal(self):
        for player_idx in range(self.nplayers):
            cards = self.pop_cards(2)
            self.add_cards(player_idx, cards)
            
    def challengable(self, action):
        return action in self.character_actions or action in self.available_counteractions_by_target or action in self.available_counteractions_by_anyone

    def counterable(self, action, nontarget=False):
        if nontarget and action in self.available_counteractions_by_anyone:
            return True
        elif action in self.available_counteractions_by_target:
            return True
        return False

    def do_challenge(self, player_idx, other_player_idx, action):
        card = self.available_character_actions.get(action)
        if card and card in self.state.players[other_player_idx].cards:
            self.remove_cards(player_idx, 1)
            return True
        elif card:
            self.remove_cards(other_player_idx, 1)
        return False
    
    def do_challenge_counter(self, player_idx, other_player_idx, action):
        cards = self.available_counteractions_by_anyone.get(action)
        if not cards:
            cards = self.available_counteractions_by_target.get(action)
        if cards and any(card in self.state.players[player_idx].cards for card in cards):
            self.remove_cards(other_player_idx, 1)
            return True
        elif cards:
            self.remove_cards(player_idx, 1)
        return False
    
    def do_action(self, player_idx, other_player_idx, action):
        if action in self.general_actions:
            self.general_actions[action](player_idx, other_player_idx)
        elif action in self.character_actions:
            self.character_actions[action](player_idx, other_player_idx)
        else:
            raise ValueError(f"Unknown action: {action}")

    def try_counter_with_challenge(self, player_idx, other_player_idx, action, nontarget=False):
        if self.counterable(action, nontarget=nontarget):
            countered = self.state.players[other_player_idx].maybe_counter(self.state, player_idx, action)
            if countered:
                challenged = self.state.players[player_idx].maybe_challenge(self.state, other_player_idx, action, counter=True)
                if challenged:
                    return self.do_challenge_counter(player_idx, other_player_idx, action)
        return False

    def announce_and_try_action(self, player_idx, action, other_player_idx):
        """Announce an action to all players"""
        print(f"Player {player_idx} is doing {action} to player {other_player_idx}")
        for i in self.alive_player_indexes:
            if i != player_idx:
                self.state.players[i].announce(self.state, player_idx, action)
        challenge_succeeded = False
        if self.challengable(action):
            challenged = self.state.players[other_player_idx].maybe_challenge(self.state, player_idx, action)
            if challenged:
                challenge_succeeded = self.do_challenge(player_idx, other_player_idx, action)
        counter_challenge_succeeded = False
        if not challenge_succeeded:
            counter_challenge_succeeded = self.try_counter_with_challenge(player_idx, other_player_idx, action)
            for i in self.alive_player_indexes:
                if i != player_idx:
                    counter_challenge_succeeded = self.try_counter_with_challenge(player_idx, other_player_idx, action, nontarget=True)
        if not counter_challenge_succeeded and not challenge_succeeded:
            self.do_action(player_idx, other_player_idx, action)

    def add_coins_to_player(self, player_idx, ncoins):
        # TODO can get more complex with actual coins, and a fixed treasury size
        self.state.players[player_idx].tokens += ncoins

    def remove_coins_from_player(self, player_idx, ncoins):
        self.state.players[player_idx].tokens -= ncoins

    def transfer_coins_to_player(self, player_idx, other_player_idx, ncoins):
        self.add_coins_to_player(player_idx, ncoins)
        self.remove_coins_to_player(other_player_idx, ncoins)

    def add_cards_to_deck(self, discards):
        self.state.deck.extend(discards)
        self.shuffle_deck()
            
    @property
    def alive_players_indexes(self):
        return [i for i, player in enumerate(self.state.players) if len(player.cards) > 0]

    def game_play(self):
        player_idx = self.starting_player_idx
        while len(self.alive_player_indexes) > 1:
            for player_idx in self.alive_player_indexes:
                action, other_player_idx = self.state.players[player_idx].get_action(self.state)
                self.announce_and_try_action(player_idx, action, other_player_idx)
        return self.state.players[self.alive_player_indexes[0]]
            

def income(self, player_idx, other_player_idx):
    """income"""
    self.add_coins_to_player(player_idx, 1)
    
def foreign_aid(self, player_idx, other_player_idx):
    """foreign aid"""
    self.add_coins_to_player(player_idx, 2)
    
def coup(self, player_idx, other_player_idx):
    """coup"""
    self.remove_coins_from_player(player_idx, 7)
    self.state.players[player_idx].remove_influence()

def tax(self, player_idx, other_player_idx):
    """tax"""
    self.add_coins_to_player(player_idx, 3)

def assassinate(self, player_idx, other_player_idx):
    self.remove_coins_from_player(player_idx, 3)
    self.state.players[player_idx].remove_influence()
    
def steal(self, player_idx, other_player_idx):
    """steal"""
    self.transfer_coins_to_player(player_idx, other_player_idx, 2)
    
def exchange(self, player_idx, other_player_idx):
    """exchange"""
    cards = self.pop_cards(2)
    card_to_keep, discards = self.choose_cards(player_idx, cards, 1)
    if card_to_keep:
        discards.append(self.remove_cards(player_idx, 1))
        self.add_cards(player_idx, [card_to_keep])
    self.add_cards_to_deck(discards)
    

if __name__ == '__main__':
    game = Coup(4)
    winner = game.game_play()
    print("Winner is: ", winner)