"""Bind unchanged classifier execution to the source-completed v3 material."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime
import json

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
def sha(path):return sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())
def rows(path):return [json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()]
def write(path,value):Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

def main():
    material=read(ROOT/'safety_population_context_v3_manifest.json')
    sourceqa=read(ROOT/'source_safety_population_v3_QA.json')
    run=read(HERE/'all_predictions_completed_material_v3.run.json')
    oldrun=read(HERE/'all_predictions_completed_material_v2.run.json')
    assert run['version']==oldrun['version']=='v31-coverage-object-synonyms-20261007'
    assert run['runtime_code_sha256']==oldrun['runtime_code_sha256']
    assert run['runner_sha256']==oldrun['runner_sha256']
    assert material['rule_input_sha256']==sourceqa['rule_input_sha256']==run['input_sha256']==sha(ROOT/'rule_inputs_v31_shared_v3.jsonl')
    assert material['llm_input_sha256']==sourceqa['llm_input_sha256']==sha(ROOT/'effective_blind_inputs_v30_v3.jsonl')
    assert sourceqa['status']=='passed_source_material_and_frozen_certificate_QA'
    assert material['frozen_previous_artifacts_sha256']=={p:sha(p) for p in material['frozen_previous_artifacts_sha256']}
    output=HERE/'all_predictions_completed_material_v3.jsonl'
    assert run['n']==4924 and run['pending_n']==0 and run['reference_labels_loaded'] is False
    assert run['prediction_sha256']==sha(output)
    inputs=rows(ROOT/'rule_inputs_v31_shared_v3.jsonl');predictions=rows(output)
    previous=rows(HERE/'all_predictions_completed_material_v2.jsonl')
    assert len(inputs)==len(predictions)==len(previous)==4924
    changes=[];evidence_n=0;suppression_n=0;altered_records=[]
    for inp,old,new in zip(inputs,previous,predictions):
        assert inp['id']==old['id']==new['id']
        assert inp['original_id']==old['original_id']==new['original_id']
        unit=inp['input']['unit_text'];p=new['prediction']
        assert p['unit_text_sha256']==sha256(unit.encode()).hexdigest()
        assert p['judgement_status']!='undetermined'
        assert set(p['labels'])=={'S','E','Ec','I','F'}
        assert all(type(v) is int and v in (0,1) for v in p['labels'].values())
        for e in p.get('evidence',[]):
            assert unit[e['start']:e['end']]==e['text'];evidence_n+=1
        for e in p.get('suppressions',[]):
            if all(k in e for k in ('start','end','text')):
                assert unit[e['start']:e['end']]==e['text'];suppression_n+=1
        if old!=new:altered_records.append(inp['id'])
        for d in p['labels']:
            if old['prediction']['labels'][d]!=p['labels'][d]:
                changes.append({'id':inp['id'],'dimension':d,'old':old['prediction']['labels'][d],
                    'new':p['labels'][d],'unit_text':unit,'reason':'Source material v3 changed; classifier code unchanged'})
    assert evidence_n==run['checks']['literal_evidence_spans']
    assert suppression_n==run['checks']['literal_suppression_spans']
    assert set(altered_records)<=set(sourceqa['changed_ids'])
    out={'status':'passed_full_rule_v3_material_execution_QA','n':4924,'binary_label_count':24620,
         'pending_n':0,'source_material_changed_ids':sourceqa['changed_ids'],
         'output_records_changed_ids':altered_records,'labels_changed_vs_v2':changes,
         'classification_code_unchanged_vs_v2':True,'runtime_version':run['version'],
         'runtime_code_sha256':run['runtime_code_sha256'],'runner_sha256':run['runner_sha256'],
         'literal_evidence_spans_checked':evidence_n,'literal_suppression_spans_checked':suppression_n,
         'all_frozen_v2_artifacts_preserved':True,'reference_labels_read_or_changed':False,
         'rule_input_sha256':run['input_sha256'],'llm_input_sha256':material['llm_input_sha256'],
         'prediction_sha256':run['prediction_sha256'],
         'source_QA_sha256':sha(ROOT/'source_safety_population_v3_QA.json'),
         'run_manifest_sha256':sha(HERE/'all_predictions_completed_material_v3.run.json'),
         'verification_script_sha256':sha(__file__)}
    write(HERE/'completed_material_v3_QA.json',out)
    write(HERE/'completed_material_v3_changes_vs_v2.json',{'comparison':'Only source completion changed; identical classifier bytes','changes':changes,'n_changed_id_dimension':len(changes),'changed_output_records':altered_records})
    artifacts=[ROOT/'rule_inputs_v31_shared_v3.jsonl',ROOT/'effective_blind_inputs_v30_v3.jsonl',
       ROOT/'safety_population_context_v3_manifest.json',ROOT/'source_safety_population_v3_QA.json',
       ROOT/'extend_safety_population_context_v3.py',ROOT/'verify_safety_population_context_v3.py',
       ROOT/'source-list-v3-visual/CDE-safety-summary-2020-physical-page6.png',
       output,HERE/'all_predictions_completed_material_v3.run.json',HERE/'completed_material_v3_QA.json',
       HERE/'completed_material_v3_changes_vs_v2.json',Path(__file__)]
    independent=ROOT/'source_safety_population_v3_independent_QA.json'
    if independent.exists():
        check=read(independent);assert check['status'].startswith('passed')
        artifacts.append(independent)
    release={'version':run['version'],'stage':'source_completed_material_v3_identical_frozen_classifier',
       'status':'source_and_structure_verified_development_revision','manual':'CAL-5D-20260926-v1.3',
       'n':4924,'pending_n':0,'prediction_path':str(output.resolve()),
       'prediction_sha256':sha(output),'input_path':str((ROOT/'rule_inputs_v31_shared_v3.jsonl').resolve()),
       'input_sha256':run['input_sha256'],'llm_input_sha256':material['llm_input_sha256'],
       'classification_code_unchanged_vs_v2':True,'frozen_previous_versions_preserved':True,
       'source_completion_scope':'Five current units in one source-defined list and its anaphoric continuation; no construct or label changes',
       'method_validation_status':'Development source review; original A/C remain AI references with their original material. This is not independent human validation.',
       'created_at':datetime.now().astimezone().isoformat(),'artifacts':{str(p.resolve()):sha(p) for p in artifacts},
       'frozen_previous_artifacts_sha256':material['frozen_previous_artifacts_sha256']}
    assert not (HERE/'release_completed_material_v3.json').exists(),'Do not overwrite a frozen v3 release'
    write(HERE/'release_completed_material_v3.json',release)
    print(json.dumps({'status':out['status'],'n':out['n'],'label_changes':len(changes),
        'prediction_sha256':sha(output),'run_manifest_sha256':out['run_manifest_sha256'],
        'release_sha256':sha(HERE/'release_completed_material_v3.json')},ensure_ascii=False))

if __name__=='__main__':main()
