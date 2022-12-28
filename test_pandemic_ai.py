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
            if info != self.current_board[_city]:
                pass
            assert info == self.current_board[_city]

def test_outbreak():
    game = PandemicGame(4)
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


if __name__ == "__main__":
    game = PandemicGame(4)
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