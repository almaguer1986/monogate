import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.protein_folding_distillation_eml import analyze_protein_folding_distillation_eml
result = analyze_protein_folding_distillation_eml()
print(json.dumps(result, indent=2, default=str))
