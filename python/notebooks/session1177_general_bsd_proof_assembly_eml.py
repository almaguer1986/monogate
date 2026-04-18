import sys, json
sys.path.insert(0, "python")
from monogate.frontiers.general_bsd_proof_assembly_eml import analyze_general_bsd_proof_assembly_eml
result = analyze_general_bsd_proof_assembly_eml()
print(json.dumps(result, indent=2))
