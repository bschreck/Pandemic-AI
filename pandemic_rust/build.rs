// build.rs
use std::env;
use std::path::Path;
use std::fs::File;
use std::io::Read;
use serde_json::{Map, Value};
use std::io::Write;
use regex::Regex;

macro_rules! p {
    ($($tokens: tt)*) => {
        println!("cargo:warning={}", format!($($tokens)*))
    }
}

fn camel_case(s: &str) -> String {
    let re = Regex::new(r"(_|-)+").unwrap();
    let s = re.replace_all(s, " ").to_string();
    let mut words = s.split_whitespace().map(str::to_owned);
    let first_word = words.next().unwrap_or_default();
    let mut upper_camel_first_word = "".to_owned();
    if first_word.len() > 0 {
        upper_camel_first_word.push_str(&first_word[..1].to_uppercase());
        upper_camel_first_word.push_str(&first_word[1..]);
    }
    words.fold(upper_camel_first_word, |mut acc, word| {
        acc.push_str(&word[..1].to_uppercase());
        acc.push_str(&word[1..]);
        acc
    })
}
// TODO: second half of file
// later, not important:
// get it to output in gen/ (requires nightly rust, --out-dir


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
        enum_str.push_str(&format!("    {},\n", camel_case(&key)));
    }
    enum_str.push('}');

    // Generate Rust code from the JSON data
    let rust_code = format!(
        "use strum_macros::EnumString;

use std::collections::HashMap;

#[derive(Debug, EnumString, PartialEq, Eq, Hash, Copy, Clone)]
{}
", enum_str
    );

    // Write the generated code to a file
    let out_dir = env::var_os("OUT_DIR").unwrap();
    //p!("{}", out_dir.clone().into_string().unwrap());
    let dest_path = Path::new(&out_dir).join("city_graph2.rs");
    //p!("{}", dest_path.clone().into_os_string().into_string().unwrap());
    let mut output_file = File::create(&dest_path).unwrap();
    output_file.write_all(rust_code.as_bytes()).unwrap();
}

