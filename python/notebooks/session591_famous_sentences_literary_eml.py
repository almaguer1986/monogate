import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.famous_sentences_literary_eml import analyze_famous_sentences_literary_eml
result = analyze_famous_sentences_literary_eml()
print(json.dumps(result, indent=2, default=str))
