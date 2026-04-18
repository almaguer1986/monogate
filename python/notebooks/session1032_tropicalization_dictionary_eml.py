import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.tropicalization_dictionary_eml import analyze_tropicalization_dictionary_eml
result = analyze_tropicalization_dictionary_eml()
print(json.dumps(result, indent=2))
