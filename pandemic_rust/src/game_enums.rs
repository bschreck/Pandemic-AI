use crate::city_graph::CityCard;
use strum_macros::EnumIter;

#[derive(Debug, EnumIter, PartialEq, Eq, Hash, Copy, Clone)]
pub enum Disease {
    Blue,
    Red,
    Black,
    Yellow,
}

#[derive(Debug, EnumIter, PartialEq, Eq, Hash, Copy, Clone)]
pub enum EventCard {
    GovernmentGrant,
    ResilientPopulation,
    Airlift,
    Forecast,
    OneQuietNight,
}

pub enum PlayerCard {
    CityCard(CityCard),
    EventCard(EventCard),
    Epidemic,
}
