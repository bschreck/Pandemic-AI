from numpy.random import default_rng
import random
import numpy as np

# TODO: test roles

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
        infection_rates=[2, 2, 2, 3, 3, 4, 4],
        testing=False,
        do_events=True):

        # this flag gets rid of all randomization
        self.testing = testing
        self.do_events = do_events
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
        self.role_power_actions = {
            "contingency": {
                self.contingency_plan,
                ("event", "contingency_event"),

            }, 
            "dispatcher": {
                ("direct_flight", "anyone"),
                ("charter_flight", "anyone"),
                "dispatch_flight",
                "dispatch_move",

            } ,
            "medic": {
                
            }, 
            "operations": {
                "operations_move",
                ("build_research_station", "any"),

            }, 
            "quarantine": {

            },
             "researcher": {
                ("share_knowledge", "any"),

             }, 
             "scientist": {

             }

        }
        self.contingency_planner_event_card = None
        self.city_graph = {
            "atlanta": ["chicago", "washington", "miami"],
            "chicago": ["montreal", "atlanta", "san francisco", "los angeles", "mexico city"],
            "washington": ["atlanta", "montreal", "new york"],
            "miami": ["atlanta", "washington", "mexico city", "bogota"],
            "montreal": ["chicago", "washington", "new york"],
            "san francisco": ["chicago", "los angeles", "tokyo", "manila"],
            "los angeles": ["san francisco", "chicago", "mexico city", "sydney"],
            "new york": ["washington", "montreal", "london", "madrid"],
            "london": ["new york", "madrid", "paris", "essen"],
            "madrid": ["new york", "london", "paris", "sao paulo"],
            "paris": ["madrid", "london", "essen", "algiers", "milan"],
            "essen": ["london", "paris", "st petersburg", "milan"],
            "algiers": ["madrid", "paris", "istanbul", "cairo"],
            "mexico city": ["los angeles", "chicago", "miami", "bogota", "lima"],
            "milan": ["istanbul", "paris", "essen"],
            "st petersburg": ["essen", "istanbul", "moscow"],
            "istanbul": ["milan", "baghdad", "cairo", "algiers"],
            "cairo": ["algiers", "istanbul", "baghdad", "riyadh", "khartoum"],
            "moscow": ["istanbul", "st petersburg", "tehran"],
            "baghdad": ["tehran", "istanbul", "cairo", "karachi", "riyadh"],
            "riyadh": ["cairo", "baghdad",  "karachi"],
            "tehran": ["baghdad", "delhi",  "karachi"],
            "karachi": ["tehran", "delhi",  "baghdad", "riyadh", "mumbai"],
            "delhi": ["mumbai", "tehran",  "karachi", "kolkata", "chennai"],
            "mumbai": ["karachi", "delhi", "chennai"],
            "kolkata": ["delhi", "chennai", "bangkok", "hong kong"],
            "hong kong": ["kolkata", "bangkok", "shanghai", "taipei", "ho chi minh", "manila"],
            "taipei": ["hong kong", "manila", "shanghai", "osaka"],
            "shanghai": ["beijing", "hong kong", "taipei", "tokyo", "seoul"],
            "beijing": ["shanghai", "seoul"],
            "seoul": ["beijing", "shanghai", "tokyo"],
            "tokyo": ["seoul", "shanghai", "osaka", "san francisco"],
            "osaka": ["tokyo", "taipei"],
            "bangkok": ["chennai", "jakarta", "ho chi minh", "hong kong", "kolkata"],
            "manila": ["san francisco", "taipei", "ho chi minh", "hong kong", "sydney"],
            "ho chi minh": ["manila", "bangkok", "jakarta", "hong kong"],
            "jakarta": ["ho chi minh", "bangkok", "chennai", "sydney"],
            "sydney": ["jakarta", "manila", "los angeles"],
            "chennai": ["jakarta", "bangkok", "mumbai", "delhi", "kolkata"],
            "khartoum": ["cairo", "lagos", "kinshasa", "johannesburg"],
            "johannesburg": ["khartoum", "kinshasa"],
            "kinshasa": ["khartoum", "johannesburg", "lagos"],
            "lagos": ["khartoum", "kinshasa", "sao paulo"],
            "sao paulo": ["madrid", "lagos", "bogota", "buenos aires"],
            "buenos aires": ["sao paulo", "bogota"],
            "lima": ["santiago", "bogota", "mexico city"],
            "santiago": ["lima"],
            "bogota": ["lima", "buenos aires", "sao paulo", "mexico city", "miami"],
        }
        self.city_colors = {
            "madrid": "blue",
            "paris": "blue",
            "chicago": "blue",
            "essen": "blue",
            "new york": "blue",
            "san francisco": "blue",
            "milan": "blue",
            "london": "blue",
            "st petersburg": "blue",
            "washington": "blue",
            "montreal": "blue",
            "atlanta": "blue",

            "osaka": "red",
            "beijing": "red",
            "taipei": "red",
            "seoul": "red",
            "shanghai": "red",
            "bangkok": "red",
            "manila": "red",
            "jakarta": "red",
            "hong kong": "red",
            "sydney": "red",
            "tokyo": "red",
            "ho chi minh": "red",

            "moscow": "black",
            "baghdad": "black",
            "cairo": "black",
            "riyadh": "black",
            "delhi": "black",
            "kolkata": "black",
            "karachi": "black",
            "algiers": "black",
            "istanbul": "black",
            "tehran": "black",
            "chennai": "black",
            "mumbai": "black",

            "sao paulo": "yellow",
            "lagos": "yellow",
            "kinshasa": "yellow",
            "buenos aires": "yellow",
            "mexico city": "yellow",
            "bogota": "yellow",
            "johannesburg": "yellow",
            "khartoum": "yellow",
            "lima": "yellow",
            "los angeles": "yellow",
            "santiago": "yellow",
            "miami": "yellow",
        }
        self.all_colors = set(self.city_colors.values())
        self.event_map = {
            fn.__name__: fn for fn in [
                self.government_grant,
                self.resilient_population,
                self.airlift,
                self.forecast,
                self.one_quiet_night,
            ]
        }
        self.action_map = {
            fn.__name__: fn for fn in [
                self.drive,
                self.direct_flight,
                self.charter_flight,
                self.shuttle_flight,
                self.dispatch_flight,
                self.dispatch_move,
                self.operations_move,
                self.treat_disease,
                self.build_research_station,
                self.share_knowledge,
                self.discover_cure,
            ]
        }
        self.current_board = {}
        self.research_stations = set()
        self.total_disease_cubes_on_board_per_color = {color: 0 for color in self.all_colors}
        self.max_disease_cubes_per_color = max_disease_cubes_per_color
        self.infection_deck = list(self.city_graph.keys())
        if not self.testing:
            self.shuffle_infection_deck()
        self.infection_discard = []
        self.player_deck = []
        self.player_discard = []
        self.player_hands = {}
        # map of disease colors to boolean indicating whether the disease is also eradicated
        self.cured_diseases = {}
        self.choose_roles()
        self.gen_player_deck()
        self.init_board()
        self.infection_rates = infection_rates
        if len(infection_rates) < self.nepidemics + 1:
            raise ValueError("number of infection rates must at least one greaer than number of epidemics")
        self.infection_rate_i = 0
        self.outbreaks = 0
        self.max_outbreaks = max_outbreaks
        self.forecasted_infection_deck = None
        self.skip_next_infect_cities = False
        if self.testing:
            self.current_player_i = 0
        else:
            self.current_player_i = random.choice(range(len(self.roles)))
        self.did_ops_move = False

    @property
    def current_player(self):
        return self.roles[self.current_player_i]

    @property
    def next_player(self):
        return self.roles[(self.current_player_i + 1) % len(self.roles)]

    def incr_current_player(self):
        self.current_player_i = (self.current_player_i + 1) % len(self.roles)

    @property
    def ndisease_colors(self):
        return len(self.all_colors)
    
    @property
    def infection_rate(self):
        return self.infection_rates[self.infection_rate_i]

    def choose_roles(self):
        if self.testing:
            self.roles = list(range(self.nplayers))
            return
        rng = default_rng()
        self.roles = rng.choice(7, size=self.nplayers, replace=False) 

    def shuffle_infection_deck(self):
        random.shuffle(self.infection_deck)

    def gen_player_deck(self):
        self.player_deck = list(self.city_graph.keys()) + list(self.event_map.keys())
        if not self.testing:
            random.shuffle(self.player_deck)
        self.init_player_hands()
        if self.nepidemics > 0:
            player_deck_split_sz = len(self.player_deck) // self.nepidemics
            remainder = len(self.player_deck) % self.nepidemics
            if self.testing:
                randints = [0] * (self.nepidemics - 1)
                last_randint = 0
            else:
                randints = np.random.randint(player_deck_split_sz, size=self.nepidemics-1)
                last_randint = np.random.randint(player_deck_split_sz + remainder)
            
            epidemic_locations = [
                player_deck_split_sz * i + randints[i]
                for i in range(self.nepidemics-1)
            ]

            epidemic_locations.append(
                player_deck_split_sz * (self.nepidemics-1) + last_randint
            )
            for i, epidemic_loc in enumerate(epidemic_locations):
                self.player_deck = self.player_deck[:epidemic_loc+i] + ["epidemic"] + self.player_deck[epidemic_loc+i:]

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

    def init_board(self):
        self.current_board = {city: {} for city in self.city_colors}
        self.add_research_station("atlanta")
        self.current_player_locations = {
            player: "atlanta"
            for player in self.roles
        }
        initial_infection_cards = self.draw_infection_cards(9)
        # first 3 cities get 3 disease cubes
        # next 3 get 2
        # next 3 get 1
        for i, ndiseases in enumerate(range(3, 0, -1)):
            for city in initial_infection_cards[i*3:(i+1)*3]:
                for _ in range(ndiseases):
                    self.add_disease_cube(city, self.city_colors[city], setup=True)

    def increment_outbreak(self):
        self.outbreaks += 1
        if self.outbreaks == self.max_outbreaks:
            raise GameEnd(False, "outbreak limit")

    def add_disease_cube(self, city, color, prior_neighbors=None, setup=False):
        # if disease is cured and medic is in city, do not place any new cubes
        medic_idx = [i for i, p in enumerate(self.role_powers) if p == "medic"][0]
        if (
            medic_idx in self.roles 
            and self.current_player_locations[medic_idx] == city
            and self.is_cured(color)
        ):
            return

        quarantine_idx = [i for i, p in enumerate(self.role_powers) if p == "quarantine"][0]
        if (
            not setup
            and quarantine_idx in self.roles 
            and (
                self.current_player_locations[quarantine_idx] == city
                or city in self.city_graph[self.current_player_locations[quarantine_idx]]
            )
        ):
            return
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
            self.add_disease_cube(neighbor, color, prior_neighbors=prior_neighbors, setup=setup)

    def has_research_station(self, city):
        return self.current_board[city].get("research_station", False)
    
    def add_research_station(self, city):
        self.current_board[city]["research_station"] = True
        self.research_stations.add(city)

    def cur_city_disease_cubes(self, city, color):
        return self.current_board[city].get(color, 0)

    def init_player_hands(self):
        self.player_hands = {
            player: set(self.draw_player_cards(self.starting_cards_per_hand))
            for player in self.roles
        }

    def is_cured(self, color):
        return color in self.cured_diseases or self.is_eradicated(color)

    def is_eradicated(self, color):
        return self.total_disease_cubes_on_board_per_color[color] == 0

    def remove_cured_if_medic(self, player):
        if self.role_powers[player] == "medic":
            for color in self.all_colors:
                if (
                    self.is_cured(color) 
                    # player's location has >0 {color} dcubes on it
                    and self.current_board[self.current_player_locations[player]].get(color, 0) > 0
                ):
                    self.treat_disease(player, color)

    ##### ACTIONS ###
    def drive(self, player, new_city, **kwargs):
        cur_city = self.current_player_locations[player]
        if new_city not in self.city_graph[cur_city]:
            raise ActionError(f"Unable to move from {cur_city} to {new_city}")
        self.current_player_locations[player] = new_city
        self.remove_cured_if_medic(player)

    def direct_flight(self, player, new_city, player_to_discard=None):
        if new_city not in self.player_hands[player]:
            raise ActionError(f"Player does not have {new_city} in hand")
        if new_city not in self.city_colors:
            raise ActionError(f"{new_city} is not a city")
        self.current_player_locations[player] = new_city
        self.player_discard.append(new_city)

        if player_to_discard is None:
            player_to_discard = player
        elif self.role_powers[player_to_discard] != "dispatcher":
            raise ActionError("player trying to discard other player's cards who's not dispatcher")
        self.player_hands[player_to_discard].remove(new_city)
        self.remove_cured_if_medic(player)

    def charter_flight(self, player, new_city, player_to_discard=None):
        cur_city = self.current_player_locations[player]
        if cur_city not in self.player_hands[player]:
            raise ActionError(f"Player does not have {cur_city} in hand")
        if new_city not in self.city_colors:
            raise ActionError(f"{new_city} is not a city")
        self.current_player_locations[player] = new_city
        self.player_discard.append(cur_city)

        if player_to_discard is None:
            player_to_discard = player
        elif self.role_powers[player_to_discard] != "dispatcher":
            raise ActionError("player trying to discard other player's cards who's not dispatcher")
        self.player_hands[player_to_discard].remove(cur_city)
        self.remove_cured_if_medic(player)

    def shuttle_flight(self, player, new_city):
        cur_city = self.current_player_locations[player]
        if new_city not in self.city_colors:
            raise ActionError(f"{new_city} is not a city")
        if not self.has_research_station(cur_city):
            raise ActionError(f"{cur_city} does not have a research station")
        if not self.has_research_station(new_city):
            raise ActionError(f"{new_city} does not have a research station")
        self.current_player_locations[player] = new_city
        self.remove_cured_if_medic(player)

    def dispatch_flight(self, dispatcher, other_player, new_city):
        if self.role_powers[dispatcher] != "dispatcher":
            raise ActionError("player is not dispatcher")
        if new_city not in self.current_player_locations.values():
            raise ActionError(f"{new_city} does not contain pawn")
        self.current_player_locations[other_player] = new_city
        self.remove_cured_if_medic(other_player)

    def dispatch_move(self, dispatcher, other_player, move_action, move_action_args):
        if self.role_powers[dispatcher] != "dispatcher":
            raise ActionError("player is not dispatcher")
        if move_action not in [
            "drive",
            "direct_flight",
            "charter_flight",
            "shuttle_flight"
        ]:
            raise ActionError("action must a move action")
        self.action_map[move_action](other_player, *move_action_args, player_to_discard=dispatcher)
        self.remove_cured_if_medic(other_player)

    def operations_move(self, ops_player, new_city, card_to_discard):
        if self.role_powers[ops_player] != "operations":
            raise ActionError("player is not operations expert")
        if not self.has_research_station(self.current_player_locations[ops_player]):
            raise ActionError("operations expert not in city with a research station")
        if card_to_discard not in self.player_hands[ops_player]:
            raise ActionError(f"{card_to_discard} not in player's hands")
        if card_to_discard not in self.city_graph:
            raise ActionError(f"{card_to_discard} not a city card")

        self.current_player_locations[ops_player] = new_city
        self.player_hands[ops_player].remove(card_to_discard)

    def treat_disease_internal(self, city, color, is_medic=False):
        ndiseases = self.current_board[city].get(color, 0)
        if ndiseases == 0:
            raise ActionError(f"{city} has no diseases to treat")
        n_to_treat = 1
        if is_medic or color in self.cured_diseases:
            n_to_treat = ndiseases
        self.current_board[city][color] = ndiseases - n_to_treat
        self.total_disease_cubes_on_board_per_color[color] -= n_to_treat

    def treat_disease(self, player, color):
        city = self.current_player_locations[player]
        is_medic = self.role_powers[player] == "medic"
        self.treat_disease_internal(city, color, is_medic=is_medic)

    def build_research_station(self, player):
        city = self.current_player_locations[player]
        if self.has_research_station(city):
            raise ActionError(f"{city} already has station")
        player_is_ops = self.role_powers[player] == "operations"
        if city not in self.player_hands[player] and not player_is_ops:
            raise ActionError(f"do not have matching {city} card")

        self.add_research_station(city)
        if not player_is_ops:
            self.player_hands[player].remove(city)

    def share_knowledge(self, player, giving_player, receiving_player, city):
        assert player in [giving_player, receiving_player]
        g_player_loc = self.current_player_locations[giving_player]
        r_player_loc = self.current_player_locations[giving_player]
        if g_player_loc != r_player_loc:
            raise ActionError(f"{giving_player} not in same city as {receiving_player}")
        g_player_hand = self.player_hands[giving_player]
        if city not in g_player_hand:
            raise ActionError(f"{giving_player} does not have {city} in hand to give")
        if city != g_player_loc and self.role_powers[giving_player] != "researcher":
            raise ActionError(f"{city} does not equal cur location and not giving player is not researcher")
        self.player_hands[giving_player].remove(city)
        self.player_hands[receiving_player].add(city)
        if len(self.player_hands[receiving_player]) > 7:
            if self.interactive:
                discard = self.choose_cards_to_discard_interactive(receiving_player)
            else:
                discard = self.choose_cards_to_discard_policy(receiving_player)
            [self.player_hands[receiving_player].remove(c) for c in discard]
            self.play_discard.extend(discard)

    def discover_cure(self, player, color, matching_city_cards: set):
        if (
            len(matching_city_cards) != 5
            or not (self.role_powers[player] == "scientist" and len(matching_city_cards) == 4)
        ):
            raise ActionError("must play exactly 5 city cards (or 4 for scientist)")
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

    def do_event(self, player, event, *args):
        contingency_event = self.role_powers[player] == "contingency" and event == self.contingency_planner_event_card
        if (
            event not in self.player_hands[player]
            and not contingency_event
        ):
            raise ActionError(f"{event} not in player's hands")
        self.event_fns[event](player, *args)
        if contingency_event:
            self.contingency_planner_event_card = None
        else:
            self.player_hands[player].remove(event)
    
    ### SPECIAL ACTIONS ###
    def contingency_plan(self, player, player_discard_event_index):
        if self.role_powers[player] != "contingency":
            raise ActionError("player must be Contingency Planner")
        if player_discard_event_index >= len(self.player_discard) or player_discard_event_index < 0:
            raise ActionError("player_discard_event_index must be within player discard")
        if self.contingency_planner_event_card is not None:
            raise ActionError("contingency planner already has an event card to be used")
        event_card = self.player_discard[player_discard_event_index]
        if not self.is_event_card(event_card):
            raise ActionError("card in player discard must be an event")
        # remove from discard, and remove from game entirely
        self.player_discard = self.player_discard[:player_discard_event_index] + self.player_discard[player_discard_event_index+1:]
        self.contingency_planner_event_card = event_card
    ######

    def do_action(self, player, action):
        args = tuple()
        kwargs = {}
        if len(action) == 2:
            action, args = action
        elif len(action) == 3:
            action, args, kwargs = action
        elif len(action) > 1:
            raise TurnError("action must be length 1, 2, or 3")
        elif isinstance(action, tuple):
            action = action[0]
        if action == "operations_move":
            if self.did_ops_move:
                raise TurnError("can only do one operations_move per turn")
            self.did_ops_move = True
        
        # could raise ActionError
        self.action_map[action](player, *args, **kwargs)

    # raises TurnErrors, ActionErrors
    def player_turn(self, player, actions):
        self.player_turn_part_1(player, actions)
        self.player_turn_part_2(player)

    def player_turn_part_1(self, player, actions):
        if player != self.current_player:
            raise TurnError(f"player {player} is not current player {self.current_player}")
        if len(actions) != 4:
            raise TurnError("must do 4 actions in a turn")
        # TODO: make idempotent in case of exceptions on later actions
        self.did_ops_move = False
        for action in actions:
            self.do_action(player, action)

    def player_turn_part_2(self, player):
        if player != self.current_player:
            raise TurnError(f"player {player} is not current player {self.current_player}")
        new_cards = list(self.draw_player_cards(self.ncards_to_draw))
        # TODO: if multiple cards in a row are not epidemic, just do discard once instead of each time
        for card in new_cards:
            self.maybe_do_event()
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
                    self.play_discard.extend(discard)
        self.maybe_do_event()
        self.do_infect_step()
        self.maybe_do_event()
        self.incr_current_player()

    def maybe_do_event(self):
        if not self.do_events:
            return
        for player in self.roles:
            do_event = input(f"Player {player}: do event? parameters separated by comma")
            if len(do_event) == 0:
                continue

            if "," in do_event:
                with_params = do_event.split(",")
                do_event, with_params = with_params[0], with_params[1:]
            if do_event and do_event in self.player_hands[player] and do_event in self.event_map:
                self.event_map[do_event](*with_params)

    def airlift(self, player_to_move, city):
        if city not in self.city_graph:
            raise ActionError("city not known")
        self.current_player_locations[player_to_move] = city

    def government_grant(self, city):
        self.add_research_station(city)

    def resilient_population(self, city):
        card = None
        while card is None:
            card = input("Which infection discard to remove?")
            if card not in self.infection_discard:
                print(f"{card} not in infection discard")
                card = None
        self.infection_discard = [c for c in self.infection_discard if c != card]

    def forecast(self, interactive=True):
        if interactive:
            self.forecast_interactive()
        else:
            self.forecast_part_1()
            yield
            self.forecast_part_2()
    def forecast_interactive(self):
        self.forecast_part_1()

        def parse_new_order(new_order):
            new_order = new_order.split(",")
            if len(new_order) != 6:
                return None, "Must be 6 total indexes"
            
            parsed = []
            for idx in new_order:
                try:
                    int_idx = int(idx)
                except:
                    return None, "Must be integers"
                if int_idx < 0 or int_idx > 5:
                    return None, "Indexes must be between 0 and 6"
                parsed.append(int_idx)
            return parsed, None

        parsed = None
        while parsed is None:
            new_order = input("new order? numbered indexes separated by commas")
            parsed, reason = parse_new_order(new_order)
            if parsed is None:
                print(f"incorrect input, reason = {reason}")
        self.forecast_order = new_order
        self.forecast_part_2()

    def forecast_part_1(self):
        self.forecasted_infection_deck = self.infection_deck[-6:]
    def forecast_part_2(self):
        self.forecasted_infection_deck = [self.forecasted_infection_deck[i] for i in self.forecast_order]
        self.infection_deck = self.infection_deck[:-6] + self.forecasted_infection_deck

    def one_quiet_night(self):
        self.skip_next_infect_cities = True

    def do_epidemic(self):
        # increase
        self.infection_rate_i += 1
        # infect
        card = self.infection_deck.pop()
        self.infection_discard.append(card)
        color = self.city_colors[card]
        if not self.is_eradicated(color):
            [self.add_disease_cube(card, color, setup=False) for _ in range(3)]
        self.maybe_do_event()
        # intensify
        random.shuffle(self.infection_discard)
        self.infection_deck.extend(self.infection_discard)
        self.infection_discard = []

    def do_infect_step(self):
        if self.skip_next_infect_cities:
            self.skip_next_infect_cities = False
            return
        cards = self.draw_infection_cards(self.infection_rate)
        for card in cards:
            color = self.city_colors[card]
            if self.is_eradicated(color):
                continue
            self.add_disease_cube(card, color, setup=False)
                
    
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

if __name__ == "__main__":
    game = PandemicGame(4, nepidemics=4, testing=True)
    print("infection deck")
    print(game.infection_deck)
    print("infection discard")
    print(game.infection_discard)
    print("current_board")
    print(game.current_board)
    print("player_hands")
    print(game.player_hands)
    print("player_deck")
    print(game.player_deck)