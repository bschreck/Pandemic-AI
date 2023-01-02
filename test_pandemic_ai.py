import pytest
from pandemic_ai import PandemicGame, ActionError, GameEnd, TurnError
import copy

def test_drive():
    game = PandemicGame(4)
    player = game.roles[0]
    game.drive(player, "new york")
    assert game.current_player_locations[player] == "new york"
    with pytest.raises(ActionError):
        game.drive(player, "lima")

def test_direct_flight():
    game = PandemicGame(4)
    player = game.roles[0]
    player_hand = list(game.player_hands[player])
    for card in player_hand:
        if card in game.city_colors:
            game.direct_flight(player, card)
            assert game.current_player_locations[player] == card
        else:
            with pytest.raises(ActionError):
                game.direct_flight(player, card)
    other_cities = [city for city in game.city_colors if city not in player_hand]
    for city in other_cities:
        print(city)
        with pytest.raises(ActionError):
            game.direct_flight(player, card)
    other_cities = [city for city in game.city_colors if city not in player_hand]
    for city in other_cities:
        print(city)
        with pytest.raises(ActionError):
            game.direct_flight(player, city)
def test_charter_flight():
    game = PandemicGame(4)
    player = game.roles[0]
    player_hand = list(game.player_hands[player])
    if "atlanta" in player_hand:
        game.player_hands[player].remove("atlanta")
    with pytest.raises(ActionError):
        game.charter_flight(player, "new york")
    game.player_hands[player].add("atlanta")
    game.charter_flight(player, "new york")

def test_shuttle_flight():
    game = PandemicGame(4)
    player = game.roles[0]
    player_hand = list(game.player_hands[player])
    with pytest.raises(ActionError):
        game.shuttle_flight(player, "new york")
    game.add_research_station("new york")
    game.shuttle_flight(player, "new york")
    game.drive(player, "tokyo")
    with pytest.raises(ActionError):
        game.shuttle_flight(player, "atlanta")

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
            assert info == self.current_board[_city]


def prep_board_for_simple_outbreak(game, city, color):
    # ensure there are none on city or surrounding
    for _ in range(3):
        for _city in [city] + game.city_graph[city]:
            try:
                game.treat_disease_internal(_city, color)
            except ActionError:
                pass
    # add 3 to city and make sure none get added to rest of board
    with assert_board_unchanged_besides(game, city):
        game.add_disease_cube(city, color)
    with assert_board_unchanged_besides(game, city):
        game.add_disease_cube(city, color)
    with assert_board_unchanged_besides(game, city):
        game.add_disease_cube(city, color)

def prep_board_for_chain_reaction(game, city, color, neighbor):
    assert neighbor in game.city_graph[city]
    # ensure there are none on city or surrounding
    for _ in range(3):
        for _city in [city] + game.city_graph[city]:
            try:
                game.treat_disease_internal(_city, color)
            except ActionError:
                pass
    # add 3 to city and neighbor and make sure none get added to rest of board
    for _ in range(3):
        with assert_board_unchanged_besides(game, city):
            game.add_disease_cube(city, color)
    for _ in range(3):
        with assert_board_unchanged_besides(game, neighbor):
            game.add_disease_cube(neighbor, color)

def assert_outbreak_simple(game, city, color):
    for neighbor in game.city_graph[city]:
        assert game.current_board[neighbor][color] == 1

def assert_outbreak_chain_reaction(game, city, color, neighbor, outbreak_func):
    ndiseases_on_neighbor_neighbors = {
        _city: game.current_board[_city].get(color, 0)
        for _city in game.city_graph[neighbor]
        if _city != city
    }
    outbreak_func()

    assert game.current_board[city][color] == 3
    assert game.current_board[neighbor][color] == 3
    for _city, ndis in ndiseases_on_neighbor_neighbors.items():
        if ndis == 3:
            assert game.current_board[_city][color] == 3
        else:
            assert game.current_board[_city][color] == ndis + 1

def test_outbreak_simple():
    game = PandemicGame(4)
    atl_color = game.city_colors["atlanta"]
    prep_board_for_simple_outbreak(game, "atlanta", atl_color)
    game.add_disease_cube("atlanta", atl_color)
    assert_outbreak_simple(game, "atlanta", atl_color)

def test_outbreak_chain_reaction():
    game = PandemicGame(4)
    atl_color = game.city_colors["atlanta"]
    neighbor = list(game.city_graph["atlanta"])[0]
    prep_board_for_chain_reaction(game, "atlanta", atl_color, neighbor)
    assert_outbreak_chain_reaction(
        game, "atlanta", atl_color, neighbor, 
        lambda: game.add_disease_cube("atlanta", atl_color)
    )

def test_treat_disease():
    game = PandemicGame(4)
    player = game.roles[0]
    # ensure there are 3  on atlanta
    game.add_disease_cube("atlanta", "blue")
    game.add_disease_cube("atlanta", "blue")
    game.add_disease_cube("atlanta", "blue")

    game.treat_disease(player, "blue")
    with pytest.raises(ActionError):
        game.treat_disease(player, "red")
    game.treat_disease(player, "blue")
    game.treat_disease(player, "blue")
    with pytest.raises(ActionError):
        game.treat_disease(player, "blue")

