import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.translation_untranslatable_eml import analyze_translation_untranslatable_eml
result = analyze_translation_untranslatable_eml()
print(json.dumps(result, indent=2, default=str))
