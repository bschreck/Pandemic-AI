// build.rs
use std::fs::File;
use std::io::Read;
use serde_json::{Map, Value};
use std::io::Write;
// TODO: Upper camel case
// second half of file
// get it to output in gen/


fn main() {
    // Read the JSON data from the file
    let mut file = File::open("src/city_graph.json").unwrap();
    let mut json_data = String::new();
    file.read_to_string(&mut json_data).unwrap();

    // Parse the JSON data
    let parsed_data: Map<String, Value> = serde_json::from_str(&json_data).expect("Expected a JSON object");

    let keys: Vec<String> = parsed_data.keys().map(|s| s.as_str().to_owned()).collect();

    let mut enum_str = String::from("pub enum CityCard2 {\n");
    for key in keys {
        enum_str.push_str(&format!("    {},\n", key));
    }
    enum_str.push('}');

    println!("{}", enum_str);

    // Generate Rust code from the JSON data
    let rust_code = format!(
        "use strum_macros::EnumString;

use std::collections::HashMap;

#[derive(Debug, EnumString, PartialEq, Eq, Hash, Copy, Clone)]
{}
", enum_str
    );

    // Write the generated code to a file
    let mut output_file = File::create("city_graph2.rs").unwrap();
    output_file.write_all(rust_code.as_bytes()).unwrap();
}

