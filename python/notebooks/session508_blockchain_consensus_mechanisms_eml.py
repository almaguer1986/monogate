"""Session 508 notebook"""
import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.blockchain_consensus_mechanisms_eml import analyze_blockchain_consensus_mechanisms_eml
print(json.dumps(analyze_blockchain_consensus_mechanisms_eml(), indent=2, default=str))
