use std::fmt;
use std::fs;


#[derive(Debug, Clone)]
struct ActionError{
    msg: String
}

impl fmt::Display for ActionError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "invalid action: {}", self.msg)
    }
}

#[derive(Debug)]
enum CityCard {
    NewYork
}

enum Agent {
    Contingency(ContingencyAgent),
    Dispatcher(DispatcherAgent),
    //Medic,
 //   Operations, 
 //   Quarantine, 
 //   Researcher, 
 //   Scientist
}

type ActionFn = dyn Fn(&mut Agent, &mut PandemicGame);
trait Actions {
    fn actions(&self) -> Vec<&ActionFn>;
}

struct ContingencyAgent;
struct DispatcherAgent;

impl Agent {
    fn contingency_plan(&mut self, _game: &mut PandemicGame) {
        println!("Doing contingency plan");
    }
    fn dispatch_flight(&mut self, _game: &mut PandemicGame) {
        println!("Doing dispatch flight");
    }
}

impl Actions for Agent {
    fn actions(&self) -> Vec<&ActionFn> {
        match self {
            Agent::Contingency(ContingencyAgent) => {
                vec![&(Agent::contingency_plan)]
            },
            Agent::Dispatcher(DispatcherAgent) => {
                vec![&(Agent::dispatch_flight)]
            }
        }
    }
}

struct PandemicGame {
    nplayers: i32,
    infection_deck: Vec<CityCard>,
    nepidemics: i32,
    ncards_to_draw: i32,
    max_disease_cubes_per_color: i32,
    max_outbreaks: i32,
    infection_rates: Vec<i32>,
    starting_cards_per_hand: i32,
    city_graph: json::JsonValue,
}

impl PandemicGame {
    fn new(
        nplayers: i32, 
        nepidemics: Option<i32>,
        ncards_to_draw: Option<i32>,
        max_disease_cubes_per_color: Option<i32>,
        max_outbreaks: Option<i32>,
        infection_rates: Option<Vec<i32>>,
        city_graph_file_path: Option<String>,
    ) -> Self {
        let starting_cards_per_hand = match nplayers {
            2 => 4,
            3 => 3,
            4 => 2,
            other => panic!("Only 2-4 players supported, {other} players requests")
        };
        let city_graph_str: String;
        if let Some(city_graph_file_path ) = city_graph_file_path {
            city_graph_str = fs::read_to_string(city_graph_file_path)
            .expect("Should have been able to read the city graph file");
        } else {
            city_graph_str = include_str!("city_graph.json").to_string();
        }
            
        let city_graph = json::parse(&city_graph_str)
            .expect("Should have been able to parse the city graph into json");
        Self {
            nplayers,
            nepidemics: nepidemics.unwrap_or(4),
            ncards_to_draw: ncards_to_draw.unwrap_or(2),
            max_disease_cubes_per_color: max_disease_cubes_per_color.unwrap_or(24),
            max_outbreaks: max_outbreaks.unwrap_or(8),
            infection_rates: infection_rates.unwrap_or(vec![2,2,2,3,3,4,4]),
            infection_deck: vec![CityCard::NewYork],
            starting_cards_per_hand,
            city_graph
        }

    }
}

impl fmt::Display for PandemicGame {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(
            f, 
            "PandemicGame: \n\
               InfectionDeck: {infection_deck:#?}\n\
               Number of Epidemics: {nepidemics}", 
            infection_deck="replacement",//self.infection_deck, 
            nepidemics=self.nepidemics)
    }
}

fn main() {
    let game = PandemicGame::new(
        4, 
        None,
        None,
        None,
        None,
        None,
        None);
    println!("infection_deck: {:#?}", game.infection_deck);
    println!("game: {game}");
}