import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.dog_training_animal_cognition_eml import analyze_dog_training_animal_cognition_eml
result = analyze_dog_training_animal_cognition_eml()
print(json.dumps(result, indent=2, default=str))
