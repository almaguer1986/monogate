import json,sys; sys.path.insert(0,"D:/monogate/python")
from monogate.frontiers.boltzmann_eml import run_session54
print(json.dumps(run_session54(),indent=2,default=str))
