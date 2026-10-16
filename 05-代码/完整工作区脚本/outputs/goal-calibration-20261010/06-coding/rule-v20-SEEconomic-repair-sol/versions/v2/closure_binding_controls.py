"""Exact structural source and clause scope controls fixed before correction."""
import sys,json,copy
from pathlib import Path
sys.dont_write_bytecode=True
from structural_controls import article
from relations import RelationView
from dimensions import judge
from evidence import validate_decisions
P=Path(__file__).resolve().parent
cs=[]
for name,node in [('wrong_container_SHA','CTX-G'),('wrong_boundary_container_SHA','CTX-B')]:
 u=article();c=next(c for c in u['contexts'] if c['context_id']==node);c['source_ref']=copy.deepcopy(c['source_ref']);c['source_ref']['sha256']='c'*64;cs.append((name,u,{'S':None,'E':None,'Ec':None}))
u=article('符合《药物条件规定》第七条第二款规定的药品可以申请。');u['contexts']=[c for c in u['contexts'] if c['context_id'] in ['CTX-SYN','CTX-E','CTX-Ec']];u['source_bundle']['source_record']['contexts']=u['contexts'];cs.append(('explicit_clause_closed_by_next_clause_only',u,{'S':0,'E':1,'Ec':0}))
u=copy.deepcopy(u);u['contexts']=[c for c in u['contexts'] if c['context_id']!='CTX-Ec'];u['source_bundle']['source_record']['contexts']=u['contexts'];cs.append(('explicit_clause_missing_own_end',u,{'S':None,'E':None,'Ec':None}))
out=[]
for name,u,expected in cs:
 v=RelationView(u);d=judge(v);validate_decisions(u,d);a={k:d[k]['value'] for k in expected};out.append({'name':name,'synthetic_input':u,'expected_fixed_before_execution':expected,'actual':a,'passed':a==expected,'decisions':d,'relations':v.traces()})
with (P/sys.argv[1]).open('x') as f:json.dump({'test_N':len(out),'failed_N':sum(not t['passed'] for t in out),'tests':out,'not_human_or_formal_gold':True},f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'test_N':len(out),'failed':[(t['name'],t['actual']) for t in out if not t['passed']]},ensure_ascii=False))
