use std::fmt;
use std::collections::{HashMap, HashSet};
use std::mem;
use strum_macros::EnumIter;
use strum::IntoEnumIterator;


use crate::city_graph::{CityCard, city_graph};
use crate::city_graph2::{CityCard2};
use crate::agent::Agent;
use crate::agent::AgentStruct;
use crate::agent::ActionError;
use rand::thread_rng;
use rand::seq::SliceRandom;

#[derive(Debug, EnumIter, PartialEq, Eq, Hash)]
pub enum Disease {
    Blue,
    Red,
    Black,
    Yellow
}

#[derive(Debug, EnumIter, PartialEq, Eq, Hash, Copy, Clone)]
pub enum EventCard {
    GovernmentGrant,
    ResilientPopulation,
    Airlift,
    Forecast,
    OneQuietNight,
}

pub enum PlayerCard {
    CityCard(CityCard),
    EventCard(EventCard),
}
impl PlayerCard {
    pub fn from_city_card(card: CityCard) -> PlayerCard {
        PlayerCard::CityCard(card)
    }
    pub fn from_event_card(card: EventCard) -> PlayerCard {
        PlayerCard::EventCard(card)
    }
}

pub struct PandemicGameState {
    pub board: HashMap<String, HashMap<Disease, u32>>,
    pub research_stations: HashSet<CityCard>,
    pub total_disease_cubes_on_board_per_color: HashMap<Disease, u32>,
    pub infection_deck: Vec<CityCard>,
    pub infection_discard: Vec<CityCard>,
    pub player_deck: Vec<PlayerCard>,
    pub player_discard: Vec<CityCard>,
    pub player_hands: HashMap<Agent, Vec<CityCard>>,
    pub cured_diseases: HashMap<Disease, bool>,
    pub infection_rate_i: u32,
    pub outbreaks: u32,
    pub forecasted_infection_deck: Vec<CityCard>,
    pub skip_next_infect_cities: bool,
    pub players: Vec<Agent>,
    pub current_player_i: u32,
    pub did_ops_move: bool,
}

impl<'a> fmt::Display for PandemicGameState {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(
            f,
            "PandemicGameState: \n\
               board: {board:#?}",
            board=self.board)
    }
}

pub struct PandemicGame<'a> {
    pub nplayers: i32,
    pub nepidemics: i32,
    pub ncards_to_draw: i32,
    pub max_disease_cubes_per_color: i32,
    pub max_outbreaks: i32,
    pub infection_rates: Vec<i32>,
    pub starting_cards_per_hand: i32,
    pub agents: Vec<AgentStruct<'a>>,
    pub city_graph: HashMap<CityCard, Vec<CityCard>>,
    pub events: Vec<EventCard>,
    pub testing: bool,
}

impl<'a> PandemicGame<'a> {
    pub fn new(
        nplayers: i32,
        nepidemics: Option<i32>,
        ncards_to_draw: Option<i32>,
        max_disease_cubes_per_color: Option<i32>,
        max_outbreaks: Option<i32>,
        infection_rates: Option<Vec<i32>>,
        testing: Option<bool>,
    ) -> (Self, PandemicGameState) {
        let starting_cards_per_hand = match nplayers {
            2 => 4,
            3 => 3,
            4 => 2,
            other => panic!("Only 2-4 players supported, {other} players requests")
        };

        let mut cured_diseases: HashMap<Disease, bool> = HashMap::new();
        for d in Disease::iter() {
            cured_diseases.insert(d, false);
        }
        let state = PandemicGameState{
            board: HashMap::new(),
            research_stations: HashSet::new(),
            total_disease_cubes_on_board_per_color: HashMap::new(),
            infection_deck: city_graph().keys().map(|k| *k).collect(),
            infection_discard: Vec::new(),
            player_deck: Vec::new(), // initialize in ::initialize()
            player_discard: Vec::new(),
            player_hands: HashMap::new(), // initialize in ::initialize()
            // map of disease colors to boolean indicating whether the disease is also eradicated
            cured_diseases: cured_diseases,
            infection_rate_i: 0,
            outbreaks: 0,
            forecasted_infection_deck: Vec::new(),
            skip_next_infect_cities: false,
            players: Vec::new(), // initialize in ::initialize()
            current_player_i: 0,
            did_ops_move: false,
        };

        let nepidemics = nepidemics.unwrap_or(4);
        let infection_rates = infection_rates.unwrap_or(vec![2,2,2,3,3,4,4]);
        if (infection_rates.len() as i32) < nepidemics + 1 {
            // TODO: return a Result from this fn instead of panicking
            panic!("Infection rates must be >= self.next_player + 1")
        }

        let mut events: Vec<EventCard> = Vec::new();
        for e in EventCard::iter() {
            events.push(e);
        }

        (Self {
            nplayers,
            nepidemics: nepidemics,
            ncards_to_draw: ncards_to_draw.unwrap_or(2),
            max_disease_cubes_per_color: max_disease_cubes_per_color.unwrap_or(24),
            max_outbreaks: max_outbreaks.unwrap_or(8),
            infection_rates: infection_rates,
            starting_cards_per_hand,
            city_graph: city_graph(),
            agents: vec![
                AgentStruct::new(Agent::Contingency),
                AgentStruct::new(Agent::Dispatcher),
            ],
            events: events,
            testing: testing.unwrap_or(false),
        }, state)
    }
    // TODO: how to call this function inside of ::new()
    // problem is needs to return Self as owned val, but initialize()
    // needs a mutable reference
    pub fn initialize(&mut self, state: PandemicGameState) -> PandemicGameState{
        self.select_roles();

        // TODO: implement these
        let state = self.gen_player_deck(state);
        /*
        if not self.testing:
            self.shuffle_infection_deck()

        self.total_disease_cubes_on_board_per_color = {color: 0 for color in self.all_colors}

        self.init_board()

        if self.testing:
            self.current_player_i = 0
        else:
            self.current_player_i = random.choice(range(len(self.roles)))
        */
        return state
    }
    pub fn gen_player_deck(&mut self, mut state: PandemicGameState) -> PandemicGameState {
        state.player_deck = state.infection_deck.clone().into_iter().map(|c| PlayerCard::from_city_card(c)).collect();
        for event in self.events.clone().into_iter().map(|e| PlayerCard::from_event_card(e)) {
            state.player_deck.push(event);
        }
        if !self.testing {
            state.player_deck.shuffle(&mut thread_rng());
        }

        /* TODO
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
        */
        return state
    }

    pub fn select_roles(&mut self) {
        let n_agent_types = mem::variant_count::<Agent>();
        let mut role_indices: Vec<usize> = (0..n_agent_types).collect();
        role_indices.shuffle(&mut thread_rng());
        let agents = (0..self.nplayers).map(|p| -> AgentStruct {
            let agent_type = num::FromPrimitive::from_u32(role_indices[p as usize] as u32).unwrap();
            AgentStruct::new(agent_type)
        }).collect();
        self.agents = agents;

    }
    pub fn do_action(&self, agent_idx: usize, action_idx: usize, state: &mut PandemicGameState) -> Result<bool, ActionError>{
        if agent_idx < self.agents.len() {
            let agent = &self.agents[agent_idx];
            if action_idx < agent.actions.len() {
                let action_fn = agent.actions[action_idx];
                action_fn(agent, self, state);
                Result::Ok(true)
            } else {
                Result::Err(ActionError::new("action_idx > agent.actions.len()".to_string()))
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
            nepidemics=self.nepidemics)
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
