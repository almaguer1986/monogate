import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.dog_chooses_person_eml import analyze_dog_chooses_person_eml
result = analyze_dog_chooses_person_eml()
print(json.dumps(result, indent=2, default=str))