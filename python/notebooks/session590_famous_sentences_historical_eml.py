import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.famous_sentences_historical_eml import analyze_famous_sentences_historical_eml
result = analyze_famous_sentences_historical_eml()
print(json.dumps(result, indent=2, default=str))
