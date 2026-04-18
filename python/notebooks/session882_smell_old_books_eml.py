import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.smell_old_books_eml import analyze_smell_old_books_eml
result = analyze_smell_old_books_eml()
print(json.dumps(result, indent=2, default=str))