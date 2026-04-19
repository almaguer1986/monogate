import json,sys; sys.path.insert(0,"D:/monogate/python")
from monogate.frontiers.eml_as_category_eml import run_session52
print(json.dumps(run_session52(),indent=2,default=str))
