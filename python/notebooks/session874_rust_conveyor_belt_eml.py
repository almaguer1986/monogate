import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.rust_conveyor_belt_eml import analyze_rust_conveyor_belt_eml
result = analyze_rust_conveyor_belt_eml()
print(json.dumps(result, indent=2, default=str))