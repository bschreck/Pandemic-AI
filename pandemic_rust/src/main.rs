use pandemic_rust::agent::{ActionEndState, AgentName};
use pandemic_rust::pandemic_game::{PandemicGameConfig, PandemicGameState};

fn check_result(expect_err: bool, result: Result<(), ActionEndState>) {
    match result {
        Ok(_) => {
            if expect_err {
                println!("expected err but found no error");
                panic!()
            }
        }
        Err(result) => match result {
            ActionEndState::Err(err) => {
                if expect_err {
                    println!("expected err but found no error");
                    panic!()
                } else {
                    println!("didn't expect err but found: {}", err.msg);
                    panic!()
                }
            }
            ActionEndState::Ok(_) => {
                if expect_err {
                    println!("expected err but found no error");
                    panic!()
                }
            }
        },
    }
}

fn main() {
    let config = PandemicGameConfig::new(
        4,
        None,
        None,
        None,
        None,
        None,
        Some(true),
        Some(true),
        Some(false),
    );
    let mut state = PandemicGameState::new(config);
    println!("infection_deck: {:#?}", state.infection_deck);
    println!("game: {}", state.config);
    for i in 0..state.config.nplayers {
        println!(
            "agent {i} = {agent_type:?}",
            i = i,
            agent_type = state.agents[i as usize].agent_type
        );

        let mut expect_err = false;
        let result = match state.agents[i as usize].agent_type {
            AgentName::Contingency => state.do_action(i as usize, 0),
            AgentName::Dispatcher => state.do_action(i as usize, 0),
            _ => {
                expect_err = true;
                state.do_action(i as usize, 0)
            }
        };
        check_result(expect_err, result);
    }
}
