use std::fmt;

use crate::game_enums::GameEnd;
use crate::pandemic_game::PandemicGameState;

#[derive(Debug, Clone)]
pub struct TurnError {
    pub msg: String,
}
#[derive(Debug, Clone)]
pub struct ActionError {
    pub msg: String,
}
// TODO: these can be done better. Ok?
#[derive(Debug)]
pub enum TurnEndState {
    TErr(TurnError),
    AErr(ActionError),
    Ok(GameEnd),
}
#[derive(Debug)]
pub enum ActionEndState {
    Err(ActionError),
    Ok(GameEnd),
}
impl TurnError {
    pub fn new(msg: String) -> Self {
        Self { msg }
    }
}

impl fmt::Display for TurnError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "{}", self.msg)
    }
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

pub type ActionFn<'a> = &'a dyn Fn(&mut PandemicGameState, usize) -> Result<(), ActionEndState>;

pub struct Agent<'a> {
    pub agent_type: AgentName,
    pub actions: Vec<ActionFn<'a>>,
}
impl<'a> Agent<'a> {
    pub fn new(agent_type: AgentName) -> Self {
        let actions = match agent_type {
            AgentName::Contingency => {
                let contingency_plan: ActionFn =
                    &|state: &mut PandemicGameState, agent_idx: usize| {
                        state.contingency_plan(agent_idx)
                    };
                vec![contingency_plan]
            }
            AgentName::Dispatcher => {
                let dispatch_flight: ActionFn =
                    &|state: &mut PandemicGameState, agent_idx: usize| {
                        state.dispatch_flight(agent_idx)
                    };
                let charter_flight: ActionFn =
                    &|state: &mut PandemicGameState, agent_idx: usize| {
                        state.charter_flight(agent_idx)
                    };
                let direct_flight: ActionFn = &|state: &mut PandemicGameState, agent_idx: usize| {
                    state.direct_flight(agent_idx)
                };
                let dispatch_move: ActionFn = &|state: &mut PandemicGameState, agent_idx: usize| {
                    state.dispatch_move(agent_idx)
                };
                vec![
                    dispatch_flight,
                    charter_flight,
                    direct_flight,
                    dispatch_move,
                ]
            }
            AgentName::Operations => {
                let operations_move: ActionFn =
                    &|state: &mut PandemicGameState, agent_idx: usize| {
                        state.operations_move(agent_idx)
                    };
                vec![operations_move]
            }
            AgentName::Researcher => {
                let share_knowledge: ActionFn =
                    &|state: &mut PandemicGameState, agent_idx: usize| {
                        state.share_knowledge(agent_idx)
                    };
                vec![share_knowledge]
            }
            _ => vec![],
        };
        Self {
            agent_type,
            actions,
        }
    }
}
