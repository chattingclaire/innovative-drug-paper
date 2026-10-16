from pathlib import Path
import json,hashlib,sys
from datetime import datetime,timezone
HERE=Path(__file__).resolve().parent
UP=HERE.parent.parent/'管理员留存-勿发编码者'
OUT=HERE/'rule-first'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert not OUT.exists(),'First pass already exists'
ready=json.loads((HERE/'READY.json').read_text())
assert sha(HERE/'common-inputs.jsonl')==ready['common_inputs']['sha256']
for x in json.loads((UP/'方法与标准冻结.json').read_text())['snapshots']:
    assert sha(x['snapshot']['path'])==x['snapshot']['sha256']
sys.dont_write_bytecode=True;sys.path.insert(0,str(UP/'冻结版本/rule'))
from source_packet import semantic_unit
from relations import RelationView
from dimensions import judge
from evidence import validate_decisions
inputs=[json.loads(l) for l in (HERE/'common-inputs.jsonl').read_text().splitlines()]
assert len(inputs)==122
OUT.mkdir();rows=[]
with (OUT/'first-predictions.jsonl').open('x') as f:
    for r in inputs:
        unit=semantic_unit(r['source_bundle']);assert unit==r['semantic_unit']
        item={'id':r['id'],'implementation_error':None,'labels':None,'decisions':None}
        try:
            view=RelationView(unit);decisions=judge(view);validate_decisions(view.unit,decisions)
            item.update(labels={k:v['value'] for k,v in decisions.items()},decisions=decisions)
        except Exception as e:item['implementation_error']=f'{type(e).__name__}: {e}'
        f.write(json.dumps(item,ensure_ascii=False)+'\n');f.flush();rows.append(item)
result={'status':'first_pass_completed','created_at_utc':datetime.now(timezone.utc).isoformat(),'units':len(rows),'technical_errors':[{'id':r['id'],'error':r['implementation_error']} for r in rows if r['implementation_error']],'null_records':sum(r['labels'] is not None and any(v is None for v in r['labels'].values()) for r in rows),'input_sha256':sha(HERE/'common-inputs.jsonl'),'output_sha256':sha(OUT/'first-predictions.jsonl'),'method_freeze_sha256':sha(UP/'方法与标准冻结.json'),'no_rule_changes':True,'no_human_results_read':True,'no_full4481_rerun':True,'independent_validation_completed':False}
(OUT/'completion.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False,indent=2))
