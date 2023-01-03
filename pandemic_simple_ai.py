from pandemic_game import PandemicGame
from itertools import combinations_with_replacement
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
        dummy=False):

        self.nactions_per_turn = 4
        self.game = PandemicGame(
            nplayers, 
            nepidemics=nepidemics,
            ncards_to_draw=ncards_to_draw,
            max_disease_cubes_per_color=max_disease_cubes_per_color,
            max_outbreaks=max_outbreaks,
            infection_rates=infection_rates,
            testing=testing
        )
        if dummy:
            self.game = DummyGame()
        self.lookahead_turns = lookahead_turns

    def gen_possible_actions(self, game):
        if isinstance(game, DummyGame):
            return [(sum([i[0] for i in a]), [i[1] for i in a]) for a in combinations_with_replacement(game.possible_actions, 4)]
        raise ValueError()

    def estimate_board_state_score(self, game):
        if isinstance(game, DummyGame):
            return game.score
        raise ValueError

    def run_simulation_turn(self, game):
        cur_player = game.current_player
        possible_actions = self.gen_possible_actions(game)
        scores = []
        for score, actions in possible_actions:
            sim_game = copy.deepcopy(game)
            sim_game.player_turn(cur_player, actions)
            new_score = self.estimate_board_state_score(sim_game)
            # insert sort (only do this if we prune search on some threshold)
            scores.append((sim_game, actions, new_score))
            # for j in range(len(scores)-1, 0, -1):
            #     if scores[j][-1] < scores[j-1][-1]:
            #         tmp = scores[j]
            #         scores[j] = scores[j-1]
            #         scores[j-1] = tmp
            # TODO: can update some internal model with dif between online estimated score and offline estimated new_score
        return scores

    def run_simulation_turn_n(self, n, game):
        # TODO: only reason to keep intermediate scores is to sort them
        # and expand tree based on best score
        # stop running simulation when some amount of clock time expires
        # until then when we just have brute force search (or greedy), only last score matters
        assert n >= 1
        rounds = {}
        for i in range(n):
            rounds[i] = []
            best_score = (None, None, math.inf)
            best_score_i = None
            if i == 0:
                to_enumerate = [(game, None, None)]
            else:
                to_enumerate = rounds[i-1]
            for j, (sim_game, actions, score) in enumerate(to_enumerate):
                new_scores = self.run_simulation_turn(sim_game)
                rounds[i].extend(new_scores)
                best_score_in_new_score = min(new_scores, key=lambda x: x[-1])
                if best_score_in_new_score[-1] < best_score[-1]:
                    best_score = best_score_in_new_score
                    best_score_i = j
                # if new_scores[0][-1] < best_score[-1]:
                #     best_score = new_scores[0]
                #    best_score_i = j
        # TODO: case where branching_factor depends on state of game
        branching_factor = len(rounds[0])
        _, best_score_actions, _ = rounds[i][best_score_i]
        path = [best_score_actions]
        cur_i = best_score_i
        for round in range(i-1, -1, -1):
            path.insert(0, rounds[round][cur_i][1])
            cur_i = cur_i // (branching_factor ** (round))
        return best_score_actions

if __name__ == "__main__":
    for i in range(1, 11):
        ai = SingleAgentRolloutPandemicAI(dummy=True)
        begin = time.time()
        best_score_actions = ai.run_simulation_turn_n(i, ai.game)
        end = time.time()
        print(f"Rounds = {i}, Elapsed = {end - begin}")