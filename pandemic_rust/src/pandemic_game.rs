use std::collections::{HashMap, HashSet};
use std::fmt;
use std::mem;
use strum::IntoEnumIterator;

use crate::agent::ActionError;
use crate::agent::Agent;
use crate::agent::AgentName;
use crate::city_graph::{city_diseases, city_graph, CityCard};
use crate::game_enums::{Disease, EventCard, PlayerCard};
use rand::seq::SliceRandom;
use rand::{thread_rng, Rng};

impl PlayerCard {
    pub fn from_city_card(card: CityCard) -> PlayerCard {
        PlayerCard::CityCard(card)
    }
    pub fn from_event_card(card: EventCard) -> PlayerCard {
        PlayerCard::EventCard(card)
    }
}

pub struct PandemicGameState {
    pub cur_city_diseases: HashMap<CityCard, HashMap<Disease, u32>>,
    pub player_locations: HashMap<AgentName, CityCard>,
    pub research_stations: HashSet<CityCard>,
    pub total_disease_cubes_on_board_per_color: HashMap<Disease, u32>,
    pub infection_deck: Vec<CityCard>,
    pub infection_discard: Vec<CityCard>,
    pub player_deck: Vec<PlayerCard>,
    pub player_discard: Vec<CityCard>,
    pub player_hands: HashMap<AgentName, Vec<CityCard>>,
    pub cured_diseases: HashMap<Disease, bool>,
    pub infection_rate_i: u32,
    pub outbreaks: u32,
    pub forecasted_infection_deck: Vec<CityCard>,
    pub skip_next_infect_cities: bool,
    pub players: Vec<AgentName>,
    pub current_player_i: u32,
    pub did_ops_move: bool,
    rng: rand::rngs::ThreadRng,
}

impl<'a> fmt::Display for PandemicGameState {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(
            f,
            "PandemicGameState: \n\
               board: {city_diseases:#?}",
            city_diseases = self.cur_city_diseases
        )
    }
}

pub struct PandemicGame<'a> {
    pub nplayers: i32,
    pub nepidemics: i32,
    pub ncards_to_draw: i32,
    pub max_disease_cubes_per_color: u32,
    pub max_outbreaks: u32,
    pub infection_rates: Vec<i32>,
    pub starting_cards_per_hand: i32,
    pub agents: Vec<Agent<'a>>,
    pub city_graph: HashMap<CityCard, Vec<CityCard>>,
    pub city_diseases: HashMap<CityCard, Disease>,
    pub events: Vec<EventCard>,
    pub testing: bool,
}

impl<'a> PandemicGame<'a> {
    pub fn new(
        nplayers: i32,
        nepidemics: Option<i32>,
        ncards_to_draw: Option<i32>,
        max_disease_cubes_per_color: Option<u32>,
        max_outbreaks: Option<u32>,
        infection_rates: Option<Vec<i32>>,
        testing: Option<bool>,
    ) -> (Self, PandemicGameState) {
        let starting_cards_per_hand = match nplayers {
            2 => 4,
            3 => 3,
            4 => 2,
            other => panic!("Only 2-4 players supported, {other} players requests"),
        };

        let mut cured_diseases: HashMap<Disease, bool> = HashMap::new();
        for d in Disease::iter() {
            cured_diseases.insert(d, false);
        }
        let state = PandemicGameState {
            cur_city_diseases: HashMap::new(),
            player_locations: HashMap::new(),
            research_stations: HashSet::new(),
            total_disease_cubes_on_board_per_color: HashMap::new(),
            infection_deck: city_graph().keys().map(|k| *k).collect(),
            infection_discard: Vec::new(),
            player_deck: Vec::new(), // initialize in ::initialize()
            player_discard: Vec::new(),
            player_hands: HashMap::new(), // initialize in ::initialize()
            // map of disease colors to boolean indicating whether the disease is also eradicated
            cured_diseases,
            infection_rate_i: 0,
            outbreaks: 0,
            forecasted_infection_deck: Vec::new(),
            skip_next_infect_cities: false,
            players: Vec::new(), // initialize in ::initialize()
            current_player_i: 0,
            did_ops_move: false,
            rng: thread_rng(),
        };

        let nepidemics = nepidemics.unwrap_or(4);
        let infection_rates = infection_rates.unwrap_or(vec![2, 2, 2, 3, 3, 4, 4]);
        if (infection_rates.len() as i32) < nepidemics + 1 {
            // TODO: return a Result from this fn instead of panicking
            panic!("Infection rates must be >= self.next_player + 1")
        }

        let mut events: Vec<EventCard> = Vec::new();
        for e in EventCard::iter() {
            events.push(e);
        }

        (
            Self {
                nplayers,
                nepidemics,
                ncards_to_draw: ncards_to_draw.unwrap_or(2),
                max_disease_cubes_per_color: max_disease_cubes_per_color.unwrap_or(24),
                max_outbreaks: max_outbreaks.unwrap_or(8),
                infection_rates,
                starting_cards_per_hand,
                city_graph: city_graph(),
                agents: vec![
                    Agent::new(AgentName::Contingency),
                    Agent::new(AgentName::Dispatcher),
                ],
                events,
                testing: testing.unwrap_or(false),
                city_diseases: city_diseases(),
            },
            state,
        )
    }
    // TODO: how to call this function inside of ::new()
    // problem is needs to return Self as owned val, but initialize()
    // needs a mutable reference
    // TODO: finish this implementationl
    pub fn initialize(&mut self, state: &mut PandemicGameState) {
        self.select_roles(state);

        self.gen_player_deck(state);
        if !self.testing {
            self.shuffle_infection_deck(state)
        }

        for d in Disease::iter() {
            state.total_disease_cubes_on_board_per_color.insert(d, 0);
        }

        self.init_board(state);

        if self.testing {
            state.current_player_i = 0;
        } else {
            state.current_player_i = state.rng.gen_range(0..self.agents.len() as u32);
        }
    }
    pub fn gen_player_deck(&mut self, state: &mut PandemicGameState) {
        state.player_deck = state
            .infection_deck
            .clone()
            .into_iter()
            .map(PlayerCard::from_city_card)
            .collect();
        for event in self
            .events
            .clone()
            .into_iter()
            .map(PlayerCard::from_event_card)
        {
            state.player_deck.push(event);
        }
        if !self.testing {
            state.player_deck.shuffle(&mut state.rng);
        }

        if self.nepidemics > 0 {
            self.add_epidemic_card_to_player_deck(state);
        }
    }

