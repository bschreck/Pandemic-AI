#![feature(variant_count)]
pub mod pandemic_game;
pub mod agent;
pub mod city_graph;
extern crate num;
#[macro_use]
extern crate num_derive;

pub mod city_graph2 {
    include!(concat!(env!("OUT_DIR"), "/city_graph2.rs"));
}
