from numpy.random import default_rng
import random
import numpy as np
import copy

class ActionError(ValueError):
    pass
class TurnError(ValueError):
    pass
class PandemicGame:
    def __init__(self, nplayers, difficulty, ncards_to_draw=2):
        self.nplayers = nplayers
        if self.nplayers == 2:
            self.starting_cards_per_hand = 4
        elif self.nplayers == 3:
            self.starting_cards_per_hand = 3
        elif self.nplayers == 4:
            self.starting_cards_per_hand = 2
        else:
            raise ValueError("only 2-4 players")
        if difficulty == "easy":
            self.nepidemics = 4
        elif difficulty == "medium":
            self.nepidemics = 5
        elif difficulty == "hard":
            self.nepidemics = 6
        else:
            raise ValueError("unknown difficulty")

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
        self.total_disease_cubes_per_color = {color: 0 for color in self.all_colors}
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

    def add_disease_cube(self, city, color, prior_neighbors=None):
        if prior_neighbors is None:
            prior_neighbors = set()
        current_ndis_cubes = self.current_board[city].get(color, 0)
        if current_ndis_cubes < 3:
            self.current_board[city][color] = current_ndis_cubes + 1
            self.total_disease_cubes_per_color[color] += 1
            return
        assert self.current_board[city][color] == 3
        self.current_board[city][color] = 3
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
        return self.total_disease_cubes_per_color[color] == 0

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
        self.total_disease_cubes_per_color[color] -= n_to_treat

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
        # TODO
        pass
    def do_infect_step(self):
        # TODO
        pass
        
                
    
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







def test_drive():
    game = PandemicGame(4, "easy")
    player = game.roles[0]
    game.drive(player, "new york")
    assert game.current_player_locations[player] == "new york"
    try:
        game.drive(player, "lima")
    except ActionError:
        pass
def test_direct_flight():
    game = PandemicGame(4, "easy")
    player = game.roles[0]
    player_hand = list(game.player_hands[player])
    for card in player_hand:
        if card in game.city_colors:
            game.direct_flight(player, card)
            assert game.current_player_locations[player] == card
        else:
            try:
                game.direct_flight(player, card)
            except ActionError:
                pass
            else:
                raise ValueError(f"should be error flying to {card}")
    other_cities = [city for city in game.city_colors if city not in player_hand]
    for city in other_cities:
        print(city)
        try:
            game.direct_flight(player, city)
        except ActionError:
            pass       
        else:
            raise ValueError(f"should be error flying to {city}")
def test_charter_flight():
    game = PandemicGame(4, "easy")
    player = game.roles[0]
    player_hand = list(game.player_hands[player])
    if "atlanta" in player_hand:
        game.player_hands[player].remove("atlanta")
    try:
        game.charter_flight(player, "new york")
    except ActionError:
        pass
    else:
        raise ValueError(f"should be error flying to new york")
    game.player_hands[player].add("atlanta")
    game.charter_flight(player, "new york")

def test_shuttle_flight():
    game = PandemicGame(4, "easy")
    player = game.roles[0]
    player_hand = list(game.player_hands[player])
    try:
        game.shuttle_flight(player, "new york")
    except ActionError:
        pass
    else:
        raise ValueError(f"should be error flying to new york")
    game.add_research_station("new york")
    game.shuttle_flight(player, "new york")
    game.drive(player, "tokyo")
    try:
        game.shuttle_flight(player, "atlanta")
    except ActionError:
        pass
    else:
        raise ValueError(f"should be error flying to atlanta")

class assert_board_unchanged_besides:
    def __init__(self, game, city):
        self.game = game
        self.city = city
    def __enter__(self):
        # TODO: also check player hands, other aspects of game
        self.current_board = {
            _city: info for _city, info in copy.deepcopy(self.game.current_board).items()
            if _city != self.city
        }
    def __exit__(self, arg1, arg2, arg3):
        for _city, info in self.game.current_board.items():
            if _city == self.city:
                continue
            if info != self.current_board[_city]:
                pass
            assert info == self.current_board[_city]