    pub fn shuffle_infection_deck(&self, state: &mut PandemicGameState) {
        state.infection_deck.shuffle(&mut state.rng);
    }

    pub fn init_board(&self, state: &mut PandemicGameState) {
        for city in self.city_graph.keys() {
            state.cur_city_diseases.insert(*city, HashMap::new());
        }
        self.add_research_station(CityCard::Atlanta, state);
        for agent in &self.agents {
            state
                .player_locations
                .insert(agent.agent_type, CityCard::Atlanta);
        }
        let initial_infection_cards = self.draw_infection_cards(9, state);
        /*
        # first 3 cities get 3 disease cubes
        # next 3 get 2
        # next 3 get 1
        */
        for (i, ndiseases) in (3..0).enumerate() {
            for city in &initial_infection_cards[i * 3..(i + 1) * 3] {
                for _ in 0..ndiseases {
                    self.add_disease_cube(
                        *city,
                        self.city_diseases[city],
                        state,
                        true,
                        &mut HashSet::<CityCard>::new(),
                    );
                }
            }
        }
    }

    pub fn add_disease_cube(
        &self,
        city: CityCard,
        disease: Disease,
        state: &mut PandemicGameState,
        setup: bool,
        prior_neighbors: &mut HashSet<CityCard>,
    ) {
        // todo: medic/quarantine
        let city_diseases = state
            .cur_city_diseases
            .entry(city)
            .or_insert_with(HashMap::new);
        let current_cubes = city_diseases.entry(disease).or_insert(0);

        if *current_cubes < 3 {
            *current_cubes += 1;
            if *state
                .total_disease_cubes_on_board_per_color
                .get(&disease)
                .expect("disease not found")
                < self.max_disease_cubes_per_color
            {
                let cur_per_color_total = state.total_disease_cubes_on_board_per_color[&disease];
                state
                    .total_disease_cubes_on_board_per_color
                    .insert(disease, cur_per_color_total + 1);
            } else {
                // TODO: implement GameEnd
                panic!("GameEnd: disease cube limit");
            }
        } else {
            assert_eq!(*current_cubes, 3);
            self.increment_outbreak(state);
            prior_neighbors.insert(city.clone());
            for neighbor in self.city_graph[&city].clone() {
                if prior_neighbors.contains(&neighbor) {
                    continue;
                }
                self.add_disease_cube(neighbor, disease, state, setup, prior_neighbors);
            }
        }
    }

    pub fn increment_outbreak(&self, state: &mut PandemicGameState) {
        state.outbreaks += 1;
        if state.outbreaks == self.max_outbreaks {
            panic!("GameEnd: outbreak limit");
        }
    }

    pub fn add_research_station(&self, city: CityCard, state: &mut PandemicGameState) {
        state.research_stations.insert(city);
    }

    pub fn draw_infection_cards(
        &self,
        ncards: usize,
        state: &mut PandemicGameState,
    ) -> Vec<CityCard> {
        let mut cards: Vec<CityCard> = Vec::new();
        for _ in 0..ncards {
            if state.infection_deck.len() == 0 {
                return cards;
                // TODO: is this a possible state to get into?
                //state.infection_deck = state.infection_discard.clone();
                //state.infection_discard = Vec::new();
                //state.infection_deck.shuffle(&mut state.rng);
            }
            let card = state.infection_deck.pop().unwrap();
            cards.push(card);
            state.infection_discard.push(card);
        }
        cards
    }

