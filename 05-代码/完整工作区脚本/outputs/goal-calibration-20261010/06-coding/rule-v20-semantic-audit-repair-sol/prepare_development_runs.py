"""Prepare exact old shared 77/800 sources and candidate code bindings only."""
import copy,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def bind(p):
    p=Path(p).resolve();b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def save(p,v):
    with p.open('x',encoding='utf8')as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def canonical(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def main():
    if (HERE/'pre-run-seal.json').exists():raise ValueError('development inputs already sealed')
    manual=json.loads((HERE/'manual-candidate-binding.json').read_bytes())['manual']
    names=('source_packet','source_receipts','evidence','relations','dimensions')
    code=[dict(bind(HERE/(n+'.py')),module=n)for n in names]
    algorithm={'version':'rule-v20-I-F-semantic-development-candidate-1','modules':code,
        'manual_binding':manual,'definitions_changed':False,'AI_development':True,'formal_execution_authorized':False,
        'input_materials_new_projection_used':False,'ID_SHA_title_or_expected_label_positive_whitelist':False,
        'inference_audit_labels_visible':False,'review_evidence_disclosed_during_development':True}
    manifest=HERE/'algorithm-bindings.json'
    if manifest.exists():
        if json.loads(manifest.read_bytes())!=algorithm:raise ValueError('partial preparation code binding differs')
    else:save(manifest,algorithm)
    # Driver helpers and their imported interface are also sealed.
    code_bindings=[bind(HERE/(n+'.py'))for n in names]+[bind(HERE/n)for n in ['development_driver.py','rule_driver.py','interface_common.py','algorithm-bindings.json','manual-candidate-binding.json']]
    dest=HERE/'cohort-inputs';dest.mkdir(exist_ok=True)
    old77=ROOT/'06-coding/rule-v19-v15-development77-first-sol/versions/v4/source-scope.json'
    old800=ROOT/'06-coding/rule-full4481-v2-root/frozen-scope.json'
    frozen=ROOT/'06-coding/rule-full4481-v2-root/run4481-first/delivered-complete-source-bundles.jsonl'
    by_id={b['source_record']['id']:b for b in map(json.loads,frozen.read_text().splitlines())}
    inventory=[];bundles=[]
    source_dir=ROOT.parent/'ai-audit800-20261010/source-A/coder-A/materials'
    for p in sorted(source_dir.glob('A-*.json')):
        b=json.loads(p.read_bytes());rid=b['source_record']['id']
        if canonical(b)!=canonical(by_id[rid]):raise ValueError('800 source is not the original frozen full bundle')
        inventory.append({'blind_id':p.stem,'source_id':rid,'file_binding':bind(p),'canonical_bundle_sha256':hashlib.sha256(canonical(b).encode()).hexdigest()})
        bundles.append(b)
    if len(bundles)!=800:raise ValueError('800 scope count')
    new800=dest/'development800-original-common-bundles.jsonl'
    with new800.open('x',encoding='utf8')as f:
        for b in bundles:f.write(canonical(b)+'\n')
    save(dest/'development800-original-file-bindings.json',inventory)
    for name,previous in [('development77',old77),('development800',old800)]:
        original=json.loads(previous.read_bytes());scope=copy.deepcopy(original)
        if name=='development800':
            scope['source_packet']=bind(new800);scope['approved_record_ids']=[b['source_record']['id']for b in bundles]
            scope['complete_bundles_canonical_sha256']=scope['source_packet']['sha256'];scope['source_manifest_sha256']=bind(dest/'development800-original-file-bindings.json')['sha256']
        scope.update(runtime_version='rule-v20-disclosed-AI-development-only',status='sealed_development_candidate',
            execution_purpose='disclosed_AI_development_only',expected_record_N=77 if name=='development77'else 800,
            expected_dimension_N=385 if name=='development77'else 4000,maximum_actual_cohort_runs=1,
            manual=manual,code_bindings=code_bindings,parent_frozen_scope_binding=bind(previous),
            new_neutral_projection_used=False,current_common_material_interface_unchanged=True,
            AI_review_exposure_acknowledged=True,human_reference_N=0,independent_validation=False,
            formal_accuracy_claimed=False)
        scope['material_bindings']=[b for b in scope['material_bindings']if Path(b['path']).name!='manual.txt']+[manual]
        save(HERE/(name+'-scope.json'),scope)
    save(HERE/'pre-run-seal.json',{'status':'sealed_candidate_code_and_old_common_source','code_bindings':code_bindings,
        'manual_binding':manual,'scope_bindings':[bind(HERE/(n+'-scope.json'))for n in ['development77','development800']],
        'source800_original_packet_binding':bind(dest/'development800-original-file-bindings.json'),
        'neutral_projection_catalog_separate_not_runtime_input':bind(HERE/'neutral-material-projection-candidate/release-candidate-manifest.json'),
        'formal_or_independent_validation':False})
    print('prepared old common sources; 77 and 800 each maximum one candidate run')
if __name__=='__main__':main()
