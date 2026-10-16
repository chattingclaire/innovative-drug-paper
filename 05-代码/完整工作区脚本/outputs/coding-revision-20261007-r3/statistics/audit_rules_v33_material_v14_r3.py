"""Read-only binding and literal-span QA of the actual frozen v33/v14 run."""
from pathlib import Path
import datetime
import hashlib
import json
import statistical_core_r3 as c


def main():
    root=c.RUN;run_path=root/'rules-v33/all_predictions_material_v14.run.json'
    run=c.read(run_path);freeze=c.read(run['candidate_freeze_path'])
    assert c.sha(run['candidate_freeze_path'])==run['candidate_freeze_sha256']
    assert freeze['status']=='frozen_before_new_r3_confirmation_revealed'
    assert run['runtime_code_sha256']==freeze['production_code_sha256']
    for key in ('runtime_code_sha256','actual_source_and_candidate_sha256'):
        assert all(c.sha(path)==sha for path,sha in run[key].items())
    assert c.sha(run['input_path'])==run['input_sha256']
    assert c.sha(run['prediction_path'])==run['prediction_sha256']
    inputs=c.jsonl(run['input_path']);predictions=c.jsonl(run['prediction_path'])
    assert set(inputs)==set(predictions) and len(inputs)==run['n']==4924 and run['pending_n']==0
    assert run['reference_labels_loaded'] is False
    counts={'literal_evidence_spans':0,'literal_suppression_spans':0}
    for rid,row in predictions.items():
        text=inputs[rid]['input']['unit_text'];p=row['prediction']
        assert p['unit_text_sha256']==hashlib.sha256(text.encode()).hexdigest()
        assert p['version']==freeze['version'] and p['judgement_status']=='rule_prediction'
        assert all(c.binary(p['labels'][d]) for d in c.DIMS)
        for field,key in [('evidence','literal_evidence_spans'),('suppressions','literal_suppression_spans')]:
            for evidence in p[field]:
                assert text[evidence['start']:evidence['end']]==evidence['text'],(rid,field,evidence)
                counts[key]+=1
    assert counts==run['checks']
    result={'status':'pass_independent_execution_QA','all_checks_pass':True,
        'created_at':datetime.datetime.now().astimezone().isoformat(),'n':4924,'material_version':'v14',
        'final_output_sha256':run['prediction_sha256'],'actual_run':{'path':str(run_path),'sha256':c.sha(run_path)},
        'source_input_sha256':run['input_sha256'],'unchanged_frozen_runtime_files':len(run['runtime_code_sha256']),
        'all_actual_sources_and_candidate_hashes_checked':len(run['actual_source_and_candidate_sha256']),
        'literal_checks':counts,'reference_or_metrics_read':False,'labels_changed':False,
        'scope':'Binding/binary/literal evidence validation of the recorded actual run; not semantic correctness.',
        'script_sha256':c.sha(Path(__file__))}
    target=root/'statistics/规则v33-v14实际执行独立QA.json';assert not target.exists();c.write_json(target,result)
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
