import json
from re import sub


def camel_case(s):
    s = sub(r"(_|-)+", " ", s).title().replace(" ", "")
    return ''.join([s[0].upper(), s[1:]])


with open('pandemic_rust/src/city_graph.json') as f:
    cg = json.load(f)


with open('pandemic_rust/src/city_graph.rs', 'w') as f:
    f.write('use strum_macros::EnumString;\n\n')
    f.write('use std::collections::HashMap;\n\n')
    f.write('#[derive(Debug, EnumString, PartialEq, Eq, Hash, Copy, Clone)]\n')
    f.write('pub enum CityCard {\n')
    for key in cg:
        f.write('    '+camel_case(key) + ',\n')
    f.write('}\n\n')
    f.write('''pub fn city_graph() -> HashMap<CityCard, Vec<CityCard>> {
    HashMap::from([
''')
    for key, vals in cg.items():
        f.write(f'        (CityCard::{camel_case(key)}, vec![{", ".join(["CityCard::"+camel_case(v) for v in vals])}]),\n')
    f.write('    ])\n')
    f.write('}')