def test_outbreak():
    game = PandemicGame(4, "easy")
    # ensure there are none on atlanta or surrounding
    atl_color = game.city_colors["atlanta"]
    for _ in range(3):
        for city in ["atlanta"] + game.city_graph["atlanta"]:
            try:
                game.treat_disease_internal(city, atl_color)
            except ActionError:
                pass

    # add 3 to atlanta and make sure none get added to rest of board
    with assert_board_unchanged_besides(game, "atlanta"):
        game.add_disease_cube("atlanta", atl_color)
    with assert_board_unchanged_besides(game, "atlanta"):
        game.add_disease_cube("atlanta", atl_color)
    with assert_board_unchanged_besides(game, "atlanta"):
        game.add_disease_cube("atlanta", atl_color)
    game.add_disease_cube("atlanta", atl_color)
    for neighbor in game.city_graph["atlanta"]:
        assert game.current_board[neighbor][atl_color] == 1
    # now chain reaction
    game.add_disease_cube(neighbor, atl_color)
    game.add_disease_cube(neighbor, atl_color)
    ndiseases_on_neighbor_neighbors = {
        city: game.current_board[city][atl_color]
        for city in game.city_graph[neighbor]
        if city != "atlanta"
    }
    game.add_disease_cube("atlanta", atl_color)
    for city, ndis in ndiseases_on_neighbor_neighbors.items():
        if ndis == 3:
            assert game.current_board[city][atl_color] == 3
        else:
            assert game.current_board[city][atl_color] == ndis + 1

def test_treat_disease():
    game = PandemicGame(4, "easy")
    player = game.roles[0]
    # ensure there are 3  on atlanta
    game.add_disease_cube("atlanta", "blue")
    game.add_disease_cube("atlanta", "blue")
    game.add_disease_cube("atlanta", "blue")

    game.treat_disease(player, "blue")
    try:
        game.treat_disease(player, "red")
    except ActionError:
        pass
    else:
        raise ValueError(f"should be error treating nonexistent red disease")
    game.treat_disease(player, "blue")
    game.treat_disease(player, "blue")
    try:
        game.treat_disease(player, "blue")
    except ActionError:
        pass
    else:
        raise ValueError(f"should be error treating nonexistent red disease")

def test_build_research_station():
    game = PandemicGame(4, "easy")
    player = game.roles[0]
    try:
        game.build_research_station(player)
    except ActionError:
        pass
    else:
        raise ValueError(f"should be error building existing research station")
    game.drive(player, "new york")
    game.build_research_station(player)
    assert game.has_research_station("new york")

def test_share_knowledge():
    game = PandemicGame(4, "easy")
    player1 = game.roles[0]
    player2 = game.roles[1]
    # TODO: case when no cities to share
    cities_to_share = [
        city for city in game.player_hands[player1]
        if city in game.city_colors]
    for city in cities_to_share:
        game.share_knowledge(player1, player2, city)
        assert city not in game.player_hands[player1]
        assert city in game.player_hands[player2]
    
    try:
        game.share_knowledge(player1, player2, city)
    except ActionError:
        pass
    else:
        raise ValueError(f"should be error sharing city not in giving player's hand")
def test_discover_cure():
    game = PandemicGame(4, "easy")
    player = game.roles[0]
    matching_cards = set([city for city, color in game.city_colors.items() if color == "blue"][:5])
    game.player_hands[player] = matching_cards
    game.discover_cure(player, "blue", matching_cards)
    assert len(game.player_hands[player]) == 0
    assert game.is_cured("blue")
    assert not game.is_eradicated("blue")

    game.player_hands[player] = matching_cards
    try:
        game.discover_cure(player, "blue", matching_cards)
    except ActionError:
        pass
    else:
        raise ValueError(f"should be error discovering cure twice")

    del game.cured_diseases["blue"]

    try:
        game.discover_cure(player, "blue", set(list(matching_cards)[:4]))
    except ActionError:
        pass
    else:
        raise ValueError(f"should be error discovering cure with fewer than 5 cards")

    game.player_hands[player] = set(list(game.player_hands[player])[:4])
    try:
        game.discover_cure(player, "blue", matching_cards)
    except ActionError:
        pass
    else:
        raise ValueError(f"should be error discovering cure with cards not in player's hand")

    game.player_hands[player].add("lima")
    try:
        game.discover_cure(player, "blue", game.player_hands[player])
    except ActionError:
        pass
    else:
        raise ValueError(f"should be error discovering cure with non matching colors")
def test_eradicate_disease():
    game = PandemicGame(4, "easy")
    player = game.roles[0]
    for city, color in game.city_colors.items():
        ndiseases = game.cur_city_disease_cubes(city, color)
        if color == "blue" and ndiseases > 0:
            for _ in range(ndiseases):
                game.treat_disease_internal(city, color)
    assert game.is_eradicated(color)


if __name__ == "__main__":
    game = PandemicGame(4, "easy")
    print(game.gen_player_deck())
    test_drive()
    test_direct_flight()
    test_charter_flight()
    test_shuttle_flight()
    test_outbreak()
    test_treat_disease()
    test_build_research_station()
    test_share_knowledge()
    test_discover_cure()
    test_eradicate_disease()