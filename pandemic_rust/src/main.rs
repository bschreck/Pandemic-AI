use pandemic_rust::pandemic_game::{PandemicGame, PandemicGameState};
use pandemic_rust::agent::{ActionError, Agent};

//include!("generated.rs");


fn check_result(expect_err: bool, result: Result<bool, ActionError>) {
    match result {
        Ok(result) => {
            if expect_err {
                println!("expected err but found no error");
                panic!()
            } else {
                assert_eq!(result, true)
            }
        }
        Err(result) => {
            if expect_err {
                assert_eq!(result.msg, "action_idx > agent.actions.len()".to_string())
            } else {
                println!("didn't expect err but found: {}", result.msg);
                panic!()
            }
        }
    }
}

fn main() {
    let (mut game, state) = PandemicGame::new(
        4,
        None,
        None,
        None,
        None,
        None,
        Some(true));
    println!("infection_deck: {:#?}", state.infection_deck);
    println!("game: {game}");
    let mut state = game.initialize(state);
    for i in 0..game.nplayers {
        println!(
            "agent {i} = {agent_type:?}",
            i=i, agent_type=game.agents[i as usize].agent_type
        );

        let mut expect_err = false;
        let result = match game.agents[i as usize].agent_type {
            Agent::Contingency => game.do_action(i as usize, 0, &mut state),
            Agent::Dispatcher => game.do_action(i as usize, 0, &mut state),
            _ => {
                expect_err = true;
                game.do_action(i as usize, 0, &mut state)
            }
        };
        check_result(expect_err, result);
    }
}