    pub fn add_epidemic_card_to_player_deck(&self, state: &mut PandemicGameState) {
        // TODO: refactor/clean up

        let player_deck_split_sz = state.player_deck.len() / self.nepidemics as usize;
        let mut possible_indices: Vec<usize> = (0..player_deck_split_sz).collect();
        possible_indices.shuffle(&mut state.rng);

        let randints: Vec<usize> = if self.testing {
            (0..self.nepidemics as usize - 1).collect()
        } else {
            possible_indices[0..self.nepidemics as usize - 1].to_vec()
        };

        let mut epidemic_indices: Vec<usize> = randints[..self.nepidemics as usize - 1]
            .to_vec()
            .iter()
            .map(|i| -> usize { player_deck_split_sz * i + randints[*i] })
            .collect();

        let last_rand_int = randints[self.nepidemics as usize - 2];
        let last_index_start = player_deck_split_sz * (self.nepidemics as usize - 1);
        let last_index = last_index_start + last_rand_int;
        epidemic_indices.push(last_index);

        for (i, epidemic_loc) in epidemic_indices.iter().enumerate() {
            state
                .player_deck
                .insert(epidemic_loc + i, PlayerCard::Epidemic);
        }
    }

    pub fn select_roles(&mut self, state: &mut PandemicGameState) {
        let n_agent_types = mem::variant_count::<AgentName>();
        let mut role_indices: Vec<usize> = (0..n_agent_types).collect();
        role_indices.shuffle(&mut state.rng);
        let agents = (0..self.nplayers)
            .map(|p| -> Agent {
                let agent_type =
                    num::FromPrimitive::from_u32(role_indices[p as usize] as u32).unwrap();
                Agent::new(agent_type)
            })
            .collect();
        self.agents = agents;
    }
    pub fn do_action(
        &self,
        agent_idx: usize,
        action_idx: usize,
        state: &mut PandemicGameState,
    ) -> Result<bool, ActionError> {
        if agent_idx < self.agents.len() {
            let agent = &self.agents[agent_idx];
            if action_idx < agent.actions.len() {
                let action_fn = agent.actions[action_idx];
                action_fn(agent, self, state);
                Result::Ok(true)
            } else {
                Result::Err(ActionError::new(
                    "action_idx > agent.actions.len()".to_string(),
                ))
            }
        } else {
            Result::Err(ActionError::new("agent_idx > agents.len()".to_string()))
        }
    }
}

impl<'a> fmt::Display for PandemicGame<'a> {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(
            f,
            "PandemicGame: \n\
               Number of Epidemics: {nepidemics}",
            nepidemics = self.nepidemics
        )
    }
}
/* HIGH LEVEL ARCHITECTURE
 * An event scheduler with discrete timesteps allows arbitrary events to be schedule
 * these events can be different types (PlayerTurn, InfectCities, DoEpidemic, DoEvent, DoAction,
 * etc)
 * A game scheduler is responsible for scheduling the correct events to the event scheduler
 * some events ask players for input
 * At first, all players are governed by the same controller process, so the input gets queried to
 * the same process, with an argument for which player's turn it is
 * Controller bot waits for the game to yield it control, during either a PlayerTurn or
 * PossibleEvent
 * When controller receives control, it receives as args the current state including whose turn
 * it is
 * Controller has its own internal state, relevant to its AI process. It comes up with its next action and yields
 * control back to the scheduler
 * Scheduler does internal housekeeping, including updating game state.
 * Then it returns control to the controller
 * This happens several times per turn (e.g. after each action, and each possibility of doing an
 * event)
 * It also checks game state to figure out if gameplay is over, and who wins
 *
 * FUTURE ISOLATED BUT COOPERATIVE MULTIAGENT ARCHITECTURE
 * This more closely mimics the real game play with multiple collaborative human players
 * There are several independent bots, each representing a player
 * Scheduler yields control to bots when it is their turn (and also on a possibility of playing an
 * event)
 * Each time a bot has control, it can either simply yield control back to the scheduler along with
 * its next action, or it can:
 *   - request advice from any or all other players (i.e. receive a fixed bit length signal from any
 *   other player)
 *   - send out a signal of fixed bit length to any or all other players (e.g. indicating what it's
 *   planning on doing, or what it could do given buy-in from other players)
 *   - Repeat for N rounds, where N is fixed ahead of time
 *
 * AI ALGORITHM
 * This could be arbitrarily complex, but to start we could stick with a simple heuristic search
 * We don't even have to assume adversarial input from any other player, because the game is
 * cooperative-- the enemy is probabilistically bad for us, not adversarial
 * The idea is just to compute a heuristic about the current board state, which is fairly easy to do
 * (e.g. number of diseased cubes, number of outbreaks, etc).
 * And then search through the space of actions and game scheduler moves, where the game scheduler
 * moves can be simulated via monte carlo and assigned expected values (prob of occurence *
 * severity of outcome)
 * This can be done in a massively parallel way, with game state copied over to each thread and
 * simulated indepdently. The simulation process can literally be the gameplay, running many times
 * to with different random seeds to achieve some degree of sampled expected value
 */
