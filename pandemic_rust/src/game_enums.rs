use crate::city_graph::CityCard;
use strum_macros::EnumIter;
use strum_macros::EnumString;

#[derive(Debug, EnumIter)]
pub enum GameEnd {
    PlayerDeckLimit,
    DiseaseCubeLimit,
    OutbreakLimit,
    Win,
}

#[derive(Debug, EnumIter, PartialEq, Eq, Hash, Copy, Clone)]
pub enum Disease {
    Blue,
    Red,
    Black,
    Yellow,
}

#[derive(Debug, Default, EnumIter, EnumString, PartialEq, Eq, Hash, Copy, Clone)]
pub enum EventCard {
    #[default]
    GovernmentGrant,
    ResilientPopulation,
    Airlift,
    Forecast,
    OneQuietNight,
}

#[derive(Debug, Default, EnumIter, PartialEq, Eq, Hash, Copy, Clone)]
pub enum PlayerCard {
    CityCard(CityCard),
    EventCard(EventCard),
    #[default]
    Epidemic,
}
