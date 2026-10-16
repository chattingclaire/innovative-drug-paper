"""Disclosure replay of independent pre-fixed synthetic controls; not formal test."""
import sys,json,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
from relations import RelationView
from dimensions import judge
from evidence import validate_decisions
P=Path(__file__).resolve().parent;ROOT=P.parents[5]
IN=ROOT/'outputs/goal-calibration-20261010/08-audits/SE-Ec-repair-independent-controls-sol/controls-fixed-before-execution.json'
x=json.loads(IN.read_text());out=[]
for c in x['cases']:
 u=c['synthetic_input'];v=RelationView(u);d=judge(v);validate_decisions(u,d);a={k:d[k]['value'] for k in c['expected']}
 out.append({**c,'actual':a,'passed':a==c['expected'],'decisions':d,'relations':v.traces()})
with (P/sys.argv[1]).open('x') as f:json.dump({'input':{'path':str(IN),'sha256':hashlib.sha256(IN.read_bytes()).hexdigest()},'test_N':len(out),'failed_N':sum(not t['passed'] for t in out),'tests':out,'non_human_development_exposure':True,'formal_gate':False},f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'test_N':len(out),'failed':[(t['name'],t['actual']) for t in out if not t['passed']]},ensure_ascii=False))
