from numpy.random import default_rng
import random
import numpy as np

class ActionError(ValueError):
    pass
class TurnError(ValueError):
    pass
class GameEnd(Exception):
    def __init__(self, win, reason):
        self.win = win
        self.reason = reason
class PandemicGame:
    def __init__(
        self, 
        nplayers, 
        nepidemics=4,
        ncards_to_draw=2, 
        max_disease_cubes_per_color=24,
        max_outbreaks=8,
        infection_rates=[2, 2, 2, 3, 3, 4, 4]):
        self.nplayers = nplayers
        if self.nplayers == 2:
            self.starting_cards_per_hand = 4
        elif self.nplayers == 3:
            self.starting_cards_per_hand = 3
        elif self.nplayers == 4:
            self.starting_cards_per_hand = 2
        else:
            raise ValueError("only 2-4 players")

        self.nepidemics = nepidemics
        self.ncards_to_draw = ncards_to_draw
        self.role_powers = [
            "contingency", "dispatcher", "medic", "operations", "quarantine", "researcher", "scientist"
        ]
        self.city_graph = {
            "atlanta": ["new york", "lima"],
            "new york": ["atlanta", "tokyo", "paris"],
            "paris": ["new york", "tehran"],
            "lima": ["atlanta"],
            "tehran": ["paris", "tokyo"],
            "tokyo": ["new york", "tehran"],
            "sao paulo": [],
            "essen": [],
            "ho chi minh": [],
            "sydney": [],
            "manila": []
        }
        self.city_colors = {
            "atlanta": "blue",
            "new york": "blue",
            "lima": "yellow",
            "paris": "black",
            "tokyo": "red",
            "tehran": "black",
            "sao paulo": "yellow",
            "essen": "blue",
            "ho chi minh": "red",
            "sydney": "red",
            "manila": "red",
            "chicago": "blue",
            "london": "blue",
        }
        self.all_colors = set(self.city_colors.values())
        self.event_cards = ["build research station", "fly somewhere"]
        self.current_board = {}
        self.total_disease_cubes_on_board_per_color = {color: 0 for color in self.all_colors}
        self.max_disease_cubes_per_color = max_disease_cubes_per_color
        self.infection_deck = list(self.city_graph.keys())
        self.shuffle_infection_deck()
        self.infection_discard = []
        self.player_deck = []
        self.player_discard = []
        self.player_hands = {}
        self.player_deck = self.gen_player_deck()
        # map of disease colors to boolean indicating whether the disease is also eradicated
        self.cured_diseases = {}
        self.choose_roles()
        self.init_board(self.roles)
        self.init_player_hands(self.roles)
        self.infection_rates = infection_rates
        if len(infection_rates) < self.nepidemics + 1:
            raise ValueError("number of infection rates must at least one greaer than number of epidemics")
        self.infection_rate_i = 0
        self.outbreaks = 0
        self.max_outbreaks = max_outbreaks

    @property
    def ndisease_colors(self):
        return len(self.all_colors)
    
    @property
    def infection_rate(self):
        return self.infection_rates[self.infection_rate_i]

    def choose_roles(self):
        rng = default_rng()
        self.roles = rng.choice(7, size=self.nplayers, replace=False) 

    def shuffle_infection_deck(self):
        random.shuffle(self.infection_deck)

    def gen_player_deck(self):
        player_deck = list(self.city_graph.keys()) + self.event_cards[:]
        random.shuffle(player_deck)
        player_deck_split_sz = len(player_deck) // self.nepidemics
        remainder = len(player_deck) % self.nepidemics
        randints = np.random.randint(player_deck_split_sz, size=self.nepidemics-1)
        epidemic_locations = [
            player_deck_split_sz * i + randints[i]
            for i in range(self.nepidemics-1)
        ]
        epidemic_locations.append(
            player_deck_split_sz * (self.nepidemics-1) + np.random.randint(player_deck_split_sz + remainder)
        )
        for i, epidemic_loc in enumerate(epidemic_locations):
            player_deck = player_deck[:epidemic_loc+i] + ["epidemic"] + player_deck[epidemic_loc+i:]
        return player_deck

    def draw_infection_cards(self, n):
        infection_deck, cards = self.infection_deck[:-n], self.infection_deck[-n:]
        self.infection_deck = infection_deck
        self.infection_discard.extend(cards)
        return cards

    def draw_player_cards(self, n):
        if n > len(self.player_deck):
            raise GameEnd(False, "player deck limit")
        player_deck, cards = self.player_deck[:-n], self.player_deck[-n:]
        self.player_deck = player_deck
        return cards

    def init_board(self, roles):
        self.current_board = {city: {} for city in self.city_colors}
        self.current_board["atlanta"]["research_station"] = True
        self.current_player_locations = {
            player: "atlanta"
            for player in roles
        }
        initial_infection_cards = self.draw_infection_cards(9)
        # first 3 cities get 3 disease cubes
        # next 3 get 2
        # next 3 get 1
        for i, ndiseases in enumerate(range(3, 0, -1)):
            for city in initial_infection_cards[i*3:(i+1)*3]:
                for _ in range(ndiseases):
                    self.add_disease_cube(city, self.city_colors[city])

    def increment_outbreak(self):
        self.outbreaks += 1
        if self.outbreaks == self.max_outbreaks:
            raise GameEnd(False, "outbreak limit")

    def add_disease_cube(self, city, color, prior_neighbors=None):
        if prior_neighbors is None:
            prior_neighbors = set()
        current_ndis_cubes = self.current_board[city].get(color, 0)
        if current_ndis_cubes < 3:
            self.current_board[city][color] = current_ndis_cubes + 1
            if self.total_disease_cubes_on_board_per_color[color] < self.max_disease_cubes_per_color:
                self.total_disease_cubes_on_board_per_color[color] += 1
            else:
                raise GameEnd(False, "disease cube limit")
            return
        assert self.current_board[city][color] == 3
        self.current_board[city][color] = 3
        self.increment_outbreak()
        prior_neighbors.add(city)
        for neighbor in self.city_graph[city]:
            if neighbor in prior_neighbors:
                continue
            self.add_disease_cube(neighbor, color, prior_neighbors)

    def has_research_station(self, city):
        return self.current_board[city].get("research_station", False)
    
    def add_research_station(self, city):
        self.current_board[city]["research_station"] = True

    def cur_city_disease_cubes(self, city, color):
        return self.current_board[city].get(color, 0)

    def init_player_hands(self, roles):
        self.player_hands = {
            player: set(self.draw_player_cards(self.starting_cards_per_hand))
            for player in roles
        }

    def is_cured(self, color):
        return color in self.cured_diseases or self.is_eradicated(color)

    def is_eradicated(self, color):
        return self.total_disease_cubes_on_board_per_color[color] == 0

    ##### ACTIONS ###
    def drive(self, player, new_city):
        cur_city = self.current_player_locations[player]
        if new_city not in self.city_graph[cur_city]:
            raise ActionError(f"Unable to move from {cur_city} to {new_city}")
        self.current_player_locations[player] = new_city
    def direct_flight(self, player, new_city):
        if new_city not in self.player_hands[player]:
            raise ActionError(f"Player does not have {new_city} in hand")
        if new_city not in self.city_colors:
            raise ActionError(f"{new_city} is not a city")
        self.current_player_locations[player] = new_city
        self.player_discard.append(new_city)
        self.player_hands[player].remove(new_city)
    def charter_flight(self, player, new_city):
        cur_city = self.current_player_locations[player]
        if cur_city not in self.player_hands[player]:
            raise ActionError(f"Player does not have {cur_city} in hand")
        if new_city not in self.city_colors:
            raise ActionError(f"{new_city} is not a city")
        self.current_player_locations[player] = new_city
        self.player_discard.append(cur_city)
        self.player_hands[player].remove(cur_city)
    def shuttle_flight(self, player, new_city):
        cur_city = self.current_player_locations[player]
        if new_city not in self.city_colors:
            raise ActionError(f"{new_city} is not a city")
        if not self.has_research_station(cur_city):
            raise ActionError(f"{cur_city} does not have a research station")
        if not self.has_research_station(new_city):
            raise ActionError(f"{new_city} does not have a research station")
        self.current_player_locations[player] = new_city

    def treat_disease_internal(self, city, color):
        ndiseases = self.current_board[city].get(color, 0)
        if ndiseases == 0:
            raise ActionError(f"{city} has no diseases to treat")
        n_to_treat = 1
        if color in self.cured_diseases:
            n_to_treat = ndiseases
        self.current_board[city][color] = ndiseases - n_to_treat
        self.total_disease_cubes_on_board_per_color[color] -= n_to_treat

    def treat_disease(self, player, color):
        city = self.current_player_locations[player]
        self.treat_disease_internal(city, color)

    def build_research_station(self, player):
        city = self.current_player_locations[player]
        if self.has_research_station(city):
            raise ActionError(f"{city} already has station")
        self.add_research_station(city)
    def share_knowledge(self, giving_player, receiving_player, city):
        g_player_loc = self.current_player_locations[giving_player]
        r_player_loc = self.current_player_locations[giving_player]
        if g_player_loc != r_player_loc:
            raise ActionError(f"{giving_player} not in same city as {receiving_player}")
        g_player_hand = self.player_hands[giving_player]
        r_player_hand = self.player_hands[receiving_player]
        if city not in g_player_hand:
            raise ActionError(f"{giving_player} does not have {city} in hand to give")
        self.player_hands[giving_player].remove(city)
        self.player_hands[receiving_player].add(city)
    def discover_cure(self, player, color, matching_city_cards: set):
        # TODO: update with player role
        if len(matching_city_cards) != 5:
            raise ActionError("must play exactly 5 city cards")
        if color in self.cured_diseases:
            raise ActionError(f"{color} already cured")
        player_hand = self.player_hands[player]
        if len(matching_city_cards & player_hand) < len(matching_city_cards):
            raise ActionError(f"{player} does not have all of {matching_city_cards} in hand")
        city_colors = set(self.city_colors[city] for city in matching_city_cards)
        if len(city_colors) != 1:
            raise ActionError(f"some of {matching_city_cards} do not have matching disease colors")
        self.player_discard.extend(list(matching_city_cards))
        self.player_hands[player] = player_hand - matching_city_cards
        self.cured_diseases[color] = False
        if len(self.cured_diseases) == self.ndisease_colors:
            raise GameEnd(True, None)
    
    # raises TurnErrors, ActionErrors
    def player_turn(self, player, actions):
        if len(actions) != 4:
            raise TurnError("must do 4 actions in a turn")
        for action, args in actions:
            # could raise ActionError
            self.action_map[action](*args)
        new_cards = list(self.draw_player_cards(self.ncards_to_draw))
        # TODO: if multiple cards in a row are not epidemic, just do discard once instead of each time
        for card in new_cards:
            if card == "epidemic":
                self.do_epidemic()
            else:
                self.player_hands[player].add(card)
                hand = self.player_hands[player]
                if len(hand) > 7:
                    if self.interactive:
                        discard = self.choose_cards_to_discard_interactive(player)
                    else:
                        discard = self.choose_cards_to_discard_policy(player)
                    [self.player_hands[player].remove(c) for c in discard]
                    self.play_discard.append(discard)
        self.do_infect_step()

    def do_epidemic(self):
        # increase
        self.infection_rate_i += 1
        # infect
        card = self.infection_deck.pop()
        self.infection_discard.append(card)
        color = self.city_colors[card]
        if not self.is_eradicated(color):
            [self.add_disease_cube(card, color) for _ in range(3)]
        # intensify
        random.shuffle(self.infection_discard)
        self.infection_deck.extend(self.infection_discard)
        self.infection_discard = []

    def do_infect_step(self):
        cards = self.draw_infection_cards(self.infection_rate)
        for card in cards:
            color = self.city_colors[card]
            if self.is_eradicated(color):
                continue
            self.add_disease_cube(card, color)
                
    
    def choose_cards_to_discard_interactive(self, player):
        hand = self.player_hands[player]
        if len(hand) <= 7:
            raise ValueError("hand not too big")
        print("Current hand: " + ", ".join(hand))
        cards_to_discard = []
        while len(cards_to_discard) != len(hand) - 7 and all(card in hand for card in cards_to_discard):
            cards_to_discard = input("Enter cards to discard separated by comma").split(',')
        return cards_to_discard

    def choose_cards_to_discard_policy(self, player):
        # TODO
        pass