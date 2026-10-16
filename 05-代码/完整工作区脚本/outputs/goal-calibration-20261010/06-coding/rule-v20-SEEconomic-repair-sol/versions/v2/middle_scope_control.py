import sys,json
from pathlib import Path
sys.dont_write_bytecode=True
from structural_controls import article
from relations import RelationView
from dimensions import judge
from evidence import validate_decisions
P=Path(__file__).resolve().parent
u=article();u['contexts']=[c for c in u['contexts'] if c['context_id']!='CTX-E'];u['source_bundle']['source_record']['contexts']=u['contexts'];next(c for c in u['contexts'] if c['context_id']=='CTX-G')['structure']['child_groups'][0]['ordered_context_ids'].remove('CTX-E')
v=RelationView(u);d=judge(v);validate_decisions(u,d);a={k:d[k]['value'] for k in ['S','E','Ec']};expect={'S':None,'E':None,'Ec':None}
out={'name':'missing_middle_member_despite_valid_first_last','synthetic_input':u,'expected_fixed_before_execution':expect,'actual':a,'passed':a==expect,'decisions':d,'relations':v.traces(),'non_human_development_only':True}
with (P/sys.argv[1]).open('x') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'passed':out['passed'],'actual':a},ensure_ascii=False))
