#![feature(variant_count)]
pub mod agent;
pub mod game_enums;
pub mod pandemic_game;
extern crate num;
#[macro_use]
extern crate num_derive;

pub mod city_graph {
    include!(concat!(env!("OUT_DIR"), "/city_graph.rs"));
}
