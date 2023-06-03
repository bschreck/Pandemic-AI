use std::collections::{HashMap, HashSet};
use std::fmt;
use std::io::{self, Write};
use std::mem;
use strum::IntoEnumIterator;

use crate::agent::{ActionEndState, ActionError, Agent, AgentName, TurnEndState, TurnError};
use crate::city_graph::{city_diseases, city_graph, CityCard};
use crate::game_enums::{Disease, EventCard, GameEnd, PlayerCard};
use rand::seq::SliceRandom;
use rand::{thread_rng, Rng};

impl PlayerCard {
    pub fn from_city_card(card: CityCard) -> PlayerCard {
        PlayerCard::CityCard(card)
    }
    pub fn from_event_card(card: EventCard) -> PlayerCard {
        PlayerCard::EventCard(card)
    }
    pub fn from_str(s: &str) -> Result<PlayerCard, ()> {
        match s.parse::<EventCard>() {
            Result::Ok(event_card) => Result::Ok(PlayerCard::EventCard(event_card)),
            Result::Err(_) => match s.parse::<CityCard>() {
                Result::Ok(city_card) => Result::Ok(PlayerCard::CityCard(city_card)),
                Result::Err(_) => match s {
                    "Epidemic" => Ok(PlayerCard::Epidemic),
                    _ => Result::Err(()),
                },
            },
        }
    }
    pub fn to_str(self) -> String {
        format!("{:?}", self)
    }
}

pub struct PandemicGameConfig {
    pub nplayers: i32,
    pub nepidemics: i32,
    pub ncards_to_draw: u32,
    pub max_disease_cubes_per_color: u32,
    pub max_outbreaks: u32,
    pub infection_rates: Vec<usize>,
    pub starting_cards_per_hand: i32,
    pub city_graph: HashMap<CityCard, Vec<CityCard>>,
    pub city_diseases: HashMap<CityCard, Disease>,
    pub events: Vec<EventCard>,
    pub testing: bool,
    pub interactive: bool,
    pub do_events: bool,
}

// actions
// special actions
// special stuff for agents
// player_turn
// event stuff
// choose_cards_to_discard

impl fmt::Display for PandemicGameConfig {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(
            f,
            "PandemicGame: \n\
               Number of Epidemics: {nepidemics}",
            nepidemics = self.nepidemics
        )
    }
}
impl PandemicGameConfig {
    pub fn new(
        nplayers: i32,
        nepidemics: Option<i32>,
        ncards_to_draw: Option<u32>,
        max_disease_cubes_per_color: Option<u32>,
        max_outbreaks: Option<u32>,
        infection_rates: Option<Vec<usize>>,
        testing: Option<bool>,
        interactive: Option<bool>,
        do_events: Option<bool>,
    ) -> Self {
        let starting_cards_per_hand = match nplayers {
            2 => 4,
            3 => 3,
            4 => 2,
            other => panic!("Only 2-4 players supported, {other} players requests"),
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

        PandemicGameConfig {
            nplayers,
            nepidemics,
            ncards_to_draw: ncards_to_draw.unwrap_or(2),
            max_disease_cubes_per_color: max_disease_cubes_per_color.unwrap_or(24),
            max_outbreaks: max_outbreaks.unwrap_or(8),
            infection_rates,
            starting_cards_per_hand,
            city_graph: city_graph(),
            events,
            testing: testing.unwrap_or(false),
            city_diseases: city_diseases(),
            interactive: interactive.unwrap_or(true),
            do_events: do_events.unwrap_or(true),
        }
    }
}
pub struct PandemicGameState<'a> {
    pub cur_city_diseases: HashMap<CityCard, HashMap<Disease, u32>>,
    pub player_locations: HashMap<AgentName, CityCard>,
    pub research_stations: HashSet<CityCard>,
    pub total_cubes_on_board_per_disease: HashMap<Disease, u32>,
    pub infection_deck: Vec<CityCard>,
    pub infection_discard: Vec<CityCard>,
    pub player_deck: Vec<PlayerCard>,
    pub player_discard: Vec<PlayerCard>,
    pub player_hands: HashMap<AgentName, HashSet<PlayerCard>>,
    pub cured_diseases: HashSet<Disease>,
    pub infection_rate_i: usize,
    pub outbreaks: u32,
    pub forecasted_infection_deck: Vec<CityCard>,
    pub skip_next_infect_cities: bool,
    pub players: Vec<AgentName>,
    pub current_player_i: u32,
    pub did_ops_move: bool,
    pub agents: Vec<Agent<'a>>,
    rng: rand::rngs::ThreadRng,
    pub config: PandemicGameConfig,
}

