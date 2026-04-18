import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.category_of_categories_eml import analyze_category_of_categories_eml
result = analyze_category_of_categories_eml()
print(json.dumps(result, indent=2, default=str))