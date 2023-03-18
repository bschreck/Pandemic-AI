use std::env;
use std::path::Path;
use std::fs::File;
use std::io::Read;
use handlebars::{to_json, Handlebars};
use serde_json::{Map, Value};
use std::io::Write;
use regex::Regex;
use std::collections::HashMap;

fn camel_case(s: String) -> String {
    let re = Regex::new(r"(_|-)+").unwrap();
    let s = re.replace_all(&s, " ").to_string();
    let mut words = s.split_whitespace().map(str::to_owned);
    let first_word = words.next().unwrap_or_default();
    let mut upper_camel_first_word = "".to_owned();
    if !first_word.is_empty() {
        upper_camel_first_word.push_str(&first_word[..1].to_uppercase());
        upper_camel_first_word.push_str(&first_word[1..]);
    }
    words.fold(upper_camel_first_word, |mut acc, word| {
        acc.push_str(&word[..1].to_uppercase());
        acc.push_str(&word[1..]);
        acc
    })
}

fn recreate_json_with_upper_camel_case(original_json_file: String, output_json_file: String) {
    let original_city_graph = load_json_map(original_json_file);

    let upper_camel_case_city_graph_as_json = convert_json_data_to_upper_camel_case_json(original_city_graph);

    write_json_map(output_json_file, upper_camel_case_city_graph_as_json)
}

fn convert_json_data_to_upper_camel_case_json(city_graph: Map<String, Value>) -> Map<String, Value> {
    convert_hashmap_to_json_data(
        convert_snake_case_city_graph_to_upper_camel_case(
            convert_json_data_to_hash_map(city_graph)
        )
    )
}

fn load_json_map(file: String) -> Map<String, Value> {
    let mut file = File::open(file).unwrap();
    let mut json_blob = String::new();
    file.read_to_string(&mut json_blob).unwrap();
    parse_json_blob_as_map(json_blob)
}

fn write_json_map(file: String, json_map: Map<String, Value>) {
    let mut file = File::create(file).unwrap();
    let json_blob = serde_json::to_string_pretty(&json_map).unwrap();
    file.write_all(json_blob.as_bytes()).unwrap();
}

fn parse_json_blob_as_map(json_blob: String) -> Map<String, Value> {
    serde_json::from_str(&json_blob).expect("Expected a JSON object")
}

fn convert_json_data_to_hash_map(json_data: Map<String, Value>) -> HashMap<String, Vec<String>> {
    json_data.into_iter().map(|(city, mut neighbors)| {
        let neighbors_vec: Vec<String> = serde_json::from_value(neighbors.take()).unwrap();
        (city, neighbors_vec)
    }).collect()
}

fn convert_hashmap_to_json_data(data: HashMap<String, Vec<String>>) -> Map<String, Value> {
    data.into_iter().map(|(city, neighbors)| {
        (city, to_json(neighbors))
    }).collect()
}

fn convert_snake_case_city_graph_to_upper_camel_case(snake_case_city_graph: HashMap<String, Vec<String>>) -> HashMap<String, Vec<String>> {
    snake_case_city_graph.into_iter().map(|(city, neighbors)| {
        (camel_case(city), neighbors.into_iter().map(camel_case).collect())
    }).collect()
}

fn create_city_graph_mod(input_city_graph_json_file: String, input_city_graph_hbs_template_file: String, output_city_graph_rust_file: String) {
    let city_graph = load_json_map(input_city_graph_json_file);

    let handlebars = Handlebars::new();

    let mut city_graph_template = File::open(input_city_graph_hbs_template_file).unwrap();
    let mut city_graph_template_str = String::new();
    city_graph_template.read_to_string(&mut city_graph_template_str).unwrap();

    let output_rust_mod = handlebars.render_template(&city_graph_template_str, &city_graph).expect("Expected a string");
    let out_dir = env::var_os("OUT_DIR").unwrap();
    let dest_path = Path::new(&out_dir).join(output_city_graph_rust_file);
    let mut output_file = File::create(dest_path).unwrap();
    output_file.write_all(output_rust_mod.as_bytes()).unwrap();
}

fn main() {
    recreate_json_with_upper_camel_case(
        "src/city_graph.json".to_string(), 
        "src/city_graph_upper_camel_case.json".to_string()
    );
    
    create_city_graph_mod(
        "src/city_graph_upper_camel_case.json".to_string(), 
        "src/city_graph_template.rs.hbs".to_string(), 
        "city_graph.rs".to_string()
    );
}

