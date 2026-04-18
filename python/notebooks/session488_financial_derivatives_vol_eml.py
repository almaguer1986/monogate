"""Session 488 notebook"""
import json, sys
sys.path.insert(0, "D:/monogate/python")
from monogate.frontiers.financial_derivatives_vol_eml import analyze_financial_derivatives_vol_eml
print(json.dumps(analyze_financial_derivatives_vol_eml(), indent=2, default=str))
