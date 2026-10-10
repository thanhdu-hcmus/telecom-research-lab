# CC0 authored fixture baseline, not downloaded code.
import json, math
rho=[1,2,5,10,20]
print(json.dumps({"rho":rho,"outage":[1-math.exp(-1/x) for x in rho]}))