impl<'a> fmt::Display for PandemicGameState<'a> {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(
            f,
            "PandemicGameState: \n\
               board: {city_diseases:#?}",
            city_diseases = self.cur_city_diseases
        )
    }
}

impl<'a> PandemicGameState<'a> {
    pub fn new(config: PandemicGameConfig) -> Self {
        let mut state = PandemicGameState {
            cur_city_diseases: HashMap::new(),
            player_locations: HashMap::new(),
            research_stations: HashSet::new(),
            total_cubes_on_board_per_disease: HashMap::new(),
            infection_deck: config.city_graph.keys().map(|k| *k).collect(),
            infection_discard: Vec::new(),
            player_deck: Vec::new(), // initialize in ::initialize()
            player_discard: Vec::new(),
            player_hands: HashMap::new(), // initialize in ::initialize()
            // map of disease colors to boolean indicating whether the disease is also eradicated
            cured_diseases: HashSet::new(),
            infection_rate_i: 0,
            outbreaks: 0,
            forecasted_infection_deck: Vec::new(),
            skip_next_infect_cities: false,
            players: Vec::new(), // initialize in ::initialize()
            current_player_i: 0,
            did_ops_move: false,
            rng: thread_rng(),
            agents: vec![
                Agent::new(AgentName::Contingency),
                Agent::new(AgentName::Dispatcher),
            ],
            config,
        };
        state.initialize();
        state
    }

    // todo: unecessary fn
    pub fn has_research_station(&self, city: CityCard) -> bool {
        self.research_stations.contains(&city)
    }

    pub fn is_eradicated(&self, disease: Disease) -> bool {
        self.total_cubes_on_board_per_disease[&disease] == 0
    }

    pub fn is_cured(self, disease: Disease) -> bool {
        self.cured_diseases.contains(&disease) || self.is_eradicated(disease)
    }

    pub fn init_player_hands(&mut self) {
        let agent_names: Vec<_> = self.agents.iter().map(|a| a.agent_type).collect();
        for agent in agent_names {
            let n = self.config.starting_cards_per_hand as u32;
            let cards = self.draw_player_cards(n).unwrap();
            self.player_hands.insert(agent, cards.into_iter().collect());
        }
    }

    // TODO: how to call this function inside of ::new()
    // problem is needs to return Self as owned val, but initialize()
    // needs a mutable reference
    pub fn initialize(&mut self) {
        self.select_roles();

        self.gen_player_deck();
        if !self.config.testing {
            self.shuffle_infection_deck()
        }

        for d in Disease::iter() {
            self.total_cubes_on_board_per_disease.insert(d, 0);
        }

        self.init_board();

        if self.config.testing {
            self.current_player_i = 0;
        } else {
            self.current_player_i = self.rng.gen_range(0..self.agents.len() as u32);
        }
    }

    pub fn incr_current_player(&mut self) {
        self.current_player_i = (self.current_player_i + 1) % self.agents.len() as u32;
    }

