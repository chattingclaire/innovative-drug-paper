"""One material-only actual comparison for the authorized old/new01402 packets."""
from pathlib import Path
import copy
import datetime
import hashlib
import importlib.util
import json
import sys
import traceback

sys.dont_write_bytecode=True
A=Path(__file__).resolve().parent
fixed=json.loads((A/'input-seal-before-execution.json').read_bytes())

def bind(p):
    p=Path(p).resolve();b=p.read_bytes()
    return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())

def save(name,x):
    with (A/name).open('x',encoding='utf8') as f:
        json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')

# All physical loading and imports finish before either classifier call.
packets=[]
for p in fixed['packets']:
    assert bind(p['path'])==p
    packets.append(json.loads(Path(p['path']).read_bytes()))
for p in fixed['code']+fixed['snapshots']:
    assert bind(p['path'])==p
modules={}
for n in ('evidence','source_packet','source_receipts','relations','dimensions'):
    spec=importlib.util.spec_from_file_location(n,A/'code-snapshot'/(n+'.py'))
    m=importlib.util.module_from_spec(spec);sys.modules[n]=m;spec.loader.exec_module(m);modules[n]=m
active=[None];io_attempts=[]
def audit(event,args):
    if active[0] is not None and (event=='open' or event.startswith(('os.listdir','os.scandir','os.remove','os.rename','os.mkdir','os.rmdir','os.link','os.symlink','os.truncate','os.chdir','os.chmod','os.chown','os.walk','subprocess.','socket.'))):
        io_attempts.append(dict(case=active[0],event=event,argument_repr=repr(args)))
        raise RuntimeError('Classifier filesystem/process/network I/O denied')
sys.addaudithook(audit)
records=[]
for case,packet in zip(('original01402_v15','same_version_article6_complete01402_v16'),packets):
    source_input=copy.deepcopy(packet['source_bundle'])
    before=copy.deepcopy(source_input)
    started=datetime.datetime.now(datetime.timezone.utc).isoformat()
    row=dict(case=case,packet_binding=fixed['packets'][len(records)],expected_retained_not_authority={'I':1},actual_started_at_utc=started)
    active[0]=case
    try:
        unit=modules['source_packet'].semantic_unit(source_input)
        original_unit=copy.deepcopy(unit)
        view=modules['relations'].RelationView(unit)
        decisions=modules['dimensions'].judge(view)
        modules['evidence'].validate_decisions(original_unit,decisions)
        assert source_input==before and view.unit==original_unit
        row.update(semantic_unit=original_unit,decisions=decisions,values={d:v['value'] for d,v in decisions.items()},relations=view.traces(),material_requests=view.material_requests,source_requests=view.source_requests,source_view_events=view.source_view_events,source_relation_traces=view.source_relation_traces,source_scope_review=view.source_scope_review,implementation_errors=getattr(view,'implementation_errors',[]),private_E_outcome_relations=getattr(view,'e_current_outcome_relations',[]),source_and_semantic_input_unchanged=True,evidence_validator_passed=True,existing_expected_matched=decisions['I']['value']==1)
    except Exception as e:
        row['technical_error']=dict(type=type(e).__name__,message=str(e),traceback=traceback.format_exc())
    finally:
        active[0]=None
    row['actual_finished_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();records.append(row)
save('actual-material-comparison-results.json',records)
code_exact=all(bind(p['path'])==p for p in fixed['code']+fixed['snapshots'])
input_exact=all(bind(p['path'])==p for p in fixed['packets'])
assert code_exact and input_exact
summary=dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),actual_comparative_run_N=1,semantic_input_N=2,code_same_exact=True,old_new_packet_files_unchanged=True,current_record_and_original_contexts_equal=packets[0]['source_bundle']['source_record']==packets[1]['source_bundle']['source_record'],values={x['case']:x.get('values') for x in records},full_decision_changed_dimensions=[d for d in ('S','E','Ec','I','F') if records[0].get('decisions',{}).get(d)!=records[1].get('decisions',{}).get(d)],technical_error_N=sum('technical_error' in x for x in records),denied_IO_attempts=io_attempts,model_calls=0,production_classifier_calls=0,new_code_revisions=0,existing_expected_changed=False,independent_human_adjudication=False,theoretical_judgment_preceded_classifier=fixed['theoretical_judgment'],actual_complete_record_results=bind(A/'actual-material-comparison-results.json'))
save('actual-material-comparison-summary.json',summary)
print(json.dumps(summary,ensure_ascii=False,indent=2))
