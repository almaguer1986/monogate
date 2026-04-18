import sys, json
sys.path.insert(0, 'python')
from monogate.frontiers.financial_risk_volatility_surface_eml import analyze_financial_risk_volatility_surface_eml
result = analyze_financial_risk_volatility_surface_eml()
print(json.dumps(result, indent=2, default=str))