def test_build_research_station():
    game = PandemicGame(4)
    player = game.roles[0]
    with pytest.raises(ActionError):
        game.build_research_station(player)
    game.drive(player, "new york")
    game.build_research_station(player)
    assert game.has_research_station("new york")

def test_share_knowledge():
    game = PandemicGame(4)
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
    
    with pytest.raises(ActionError):
        game.share_knowledge(player1, player2, city)

def test_discover_cure():
    game = PandemicGame(4)
    player = game.roles[0]
    matching_cards = set([city for city, color in game.city_colors.items() if color == "blue"][:5])
    game.player_hands[player] = matching_cards
    game.discover_cure(player, "blue", matching_cards)
    assert len(game.player_hands[player]) == 0
    assert game.is_cured("blue")
    assert not game.is_eradicated("blue")

    game.player_hands[player] = matching_cards
    with pytest.raises(ActionError):
        game.discover_cure(player, "blue", matching_cards)

    del game.cured_diseases["blue"]

    with pytest.raises(ActionError):
        game.discover_cure(player, "blue", set(list(matching_cards)[:4]))

    game.player_hands[player] = set(list(game.player_hands[player])[:4])
    with pytest.raises(ActionError):
        game.discover_cure(player, "blue", matching_cards)

    game.player_hands[player].add("lima")
    with pytest.raises(ActionError):
        game.discover_cure(player, "blue", game.player_hands[player])

def test_eradicate_disease():
    game = PandemicGame(4)
    player = game.roles[0]
    for city, color in game.city_colors.items():
        ndiseases = game.cur_city_disease_cubes(city, color)
        if color == "blue" and ndiseases > 0:
            for _ in range(ndiseases):
                game.treat_disease_internal(city, color)
    assert game.is_eradicated(color)

def test_do_infect_step_simple():
    game = PandemicGame(4)
    top_cards = game.infection_deck[-2:]
    colors = [game.city_colors[c] for c in top_cards]
    for card, color in zip(top_cards, colors):
        game.current_board[card][color] = 0
    game.do_infect_step()
    for card, color in zip(top_cards, colors):
        assert game.current_board[card][color] == 1

def test_do_infect_step_outbreak():
    game = PandemicGame(4)
    top_cards = game.infection_deck[-2:]
    colors = [game.city_colors[c] for c in top_cards]
    game.current_board[top_cards[0]][colors[0]] = 0
    prep_board_for_simple_outbreak(game, top_cards[1], colors[1])
    game.do_infect_step()
    assert_outbreak_simple(game, top_cards[1], colors[1])

def test_do_infect_step_outbreak_chain_reaction():
    game = PandemicGame(4)
    top_cards = game.infection_deck[-2:]
    colors = [game.city_colors[c] for c in top_cards]
    game.current_board[top_cards[0]][colors[0]] = 0
    neighbor = game.city_graph[top_cards[1]][0]
    prep_board_for_chain_reaction(game, top_cards[1], colors[1], neighbor)
    assert_outbreak_chain_reaction(
        game, top_cards[1], colors[1], neighbor,
        lambda: game.do_infect_step()
    )
    
def test_do_epidemic():
    infection_rates = [2,2,4,5, 6]
    game = PandemicGame(4, nepidemics=4, infection_rates=infection_rates)
    assert game.infection_rate == infection_rates[0]
    for i in range(2):
        topcard = game.infection_deck[-1]
        neighbors = game.city_graph[topcard]
        color = game.city_colors[topcard]
        prev_ndisease_cubes = game.current_board[topcard].get(color, 0)
        prev_neighbor_dcubes = {n: game.current_board[n].get(color, 0) for n in neighbors}
        prev_infection_discard = game.infection_discard[:]
        game.do_epidemic()
        assert game.infection_rate == infection_rates[i+1]
        assert game.current_board[topcard][color] == min(3, prev_ndisease_cubes+3)
        if prev_ndisease_cubes > 0:
            for n, prev_dcubes in prev_neighbor_dcubes.items():
                # doesn't test chain reaction precisely, but its tested elsewhere
                assert game.current_board[n][color] >= min(3, prev_dcubes+1)
        # shuffled infection discard placed back on top of deck
        assert len(game.infection_discard) == 0
        assert set(game.infection_deck[-(len(prev_infection_discard)+1):]) == set(prev_infection_discard + [topcard])
        # shuffling could result in exact same order, causing this to fail, but exceedingly unlikely so if it happens just rerun test
        assert game.infection_deck[-len(prev_infection_discard):] != prev_infection_discard + [topcard]
        assert game.infection_deck[-len(prev_infection_discard):] != [topcard] + prev_infection_discard

