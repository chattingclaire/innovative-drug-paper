import hashlib
import json
from pathlib import Path

D=Path(__file__).resolve().parent
def bind(p):
    b=p.read_bytes()
    return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}

def main():
    target=D/'output-seal.json'
    if target.exists(): raise RuntimeError('Existing seal must remain unchanged')
    fixed=json.loads((D/'fixed-S3-before-execution.json').read_text())
    assert [(x['record_id'],x['dimension'],x['expected_value']) for x in fixed]==[
        ('RECODE25-00036','S',1),('RECODE25-00038','S',1),('RECODE25-00045','S',1)]
    plan=json.loads((D/'execution-plan.json').read_text())
    assert plan['judge_calls_now']==0 and plan['required_final_rule_algorithm_binding'] is None
    inputs=json.loads((D/'input-bindings.json').read_text())
    members=[bind(p) for p in sorted(D.rglob('*')) if p.is_file() and p.name!='output-seal.json']
    for item in inputs+members: assert bind(Path(item['path']))==item
    value={'status':'sealed_pre_execution_historical_S3_development_plan',
        'identity':'nonhuman preparation of existing human-confirmed historical expectations',
        'fixed_dimensions':['S'],'fixed_expectations':3,'real_new_human_results':0,
        'judge_calls':0,'RelationView_calls':0,'adapter_calls_in_plan':0,
        'algorithm_binding':None,'awaiting':'ROOT v4 final exact binding and execution authorization',
        'members':members,'inputs':inputs}
    target.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    for item in json.loads(target.read_bytes())['members']+inputs: assert bind(Path(item['path']))==item
    parent=D.parent/'output-seal.json'
    assert bind(parent)['sha256']=='0e4d70ac1bc0d78e54b302e87a3123ade68edef888000df6446cf1232ce9f156'
    for item in json.loads(parent.read_bytes())['members']+json.loads(parent.read_bytes())['inputs']:
        assert bind(Path(item['path']))==item
    print(json.dumps({'seal':bind(target),'member_count':len(members),'input_count':len(inputs),
        'plan_and_parent_readback':'all_equal'},ensure_ascii=False))

if __name__=='__main__': main()
