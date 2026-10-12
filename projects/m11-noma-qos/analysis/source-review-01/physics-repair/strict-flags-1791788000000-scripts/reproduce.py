import json,math,sys
from pathlib import Path
sys.dont_write_bytecode=True
repo=Path.cwd()
sys.path.insert(0,str(repo/'projects/m11-noma-qos/analysis/supplement'))
from independent import rates
records=[]
for A in (1.,3.,4.,10.,40.,100.):
    for qw in (.25,.5):
        target=math.expm1(qw*math.log(2))
        a=(A-target)/(A*(1+target))
        inputs=(1.,A,4*A,qw,0.)
        direct=rates(inputs,a)['rw']
        quotient=math.log2((1+A)/(1+a*A))
        records.append(dict(inputs=inputs,a=a,original_sinr_log1p=direct,
                            original_equivalent_log_quotient=quotient,
                            direct_flag=direct>=qw,quotient_flag=quotient>=qw,
                            rate_difference=quotient-direct,
                            rate_difference_ulps=(quotient-direct)/math.ulp(qw)))
area=repo/'projects/m11-noma-qos/analysis/source-review-01/physics-repair/strict-flags-1791788000000'
area.mkdir()
target=area/'reproduction.json'
target.write_text(json.dumps(dict(hypothesis='A strict bit comparison can flip between mathematically equivalent approved original-rate equations when their evaluated endpoint residual is within one ulp.',synthetic_only=True,records=records),indent=2,allow_nan=False)+'\n',encoding='utf8')
print(json.dumps([r for r in records if r['direct_flag']!=r['quotient_flag']],indent=2))
