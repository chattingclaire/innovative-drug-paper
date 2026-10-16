import hashlib
import json
from pathlib import Path

D=Path(__file__).resolve().parent
def bind(p):
    b=p.read_bytes()
    return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}

def main():
    seal=D/'output-seal.json'
    if seal.exists(): raise RuntimeError('Existing execution seal must remain unchanged')
    summary=json.loads((D/'execution-summary.json').read_bytes())
    assert summary['actual_S']==[0,0,0] and summary['calls']=={'semantic_unit':3,'RelationView':3,'judge':3}
    inputs=json.loads((D/'input-bindings.json').read_bytes())
    members=[bind(p) for p in sorted(D.rglob('*')) if p.is_file() and p.name!='output-seal.json']
    for item in inputs+members: assert bind(Path(item['path']))==item
    value={'status':'sealed_first_and_only_v4_actual_historical_S3_execution',
        'identity':'nonhuman development check; preexisting historical human expectations only',
        'record_ids':summary['case_ids'],'fixed_dimensions':['S'],'actual_S':[0,0,0],
        'calls':summary['calls'],'retry_attempts':0,'execution_errors':0,
        'mechanical_validation_errors':0,'new_real_human_results':0,'formal_metrics':0,
        'classification_inputs_changed':False,'algorithm_or_manual_changed':False,
        'members':members,'inputs':inputs,'self_excluded':True}
    seal.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    for item in json.loads(seal.read_bytes())['members']+inputs: assert bind(Path(item['path']))==item
    print(json.dumps({'seal':bind(seal),'members':len(members),'inputs':len(inputs),'readback':'all_equal'},ensure_ascii=False))

if __name__=='__main__':main()
