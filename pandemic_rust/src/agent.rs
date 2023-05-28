use std::fmt;

use crate::pandemic_game::PandemicGame;
use crate::pandemic_game::PandemicGameState;

#[derive(Debug, Clone)]
pub struct ActionError {
    pub msg: String,
}

impl ActionError {
    pub fn new(msg: String) -> Self {
        Self { msg }
    }
}

impl fmt::Display for ActionError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "invalid action: {}", self.msg)
    }
}

#[derive(Debug, Copy, Clone, Hash, PartialEq, Eq, FromPrimitive)]
pub enum AgentName {
    Contingency,
    Dispatcher,
    Medic,
    Operations,
    Quarantine,
    Researcher,
    Scientist,
}

impl AgentName {
    pub fn index(&self) -> usize {
        *self as usize
    }
}

pub type ActionFn<'a> = &'a dyn Fn(&Agent<'a>, &PandemicGame, &mut PandemicGameState);

pub struct Agent<'a> {
    pub agent_type: AgentName,
    pub actions: Vec<ActionFn<'a>>,
}
impl<'a> Agent<'a> {
    pub fn new(agent_type: AgentName) -> Self {
        let actions = match agent_type {
            AgentName::Contingency => {
                let contingency_plan: ActionFn =
                    &|this: &Agent, game: &PandemicGame, state: &mut PandemicGameState| {
                        Self::contingency_plan(this, game, state)
                    };
                vec![contingency_plan]
            }
            AgentName::Dispatcher => {
                let dispatch_flight: ActionFn =
                    &|this: &Agent, game: &PandemicGame, state: &mut PandemicGameState| {
                        Self::dispatch_flight(this, game, state)
                    };
                vec![dispatch_flight]
            }
            _ => vec![],
        };
        Self {
            agent_type,
            actions,
        }
    }
    pub fn dispatch_flight(&self, _game: &PandemicGame, _state: &mut PandemicGameState) {
        println!("Doing dispatch flight");
    }
    pub fn contingency_plan(&self, _game: &PandemicGame, _state: &mut PandemicGameState) {
        println!("Doing contingency plan");
    }
}
