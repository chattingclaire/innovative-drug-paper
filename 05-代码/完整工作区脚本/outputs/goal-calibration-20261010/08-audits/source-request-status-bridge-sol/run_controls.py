"""Execute only fixed synthetic field contracts, preserving first results."""
from pathlib import Path
import copy
import hashlib
import json
import sys
import traceback

D=Path(__file__).resolve().parent
sys.dont_write_bytecode=True
def bind(p):
    p=Path(p).resolve();b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
pre=json.loads((D/'preparation-seal.json').read_bytes())
for m in pre['members']:assert bind(m['path'])==m
assert not (D/'execution').exists();(D/'execution').mkdir()
from status_bridge import bridge_json_bytes,BridgeContractError
cases=json.loads((D/'fixed-synthetic-controls.json').read_bytes());rows=[]
with (D/'execution/first-results.jsonl').open('x',encoding='utf8') as stream:
    for c in cases:
        row={'control_id':c['control_id'],'synthetic':True,'expected_statuses':c['expected_statuses'],'expected_error':c['expected_error'],'first_execution':True}
        try:
            out,receipt=bridge_json_bytes(c['raw_utf8_json'].encode(),c['supplied_sha256'],pointer=c['request_pointer'])
            row.update(actual_statuses=receipt['canonical_statuses'],actual_error=None,canonical_document=out,receipt=receipt)
            original=json.loads(c['raw_utf8_json']);a=copy.deepcopy(original);b=copy.deepcopy(out)
            reqs_a=a['log'].pop('source_requests');reqs_b=b['log'].pop('source_requests')
            assert a==b
            assert len(reqs_a)==len(reqs_b)
            for orig,norm in zip(reqs_a,reqs_b):
                assert {k:v for k,v in orig.items() if k!='status'}=={k:v for k,v in norm.items() if k!='status'}
            row['all_nonstatus_fields_and_other_document_parts_unchanged']=True
            # Exact existing protocol/driver request predicate; no invocation of their full check.
            row['legacy_required_stop_N']=sum(r.get('status','unresolved')!='resolved' and r.get('necessary_dependency',True) for r in reqs_b)
            row['whole_source_protocol_check_executed']=False
        except BridgeContractError as error:
            row.update(actual_statuses=None,actual_error=error.code,error_detail=error.detail,canonical_document=None,canonical_document_withheld=True)
        except Exception as error:
            row.update(actual_statuses=None,actual_error='UNEXPECTED_TECHNICAL_FAILURE',technical_error={'type':type(error).__name__,'message':str(error),'traceback':traceback.format_exc()})
        row['matches_fixed_expectation']=row['actual_statuses']==c['expected_statuses'] and row['actual_error']==c['expected_error']
        stream.write(json.dumps(row,ensure_ascii=False,allow_nan=False)+'\n');stream.flush();rows.append(row)
summary={'controls_N':len(rows),'matches_N':sum(r['matches_fixed_expectation'] for r in rows),'mismatches_N':sum(not r['matches_fixed_expectation'] for r in rows),'unexpected_technical_failures_N':sum(r['actual_error']=='UNEXPECTED_TECHNICAL_FAILURE' for r in rows),'classifier_calls_N':0,'actual_full_domain_records_processed_N':0,'actual_source_protocol_checks_N':0,'recovery_executed':False,'semantic_or_source_validation_certified':False}
with (D/'execution/summary.json').open('x',encoding='utf8') as f:json.dump(summary,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(summary,ensure_ascii=False))
raise SystemExit(0 if summary['mismatches_N']==0 else 2)
