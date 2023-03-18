#![feature(variant_count)]
pub mod pandemic_game;
pub mod agent;
extern crate num;
#[macro_use]
extern crate num_derive;

pub mod city_graph {
    include!(concat!(env!("OUT_DIR"), "/city_graph.rs"));
}
