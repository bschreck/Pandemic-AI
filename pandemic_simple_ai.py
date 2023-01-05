from pandemic_game import PandemicGame
from itertools import combinations_with_replacement, combinations, permutations
import copy
import math
import time

class DummyGame:
    current_player = 0
    possible_actions = [(-1, "a"), (-2, "b")]
    def __init__(self, *args,**kwargs):
        self.score = 0
    def player_turn(self, player, actions):
        for action in actions:
            if action == "a":
                self.score -= 1
            else:
                self.score -= 2

class SingleAgentRolloutPandemicAI:
    def __init__(
        self, 
        lookahead_turns=2,
        nplayers=4, 
        nepidemics=4,
        ncards_to_draw=2, 
        max_disease_cubes_per_color=24,
        max_outbreaks=8,
        infection_rates=[2, 2, 2, 3, 3, 4, 4],
        testing=False,
        dummy=False,
        do_events=True):

        self.nactions_per_turn = 4
        self.game = PandemicGame(
            nplayers, 
            nepidemics=nepidemics,
            ncards_to_draw=ncards_to_draw,
            max_disease_cubes_per_color=max_disease_cubes_per_color,
            max_outbreaks=max_outbreaks,
            infection_rates=infection_rates,
            testing=testing,
            do_events=do_events,
        )
        if dummy:
            self.game = DummyGame()
        self.lookahead_turns = lookahead_turns

    def gen_drive_actions(self, game, player):
        cur_location = game.current_player_locations[player]
        neighbors = game.city_graph[cur_location]
        return [("drive", (n, )) for n in neighbors]

    def gen_direct_flight_actions(self, game, player):
        # TODO: dispatcher
        cities_in_hand = [
            c for c in game.player_hands[player]
            if c in game.city_graph
        ]
        return [("direct_flight", (c, )) for c in cities_in_hand]

    def gen_charter_flight_actions(self, game, player):
        # TODO: dispatcher
        cur_location = game.current_player_locations[player]
        has_cur_city = False
        for c in game.player_hands[player]:
            if c == cur_location:
                has_cur_city = True
                break
        if has_cur_city:
            return [("charter_flight", (c, )) for c in game.city_graph if c != cur_location]
        return []

    def gen_shuttle_flight_actions(self, game, player):
        cur_location = game.current_player_locations[player]
        if game.has_research_station(cur_location):
            return [
                ("shuttle_flight", (rs,)) for rs in game.research_stations
                if rs != cur_location
            ]
        return []

    def gen_dispatch_flight_actions(self, game, player):
        if game.role_powers[player] != "dispatcher":
            return []
        return [
            ("dispatch_flight", (op, c))
            for op in game.roles
            for c in game.current_player_locations.values()
            if c != game.current_player_locations[op] and player != op
        ]

    def gen_dispatch_move_actions(self, game, player):
        if game.role_powers[player] != "dispatcher":
            return []
        actions = []
        for op in game.roles:
            if op != player:
                for move in ["drive", "direct_flight", "charter_flight", "shuttle_flight"]:
                    fn_name = f"gen_{move}_actions"
                    for mv_action in getattr(self, fn_name)(game, op):
                        actions.append(
                            ("dispatch_move", tuple([op, move, tuple([a for a in mv_action[1]])]))
                        )
        return actions

    def gen_operations_move_actions(self, game, player):
        if game.did_ops_move:
            return []
        if game.role_powers[player] != "operations":
            return []
        cur_location = game.current_player_locations[player]
        if not game.has_research_station(cur_location):
            return []
        actions = []
        for c_to_discard in game.player_hands[player]:
            if c_to_discard  in game.city_graph and c_to_discard != cur_location:
                for new_city in game.city_graph:
                    if new_city not in [c_to_discard, cur_location]:
                        actions.append(("operations_move", (new_city, c_to_discard)))
        return actions

    def gen_treat_disease_actions(self, game, player):
        cur_location = game.current_player_locations[player]
        actions = []
        for color in game.all_colors:
            if game.current_board[cur_location].get(color, 0) > 0:
                actions.append(("treat_disease", (color,)))
        return actions

    def gen_build_research_station_actions(self, game, player):
        cur_location = game.current_player_locations[player]
        if game.has_research_station(cur_location):
            return []
        player_is_ops = game.role_powers[player] == "operations"
        if player_is_ops or cur_location in game.player_hands[player]:
            return [("build_research_station",)]
        return []

    def gen_share_knowledge_actions(self, game, player):
        # TODO: enumerate policies on card discarding if >7
        cur_location = game.current_player_locations[player]
        actions = []
        for op, city in game.current_player_locations.items():
            if op != player and city == cur_location:
                if city in game.player_hands[player]:
                    actions.append(("share_knowledge", (player, op, city)))
                elif city in game.player_hands[op]:
                    actions.append(("share_knowledge", (op, player, city)))
                if game.role_powers[player] == "researcher":
                    for city in game.player_hands[player]:
                        if city != cur_location:
                            actions.append(("share_knowledge", (player, op, city)))
                elif game.role_powers[op] == "researcher":
                    for city in game.player_hands[op]:
                        if city != cur_location:
                            actions.append(("share_knowledge", (op, player, city)))
        return actions

    def gen_discover_cure_actions(self, game, player):
        n_cards_needed = 5
        if game.role_powers[player] == "scientist":
            n_cards_needed = 4
        actions = []
        for color in game.all_colors:
            matching_cards = [
                c for c in game.player_hands[player]
                if game.city_colors.get(c) == color
            ]
            if len(matching_cards) >= n_cards_needed:
                for comb in combinations(matching_cards, n_cards_needed):
                    actions.append(("discover_cure", (color, set(comb))))
        return actions

    def gen_contingency_plan_actions(self, game, player):
        if game.role_powers[player] != "contingency":
            return []
        if game.contingency_planner_event_card is not None:
            return []
        actions = []
        for i, card in enumerate(game.player_discard):
            # if not a city, must be an event
            if card not in game.city_graph:
                actions.append(("contingency_plan", (i,)))
        return actions

    def gen_event_actions(self, game, player):
        actions = []
        events = game.player_hands[player]
        if (
            game.role_powers[player] == "contingency"
            and game.contingency_planner_event_card is not None
        ):
            events.append(game.contingency_planner_event_card)
        for card in events:
            if card == "airlift":
                for player_to_move in game.roles:
                    for city in game.city_graph:
                        if city != game.current_player_locations[player_to_move]:
                            actions.append((card, player_to_move, city))
            elif card == "resilient_population":
                for city in game.infection_discard:
                    actions.append((card, city))
            elif card == "forecast":
                # TODO: this needs to be interactive
                for new_order in permutations(range(6)):
                    actions.append(((card, new_order)))
            elif card == "one_quiet_night":
                actions.append(("one_quiet_night",))
            elif card == "government_grant":
                for city in game.city_graph:
                    if not game.has_research_station(city):
                        actions.append(("government_grant", city))

        return actions
        

    def gen_possible_actions(self, game, max_branching_factor=5):
        # TODO: max_branching_factor and events
        if isinstance(game, DummyGame):
            actions = [(sum([i[0] for i in a]), [i[1] for i in a]) for a in combinations_with_replacement(game.possible_actions, 4)]
            actions = sorted(actions, key=lambda x: x[0])
            return actions[:max_branching_factor]
        player = game.current_player
        actions = (
            self.gen_drive_actions(game, player) +
            self.gen_direct_flight_actions(game, player) + 
            self.gen_charter_flight_actions(game, player) +
            self.gen_shuttle_flight_actions(game, player)+
            self.gen_dispatch_flight_actions(game, player)+
            self.gen_dispatch_move_actions(game, player)+
            self.gen_operations_move_actions(game, player)+
            self.gen_treat_disease_actions(game, player)+
            self.gen_build_research_station_actions(game, player)+
            self.gen_share_knowledge_actions(game, player)+
            self.gen_discover_cure_actions(game, player)+
            self.gen_contingency_plan_actions(game, player)
        )
        events = self.gen_event_actions(game, player)
        return actions

    def estimate_board_state_score(self, game):
        if isinstance(game, DummyGame):
            return game.score
        
        ncube_score = 0
        for city, info in game.current_board.items():
            for color in game.all_colors:
                ncubes = info.get(color, 0)
                if ncubes < 3:
                    ncube_score += ncubes
                else:
                    # DFS for outbreaks
                    stack = [city]
                    visited = set()
                    while len(stack):
                        c = stack.pop()
                        visited.add(c)
                        ncube_score += 1
                        for n in game.city_graph[c]:
                            if n in visited:
                                continue
                            ncubes_on_neighbor = game.current_board[n].get(color, 0)
                            if ncubes_on_neighbor < 3:
                                ncube_score += 1
                            else:
                                stack.append(n)

        ncube_score /= (len(game.all_colors) * game.max_disease_cubes_per_color)
        outbreak_score = game.outbreaks / game.max_outbreaks
        # fraction of diseases cured, negative because more is better
        cured_score = -1 * (sum(game.cured_diseases.values())) / len(game.all_colors)
        # fraction of diseases eradicated, negative because more is better
        eradicated_score = -1 * (sum(1 if game.is_eradicated(c) else 0 for c in game.all_colors) / len(game.all_colors))
        # random numbers here, but weighting cured > eradicated > outbreak > ncube
        return cured_score * 0.5 + eradicated_score * 0.25 + outbreak_score * 0.2 + ncube_score * 0.05

    def run_simulation_action(self, game, action):
        cur_player = game.current_player
        sim_game = copy.deepcopy(game)
        sim_game.do_action(cur_player, action)
        return self.estimate_board_state_score(sim_game), sim_game

    def run_simulation_turn(self, game, max_simulated_branching_factor=5, max_estimated_branching_factor=10):
        # TODO: figure out why we are generating treat disease actions when no diseases to treat in a city
        # TODO events
        cur_player = game.current_player
        rounds = {0: [(None, game, [a]) for a in self.gen_possible_actions(game, max_branching_factor=max_estimated_branching_factor)]}
        for i in range(3):
            round_game_states = []
            for (_, old_game, action_path) in rounds[i]:
                score_estimate, new_game = self.run_simulation_action(old_game, action_path[-1])
                round_game_states.append((score_estimate, new_game, action_path))
            round_game_states = sorted(round_game_states, key=lambda x: x[0])[:max_estimated_branching_factor]
            rounds[i+1] = []
            for (score_estimate, new_game, action_path) in round_game_states:
                for new_action in self.gen_possible_actions(new_game, max_branching_factor=max_estimated_branching_factor):
                    rounds[i+1].append((score_estimate, new_game, action_path + [new_action]))

        scores = []
        for _, game, actions in rounds[3]:
            sim_game = copy.deepcopy(game)
            sim_game.player_turn_part_2(cur_player)
            new_score = self.estimate_board_state_score(sim_game)
            # insert sort so that we can prune based on branching factor
            scores.append((sim_game, cur_player, actions, new_score))
            for j in range(len(scores)-1, 0, -1):
                if scores[j][-1] < scores[j-1][-1]:
                    tmp = scores[j]
                    scores[j] = scores[j-1]
                    scores[j-1] = tmp
            # TODO: can update some internal model with dif between online estimated score and offline estimated new_score
        return scores[:max_simulated_branching_factor]

    def run_simulation_turn_n(self, n, game, max_simulated_branching_factor=5, max_estimated_branching_factor=10):
        # TODO: only reason to keep intermediate scores is to sort them
        # and expand tree based on best score
        # stop running simulation when some amount of clock time expires
        # until then when we just have brute force search (or greedy), only last score matters
        assert n >= 1
        rounds = {}
        for i in range(n):
            rounds[i] = []
            best_score = (None, None, None, math.inf)
            best_score_i = None
            if i == 0:
                to_enumerate = [(game, game.current_player, None, None)]
            else:
                to_enumerate = rounds[i-1]
            for j, (sim_game, player, actions, score) in enumerate(to_enumerate):
                new_scores = self.run_simulation_turn(
                    sim_game, 
                    max_simulated_branching_factor=max_simulated_branching_factor,
                    max_estimated_branching_factor=max_estimated_branching_factor,
                )
                rounds[i].extend(new_scores)
                best_score_in_new_score = min(new_scores, key=lambda x: x[-1])
                if best_score_in_new_score[-1] < best_score[-1]:
                    best_score = best_score_in_new_score
                    best_score_i = j
                # if new_scores[0][-1] < best_score[-1]:
                #     best_score = new_scores[0]
                #    best_score_i = j
        _, player, best_score_actions, score = rounds[i][best_score_i]
        path = [(player, best_score_actions, score)]
        cur_i = best_score_i
        for round in range(i-1, -1, -1):
            _, player, actions, score = rounds[round][cur_i]
            path.insert(0, (player, actions, score))
            cur_i = cur_i // (max_simulated_branching_factor ** (round))
        return path

if __name__ == "__main__":
    ai = SingleAgentRolloutPandemicAI(dummy=False, do_events=False)
    best_score_actions = ai.run_simulation_turn_n(2, ai.game)
    print(best_score_actions)