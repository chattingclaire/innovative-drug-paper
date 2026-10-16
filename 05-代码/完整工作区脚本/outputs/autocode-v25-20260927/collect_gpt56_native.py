"""Count native LLM progress or seal a fully completed first-output run.

Does not read reference labels. Never selects outputs by agreement or score.
"""
import argparse
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE/'llm_runs/gpt56-sol-v13-native-1'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def load_validator(path):
    spec=importlib.util.spec_from_file_location('frozen_output_validator',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--seal',action='store_true');args=parser.parse_args()
    plan=json.loads((ROOT/'run_plan.json').read_text())
    manifests=[];progress=[]
    for shard in plan['shards']:
        p=ROOT/f'shard-{shard["index"]:02d}'
        assert sha(p/'manifest.json')==shard['manifest_sha256']
        m=json.loads((p/'manifest.json').read_text());manifests.append((p,m))
        for name,digest in m['files'].items():assert sha(p/name)==digest,(p.name,name,'changed')
        count=0;n=0
        for packet in m['packets']:
            assert sha(p/packet['name'])==packet['sha256'],(p.name,packet['name'],'changed')
            output=p/packet['name'].replace('input-','output-')
            if output.exists():count+=1;n+=packet['n']
        progress.append({'shard':shard['index'],'saved_batches':count,'saved_unit_slots':n,
                         'planned_batches':shard['batches'],'planned_n':shard['n'],
                         'completion_manifest_present':(p/'completion.json').exists()})
    summary={'method_version':plan['method_version'],'requested_model':plan['requested_model'],
             'planned_n':plan['n'],'saved_unit_slots':sum(x['saved_unit_slots'] for x in progress),
             'saved_batches':sum(x['saved_batches'] for x in progress),'planned_batches':plan['batch_count'],
             'status_scope':'file presence only, not validation or research performance','shards':progress}
    if not args.seal:
        print(json.dumps(summary,ensure_ascii=False));return
    assert summary['saved_unit_slots']==4924,'Do not inspect or score partial outputs'
    assert all(x['completion_manifest_present'] for x in progress),'All agents must have sealed their shards'
    target=ROOT/'all_predictions.jsonl';sealed=ROOT/'prediction_seal.json'
    if target.exists() or sealed.exists():raise RuntimeError('Existing sealed outputs must never be overwritten')
    results=[];qa=[];bindings={}
    for p,m in manifests:
        validator=load_validator(p/'validate_output.py')
        schema=json.loads((p/'output_schema.json').read_text())
        for packet in m['packets']:
            output=p/packet['name'].replace('input-','output-')
            inputs=json.loads((p/packet['name']).read_text())['rows']
            raw=json.loads(output.read_text());errors=validator.shape(raw,schema)
            if not errors:errors+=validator.validate(raw,inputs)
            qa.append({'shard':p.name,'output':output.name,'n':packet['n'],'errors':errors})
            bindings[str(output.relative_to(ROOT))]=sha(output)
            # No score-based dropping or correction preference: first complete
            # labels remain the primary estimates. Malformed records prevent seal.
            assert [r['id'] for r in raw['rows']]==packet['ids'],'ID mismatch prevents seal'
            for row in raw['rows']:
                assert set(row['labels'])=={'S','E','Ec','I','F'}
                assert all(type(v) is int and v in (0,1) or v=='待定' for v in row['labels'].values())
                results.append(row)
        bindings[str((p/'completion.json').relative_to(ROOT))]=sha(p/'completion.json')
    results.sort(key=lambda row:row['id'])
    full=[json.loads(line) for line in (HERE/'current_llm_inputs.jsonl').read_text().splitlines()]
    assert sha(HERE/'current_llm_inputs.jsonl')==plan['source_input_sha256']
    assert [r['id'] for r in results]==sorted(r['id'] for r in full)
    target.write_text(''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in results))
    (ROOT/'first_output_QA.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
    seal={'created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'n':len(results),
          'method_version':plan['method_version'],'requested_model':plan['requested_model'],
          'run_plan_sha256':sha(ROOT/'run_plan.json'),'predictions_sha256':sha(target),
          'first_output_QA_sha256':sha(ROOT/'first_output_QA.json'),
          'batches_with_QA_issues':sum(bool(x['errors']) for x in qa),'output_bindings':bindings,
          'first_outputs_primary':True,'reference_labels_read':False,
          'corrections_not_silently_substituted':True,'collector_sha256':sha(Path(__file__))}
    sealed.write_text(json.dumps(seal,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in seal.items() if k!='output_bindings'},ensure_ascii=False))

if __name__=='__main__':main()
