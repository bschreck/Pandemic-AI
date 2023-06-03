use handlebars::Handlebars;
use regex::Regex;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::env;
use std::fs::File;
use std::io::Read;
use std::io::Write;
use std::path::Path;

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

fn recreate_city_graph_with_upper_camel_case(original_json_file: String, output_json_file: String) {
    let original_city_graph = load_json_city_graph(original_json_file);

    write_json_city_graph(
        output_json_file,
        convert_snake_case_city_graph_to_upper_camel_case(original_city_graph),
    );
}

fn recreate_city_disease_with_upper_camel_case(
    original_json_file: String,
    output_json_file: String,
) {
    let original_city_disease = load_json_city_disease(original_json_file);

    write_json_city_disease(
        output_json_file,
        convert_snake_case_city_disease_to_upper_camel_case(original_city_disease),
    );
}

fn load_json_city_graph(file: String) -> HashMap<String, Vec<String>> {
    let mut file = File::open(file).unwrap();
    let mut json_blob = String::new();
    file.read_to_string(&mut json_blob).unwrap();
    parse_json_blob_as_city_graph(json_blob)
}

fn load_json_city_disease(file: String) -> HashMap<String, String> {
    let mut file = File::open(file).unwrap();
    let mut json_blob = String::new();
    file.read_to_string(&mut json_blob).unwrap();
    parse_json_blob_as_city_disease(json_blob)
}

fn write_json_city_graph(file: String, city_graph: HashMap<String, Vec<String>>) {
    let mut file = File::create(file).unwrap();
    let json_blob = serde_json::to_string_pretty(&city_graph).unwrap();
    file.write_all(json_blob.as_bytes()).unwrap();
}

fn write_json_city_disease(file: String, city_disease: HashMap<String, String>) {
    let mut file = File::create(file).unwrap();
    let json_blob = serde_json::to_string_pretty(&city_disease).unwrap();
    file.write_all(json_blob.as_bytes()).unwrap();
}

fn parse_json_blob_as_city_graph(json_blob: String) -> HashMap<String, Vec<String>> {
    serde_json::from_str(&json_blob).expect("Expected a JSON object")
}
fn parse_json_blob_as_city_disease(json_blob: String) -> HashMap<String, String> {
    serde_json::from_str(&json_blob).expect("Expected a JSON object")
}

fn convert_snake_case_city_graph_to_upper_camel_case(
    snake_case_city_graph: HashMap<String, Vec<String>>,
) -> HashMap<String, Vec<String>> {
    snake_case_city_graph
        .into_iter()
        .map(|(city, neighbors)| {
            (
                camel_case(city),
                neighbors.into_iter().map(camel_case).collect(),
            )
        })
        .collect()
}

fn convert_snake_case_city_disease_to_upper_camel_case(
    snake_case_city_disease: HashMap<String, String>,
) -> HashMap<String, String> {
    snake_case_city_disease
        .into_iter()
        .map(|(city, disease)| (camel_case(city), camel_case(disease)))
        .collect()
}

#[derive(Deserialize, Serialize)]
struct TemplateData {
    first_variant: String,
    city_graph: HashMap<String, Vec<String>>,
    city_graph_keys: Vec<String>,
    city_disease: HashMap<String, String>,
}
fn create_city_graph_mod(
    input_city_graph_json_file: String,
    input_city_disease_json_file: String,
    input_city_graph_hbs_template_file: String,
    output_city_graph_rust_file: String,
) {
    let city_graph = load_json_city_graph(input_city_graph_json_file);
    let city_disease = load_json_city_disease(input_city_disease_json_file);

    let handlebars = Handlebars::new();

    let mut city_graph_template = File::open(input_city_graph_hbs_template_file).unwrap();
    let mut city_graph_template_str = String::new();
    city_graph_template
        .read_to_string(&mut city_graph_template_str)
        .unwrap();

    let mut city_graph_keys: Vec<String> = city_graph.keys().map(|s| s.to_string()).collect();
    let first_variant = city_graph_keys.pop().unwrap();
    let template_data = TemplateData {
        first_variant,
        city_graph_keys,
        city_graph,
        city_disease,
    };
    let output_rust_mod = handlebars
        .render_template(&city_graph_template_str, &template_data)
        .expect("Expected a string");
    let out_dir = env::var_os("OUT_DIR").unwrap();
    let dest_path = Path::new(&out_dir).join(output_city_graph_rust_file);
    let mut output_file = File::create(dest_path).unwrap();
    output_file.write_all(output_rust_mod.as_bytes()).unwrap();
}

fn main() {
    recreate_city_graph_with_upper_camel_case(
        "src/city_graph.json".to_string(),
        "src/city_graph_upper_camel_case.json".to_string(),
    );

    recreate_city_disease_with_upper_camel_case(
        "src/city_diseases.json".to_string(),
        "src/city_diseases_upper_camel_case.json".to_string(),
    );

    create_city_graph_mod(
        "src/city_graph_upper_camel_case.json".to_string(),
        "src/city_diseases_upper_camel_case.json".to_string(),
        "src/city_graph_template.rs.hbs".to_string(),
        "city_graph.rs".to_string(),
    );
}
