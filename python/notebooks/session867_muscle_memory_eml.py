import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.muscle_memory_eml import analyze_muscle_memory_eml
result = analyze_muscle_memory_eml()
print(json.dumps(result, indent=2, default=str))