def test_do_epidemic_eradicated():
    infection_rates = [2,2,4,5, 6]
    game = PandemicGame(4, nepidemics=4, infection_rates=infection_rates)
    assert game.infection_rate == infection_rates[0]

    # eradicate all blue dcubes
    blue_cities = [city for city, color in game.city_colors.items() if color == "blue"]
    for city in blue_cities:
        dcubes = game.current_board[city].get("blue", 0)
        [game.treat_disease_internal(city, "blue") for _ in range(dcubes)]
    assert game.is_eradicated("blue")

    # make sure there is a blue card on top
    for i in range(len(game.infection_deck) // game.infection_rate):
        if "blue" in [game.city_colors[c] for c in game.infection_deck[-game.infection_rate:]]:
            break
        game.do_infect_step()


    infection_rate = game.infection_rate
    for i in range(infection_rate):
        topcard = game.infection_deck[-1]
        neighbors = game.city_graph[topcard]
        color = game.city_colors[topcard]
        prev_ndisease_cubes = game.current_board[topcard].get(color, 0)
        prev_neighbor_dcubes = {n: game.current_board[n].get(color, 0) for n in neighbors}
        prev_infection_discard = game.infection_discard[:]
        game.do_epidemic()
        if color != "blue":
            continue
        found_blue = True
        assert game.infection_rate == infection_rates[i]
        # no new dcubes
        assert game.current_board[topcard].get(color, 0) == prev_ndisease_cubes
        # shuffled infection discard placed back on top of deck
        assert len(game.infection_discard) == 0
        assert set(game.infection_deck[-(len(prev_infection_discard)+1):]) == set(prev_infection_discard + [topcard])
        # shuffling could result in exact same order, causing this to fail, but exceedingly unlikely so if it happens just rerun test
        assert game.infection_deck[-len(prev_infection_discard):] != prev_infection_discard + [topcard]
        assert game.infection_deck[-len(prev_infection_discard):] != [topcard] + prev_infection_discard
    # something weird happened
    assert found_blue

def test_do_player_turn():
    """
    Starting infection deck:
    ['atlanta', 'new york', 'paris', 'lima'

    Starting infection discard
    ['tehran', 'tokyo', 'sao paulo', 'essen', 'ho chi minh', 'sydney', 'manila', 'chicago', 'london']

    Starting game board:

    {'atlanta': {'research_station': True},
     'new york': {},
     'lima': {},
     'paris': {},
     'tokyo': {'red': 3},
     'tehran': {'black': 3},
     'sao paulo': {'yellow': 3},
     'essen': {'blue': 2},
     'ho chi minh': {'red': 2},
     'sydney': {'red': 2},
     'manila': {'red': 1},
     'chicago': {'blue': 1},
     'london': {'blue': 1}}

    Starting player hands:
    {
        0: {'build research station', 'fly somewhere'},
        1: {'khartoum', 'london'},
        2: {'manila', 'chicago'},
        3: {'sydney', 'ho chi minh'}
    }

    Starting player deck without epidemics
    ['atlanta', 'new york', 'paris', 'lima', 'tehran', 'tokyo', 'sao paulo', 'essen']
    Starting player deck with epidemics
    ['epidemic', 'atlanta', 'new york', 'epidemic', 'paris', 'lima', 'epidemic', 'tehran', 'tokyo', 'epidemic', 'sao paulo', 'essen']

    """
    game = PandemicGame(4, nepidemics=0, testing=True)
    # TODO: test discover_cure and disallowed actions
    allowed_actions_to_test = {
        0: [
                ["drive", ("new york",)],
                ["drive", ("chicago",)],
                ["drive", ("manila",)],
                ["drive", ("chicago",)],
            ],
        1: [
                ["direct_flight", ("london",)],
                ["drive", ("new york",)],
                ["drive", ("khartoum",)],
                ["charter_flight", ("khartoum",)],

            ],
        2: [
                ["direct_flight", ("chicago",)],
                ["drive", ("manila",)],
                ["drive", ("sydney",)],
                ["build_research_station"],

            ],
        3: [
                ["shuttle_flight", ("sydney",)],
                ["drive", ("manila",)],
                ["drive", ("chicago",)],
                ["share_knowledge", (3, 0, "ho chi minh",)],
            ]
    }

    prev_game_board = game.current_board
    player = 0
    actions = allowed_actions_to_test[player]
    with pytest.raises(TurnError):
        game.player_turn(player, actions[:3])
    assert prev_game_board == game.current_board
    with pytest.raises(TurnError):
        game.player_turn(player, actions + [actions[0]])
    assert prev_game_board == game.current_board

    for player, actions in allowed_actions_to_test.items():
        game.player_turn(player, actions)

#    disallowed_actions_to_test = {
#     ["drive", ("new york",)],
#     ["drive", ("tokyo",)],
#     ["drive", ("tehran",)],
#     ["drive", ("new york",)],
#    }
#    with pytest.raises(ActionError):
#        game.player_turn(player, disallowed_actions_to_test[:4])