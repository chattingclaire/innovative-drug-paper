"""One authorized, frozen 4924-record development shadow run.

No human/LLM labels or comparison results are read. Every first error and
material-pending value is retained; no retry or default-zero substitution.
"""
import argparse
import copy
import datetime
import hashlib
import importlib.metadata
import importlib.util
import json
from pathlib import Path
import sys
import time
import traceback
sys.dont_write_bytecode = True

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def environment_identity():
    spec=importlib.util.find_spec('pypdf')
    assert spec and spec.origin, 'Required PDF dependency unavailable'
    package=Path(spec.origin).resolve().parent
    return {'python_real_path':str(Path(sys.executable).resolve()),
            'python_version':sys.version,
            'python_binary_sha256':sha(Path(sys.executable).resolve()),
            'pypdf_version':importlib.metadata.version('pypdf'),
            'pypdf_package_real_path':str(package),
            'pypdf_key_file_sha256':{str(package/name):sha(package/name)
                                    for name in ('__init__.py','_reader.py','_page.py')}}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--freeze',required=True);args=ap.parse_args()
    fp=Path(args.freeze);frozen=json.loads(fp.read_text());root=fp.parent
    source=Path(frozen['input']);output=root/'full_actual4924.jsonl';manifest=output.with_suffix('.run.json')
    assert not output.exists() and not manifest.exists(), 'First full execution must be preserved'
    environment=environment_identity();assert environment==frozen['environment_identity']
    assert sha(source)==frozen['input_sha256']
    assert all(sha(p)==h for p,h in frozen['code_sha256'].items())
    assert all(sha(p)==h for p,h in frozen['protected_sha256'].items())
    rows=[json.loads(s)for s in source.read_text().splitlines()if s.strip()]
    assert len(rows)==4924==len({r['id']for r in rows})
    assert all(set(r)<= {'id','original_id','input'} and 'input'in r for r in rows)
    runtime=Path(frozen['runtime_directory']);sys.path.insert(0,str(runtime))
    import policy_coding_v27 as coder
    assert Path(coder.__file__).resolve().parent==runtime
    started=datetime.datetime.now().astimezone().isoformat();tick=time.monotonic()
    failures=[];pending=[];evidence_count=0;anchor_count=0;processed=0
    print(json.dumps({'event':'full_shadow_started','n':len(rows),'started_at':started,
                      'input_sha256':sha(source),'frozen_runtime':str(runtime)},ensure_ascii=False),flush=True)
    with output.open('x')as sink:
        for row in rows:
            item={'id':row['id'],'original_id':row.get('original_id')}
            original=copy.deepcopy(row['input']);record=copy.deepcopy(original)
            try:
                prediction=coder.code_unit(record)
                assert record==original, 'Coder mutated source input'
                assert prediction['unit_text_sha256']==hashlib.sha256(original['unit_text'].encode()).hexdigest()
                for e in prediction.get('evidence',[]):
                    assert original['unit_text'][e['start']:e['end']]==e['text']
                    evidence_count+=1
                    for a in e.get('current_relation_anchors',[]):
                        assert original['unit_text'][a['start']:a['end']]==a['text'];anchor_count+=1
                item.update(prediction=prediction,input_unchanged=True,current_evidence_and_relation_offsets_checked=True)
                if prediction.get('judgement_status')=='undetermined' or any(v is None for v in prediction['labels'].values()):pending.append(row['id'])
            except Exception as error:
                item['first_execution_failure']={'error_type':type(error).__name__,'message':str(error),'traceback':traceback.format_exc()}
                failures.append(row['id'])
            sink.write(json.dumps(item,ensure_ascii=False)+'\n');sink.flush();processed+=1
            if processed%100==0 or processed==len(rows):
                elapsed=time.monotonic()-tick
                progress={'event':'progress','processed':processed,'total':len(rows),'elapsed_seconds':round(elapsed,3),
                          'estimated_remaining_seconds_from_actual_mean':round(elapsed/processed*(len(rows)-processed),3),
                          'runtime_failures_so_far':len(failures),'pending_so_far':len(pending)}
                (root/'progress_latest.json').write_text(json.dumps(progress,ensure_ascii=False,indent=2)+'\n')
                print(json.dumps(progress,ensure_ascii=False),flush=True)
    elapsed=time.monotonic()-tick
    integrity=sha(source)==frozen['input_sha256'] and all(sha(p)==h for p,h in frozen['code_sha256'].items()) and all(sha(p)==h for p,h in frozen['protected_sha256'].items())
    environment_unchanged=environment_identity()==environment
    result={'started_at':started,'completed_at':datetime.datetime.now().astimezone().isoformat(),'elapsed_seconds':elapsed,
            'scope':'authorized_full_real_development_shadow_not_shared_material_validation_or_adoption',
            'n':len(rows),'n_processed':processed,'runtime_failure_ids':failures,'pending_ids':pending,
            'version':coder.VERSION,'input':str(source),'input_sha256':sha(source),'output':str(output),
            'output_sha256':sha(output),'freeze_sha256':sha(fp),'code_sha256':frozen['code_sha256'],
            'environment_identity':environment,'environment_identity_unchanged':environment_unchanged,
            'source_and_protected_file_integrity':integrity,'current_evidence_count_checked':evidence_count,
            'current_relation_anchor_count_checked':anchor_count,'single_attempt_per_record':True,
            'first_execution_failures_preserved':True,'unresolved_values_not_filled_with_zero':True,
            'human_or_LLM_labels_loaded':False,'kappa_or_accuracy_calculated':False,'full_corpus_run':True,'adopted':False}
    with manifest.open('x')as sink:json.dump(result,sink,ensure_ascii=False,indent=2);sink.write('\n')
    print(json.dumps({'event':'full_shadow_completed',**{k:result[k]for k in ('n_processed','elapsed_seconds','runtime_failure_ids','pending_ids','source_and_protected_file_integrity','environment_identity_unchanged','output_sha256')}},ensure_ascii=False),flush=True)
    assert integrity and environment_unchanged, 'Integrity failure preserved; no retry'
if __name__=='__main__':main()