    pub fn current_player(&self) -> &'a Agent {
        &self.agents[self.current_player_i as usize]
    }

    pub fn next_player(&self) -> &'a Agent {
        &self.agents[((self.current_player_i + 1) % self.agents.len() as u32) as usize]
    }

    pub fn infection_rate(&self) -> usize {
        self.config.infection_rates[self.infection_rate_i]
    }

    pub fn gen_player_deck(&mut self) {
        self.player_deck = self
            .infection_deck
            .clone()
            .into_iter()
            .map(PlayerCard::from_city_card)
            .collect();
        for event in self
            .config
            .events
            .clone()
            .into_iter()
            .map(PlayerCard::from_event_card)
        {
            self.player_deck.push(event);
        }
        self.init_player_hands();
        if !self.config.testing {
            self.player_deck.shuffle(&mut self.rng);
        }

        if self.config.nepidemics > 0 {
            self.add_epidemic_card_to_player_deck();
        }
    }

    pub fn shuffle_infection_deck(&mut self) {
        self.infection_deck.shuffle(&mut self.rng);
    }

    pub fn shuffle_infection_discard(&mut self) {
        self.infection_discard.shuffle(&mut self.rng);
    }

    pub fn init_board(&mut self) {
        for city in self.config.city_graph.keys() {
            self.cur_city_diseases.insert(*city, HashMap::new());
        }
        self.add_research_station(CityCard::Atlanta);
        for agent in &self.agents {
            self.player_locations
                .insert(agent.agent_type, CityCard::Atlanta);
        }
        let initial_infection_cards = self.draw_infection_cards(9);
        /*
        # first 3 cities get 3 disease cubes
        # next 3 get 2
        # next 3 get 1
        */
        for (i, ndiseases) in (0..3).rev().enumerate() {
            for city in &initial_infection_cards[i * 3..(i + 1) * 3] {
                for _ in 0..ndiseases {
                    let result =
                        self.add_disease_cube(*city, self.config.city_diseases[city], true);
                    match result {
                        Result::Ok(_) => {}
                        Result::Err(e) => {
                            panic!("Early GameEnd (shouldn't get here): {:?}", e);
                        }
                    }
                }
            }
        }
    }

    pub fn add_disease_cube(
        &mut self,
        city: CityCard,
        disease: Disease,
        setup: bool,
    ) -> Result<(), GameEnd> {
        self._add_disease_cube(city, disease, setup, &mut HashSet::<CityCard>::new())
    }

    fn _add_disease_cube(
        &mut self,
        city: CityCard,
        disease: Disease,
        setup: bool,
        _prior_neighbors: &mut HashSet<CityCard>,
    ) -> Result<(), GameEnd> {
        // todo: medic/quarantine
        let city_diseases = self
            .cur_city_diseases
            .entry(city)
            .or_insert_with(HashMap::new);
        let current_cubes = city_diseases.entry(disease).or_insert(0);

        if *current_cubes < 3 {
            *current_cubes += 1;
            if *self
                .total_cubes_on_board_per_disease
                .get(&disease)
                .expect("disease not found")
                < self.config.max_disease_cubes_per_color
            {
                let cur_per_color_total = self.total_cubes_on_board_per_disease[&disease];
                self.total_cubes_on_board_per_disease
                    .insert(disease, cur_per_color_total + 1);
            } else {
                return Result::Err(GameEnd::DiseaseCubeLimit);
            }
        } else {
            assert_eq!(*current_cubes, 3);
            let result = self.increment_outbreak();
            match result {
                Result::Ok(_) => {}
                Result::Err(e) => {
                    return Result::Err(e);
                }
            }
            _prior_neighbors.insert(city);
            for neighbor in self.config.city_graph[&city].clone() {
                if _prior_neighbors.contains(&neighbor) {
                    continue;
                }
                let result = self._add_disease_cube(neighbor, disease, setup, _prior_neighbors);
                match result {
                    Result::Ok(_) => {}
                    Result::Err(e) => {
                        return Result::Err(e);
                    }
                }
            }
        }
        Result::Ok(())
    }

    pub fn increment_outbreak(&mut self) -> Result<(), GameEnd> {
        self.outbreaks += 1;
        if self.outbreaks == self.config.max_outbreaks {
            return Result::Err(GameEnd::OutbreakLimit);
        }
        Result::Ok(())
    }

    pub fn add_research_station(&mut self, city: CityCard) {
        self.research_stations.insert(city);
    }

    pub fn draw_infection_cards(&mut self, ncards: usize) -> Vec<CityCard> {
        let mut cards: Vec<CityCard> = Vec::new();
        for _ in 0..ncards {
            if self.infection_deck.is_empty() {
                return cards;
                // TODO: is this a possible state to get into?
                //self.infection_deck = self.infection_discard.clone();
                //self.infection_discard = Vec::new();
                //self.infection_deck.shuffle(&mut self.rng);
            }
            let card = self.infection_deck.pop().unwrap();
            cards.push(card);
            self.infection_discard.push(card);
        }
        cards
    }

    pub fn add_epidemic_card_to_player_deck(&mut self) {
        // TODO: refactor/clean up
        let player_deck_split_sz = self.player_deck.len() / self.config.nepidemics as usize;
        let mut possible_indices: Vec<usize> = (0..player_deck_split_sz).collect();
        possible_indices.shuffle(&mut self.rng);

        let randints: Vec<usize> = if self.config.testing {
            (0..self.config.nepidemics as usize - 1).collect()
        } else {
            possible_indices[0..self.config.nepidemics as usize - 1].to_vec()
        };

        let mut epidemic_indices: Vec<usize> = randints[..self.config.nepidemics as usize - 1]
            .to_vec()
            .iter()
            .map(|i| -> usize { player_deck_split_sz * i + randints[*i] })
            .collect();

        let last_rand_int = randints[self.config.nepidemics as usize - 2];
        let last_index_start = player_deck_split_sz * (self.config.nepidemics as usize - 1);
        let last_index = last_index_start + last_rand_int;
        epidemic_indices.push(last_index);

        for (i, epidemic_loc) in epidemic_indices.iter().enumerate() {
            self.player_deck
                .insert(epidemic_loc + i, PlayerCard::Epidemic);
        }
    }

    // how should we initialize agents in init?
    pub fn select_roles(&mut self) {
        let n_agent_types = mem::variant_count::<AgentName>();
        let mut role_indices: Vec<usize> = (0..n_agent_types).collect();
        role_indices.shuffle(&mut self.rng);
        let agents = (0..self.config.nplayers)
            .map(|p| -> Agent {
                let agent_type =
                    num::FromPrimitive::from_u32(role_indices[p as usize] as u32).unwrap();
                Agent::new(agent_type)
            })
            .collect();
        self.agents = agents;
    }

    pub fn do_action(&mut self, agent_idx: usize, action_idx: usize) -> Result<(), ActionEndState> {
        if agent_idx < self.agents.len() {
            let agent = &mut self.agents[agent_idx];
            if action_idx < agent.actions.len() {
                let action_fn = agent.actions[action_idx];
                return action_fn(self, agent_idx);
            } else {
                return Result::Err(ActionEndState::Err(ActionError::new(
                    "action_idx > agent.actions.len()".to_string(),
                )));
            }
        } else {
            return Result::Err(ActionEndState::Err(ActionError::new(
                "agent_idx > agents.len()".to_string(),
            )));
        }
    }

    pub fn draw_player_cards(&mut self, n: u32) -> Result<Vec<PlayerCard>, GameEnd> {
        if n as usize > self.player_deck.len() {
            return Result::Err(GameEnd::PlayerDeckLimit);
        }

        let mut cards: Vec<PlayerCard> = Vec::new();
        for _ in 0..n {
            let card = self.player_deck.pop().unwrap();
            cards.push(card);
        }
        Result::Ok(cards)
    }

    pub fn player_turn(
        &mut self,
        agent_idx: usize,
        actions: Vec<usize>,
    ) -> Result<(), TurnEndState> {
        if agent_idx != self.current_player_i as usize {
            return Result::Err(TurnEndState::TErr(TurnError::new(format!(
                "player {} is not current player {}",
                agent_idx, self.current_player_i,
            ))));
        }
        if actions.len() != 4 {
            return Result::Err(TurnEndState::TErr(TurnError::new(
                "must do 4 actions in a turn".to_string(),
            )));
        }

        match self.player_turn_part_1(agent_idx, actions) {
            Result::Ok(_) => {}
            Result::Err(game_end) => {
                return Result::Err(TurnEndState::Ok(game_end));
            }
        };
        match self.player_turn_part_2(self.agents[agent_idx].agent_type) {
            Result::Ok(_) => Result::Ok(()),
            Result::Err(game_end) => Result::Err(TurnEndState::Ok(game_end)),
        }
    }

    fn player_turn_part_1(&mut self, agent_idx: usize, actions: Vec<usize>) -> Result<(), GameEnd> {
        // TODO: make idempotent in case of exceptions on later actions
        self.did_ops_move = false;
        for action_idx in actions {
            let result = self.do_action(agent_idx, action_idx);
            match result {
                Result::Ok(_) => {}
                Result::Err(ActionEndState::Ok(game_end)) => {
                    return Result::Err(game_end);
                }
                Result::Err(ActionEndState::Err(action_error)) => {
                    panic!("invalid action: {}", action_error.msg)
                }
            }
        }
        Result::Ok(())
    }
    pub fn player_turn_part_2(&mut self, agent: AgentName) -> Result<(), GameEnd> {
        // TODO: if multiple cards in a row are not epidemic, just do discard once instead of each time
        let new_cards = match self.draw_player_cards(self.config.ncards_to_draw.clone()) {
            Result::Ok(cards) => cards,
            Result::Err(game_end) => {
                return Result::Err(game_end);
            }
        };

        for card in new_cards {
            match self.maybe_do_event() {
                Result::Ok(_) => {}
                Result::Err(game_end) => {
                    return Result::Err(game_end);
                }
            };
            if card == PlayerCard::Epidemic {
                match self.do_epidemic() {
                    Result::Ok(_) => {}
                    Result::Err(game_end) => {
                        return Result::Err(game_end);
                    }
                };
            } else {
                self.player_hands
                    .entry(agent)
                    .or_insert_with(HashSet::new)
                    .insert(card);
                if let Some(cards) = self.player_hands.get_mut(&agent) {
                    cards.insert(card);
                }
                if self.player_hands.get_mut(&agent).unwrap().len() > 7 {
                    let discard: Vec<PlayerCard>;
                    if self.config.interactive {
                        discard = self.choose_cards_to_discard_interactive(agent);
                    } else {
                        panic!("policy discard not implemented");
                        // discard = self.choose_cards_to_discard_policy(&agent);
                    }
                    for c in &discard {
                        self.player_hands.get_mut(&agent).unwrap().remove(c);
                    }
                    for card in discard {
                        self.player_discard.push(card);
                    }
                }
            }
        }
        match self.maybe_do_event() {
            Result::Ok(_) => {}
            Result::Err(game_end) => {
                return Result::Err(game_end);
            }
        };
        match self.do_infect_step() {
            Result::Ok(_) => {}
            Result::Err(game_end) => {
                return Result::Err(game_end);
            }
        };
        match self.maybe_do_event() {
            Result::Ok(_) => {}
            Result::Err(game_end) => {
                return Result::Err(game_end);
            }
        }
        self.incr_current_player();
        Result::Ok(())
    }
    pub fn maybe_do_event(&mut self) -> Result<(), GameEnd> {
        if !self.config.do_events {
            return Result::Ok(());
        }
        let agent_types: Vec<AgentName> =
            self.agents.iter().map(|agent| agent.agent_type).collect();
        for agent_type in agent_types {
            let mut input = String::new();
            if self.config.interactive {
                loop {
                    print!(
                        "Player {:?}: do event? parameters separated by comma",
                        agent_type
                    );
                    io::stdout().flush().unwrap();
                    io::stdin()
                        .read_line(&mut input)
                        .expect("Failed to read line");

                    if input.is_empty() {
                        continue;
                    }
                    let do_event: Result<EventCard, _> = input.parse();
                    match do_event {
                        Result::Ok(do_event) => {
                            if self.player_hands[&agent_type]
                                .contains(&PlayerCard::EventCard(do_event))
                            {
                                let result = self.do_event(do_event);
                                match result {
                                    Result::Ok(_) => {}
                                    Result::Err(game_end) => {
                                        return Result::Err(game_end);
                                    }
                                }
                            } else {
                                println!("Invalid event: {:?}", do_event);
                                continue;
                            }
                            break;
                        }
                        Result::Err(e) => {
                            println!("Invalid event: {:?}", e);
                            continue;
                        }
                    }
                }
            } else {
                panic!("policy events not implemented");
                // do_event = self.do_event_from_policy(agent_type);
            }
        }
        Result::Ok(())
    }

    pub fn do_event(&mut self, event: EventCard) -> Result<(), GameEnd> {
        match event {
            EventCard::Airlift => self.airlift(),
            EventCard::GovernmentGrant => self.governemnt_grant(),
            EventCard::ResilientPopulation => self.resilient_population(),
            EventCard::Forecast => self.forecast(),
            EventCard::OneQuietNight => self.one_quiet_night(),
        }
    }

    pub fn airlift(&mut self) -> Result<(), GameEnd> {
        // get player_to_movve and city from input
        Result::Ok(())
    }
    pub fn governemnt_grant(&mut self) -> Result<(), GameEnd> {
        // get city from input
        Result::Ok(())
    }
    pub fn resilient_population(&mut self) -> Result<(), GameEnd> {
        // get infection discard card from input
        Result::Ok(())
    }
    pub fn forecast(&mut self) -> Result<(), GameEnd> {
        // forecast_part1 and forecast_part2
        Result::Ok(())
    }
    pub fn one_quiet_night(&mut self) -> Result<(), GameEnd> {
        self.skip_next_infect_cities = true;
        Result::Ok(())
    }
    pub fn do_infect_step(&mut self) -> Result<(), GameEnd> {
        if self.skip_next_infect_cities {
            self.skip_next_infect_cities = false;
            return Result::Ok(());
        }
        let cards = self.draw_infection_cards(self.infection_rate());
        for card in cards {
            let disease = self
                .config
                .city_diseases
                .get(&card)
                .expect("City card not found in city disease map");
            if self.is_eradicated(*disease) {
                continue;
            }
            match self.add_disease_cube(card, *disease, false) {
                Result::Ok(_) => {}
                Result::Err(game_end) => {
                    return Result::Err(game_end);
                }
            };
        }
        Result::Ok(())
    }

    pub fn do_epidemic(&mut self) -> Result<(), GameEnd> {
        // increase
        self.infection_rate_i += 1;
        // infect
        let card = self
            .infection_deck
            .pop()
            .expect("infection deck should not be empty");
        self.infection_discard.push(card);
        // TODO: encapsulate this in a method, along with other locations its used
        let disease = self
            .config
            .city_diseases
            .get(&card)
            .expect("City card not found in city disease map");
        if !self.is_eradicated(*disease) {}
        match self.maybe_do_event() {
            Result::Ok(_) => {}
            Result::Err(game_end) => {
                return Result::Err(game_end);
            }
        };
        // intensify
        self.shuffle_infection_discard();
        for _ in 0..self.infection_discard.len() {
            self.infection_deck
                .push(self.infection_discard.pop().expect("should not panic"));
        }
        Result::Ok(())
    }

    pub fn choose_cards_to_discard_interactive(&self, agent: AgentName) -> Vec<PlayerCard> {
        let hand = &self.player_hands[&agent];
        if hand.len() <= 7 {
            // TODO: return Result. is this a state that can happen?
            panic!("hand not too big")
        }
        let hand_strs: Vec<String> = hand.iter().map(|c| c.to_str()).collect();
        println!("Current hand: {}", hand_strs.join(", "));

        let mut cards_to_discard = vec![];
        while cards_to_discard.len() != hand.len() - 7
            && cards_to_discard.iter().all(|card| hand.contains(card))
        {
            println!("Enter cards to discard separated by comma");
            let mut input = String::new();
            io::stdin()
                .read_line(&mut input)
                .expect("Failed to read line");
            let input_trimmed = input.trim();
            let cards: Vec<PlayerCard> = input_trimmed
                .split(',')
                .map(|s| PlayerCard::from_str(s).expect("Failed to parse PlayerCard"))
                .collect();
            cards_to_discard = cards;
        }
        cards_to_discard
    }

    pub fn dispatch_flight(&mut self, _agent_idx: usize) -> Result<(), ActionEndState> {
        println!("Doing dispatch flight");
        Result::Ok(())
    }
    pub fn contingency_plan(&mut self, _agent_idx: usize) -> Result<(), ActionEndState> {
        println!("Doing contingency plan");
        Result::Ok(())
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
