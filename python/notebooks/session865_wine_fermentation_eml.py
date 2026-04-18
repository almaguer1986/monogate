import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.wine_fermentation_eml import analyze_wine_fermentation_eml
result = analyze_wine_fermentation_eml()
print(json.dumps(result, indent=2, default=str))