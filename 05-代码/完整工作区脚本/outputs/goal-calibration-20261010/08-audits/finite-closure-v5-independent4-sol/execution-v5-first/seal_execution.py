import hashlib
import json
from pathlib import Path

D=Path(__file__).resolve().parent
def bind(p):
    b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}

def main():
    target=D/'output-seal.json'
    if target.exists():raise RuntimeError('Execution seal exists; do not overwrite')
    summary=json.loads((D/'execution-summary.json').read_bytes())
    assert summary['actual_S']==[1,None,1,0] and summary['matches']==4
    assert summary['calls']=={'semantic_unit':4,'RelationView':4,'judge':4}
    assert summary['execution_errors']==summary['mechanical_errors']==summary['retry_count']==0
    inputs=json.loads((D/'input-bindings.json').read_bytes())
    prep=json.loads((D.parent/'preparation-seal.json').read_bytes())
    assert bind(D.parent/'preparation-seal.json')['sha256']=='74491ccf70822fc36b8426d0fb13c5f2b337cc9d7dd2bc36ef86435b128a941d'
    members=[bind(p) for p in sorted(D.rglob('*')) if p.is_file() and p.name!='output-seal.json']
    for item in members+inputs+prep['members']+prep['inputs']:assert bind(Path(item['path']))==item
    value={'status':'sealed_once_only_hidden_synthetic_v5_controls',
        'identity':'nonhuman independent source-only development controls; not formal accuracy',
        'case_count':4,'unique_current_source_text_combinations':3,'actual_S':[1,None,1,0],
        'fixed_S_expectations':[1,None,1,0],'matches':4,'calls':summary['calls'],
        'execution_errors':0,'mechanical_errors':0,'retries':0,'actual_policy_IDs_added':0,
        'new_real_human_results':0,'formal_statistics':0,'members':members,'inputs':inputs,'self_excluded':True}
    target.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    for item in json.loads(target.read_bytes())['members']+inputs:assert bind(Path(item['path']))==item
    print(json.dumps({'seal':bind(target),'member_count':len(members),'input_count':len(inputs),
        'prep_members_unchanged':len(prep['members']),'readback':'all_equal'},ensure_ascii=False))

if __name__=='__main__':main()
