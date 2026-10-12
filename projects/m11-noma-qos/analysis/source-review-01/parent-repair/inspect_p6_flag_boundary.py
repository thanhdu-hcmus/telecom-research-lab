import sys,math
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'projects/m11-noma-qos/analysis/supplement'))
from test_supplement import fixture,audit_fixture
import independent as ind
for v in [(1.,3.,9.,1.,2.),(1.,1.,4.,.5,.5),(100.,.3557646508449167,1.1182434120044833,.5,.5)]:
 r,m=fixture(v);a=float(r['a_star']);rd=ind.rates(v,a)
 print(v, a,repr(rd['rw']),repr(v[3]),'difference',rd['rw']-v[3],audit_fixture(r,m,v).counts)
