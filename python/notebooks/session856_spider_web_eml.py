import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.spider_web_eml import analyze_spider_web_eml
result = analyze_spider_web_eml()
print(json.dumps(result, indent=2, default=str))