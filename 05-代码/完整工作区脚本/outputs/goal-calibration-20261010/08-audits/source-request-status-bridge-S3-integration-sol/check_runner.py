"""Check existing three logs old/alias once each; no reconstruction or coding."""
from pathlib import Path
import ast
import copy
import datetime
import hashlib
import json
import sys
import traceback
import types

D=Path(__file__).resolve().parent;R=D.parents[1]
sys.dont_write_bytecode=True
def bind(p):
    p=Path(p).resolve();b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def cj(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def write(name,v):
    p=D/'execution'/name;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
pre=json.loads((D/'preparation-seal.json').read_bytes())
for m in pre['members']+pre['inputs']:assert bind(m['path'])==m
assert not (D/'execution').exists();(D/'execution').mkdir()
cases=json.loads((D/'pointer-whitelist-and-fixed-expectations.json').read_bytes())
assert [c['record_id'] for c in cases]==pre['allowed_record_ids']
scope=json.loads((R/'06-coding/rule-full4481-final-v5-sol/frozen-scope.json').read_bytes())
counts={'semantic_unit':0,'RelationView':0,'judge':0,'actual_reading_log':0,'source_inventory':0,'protocol_check':0}
snapshot=D/'code-snapshot'
def import_code(name):
    p=snapshot/(name+'.py');mod=types.ModuleType(name);mod.__file__=str(p);sys.modules[name]=mod
    exec(compile(p.read_bytes(),str(p),'exec'),mod.__dict__);return mod
source=import_code('source_packet');receipts=import_code('source_receipts');bridge=import_code('status_bridge')
def forbidden_semantic(*args,**kwargs):
    counts['semantic_unit']+=1;raise RuntimeError('semantic_unit prohibited in mechanical integration')
source.semantic_unit=forbidden_semantic
original_inventory=source.source_inventory
def observed_inventory(bundle):
    counts['source_inventory']+=1;return original_inventory(bundle)
source.source_inventory=observed_inventory
bundles=[json.loads(Path(c['raw_source_packet_copy']['path']).read_bytes())['source_bundle'] for c in cases]
driver_raw=(snapshot/'rule_driver.py').read_bytes();tree=ast.parse(driver_raw)
finite=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='finite_protocol')
driver_namespace={'Path':Path,'hashlib':hashlib,'copy':copy,'sys':sys,'types':types,'cj':cj,'VERSION':scope['driver_version']}
exec(compile(ast.Module(body=[finite],type_ignores=[]),str(snapshot/'rule_driver.py'),'exec'),driver_namespace)
protocol=driver_namespace['finite_protocol'](source,bundles,scope['material_bindings'],scope)
protocol_payload=Path(scope['source_reading_protocol_code']['path']).read_bytes()
assert hashlib.sha256(protocol_payload).hexdigest()==bind(snapshot/'source_reading_protocol_v12.py')['sha256']
results=[];preservation=[]
with (D/'execution/immediate-check-results.jsonl').open('x',encoding='utf8') as stream:
    for c in cases:
        rid=c['record_id'];raw=Path(c['raw_saved_row_copy']['path']).read_bytes();original_row=json.loads(raw)
        pointer='/uniform_source_reading_log/source_requests'
        assert c['source_requests_pointer_whitelist']==[pointer]
        bridge_error=None;alias_row=receipt=None
        try:alias_row,receipt=bridge.bridge_json_bytes(raw,c['raw_saved_row_copy']['sha256'],pointer=pointer)
        except Exception as error:bridge_error={'type':type(error).__name__,'message':str(error),'traceback':traceback.format_exc()}
        if alias_row is not None:
            original_without_requests=copy.deepcopy(original_row);alias_without_requests=copy.deepcopy(alias_row)
            raw_requests=original_without_requests['uniform_source_reading_log'].pop('source_requests')
            canonical_requests=alias_without_requests['uniform_source_reading_log'].pop('source_requests')
            assert original_without_requests==alias_without_requests
            assert len(raw_requests)==len(canonical_requests)
            assert all({k:v for k,v in a.items() if k!='status'}=={k:v for k,v in b.items() if k!='status'} for a,b in zip(raw_requests,canonical_requests))
            details={'record_id':rid,'exact_only_status_alias_added':True,'complete_original_wrapper_except_target_request_array_equal':True,'original_log_sha256':hashlib.sha256(cj(original_row['uniform_source_reading_log']).encode()).hexdigest(),'alias_log_sha256':hashlib.sha256(cj(alias_row['uniform_source_reading_log']).encode()).hexdigest(),'preserved_log_fields_sha256':{k:hashlib.sha256(cj(v).encode()).hexdigest() for k,v in original_row['uniform_source_reading_log'].items() if k!='source_requests'},'preserved_capture_error_material_and_raw_request_fields_sha256':{k:hashlib.sha256(cj(v).encode()).hexdigest() for k,v in original_row.items() if k!='uniform_source_reading_log'},'mapping_receipt':receipt,'original_field_added':{'request_index':0,'field':'status','value':'resolved'},'diagnostic_retained_label_or_recovery_record_created':False}
            preservation.append(details);write('preservation/'+rid+'.json',details)
        for version,row,expected in [('original',original_row,c['expected_original_check']),('alias',alias_row,c['expected_alias_check'])]:
            result={'record_id':rid,'log_version':version,'fixed_expected':expected,'first_and_only_check_attempt':True,'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'check_entered':False,'actual_output':None,'exception':None,'bridge_exception':bridge_error if version=='alias' else None}
            stream.write(cj({'event':'protocol_check_start','record_id':rid,'log_version':version})+'\n');stream.flush()
            try:
                if row is None:raise RuntimeError('alias document withheld due to bridge exception')
                log=copy.deepcopy(row['uniform_source_reading_log']);result['input_log_sha256']=hashlib.sha256(cj(log).encode()).hexdigest()
                counts['protocol_check']+=1;result['check_entered']=True
                outcome=protocol.check(log);result['actual_output']=outcome
                assert log==row['uniform_source_reading_log'],'protocol.check mutated original supplied log'
                canonical_requests=row['uniform_source_reading_log']['source_requests']
                driver_stops=[q for q in canonical_requests if q.get('status','unresolved')!='resolved' and q.get('necessary_dependency',True)]
                result['driver_equivalent_required_stops_N']=len(driver_stops)
                result['driver_equivalent_same_request_array_sha256']=hashlib.sha256(cj(canonical_requests).encode()).hexdigest()
                result['requests_used_identically_by_protocol_and_driver_equivalent']=True
                result['matches_fixed_expectation']=outcome['errors']==expected['errors'] and outcome['dependency_stop_reasons']==expected['dependency_stop_reasons'] and len(driver_stops)==c['expected_'+version+'_driver_required_stop_N']
            except Exception as error:
                result['exception']={'type':type(error).__name__,'message':str(error),'traceback':traceback.format_exc()};result['matches_fixed_expectation']=False
            write('checks/'+rid+'-'+version+'.json',result)
            stream.write(cj({'event':'protocol_check_saved',**result})+'\n');stream.flush();results.append(result)
summary={'status':'three_saved_source_logs_mechanical_contract_integration_only','saved_check_results_N':len(results),'actual_protocol_check_calls_N':counts['protocol_check'],'matching_fixed_checks_N':sum(r['matches_fixed_expectation'] for r in results),'check_exceptions_N':sum(r['exception'] is not None for r in results),'alias_preservation_reports_N':len(preservation),'calls':counts,'new_retained_labels_N':0,'recovery_records_N':0,'metrics_N':0,'full_run_cleared':False,'classification_or_check_retries_N':0,'original_and_alias_results':[{k:r[k] for k in ['record_id','log_version','actual_output','exception','matches_fixed_expectation']} for r in results]}
write('summary.json',summary);print(json.dumps({k:v for k,v in summary.items() if k!='original_and_alias_results'},ensure_ascii=False))
raise SystemExit(0 if all(r['matches_fixed_expectation'] for r in results) else 2)
